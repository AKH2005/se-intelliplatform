import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export type AppMode = 'user' | 'developer';

export interface ModeContextValue {
  mode: AppMode;
  isModeSelected: boolean;
  isModeSelectionOpen: boolean;
  setMode: (mode: AppMode, remember?: boolean) => void;
  switchMode: (mode: AppMode) => void;
  openModeSelection: () => void;
  closeModeSelection: () => void;
  clearMode: () => void;
}

export const MODE_STORAGE_KEY = 'se_platform_mode';
export const MODE_REMEMBER_KEY = 'se_platform_mode_remember';

export const isValidMode = (value: unknown): value is AppMode => {
  return value === 'user' || value === 'developer';
};

const getStoredModeSafely = (): AppMode | null => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    const stored = window.localStorage.getItem(MODE_STORAGE_KEY);
    if (isValidMode(stored)) {
      return stored;
    }
    // Clean up corrupted or invalid values safely
    if (stored !== null) {
      window.localStorage.removeItem(MODE_STORAGE_KEY);
    }
    return null;
  } catch {
    return null;
  }
};

const defaultModeContext: ModeContextValue = {
  mode: 'developer',
  isModeSelected: true,
  isModeSelectionOpen: false,
  setMode: () => {},
  switchMode: () => {},
  openModeSelection: () => {},
  closeModeSelection: () => {},
  clearMode: () => {},
};

export const ModeContext = createContext<ModeContextValue | undefined>(undefined);

export const ModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isUrlSelectMode = typeof window !== 'undefined' && window.location.pathname.startsWith('/select-mode');
  const [storedMode] = useState<AppMode | null>(() => getStoredModeSafely());
  
  // If user explicitly navigated to /select-mode, require explicit mode selection
  const [mode, setModeState] = useState<AppMode>(() => storedMode ?? 'developer');
  const [isModeSelected, setIsModeSelected] = useState<boolean>(() => !isUrlSelectMode && storedMode !== null);
  const [isModeSelectionOpen, setIsModeSelectionOpen] = useState<boolean>(() => isUrlSelectMode || storedMode === null);

  // Sync state if localStorage changes from another tab/window
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === MODE_STORAGE_KEY) {
        if (isValidMode(e.newValue)) {
          setModeState(e.newValue);
          setIsModeSelected(true);
          setIsModeSelectionOpen(false);
        } else if (!e.newValue) {
          setIsModeSelected(false);
          setIsModeSelectionOpen(true);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const setMode = useCallback((newMode: AppMode, remember: boolean = true) => {
    if (!isValidMode(newMode)) return;

    setModeState(newMode);
    setIsModeSelected(true);
    setIsModeSelectionOpen(false);

    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(MODE_STORAGE_KEY, newMode);
        if (remember) {
          window.localStorage.setItem(MODE_REMEMBER_KEY, 'true');
        }
      }
    } catch {
      // Ignore quota or private-browsing errors
    }
  }, []);

  const switchMode = useCallback((newMode: AppMode) => {
    setMode(newMode, true);
  }, [setMode]);

  const openModeSelection = useCallback(() => {
    setIsModeSelectionOpen(true);
    if (typeof window !== 'undefined' && window.location.pathname !== '/select-mode') {
      window.history.pushState({}, '', '/select-mode');
    }
  }, []);

  const closeModeSelection = useCallback(() => {
    // Only permit closing if a mode has already been selected and not on /select-mode
    if (isModeSelected) {
      setIsModeSelectionOpen(false);
      if (typeof window !== 'undefined' && window.location.pathname === '/select-mode') {
        const dest = mode === 'user' ? '/user' : '/projects';
        window.history.replaceState({}, '', dest);
      }
    }
  }, [isModeSelected, mode]);

  const clearMode = useCallback(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.removeItem(MODE_STORAGE_KEY);
        window.localStorage.removeItem(MODE_REMEMBER_KEY);
      }
    } catch {
      // Ignore storage errors
    }
    setIsModeSelected(false);
    setIsModeSelectionOpen(true);
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', '/select-mode');
    }
  }, []);

  const value: ModeContextValue = {
    mode,
    isModeSelected,
    isModeSelectionOpen,
    setMode,
    switchMode,
    openModeSelection,
    closeModeSelection,
    clearMode,
  };

  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>;
};

export const useMode = (): ModeContextValue => {
  const context = useContext(ModeContext);
  if (!context) {
    return defaultModeContext;
  }
  return context;
};
