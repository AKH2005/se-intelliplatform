/**
 * RFC 7807 Problem Details representation and core API structures.
 */

export interface ProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  trace_id?: string;
  invalid_params?: Array<{ name: string; reason: string }>;
  errors?: Record<string, string[]>;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly problemDetails?: ProblemDetails;
  public readonly correlationId?: string;

  constructor(
    status: number,
    message: string,
    problemDetails?: ProblemDetails,
    correlationId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.problemDetails = problemDetails;
    this.correlationId = correlationId;
  }
}
