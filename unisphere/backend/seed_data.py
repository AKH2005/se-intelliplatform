"""Idempotent seed script for UniSphere University Management System."""

from datetime import datetime, date, timedelta
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.entities import (
    User, UserRole, Department, StudentProfile, FacultyProfile,
    Course, CourseEnrollment, AttendanceRecord, AttendanceStatus,
    Assignment, AssignmentSubmission, SubmissionStatus,
    Examination, ExamType, ExaminationResult,
    Announcement, AnnouncementCategory, NotificationPreference
)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Departments
        departments_data = [
            {"code": "CS", "name": "Computer Science & Engineering", "description": "Cutting edge computing, software engineering, and AI.", "head_of_department": "Dr. Alan Smith"},
            {"code": "EE", "name": "Electrical & Electronics Engineering", "description": "Power systems, circuits, embedded devices, and robotics.", "head_of_department": "Dr. Elena Rostova"},
            {"code": "BA", "name": "School of Business Administration", "description": "Finance, management, entrepreneurship, and analytics.", "head_of_department": "Prof. David Miller"},
            {"code": "MATH", "name": "Department of Mathematics & Statistics", "description": "Pure mathematics, applied statistics, and discrete modeling.", "head_of_department": "Dr. Clara Oswald"},
        ]

        depts = {}
        for d_info in departments_data:
            existing = db.query(Department).filter(Department.code == d_info["code"]).first()
            if not existing:
                dept = Department(**d_info)
                db.add(dept)
                db.flush()
                depts[d_info["code"]] = dept
            else:
                depts[d_info["code"]] = existing

        # 2. Administrator
        admin = db.query(User).filter(User.email == "admin@unisphere.edu").first()
        if not admin:
            admin = User(
                email="admin@unisphere.edu",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Chancellor Victoria Sterling",
                role=UserRole.ADMINISTRATOR,
                is_active=True
            )
            db.add(admin)
            db.flush()
            db.add(NotificationPreference(user_id=admin.id))

        # 3. Faculty Members
        faculty_data = [
            {
                "email": "prof.smith@unisphere.edu",
                "name": "Dr. Alan Smith",
                "dept": "CS",
                "employee_id": "FAC-CS-001",
                "designation": "Associate Professor",
                "office": "Turing Hall 402",
                "phone": "+1 (555) 019-2831",
                "qual": "Ph.D. in Computer Science (MIT)"
            },
            {
                "email": "dr.elena@unisphere.edu",
                "name": "Dr. Elena Rostova",
                "dept": "EE",
                "employee_id": "FAC-EE-001",
                "designation": "Professor & Dept Chair",
                "office": "Tesla Labs 210",
                "phone": "+1 (555) 019-4492",
                "qual": "Ph.D. in Robotics (Stanford)"
            }
        ]

        faculty_records = {}
        for f_info in faculty_data:
            u = db.query(User).filter(User.email == f_info["email"]).first()
            if not u:
                u = User(
                    email=f_info["email"],
                    hashed_password=get_password_hash("FacultyPass123!"),
                    full_name=f_info["name"],
                    role=UserRole.FACULTY,
                    is_active=True
                )
                db.add(u)
                db.flush()
                db.add(NotificationPreference(user_id=u.id))

                f_profile = FacultyProfile(
                    user_id=u.id,
                    employee_id=f_info["employee_id"],
                    department_id=depts[f_info["dept"]].id,
                    designation=f_info["designation"],
                    office_room=f_info["office"],
                    phone=f_info["phone"],
                    qualification=f_info["qual"]
                )
                db.add(f_profile)
                db.flush()
                faculty_records[f_info["email"]] = f_profile
            else:
                faculty_records[f_info["email"]] = u.faculty_profile

        # 4. Students
        students_data = [
            {
                "email": "student.alex@unisphere.edu",
                "name": "Alex Rivera",
                "dept": "CS",
                "sid": "CS-2024-001",
                "year": 3,
                "semester": 5,
                "gpa": 3.85,
                "phone": "+1 (555) 123-4567",
                "address": "402 North Quad Dorms, Campus West",
                "emergency": "+1 (555) 987-6543 (Mother: Maria Rivera)"
            },
            {
                "email": "student.sarah@unisphere.edu",
                "name": "Sarah Chen",
                "dept": "CS",
                "sid": "CS-2024-002",
                "year": 2,
                "semester": 3,
                "gpa": 3.92,
                "phone": "+1 (555) 234-5678",
                "address": "12 University Terrace, Apt 3B",
                "emergency": "+1 (555) 876-5432 (Father: David Chen)"
            },
            {
                "email": "student.marcus@unisphere.edu",
                "name": "Marcus Brody",
                "dept": "EE",
                "sid": "EE-2024-001",
                "year": 3,
                "semester": 5,
                "gpa": 3.68,
                "phone": "+1 (555) 345-6789",
                "address": "88 College Way, Suite 12",
                "emergency": "+1 (555) 765-4321 (Sister: Laura Brody)"
            }
        ]

        student_records = {}
        for s_info in students_data:
            u = db.query(User).filter(User.email == s_info["email"]).first()
            if not u:
                u = User(
                    email=s_info["email"],
                    hashed_password=get_password_hash("StudentPass123!"),
                    full_name=s_info["name"],
                    role=UserRole.STUDENT,
                    is_active=True
                )
                db.add(u)
                db.flush()
                db.add(NotificationPreference(user_id=u.id))

                s_profile = StudentProfile(
                    user_id=u.id,
                    student_id_number=s_info["sid"],
                    department_id=depts[s_info["dept"]].id,
                    year=s_info["year"],
                    semester=s_info["semester"],
                    gpa=s_info["gpa"],
                    phone=s_info["phone"],
                    address=s_info["address"],
                    emergency_contact=s_info["emergency"]
                )
                db.add(s_profile)
                db.flush()
                student_records[s_info["email"]] = s_profile
            else:
                student_records[s_info["email"]] = u.student_profile

        # 5. Courses
        courses_data = [
            {
                "code": "CS101",
                "title": "Introduction to Computer Science & Python",
                "desc": "Foundational computing concepts, algorithmic problem solving, procedural programming, and modern software paradigms.",
                "credits": 4,
                "dept": "CS",
                "faculty": faculty_records["prof.smith@unisphere.edu"].id,
                "semester": "Fall 2026",
                "schedule": "Mon/Wed 09:00 - 10:30 AM",
                "capacity": 60
            },
            {
                "code": "CS201",
                "title": "Data Structures & Algorithm Design",
                "desc": "In-depth study of linked lists, balanced trees, hash tables, graphs, asymptotic complexity analysis, and dynamic programming.",
                "credits": 4,
                "dept": "CS",
                "faculty": faculty_records["prof.smith@unisphere.edu"].id,
                "semester": "Fall 2026",
                "schedule": "Tue/Thu 11:00 AM - 12:30 PM",
                "capacity": 45
            },
            {
                "code": "CS305",
                "title": "Database Systems & Distributed Storage",
                "desc": "Relational calculus, SQL querying, indexing, transaction ACID properties, distributed replication, and modern NoSQL paradigms.",
                "credits": 3,
                "dept": "CS",
                "faculty": faculty_records["prof.smith@unisphere.edu"].id,
                "semester": "Fall 2026",
                "schedule": "Fri 01:00 - 04:00 PM",
                "capacity": 40
            },
            {
                "code": "EE101",
                "title": "Circuit Theory & Electronic Analysis",
                "desc": "Kirchhoff laws, nodal analysis, AC/DC circuit analysis, operational amplifiers, and laboratory signal instrumentation.",
                "credits": 4,
                "dept": "EE",
                "faculty": faculty_records["dr.elena@unisphere.edu"].id,
                "semester": "Fall 2026",
                "schedule": "Mon/Wed 02:00 - 03:30 PM",
                "capacity": 35
            }
        ]

        course_records = {}
        for c_info in courses_data:
            existing = db.query(Course).filter(Course.code == c_info["code"]).first()
            if not existing:
                c = Course(
                    code=c_info["code"],
                    title=c_info["title"],
                    description=c_info["desc"],
                    credits=c_info["credits"],
                    department_id=depts[c_info["dept"]].id,
                    faculty_id=c_info["faculty"],
                    semester=c_info["semester"],
                    schedule=c_info["schedule"],
                    max_capacity=c_info["capacity"]
                )
                db.add(c)
                db.flush()
                course_records[c_info["code"]] = c
            else:
                course_records[c_info["code"]] = existing

        # 6. Enrollments
        enrollment_pairs = [
            ("student.alex@unisphere.edu", "CS101"),
            ("student.alex@unisphere.edu", "CS201"),
            ("student.alex@unisphere.edu", "CS305"),
            ("student.sarah@unisphere.edu", "CS101"),
            ("student.sarah@unisphere.edu", "CS201"),
            ("student.marcus@unisphere.edu", "EE101"),
            ("student.marcus@unisphere.edu", "CS101"),
        ]

        for s_email, c_code in enrollment_pairs:
            st = student_records[s_email]
            c = course_records[c_code]
            exists = db.query(CourseEnrollment).filter(
                CourseEnrollment.course_id == c.id,
                CourseEnrollment.student_id == st.id
            ).first()
            if not exists:
                db.add(CourseEnrollment(course_id=c.id, student_id=st.id))

        db.flush()

        # 7. Attendance Records (Last 5 class sessions)
        today = date.today()
        dates = [today - timedelta(days=i * 2) for i in range(1, 6)]
        for d in dates:
            for s_email, c_code in [("student.alex@unisphere.edu", "CS101"), ("student.sarah@unisphere.edu", "CS101"), ("student.alex@unisphere.edu", "CS201")]:
                st = student_records[s_email]
                c = course_records[c_code]
                exists = db.query(AttendanceRecord).filter(
                    AttendanceRecord.course_id == c.id,
                    AttendanceRecord.student_id == st.id,
                    AttendanceRecord.date == d
                ).first()
                if not exists:
                    db.add(AttendanceRecord(
                        course_id=c.id,
                        student_id=st.id,
                        date=d,
                        status=AttendanceStatus.PRESENT,
                        notes="On time, active participation."
                    ))

        # 8. Assignments & Submissions
        cs201 = course_records["CS201"]
        existing_a1 = db.query(Assignment).filter(Assignment.title == "Project 1: Balanced AVL Tree Implementation").first()
        if not existing_a1:
            a1 = Assignment(
                course_id=cs201.id,
                title="Project 1: Balanced AVL Tree Implementation",
                description="Implement a generic, self-balancing AVL Tree in Python with insertion, deletion, and rotation unit tests.",
                due_date=datetime.utcnow() + timedelta(days=7),
                max_marks=100.0
            )
            db.add(a1)
            db.flush()

            # Alex submitted
            alex_st = student_records["student.alex@unisphere.edu"]
            db.add(AssignmentSubmission(
                assignment_id=a1.id,
                student_id=alex_st.id,
                submitted_at=datetime.utcnow() - timedelta(days=1),
                content="Full AVL tree implementation with O(log n) rotations and 100% test coverage.",
                file_name="alex_rivera_avl_tree.zip",
                marks_obtained=96.0,
                feedback="Excellent work on double rotations and edge-case handling.",
                status=SubmissionStatus.GRADED
            ))

        # 9. Examinations & Results
        cs101 = course_records["CS101"]
        existing_exam = db.query(Examination).filter(Examination.title == "CS101 Midterm Examination").first()
        if not existing_exam:
            exam1 = Examination(
                course_id=cs101.id,
                title="CS101 Midterm Examination",
                exam_type=ExamType.MIDTERM,
                exam_date=today - timedelta(days=10),
                start_time="10:00 AM",
                duration_minutes=90,
                max_marks=100.0,
                room_number="Auditorium B-201"
            )
            db.add(exam1)
            db.flush()

            alex_st = student_records["student.alex@unisphere.edu"]
            sarah_st = student_records["student.sarah@unisphere.edu"]
            db.add(ExaminationResult(
                examination_id=exam1.id,
                student_id=alex_st.id,
                marks_obtained=94.5,
                grade="A",
                remarks="Outstanding understanding of recursion and computational complexity."
            ))
            db.add(ExaminationResult(
                examination_id=exam1.id,
                student_id=sarah_st.id,
                marks_obtained=98.0,
                grade="A+",
                remarks="Top score in class. Flawless syntax and logic."
            ))

        # Upcoming exam
        existing_final = db.query(Examination).filter(Examination.title == "CS201 Comprehensive Final").first()
        if not existing_final:
            db.add(Examination(
                course_id=cs201.id,
                title="CS201 Comprehensive Final",
                exam_type=ExamType.FINAL,
                exam_date=today + timedelta(days=14),
                start_time="09:00 AM",
                duration_minutes=120,
                max_marks=100.0,
                room_number="Science Hall 105"
            ))

        # 10. Announcements
        announcements_data = [
            {
                "title": "Fall 2026 Midterm Examination Schedule Published",
                "content": "The midterm examination timetable has been finalized. Students are encouraged to verify room allocations and start times on their student dashboard.",
                "category": AnnouncementCategory.ACADEMIC
            },
            {
                "title": "Annual University Hackathon & Innovation Expo",
                "content": "UniSphere Innovation Club is hosting the 2026 Fall Hackathon this weekend. Over $20,000 in grand prizes. Register your team by Friday.",
                "category": AnnouncementCategory.EVENT
            },
            {
                "title": "Campus Library Extended Hours for Finals Preparation",
                "content": "Beginning next Monday, Turing Memorial Library will remain open 24/7 to support students throughout the examination period.",
                "category": AnnouncementCategory.GENERAL
            }
        ]

        for a_data in announcements_data:
            exists = db.query(Announcement).filter(Announcement.title == a_data["title"]).first()
            if not exists:
                db.add(Announcement(
                    title=a_data["title"],
                    content=a_data["content"],
                    category=a_data["category"],
                    author_id=admin.id,
                    published_at=datetime.utcnow() - timedelta(days=1),
                    is_published=True
                ))

        db.commit()
        print("UniSphere database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
