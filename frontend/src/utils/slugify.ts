export const SLUG_REGEX = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

/**
 * Deterministically derives a URL-safe, backend-compatible slug from a project name.
 * 1. Converts to lowercase
 * 2. Replaces non-alphanumeric character sequences with '-'
 * 3. Trims leading and trailing '-'
 * 4. Truncates to max length 100 while ensuring no trailing '-'
 */
export function slugify(name: string): string {
  if (!name) return '';
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 100)
    .replace(/-+$/, '');
}

export function isValidSlug(slug: string): boolean {
  return SLUG_REGEX.test(slug) && slug.length >= 1 && slug.length <= 100;
}
