import React, { useState } from 'react';
import CombatArena from './components/CombatArena';
import SkillDesigner from './components/SkillDesigner';
import StatsPanel from './components/StatsPanel';
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

  const handleUpdateSkill = (updated: SkillConfig) => {
    setSkills(prev => prev.map(s => s.id === updated.id ? updated : s));
    shadowApi.saveSkill(updated);
  };

  return (
    <div className="shadow-master-root">
      <header className="shadow-header"><h1>Shadow Master Skill Builder</h1><p>A web-based tool that lets game designers create, preview, and export custom skills for the Shadow Master game, streamlining the development workflow and ensuring consistency across the game’s skill system.</p></header>
      <StatsPanel stats={stats} />
      <div className="shadow-workspace-grid">
        <CombatArena skills={skills} onStatsChange={setStats} />
        <SkillDesigner skills={skills} onUpdateSkill={handleUpdateSkill} />
      </div>
    </div>
  );
}
