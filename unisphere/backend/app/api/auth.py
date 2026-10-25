from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.deps import get_current_user
from app.models.entities import User, UserRole, StudentProfile, FacultyProfile, NotificationPreference
from app.schemas.schemas import (
    LoginRequest, TokenResponse, RegisterStudentRequest, UserResponse,
    ChangePasswordRequest, UpdateProfileRequest, ForgotPasswordRequest,
    ForgotPasswordResponse, ResetPasswordRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

def format_user_response(user: User) -> UserResponse:
    student_id = user.student_profile.id if user.student_profile else None
    faculty_id = user.faculty_profile.id if user.faculty_profile else None
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        student_profile_id=student_id,
        faculty_profile_id=faculty_id,
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact the administrator."
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=format_user_response(user)
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterStudentRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Check student ID uniqueness
    existing_sid = db.query(StudentProfile).filter(StudentProfile.student_id_number == payload.student_id_number).first()
    if existing_sid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This student ID number is already registered in the system."
        )

    # Public registration strictly restricted to STUDENT role
    user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.STUDENT,
        is_active=True
    )
    db.add(user)
    db.flush()

    student_profile = StudentProfile(
        user_id=user.id,
        student_id_number=payload.student_id_number,
        department_id=payload.department_id,
        year=payload.year,
        semester=payload.semester,
        phone=payload.phone,
        address=payload.address,
        gpa=3.5
    )
    db.add(student_profile)

    prefs = NotificationPreference(user_id=user.id)
    db.add(prefs)

    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=format_user_response(user)
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return format_user_response(current_user)

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        # Return generic safe message to avoid email enumeration
        return ForgotPasswordResponse(
            message="If this email is registered in UniSphere, instructions with a recovery token have been generated."
        )
    # Generate password reset token
    reset_token = create_access_token({"sub": str(user.id), "type": "reset"})
    return ForgotPasswordResponse(
        message="Recovery token generated successfully. In development mode, use this token on the reset screen.",
        reset_token=reset_token
    )

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    data = decode_access_token(payload.reset_token)
    if not data or data.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    user_id = data.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "SUCCESS", "message": "Password reset successfully. You can now log in."}

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match our records."
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "SUCCESS", "message": "Password updated successfully."}

@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Role cannot be modified by user
    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()

    if current_user.role == UserRole.STUDENT and current_user.student_profile:
        if payload.phone is not None:
            current_user.student_profile.phone = payload.phone
        if payload.address is not None:
            current_user.student_profile.address = payload.address
        if payload.emergency_contact is not None:
            current_user.student_profile.emergency_contact = payload.emergency_contact

    elif current_user.role == UserRole.FACULTY and current_user.faculty_profile:
        if payload.phone is not None:
            current_user.faculty_profile.phone = payload.phone

    # Notification preferences
    if not current_user.notifications:
        current_user.notifications = NotificationPreference(user_id=current_user.id)
        db.add(current_user.notifications)

    if payload.email_notifications is not None:
        current_user.notifications.email_notifications = payload.email_notifications
    if payload.assignment_reminders is not None:
        current_user.notifications.assignment_reminders = payload.assignment_reminders
    if payload.exam_alerts is not None:
        current_user.notifications.exam_alerts = payload.exam_alerts
    if payload.announcement_updates is not None:
        current_user.notifications.announcement_updates = payload.announcement_updates

    db.commit()
    db.refresh(current_user)
    return format_user_response(current_user)
