/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  preview: {
    port: 4173,
    host: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    testTimeout: 10000,
    hookTimeout: 10000,
    clearMocks: true,
    fileParallelism: false,
    pool: 'forks',
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return;
          }
          const normalized = id.replace(/\\/g, '/');

          // 1. Core React runtime & fundamental primitives
          if (
            normalized.includes('/node_modules/react/') ||
            normalized.includes('/node_modules/react-dom/') ||
            normalized.includes('/node_modules/scheduler/') ||
            normalized.includes('/node_modules/use-sync-external-store/') ||
            normalized.includes('/node_modules/react-is/')
          ) {
            return 'vendor-react';
          }

          // 2. TanStack React Query data client
          if (
            normalized.includes('/node_modules/@tanstack/react-query/') ||
            normalized.includes('/node_modules/@tanstack/query-core/')
          ) {
            return 'vendor-query';
          }

          // 3. UI Icons
          if (normalized.includes('/node_modules/lucide-react/')) {
            return 'vendor-lucide';
          }
        },
      },
    },
  },
});
