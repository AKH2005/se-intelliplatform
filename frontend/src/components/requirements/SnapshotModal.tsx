import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ContextSnapshotCreate } from '../../types/context';

interface SnapshotModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ContextSnapshotCreate) => Promise<void>;
}

export const SnapshotModal: React.FC<SnapshotModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [summary, setSummary] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({
        summary: summary.trim() || null,
      });
      setSummary('');
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to capture snapshot');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Context Snapshot"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={isSubmitting}>
            Commit Snapshot
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

        <p style={{ fontSize: '0.85rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Snapshots freeze an immutable point-in-time copy of the active project requirements.
          Multi-agent workflows can be pinned to specific historical snapshot versions.
        </p>

        <div className="form-group">
          <label className="form-label" htmlFor="snapshot-summary">
            Milestone Summary / Tag
          </label>
          <input
            id="snapshot-summary"
            type="text"
            className="form-input"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="e.g. Sprint 1 Requirements Freeze"
            maxLength={500}
          />
        </div>
      </form>
    </Modal>
  );
};
