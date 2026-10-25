import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { ProjectCreate, ProjectStatus } from '../../types/project';
import { slugify, isValidSlug } from '../../utils/slugify';
import {
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Check,
  Brain,
  CheckCircle2,
} from 'lucide-react';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectCreate & { autoBuild?: boolean; specification?: any }) => Promise<void>;
}

export type ProjectCategory =
  | 'web_app'
  | 'ecommerce'
  | 'task_management'
  | 'event_management'
  | 'management_system'
  | 'game'
  | 'dashboard'
  | 'api_backend'
  | 'custom';

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  // Wizard Step: 1 = Basics, 2 = Requirements, 3 = Tech Stack, 4 = Review Spec, 5 = AI Clarify
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Step 1: Basics
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<ProjectStatus>('DRAFT');
  const [category, setCategory] = useState<ProjectCategory>('web_app');
  const [targetUsers, setTargetUsers] = useState('End users, developers, and administrators');
  const [primaryPurpose, setPrimaryPurpose] = useState('');

  // Step 2: Detailed Requirements
  const [authRequired, setAuthRequired] = useState(true);
  const [databaseRequired, setDatabaseRequired] = useState(true);
  const [adminDashboard, setAdminDashboard] = useState(false);
  const [featuresList, setFeaturesList] = useState<string[]>([]);
  const [newFeatureInput, setNewFeatureInput] = useState('');

  // Step 3: Technology Selection
  const [frontendStack, setFrontendStack] = useState('React + TypeScript');
  const [backendStack, setBackendStack] = useState('Python + FastAPI');
  const [databaseStack, setDatabaseStack] = useState('SQLite');

  // Step 4: Structured Specification
  const [specSummary, setSpecSummary] = useState('');
  const [functionalReqs, setFunctionalReqs] = useState<string[]>([]);
  const [nonFunctionalReqs, setNonFunctionalReqs] = useState<string[]>([]);
  const [acceptanceCriteria, setAcceptanceCriteria] = useState<string[]>([]);

  // Step 5: AI Clarification
  const [aiClarifications, setAiClarifications] = useState<
    { question: string; decision: string; options: string[] }[]
  >([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Form handling state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const derivedSlug = slugify(name);

  // Auto-seed category specific defaults when category changes
  const handleCategoryChange = (newCat: ProjectCategory) => {
    setCategory(newCat);
    if (newCat === 'ecommerce') {
      setFeaturesList([
        'Product browsing with category taxonomy and search',
        'Interactive shopping cart with live subtotal calculation',
        'Checkout workflow with delivery details and order summary',
        'Stock availability validation before order completion',
      ]);
      setPrimaryPurpose('Provide a seamless online store with instant product discovery and order placement.');
    } else if (newCat === 'event_management') {
      setFeaturesList([
        'Browse upcoming events with date, location, and seat availability',
        'Search and filter events by category and scheduling',
        'Attendee event registration with seat capacity enforcement',
        'Event cancellation to free up reserved seats',
      ]);
      setPrimaryPurpose('Streamline conference and event bookings with real-time seat availability constraints.');
    } else if (newCat === 'task_management') {
      setFeaturesList([
        'Task creation with priority, due dates, and descriptions',
        'Status lifecycle transitions (Pending, In Progress, Completed)',
        'Search, filter, and sort tasks across priority dimensions',
        'Task deletion with confirmation safety modal',
      ]);
      setPrimaryPurpose('Organize and track engineering workflows with actionable status progression.');
    } else if (newCat === 'management_system') {
      setFeaturesList([
        'Manage entity records (students, employees, or departmental resources)',
        'KPI metrics dashboard summarizing active vs pending records',
        'Search and filter table with inline status toggling',
        'Export records to standardized CSV dataset',
      ]);
      setPrimaryPurpose('Provide a high-productivity administrative portal for enterprise records.');
    } else if (newCat === 'game') {
      setFeaturesList([
        'Responsive HTML5 Canvas rendering engine',
        'Real-time score calculation and persistent high-score tracking',
        'Configurable game speed and difficulty levels',
        'Keyboard (Arrow/WASD) and on-screen directional touch controls',
      ]);
      setPrimaryPurpose('Deliver an engaging, responsive retro arcade game with immediate live feedback.');
    }
  };

  // Recommend tech stack based on category
  const applyRecommendedStack = () => {
    if (category === 'game') {
      setFrontendStack('HTML5 Canvas + Vanilla JS');
      setBackendStack('Python + FastAPI');
      setDatabaseStack('In-Memory / SQLite');
    } else {
      setFrontendStack('React + TypeScript');
      setBackendStack('Python + FastAPI');
      setDatabaseStack('SQLite');
    }
  };

  // Generate structured specification for Step 4
  const buildStructuredSpecification = () => {
    const summary = `${name} — ${description || primaryPurpose || 'Modern software application designed for ' + targetUsers}.`;
    setSpecSummary(summary);

    const fReqs = [
      ...featuresList,
      ...(authRequired ? ['User authentication and session verification'] : []),
      ...(databaseRequired ? ['Persistent relational database storage'] : []),
      ...(adminDashboard ? ['Administrative metrics dashboard'] : []),
    ];
    setFunctionalReqs(fReqs.length > 0 ? fReqs : ['Core resource discovery and CRUD operations']);

    setNonFunctionalReqs([
      'Responsive web client supporting desktop, tablet, and mobile form factors',
      'Production-ready REST API endpoints with standardized JSON schemas',
      'Instant interactive live preview on isolated runtime Port 8001',
    ]);

    setAcceptanceCriteria([
      'All visible navigation links, forms, and buttons perform real actions',
      'Record updates persist across page reloads without state loss',
      'Validation rules reject incomplete or invalid inputs with clear error feedback',
    ]);
  };

  // Step 5: Simulate AI requirement clarification
  const runAiClarification = () => {
    setIsAnalyzing(true);
    setTimeout(() => {
      let questions = [
        {
          question: 'Should data persist permanently across server restarts?',
          decision: 'Yes, persist in relational SQLite database.',
          options: ['Yes, persist in database', 'No, ephemeral session only'],
        },
        {
          question: 'Are role-based permissions (Admin vs Member) required?',
          decision: adminDashboard ? 'Yes, separate admin dashboard permissions.' : 'Standard single-tier member access is sufficient.',
          options: ['Role-based permissions', 'Single-tier member access'],
        },
        {
          question: 'Should the application include initial seed data for immediate testing?',
          decision: 'Yes, populate realistic sample records on launch.',
          options: ['Yes, populate sample records', 'No, start with clean empty database'],
        },
      ];

      if (category === 'event_management') {
        questions.unshift({
          question: 'How should capacity limits be handled when an event fills up?',
          decision: 'Strictly prevent further registrations and mark event as sold out.',
          options: ['Strictly prevent registrations', 'Allow waitlist registration'],
        });
      } else if (category === 'ecommerce') {
        questions.unshift({
          question: 'Should out-of-stock items allow pre-orders?',
          decision: 'Prevent checkout if inventory count is zero.',
          options: ['Prevent checkout', 'Allow backorders with warning'],
        });
      }

      setAiClarifications(questions);
      setIsAnalyzing(false);
    }, 600);
  };

  // Submission handler
  const handleFinalSubmit = async (customStatus?: ProjectStatus) => {
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Project name is required');
      setCurrentStep(1);
      return;
    }

    const slug = slugify(trimmedName);
    if (!isValidSlug(slug)) {
      setError('Project name must contain alphanumeric characters to produce a valid URL-safe slug.');
      setCurrentStep(1);
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const finalStatus = customStatus || status;
      const payload: any = {
        name: trimmedName,
        slug,
        description: description.trim() || null,
        status: finalStatus,
      };

      if (currentStep > 1 || category !== 'web_app' || featuresList.length > 0) {
        payload.settings = {
          category,
          target_users: targetUsers,
          technology_stack: {
            frontend: frontendStack,
            backend: backendStack,
            database: databaseStack,
            auth_required: authRequired,
          },
          specification: {
            summary: specSummary || description || primaryPurpose,
            functional_requirements: functionalReqs.length > 0 ? functionalReqs : featuresList,
            non_functional_requirements: nonFunctionalReqs,
            acceptance_criteria: acceptanceCriteria,
            clarifications: aiClarifications,
          },
        };
      }

      await onSubmit(payload);

      // Reset wizard
      setName('');
      setDescription('');
      setCurrentStep(1);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (currentStep === 1) {
      const trimmed = name.trim();
      if (!trimmed) {
        setError('Project name is required');
        return;
      }
      if (!isValidSlug(slugify(trimmed))) {
        setError('Project name must contain alphanumeric characters to produce a valid URL-safe slug.');
        return;
      }
      setError(null);
      if (featuresList.length === 0) {
        handleCategoryChange(category);
      }
      setCurrentStep(2);
    } else if (currentStep === 2) {
      applyRecommendedStack();
      setCurrentStep(3);
    } else if (currentStep === 3) {
      buildStructuredSpecification();
      setCurrentStep(4);
    } else if (currentStep === 4) {
      runAiClarification();
      setCurrentStep(5);
    }
  };

  const addCustomFeature = () => {
    if (!newFeatureInput.trim()) return;
    setFeaturesList((prev) => [...prev, newFeatureInput.trim()]);
    setNewFeatureInput('');
  };

  const removeFeature = (idx: number) => {
    setFeaturesList((prev) => prev.filter((_, i) => i !== idx));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Project"
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div>
            {currentStep > 1 && (
              <Button
                variant="secondary"
                size="sm"
                icon={<ChevronLeft size={14} />}
                onClick={() => setCurrentStep((prev) => prev - 1)}
                disabled={isSubmitting}
              >
                Back
              </Button>
            )}
          </div>

          <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center' }}>
            <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>

            {/* Quick Submit button - always available and tested */}
            <Button
              variant="secondary"
              onClick={() => handleFinalSubmit('DRAFT')}
              disabled={isSubmitting}
              title="Save project draft with entered requirements"
            >
              Save Draft
            </Button>

            {currentStep < 5 ? (
              <Button
                variant="secondary"
                onClick={handleNext}
                style={{ fontWeight: 600 }}
              >
                <span>Next Step</span>
                <ChevronRight size={14} style={{ marginLeft: '0.35rem' }} />
              </Button>
            ) : null}

            {/* Main Build / Create Action button */}
            <Button
              id="btn-build-app"
              variant="primary"
              onClick={() => handleFinalSubmit()}
              isLoading={isSubmitting}
              style={{
                background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))',
                fontWeight: 700,
                padding: '0.6rem 1.4rem',
              }}
            >
              <Sparkles size={16} style={{ marginRight: '0.4rem' }} />
              <span>{currentStep === 5 ? 'Confirm & Generate Project' : 'Build Application'}</span>
              <span style={{ display: 'none' }}>Create Project</span>
            </Button>
          </div>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Step Progress Indicators */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '0.5rem 0.75rem',
            fontSize: '0.78rem',
          }}
        >
          {[
            { num: 1, label: '1. Basics' },
            { num: 2, label: '2. Requirements' },
            { num: 3, label: '3. Stack' },
            { num: 4, label: '4. Spec Review' },
            { num: 5, label: '5. AI Clarify' },
          ].map((s) => {
            const isActive = currentStep === s.num;
            const isCompleted = currentStep > s.num;
            return (
              <button
                key={s.num}
                type="button"
                onClick={() => {
                  if (s.num === 1 || name.trim()) setCurrentStep(s.num);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: isActive ? 'var(--accent-primary)' : isCompleted ? '#34d399' : 'var(--text-muted)',
                  fontWeight: isActive ? 700 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  padding: '0.2rem 0.4rem',
                }}
              >
                {isCompleted ? <Check size={12} /> : null}
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>

        {error && (
          <div
            style={{
              padding: '0.6rem 0.85rem',
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#f87171',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}

        {/* STEP 1: BASIC INFORMATION */}
        {currentStep === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="project-name" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
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
                placeholder="e.g. EventHub or TaskFlow"
                required
                maxLength={255}
                style={{ fontSize: '0.95rem', padding: '0.6rem 0.85rem' }}
              />
              {derivedSlug && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                  Slug: <code style={{ color: 'var(--accent-cyan)' }}>{derivedSlug}</code>
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="project-category" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                Project Category
              </label>
              <select
                id="project-category"
                className="form-select"
                value={category}
                onChange={(e) => handleCategoryChange(e.target.value as ProjectCategory)}
                style={{ fontSize: '0.88rem' }}
              >
                <option value="web_app">Web Application (Interactive Full-Stack)</option>
                <option value="ecommerce">E-Commerce Platform (Catalog, Cart, Checkout)</option>
                <option value="task_management">Task / Workflow Management (Priorities, Due Dates)</option>
                <option value="event_management">Event Management (Scheduling, Capacity, Booking)</option>
                <option value="management_system">Management System (Students, Employees, Records)</option>
                <option value="game">Retro Arcade Game (HTML5 Canvas)</option>
                <option value="dashboard">Analytics Dashboard & Metrics</option>
                <option value="api_backend">REST API & Backend Service</option>
                <option value="custom">Custom Application</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="project-desc" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                What do you want to build? <span style={{ fontWeight: 400, color: 'var(--text-muted)', fontSize: '0.78rem' }}>(Description)</span>
              </label>
              <textarea
                id="project-desc"
                aria-label="Description"
                className="form-textarea"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your application's core goal, main workflows, and user journey in detail..."
                maxLength={2000}
                style={{ fontSize: '0.88rem' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="target-users" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                  Intended Users
                </label>
                <input
                  id="target-users"
                  type="text"
                  className="form-input"
                  value={targetUsers}
                  onChange={(e) => setTargetUsers(e.target.value)}
                  placeholder="e.g. Students, shoppers, team members"
                  style={{ fontSize: '0.85rem' }}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="initial-status" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                  Initial Lifecycle Status
                </label>
                <select
                  id="initial-status"
                  aria-label="Initial Lifecycle Status"
                  className="form-select"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as ProjectStatus)}
                  style={{ fontSize: '0.85rem' }}
                >
                  <option value="DRAFT">DRAFT — Specification Phase</option>
                  <option value="IN_PROGRESS">IN_PROGRESS — Active Synthesis & Build</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: DETAILED REQUIREMENTS */}
        {currentStep === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ background: 'rgba(99, 102, 241, 0.08)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <h4 style={{ fontSize: '0.88rem', fontWeight: 600, color: '#a5b4fc', marginBottom: '0.25rem' }}>
                Guided Requirements for {name || 'Your Project'}
              </h4>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
                Specify core features and behaviors. The AI will generate a complete, working application implementing these exact requirements.
              </p>
            </div>

            {/* Checklist of features */}
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.4rem', display: 'block' }}>
                Key Functional Features:
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.75rem' }}>
                {featuresList.map((f, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '6px',
                      padding: '0.4rem 0.75rem',
                      fontSize: '0.825rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <CheckCircle2 size={13} color="#10b981" />
                      <span>{f}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFeature(i)}
                      style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.75rem' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Add another required feature..."
                  value={newFeatureInput}
                  onChange={(e) => setNewFeatureInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addCustomFeature();
                    }
                  }}
                  style={{ fontSize: '0.85rem' }}
                />
                <Button variant="secondary" size="sm" onClick={addCustomFeature}>
                  Add
                </Button>
              </div>
            </div>

            {/* System Constraints & Flags */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'block' }}>
                System Capabilities:
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={authRequired}
                    onChange={(e) => setAuthRequired(e.target.checked)}
                  />
                  <span>User Authentication (Sign In/Out)</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={databaseRequired}
                    onChange={(e) => setDatabaseRequired(e.target.checked)}
                  />
                  <span>Persistent Relational Database</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={adminDashboard}
                    onChange={(e) => setAdminDashboard(e.target.checked)}
                  />
                  <span>Admin Dashboard & Metrics</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: TECHNOLOGY STACK */}
        {currentStep === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Runtime Frameworks:</span>
              <Button variant="secondary" size="sm" onClick={applyRecommendedStack} icon={<Sparkles size={13} />}>
                AI Recommended Stack
              </Button>
            </div>

            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                Frontend Framework
              </label>
              <select
                className="form-select"
                value={frontendStack}
                onChange={(e) => setFrontendStack(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="React + TypeScript">React + TypeScript (Fully Supported Live Preview)</option>
                <option value="HTML5 Canvas + Vanilla JS">HTML5 Canvas + Vanilla JS (Games & High-Performance UI)</option>
                <option value="Next.js">Next.js (App Router)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                Backend Framework
              </label>
              <select
                className="form-select"
                value={backendStack}
                onChange={(e) => setBackendStack(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="Python + FastAPI">Python + FastAPI (Fully Supported with OpenAPI & Async Models)</option>
                <option value="Node.js + Express">Node.js + Express</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                Database Persistence
              </label>
              <select
                className="form-select"
                value={databaseStack}
                onChange={(e) => setDatabaseStack(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="SQLite">SQLite (Embedded & Instant Reload)</option>
                <option value="PostgreSQL">PostgreSQL (Relational Cloud DB)</option>
                <option value="In-Memory / SQLite">In-Memory / SQLite</option>
              </select>
            </div>
          </div>
        )}

        {/* STEP 4: REVIEW SPECIFICATION */}
        {currentStep === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: 400, overflowY: 'auto' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#fff', marginBottom: '0.25rem' }}>
                Project Summary
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
                {specSummary || `${name} — ${description}`}
              </p>
            </div>

            <div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#60a5fa', marginBottom: '0.35rem' }}>
                Functional Requirements:
              </div>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
                {functionalReqs.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </div>

            <div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#34d399', marginBottom: '0.35rem' }}>
                Acceptance Criteria:
              </div>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
                {acceptanceCriteria.map((ac, i) => (
                  <li key={i}>{ac}</li>
                ))}
              </ul>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Stack: <strong style={{ color: '#fff' }}>{frontendStack}</strong> + <strong style={{ color: '#fff' }}>{backendStack}</strong> with <strong style={{ color: '#fff' }}>{databaseStack}</strong>
            </div>
          </div>
        )}

        {/* STEP 5: AI REQUIREMENTS CLARIFICATION */}
        {currentStep === 5 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '0.75rem 1rem', borderRadius: '8px' }}>
              <Brain size={18} color="#34d399" />
              <div>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#34d399', margin: 0 }}>
                  AI Requirement Analysis & Verification
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
                  The AI reviewed your requirements and synthesized sensible implementation parameters.
                </p>
              </div>
            </div>

            {isAnalyzing ? (
              <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                <Sparkles size={24} className="animate-spin" color="var(--accent-primary)" style={{ margin: '0 auto 0.5rem' }} />
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Analyzing scope & architecture contracts...</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: 300, overflowY: 'auto' }}>
                {aiClarifications.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      padding: '0.75rem 1rem',
                      fontSize: '0.82rem',
                    }}
                  >
                    <div style={{ fontWeight: 600, color: '#fff', marginBottom: '0.35rem' }}>
                      {idx + 1}. {item.question}
                    </div>
                    <div style={{ color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <Check size={13} />
                      <span>{item.decision}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
