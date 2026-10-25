from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin, require_faculty_or_admin
from app.models.entities import (
    User, UserRole, Course, Department, FacultyProfile, StudentProfile,
    CourseEnrollment, Assignment
)
from app.schemas.schemas import CourseCreate, CourseUpdate, CourseResponse, EnrollmentCreate

router = APIRouter(prefix="/courses", tags=["Courses"])

def format_course(c: Course) -> CourseResponse:
    dept_name = c.department.name if c.department else None
    inst_name = c.instructor.user.full_name if (c.instructor and c.instructor.user) else "TBA"
    return CourseResponse(
        id=c.id,
        code=c.code,
        title=c.title,
        description=c.description,
        credits=c.credits,
        department_id=c.department_id,
        department_name=dept_name,
        faculty_id=c.faculty_id,
        instructor_name=inst_name,
        semester=c.semester,
        schedule=c.schedule,
        max_capacity=c.max_capacity,
        enrolled_count=len(c.enrollments),
    )

@router.get("", response_model=List[CourseResponse])
def list_courses(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    semester: Optional[str] = None,
    faculty_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Course)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Course.title.ilike(s)) | (Course.code.ilike(s)) | (Course.description.ilike(s)))
    if department_id:
        query = query.filter(Course.department_id == department_id)
    if semester:
        query = query.filter(Course.semester == semester)
    if faculty_id:
        query = query.filter(Course.faculty_id == faculty_id)

    courses = query.order_by(Course.code.asc()).all()
    return [format_course(c) for c in courses]

@router.get("/{course_id}")
def get_course_details(course_id: int, db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")

    enrolled_students = []
    for en in c.enrollments:
        st = en.student
        if st and st.user:
            enrolled_students.append({
                "student_id": st.id,
                "student_id_number": st.student_id_number,
                "full_name": st.user.full_name,
                "email": st.user.email,
                "year": st.year,
                "semester": st.semester,
                "enrolled_at": en.enrolled_at.isoformat()
            })

    assignments = []
    for a in c.assignments:
        assignments.append({
            "id": a.id,
            "title": a.title,
            "due_date": a.due_date.isoformat(),
            "max_marks": a.max_marks,
            "submissions_count": len(a.submissions)
        })

    # Syllabus & course materials
    materials = [
        {"id": 1, "title": f"{c.code} Lecture Notes & Course Syllabus", "type": "PDF", "uploaded_at": "2026-09-01"},
        {"id": 2, "title": "Reference Guide & Lab Specifications", "type": "Document", "uploaded_at": "2026-09-15"},
        {"id": 3, "title": "Problem Set 1 Solution Discussion", "type": "Notes", "uploaded_at": "2026-10-05"},
    ]

    return {
        "course": format_course(c),
        "instructor": {
            "id": c.instructor.id if c.instructor else None,
            "name": c.instructor.user.full_name if (c.instructor and c.instructor.user) else "Unassigned",
            "email": c.instructor.user.email if (c.instructor and c.instructor.user) else None,
            "designation": c.instructor.designation if c.instructor else None,
            "office_room": c.instructor.office_room if c.instructor else None,
        } if c.instructor else None,
        "enrolled_students": enrolled_students,
        "assignments": assignments,
        "materials": materials,
    }

@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    _staff: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Course).filter(Course.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course with this code already exists.")

    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    if payload.faculty_id:
        f = db.query(FacultyProfile).filter(FacultyProfile.id == payload.faculty_id).first()
        if not f:
            raise HTTPException(status_code=404, detail="Assigned faculty member not found.")

    c = Course(
        code=payload.code.upper(),
        title=payload.title,
        description=payload.description,
        credits=payload.credits,
        department_id=payload.department_id,
        faculty_id=payload.faculty_id,
        semester=payload.semester,
        schedule=payload.schedule,
        max_capacity=payload.max_capacity
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return format_course(c)

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    _staff: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")

    if payload.title is not None:
        c.title = payload.title
    if payload.description is not None:
        c.description = payload.description
    if payload.credits is not None:
        c.credits = payload.credits
    if payload.department_id is not None:
        dept = db.query(Department).filter(Department.id == payload.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found.")
        c.department_id = payload.department_id
    if payload.faculty_id is not None:
        if payload.faculty_id > 0:
            f = db.query(FacultyProfile).filter(FacultyProfile.id == payload.faculty_id).first()
            if not f:
                raise HTTPException(status_code=404, detail="Faculty member not found.")
            c.faculty_id = payload.faculty_id
        else:
            c.faculty_id = None
    if payload.semester is not None:
        c.semester = payload.semester
    if payload.schedule is not None:
        c.schedule = payload.schedule
    if payload.max_capacity is not None:
        c.max_capacity = payload.max_capacity

    db.commit()
    db.refresh(c)
    return format_course(c)

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")

    db.delete(c)
    db.commit()
    return None

@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_student(
    course_id: int,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found.")

    target_student_id = student_id
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(status_code=400, detail="Student profile is not initialized.")
        target_student_id = current_user.student_profile.id
    elif not target_student_id:
        raise HTTPException(status_code=400, detail="student_id is required for staff enrollment.")

    st = db.query(StudentProfile).filter(StudentProfile.id == target_student_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Check already enrolled
    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.student_id == target_student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student is already enrolled in this course.")

    # Check capacity
    if len(c.enrollments) >= c.max_capacity:
        raise HTTPException(status_code=400, detail="Course has reached maximum student capacity.")

    enrollment = CourseEnrollment(course_id=course_id, student_id=target_student_id)
    db.add(enrollment)
    db.commit()
    return {"status": "SUCCESS", "message": f"Successfully enrolled in {c.code}."}

@router.delete("/{course_id}/enroll/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def drop_student_enrollment(
    course_id: int,
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Student can drop own course; admin/faculty can drop any
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile or current_user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="You cannot drop courses for another student.")

    enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course_id,
        CourseEnrollment.student_id == student_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found.")

    db.delete(enrollment)
    db.commit()
    return None
