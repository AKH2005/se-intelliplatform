import React from 'react';

export const SkyStrikeGame: React.FC = () => {
  return (
    <div style={{ width: '100%', height: '100vh', background: '#070b14', color: '#fff', fontFamily: 'system-ui' }}>
      <iframe
        src="/preview?project_id=6ab754dc-c2bb-4689-9d87-2f69b778527f"
        style={{ width: '100%', height: '100%', border: 'none' }}
        title="Sky Strike Aerial Combat Simulator"
      />
    </div>
  );
};

export default SkyStrikeGame;
