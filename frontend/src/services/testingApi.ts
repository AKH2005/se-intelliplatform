/**
 * Phase 11L: Testing Intelligence & Regression REST API Client
 *
 * Exposes authoritative Stage 1–6 backend capabilities:
 * - Test Inventory (11L-1)
 * - Multi-Tier Coverage (11L-2)
 * - Coverage Gaps (11L-2 / 11L-6)
 * - Change Impact Analysis (11L-3)
 * - Selective Regression Planning (11L-4)
 * - Selective Regression Execution (11L-5)
 */

import { apiClient } from './apiClient';
import {
  ChangeImpactReport,
  ChangeImpactRequest,
  CoverageGapsResponse,
  ExecuteRegressionRequest,
  PlanRegressionRequest,
  RegressionExecutionResult,
  RegressionPlan,
  UnifiedCoverageReport,
  UnifiedTestInventory,
} from '../types/testing';

export const testingApi = {
  /**
   * Retrieve the authoritative Unified Test Inventory across all four testing tiers.
   */
  getTestInventory: (
    projectId: string,
    versionId?: string,
    strict: boolean = true
  ): Promise<UnifiedTestInventory> => {
    const params: Record<string, string | boolean> = { strict };
    if (versionId) {
      params.version_id = versionId;
    }
    return apiClient.get<UnifiedTestInventory>(`/projects/${projectId}/testing/inventory`, { params });
  },

  /**
   * Compute multi-tier requirement coverage across UNIT, AI_TEST, BROWSER_SMOKE, and BROWSER_JOURNEY.
   */
  getCoverage: (
    projectId: string,
    versionId?: string
  ): Promise<UnifiedCoverageReport> => {
    const params = versionId ? { version_id: versionId } : undefined;
    return apiClient.get<UnifiedCoverageReport>(`/projects/${projectId}/testing/coverage`, { params });
  },

  /**
   * Derive uncovered active requirements and gap analysis from the authoritative coverage report.
   */
  getCoverageGaps: (
    projectId: string,
    versionId?: string
  ): Promise<CoverageGapsResponse> => {
    const params = versionId ? { version_id: versionId } : undefined;
    return apiClient.get<CoverageGapsResponse>(`/projects/${projectId}/testing/coverage/gaps`, { params });
  },

  /**
   * Perform deterministic AST dependency graph analysis and change impact calculation.
   */
  analyzeImpact: (
    projectId: string,
    request: ChangeImpactRequest
  ): Promise<ChangeImpactReport> => {
    return apiClient.post<ChangeImpactReport>(`/projects/${projectId}/testing/impact`, request);
  },

  /**
   * Generate a deterministic regression plan (SELECTIVE, BROAD, or FULL mode).
   */
  planRegression: (
    projectId: string,
    request: PlanRegressionRequest
  ): Promise<RegressionPlan> => {
    return apiClient.post<RegressionPlan>(`/projects/${projectId}/testing/regression/plan`, request);
  },

  /**
   * Execute an authoritative regression plan across platform test runners in isolated sandboxes.
   */
  executeRegression: (
    projectId: string,
    request: ExecuteRegressionRequest
  ): Promise<RegressionExecutionResult> => {
    return apiClient.post<RegressionExecutionResult>(`/projects/${projectId}/testing/regression/execute`, request);
  },
};
