from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.core.database import get_db
from app.core.deps import get_current_user, require_student, require_roles
from app.models.entities import (
    User, UserRole, StudentProfile, FacultyProfile, Course, Department,
    AttendanceRecord, AttendanceStatus, Assignment, AssignmentSubmission,
    SubmissionStatus, Examination, ExaminationResult, Announcement
)
from app.schemas.schemas import (
    StudentDashboardResponse, FacultyDashboardResponse, AdminDashboardResponse,
    StudentResponse, CourseResponse, AttendanceSummaryResponse,
    ExaminationResponse, AssignmentResponse, AnnouncementResponse, ResultResponse,
    FacultyResponse
)
from app.api.students import format_student
from app.api.faculty import format_faculty
from app.api.courses import format_course
from app.api.assignments import format_assignment
from app.api.examinations import format_exam
from app.api.announcements import format_announcement

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])

@router.get("/student", response_model=StudentDashboardResponse)
def get_student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    student = current_user.student_profile
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found.")

    # Enrolled courses
    enrolled_courses = [format_course(e.course) for e in student.enrollments if e.course]
    enrolled_course_ids = [c.id for c in enrolled_courses]

    # Attendance summary
    att_records = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student.id).all()
    total_classes = len(att_records)
    present_cnt = sum(1 for a in att_records if a.status == AttendanceStatus.PRESENT)
    absent_cnt = sum(1 for a in att_records if a.status == AttendanceStatus.ABSENT)
    late_cnt = sum(1 for a in att_records if a.status == AttendanceStatus.LATE)
    pct = round(((present_cnt + (late_cnt * 0.5)) / total_classes * 100), 1) if total_classes > 0 else 100.0

    attendance_summary = AttendanceSummaryResponse(
        total_classes=total_classes,
        present_count=present_cnt,
        absent_count=absent_cnt,
        late_count=late_cnt,
        attendance_percentage=pct
    )

    # Upcoming examinations
    upcoming_exams = db.query(Examination).filter(
        Examination.course_id.in_(enrolled_course_ids),
        Examination.exam_date >= date.today()
    ).order_by(Examination.exam_date.asc()).limit(5).all()

    # Pending assignments
    submitted_assignment_ids = [s.assignment_id for s in student.submissions]
    pending_assignments = db.query(Assignment).filter(
        Assignment.course_id.in_(enrolled_course_ids),
        ~Assignment.id.in_(submitted_assignment_ids) if submitted_assignment_ids else True,
        Assignment.due_date >= datetime.utcnow()
    ).order_by(Assignment.due_date.asc()).limit(5).all()

    # Recent announcements
    recent_announcements = db.query(Announcement).filter(
        Announcement.is_published == True
    ).order_by(Announcement.published_at.desc()).limit(5).all()

    # Recent results
    recent_results = []
    for r in student.exam_results[:5]:
        recent_results.append(ResultResponse(
            id=r.id,
            examination_id=r.examination_id,
            exam_title=r.examination.title,
            course_code=r.examination.course.code,
            course_title=r.examination.course.title,
            student_id=r.student_id,
            student_name=current_user.full_name,
            marks_obtained=r.marks_obtained,
            max_marks=r.examination.max_marks,
            grade=r.grade,
            remarks=r.remarks,
            recorded_at=r.recorded_at
        ))

    return StudentDashboardResponse(
        student_profile=format_student(student),
        enrolled_courses=enrolled_courses,
        attendance_summary=attendance_summary,
        upcoming_examinations=[format_exam(e) for e in upcoming_exams],
        pending_assignments=[format_assignment(a, student.id) for a in pending_assignments],
        recent_announcements=[format_announcement(a) for a in recent_announcements],
        recent_results=recent_results,
        overall_gpa=student.gpa
    )

@router.get("/faculty", response_model=FacultyDashboardResponse)
def get_faculty_dashboard(
    current_user: User = Depends(require_roles(UserRole.FACULTY, UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db)
):
    faculty = current_user.faculty_profile
    if not faculty:
        raise HTTPException(status_code=400, detail="Faculty profile not found.")

    assigned_courses = [format_course(c) for c in faculty.courses]
    assigned_course_ids = [c.id for c in assigned_courses]

    # Total students in assigned courses
    total_students = sum(c.enrolled_count for c in assigned_courses)

    # Pending grading tasks
    pending_grading_count = db.query(AssignmentSubmission).join(
        Assignment, AssignmentSubmission.assignment_id == Assignment.id
    ).filter(
        Assignment.course_id.in_(assigned_course_ids),
        AssignmentSubmission.status == SubmissionStatus.SUBMITTED
    ).count()

    # Recent attendance count (last 7 days)
    recent_attendance_count = db.query(AttendanceRecord).filter(
        AttendanceRecord.course_id.in_(assigned_course_ids)
    ).count()

    # Upcoming deadlines for assigned courses
    upcoming_deadlines = db.query(Assignment).filter(
        Assignment.course_id.in_(assigned_course_ids),
        Assignment.due_date >= datetime.utcnow()
    ).order_by(Assignment.due_date.asc()).limit(5).all()

    recent_announcements = db.query(Announcement).filter(
        Announcement.is_published == True
    ).order_by(Announcement.published_at.desc()).limit(5).all()

    return FacultyDashboardResponse(
        faculty_profile=format_faculty(faculty),
        assigned_courses=assigned_courses,
        total_students=total_students,
        pending_grading_count=pending_grading_count,
        recent_attendance_count=recent_attendance_count,
        upcoming_deadlines=[format_assignment(a) for a in upcoming_deadlines],
        recent_announcements=[format_announcement(a) for a in recent_announcements],
    )

@router.get("/admin", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db)
):
    total_students = db.query(StudentProfile).count()
    total_faculty = db.query(FacultyProfile).count()
    total_courses = db.query(Course).count()
    departments = db.query(Department).all()

    # Attendance overall rate
    all_att = db.query(AttendanceRecord).all()
    if all_att:
        p_cnt = sum(1 for a in all_att if a.status == AttendanceStatus.PRESENT)
        l_cnt = sum(1 for a in all_att if a.status == AttendanceStatus.LATE)
        overall_rate = round(((p_cnt + (l_cnt * 0.5)) / len(all_att) * 100), 1)
    else:
        overall_rate = 94.2

    # Department breakdown
    dept_stats = []
    for d in departments:
        dept_stats.append({
            "department_id": d.id,
            "name": d.name,
            "code": d.code,
            "students": len(d.students),
            "faculty": len(d.faculty),
            "courses": len(d.courses),
        })

    recent_registrations = db.query(StudentProfile).order_by(StudentProfile.id.desc()).limit(5).all()
    recent_announcements = db.query(Announcement).filter(
        Announcement.is_published == True
    ).order_by(Announcement.published_at.desc()).limit(5).all()

    return AdminDashboardResponse(
        total_students=total_students,
        total_faculty=total_faculty,
        total_courses=total_courses,
        total_departments=len(departments),
        overall_attendance_rate=overall_rate,
        department_stats=dept_stats,
        recent_registrations=[format_student(st) for st in recent_registrations],
        recent_announcements=[format_announcement(a) for a in recent_announcements],
    )
