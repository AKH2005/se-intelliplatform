import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import {
  RequirementCreate,
  RequirementPriority,
  RequirementStatus,
  RequirementType,
} from '../../types/requirement';

interface CreateRequirementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: RequirementCreate) => Promise<void>;
}

export const CreateRequirementModal: React.FC<CreateRequirementModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<RequirementType>('FUNCTIONAL');
  const [priority, setPriority] = useState<RequirementPriority>('MEDIUM');
  const [status, setStatus] = useState<RequirementStatus>('DRAFT');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Requirement title is required');
      return;
    }
    if (!description.trim()) {
      setError('Requirement description is required');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        type,
        priority,
        status,
      });
      setTitle('');
      setDescription('');
      setType('FUNCTIONAL');
      setPriority('MEDIUM');
      setStatus('DRAFT');
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create requirement');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add Project Requirement"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={isSubmitting}>
            Save Requirement
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
          <label className="form-label" htmlFor="req-title">
            Title *
          </label>
          <input
            id="req-title"
            type="text"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. OAuth2 Authentication with RS256 JWT"
            required
            maxLength={255}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="req-desc">
            Description / Acceptance Criteria *
          </label>
          <textarea
            id="req-desc"
            className="form-textarea"
            style={{ minHeight: '120px' }}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="System must authenticate incoming bearer tokens via asymmetric RS256 public key verification..."
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="req-type">
              Type
            </label>
            <select
              id="req-type"
              className="form-select"
              value={type}
              onChange={(e) => setType(e.target.value as RequirementType)}
            >
              <option value="FUNCTIONAL">FUNCTIONAL</option>
              <option value="NON_FUNCTIONAL">NON_FUNCTIONAL</option>
              <option value="CONSTRAINT">CONSTRAINT</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="req-priority">
              Priority
            </label>
            <select
              id="req-priority"
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value as RequirementPriority)}
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="req-status">
              Lifecycle Status
            </label>
            <select
              id="req-status"
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value as RequirementStatus)}
            >
              <option value="DRAFT">DRAFT</option>
              <option value="APPROVED">APPROVED</option>
              <option value="IMPLEMENTED">IMPLEMENTED</option>
              <option value="DEFERRED">DEFERRED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>
        </div>
      </form>
    </Modal>
  );
};
