/**
 * Project Recovery and Error Normalization Utilities
 *
 * Ensures consistent detection and user-friendly presentation of stale or
 * non-existent project contexts (HTTP 404), hiding raw UUIDs by default
 * and providing deterministic recovery pathways.
 */


/**
 * Standard UUID regex pattern (v4 / general UUID format).
 */
export const UUID_REGEX = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

/**
 * Detects whether an error represents a missing or non-existent project (HTTP 404).
 *
 * @param error - The caught error object, ApiError, or string message.
 * @returns boolean indicating if the failure was specifically due to project not found.
 */
export function isProjectNotFoundError(error: unknown): boolean {
  if (!error) return false;

  const err = error as any;
  const status = err.status ?? err.response?.status;

  // Must be an HTTP 404
  if (status !== 404) {
    // If it's a string, inspect content
    if (typeof error === 'string') {
      const lower = error.toLowerCase();
      return (
        lower.includes('project with identifier') ||
        (lower.includes('project') && (lower.includes('was not found') || lower.includes('not found')))
      );
    }
    return false;
  }

  const detail =
    err.problemDetails?.detail ??
    err.problemDetails?.title ??
    err.response?.data?.detail ??
    err.response?.data?.title ??
    err.message ??
    '';

  const resource =
    err.problemDetails?.resource ??
    err.response?.data?.resource;

  if (resource === 'Project') {
    return true;
  }

  const lower = String(detail).toLowerCase();
  if (
    lower.includes('project with identifier') ||
    lower.includes('project not found') ||
    (lower.includes('project') && (lower.includes('not found') || lower.includes('was not found')))
  ) {
    return true;
  }

  // Check URL / instance if available
  const instance = err.problemDetails?.instance ?? err.response?.config?.url ?? '';
  if (typeof instance === 'string' && instance.includes('/projects/')) {
    return true;
  }

  return false;
}

/**
 * Extracts raw UUID if present in a message.
 */
export function extractUuidFromMessage(message: string): string | null {
  const match = message.match(UUID_REGEX);
  return match ? match[0] : null;
}
