from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime, timezone

class CarromScoreBase(BaseModel):
    player_name: str = Field(..., max_length=100)
    score: int = Field(0, ge=0)
    game: Optional[str] = "carrom"

class CarromScoreCreate(CarromScoreBase):
    pass

class CarromScore(CarromScoreBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
