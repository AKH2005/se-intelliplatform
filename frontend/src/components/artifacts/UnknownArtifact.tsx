import React from 'react';

interface UnknownArtifactProps {
  artifactKey: string;
  data: any;
}

export const UnknownArtifact: React.FC<UnknownArtifactProps> = ({ artifactKey, data }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        Raw structured payload for artifact key: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{artifactKey}</span>
      </div>
      <pre style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};
