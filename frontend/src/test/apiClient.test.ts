import { describe, it, expect, vi, beforeEach } from 'vitest';
import { HttpClient } from '../services/apiClient';
import { ApiError } from '../types/api';

describe('Centralized API Client', () => {
  let client: HttpClient;

  beforeEach(() => {
    client = new HttpClient('http://test-api:8000/api/v1');
    vi.restoreAllMocks();
  });

  it('performs successful GET request and returns JSON data', async () => {
    const mockData = { id: 'p1', name: 'Test Project' };
    const mockResponse = new Response(JSON.stringify(mockData), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': 'test-corr-123',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    const result = await client.get('/projects');

    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledTimes(1);

    const calledUrl = (global.fetch as any).mock.calls[0][0];
    const calledOptions = (global.fetch as any).mock.calls[0][1];

    expect(calledUrl).toBe('http://test-api:8000/api/v1/projects');
    expect(calledOptions.headers.get('Accept')).toBe('application/json, application/problem+json');
    expect(calledOptions.headers.get('X-Correlation-ID')).toBeDefined();
  });

  it('handles RFC 7807 problem details error responses', async () => {
    const problemPayload = {
      type: 'about:blank',
      title: 'Project Not Found',
      status: 404,
      detail: "Project '00000000-0000-0000-0000-000000000000' not found.",
      instance: '/api/v1/projects/00000000-0000-0000-0000-000000000000',
    };

    const mockResponse = new Response(JSON.stringify(problemPayload), {
      status: 404,
      statusText: 'Not Found',
      headers: {
        'Content-Type': 'application/problem+json',
        'X-Correlation-ID': 'corr-404-xyz',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    try {
      await client.get('/projects/00000000-0000-0000-0000-000000000000');
      expect.fail('Expected ApiError to be thrown');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(404);
      expect(err.message).toBe("Project '00000000-0000-0000-0000-000000000000' not found.");
      expect(err.problemDetails).toEqual(problemPayload);
      expect(err.correlationId).toBe('corr-404-xyz');
    }
  });

  it('propagates correlation ID on outgoing requests and preserves it on error', async () => {
    const customCorrelationId = 'custom-correlation-999';
    const mockResponse = new Response(JSON.stringify({ detail: 'Unprocessable Entity' }), {
      status: 422,
      statusText: 'Unprocessable Entity',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(mockResponse);

    try {
      await client.post('/workflows/software-design/execute', {}, { correlationId: customCorrelationId });
      expect.fail('Expected ApiError to be thrown');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(422);
      expect(err.correlationId).toBe(customCorrelationId);

      const calledOptions = (global.fetch as any).mock.calls[0][1];
      expect(calledOptions.headers.get('X-Correlation-ID')).toBe(customCorrelationId);
    }
  });

  it('uses configured environment URL or default localhost in local/test environment', () => {
    const defaultClient = new HttpClient();
    const expected = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    expect(defaultClient.getBaseUrl()).toBe(expected);
  });
});

describe('Projects API Download', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('uses apiClient.getBaseUrl() and triggers file download for valid ZIP response', async () => {
    const { projectsApi } = await import('../services/projectsApi');
    const { apiClient } = await import('../services/apiClient');

    const fakeZipBlob = new Blob(['PK\x03\x04fake-zip-binary'], { type: 'application/zip' });
    const mockResponse = new Response(fakeZipBlob, {
      status: 200,
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename="demo-project.zip"',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(mockResponse);
    window.URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/fake-blob');
    window.URL.revokeObjectURL = vi.fn();

    await projectsApi.download('proj-123', 'custom-demo.zip');

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const calledUrl = (global.fetch as any).mock.calls[0][0];
    const expectedBase = apiClient.getBaseUrl();
    expect(calledUrl).toBe(`${expectedBase}/projects/proj-123/download`);
    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });

  it('rejects when response content-type is text/html (SPA fallback protection)', async () => {
    const { projectsApi } = await import('../services/projectsApi');

    const htmlResponse = new Response('<!DOCTYPE html><html><body>SPA Fallback</body></html>', {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(htmlResponse);

    await expect(projectsApi.download('proj-html-fallback')).rejects.toThrow(
      /Received HTML response instead of project ZIP archive/
    );
  });
});
