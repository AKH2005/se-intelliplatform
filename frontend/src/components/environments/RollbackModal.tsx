import React, { useState } from 'react';
import { Environment, RollbackEnvironmentPayload } from '../../types/environment';
import { environmentApi } from '../../services/environmentApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { RotateCcw, AlertTriangle } from 'lucide-react';

interface RollbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  environment: Environment | null;
  availableVersions: Array<{
    version_id: string;
    version_number: number;
    status?: string;
  }>;
  onRollbackSuccess: () => void;
}

export const RollbackModal: React.FC<RollbackModalProps> = ({
  isOpen,
  onClose,
  projectId,
  environment,
  availableVersions,
  onRollbackSuccess,
}) => {
  const [targetVersionId, setTargetVersionId] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [rollingBack, setRollingBack] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filter out the currently deployed version so user picks a previous/different version
  const candidateVersions = availableVersions.filter(
    (v) => v.version_id !== environment?.current_version_id
  );

  const handleRollback = async () => {
    if (!environment || !targetVersionId || !reason.trim()) return;

    setRollingBack(true);
    setErrorMessage(null);
    try {
      const payload: RollbackEnvironmentPayload = {
        target_version_id: targetVersionId,
        requested_by: 'Engineer',
        reason: reason.trim(),
      };
      await environmentApi.rollbackEnvironment(projectId, environment.id, payload);
      onRollbackSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Rollback execution failed');
    } finally {
      setRollingBack(false);
    }
  };

  const isRollbackDisabled =
    rollingBack || !targetVersionId || reason.trim().length < 5;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Rollback ${environment?.name ?? 'Environment'}`}
      size="default"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', width: '100%' }}>
          <Button variant="ghost" onClick={onClose} disabled={rollingBack}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleRollback}
            disabled={isRollbackDisabled}
            isLoading={rollingBack}
            icon={<RotateCcw size={14} />}
          >
            Execute Rollback
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Current status display */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              ENVIRONMENT
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {environment?.name} ({environment?.environment_type})
            </span>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              ACTIVE VERSION
            </span>
            <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
              v{environment?.current_version_number ?? 'None'}
            </span>
          </div>
        </div>

        {/* Safety Invariant Notice */}
        <div
          style={{
            background: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: '6px',
            padding: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <AlertTriangle size={18} style={{ color: '#facc15', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            <strong style={{ color: '#facc15' }}>Non-Destructive Invariant:</strong> Rollback will not delete or alter any version records.
            The environment pointer will be safely reverted to the chosen version, and an append-only deployment record will be logged.
          </div>
        </div>

        {/* Target Version Selector */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Rollback Target Version <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <select
            className="input"
            value={targetVersionId}
            onChange={(e) => setTargetVersionId(e.target.value)}
            disabled={rollingBack}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
            }}
          >
            <option value="">-- Select a version to rollback to --</option>
            {candidateVersions.map((v) => (
              <option key={v.version_id} value={v.version_id}>
                Version {v.version_number} {v.status ? `(${v.status})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Audit Reason */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Rollback Reason (Required for audit log) <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <textarea
            className="input"
            rows={3}
            placeholder="e.g. Critical regression observed in checkout flow; reverting to known good version"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={rollingBack}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
              resize: 'vertical',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Minimum 5 characters required for compliance.
          </span>
        </div>

        {/* Error message */}
        {errorMessage && (
          <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', borderRadius: '4px', fontSize: '0.8125rem' }}>
            {errorMessage}
          </div>
        )}
      </div>
    </Modal>
  );
};
