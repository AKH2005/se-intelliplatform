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

export interface UserAuthResponse {
  token: string;
  user: {
    email: string;
    name: string;
    level: number;
    role: string;
  };
}

export const shadowApi = {
  async saveSkill(skill: SkillConfig): Promise<boolean> {
    try {
      const res = await fetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skill),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  async login(email: string, password: string): Promise<UserAuthResponse> {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Invalid email or password');
    return res.json();
  },

  async register(email: string, password: string, name: string): Promise<UserAuthResponse> {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });
    if (!res.ok) throw new Error('Registration failed');
    return res.json();
  },

  async logout(): Promise<void> {
    await fetch('/api/auth/logout', { method: 'POST' });
  }
};
