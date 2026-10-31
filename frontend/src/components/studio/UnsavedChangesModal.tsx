import React from 'react';
import { AlertTriangle, Save, Trash2, X } from 'lucide-react';

interface UnsavedChangesModalProps {
  isOpen: boolean;
  filePath: string | null;
  onSaveAndProceed: () => void;
  onDiscardAndProceed: () => void;
  onCancel: () => void;
  isSaving?: boolean;
}

export const UnsavedChangesModal: React.FC<UnsavedChangesModalProps> = ({
  isOpen,
  filePath,
  onSaveAndProceed,
  onDiscardAndProceed,
  onCancel,
  isSaving = false,
}) => {
  if (!isOpen) return null;

  const fileName = filePath ? filePath.split('/').pop() : 'this file';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(2, 6, 23, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backdropFilter: 'blur(3px)',
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="unsaved-modal-title"
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: 'var(--bg-secondary, #0f172a)',
          border: '1px solid var(--border-color, #334155)',
          borderRadius: '8px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-color, #1e293b)',
            backgroundColor: 'var(--bg-elevated, #1e293b)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="var(--accent-amber, #fbbf24)" />
            <h3
              id="unsaved-modal-title"
              style={{
                margin: 0,
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary, #f8fafc)',
              }}
            >
              Unsaved Changes
            </h3>
          </div>
          <button
            type="button"
            onClick={onCancel}
            disabled={isSaving}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted, #94a3b8)',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              padding: '2px',
              display: 'flex',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '18px', fontSize: '13px', color: 'var(--text-secondary, #cbd5e1)', lineHeight: '1.5' }}>
          <p style={{ margin: '0 0 10px 0' }}>
            You have unsaved modifications in <strong style={{ color: 'var(--accent-cyan, #38bdf8)' }}>{fileName}</strong>.
          </p>
          <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted, #94a3b8)' }}>
            Do you want to save your changes to the backend before switching, or discard them?
          </p>
        </div>

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '8px',
            padding: '12px 18px',
            backgroundColor: 'var(--bg-elevated, #1e293b)',
            borderTop: '1px solid var(--border-color, #1e293b)',
          }}
        >
          <button
            type="button"
            onClick={onCancel}
            disabled={isSaving}
            style={{
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              backgroundColor: 'transparent',
              color: 'var(--text-secondary, #cbd5e1)',
              border: '1px solid var(--border-color, #334155)',
              cursor: isSaving ? 'not-allowed' : 'pointer',
            }}
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={onDiscardAndProceed}
            disabled={isSaving}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 500,
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              cursor: isSaving ? 'not-allowed' : 'pointer',
            }}
          >
            <Trash2 size={13} /> Discard Changes
          </button>

          <button
            type="button"
            onClick={onSaveAndProceed}
            disabled={isSaving}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 14px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              backgroundColor: 'var(--accent-primary, #6366f1)',
              color: '#ffffff',
              border: 'none',
              cursor: isSaving ? 'not-allowed' : 'pointer',
              opacity: isSaving ? 0.7 : 1,
            }}
          >
            <Save size={13} /> {isSaving ? 'Saving...' : 'Save & Continue'}
          </button>
        </div>
      </div>
    </div>
  );
};
