export interface CarromScore {
  id?: string;
  player_name: string;
  score: number;
  game?: string;
  created_at?: string;
}

export const scoreApi = {
  async getScores(): Promise<CarromScore[]> {
    try {
      const res = await fetch('/api/scores');
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  },
  async submitScore(data: CarromScore): Promise<CarromScore | null> {
    try {
      const res = await fetch('/api/scores', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }
};
