import React from 'react';

interface Stats { health: number; energy: number; score: number; combo: number; level: number; xp: number; }

export default function StatsPanel({ stats }: { stats: Stats }) {
  return (
    <div className="stats-hud-bar">
      <div className="hud-stat"><label>HP</label><div className="bar-bg"><div className="bar-fill hp" style={{ width: `${stats.health}%` }}></div></div><span>{Math.round(stats.health)}/100</span></div>
      <div className="hud-stat"><label>ENERGY</label><div className="bar-bg"><div className="bar-fill nrg" style={{ width: `${stats.energy}%` }}></div></div><span>{Math.round(stats.energy)}/100</span></div>
      <div className="hud-pill">LVL <strong>{stats.level}</strong> (XP: {stats.xp}/100)</div>
      <div className="hud-pill combo">COMBO <strong>{stats.combo.toFixed(1)}x</strong></div>
      <div className="hud-pill score">SCORE <strong>{stats.score}</strong></div>
    </div>
  );
}
