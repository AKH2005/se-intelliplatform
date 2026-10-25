import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ProjectProvider } from './context/ProjectContext';
import { isProjectNotFoundError } from './utils/projectRecovery';
import { App } from './App';
import './styles/tokens.css';
import './styles/globals.css';
import './styles/components.css';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (isProjectNotFoundError(error)) {
        window.dispatchEvent(
          new CustomEvent('project:not-found', {
            detail: { error },
          })
        );
      }
    },
  }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Do not retry 4xx client errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
      staleTime: 5000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProjectProvider>
          <App />
        </ProjectProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
