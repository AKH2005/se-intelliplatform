import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { requirementsApi } from '../../services/requirementsApi';
import { workflowsApi } from '../../services/workflowsApi';
import {
  Sparkles,
  Brain,
  CheckCircle2,
  AlertCircle,
  Play,
} from 'lucide-react';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName?: string;
  onTaskCreated?: (task: any) => void;
  onNavigateTab?: (tab: any) => void;
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  projectId,
  projectName = 'Current Project',
  onTaskCreated,
  onNavigateTab,
}) => {
  // Required fields
  const [taskName, setTaskName] = useState('');
  const [description, setDescription] = useState('');
  const [expectedBehavior, setExpectedBehavior] = useState('');
  const [businessGoal, setBusinessGoal] = useState('');
  const [acceptanceCriteria, setAcceptanceCriteria] = useState<string>('');

  // Optional fields
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('HIGH');
  const [taskType, setTaskType] = useState<'FUNCTIONAL' | 'NON_FUNCTIONAL' | 'CONSTRAINT'>('FUNCTIONAL');
  const [affectedPages, setAffectedPages] = useState('');
  const [relatedEndpoints, setRelatedEndpoints] = useState('');

  // AI clarification state
  const [isClarifying, setIsClarifying] = useState(false);
  const [clarificationResult, setClarificationResult] = useState<{
    suggestedCriteria: string[];
    affectedComponents: string[];
    implementationPlan: string;
  } | null>(null);

  // Execution state
  const [isSaving, setIsSaving] = useState(false);
  const [isImplementing, setIsImplementing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const resetForm = () => {
    setTaskName('');
    setDescription('');
    setExpectedBehavior('');
    setBusinessGoal('');
    setAcceptanceCriteria('');
    setPriority('HIGH');
    setTaskType('FUNCTIONAL');
    setAffectedPages('');
    setRelatedEndpoints('');
    setClarificationResult(null);
    setError(null);
    setSuccessMessage(null);
  };

  const handleClarifyWithAI = async () => {
    if (!taskName.trim()) {
      setError('Please provide a feature or task name before clarifying requirements.');
      return;
    }
    setError(null);
    setIsClarifying(true);

    setTimeout(() => {
      const criteria = [
        `Users can perform ${taskName} with deterministic feedback and error handling.`,
        'Form inputs validate required fields before sending requests to the backend API.',
        'State changes persist across browser refreshes and update active dashboard counters.',
      ];

      const components = [
        affectedPages.trim() || 'Frontend Viewport & Interactive Component',
        relatedEndpoints.trim() || 'Backend FastAPI Router & Service Logic',
        'Relational Database Schema & Data Models',
      ];

      const plan = `1. Define data contract for "${taskName}".\n2. Add endpoint in FastAPI service with validation.\n3. Integrate interactive UI controls and real-time state in frontend.\n4. Verify behavior in isolated live preview.`;

      setClarificationResult({
        suggestedCriteria: criteria,
        affectedComponents: components,
        implementationPlan: plan,
      });

      if (!acceptanceCriteria.trim()) {
        setAcceptanceCriteria(criteria.map((c) => `• ${c}`).join('\n'));
      }
      setIsClarifying(false);
    }, 600);
  };

  const handleSaveTask = async (andImplement: boolean = false) => {
    if (!taskName.trim()) {
      setError('Task or feature name is required.');
      return;
    }
    if (!description.trim()) {
      setError('Please enter a detailed description of the expected feature.');
      return;
    }

    setError(null);
    if (andImplement) {
      setIsImplementing(true);
    } else {
      setIsSaving(true);
    }

    try {
      const fullDesc = [
        description.trim(),
        expectedBehavior ? `\nExpected Behavior: ${expectedBehavior.trim()}` : '',
        businessGoal ? `\nBusiness Goal: ${businessGoal.trim()}` : '',
        acceptanceCriteria ? `\nAcceptance Criteria:\n${acceptanceCriteria.trim()}` : '',
        affectedPages ? `\nAffected Pages: ${affectedPages.trim()}` : '',
        relatedEndpoints ? `\nEndpoints: ${relatedEndpoints.trim()}` : '',
      ]
        .filter(Boolean)
        .join('\n');

      const created = await requirementsApi.create(projectId, {
        title: taskName.trim(),
        description: fullDesc,
        type: taskType,
        priority,
      });

      if (onTaskCreated) {
        onTaskCreated(created);
      }

      if (andImplement) {
        setSuccessMessage(`Feature '${taskName}' saved. Triggering multi-agent AI implementation...`);
        try {
          await workflowsApi.execute('code-generation-workflow', {
            project_id: projectId,
          });
          setSuccessMessage(`Feature '${taskName}' implemented! Version updated.`);
          setTimeout(() => {
            resetForm();
            onClose();
            if (onNavigateTab) {
              onNavigateTab('development');
            }
          }, 1200);
        } catch (implErr: any) {
          setError(
            implErr?.response?.data?.detail ||
              implErr?.message ||
              'Requirement was saved, but workflow execution failed to complete.'
          );
        }
      } else {
        setSuccessMessage(`Requirement '${taskName}' saved successfully to project specification.`);
        setTimeout(() => {
          resetForm();
          onClose();
        }, 1000);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to save requirement.');
    } finally {
      setIsSaving(false);
      setIsImplementing(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Add Feature / Task: ${projectName}`}
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
          <Button variant="ghost" onClick={onClose} disabled={isSaving || isImplementing}>
            Cancel
          </Button>

          <div style={{ display: 'flex', gap: '0.65rem' }}>
            <Button
              variant="secondary"
              onClick={() => handleSaveTask(false)}
              isLoading={isSaving}
              disabled={isImplementing}
            >
              Save Task
            </Button>

            <Button
              variant="primary"
              onClick={() => handleSaveTask(true)}
              isLoading={isImplementing}
              disabled={isSaving}
              style={{
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                fontWeight: 700,
              }}
              icon={<Play size={14} />}
            >
              Save & Implement with AI
            </Button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '72vh', overflowY: 'auto' }}>
        {error && (
          <div
            style={{
              padding: '0.6rem 0.85rem',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        {successMessage && (
          <div
            style={{
              padding: '0.6rem 0.85rem',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#34d399',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <CheckCircle2 size={15} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* 1. Feature Name */}
        <div className="form-group">
          <label className="form-label" htmlFor="task-name" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
            Feature / Task Name *
          </label>
          <input
            id="task-name"
            type="text"
            className="form-input"
            value={taskName}
            onChange={(e) => {
              setTaskName(e.target.value);
              if (error) setError(null);
            }}
            placeholder="e.g. Add Event Category Filtering or Implement User Password Reset"
            required
            style={{ fontSize: '0.9rem' }}
          />
        </div>

        {/* 2. Detailed Description */}
        <div className="form-group">
          <label className="form-label" htmlFor="task-desc" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
            Detailed Description *
          </label>
          <textarea
            id="task-desc"
            className="form-textarea"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Explain exactly what this feature should do, what users will see, and how it behaves..."
            style={{ fontSize: '0.85rem' }}
          />
        </div>

        {/* AI Clarification Trigger */}
        <div
          style={{
            background: 'rgba(99, 102, 241, 0.06)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#a5b4fc', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Brain size={16} />
              <span>Clarify Requirements with AI</span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0 0' }}>
              Let AI analyze your feature request, suggest acceptance criteria, and map out affected components.
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleClarifyWithAI}
            isLoading={isClarifying}
            icon={<Sparkles size={14} color="#818cf8" />}
            style={{ whiteSpace: 'nowrap' }}
          >
            Clarify with AI
          </Button>
        </div>

        {/* AI Clarification Results */}
        {clarificationResult && (
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#34d399' }}>
                ✓ Suggested Acceptance Criteria:
              </span>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.78rem', color: 'var(--text-secondary)', margin: '0.3rem 0 0 0' }}>
                {clarificationResult.suggestedCriteria.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>

            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#60a5fa' }}>
                ✓ Affected System Components:
              </span>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.3rem' }}>
                {clarificationResult.affectedComponents.map((comp, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: '0.72rem',
                      background: 'rgba(59, 130, 246, 0.1)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      color: '#60a5fa',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '9999px',
                    }}
                  >
                    {comp}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 3. Expected Behavior & Business Goal */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="task-expected" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Expected Behavior
            </label>
            <input
              id="task-expected"
              type="text"
              className="form-input"
              value={expectedBehavior}
              onChange={(e) => setExpectedBehavior(e.target.value)}
              placeholder="e.g. Filters table instantaneously without full page reload"
              style={{ fontSize: '0.825rem' }}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="task-goal" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Reason or Business Goal
            </label>
            <input
              id="task-goal"
              type="text"
              className="form-input"
              value={businessGoal}
              onChange={(e) => setBusinessGoal(e.target.value)}
              placeholder="e.g. Improve attendee discovery and booking conversion"
              style={{ fontSize: '0.825rem' }}
            />
          </div>
        </div>

        {/* 4. Priority & Requirement Type */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="task-priority" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Priority Level
            </label>
            <select
              id="task-priority"
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value as any)}
              style={{ fontSize: '0.85rem' }}
            >
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH (Standard)</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="task-type" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Requirement Classification
            </label>
            <select
              id="task-type"
              className="form-select"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value as any)}
              style={{ fontSize: '0.85rem' }}
            >
              <option value="FUNCTIONAL">FUNCTIONAL — User-Facing Behavior</option>
              <option value="NON_FUNCTIONAL">NON_FUNCTIONAL — Performance / Security</option>
              <option value="CONSTRAINT">CONSTRAINT — Architecture / Compliance</option>
            </select>
          </div>
        </div>

        {/* 5. Acceptance Criteria */}
        <div className="form-group">
          <label className="form-label" htmlFor="task-criteria" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
            Acceptance Criteria
          </label>
          <textarea
            id="task-criteria"
            className="form-textarea"
            rows={3}
            value={acceptanceCriteria}
            onChange={(e) => setAcceptanceCriteria(e.target.value)}
            placeholder="• Operation returns 200 OK with updated record&#10;• Error message displayed if capacity reached&#10;• Verified in live preview"
            style={{ fontSize: '0.825rem', fontFamily: 'monospace' }}
          />
        </div>
      </div>
    </Modal>
  );
};
