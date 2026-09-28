import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { slugify, isValidSlug, SLUG_REGEX } from '../utils/slugify';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { ProjectCreate } from '../types/project';

describe('Project Slug Derivation & Contract Safety', () => {
  it('1. ProjectCreate type requires slug property', () => {
    const validPayload: ProjectCreate = {
      name: 'Smart Software Development Platform',
      slug: 'smart-software-development-platform',
      description: 'Platform overview',
      status: 'DRAFT',
    };

    expect(validPayload.slug).toBe('smart-software-development-platform');
    expect(SLUG_REGEX.test(validPayload.slug)).toBe(true);
  });

  it('2. slugify converts "Smart Software Development Platform" to "smart-software-development-platform"', () => {
    const input = 'Smart Software Development Platform';
    const output = slugify(input);

    expect(output).toBe('smart-software-development-platform');
    expect(isValidSlug(output)).toBe(true);
    expect(SLUG_REGEX.test(output)).toBe(true);
  });

  it('2b. slugify handles complex symbols, punctuation, and multiple dashes deterministically', () => {
    expect(slugify('  Telemetry & Ingestion Service (v2.0)  ')).toBe('telemetry-ingestion-service-v2-0');
    expect(slugify('--leading-and-trailing--')).toBe('leading-and-trailing');
    expect(slugify('Multiple   Spaces   And---Hyphens')).toBe('multiple-spaces-and-hyphens');
    expect(slugify('123 Numbers Allowed 456')).toBe('123-numbers-allowed-456');
  });

  it('3 & 4. CreateProjectModal derives slug and passes it to onSubmit API', async () => {
    const mockOnSubmit = vi.fn().mockResolvedValue(undefined);
    const mockOnClose = vi.fn();

    render(
      <CreateProjectModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/Project Name/i);
    fireEvent.change(nameInput, { target: { value: 'Smart Software Development Platform' } });

    // Verify slug preview in UI
    expect(screen.getByText('smart-software-development-platform')).toBeInTheDocument();

    const submitBtn = screen.getByText('Create Project');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    const submittedData: ProjectCreate = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.name).toBe('Smart Software Development Platform');
    expect(submittedData.slug).toBe('smart-software-development-platform');
    expect(submittedData.status).toBe('DRAFT');
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('5. Invalid or empty project names are handled safely with validation error', async () => {
    const mockOnSubmit = vi.fn();
    const mockOnClose = vi.fn();

    render(
      <CreateProjectModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const submitBtn = screen.getByText('Create Project');

    // Case A: Empty name
    fireEvent.click(submitBtn);
    expect(await screen.findByText('Project name is required')).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();

    // Case B: Non-alphanumeric name that cannot form a valid slug
    const nameInput = screen.getByLabelText(/Project Name/i);
    fireEvent.change(nameInput, { target: { value: '??? ### !!!' } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Project name must contain alphanumeric characters/i)
    ).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('6. Existing project creation flow still works seamlessly', async () => {
    const mockOnSubmit = vi.fn().mockResolvedValue(undefined);
    const mockOnClose = vi.fn();

    render(
      <CreateProjectModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    fireEvent.change(screen.getByLabelText(/Project Name/i), {
      target: { value: 'Core Analytics Engine' },
    });
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'High throughput telemetry processing' },
    });
    fireEvent.change(screen.getByLabelText(/Initial Lifecycle Status/i), {
      target: { value: 'IN_PROGRESS' },
    });

    fireEvent.click(screen.getByText('Create Project'));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Core Analytics Engine',
        slug: 'core-analytics-engine',
        description: 'High throughput telemetry processing',
        status: 'IN_PROGRESS',
      });
    });
  });
});
