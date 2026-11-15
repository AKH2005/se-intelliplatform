export interface SkillConfig {
  id: string;
  name: string;
  key: string;
  damage: number;
  energyCost: number;
  cooldown: number;
  radius: number;
  color: string;
  element: string;
  desc: string;
}

export const shadowApi = {
  async getSkills(): Promise<SkillConfig[]> {
    try {
      const res = await fetch('/api/skills');
      return res.ok ? await res.json() : [];
    } catch { return []; }
  },
  async saveSkill(skill: SkillConfig): Promise<boolean> {
    try {
      const res = await fetch('/api/skills', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(skill) });
      return res.ok;
    } catch { return false; }
  },
  async recordScore(score: number): Promise<boolean> {
    try {
      const res = await fetch('/api/scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ score }) });
      return res.ok;
    } catch { return false; }
  }
};
