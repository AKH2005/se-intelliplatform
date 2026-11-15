import React from 'react';

interface GameControlsProps {
  strikerPos: number;
  onStrikerPosChange: (pos: number) => void;
  onShoot: () => void;
  onReset: () => void;
  soloMode: boolean;
  onToggleSolo: () => void;
}

export const GameControls: React.FC<GameControlsProps> = ({
  strikerPos, onStrikerPosChange, onShoot, onReset, soloMode, onToggleSolo
}) => (
  <div className="controls-panel">
    <div className="control-item">
      <label htmlFor="striker-slider">Striker Pos:</label>
      <input
        id="striker-slider"
        type="range"
        min={175}
        max={425}
        value={strikerPos}
        onChange={(e) => onStrikerPosChange(parseFloat(e.target.value))}
      />
    </div>
    <button className="btn btn-primary" onClick={onShoot}>Shoot Striker</button>
    <button className="btn btn-secondary" onClick={onReset}>Reset Board</button>
    <button className="btn" onClick={onToggleSolo}>
      {soloMode ? 'Mode: Solo Practice' : 'Mode: 2 Players'}
    </button>
  </div>
);
