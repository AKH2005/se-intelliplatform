from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.entities import Department
from app.schemas.schemas import DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    out = []
    for d in departments:
        out.append(DepartmentResponse(
            id=d.id,
            name=d.name,
            code=d.code,
            description=d.description,
            head_of_department=d.head_of_department,
            student_count=len(d.students),
            faculty_count=len(d.faculty),
            course_count=len(d.courses),
        ))
    return out

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    d = db.query(Department).filter(Department.id == department_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found.")
    return DepartmentResponse(
        id=d.id,
        name=d.name,
        code=d.code,
        description=d.description,
        head_of_department=d.head_of_department,
        student_count=len(d.students),
        faculty_count=len(d.faculty),
        course_count=len(d.courses),
    )

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _admin = Depends(require_admin)
):
    existing = db.query(Department).filter(
        (Department.code == payload.code.upper()) | (Department.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department with this code or name already exists.")

    d = Department(
        name=payload.name,
        code=payload.code.upper(),
        description=payload.description,
        head_of_department=payload.head_of_department
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return DepartmentResponse(
        id=d.id,
        name=d.name,
        code=d.code,
        description=d.description,
        head_of_department=d.head_of_department,
        student_count=0,
        faculty_count=0,
        course_count=0,
    )
