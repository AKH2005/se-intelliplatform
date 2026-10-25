import React, { useState } from 'react';
import { DeployVersionPayload, Environment } from '../../types/environment';
import { environmentApi } from '../../services/environmentApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { UploadCloud } from 'lucide-react';

interface DeployModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  environment: Environment | null;
  availableVersions: Array<{
    version_id: string;
    version_number: number;
    status?: string;
  }>;
  onDeploySuccess: () => void;
}

export const DeployModal: React.FC<DeployModalProps> = ({
  isOpen,
  onClose,
  projectId,
  environment,
  availableVersions,
  onDeploySuccess,
}) => {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [deploying, setDeploying] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDeploy = async () => {
    if (!environment || !selectedVersionId) return;

    setDeploying(true);
    setErrorMessage(null);
    try {
      const payload: DeployVersionPayload = {
        version_id: selectedVersionId,
        requested_by: 'Engineer',
        notes: notes.trim() || undefined,
      };
      await environmentApi.deployVersion(projectId, environment.id, payload);
      onDeploySuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Direct deployment execution failed');
    } finally {
      setDeploying(false);
    }
  };

  const isDeployDisabled = deploying || !selectedVersionId;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Deploy Version to ${environment?.name ?? 'Environment'}`}
      size="default"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', width: '100%' }}>
          <Button variant="ghost" onClick={onClose} disabled={deploying}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleDeploy}
            disabled={isDeployDisabled}
            isLoading={deploying}
            icon={<UploadCloud size={14} />}
          >
            Deploy Version
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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
              TARGET ENVIRONMENT
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {environment?.name} ({environment?.environment_type})
            </span>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              CURRENT VERSION
            </span>
            <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
              {environment?.current_version_number != null
                ? `v${environment.current_version_number}`
                : 'None'}
            </span>
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Candidate Version to Deploy <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <select
            className="input"
            value={selectedVersionId}
            onChange={(e) => setSelectedVersionId(e.target.value)}
            disabled={deploying}
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
            <option value="">-- Select a version to deploy --</option>
            {availableVersions.map((v) => (
              <option key={v.version_id} value={v.version_id}>
                Version {v.version_number} {v.status ? `(${v.status})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Deployment Notes (Optional)
          </label>
          <input
            type="text"
            className="input"
            placeholder="e.g. Deploying feature branch verification version"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={deploying}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              color: 'var(--text-primary)',
              fontSize: '0.875rem',
            }}
          />
        </div>

        {errorMessage && (
          <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', borderRadius: '4px', fontSize: '0.8125rem' }}>
            {errorMessage}
          </div>
        )}
      </div>
    </Modal>
  );
};
