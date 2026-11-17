import threading
from app.models import SkillModel, CombatScoreRecord

class ShadowMasterRepository:
    def __init__(self):
        self._lock = threading.Lock()
        self._skills = {
            'slash': SkillModel(id='slash', name='Katana Slash', key='Q', damage=45, energy_cost=15, cooldown=0.6, radius=65, color='#c084fc', element='VOID', desc='Rapid crescent slash'),
            'dash': SkillModel(id='dash', name='Shadow Dash', key='W', damage=25, energy_cost=25, cooldown=1.5, radius=120, color='#06b6d4', element='SHADOW', desc='Phases through enemies'),
            'shuriken': SkillModel(id='shuriken', name='Shuriken Volley', key='E', damage=30, energy_cost=20, cooldown=1.0, radius=240, color='#eab308', element='LIGHTNING', desc='Piercing shurikens'),
            'cloak': SkillModel(id='cloak', name='Shadow Cloak', key='R', damage=0, energy_cost=35, cooldown=4.0, radius=0, color='#a855f7', element='VOID', desc='Stealth crit stance'),
            'decoy': SkillModel(id='decoy', name='Shadow Decoy', key='Space', damage=55, energy_cost=40, cooldown=3.5, radius=90, color='#ec4899', element='FIRE', desc='Taunt mirror duplicate'),
        }
        self._scores = []

    def list_skills(self):
        with self._lock:
            return list(self._skills.values())

    def save_skill(self, skill: SkillModel):
        with self._lock:
            self._skills[skill.id] = skill
            return skill

    def list_scores(self):
        with self._lock:
            return list(self._scores)

    def add_score(self, record: CombatScoreRecord):
        with self._lock:
            self._scores.insert(0, record)
            return record

repository = ShadowMasterRepository()
