import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { EnvironmentWorkspace } from '../views/EnvironmentWorkspace';
import { EnvironmentCard } from '../components/environments/EnvironmentCard';
import { PromotionModal } from '../components/environments/PromotionModal';
import { RollbackModal } from '../components/environments/RollbackModal';
import { DeploymentHistoryFeed } from '../components/environments/DeploymentHistoryFeed';
import { environmentApi } from '../services/environmentApi';
import { developmentVersionApi } from '../services/developmentVersionApi';
import {
  Environment,
  DeploymentRecord,
  PromotionEligibilityResult,
} from '../types/environment';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>{ui}</ProjectProvider>
    </QueryClientProvider>
  );
}

describe('Phase 13: Multi-Environment Development & Deployment Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-phase13-test');
  });

  const mockEnvironments: Environment[] = [
    {
      id: 'env-dev-1',
      project_id: 'proj-phase13-test',
      environment_type: 'DEVELOPMENT',
      name: 'Development',
      status: 'HEALTHY',
      current_version_id: 'ver-10',
      current_version_number: 10,
      current_version_status: 'VERIFIED',
      current_version_hash: 'abc123456789',
      is_production: false,
      configuration: {},
      last_deployed_at: '2026-10-04T12:00:00Z',
      created_at: '2026-10-04T10:00:00Z',
      updated_at: '2026-10-04T12:00:00Z',
    },
    {
      id: 'env-staging-1',
      project_id: 'proj-phase13-test',
      environment_type: 'STAGING',
      name: 'Staging',
      status: 'HEALTHY',
      current_version_id: 'ver-9',
      current_version_number: 9,
      current_version_status: 'VERIFIED',
      current_version_hash: 'def987654321',
      is_production: false,
      configuration: {},
      last_deployed_at: '2026-10-04T11:00:00Z',
      created_at: '2026-10-04T10:00:00Z',
      updated_at: '2026-10-04T11:00:00Z',
    },
    {
      id: 'env-prod-1',
      project_id: 'proj-phase13-test',
      environment_type: 'PRODUCTION',
      name: 'Production',
      status: 'HEALTHY',
      current_version_id: 'ver-8',
      current_version_number: 8,
      current_version_status: 'VERIFIED',
      current_version_hash: 'fff111222333',
      is_production: true,
      configuration: {},
      last_deployed_at: '2026-10-04T09:00:00Z',
      created_at: '2026-10-04T10:00:00Z',
      updated_at: '2026-10-04T09:00:00Z',
    },
  ];

  const mockDeployments: DeploymentRecord[] = [
    {
      id: 'dep-1',
      project_id: 'proj-phase13-test',
      environment_id: 'env-prod-1',
      environment_type: 'PRODUCTION',
      version_id: 'ver-8',
      version_number: 8,
      previous_version_id: 'ver-7',
      previous_version_number: 7,
      operation: 'PROMOTION',
      source_environment_id: 'env-staging-1',
      source_environment_type: 'STAGING',
      status: 'SUCCEEDED',
      requested_by: 'Lead Architect',
      started_at: '2026-10-04T09:00:00Z',
      completed_at: '2026-10-04T09:00:05Z',
      created_at: '2026-10-04T09:00:00Z',
      metadata_payload: { notes: 'Production release v8' },
    },
    {
      id: 'dep-2',
      project_id: 'proj-phase13-test',
      environment_id: 'env-staging-1',
      environment_type: 'STAGING',
      version_id: 'ver-9',
      version_number: 9,
      operation: 'PROMOTION',
      source_environment_type: 'DEVELOPMENT',
      status: 'SUCCEEDED',
      requested_by: 'Engineer',
      started_at: '2026-10-04T11:00:00Z',
      completed_at: '2026-10-04T11:00:02Z',
      created_at: '2026-10-04T11:00:00Z',
    },
  ];

  it('renders EnvironmentCard with version pointer and promote button', () => {
    const onPromote = vi.fn();
    const onDeploy = vi.fn();
    const onRollback = vi.fn();

    render(
      <EnvironmentCard
        environment={mockEnvironments[0]}
        onPromote={onPromote}
        onDeploy={onDeploy}
        onRollback={onRollback}
      />
    );

    expect(screen.getByText('Development')).toBeDefined();
    expect(screen.getByText('DEV')).toBeDefined();
    expect(screen.getByText('v10')).toBeDefined();
    expect(screen.getByText('Promote to Staging')).toBeDefined();

    fireEvent.click(screen.getByText('Promote to Staging'));
    expect(onPromote).toHaveBeenCalledWith(mockEnvironments[0]);
  });

  it('renders EnvironmentCard for Production with safeguard badge and without promote button', () => {
    render(<EnvironmentCard environment={mockEnvironments[2]} />);

    expect(screen.getByText('Production')).toBeDefined();
    expect(screen.getByText('PROD')).toBeDefined();
    expect(screen.getByText('v8')).toBeDefined();
    expect(screen.queryByText(/Promote to/)).toBeNull();
  });

  it('evaluates and displays promotion eligibility in PromotionModal', async () => {
    const mockEligibility: PromotionEligibilityResult = {
      eligible: true,
      version_id: 'ver-10',
      version_number: 10,
      source_environment: 'DEVELOPMENT',
      target_environment: 'STAGING',
      reasons: ['Version is verified and eligible for promotion to STAGING.'],
      passed_checks: [
        'Candidate version exists and belongs to project',
        'Verification status passed',
      ],
      failed_checks: [],
      warnings: [],
      requires_confirmation: false,
    };

    vi.spyOn(environmentApi, 'checkPromotionEligibility').mockResolvedValue(mockEligibility);
    vi.spyOn(environmentApi, 'promoteVersion').mockResolvedValue(mockDeployments[1]);

    const onClose = vi.fn();
    const onSuccess = vi.fn();

    render(
      <PromotionModal
        isOpen={true}
        onClose={onClose}
        projectId="proj-phase13-test"
        sourceEnvironment={mockEnvironments[0]}
        targetEnvironmentType="STAGING"
        candidateVersionId="ver-10"
        candidateVersionNumber={10}
        onPromoteSuccess={onSuccess}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Promotion Gate Passed')).toBeDefined();
      expect(screen.getByText('Candidate version exists and belongs to project')).toBeDefined();
    });

    const confirmBtn = screen.getByText('Confirm Promotion');
    expect(confirmBtn.closest('button')?.disabled).toBe(false);

    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(environmentApi.promoteVersion).toHaveBeenCalledWith('proj-phase13-test', {
        version_id: 'ver-10',
        target_environment: 'STAGING',
        source_environment: 'DEVELOPMENT',
        requested_by: 'Engineer',
      });
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('blocks promotion in PromotionModal when eligibility check fails', async () => {
    const mockBlockedEligibility: PromotionEligibilityResult = {
      eligible: false,
      version_id: 'ver-10',
      version_number: 10,
      source_environment: 'DEVELOPMENT',
      target_environment: 'PRODUCTION',
      reasons: ['Promotion to PRODUCTION requires prior deployment to STAGING.'],
      passed_checks: ['Candidate version exists and belongs to project'],
      failed_checks: ['Version has not been deployed to STAGING'],
      warnings: [],
      requires_confirmation: true,
    };

    vi.spyOn(environmentApi, 'checkPromotionEligibility').mockResolvedValue(mockBlockedEligibility);

    render(
      <PromotionModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-phase13-test"
        sourceEnvironment={mockEnvironments[0]}
        targetEnvironmentType="PRODUCTION"
        candidateVersionId="ver-10"
        candidateVersionNumber={10}
        onPromoteSuccess={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Promotion Gate Blocked')).toBeDefined();
      expect(screen.getByText('Version has not been deployed to STAGING')).toBeDefined();
    });

    const confirmBtn = screen.getByText('Confirm Promotion');
    expect(confirmBtn.closest('button')?.disabled).toBe(true);
  });

  it('handles rollback in RollbackModal with required audit reason', async () => {
    vi.spyOn(environmentApi, 'rollbackEnvironment').mockResolvedValue({
      ...mockDeployments[0],
      operation: 'ROLLBACK',
      version_id: 'ver-7',
      version_number: 7,
    });

    const onSuccess = vi.fn();
    const onClose = vi.fn();

    render(
      <RollbackModal
        isOpen={true}
        onClose={onClose}
        projectId="proj-phase13-test"
        environment={mockEnvironments[2]}
        availableVersions={[
          { version_id: 'ver-8', version_number: 8, status: 'ACTIVE' },
          { version_id: 'ver-7', version_number: 7, status: 'VERIFIED' },
          { version_id: 'ver-6', version_number: 6, status: 'VERIFIED' },
        ]}
        onRollbackSuccess={onSuccess}
      />
    );

    expect(screen.getByText(/Rollback Production/)).toBeDefined();
    expect(screen.getByText('Non-Destructive Invariant:')).toBeDefined();

    const rollbackBtn = screen.getByText('Execute Rollback');
    expect(rollbackBtn.closest('button')?.disabled).toBe(true);

    // Select target version
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'ver-7' } });

    // Enter audit reason
    const textarea = screen.getByPlaceholderText(/Critical regression observed/);
    fireEvent.change(textarea, { target: { value: 'Regression in checkout flow observed in prod' } });

    expect(rollbackBtn.closest('button')?.disabled).toBe(false);
    fireEvent.click(rollbackBtn);

    await waitFor(() => {
      expect(environmentApi.rollbackEnvironment).toHaveBeenCalledWith(
        'proj-phase13-test',
        'env-prod-1',
        {
          target_version_id: 'ver-7',
          requested_by: 'Engineer',
          reason: 'Regression in checkout flow observed in prod',
        }
      );
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('renders DeploymentHistoryFeed with operations and version transitions', () => {
    render(
      <DeploymentHistoryFeed
        deployments={mockDeployments}
        isLoading={false}
      />
    );

    expect(screen.getByText('Append-Only Deployment History')).toBeDefined();
    expect(screen.getByText('(2 records)')).toBeDefined();
    expect(screen.getAllByText('PROMOTION').length).toBe(2);
    expect(screen.getByText('Lead Architect')).toBeDefined();
    expect(screen.getByText('v7')).toBeDefined();
    expect(screen.getByText('v8')).toBeDefined();
  });

  it('loads and renders full EnvironmentWorkspace with metrics and environment cards', async () => {
    vi.spyOn(environmentApi, 'listEnvironments').mockResolvedValue(mockEnvironments);
    vi.spyOn(developmentVersionApi, 'listVersions').mockResolvedValue({
      items: [
        {
          version_id: 'ver-10',
          project_id: 'proj-phase13-test',
          version_number: 10,
          artifact_key: 'art-10',
          status: 'VERIFIED',
          is_active: true,
          content_hash: 'abc',
          manifest_hash: 'def',
          file_count: 5,
          total_size_bytes: 1024,
          source_reason: 'Testing',
          created_by: 'System',
          requirement_ids: [],
          files_manifest: [],
          created_at: '2026-10-04T12:00:00Z',
        },
      ],
      total: 1,
    });
    vi.spyOn(environmentApi, 'listDeployments').mockResolvedValue(mockDeployments);

    renderWithProviders(<EnvironmentWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('Environments & Continuous Deployment')).toBeDefined();
      expect(screen.getByText('Active Environments')).toBeDefined();
      expect(screen.getAllByText('v8').length).toBeGreaterThan(0);
      expect(screen.getByText('Development')).toBeDefined();
      expect(screen.getByText('Staging')).toBeDefined();
      expect(screen.getByText('Production')).toBeDefined();
    });
  });
});
