from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.deps import get_current_user, require_admin
from app.models.entities import User, UserRole, FacultyProfile, Department, Course, NotificationPreference
from app.schemas.schemas import FacultyCreate, FacultyUpdate, FacultyResponse, CourseResponse

router = APIRouter(prefix="/faculty", tags=["Faculty"])

def format_faculty(f: FacultyProfile) -> FacultyResponse:
    dept_name = f.department.name if f.department else None
    return FacultyResponse(
        id=f.id,
        user_id=f.user.id,
        employee_id=f.employee_id,
        full_name=f.user.full_name,
        email=f.user.email,
        department_id=f.department_id,
        department_name=dept_name,
        designation=f.designation,
        office_room=f.office_room,
        phone=f.phone,
        qualification=f.qualification,
        assigned_course_count=len(f.courses),
    )

@router.get("", response_model=List[FacultyResponse])
def list_faculty(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    designation: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(FacultyProfile).join(User, FacultyProfile.user_id == User.id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (FacultyProfile.employee_id.ilike(s)) | (User.email.ilike(s)))
    if department_id:
        query = query.filter(FacultyProfile.department_id == department_id)
    if designation:
        query = query.filter(FacultyProfile.designation.ilike(f"%{designation}%"))

    faculty_members = query.order_by(User.full_name.asc()).all()
    return [format_faculty(f) for f in faculty_members]

@router.get("/{faculty_id}")
def get_faculty_details(faculty_id: int, db: Session = Depends(get_db)):
    f = db.query(FacultyProfile).filter(FacultyProfile.id == faculty_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Faculty member not found.")

    assigned_courses = []
    for c in f.courses:
        assigned_courses.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "credits": c.credits,
            "semester": c.semester,
            "schedule": c.schedule,
            "enrolled_count": len(c.enrollments)
        })

    return {
        "faculty": format_faculty(f),
        "assigned_courses": assigned_courses
    }

@router.post("", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
def create_faculty(
    payload: FacultyCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    existing_eid = db.query(FacultyProfile).filter(FacultyProfile.employee_id == payload.employee_id).first()
    if existing_eid:
        raise HTTPException(status_code=400, detail="Employee ID already registered.")

    dept = db.query(Department).filter(Department.id == payload.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.FACULTY,
        is_active=True
    )
    db.add(user)
    db.flush()

    faculty = FacultyProfile(
        user_id=user.id,
        employee_id=payload.employee_id,
        department_id=payload.department_id,
        designation=payload.designation,
        office_room=payload.office_room,
        phone=payload.phone,
        qualification=payload.qualification
    )
    db.add(faculty)
    db.add(NotificationPreference(user_id=user.id))
    db.commit()
    db.refresh(faculty)
    return format_faculty(faculty)

@router.put("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    f = db.query(FacultyProfile).filter(FacultyProfile.id == faculty_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Faculty member not found.")

    if payload.full_name is not None and payload.full_name.strip():
        f.user.full_name = payload.full_name.strip()
    if payload.department_id is not None:
        dept = db.query(Department).filter(Department.id == payload.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found.")
        f.department_id = payload.department_id
    if payload.designation is not None:
        f.designation = payload.designation
    if payload.office_room is not None:
        f.office_room = payload.office_room
    if payload.phone is not None:
        f.phone = payload.phone
    if payload.qualification is not None:
        f.qualification = payload.qualification

    db.commit()
    db.refresh(f)
    return format_faculty(f)

@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty(
    faculty_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    f = db.query(FacultyProfile).filter(FacultyProfile.id == faculty_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Faculty member not found.")

    db.delete(f.user)  # Cascades to faculty_profile
    db.commit()
    return None
