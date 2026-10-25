import { ApiError, ProblemDetails } from '../types/api';

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1';

function getBaseUrl(): string {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  return DEFAULT_BASE_URL;
}

function generateCorrelationId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export interface RequestOptions extends RequestInit {
  correlationId?: string;
  params?: Record<string, string | number | boolean | undefined | null>;
  timeoutMs?: number;
}

export class HttpClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getBaseUrl();
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined | null>): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const url = new URL(`${this.baseUrl}${cleanPath}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    return url.toString();
  }

  public async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, correlationId, headers, ...restOptions } = options;
    const url = this.buildUrl(path, params);

    const activeCorrelationId = correlationId || generateCorrelationId();
    const finalHeaders = new Headers(headers);

    if (!finalHeaders.has('Content-Type') && restOptions.body) {
      finalHeaders.set('Content-Type', 'application/json');
    }
    if (!finalHeaders.has('Accept')) {
      finalHeaders.set('Accept', 'application/json, application/problem+json');
    }
    finalHeaders.set('X-Correlation-ID', activeCorrelationId);

    // Automatically attach Bearer token if present
    if (typeof localStorage !== 'undefined') {
      const token = localStorage.getItem('se_auth_token');
      if (token && !finalHeaders.has('Authorization')) {
        finalHeaders.set('Authorization', `Bearer ${token}`);
      }
    }

    const timeoutMs = options.timeoutMs ?? 10000;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    let response: Response;
    try {
      response = await fetch(url, {
        ...restOptions,
        headers: finalHeaders,
        signal: restOptions.signal || controller.signal,
      });
    } catch (networkError: any) {
      if (networkError.name === 'AbortError') {
        throw new ApiError(
          0,
          `Request timed out after ${timeoutMs}ms reaching ${url}`,
          undefined,
          activeCorrelationId
        );
      }
      throw new ApiError(
        0,
        `Network error: unable to reach backend service at ${url}`,
        undefined,
        activeCorrelationId
      );
    } finally {
      clearTimeout(timer);
    }

    const responseCorrelationId = response.headers.get('X-Correlation-ID') || activeCorrelationId;

    if (!response.ok) {
      let problemDetails: ProblemDetails | undefined;
      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;

      try {
        const data = await response.json();
        if (data && typeof data === 'object') {
          problemDetails = data as ProblemDetails;
          errorMessage = data.detail || data.title || errorMessage;
        }
      } catch {
        try {
          const text = await response.text();
          if (text) errorMessage = text;
        } catch {
          // Keep default errorMessage
        }
      }

      throw new ApiError(response.status, errorMessage, problemDetails, responseCorrelationId);
    }

    // 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/plain') || contentType.includes('text/html')) {
      return (await response.text()) as unknown as T;
    }

    try {
      return await response.json();
    } catch (parseError) {
      return {} as T;
    }
  }

  public get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' });
  }

  public post<T>(path: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(path: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public patch<T>(path: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new HttpClient();
