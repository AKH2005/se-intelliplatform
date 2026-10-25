from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.deps import get_current_user, require_admin, require_faculty_or_admin
from app.models.entities import (
    User, UserRole, StudentProfile, Department, CourseEnrollment, Course,
    AttendanceRecord, AssignmentSubmission, ExaminationResult, NotificationPreference
)
from app.schemas.schemas import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter(prefix="/students", tags=["Students"])

def format_student(student: StudentProfile) -> StudentResponse:
    dept_name = student.department.name if student.department else None
    return StudentResponse(
        id=student.id,
        user_id=student.user.id,
        student_id_number=student.student_id_number,
        full_name=student.user.full_name,
        email=student.user.email,
        department_id=student.department_id,
        department_name=dept_name,
        year=student.year,
        semester=student.semester,
        gpa=student.gpa,
        phone=student.phone,
        address=student.address,
    )

@router.get("", response_model=List[StudentResponse])
def list_students(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    sort_by: Optional[str] = "name",
    order: Optional[str] = "asc",
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(StudentProfile).join(User, StudentProfile.user_id == User.id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (StudentProfile.student_id_number.ilike(s)) | (User.email.ilike(s)))
    if department_id:
        query = query.filter(StudentProfile.department_id == department_id)
    if year:
        query = query.filter(StudentProfile.year == year)

    # Sorting
    if sort_by == "gpa":
        query = query.order_by(StudentProfile.gpa.desc() if order == "desc" else StudentProfile.gpa.asc())
    elif sort_by == "student_id":
        query = query.order_by(StudentProfile.student_id_number.desc() if order == "desc" else StudentProfile.student_id_number.asc())
    else:
        query = query.order_by(User.full_name.desc() if order == "desc" else User.full_name.asc())

    students = query.offset(skip).limit(limit).all()
    return [format_student(st) for st in students]

@router.get("/{student_id}")
def get_student_details(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found.")

    # Students can view their own record or public directory details
    is_self = (current_user.role == UserRole.STUDENT and current_user.student_profile and current_user.student_profile.id == student.id)
    is_staff = current_user.role in (UserRole.FACULTY, UserRole.ADMINISTRATOR)

    # Enrolled courses
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.student_id == student.id).all()
    enrolled_courses = []
    for en in enrollments:
        c = en.course
        enrolled_courses.append({
            "enrollment_id": en.id,
            "course_id": c.id,
            "course_code": c.code,
            "title": c.title,
            "credits": c.credits,
            "semester": c.semester,
            "schedule": c.schedule,
            "instructor": c.instructor.user.full_name if c.instructor and c.instructor.user else "TBA",
            "enrolled_at": en.enrolled_at.isoformat() if en.enrolled_at else None
        })

    # Attendance summary & records
    att_records = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).order_by(AttendanceRecord.date.desc()).all()
    total_classes = len(att_records)
    present_cnt = sum(1 for a in att_records if a.status.value == "PRESENT")
    absent_cnt = sum(1 for a in att_records if a.status.value == "ABSENT")
    late_cnt = sum(1 for a in att_records if a.status.value == "LATE")
    pct = round(((present_cnt + (late_cnt * 0.5)) / total_classes * 100), 1) if total_classes > 0 else 100.0

    attendance_history = [{
        "id": a.id,
        "course_code": a.course.code,
        "course_title": a.course.title,
        "date": a.date.isoformat(),
        "status": a.status.value,
        "notes": a.notes
    } for a in att_records[:20]]

    # Exam results
    exam_results = []
    results = db.query(ExaminationResult).filter(ExaminationResult.student_id == student.id).all()
    for r in results:
        exam_results.append({
            "id": r.id,
            "exam_id": r.examination.id,
            "exam_title": r.examination.title,
            "course_code": r.examination.course.code,
            "marks_obtained": r.marks_obtained,
            "max_marks": r.examination.max_marks,
            "grade": r.grade,
            "remarks": r.remarks,
            "date": r.examination.exam_date.isoformat()
        })

    # Assignment submissions
    submissions = []
    subs = db.query(AssignmentSubmission).filter(AssignmentSubmission.student_id == student.id).all()
    for s in subs:
        submissions.append({
            "id": s.id,
            "assignment_id": s.assignment.id,
            "assignment_title": s.assignment.title,
            "course_code": s.assignment.course.code,
            "submitted_at": s.submitted_at.isoformat(),
            "status": s.status.value,
            "marks_obtained": s.marks_obtained,
            "max_marks": s.assignment.max_marks,
            "feedback": s.feedback
        })

    return {
        "student": format_student(student),
        "personal_info": {
            "email": student.user.email,
            "phone": student.phone if (is_self or is_staff) else "Restricted",
            "address": student.address if (is_self or is_staff) else "Restricted",
            "emergency_contact": student.emergency_contact if (is_self or is_staff) else "Restricted",
        },
        "enrolled_courses": enrolled_courses,
        "attendance": {
            "total_classes": total_classes,
            "present": present_cnt,
            "absent": absent_cnt,
            "late": late_cnt,
            "percentage": pct,
            "history": attendance_history
        },
        "exam_results": exam_results,
        "submissions": submissions,
        "can_edit": is_staff
    }

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    existing_sid = db.query(StudentProfile).filter(StudentProfile.student_id_number == payload.student_id_number).first()
    if existing_sid:
        raise HTTPException(status_code=400, detail="Student ID number already registered.")

    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT,
        is_active=True
    )
    db.add(user)
    db.flush()

    student = StudentProfile(
        user_id=user.id,
        student_id_number=payload.student_id_number,
        department_id=payload.department_id,
        year=payload.year,
        semester=payload.semester,
        gpa=payload.gpa,
        phone=payload.phone,
        address=payload.address,
        emergency_contact=payload.emergency_contact
    )
    db.add(student)
    db.add(NotificationPreference(user_id=user.id))
    db.commit()
    db.refresh(student)
    return format_student(student)

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    _staff: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    if payload.full_name is not None and payload.full_name.strip():
        student.user.full_name = payload.full_name.strip()
    if payload.department_id is not None:
        dept = db.query(Department).filter(Department.id == payload.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Target department does not exist.")
        student.department_id = payload.department_id
    if payload.year is not None:
        student.year = payload.year
    if payload.semester is not None:
        student.semester = payload.semester
    if payload.gpa is not None:
        student.gpa = payload.gpa
    if payload.phone is not None:
        student.phone = payload.phone
    if payload.address is not None:
        student.address = payload.address
    if payload.emergency_contact is not None:
        student.emergency_contact = payload.emergency_contact

    db.commit()
    db.refresh(student)
    return format_student(student)

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    user = student.user
    db.delete(user)  # Cascades to student_profile
    db.commit()
    return None
