import React, { useRef, useState, useMemo } from 'react';
import {
  Save,
  Copy,
  Check,
  FileCode2,
  Lock,
  ChevronRight,
  Plus,
  Sparkles,
  RotateCw,
} from 'lucide-react';

interface CodeEditorProps {
  filePath: string | null;
  content: string;
  language: string;
  isDirty: boolean;
  isLoading: boolean;
  isSaving: boolean;
  isReadOnly?: boolean;
  onChangeContent: (newContent: string) => void;
  onSave: () => void;
  onCloseTab?: () => void;
  onCreateFirstFile?: () => void;
  onGenerateScaffolding?: () => void;
  isGeneratingScaffolding?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  filePath,
  content,
  language,
  isDirty,
  isLoading,
  isSaving,
  isReadOnly = false,
  onChangeContent,
  onSave,
  onCloseTab,
  onCreateFirstFile,
  onGenerateScaffolding,
  isGeneratingScaffolding = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const gutterRef = useRef<HTMLDivElement>(null);

  const [cursorPos, setCursorPos] = useState<{ line: number; col: number }>({ line: 1, col: 1 });
  const [copied, setCopied] = useState<boolean>(false);

  // Calculate lines
  const lines = useMemo(() => {
    return content.split('\n');
  }, [content]);

  // Sync gutter vertical scroll with textarea
  const handleScroll = () => {
    if (textareaRef.current && gutterRef.current) {
      gutterRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Track cursor position
  const updateCursorPosition = () => {
    if (!textareaRef.current) return;
    const text = textareaRef.current.value;
    const selStart = textareaRef.current.selectionStart;
    const textBeforeCursor = text.substring(0, selStart);
    const lineNum = textBeforeCursor.split('\n').length;
    const colNum = selStart - textBeforeCursor.lastIndexOf('\n');
    setCursorPos({ line: lineNum, col: colNum });
  };

  // Keyboard shortcuts (Ctrl+S / Cmd+S, Tab key)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+S or Cmd+S to Save
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      if (!isReadOnly && isDirty && !isSaving) {
        onSave();
      }
      return;
    }

    // Tab key inserts 2 spaces
    if (e.key === 'Tab' && !isReadOnly) {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;

      const newContent = content.substring(0, start) + '  ' + content.substring(end);
      onChangeContent(newContent);

      // Restore cursor position after state update
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
        updateCursorPosition();
      }, 0);
    }
  };

  // Copy to clipboard
  const handleCopy = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const fileName = filePath ? filePath.split('/').pop() : null;
  const breadcrumbSegments = filePath ? filePath.split('/') : [];

  if (!filePath) {
    return (
      <div
        data-testid="editor-empty-state"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          backgroundColor: 'var(--bg-primary, #0a0d14)',
          color: 'var(--text-muted, #94a3b8)',
          padding: '32px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            maxWidth: '440px',
            width: '100%',
            background: 'linear-gradient(180deg, rgba(17, 24, 39, 0.7) 0%, rgba(13, 18, 30, 0.85) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '16px',
            padding: '2.25rem 2rem',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.45)',
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2))',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem',
            }}
          >
            <FileCode2 size={26} color="#818cf8" />
          </div>
          <h3 style={{ margin: '0 0 8px 0', color: 'var(--text-primary, #ffffff)', fontSize: '18px', fontWeight: 700 }}>
            No File Open
          </h3>
          <p style={{ margin: '0 0 1.5rem 0', fontSize: '13px', lineHeight: '1.55', color: 'var(--text-muted, #94a3b8)' }}>
            Select an existing file from the explorer on the left, create a new entrypoint file, or synthesize complete scaffolding using SE IntelliPlatform AI.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%' }}>
            {onCreateFirstFile && (
              <button
                id="btn-create-first-file"
                data-testid="btn-create-first-file"
                type="button"
                onClick={onCreateFirstFile}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1rem',
                  background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 650,
                  fontSize: '0.86rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(79, 70, 229, 0.35)',
                  transition: 'all 0.15s ease',
                }}
              >
                <Plus size={15} />
                <span>Create First File (main.py)</span>
              </button>
            )}

            {onGenerateScaffolding && (
              <button
                id="btn-generate-scaffolding"
                data-testid="btn-generate-scaffolding"
                type="button"
                disabled={isGeneratingScaffolding}
                onClick={onGenerateScaffolding}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1rem',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#e2e8f0',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.86rem',
                  cursor: isGeneratingScaffolding ? 'not-allowed' : 'pointer',
                  opacity: isGeneratingScaffolding ? 0.7 : 1,
                  transition: 'all 0.15s ease',
                }}
              >
                {isGeneratingScaffolding ? (
                  <>
                    <RotateCw size={15} className="animate-spin" color="#38bdf8" />
                    <span>Synthesizing Scaffolding...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={15} color="#38bdf8" />
                    <span>Generate Project Scaffolding</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--bg-primary, #0a0d14)',
        overflow: 'hidden',
      }}
    >
      {/* File Tab & Editor Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-secondary, #0f1422)',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          padding: '0 8px',
          minHeight: '38px',
        }}
      >
        {/* Active Tab */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--bg-primary, #0a0d14)',
              borderTop: '2px solid var(--accent-violet, #8b5cf6)',
              borderRight: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              borderLeft: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--text-primary, #ffffff)',
            }}
          >
            <FileCode2 size={14} color="var(--accent-violet-light, #a78bfa)" />
            <span>{fileName}</span>
            {isDirty && (
              <span
                style={{
                  color: 'var(--accent-amber, #fbbf24)',
                  fontWeight: 'bold',
                  fontSize: '14px',
                }}
                title="Unsaved changes"
              >
                *
              </span>
            )}
            {onCloseTab && (
              <button
                type="button"
                onClick={onCloseTab}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted, #94a3b8)',
                  cursor: 'pointer',
                  padding: '0 2px',
                  marginLeft: '6px',
                  fontSize: '14px',
                  lineHeight: '1',
                  borderRadius: '2px',
                }}
                title="Close tab"
              >
                &times;
              </button>
            )}
          </div>
        </div>

        {/* Toolbar Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isReadOnly && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 650,
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.3)',
              }}
            >
              <Lock size={12} /> READ-ONLY
            </span>
          )}

          <button
            type="button"
            onClick={handleCopy}
            title="Copy code to clipboard"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm, 6px)',
              fontSize: '11px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              color: 'var(--text-secondary, #cbd5e1)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {copied ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {!isReadOnly && (
            <button
              type="button"
              onClick={onSave}
              disabled={isSaving || !isDirty}
              title="Save changes (Ctrl+S / Cmd+S)"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 12px',
                borderRadius: 'var(--radius-sm, 6px)',
                fontSize: '12px',
                fontWeight: 650,
                backgroundColor: isDirty
                  ? 'var(--accent-gradient, linear-gradient(135deg, #7c3aed, #6366f1))'
                  : 'var(--bg-surface-elevated, #1a2238)',
                color: isDirty ? '#ffffff' : 'var(--text-dim, #64748b)',
                border: 'none',
                cursor: isDirty && !isSaving ? 'pointer' : 'default',
                opacity: isSaving ? 0.7 : 1,
                boxShadow: isDirty ? '0 2px 8px rgba(124, 58, 237, 0.35)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <Save size={13} />
              <span>{isSaving ? 'Saving...' : 'Save'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Path Breadcrumbs Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 14px',
          backgroundColor: 'var(--bg-surface-subtle, #0d121f)',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.06))',
          fontSize: '11px',
          color: 'var(--text-dim, #64748b)',
          fontFamily: 'monospace',
        }}
      >
        {breadcrumbSegments.map((segment, idx) => (
          <React.Fragment key={idx}>
            {idx > 0 && <ChevronRight size={11} color="var(--text-dim, #64748b)" />}
            <span
              style={{
                color: idx === breadcrumbSegments.length - 1 ? 'var(--text-primary, #ffffff)' : 'inherit',
                fontWeight: idx === breadcrumbSegments.length - 1 ? 600 : 400,
              }}
            >
              {segment}
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* Editor Body: Gutter + Textarea */}
      <div
        style={{
          position: 'relative',
          display: 'flex',
          flex: 1,
          overflow: 'hidden',
          backgroundColor: '#070a12',
        }}
      >
        {isLoading ? (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(7, 10, 18, 0.85)',
              zIndex: 10,
              color: 'var(--text-secondary, #cbd5e1)',
              fontSize: '13px',
            }}
          >
            Loading file contents...
          </div>
        ) : null}

        {/* Line Numbers Gutter */}
        <div
          ref={gutterRef}
          data-testid="line-numbers-gutter"
          style={{
            width: '48px',
            padding: '12px 0',
            textAlign: 'right',
            backgroundColor: '#090d18',
            borderRight: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            color: 'var(--text-dim, #475569)',
            fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, Consolas, monospace",
            fontSize: '13px',
            lineHeight: '22px',
            userSelect: 'none',
            overflowY: 'hidden',
          }}
        >
          {lines.map((_, i) => (
            <div
              key={i}
              style={{
                paddingRight: '12px',
                color: i + 1 === cursorPos.line ? 'var(--text-secondary, #cbd5e1)' : 'var(--text-dim, #475569)',
                fontWeight: i + 1 === cursorPos.line ? 600 : 400,
              }}
            >
              {i + 1}
            </div>
          ))}
        </div>

        {/* Source Textarea */}
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => {
            if (!isReadOnly) {
              onChangeContent(e.target.value);
            }
          }}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          onClick={updateCursorPosition}
          onKeyUp={updateCursorPosition}
          readOnly={isReadOnly}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          autoCorrect="off"
          placeholder="Enter source code..."
          style={{
            flex: 1,
            height: '100%',
            padding: '12px 16px',
            margin: 0,
            border: 'none',
            outline: 'none',
            resize: 'none',
            backgroundColor: '#070a12',
            color: '#f8fafc',
            fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, Monaco, Consolas, monospace",
            fontSize: '13px',
            lineHeight: '22px',
            whiteSpace: 'pre',
            wordWrap: 'normal',
            overflowX: 'auto',
            overflowY: 'auto',
            tabSize: 2,
            caretColor: 'var(--accent-violet-light, #a78bfa)',
          }}
        />
      </div>

      {/* Editor Status Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#090d18',
          borderTop: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          padding: '4px 14px',
          fontSize: '11px',
          color: 'var(--text-dim, #64748b)',
          fontFamily: "'JetBrains Mono', Menlo, monospace",
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span>
            Ln {cursorPos.line}, Col {cursorPos.col}
          </span>
          <span>{lines.length} lines</span>
          <span>{content.length} chars</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span>UTF-8</span>
          <span style={{ textTransform: 'uppercase', color: 'var(--accent-violet-light, #a78bfa)', fontWeight: 600 }}>
            {language}
          </span>
          <span>{isReadOnly ? 'READ-ONLY' : 'READ/WRITE'}</span>
        </div>
      </div>
    </div>
  );
};
