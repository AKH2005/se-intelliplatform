from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user

def require_roles(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation restricted to roles: {[r.value for r in allowed_roles]}. Your role: {current_user.role.value}"
            )
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(require_roles(UserRole.ADMINISTRATOR))) -> User:
    return current_user

def require_faculty_or_admin(current_user: User = Depends(require_roles(UserRole.FACULTY, UserRole.ADMINISTRATOR))) -> User:
    return current_user

def require_student(current_user: User = Depends(require_roles(UserRole.STUDENT))) -> User:
    return current_user
