import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ProjectCreate, ProjectStatus } from '../../types/project';
import { slugify, isValidSlug } from '../../utils/slugify';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectCreate) => Promise<void>;
}

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<ProjectStatus>('DRAFT');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const derivedSlug = slugify(name);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Project name is required');
      return;
    }

    const slug = slugify(trimmedName);
    if (!isValidSlug(slug)) {
      setError('Project name must contain alphanumeric characters to produce a valid URL-safe slug.');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({
        name: trimmedName,
        slug,
        description: description.trim() || null,
        status,
      });
      setName('');
      setDescription('');
      setStatus('DRAFT');
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Project"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={isSubmitting}>
            Create Project
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div
            style={{
              padding: '0.6rem',
              marginBottom: '1rem',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="project-name">
            Project Name *
          </label>
          <input
            id="project-name"
            type="text"
            className="form-input"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (error) setError(null);
            }}
            placeholder="e.g. Smart Software Development Platform"
            required
            maxLength={255}
          />
          {derivedSlug && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
              Slug: <code style={{ color: 'var(--accent-cyan)' }}>{derivedSlug}</code>
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="project-desc">
            Description
          </label>
          <textarea
            id="project-desc"
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Detailed description of the project goals, domain, and architecture..."
            maxLength={2000}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="project-status">
            Initial Lifecycle Status
          </label>
          <select
            id="project-status"
            className="form-select"
            value={status}
            onChange={(e) => setStatus(e.target.value as ProjectStatus)}
          >
            <option value="DRAFT">DRAFT</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
          </select>
        </div>
      </form>
    </Modal>
  );
};
