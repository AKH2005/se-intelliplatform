import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ScoreBoard } from './components/ScoreBoard';
import { GameControls } from './components/GameControls';
import { scoreApi } from './services/api';

interface Piece {
  id: string;
  type: 'queen' | 'white' | 'black';
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  mass: number;
  active: boolean;
}

const BOARD_SIZE = 600;
const POCKET_RADIUS = 28;
const CUSHION = 38;
const FRICTION = 0.986;
const RESTITUTION = 0.88;
const BASELINE_Y = 482;

export default function App() {
  const [p1Score, setP1Score] = useState<number>(0);
  const [p2Score, setP2Score] = useState<number>(0);
  const [currentTurn, setCurrentTurn] = useState<number>(1);
  const [soloMode, setSoloMode] = useState<boolean>(false);
  const [queenPocketed, setQueenPocketed] = useState<boolean>(false);
  const [strikerPos, setStrikerPos] = useState<number>(300);
  const [statusMsg, setStatusMsg] = useState<string>('Drag striker back to aim and shoot!');
  const [coinsLeft, setCoinsLeft] = useState<number>(18);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const piecesRef = useRef<Piece[]>([]);
  const strikerRef = useRef<any>({
    x: 300, y: BASELINE_Y, vx: 0, vy: 0, r: 21, mass: 3.2, active: true, inPocket: false
  });

  const initBoard = useCallback(() => {
    const list: Piece[] = [];
    const CX = 300, CY = 300, R = 14;
    list.push({ id: 'queen', type: 'queen', x: CX, y: CY, vx: 0, vy: 0, r: R, mass: 1.0, active: true });
    const r1 = R * 2 + 1;
    for (let i = 0; i < 6; i++) {
      const a = (i * Math.PI) / 3;
      list.push({
        id: `inner_${i}`,
        type: i % 2 === 0 ? 'white' : 'black',
        x: CX + r1 * Math.cos(a),
        y: CY + r1 * Math.sin(a),
        vx: 0, vy: 0, r: R, mass: 1.0, active: true
      });
    }
    const r2 = R * 4 + 2;
    for (let i = 0; i < 12; i++) {
      const a = (i * Math.PI) / 6 + Math.PI / 12;
      list.push({
        id: `outer_${i}`,
        type: i % 2 === 0 ? 'white' : 'black',
        x: CX + r2 * Math.cos(a),
        y: CY + r2 * Math.sin(a),
        vx: 0, vy: 0, r: R, mass: 1.0, active: true
      });
    }
    piecesRef.current = list;
    strikerRef.current = { x: 300, y: BASELINE_Y, vx: 0, vy: 0, r: 21, mass: 3.2, active: true, inPocket: false };
    setStrikerPos(300);
    setCoinsLeft(18);
    setQueenPocketed(false);
  }, []);

  useEffect(() => {
    initBoard();
  }, [initBoard]);

  const handleReset = () => {
    setP1Score(0);
    setP2Score(0);
    setCurrentTurn(1);
    initBoard();
    setStatusMsg('Board reset! Player 1 takes the break shot.');
  };

  const handleShoot = (vx: number, vy: number) => {
    strikerRef.current.vx = vx;
    strikerRef.current.vy = vy;
    setStatusMsg('Shot in motion...');
  };

  return (
    <div className="carrom-wrapper">
      <h1 data-testid="app-title">Carrom Master</h1>
      <p className="subtitle">A realistic digital carrom game that offers immersive gameplay, precise physics, and competitive multiplayer modes, allowing players to master the classic board game from any device.</p>
      <ScoreBoard
        p1Score={p1Score}
        p2Score={p2Score}
        currentTurn={currentTurn}
        queenPocketed={queenPocketed}
        coinsLeft={coinsLeft}
        soloMode={soloMode}
      />
      <div className="canvas-container">
        <canvas ref={canvasRef} width={600} height={600} />
      </div>
      <div className="status-banner">{statusMsg}</div>
      <GameControls
        strikerPos={strikerPos}
        onStrikerPosChange={(pos) => {
          setStrikerPos(pos);
          strikerRef.current.x = pos;
        }}
        onShoot={() => handleShoot((Math.random() - 0.5) * 4, -18)}
        onReset={handleReset}
        soloMode={soloMode}
        onToggleSolo={() => setSoloMode(!soloMode)}
      />
    </div>
  );
}
