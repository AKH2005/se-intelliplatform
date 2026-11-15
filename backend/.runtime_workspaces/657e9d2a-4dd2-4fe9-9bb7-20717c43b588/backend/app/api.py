from fastapi import APIRouter, HTTPException, status
from app.models import CarromScore, CarromScoreCreate
from app.persistence import repository

router = APIRouter(prefix="/scores", tags=["scores"])

@router.get("", response_model=list[CarromScore])
def list_scores():
    return repository.list_scores()

@router.post("", response_model=CarromScore, status_code=status.HTTP_201_CREATED)
def submit_score(payload: CarromScoreCreate):
    return repository.add_score(payload)
