import React from 'react';

interface ScoreBoardProps {
  p1Score: number;
  p2Score: number;
  currentTurn: number;
  queenPocketed: boolean;
  coinsLeft: number;
  soloMode: boolean;
}

export const ScoreBoard: React.FC<ScoreBoardProps> = ({
  p1Score, p2Score, currentTurn, queenPocketed, coinsLeft, soloMode
}) => (
  <div className="scoreboard">
    <div className="score-pill">P1 (White): <span>{p1Score}</span></div>
    <div className="score-pill">P2 (Black): <span>{p2Score}</span></div>
    {!soloMode && (
      <div className="turn-pill">
        {currentTurn === 1 ? 'Player 1 Turn (White)' : 'Player 2 Turn (Black)'}
      </div>
    )}
    <div className={`queen-pill ${queenPocketed ? 'pocketed' : 'on-board'}`}>
      Queen: {queenPocketed ? 'Pocketed' : 'On Board'}
    </div>
    <div className="score-pill">Coins: <span>{coinsLeft}</span></div>
  </div>
);
