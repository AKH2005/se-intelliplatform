import React, { useState } from 'react';
import { Card, CardBody, CardHeader, CardTitle } from '../common/Card';
import { RiskArtifact } from './RiskArtifact';
import { TimelineArtifact } from './TimelineArtifact';
import { BugPredictionArtifact } from './BugPredictionArtifact';
import { ArchitectureArtifact } from './ArchitectureArtifact';
import { DatabaseArtifact } from './DatabaseArtifact';
import { RequirementAnalysisArtifact } from './RequirementAnalysisArtifact';
import { TestCaseArtifact } from './TestCaseArtifact';
import { CodeReviewArtifact } from './CodeReviewArtifact';
import { ExplainabilityArtifact } from './ExplainabilityArtifact';
import { UnknownArtifact } from './UnknownArtifact';
import { Layers } from 'lucide-react';

interface ArtifactViewerProps {
  artifacts: Record<string, any>;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifacts }) => {
  const artifactKeys = Object.keys(artifacts);

  const [selectedKey, setSelectedKey] = useState<string>(() => {
    return artifactKeys.length > 0 ? artifactKeys[0] : '';
  });

  const activeKey = selectedKey && artifacts[selectedKey] ? selectedKey : artifactKeys[0] || '';

  if (artifactKeys.length === 0) {
    return (
      <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        No output artifacts produced.
      </div>
    );
  }

  const renderSpecificArtifact = (key: string, data: any) => {
    if (!data || typeof data !== 'object') {
      return <UnknownArtifact artifactKey={key} data={data} />;
    }

    // Risk Prediction Artifact
    if ('predicted_risk_score' in data && 'risk_level' in data) {
      return <RiskArtifact artifact={data} />;
    }

    // Timeline Prediction Artifact
    if ('predicted_duration_months' in data || ('estimated_duration_months' in data && data.target === 'Duration')) {
      return <TimelineArtifact artifact={data} />;
    }

    // Bug Prediction Artifact
    if ('prediction_label' in data && (data.prediction_label === 'DEFECTIVE' || data.prediction_label === 'NON_DEFECTIVE')) {
      return <BugPredictionArtifact artifact={data} />;
    }

    // Architecture Recommendation Artifact
    if ('architecture_styles' in data || ('components' in data && 'data_flows' in data)) {
      return <ArchitectureArtifact artifact={data} />;
    }

    // Database Design Artifact
    if ('database_paradigm' in data || ('entities' in data && 'relationships' in data)) {
      return <DatabaseArtifact artifact={data} />;
    }

    // Requirement Analysis Artifact
    if ('ambiguities' in data || 'completeness_score' in data) {
      return <RequirementAnalysisArtifact artifact={data} />;
    }

    // Test Case Generation Artifact
    if ('test_cases' in data && 'coverage' in data) {
      return <TestCaseArtifact artifact={data} />;
    }

    // Code Review Artifact
    if ('files_reviewed' in data || ('findings' in data && 'metrics' in data && 'by_severity' in data.metrics)) {
      return <CodeReviewArtifact artifact={data} />;
    }

    // Explainability Artifact
    if ('insights' in data && 'metrics' in data && 'analyzed_agents' in data.metrics) {
      return <ExplainabilityArtifact artifact={data} />;
    }

    return <UnknownArtifact artifactKey={key} data={data} />;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Layers size={18} color="var(--accent-primary)" />
          Execution Artifacts ({artifactKeys.length})
        </CardTitle>
      </CardHeader>

      <CardBody>
        {/* Artifact Tabs */}
        {artifactKeys.length > 1 && (
          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
              borderBottom: '1px solid var(--border-subtle)',
              paddingBottom: '0.75rem',
              marginBottom: '1.25rem',
              overflowX: 'auto',
            }}
          >
            {artifactKeys.map((key) => {
              const isActive = key === activeKey;
              return (
                <button
                  key={key}
                  onClick={() => setSelectedKey(key)}
                  style={{
                    padding: '0.4rem 0.8rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--border-focus)' : 'var(--border-subtle)',
                    background: isActive ? 'var(--bg-surface-active)' : 'var(--bg-surface)',
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {key}
                </button>
              );
            })}
          </div>
        )}

        {/* Selected Artifact Body */}
        {activeKey && renderSpecificArtifact(activeKey, artifacts[activeKey])}
      </CardBody>
    </Card>
  );
};
