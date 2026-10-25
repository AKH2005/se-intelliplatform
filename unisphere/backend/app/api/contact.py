from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import ContactMessage
from app.schemas.schemas import ContactCreate, ContactResponse

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def submit_contact_form(payload: ContactCreate, db: Session = Depends(get_db)):
    msg = ContactMessage(
        name=payload.name.strip(),
        email=payload.email.lower(),
        subject=payload.subject.strip(),
        message=payload.message.strip()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return ContactResponse(
        id=msg.id,
        name=msg.name,
        email=msg.email,
        subject=msg.subject,
        message=msg.message,
        submitted_at=msg.submitted_at,
        is_resolved=msg.is_resolved
    )
