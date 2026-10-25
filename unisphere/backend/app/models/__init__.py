from app.models.entities import (
    Base, User, UserRole, Department, StudentProfile, FacultyProfile,
    Course, CourseEnrollment, AttendanceRecord, AttendanceStatus,
    Assignment, AssignmentSubmission, SubmissionStatus,
    Examination, ExamType, ExaminationResult,
    Announcement, AnnouncementCategory, ContactMessage, NotificationPreference
)

__all__ = [
    "Base", "User", "UserRole", "Department", "StudentProfile", "FacultyProfile",
    "Course", "CourseEnrollment", "AttendanceRecord", "AttendanceStatus",
    "Assignment", "AssignmentSubmission", "SubmissionStatus",
    "Examination", "ExamType", "ExaminationResult",
    "Announcement", "AnnouncementCategory", "ContactMessage", "NotificationPreference"
]
