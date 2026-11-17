import threading
from app.models import CarromScore, CarromScoreCreate

class CarromScoreRepository:
    def __init__(self):
        self._lock = threading.Lock()
        self._scores: list[CarromScore] = []

    def list_scores(self) -> list[CarromScore]:
        with self._lock:
            return sorted(self._scores, key=lambda s: s.score, reverse=True)

    def add_score(self, payload: CarromScoreCreate) -> CarromScore:
        with self._lock:
            item = CarromScore(**payload.model_dump())
            self._scores.append(item)
            return item

repository = CarromScoreRepository()
