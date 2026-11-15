from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime, timezone

class SkillModel(BaseModel):
    id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    key: str = Field(..., max_length=10)
    damage: int = Field(50, ge=0, le=500)
    energy_cost: int = Field(20, ge=0, le=100)
    cooldown: float = Field(1.0, ge=0.1, le=60.0)
    radius: int = Field(60, ge=10, le=500)
    color: str = Field("#a855f7", max_length=30)
    element: str = Field("VOID", max_length=30)
    desc: Optional[str] = ""

class CombatScoreRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_name: str = Field("Shadow Master", max_length=100)
    score: int = Field(0, ge=0)
    combo_max: float = Field(1.0, ge=1.0)
    level_reached: int = Field(1, ge=1)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
