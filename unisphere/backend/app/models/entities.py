import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    ADMINISTRATOR = "ADMINISTRATOR"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"

class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"

class ExamType(str, enum.Enum):
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    QUIZ = "QUIZ"

class AnnouncementCategory(str, enum.Enum):
    ACADEMIC = "ACADEMIC"
    GENERAL = "GENERAL"
    EVENT = "EVENT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("FacultyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    announcements = relationship("Announcement", back_populates="author")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    head_of_department = Column(String(255), nullable=True)

    students = relationship("StudentProfile", back_populates="department")
    faculty = relationship("FacultyProfile", back_populates="department")
    courses = relationship("Course", back_populates="department")

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id_number = Column(String(50), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    year = Column(Integer, default=1)
    semester = Column(Integer, default=1)
    gpa = Column(Float, default=3.5)
    phone = Column(String(30), nullable=True)
    address = Column(String(255), nullable=True)
    emergency_contact = Column(String(255), nullable=True)

    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    enrollments = relationship("CourseEnrollment", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    submissions = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    exam_results = relationship("ExaminationResult", back_populates="student", cascade="all, delete-orphan")

class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Assistant Professor")
    office_room = Column(String(50), nullable=True)
    phone = Column(String(30), nullable=True)
    qualification = Column(String(100), nullable=True)

    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty")
    courses = relationship("Course", back_populates="instructor")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id"), nullable=True)
    semester = Column(String(50), default="Fall 2026")
    schedule = Column(String(100), default="Mon/Wed 10:00 - 11:30 AM")
    max_capacity = Column(Integer, default=50)

    department = relationship("Department", back_populates="courses")
    instructor = relationship("FacultyProfile", back_populates="courses")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="course", cascade="all, delete-orphan")

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="ENROLLED")

    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_course_student_enrollment"),)

    course = relationship("Course", back_populates="enrollments")
    student = relationship("StudentProfile", back_populates="enrollments")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False)
    notes = Column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("course_id", "student_id", "date", name="uq_attendance_course_student_date"),)

    course = relationship("Course", back_populates="attendance_records")
    student = relationship("StudentProfile", back_populates="attendance_records")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    max_marks = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    content = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    marks_obtained = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.SUBMITTED, nullable=False)

    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student_submission"),)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("StudentProfile", back_populates="submissions")

class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    exam_type = Column(Enum(ExamType), default=ExamType.FINAL, nullable=False)
    exam_date = Column(Date, nullable=False)
    start_time = Column(String(20), default="09:00 AM")
    duration_minutes = Column(Integer, default=120)
    max_marks = Column(Float, default=100.0)
    room_number = Column(String(50), default="Hall A-101")
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="examinations")
    results = relationship("ExaminationResult", back_populates="examination", cascade="all, delete-orphan")

class ExaminationResult(Base):
    __tablename__ = "examination_results"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    marks_obtained = Column(Float, nullable=False)
    grade = Column(String(5), default="A")
    remarks = Column(String(255), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("examination_id", "student_id", name="uq_exam_student_result"),)

    examination = relationship("Examination", back_populates="results")
    student = relationship("StudentProfile", back_populates="exam_results")

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(Enum(AnnouncementCategory), default=AnnouncementCategory.GENERAL, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    is_published = Column(Boolean, default=True)

    author = relationship("User", back_populates="announcements")

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_notifications = Column(Boolean, default=True)
    assignment_reminders = Column(Boolean, default=True)
    exam_alerts = Column(Boolean, default=True)
    announcement_updates = Column(Boolean, default=True)

    user = relationship("User", back_populates="notifications")
