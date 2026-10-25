from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from app.models.entities import (
    UserRole, AttendanceStatus, SubmissionStatus, ExamType, AnnouncementCategory
)

# ----------------- AUTH SCHEMAS -----------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterStudentRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)
    department_id: int
    student_id_number: str
    year: int = 1
    semester: int = 1
    phone: Optional[str] = None
    address: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    email_notifications: Optional[bool] = None
    assignment_reminders: Optional[bool] = None
    exam_alerts: Optional[bool] = None
    announcement_updates: Optional[bool] = None

class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3)

class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=6)

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    student_profile_id: Optional[int] = None
    faculty_profile_id: Optional[int] = None

    class Config:
        from_attributes = True

# ----------------- DEPARTMENT SCHEMAS -----------------
class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    head_of_department: Optional[str] = None

class DepartmentResponse(DepartmentCreate):
    id: int
    student_count: Optional[int] = 0
    faculty_count: Optional[int] = 0
    course_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- STUDENT SCHEMAS -----------------
class StudentCreate(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(default="student123", min_length=6)
    full_name: str
    department_id: int
    student_id_number: str
    year: int = 1
    semester: int = 1
    gpa: float = 3.5
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[int] = None
    year: Optional[int] = None
    semester: Optional[int] = None
    gpa: Optional[float] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    user_id: int
    student_id_number: str
    full_name: str
    email: str
    department_id: int
    department_name: Optional[str] = None
    year: int
    semester: int
    gpa: float
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- FACULTY SCHEMAS -----------------
class FacultyCreate(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(default="faculty123", min_length=6)
    full_name: str
    department_id: int
    employee_id: str
    designation: str = "Assistant Professor"
    office_room: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None

class FacultyUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    office_room: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None

class FacultyResponse(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    email: str
    department_id: int
    department_name: Optional[str] = None
    designation: str
    office_room: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    assigned_course_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- COURSE SCHEMAS -----------------
class CourseCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    credits: int = 3
    department_id: int
    faculty_id: Optional[int] = None
    semester: str = "Fall 2026"
    schedule: str = "Mon/Wed 10:00 - 11:30 AM"
    max_capacity: int = 50

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    department_id: Optional[int] = None
    faculty_id: Optional[int] = None
    semester: Optional[str] = None
    schedule: Optional[str] = None
    max_capacity: Optional[int] = None

class CourseResponse(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    credits: int
    department_id: int
    department_name: Optional[str] = None
    faculty_id: Optional[int] = None
    instructor_name: Optional[str] = None
    semester: str
    schedule: str
    max_capacity: int
    enrolled_count: int = 0

    class Config:
        from_attributes = True

class EnrollmentCreate(BaseModel):
    course_id: int
    student_id: int

# ----------------- ATTENDANCE SCHEMAS -----------------
class AttendanceItem(BaseModel):
    student_id: int
    status: AttendanceStatus
    notes: Optional[str] = None

class AttendanceBatchSave(BaseModel):
    course_id: int
    date: date
    records: List[AttendanceItem]

class AttendanceRecordResponse(BaseModel):
    id: int
    course_id: int
    course_code: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    student_number: Optional[str] = None
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class AttendanceSummaryResponse(BaseModel):
    total_classes: int
    present_count: int
    absent_count: int
    late_count: int
    attendance_percentage: float

# ----------------- ASSIGNMENT SCHEMAS -----------------
class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    max_marks: float = 100.0

class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: datetime
    max_marks: float
    created_at: datetime
    is_overdue: bool = False
    submission_count: int = 0
    my_submission_status: Optional[SubmissionStatus] = None
    my_marks: Optional[float] = None

    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    content: str
    file_name: Optional[str] = None

class SubmissionGradeRequest(BaseModel):
    marks_obtained: float
    feedback: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    assignment_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    submitted_at: datetime
    content: Optional[str] = None
    file_name: Optional[str] = None
    marks_obtained: Optional[float] = None
    feedback: Optional[str] = None
    status: SubmissionStatus
    max_marks: Optional[float] = 100.0

    class Config:
        from_attributes = True

# ----------------- EXAMINATION SCHEMAS -----------------
class ExaminationCreate(BaseModel):
    course_id: int
    title: str
    exam_type: ExamType = ExamType.FINAL
    exam_date: date
    start_time: str = "09:00 AM"
    duration_minutes: int = 120
    max_marks: float = 100.0
    room_number: str = "Hall A-101"

class ExaminationResponse(BaseModel):
    id: int
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    title: str
    exam_type: ExamType
    exam_date: date
    start_time: str
    duration_minutes: int
    max_marks: float
    room_number: str
    is_past: bool = False
    result_count: int = 0

    class Config:
        from_attributes = True

class ResultEntryItem(BaseModel):
    student_id: int
    marks_obtained: float
    grade: str = "A"
    remarks: Optional[str] = None

class ResultBatchEntry(BaseModel):
    examination_id: int
    results: List[ResultEntryItem]

class ResultResponse(BaseModel):
    id: int
    examination_id: int
    exam_title: Optional[str] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    marks_obtained: float
    max_marks: Optional[float] = 100.0
    grade: str
    remarks: Optional[str] = None
    recorded_at: datetime

    class Config:
        from_attributes = True

# ----------------- ANNOUNCEMENT SCHEMAS -----------------
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    category: AnnouncementCategory = AnnouncementCategory.GENERAL
    is_published: bool = True

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[AnnouncementCategory] = None
    is_published: Optional[bool] = None

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    category: AnnouncementCategory
    author_id: int
    author_name: Optional[str] = None
    published_at: datetime
    is_published: bool

    class Config:
        from_attributes = True

# ----------------- CONTACT FORM SCHEMAS -----------------
class ContactCreate(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    subject: str = Field(min_length=3)
    message: str = Field(min_length=10)

class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    submitted_at: datetime
    is_resolved: bool

    class Config:
        from_attributes = True

# ----------------- DASHBOARD SCHEMAS -----------------
class StudentDashboardResponse(BaseModel):
    student_profile: StudentResponse
    enrolled_courses: List[CourseResponse]
    attendance_summary: AttendanceSummaryResponse
    upcoming_examinations: List[ExaminationResponse]
    pending_assignments: List[AssignmentResponse]
    recent_announcements: List[AnnouncementResponse]
    recent_results: List[ResultResponse]
    overall_gpa: float

class FacultyDashboardResponse(BaseModel):
    faculty_profile: FacultyResponse
    assigned_courses: List[CourseResponse]
    total_students: int
    pending_grading_count: int
    recent_attendance_count: int
    upcoming_deadlines: List[AssignmentResponse]
    recent_announcements: List[AnnouncementResponse]

class AdminDashboardResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_courses: int
    total_departments: int
    overall_attendance_rate: float
    department_stats: List[dict]
    recent_registrations: List[StudentResponse]
    recent_announcements: List[AnnouncementResponse]
