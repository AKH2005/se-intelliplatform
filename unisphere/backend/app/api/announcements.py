from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, require_faculty_or_admin
from app.models.entities import User, UserRole, Announcement, AnnouncementCategory
from app.schemas.schemas import AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse

router = APIRouter(prefix="/announcements", tags=["Announcements"])

def format_announcement(a: Announcement) -> AnnouncementResponse:
    author_name = a.author.full_name if a.author else "UniSphere Administration"
    return AnnouncementResponse(
        id=a.id,
        title=a.title,
        content=a.content,
        category=a.category,
        author_id=a.author_id,
        author_name=author_name,
        published_at=a.published_at,
        is_published=a.is_published,
    )

@router.get("", response_model=List[AnnouncementResponse])
def list_announcements(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Announcement).filter(Announcement.is_published == True)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Announcement.title.ilike(s)) | (Announcement.content.ilike(s)))
    if category and category.upper() in [c.value for c in AnnouncementCategory]:
        query = query.filter(Announcement.category == AnnouncementCategory(category.upper()))

    announcements = query.order_by(Announcement.published_at.desc()).all()
    return [format_announcement(a) for a in announcements]

@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement_details(announcement_id: int, db: Session = Depends(get_db)):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return format_announcement(a)

@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    announcement = Announcement(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        author_id=current_user.id,
        published_at=datetime.utcnow(),
        is_published=payload.is_published
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return format_announcement(announcement)

@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Announcement not found.")

    # Faculty can edit their own, admin can edit any
    if current_user.role == UserRole.FACULTY and a.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit announcements you authored.")

    if payload.title is not None:
        a.title = payload.title
    if payload.content is not None:
        a.content = payload.content
    if payload.category is not None:
        a.category = payload.category
    if payload.is_published is not None:
        a.is_published = payload.is_published

    db.commit()
    db.refresh(a)
    return format_announcement(a)

@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Announcement not found.")

    if current_user.role == UserRole.FACULTY and a.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete announcements you authored.")

    db.delete(a)
    db.commit()
    return None
