import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from '../context/ProjectContext';
import { CodeIntelligenceWorkspace } from '../views/CodeIntelligenceWorkspace';
import { codeIntelligenceApi } from '../services/codeIntelligenceApi';
import {
  CodeIntelligenceSummaryResponse,
  DependencyGraphResponse,
  FileCodeIntelligenceResponse,
  LanguageInventoryResponse,
} from '../types/codeIntelligence';

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

describe('Phase 14: Polyglot Code Intelligence Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.setItem('se_intelliplatform_active_project_id', 'proj-phase14-test');
  });

  const mockLanguages: LanguageInventoryResponse = {
    project_id: 'proj-phase14-test',
    total_files: 4,
    counts: {
      python: 1,
      typescript: 1,
      javascript: 1,
      java: 1,
    },
    percentages: {
      python: 25.0,
      typescript: 25.0,
      javascript: 25.0,
      java: 25.0,
    },
    supported_languages: ['PYTHON', 'JAVASCRIPT', 'TYPESCRIPT', 'JAVA'],
  };

  const mockSummary: CodeIntelligenceSummaryResponse = {
    project_id: 'proj-phase14-test',
    version_id: 'ver-14',
    version_number: 1,
    total_files: 4,
    total_symbols: 18,
    total_edges: 6,
    total_diagnostics: 1,
    language_breakdown: { python: 1, typescript: 1, javascript: 1, java: 1 },
    unresolved_imports_count: 0,
    uncertain_dependencies_count: 1,
    analyzed_at: '2026-10-05T00:00:00Z',
  };

  const mockGraph: DependencyGraphResponse = {
    project_id: 'proj-phase14-test',
    files_count: 4,
    edges_count: 6,
    forward_adjacency: {
      'src/index.ts': ['src/service.ts'],
      'src/service.ts': [],
    },
    reverse_adjacency: {
      'src/service.ts': ['src/index.ts'],
      'src/index.ts': [],
    },
    language_breakdown: { typescript: 2 },
    unresolved_imports: [],
    uncertain_dependencies: [
      {
        file_path: 'src/dynamic.js',
        reason: 'DYNAMIC_IMPORT_DETECTED',
        line_number: 12,
        raw_statement: 'import(path)',
      },
    ],
    diagnostics_count: 1,
  };

  const mockFileDetails: FileCodeIntelligenceResponse = {
    file_path: 'src/index.ts',
    language: 'typescript',
    is_test_file: false,
    content_hash: 'abc123hash',
    symbols: [
      {
        name: 'UserService',
        kind: 'CLASS',
        is_exported: true,
        line_number: 10,
      },
      {
        name: 'getUser',
        kind: 'METHOD',
        is_exported: true,
        signature: '(): User',
        line_number: 15,
      },
    ],
    imports: [
      {
        module: './service',
        imported_symbols: ['Service'],
        is_dynamic: false,
        is_relative: true,
        line_number: 2,
      },
    ],
    exports: [
      {
        name: 'UserService',
        is_default: false,
        line_number: 10,
      },
    ],
    dependencies: [
      {
        source_file: 'src/index.ts',
        target_file: 'src/service.ts',
        relation: 'IMPORT',
        is_resolved: true,
      },
    ],
    diagnostics: [],
    has_syntax_error: false,
    has_dynamic_constructs: false,
  };

  it('renders code intelligence workspace and displays metrics and language badges', async () => {
    vi.spyOn(codeIntelligenceApi, 'getLanguages').mockResolvedValue(mockLanguages);
    vi.spyOn(codeIntelligenceApi, 'getSummary').mockResolvedValue(mockSummary);
    vi.spyOn(codeIntelligenceApi, 'getGraph').mockResolvedValue(mockGraph);
    vi.spyOn(codeIntelligenceApi, 'getFileDetails').mockResolvedValue(mockFileDetails);

    renderWithProviders(<CodeIntelligenceWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('Polyglot Code Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Deterministic Language Detection')).toBeInTheDocument();
      expect(screen.getByText('Analyzed Files')).toBeInTheDocument();
      expect(screen.getByText('Total Symbols')).toBeInTheDocument();
      expect(screen.getByText('Dependency Edges')).toBeInTheDocument();
    });

    // Check language pills
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('typescript')).toBeInTheDocument();
    expect(screen.getByText('javascript')).toBeInTheDocument();
    expect(screen.getByText('java')).toBeInTheDocument();
  });

  it('allows navigating to File & Symbol Details subtab and viewing extracted symbols', async () => {
    vi.spyOn(codeIntelligenceApi, 'getLanguages').mockResolvedValue(mockLanguages);
    vi.spyOn(codeIntelligenceApi, 'getSummary').mockResolvedValue(mockSummary);
    vi.spyOn(codeIntelligenceApi, 'getGraph').mockResolvedValue(mockGraph);
    vi.spyOn(codeIntelligenceApi, 'getFileDetails').mockResolvedValue(mockFileDetails);

    renderWithProviders(<CodeIntelligenceWorkspace />);

    await waitFor(() => {
      expect(screen.getAllByText('src/index.ts').length).toBeGreaterThan(0);
    });

    const subtabBtn = screen.getByRole('button', { name: /File & Symbol Details/i });
    fireEvent.click(subtabBtn);

    await waitFor(() => {
      expect(screen.getByText(/Extracted Symbols/)).toBeInTheDocument();
      expect(screen.getAllByText('UserService').length).toBeGreaterThan(0);
      expect(screen.getByText('getUser')).toBeInTheDocument();
    });
  });

  it('allows viewing uncertainty and fallback diagnostic records', async () => {
    vi.spyOn(codeIntelligenceApi, 'getLanguages').mockResolvedValue(mockLanguages);
    vi.spyOn(codeIntelligenceApi, 'getSummary').mockResolvedValue(mockSummary);
    vi.spyOn(codeIntelligenceApi, 'getGraph').mockResolvedValue(mockGraph);
    vi.spyOn(codeIntelligenceApi, 'getFileDetails').mockResolvedValue(mockFileDetails);

    renderWithProviders(<CodeIntelligenceWorkspace />);

    await waitFor(() => {
      expect(screen.getByText(/Uncertainty & Diagnostics/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Uncertainty & Diagnostics/));

    await waitFor(() => {
      expect(screen.getByText('DYNAMIC_IMPORT_DETECTED')).toBeInTheDocument();
      expect(screen.getByText(/import\(path\)/)).toBeInTheDocument();
    });
  });

  it('renders empty state when no active project is selected', () => {
    localStorage.removeItem('se_intelliplatform_active_project_id');

    renderWithProviders(<CodeIntelligenceWorkspace />);

    expect(screen.getByText('No Active Project Selected')).toBeInTheDocument();
  });
});
