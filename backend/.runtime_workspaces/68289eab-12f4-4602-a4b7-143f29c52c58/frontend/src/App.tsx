import React, { useState } from 'react';
import CombatArena from './components/CombatArena';
import SkillDesigner from './components/SkillDesigner';
import StatsPanel from './components/StatsPanel';
import LoginPage, { UserProfile } from './components/LoginPage';
import { shadowApi, SkillConfig } from './services/api';

const DEFAULT_SKILLS: SkillConfig[] = [
  { id: 'slash', name: 'Katana Slash', key: 'Q', damage: 45, energyCost: 15, cooldown: 0.6, radius: 65, color: '#c084fc', element: 'VOID', desc: 'Rapid crescent slash that strikes nearby foes in an arc.' },
  { id: 'dash', name: 'Shadow Dash', key: 'W', damage: 25, energyCost: 25, cooldown: 1.5, radius: 120, color: '#06b6d4', element: 'SHADOW', desc: 'Phases through enemies dealing damage and granting brief invulnerability.' },
  { id: 'shuriken', name: 'Shuriken Volley', key: 'E', damage: 30, energyCost: 20, cooldown: 1.0, radius: 240, color: '#eab308', element: 'LIGHTNING', desc: 'Fires three piercing void shurikens in a spreading fan.' },
  { id: 'cloak', name: 'Shadow Cloak', key: 'R', damage: 0, energyCost: 35, cooldown: 4.0, radius: 0, color: '#a855f7', element: 'VOID', desc: 'Enters stealth mode; next attack deals 250% critical ambush damage.' },
  { id: 'decoy', name: 'Shadow Decoy', key: 'Space', damage: 55, energyCost: 40, cooldown: 3.5, radius: 90, color: '#ec4899', element: 'FIRE', desc: 'Summons a mirror duplicate that taunts enemies then detonates.' }
];

export default function App() {
  const [skills, setSkills] = useState<SkillConfig[]>(DEFAULT_SKILLS);
  const [stats, setStats] = useState({ health: 100, energy: 100, score: 0, combo: 1, level: 1, xp: 0 });
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  const handleUpdateSkill = (updated: SkillConfig) => {
    setSkills(prev => prev.map(s => s.id === updated.id ? updated : s));
    shadowApi.saveSkill(updated);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  return (
    <div className="shadow-master-root">
      <header className="shadow-header">
        <div className="shadow-header-top">
          <h1>Shadow Duel</h1>
          <div className="shadow-auth-ctrl">
            {currentUser ? (
              <div className="shadow-user-pill">
                <span className="user-avatar">👤</span>
                <span className="user-name">{currentUser.name}</span>
                <span className="user-rank">Rank: {currentUser.role || 'Grandmaster'}</span>
                <button id="btn-logout" className="btn-logout" onClick={handleLogout}>Log Out</button>
              </div>
            ) : (
              <button id="btn-open-login" className="btn-login-trigger" onClick={() => setIsLoginOpen(true)}>
                🔑 Sign In / Register
              </button>
            )}
          </div>
        </div>
        <p>A fast‑paced 2D fighting game where players control shadow avatars in dynamic arenas, combining fluid combat mechanics with strategic power‑ups. The game offers single‑player and online multiplayer modes, delivering an immersive experience across mobile and web platforms.</p>
      </header>

      <StatsPanel stats={stats} />
      <div className="shadow-workspace-grid">
        <CombatArena skills={skills} onStatsChange={setStats} />
        <SkillDesigner skills={skills} onUpdateSkill={handleUpdateSkill} />
      </div>

      <LoginPage
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLoginSuccess={(u) => {
          setCurrentUser(u);
          setIsLoginOpen(false);
        }}
      />
    </div>
  );
}
