import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskArtifact } from '../components/artifacts/RiskArtifact';
import { BugPredictionArtifact } from '../components/artifacts/BugPredictionArtifact';
import { TimelineArtifact } from '../components/artifacts/TimelineArtifact';
import { ArchitectureArtifact } from '../components/artifacts/ArchitectureArtifact';
import { ExplainabilityArtifact } from '../components/artifacts/ExplainabilityArtifact';
import {
  ArchitectureRecommendationOutput,
  BugPredictionOutput,
  ExplainabilityOutput,
  RiskPredictionOutput,
  TimelinePredictionOutput,
} from '../types/artifacts';

describe('Contract-Sensitive ML and Agent Rendering Safety', () => {
  it('Risk Artifact: renders on 1.0 - 10.0 scale and deterministic band without 0-1 meters or invented factors', () => {
    const riskData: RiskPredictionOutput = {
      summary: 'Empirical risk assessment derived from dataset features.',
      predicted_risk_score: 5.42,
      risk_level: 'MEDIUM',
      feature_summary: {
        Team_Experience: 3,
        Requirements_Volatility: 4,
      },
      model_provenance: {
        model_name: 'risk_rf_model',
        model_version: '1.0.0',
        algorithm: 'RandomForestRegressor',
        training_dataset: 'risk_dataset.csv',
        feature_schema_version: '1.0',
        artifact_checksum: 'sha256-abc',
      },
      limitations: ['Test R² is negative', 'Dataset size limited to 585 projects'],
    };

    const { container } = render(<RiskArtifact artifact={riskData} />);

    // Score on 1-10 scale
    expect(screen.getByText('5.42')).toBeInTheDocument();
    expect(screen.getByText('/ 10.0 scale')).toBeInTheDocument();
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();

    // Invariants: Should NOT contain invented percentage meters or 0-1 scales
    expect(container.textContent).not.toContain('%');
    expect(container.textContent).not.toContain('/ 1.0');
    expect(container.textContent).not.toContain('0.54');
    expect(screen.getByText('Test R² is negative')).toBeInTheDocument();
  });

  it('Bug Artifact: renders strictly DEFECTIVE label and handles probability accurately', () => {
    const defectiveData: BugPredictionOutput = {
      summary: 'Static analysis indicates high defect probability in module.',
      prediction_label: 'DEFECTIVE',
      predicted_probability: 0.732,
      target: 'defects',
      model_provenance: {
        model_name: 'nasa_jm1_nb',
        model_version: '1.0.0',
        algorithm: 'GaussianNB',
        training_dataset: 'NASA_JM1',
        feature_schema_version: '1.0',
        artifact_checksum: 'checksum123',
      },
      feature_names: ['loc', 'v(g)'],
      feature_summary: { loc: 140, 'v(g)': 12 },
      limitations: ['Advisory quality indicator only'],
    };

    const { container } = render(<BugPredictionArtifact artifact={defectiveData} />);

    expect(screen.getByText('DEFECTIVE')).toBeInTheDocument();
    expect(screen.getByText('73.2%')).toBeInTheDocument();

    // Must NOT contain forbidden stale labels
    expect(container.textContent).not.toContain('DEFECT_PRONE');
    expect(container.textContent).not.toContain('NOT_DEFECT_PRONE');
  });

  it('Bug Artifact: renders NON_DEFECTIVE and does NOT fabricate probability when omitted', () => {
    const nonDefectiveData: BugPredictionOutput = {
      summary: 'Static complexity within normal bounds.',
      prediction_label: 'NON_DEFECTIVE',
      predicted_probability: undefined as any,
      target: 'defects',
      model_provenance: {
        model_name: 'nasa_jm1_nb',
        model_version: '1.0.0',
        algorithm: 'GaussianNB',
        training_dataset: 'NASA_JM1',
        feature_schema_version: '1.0',
        artifact_checksum: 'checksum123',
      },
      feature_names: ['loc'],
      feature_summary: { loc: 25 },
      limitations: ['Advisory only'],
    };

    const { container } = render(<BugPredictionArtifact artifact={nonDefectiveData} />);

    expect(screen.getByText('NON_DEFECTIVE')).toBeInTheDocument();
    // Invariant: Classifier Probability block must not be rendered when probability is omitted
    expect(container.textContent).not.toContain('Classifier Probability');
    expect(container.textContent).not.toContain('NaN');
  });

  it('Timeline Artifact: renders duration point estimates without fabricating confidence intervals', () => {
    const timelineData: TimelinePredictionOutput = {
      summary: 'Estimated elapsed time for functional requirements.',
      predicted_duration_months: 6.84,
      estimated_duration_months: 7.0,
      target: 'Duration',
      target_unit: 'months',
      model_provenance: {
        model_name: 'china_linear_ridge',
        model_version: '1.0.0',
        algorithm: 'Ridge',
        training_dataset: 'China_Software_Projects',
        feature_schema_version: '1.0',
        artifact_checksum: 'checksum-timeline',
      },
      feature_names: ['AfFP', 'Input', 'Output'],
      feature_summary: { AfFP: 180, Input: 22, Output: 14 },
      limitations: ['The continuous point estimate represents expected elapsed months, not a contractually binding project management deadline.'],
    };

    const { container } = render(<TimelineArtifact artifact={timelineData} />);

    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('6.84')).toBeInTheDocument();

    // Invariants: No fabricated intervals or confidence scores
    expect(container.textContent).not.toContain('confidence interval');
    expect(container.textContent).not.toContain('95% CI');
    expect(container.textContent).not.toContain('minimum duration');
    expect(container.textContent).not.toContain('maximum duration');
  });

  it('Architecture Artifact: renders styles, components, and trade-offs without inventing overall quality score', () => {
    const archData: ArchitectureRecommendationOutput = {
      summary: 'Modular Monolith architecture recommended for current team scale.',
      architecture_styles: [
        {
          style: 'MODULAR_MONOLITH',
          rationale: 'Provides clear domain boundaries while minimizing distributed system operational overhead.',
          confidence: 0.85,
        },
      ],
      components: [
        {
          name: 'Core Application Service',
          responsibility: 'Handles domain workflows and state',
          reason: 'Encapsulates business rules',
          related_requirement_ids: [],
        },
      ],
      data_flows: [],
      technologies: [
        {
          technology: 'FastAPI',
          category: 'BACKEND',
          reason: 'High performance async Python',
          trade_off: 'Async library ecosystem learning curve',
        },
      ],
      trade_offs: [
        {
          decision_area: 'Architecture Paradigm',
          recommended_option: 'Modular Monolith',
          advantages: ['Simpler operational model', 'Single deployment artifact'],
          disadvantages: ['Shared database coupling if undisciplined'],
          alternative: 'Microservices',
          alternative_tradeoff: 'Higher operational and latency overhead',
        },
      ],
      assumptions: [],
      constraints: [],
      unknowns: [],
      traceability_matrix: [],
    };

    const { container } = render(<ArchitectureArtifact artifact={archData} />);

    expect(screen.getByText('MODULAR_MONOLITH')).toBeInTheDocument();
    expect(screen.getByText('Core Application Service')).toBeInTheDocument();
    expect(screen.getByText('FastAPI')).toBeInTheDocument();

    // Invariants: No fabricated overall quality scores or rankings
    expect(container.textContent).not.toContain('Architecture Score');
    expect(container.textContent).not.toContain('Architecture Quality');
    expect(container.textContent).not.toContain('Architecture Ranking');
  });

  it('Explainability Artifact: preserves exact claim types (FACT, INTERPRETATION, RECOMMENDATION, LIMITATION)', () => {
    const explainData: ExplainabilityOutput = {
      summary: 'Cross-agent correlation and rationale.',
      insights: [
        {
          insight_id: 'INSIGHT-001',
          category: 'CROSS_CUTTING',
          title: 'Risk and Timeline Convergence',
          summary: 'High function point volume drives longer timeline estimate.',
          explanation: 'Function point metrics correlate with historical duration and moderate complexity.',
          source_references: [
            {
              agent_id: 'timeline-prediction',
              source_entity_id: 'predicted_duration_months',
              source_field: 'predicted_duration_months',
              claim_type: 'FACT',
            },
            {
              agent_id: 'explainability-insights',
              source_entity_id: null,
              source_field: null,
              claim_type: 'INTERPRETATION',
            },
            {
              agent_id: 'risk-prediction',
              source_entity_id: null,
              source_field: null,
              claim_type: 'RECOMMENDATION',
            },
            {
              agent_id: 'timeline-prediction',
              source_entity_id: null,
              source_field: 'limitations',
              claim_type: 'LIMITATION',
            },
          ],
          suggested_actions: ['Review requirement scope before sprint freeze'],
        },
      ],
      metrics: {
        analyzed_agents: ['timeline-prediction', 'risk-prediction'],
        total_insights: 1,
        insights_by_category: { CROSS_CUTTING: 1 },
        claims_count_by_type: { FACT: 1, INTERPRETATION: 1, RECOMMENDATION: 1, LIMITATION: 1 },
      },
      limitations: ['Explanations reflect upstream outputs provided in execution run.'],
    };

    render(<ExplainabilityArtifact artifact={explainData} />);

    expect(screen.getByText('FACT')).toBeInTheDocument();
    expect(screen.getByText('INTERPRETATION')).toBeInTheDocument();
    expect(screen.getByText('RECOMMENDATION')).toBeInTheDocument();
    expect(screen.getByText('LIMITATION')).toBeInTheDocument();
    expect(screen.getByText('INSIGHT-001')).toBeInTheDocument();
    expect(screen.getByText('Risk and Timeline Convergence')).toBeInTheDocument();
  });
});
