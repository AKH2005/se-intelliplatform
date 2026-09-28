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
});
