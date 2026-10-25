import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastProps {
  type: 'success' | 'error' | 'info';
  message: string;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ type, message, onClose }) => {
  const bg =
    type === 'success'
      ? 'rgba(16, 185, 129, 0.95)'
      : type === 'error'
      ? 'rgba(244, 63, 94, 0.95)'
      : 'rgba(56, 189, 248, 0.95)';

  const Icon = type === 'success' ? CheckCircle2 : type === 'error' ? AlertCircle : Info;

  return (
    <div
      role="status"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.85rem 1.25rem',
        background: bg,
        color: '#ffffff',
        borderRadius: 'var(--radius-sm)',
        boxShadow: 'var(--shadow-lg)',
        fontSize: '0.875rem',
        fontWeight: 600,
        maxWidth: '420px',
        animation: 'slideIn 0.25s ease-out',
      }}
    >
      <Icon size={18} />
      <span style={{ flex: 1 }}>{message}</span>
      <button
        type="button"
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: '#ffffff',
          cursor: 'pointer',
          padding: '0.15rem',
          display: 'flex',
        }}
      >
        <X size={15} />
      </button>
    </div>
  );
};
