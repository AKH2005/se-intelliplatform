from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, require_faculty_or_admin, require_student
from app.models.entities import (
    User, UserRole, Course, CourseEnrollment, Assignment, AssignmentSubmission,
    SubmissionStatus, StudentProfile
)
from app.schemas.schemas import (
    AssignmentCreate, AssignmentResponse, SubmissionCreate,
    SubmissionGradeRequest, SubmissionResponse
)

router = APIRouter(prefix="/assignments", tags=["Assignments"])

def format_assignment(a: Assignment, student_id: Optional[int] = None) -> AssignmentResponse:
    now = datetime.utcnow()
    my_sub = None
    if student_id:
        my_sub = next((s for s in a.submissions if s.student_id == student_id), None)

    return AssignmentResponse(
        id=a.id,
        course_id=a.course_id,
        course_code=a.course.code if a.course else None,
        course_title=a.course.title if a.course else None,
        title=a.title,
        description=a.description,
        due_date=a.due_date,
        max_marks=a.max_marks,
        created_at=a.created_at,
        is_overdue=now > a.due_date,
        submission_count=len(a.submissions),
        my_submission_status=my_sub.status if my_sub else None,
        my_marks=my_sub.marks_obtained if my_sub else None,
    )

@router.get("", response_model=List[AssignmentResponse])
def list_assignments(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Assignment).join(Course, Assignment.course_id == Course.id)

    student_id = current_user.student_profile.id if (current_user.role == UserRole.STUDENT and current_user.student_profile) else None

    # If student, list assignments for their enrolled courses
    if current_user.role == UserRole.STUDENT and student_id:
        enrolled_course_ids = [e.course_id for e in current_user.student_profile.enrollments]
        query = query.filter(Assignment.course_id.in_(enrolled_course_ids))
    elif current_user.role == UserRole.FACULTY and current_user.faculty_profile:
        query = query.filter(Course.faculty_id == current_user.faculty_profile.id)

    if course_id:
        query = query.filter(Assignment.course_id == course_id)

    assignments = query.order_by(Assignment.due_date.asc()).all()
    return [format_assignment(a, student_id) for a in assignments]

@router.get("/{assignment_id}")
def get_assignment_details(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    student_id = current_user.student_profile.id if (current_user.role == UserRole.STUDENT and current_user.student_profile) else None

    # Get submissions
    submissions = []
    if current_user.role in (UserRole.FACULTY, UserRole.ADMINISTRATOR):
        for s in a.submissions:
            submissions.append(SubmissionResponse(
                id=s.id,
                assignment_id=s.assignment_id,
                assignment_title=a.title,
                student_id=s.student_id,
                student_name=s.student.user.full_name if s.student and s.student.user else "Unknown",
                submitted_at=s.submitted_at,
                content=s.content,
                file_name=s.file_name,
                marks_obtained=s.marks_obtained,
                feedback=s.feedback,
                status=s.status,
                max_marks=a.max_marks
            ))
    elif student_id:
        my_sub = next((s for s in a.submissions if s.student_id == student_id), None)
        if my_sub:
            submissions.append(SubmissionResponse(
                id=my_sub.id,
                assignment_id=my_sub.assignment_id,
                assignment_title=a.title,
                student_id=my_sub.student_id,
                student_name=current_user.full_name,
                submitted_at=my_sub.submitted_at,
                content=my_sub.content,
                file_name=my_sub.file_name,
                marks_obtained=my_sub.marks_obtained,
                feedback=my_sub.feedback,
                status=my_sub.status,
                max_marks=a.max_marks
            ))

    return {
        "assignment": format_assignment(a, student_id),
        "submissions": submissions,
        "is_faculty": current_user.role in (UserRole.FACULTY, UserRole.ADMINISTRATOR)
    }

@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.id == payload.course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Target course not found.")

    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or c.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only create assignments for your assigned courses.")

    assignment = Assignment(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        max_marks=payload.max_marks
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return format_assignment(assignment)

@router.post("/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: int,
    payload: SubmissionCreate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    student = current_user.student_profile
    if not student:
        raise HTTPException(status_code=400, detail="Student profile not found.")

    # Check enrollment
    enrolled = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == a.course_id,
        CourseEnrollment.student_id == student.id
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in the course for this assignment.")

    # Check existing submission
    existing = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == student.id
    ).first()

    if existing:
        existing.content = payload.content
        existing.file_name = payload.file_name or existing.file_name
        existing.submitted_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        target_sub = existing
    else:
        new_sub = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student.id,
            content=payload.content,
            file_name=payload.file_name or "submission.zip",
            status=SubmissionStatus.SUBMITTED
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        target_sub = new_sub

    return SubmissionResponse(
        id=target_sub.id,
        assignment_id=target_sub.assignment_id,
        assignment_title=a.title,
        student_id=target_sub.student_id,
        student_name=current_user.full_name,
        submitted_at=target_sub.submitted_at,
        content=target_sub.content,
        file_name=target_sub.file_name,
        marks_obtained=target_sub.marks_obtained,
        feedback=target_sub.feedback,
        status=target_sub.status,
        max_marks=a.max_marks
    )

@router.put("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
def grade_submission(
    submission_id: int,
    payload: SubmissionGradeRequest,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    sub = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission record not found.")

    course = sub.assignment.course
    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_profile or course.faculty_id != current_user.faculty_profile.id:
            raise HTTPException(status_code=403, detail="You can only grade submissions for your assigned courses.")

    if payload.marks_obtained < 0 or payload.marks_obtained > sub.assignment.max_marks:
        raise HTTPException(status_code=400, detail=f"Marks must be between 0 and {sub.assignment.max_marks}.")

    sub.marks_obtained = payload.marks_obtained
    sub.feedback = payload.feedback
    sub.status = SubmissionStatus.GRADED
    db.commit()
    db.refresh(sub)

    return SubmissionResponse(
        id=sub.id,
        assignment_id=sub.assignment_id,
        assignment_title=sub.assignment.title,
        student_id=sub.student_id,
        student_name=sub.student.user.full_name,
        submitted_at=sub.submitted_at,
        content=sub.content,
        file_name=sub.file_name,
        marks_obtained=sub.marks_obtained,
        feedback=sub.feedback,
        status=sub.status,
        max_marks=sub.assignment.max_marks
    )
