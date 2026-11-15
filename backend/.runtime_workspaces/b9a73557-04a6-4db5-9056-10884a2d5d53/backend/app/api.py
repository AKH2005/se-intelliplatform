from fastapi import APIRouter, HTTPException
from app.models import SkillModel, CombatScoreRecord
from app.persistence import repository

router = APIRouter(tags=["shadow_master"])

@router.get("/skills", response_model=list[SkillModel])
def list_skills():
    return repository.list_skills()

@router.post("/skills", response_model=SkillModel)
def save_skill(skill: SkillModel):
    return repository.save_skill(skill)

@router.get("/scores", response_model=list[CombatScoreRecord])
def list_scores():
    return repository.list_scores()

@router.post("/scores", response_model=CombatScoreRecord)
def record_score(record: CombatScoreRecord):
    return repository.add_score(record)
