from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, require_faculty_or_admin
from app.models.entities import (
    User, UserRole, Course, CourseEnrollment, AttendanceRecord, AttendanceStatus, StudentProfile
)
from app.schemas.schemas import AttendanceBatchSave, AttendanceRecordResponse, AttendanceSummaryResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get("/course/{course_id}")
def get_course_attendance_sheet(
    course_id: int,
    date_val: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    # Permissions: Faculty can view only if assigned or Admin
    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or course.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only manage attendance for your assigned courses.")

    # Get enrolled students
    enrollments = db.query(CourseEnrollment).filter(CourseEnrollment.course_id == course_id).all()
    # Get existing records for this date
    existing_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.course_id == course_id,
        AttendanceRecord.date == date_val
    ).all()
    records_by_student = {r.student_id: r for r in existing_records}

    roster = []
    for en in enrollments:
        st = en.student
        rec = records_by_student.get(st.id)
        roster.append({
            "student_id": st.id,
            "student_id_number": st.student_id_number,
            "full_name": st.user.full_name,
            "email": st.user.email,
            "status": rec.status.value if rec else "PRESENT",
            "notes": rec.notes if rec else "",
            "is_saved": rec is not None
        })

    return {
        "course_id": course.id,
        "course_code": course.code,
        "course_title": course.title,
        "date": date_val.isoformat(),
        "total_enrolled": len(enrollments),
        "roster": roster
    }

@router.post("/batch")
def save_batch_attendance(
    payload: AttendanceBatchSave,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or course.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only submit attendance for your assigned courses.")

    saved_count = 0
    for item in payload.records:
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.course_id == payload.course_id,
            AttendanceRecord.student_id == item.student_id,
            AttendanceRecord.date == payload.date
        ).first()

        if existing:
            existing.status = item.status
            existing.notes = item.notes
        else:
            new_rec = AttendanceRecord(
                course_id=payload.course_id,
                student_id=item.student_id,
                date=payload.date,
                status=item.status,
                notes=item.notes
            )
            db.add(new_rec)
        saved_count += 1

    db.commit()
    return {
        "status": "SUCCESS",
        "message": f"Successfully saved attendance for {saved_count} students on {payload.date.isoformat()}.",
        "saved_count": saved_count
    }

@router.get("/student/{student_id}")
def get_student_attendance(
    student_id: int,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Permissions: Student can only view own; Faculty/Admin can view any
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile or current_user.student_profile.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied to other student's attendance records.")

    query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    if course_id:
        query = query.filter(AttendanceRecord.course_id == course_id)

    records = query.order_by(AttendanceRecord.date.desc()).all()
    total = len(records)
    present_cnt = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent_cnt = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    late_cnt = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    pct = round(((present_cnt + (late_cnt * 0.5)) / total * 100), 1) if total > 0 else 100.0

    formatted_records = [
        AttendanceRecordResponse(
            id=r.id,
            course_id=r.course_id,
            course_code=r.course.code,
            student_id=r.student_id,
            student_name=r.student.user.full_name,
            student_number=r.student.student_id_number,
            date=r.date,
            status=r.status,
            notes=r.notes
        ) for r in records
    ]

    return {
        "student_id": student.id,
        "student_name": student.user.full_name,
        "summary": AttendanceSummaryResponse(
            total_classes=total,
            present_count=present_cnt,
            absent_count=absent_cnt,
            late_count=late_cnt,
            attendance_percentage=pct
        ),
        "records": formatted_records
    }
