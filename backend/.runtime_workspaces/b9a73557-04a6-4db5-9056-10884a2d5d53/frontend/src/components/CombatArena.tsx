import React, { useRef, useEffect } from 'react';
import { SkillConfig } from '../services/api';

interface Props { skills: SkillConfig[]; onStatsChange: (s: any) => void; }

export default function CombatArena({ skills, onStatsChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let animId: number;
    let pX = 350, pY = 210, hp = 100, energy = 100, score = 0, combo = 1, lvl = 1, xp = 0;
    const loop = () => {
      ctx.fillStyle = '#07090e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      // Draw grid
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.1)';
      for (let x = 0; x < canvas.width; x += 35) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }
      for (let y = 0; y < canvas.height; y += 35) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke(); }
      // Player
      ctx.shadowBlur = 15; ctx.shadowColor = '#a855f7';
      ctx.fillStyle = '#c084fc';
      ctx.beginPath(); ctx.arc(pX, pY, 18, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [skills]);

  return (
    <div className="combat-arena-container">
      <canvas ref={canvasRef} width={700} height={420} className="arena-canvas" />
      <div className="ability-bar">
        {skills.map(s => (
          <div key={s.id} className="skill-slot" style={{ borderColor: s.color }}>
            <span className="key-badge">{s.key}</span>
            <div className="skill-name">{s.name}</div>
            <div className="skill-meta">{s.energyCost} NRG</div>
          </div>
        ))}
      </div>
    </div>
  );
}
