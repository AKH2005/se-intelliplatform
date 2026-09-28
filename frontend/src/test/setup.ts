import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';

// Clean up after each test
afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});
