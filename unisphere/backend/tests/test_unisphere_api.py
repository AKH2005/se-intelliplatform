import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. Health check & root
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# 2. Public Contact Form
def test_submit_contact_form():
    payload = {
        "name": "Jordan Lee",
        "email": "jordan.lee@example.com",
        "subject": "Admissions Inquiry for Fall 2027",
        "message": "Hello, I would like to know more about the scholarship opportunities for the Computer Science program."
    }
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jordan Lee"
    assert data["is_resolved"] is False

def test_contact_form_validation():
    # Message too short
    payload = {
        "name": "J",
        "email": "invalid-email",
        "subject": "Hi",
        "message": "Short"
    }
    response = client.post("/api/contact", json=payload)
    assert response.status_code == 422  # Validation error

# 3. Public Course Catalogue
def test_public_course_catalogue():
    response = client.get("/api/courses")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) >= 4
    codes = [c["code"] for c in courses]
    assert "CS101" in codes
    assert "CS201" in codes

def test_public_course_details():
    # First get course id of CS101
    list_res = client.get("/api/courses?search=CS101")
    assert list_res.status_code == 200
    cs101_id = list_res.json()[0]["id"]

    detail_res = client.get(f"/api/courses/{cs101_id}")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["course"]["code"] == "CS101"
    assert "enrolled_students" in data
    assert len(data["enrolled_students"]) > 0

def test_invalid_course_id():
    response = client.get("/api/courses/999999")
    assert response.status_code == 404

# 4. Authentication: Admin, Faculty, Student
def test_admin_login():
    response = client.post("/api/auth/login", json={
        "email": "admin@unisphere.edu",
        "password": "AdminPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMINISTRATOR"

def test_faculty_login():
    response = client.post("/api/auth/login", json={
        "email": "prof.smith@unisphere.edu",
        "password": "FacultyPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "FACULTY"

def test_student_login():
    response = client.post("/api/auth/login", json={
        "email": "student.alex@unisphere.edu",
        "password": "StudentPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "STUDENT"

def test_login_invalid_credentials():
    response = client.post("/api/auth/login", json={
        "email": "admin@unisphere.edu",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

# 5. Role-based Access Control (RBAC) & Journey F
def test_student_cannot_access_admin_dashboard():
    # Student login
    login_res = client.post("/api/auth/login", json={
        "email": "student.alex@unisphere.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access admin dashboard
    admin_res = client.get("/api/dashboard/admin", headers=headers)
    assert admin_res.status_code == 403  # Forbidden!

def test_student_cannot_access_faculty_dashboard():
    login_res = client.post("/api/auth/login", json={
        "email": "student.alex@unisphere.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/dashboard/faculty", headers=headers)
    assert res.status_code == 403

def test_unauthenticated_protected_route():
    response = client.get("/api/dashboard/student")
    assert response.status_code == 401

# 6. Student Dashboard & Academic Details
def test_student_dashboard():
    login_res = client.post("/api/auth/login", json={
        "email": "student.alex@unisphere.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    dash_res = client.get("/api/dashboard/student", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert data["student_profile"]["full_name"] == "Alex Rivera"
    assert len(data["enrolled_courses"]) >= 3
    assert data["attendance_summary"]["attendance_percentage"] > 0
    assert data["overall_gpa"] == 3.85

# 7. Admin Student CRUD Workflow (Journey B)
def test_admin_add_and_edit_student():
    # Admin login
    admin_token = client.post("/api/auth/login", json={
        "email": "admin@unisphere.edu",
        "password": "AdminPass123!"
    }).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Add student
    create_payload = {
        "email": "new.student.test@unisphere.edu",
        "password": "StudentPass123!",
        "full_name": "Oliver Queen",
        "department_id": 1,
        "student_id_number": "CS-TEST-999",
        "year": 1,
        "semester": 1,
        "gpa": 3.75,
        "phone": "+1 (555) 000-1111",
        "address": "Star City Campus Dorms"
    }
    create_res = client.post("/api/students", json=create_payload, headers=admin_headers)
    assert create_res.status_code == 201
    new_student = create_res.json()
    new_student_id = new_student["id"]

    # Open details
    detail_res = client.get(f"/api/students/{new_student_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["student"]["full_name"] == "Oliver Queen"

    # Edit student
    update_res = client.put(f"/api/students/{new_student_id}", json={
        "full_name": "Oliver Queen (Honor Student)",
        "gpa": 3.95
    }, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Oliver Queen (Honor Student)"
    assert update_res.json()["gpa"] == 3.95

    # Clean up (Delete student)
    del_res = client.delete(f"/api/students/{new_student_id}", headers=admin_headers)
    assert del_res.status_code == 204

# 8. Attendance Marking & Persistence (Journey C)
def test_faculty_attendance_flow():
    # Faculty login
    fac_token = client.post("/api/auth/login", json={
        "email": "prof.smith@unisphere.edu",
        "password": "FacultyPass123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {fac_token}"}

    # CS101 Course ID
    cs101_id = client.get("/api/courses?search=CS101").json()[0]["id"]

    # Get attendance sheet
    sheet_res = client.get(f"/api/attendance/course/{cs101_id}?date_val=2026-10-24", headers=headers)
    assert sheet_res.status_code == 200
    roster = sheet_res.json()["roster"]
    assert len(roster) > 0

    student1_id = roster[0]["student_id"]

    # Save attendance
    batch_payload = {
        "course_id": cs101_id,
        "date": "2026-10-24",
        "records": [
            {"student_id": student1_id, "status": "PRESENT", "notes": "Verified in laboratory"}
        ]
    }
    save_res = client.post("/api/attendance/batch", json=batch_payload, headers=headers)
    assert save_res.status_code == 200
    assert save_res.json()["saved_count"] == 1

    # Re-open attendance on that date and verify persistence
    reopen_res = client.get(f"/api/attendance/course/{cs101_id}?date_val=2026-10-24", headers=headers)
    assert reopen_res.status_code == 200
    updated_roster = reopen_res.json()["roster"]
    match = next(r for r in updated_roster if r["student_id"] == student1_id)
    assert match["status"] == "PRESENT"
    assert match["notes"] == "Verified in laboratory"
    assert match["is_saved"] is True

# 9. Assignment Submission & Review (Journey D)
def test_student_submit_assignment_flow():
    # Student login
    st_token = client.post("/api/auth/login", json={
        "email": "student.sarah@unisphere.edu",
        "password": "StudentPass123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {st_token}"}

    # List assignments
    assignments = client.get("/api/assignments", headers=headers).json()
    assert len(assignments) > 0
    target_assign = assignments[0]

    # Submit work
    sub_payload = {
        "content": "Sarah Chen AVL Tree Implementation: Complete rotations with balance factor logic.",
        "file_name": "sarah_chen_avl.py"
    }
    sub_res = client.post(f"/api/assignments/{target_assign['id']}/submit", json=sub_payload, headers=headers)
    assert sub_res.status_code == 201
    assert sub_res.json()["status"] == "SUBMITTED"
    assert sub_res.json()["file_name"] == "sarah_chen_avl.py"

# 10. Examination Results & Student Isolation (Journey E)
def test_exam_marks_entry_and_student_results():
    # Faculty login
    fac_token = client.post("/api/auth/login", json={
        "email": "prof.smith@unisphere.edu",
        "password": "FacultyPass123!"
    }).json()["access_token"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    # Get CS101 Midterm Exam ID
    exams = client.get("/api/examinations", headers=fac_headers).json()
    midterm = next(e for e in exams if "Midterm" in e["title"])

    # Faculty enters marks
    marks_payload = {
        "examination_id": midterm["id"],
        "results": [
            {"student_id": 1, "marks_obtained": 97.5, "grade": "A+", "remarks": "Excellent conceptual clarity"}
        ]
    }
    enter_res = client.post(f"/api/examinations/{midterm['id']}/results/batch", json=marks_payload, headers=fac_headers)
    assert enter_res.status_code == 200

    # Student login (Alex, student_id = 1)
    alex_token = client.post("/api/auth/login", json={
        "email": "student.alex@unisphere.edu",
        "password": "StudentPass123!"
    }).json()["access_token"]
    alex_headers = {"Authorization": f"Bearer {alex_token}"}

    # Student views own results
    results_res = client.get("/api/examinations/results/student/1", headers=alex_headers)
    assert results_res.status_code == 200
    alex_results = results_res.json()
    assert len(alex_results) > 0
    assert any(r["marks_obtained"] == 97.5 for r in alex_results)

    # Student cannot view another student's results
    forbidden_res = client.get("/api/examinations/results/student/2", headers=alex_headers)
    assert forbidden_res.status_code == 403
