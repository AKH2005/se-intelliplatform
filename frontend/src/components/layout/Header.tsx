import React from 'react';
import { Layers, Plus, FolderKanban } from 'lucide-react';
import { useProject } from '../../context/ProjectContext';
import { ProjectResponse } from '../../types/project';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface HeaderProps {
  projects: ProjectResponse[];
  onOpenCreateProject: () => void;
}

export const Header: React.FC<HeaderProps> = ({ projects, onOpenCreateProject }) => {
  const { selectedProjectId, setSelectedProjectId, selectedProject, setSelectedProject } =
    useProject();

  const handleSelectProject = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (!val) {
      setSelectedProjectId(null);
      setSelectedProject(null);
      return;
    }
    const found = projects.find((p) => p.id === val);
    setSelectedProjectId(val);
    setSelectedProject(found || null);
  };

  return (
    <header
      style={{
        height: '64px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-xl)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)',
          }}
        >
          <Layers size={18} color="#fff" />
        </div>
        <div>
          <span style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.02em' }}>
            SE IntelliPlatform
          </span>
          <span
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              marginLeft: '0.5rem',
              fontWeight: 500,
            }}
          >
            v1.0 (Phase 9)
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FolderKanban size={16} color="var(--text-muted)" />
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Project:</span>
          <select
            className="form-select"
            style={{ width: '220px', padding: '0.35rem 0.6rem' }}
            value={selectedProjectId || ''}
            onChange={handleSelectProject}
            aria-label="Select active project"
          >
            <option value="">-- Select Active Project --</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.status})
              </option>
            ))}
          </select>
          {selectedProject && (
            <Badge variant={selectedProject.status}>{selectedProject.status}</Badge>
          )}
        </div>

        <Button variant="primary" size="sm" icon={<Plus size={14} />} onClick={onOpenCreateProject}>
          New Project
        </Button>
      </div>
    </header>
  );
};
