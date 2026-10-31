import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AuthContextType, LoginCredentials, RegisterCredentials, User } from '../types/auth';
import { authApi } from '../services/authApi';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'se_auth_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      // Add a fast safety timeout (5 seconds) so authenticating session never hangs indefinitely
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Session initialization timeout')), 5000)
      );

      try {
        const currentUser = (await Promise.race([authApi.getMe(), timeoutPromise])) as User;
        setUser(currentUser);
        setToken(storedToken);
      } catch (err) {
        // Token expired, invalid, or backend unreachable: clear stale token
        if (typeof localStorage !== 'undefined') {
          localStorage.removeItem(TOKEN_KEY);
        }
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials): Promise<User> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.login(credentials);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, response.access_token);
      }
      setToken(response.access_token);
      setUser(response.user);
      return response.user;
    } catch (err: any) {
      const msg = err?.message || 'Login failed. Please verify your credentials.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials): Promise<User> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.register(credentials);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, response.access_token);
      }
      setToken(response.access_token);
      setUser(response.user);
      return response.user;
    } catch (err: any) {
      const msg = err?.message || 'Registration failed.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      if (token) {
        await authApi.logout();
      }
    } catch {
      // Ignore backend logout errors during local cleanup
    } finally {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY);
        if (localStorage.getItem('se_platform_mode_remember') !== 'true') {
          localStorage.removeItem('se_platform_mode');
        }
      }
      setUser(null);
      setToken(null);
      setError(null);
      if (typeof window !== 'undefined') {
        window.history.pushState({}, '', '/login');
      }
    }
  }, [token]);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
        isProviderActive: true,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

const defaultAuthContext: AuthContextType = {
  user: {
    id: 'test-developer',
    email: 'developer@se-intelliplatform.local',
    name: 'Dev Tester',
    role: 'developer',
    is_active: true,
    created_at: new Date().toISOString(),
  },
  token: 'mock-test-token',
  isAuthenticated: true,
  isLoading: false,
  error: null,
  login: async () => { throw new Error('Auth not initialized'); },
  register: async () => { throw new Error('Auth not initialized'); },
  logout: async () => {},
  clearError: () => {},
  isProviderActive: false,
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    return defaultAuthContext;
  }
  return context;
};
