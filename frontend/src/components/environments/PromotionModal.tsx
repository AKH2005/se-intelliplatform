import React, { useEffect, useState } from 'react';
import { Environment, EnvironmentType, PromoteVersionPayload, PromotionEligibilityResult } from '../../types/environment';
import { environmentApi } from '../../services/environmentApi';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import {
  ArrowRight,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Lock,
} from 'lucide-react';

interface PromotionModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  sourceEnvironment: Environment | null;
  targetEnvironmentType: EnvironmentType;
  candidateVersionId: string;
  candidateVersionNumber: number;
  onPromoteSuccess: () => void;
}

export const PromotionModal: React.FC<PromotionModalProps> = ({
  isOpen,
  onClose,
  projectId,
  sourceEnvironment,
  targetEnvironmentType,
  candidateVersionId,
  candidateVersionNumber,
  onPromoteSuccess,
}) => {
  const [eligibility, setEligibility] = useState<PromotionEligibilityResult | null>(null);
  const [checking, setChecking] = useState<boolean>(false);
  const [promoting, setPromoting] = useState<boolean>(false);
  const [notes, setNotes] = useState<string>('');
  const [productionConfirmed, setProductionConfirmed] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isProductionTarget = targetEnvironmentType === 'PRODUCTION';

  useEffect(() => {
    if (isOpen && projectId && candidateVersionId && sourceEnvironment) {
      setChecking(true);
      setErrorMessage(null);
      setProductionConfirmed(false);
      environmentApi
        .checkPromotionEligibility(
          projectId,
          candidateVersionId,
          targetEnvironmentType,
          sourceEnvironment.environment_type
        )
        .then((result) => {
          setEligibility(result);
        })
        .catch((err) => {
          setErrorMessage(err.message || 'Failed to evaluate promotion eligibility');
        })
        .finally(() => {
          setChecking(false);
        });
    }
  }, [isOpen, projectId, candidateVersionId, targetEnvironmentType, sourceEnvironment]);

  const handlePromote = async () => {
    if (!eligibility?.eligible) return;
    if (isProductionTarget && !productionConfirmed) return;

    setPromoting(true);
    setErrorMessage(null);
    try {
      const payload: PromoteVersionPayload = {
        version_id: candidateVersionId,
        target_environment: targetEnvironmentType,
        source_environment: sourceEnvironment?.environment_type,
        requested_by: 'Engineer',
        notes: notes.trim() || undefined,
      };
      await environmentApi.promoteVersion(projectId, payload);
      onPromoteSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Promotion execution failed');
    } finally {
      setPromoting(false);
    }
  };

  const isPromoteDisabled =
    checking ||
    promoting ||
    !eligibility?.eligible ||
    (isProductionTarget && !productionConfirmed);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Promote Version to ${targetEnvironmentType}`}
      size="default"
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', width: '100%' }}>
          <Button variant="ghost" onClick={onClose} disabled={promoting}>
            Cancel
          </Button>
          <Button
            variant={isProductionTarget ? 'danger' : 'primary'}
            onClick={handlePromote}
            disabled={isPromoteDisabled}
            isLoading={promoting}
            icon={isProductionTarget ? <Lock size={14} /> : undefined}
          >
            Confirm Promotion
          </Button>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Promotion Route Visual */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            background: 'var(--bg-secondary)',
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              SOURCE
            </span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {sourceEnvironment?.name ?? sourceEnvironment?.environment_type}
            </span>
          </div>
          <ArrowRight size={18} style={{ color: 'var(--text-secondary)' }} />
          <div style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              TARGET
            </span>
            <span
              style={{
                fontWeight: 700,
                color: isProductionTarget ? '#f87171' : 'var(--text-primary)',
              }}
            >
              {targetEnvironmentType}
            </span>
          </div>
          <div style={{ marginLeft: '16px', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '16px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>
              VERSION
            </span>
            <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
              v{candidateVersionNumber}
            </span>
          </div>
        </div>

        {/* Eligibility Engine Results */}
        {checking ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
            <LoadingSpinner />
            <span style={{ marginLeft: '12px', color: 'var(--text-secondary)' }}>
              Evaluating deterministic promotion gates...
            </span>
          </div>
        ) : eligibility ? (
          <div
            style={{
              borderRadius: '6px',
              border: eligibility.eligible
                ? '1px solid rgba(16, 185, 129, 0.4)'
                : '1px solid rgba(239, 68, 68, 0.4)',
              background: eligibility.eligible
                ? 'rgba(16, 185, 129, 0.05)'
                : 'rgba(239, 68, 68, 0.05)',
              padding: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              {eligibility.eligible ? (
                <>
                  <CheckCircle2 size={18} style={{ color: 'var(--status-completed)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--status-completed)' }}>
                    Promotion Gate Passed
                  </span>
                </>
              ) : (
                <>
                  <XCircle size={18} style={{ color: 'var(--status-failed)' }} />
                  <span style={{ fontWeight: 600, color: 'var(--status-failed)' }}>
                    Promotion Gate Blocked
                  </span>
                </>
              )}
            </div>

            {/* Passed checks */}
            {eligibility.passed_checks.length > 0 && (
              <ul style={{ margin: '4px 0 8px 18px', padding: 0, fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                {eligibility.passed_checks.map((check, idx) => (
                  <li key={idx} style={{ color: 'var(--text-secondary)' }}>{check}</li>
                ))}
              </ul>
            )}

            {/* Failed checks */}
            {eligibility.failed_checks.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--status-failed)', textTransform: 'uppercase' }}>
                  Blocking Reasons:
                </span>
                <ul style={{ margin: '4px 0 0 18px', padding: 0, fontSize: '0.8125rem', color: '#f87171' }}>
                  {eligibility.failed_checks.map((check, idx) => (
                    <li key={idx}>{check}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : null}

        {/* Production Confirmation Safeguard */}
        {isProductionTarget && eligibility?.eligible && (
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontWeight: 600, fontSize: '0.875rem' }}>
              <ShieldAlert size={16} /> Production Deployment Safeguard
            </div>
            <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Promoting to Production will immediately update the live production environment pointer.
              Ensure all end-to-end tests and browser journeys have been validated in Staging.
            </p>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', color: 'var(--text-primary)', cursor: 'pointer', marginTop: '4px' }}>
              <input
                type="checkbox"
                checked={productionConfirmed}
                onChange={(e) => setProductionConfirmed(e.target.checked)}
              />
              <span>I confirm promotion of Version {candidateVersionNumber} to Production</span>
            </label>
          </div>
        )}

        {/* Promotion Notes */}
        <div>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Promotion Notes (Optional)
          </label>
          <input
            type="text"
            className="input"
            placeholder="e.g. Release candidate for sprint 42"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={promoting}
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
