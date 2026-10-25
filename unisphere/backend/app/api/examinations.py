from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, require_faculty_or_admin
from app.models.entities import (
    User, UserRole, Course, CourseEnrollment, Examination, ExaminationResult, StudentProfile
)
from app.schemas.schemas import (
    ExaminationCreate, ExaminationResponse, ResultBatchEntry, ResultResponse
)

router = APIRouter(prefix="/examinations", tags=["Examinations"])

def format_exam(e: Examination) -> ExaminationResponse:
    today = date.today()
    return ExaminationResponse(
        id=e.id,
        course_id=e.course_id,
        course_code=e.course.code if e.course else None,
        course_title=e.course.title if e.course else None,
        title=e.title,
        exam_type=e.exam_type,
        exam_date=e.exam_date,
        start_time=e.start_time,
        duration_minutes=e.duration_minutes,
        max_marks=e.max_marks,
        room_number=e.room_number,
        is_past=e.exam_date < today,
        result_count=len(e.results),
    )

@router.get("", response_model=List[ExaminationResponse])
def list_examinations(
    course_id: Optional[int] = None,
    upcoming_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Examination).join(Course, Examination.course_id == Course.id)

    if current_user.role == UserRole.STUDENT and current_user.student_profile:
        enrolled_ids = [e.course_id for e in current_user.student_profile.enrollments]
        query = query.filter(Examination.course_id.in_(enrolled_ids))
    elif current_user.role == UserRole.FACULTY and current_user.faculty_profile:
        query = query.filter(Course.faculty_id == current_user.faculty_profile.id)

    if course_id:
        query = query.filter(Examination.course_id == course_id)
    if upcoming_only:
        query = query.filter(Examination.exam_date >= date.today())

    exams = query.order_by(Examination.exam_date.asc()).all()
    return [format_exam(e) for e in exams]

@router.get("/{examination_id}")
def get_examination_details(
    examination_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    e = db.query(Examination).filter(Examination.id == examination_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Examination not found.")

    student_id = current_user.student_profile.id if (current_user.role == UserRole.STUDENT and current_user.student_profile) else None

    # Roster of enrolled students
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == e.course_id).all()
    existing_results = {r.student_id: r for r in e.results}

    student_roster = []
    if current_user.role in (UserRole.FACULTY, UserRole.ADMINISTRATOR):
        for en in enrollments:
            st = en.student
            res = existing_results.get(st.id)
            student_roster.append({
                "student_id": st.id,
                "student_id_number": st.student_id_number,
                "full_name": st.user.full_name,
                "marks_obtained": res.marks_obtained if res else None,
                "grade": res.grade if res else None,
                "remarks": res.remarks if res else None,
                "is_recorded": res is not None
            })
    elif student_id:
        my_res = existing_results.get(student_id)
        if my_res:
            student_roster.append({
                "student_id": student_id,
                "student_id_number": current_user.student_profile.student_id_number,
                "full_name": current_user.full_name,
                "marks_obtained": my_res.marks_obtained,
                "grade": my_res.grade,
                "remarks": my_res.remarks,
                "is_recorded": True
            })

    return {
        "examination": format_exam(e),
        "results": student_roster,
        "can_enter_marks": current_user.role in (UserRole.FACULTY, UserRole.ADMINISTRATOR)
    }

@router.post("", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_examination(
    payload: ExaminationCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.id == payload.course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")

    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or c.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only schedule exams for your assigned courses.")

    exam = Examination(
        course_id=payload.course_id,
        title=payload.title,
        exam_type=payload.exam_type,
        exam_date=payload.exam_date,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        max_marks=payload.max_marks,
        room_number=payload.room_number
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return format_exam(exam)

@router.post("/{examination_id}/results/batch")
def enter_batch_results(
    examination_id: int,
    payload: ResultBatchEntry,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    exam = db.query(Examination).filter(Examination.id == examination_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found.")

    course = exam.course
    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or course.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only submit marks for your assigned courses.")

    saved_count = 0
    for item in payload.results:
        if item.marks_obtained < 0 or item.marks_obtained > exam.max_marks:
            raise HTTPException(
                status_code=400,
                detail=f"Marks for student {item.student_id} must be between 0 and {exam.max_marks}."
            )

        existing = db.query(ExaminationResult).filter(
            ExaminationResult.examination_id == examination_id,
            ExaminationResult.student_id == item.student_id
        ).first()

        if existing:
            existing.marks_obtained = item.marks_obtained
            existing.grade = item.grade
            existing.remarks = item.remarks
            existing.recorded_at = datetime.utcnow()
        else:
            res = ExaminationResult(
                examination_id=examination_id,
                student_id=item.student_id,
                marks_obtained=item.marks_obtained,
                grade=item.grade,
                remarks=item.remarks
            )
            db.add(res)
        saved_count += 1

    db.commit()
    return {
        "status": "SUCCESS",
        "message": f"Successfully recorded marks for {saved_count} students.",
        "saved_count": saved_count
    }

@router.get("/results/student/{student_id}", response_model=List[ResultResponse])
def get_student_results(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Permissions: Student can only view own results
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile or current_user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied to other student's examination results.")

    results = db.query(ExaminationResult).filter(ExaminationResult.student_id == student_id).all()
    out = []
    for r in results:
        out.append(ResultResponse(
            id=r.id,
            examination_id=r.examination_id,
            exam_title=r.examination.title,
            course_code=r.examination.course.code,
            course_title=r.examination.course.title,
            student_id=r.student_id,
            student_name=r.student.user.full_name,
            marks_obtained=r.marks_obtained,
            max_marks=r.examination.max_marks,
            grade=r.grade,
            remarks=r.remarks,
            recorded_at=r.recorded_at
        ))
    return out
