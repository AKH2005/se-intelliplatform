import React, { useState } from 'react';
import { SkillConfig } from '../services/api';

interface Props { skills: SkillConfig[]; onUpdateSkill: (s: SkillConfig) => void; }

export default function SkillDesigner({ skills, onUpdateSkill }: Props) {
  const [selectedId, setSelectedId] = useState<string>(skills[0]?.id || 'slash');
  const active = skills.find(s => s.id === selectedId) || skills[0];
  const [exported, setExported] = useState<string>('');

  const handleExport = () => {
    setExported(JSON.stringify({ game: 'Shadow Master', skills }, null, 2));
  };

  return (
    <div className="skill-designer-panel">
      <h3>Skill Customizer & Builder</h3>
      <div className="skill-tabs">
        {skills.map(s => (
          <button key={s.id} className={`tab-btn ${s.id === selectedId ? 'active' : ''}`} onClick={() => setSelectedId(s.id)}>{s.name}</button>
        ))}
      </div>
      {active && (
        <div className="editor-controls">
          <div className="control-row">
            <label>Damage: {active.damage}</label>
            <input type="range" min={10} max={150} value={active.damage} onChange={e => onUpdateSkill({ ...active, damage: Number(e.target.value) })} />
          </div>
          <div className="control-row">
            <label>Energy Cost: {active.energyCost}</label>
            <input type="range" min={5} max={80} value={active.energyCost} onChange={e => onUpdateSkill({ ...active, energyCost: Number(e.target.value) })} />
          </div>
          <div className="control-row">
            <label>Cooldown: {active.cooldown.toFixed(1)}s</label>
            <input type="range" min={2} max={60} value={Math.round(active.cooldown * 10)} onChange={e => onUpdateSkill({ ...active, cooldown: Number(e.target.value) / 10 })} />
          </div>
        </div>
      )}
      <button className="export-btn" onClick={handleExport}>Export Skill Tree JSON</button>
      {exported && <pre className="json-view">{exported}</pre>}
    </div>
  );
}
