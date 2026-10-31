import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { ProjectResponse } from '../types/project';
import { projectsApi } from '../services/projectsApi';

export interface ProjectContextValue {
  selectedProjectId: string | null;
  setSelectedProjectId: (id: string | null) => void;
  selectedProject: ProjectResponse | null;
  setSelectedProject: (project: ProjectResponse | null) => void;
  selectProject: (project: ProjectResponse | null) => void;
  projects: ProjectResponse[];
  setProjects?: (projects: ProjectResponse[]) => void;
  validateAndSyncProjects: (projects: ProjectResponse[]) => void;
  handleStaleProject: (staleId?: string) => Promise<void>;
  isProjectStale: boolean;
  staleProjectNotice: string | null;
  clearStaleProjectNotice: () => void;
  openCreateProject?: () => void;
  registerOpenCreateProject?: (fn: () => void) => void;
}

export const ProjectContext = createContext<ProjectContextValue | undefined>(undefined);

export const LOCAL_STORAGE_KEY = 'se_intelliplatform_active_project_id';

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(() => {
    return localStorage.getItem(LOCAL_STORAGE_KEY) || null;
  });

  const [selectedProject, setSelectedProjectState] = useState<ProjectResponse | null>(null);
  const [projects, setProjectsState] = useState<ProjectResponse[]>([]);
  const [staleProjectNotice, setStaleProjectNotice] = useState<string | null>(null);
  const [isProjectStale, setIsProjectStale] = useState<boolean>(false);

  const selectedProjectIdRef = useRef<string | null>(selectedProjectId);
  const justSelectedProjectIdRef = useRef<string | null>(null);
  const openCreateProjectRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    selectedProjectIdRef.current = selectedProjectId;
  }, [selectedProjectId]);

  const selectProject = useCallback((project: ProjectResponse | null) => {
    if (!project) {
      selectedProjectIdRef.current = null;
      justSelectedProjectIdRef.current = null;
      setSelectedProjectIdState(null);
      setSelectedProjectState(null);
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      return;
    }

    selectedProjectIdRef.current = project.id;
    justSelectedProjectIdRef.current = project.id;
    setSelectedProjectIdState(project.id);
    setSelectedProjectState(project);
    localStorage.setItem(LOCAL_STORAGE_KEY, project.id);
    setIsProjectStale(false);
    setStaleProjectNotice(null);

    // Make sure project exists in internal projects state immediately
    setProjectsState((prev) => {
      const exists = prev.some((p) => p.id === project.id);
      return exists ? prev.map((p) => (p.id === project.id ? project : p)) : [project, ...prev];
    });
  }, []);

  const setSelectedProjectId = useCallback((id: string | null) => {
    selectedProjectIdRef.current = id;
    justSelectedProjectIdRef.current = id;
    setSelectedProjectIdState(id);
    setIsProjectStale(false);
    if (id) {
      localStorage.setItem(LOCAL_STORAGE_KEY, id);
    } else {
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      setSelectedProjectState(null);
    }
  }, []);

  const setSelectedProject = useCallback((project: ProjectResponse | null) => {
    selectProject(project);
  }, [selectProject]);

  // Validate active project against authoritative project list
  const validateAndSyncProjects = useCallback(
    (availableProjects: ProjectResponse[]) => {
      setProjectsState((prev) => {
        if (
          prev.length === availableProjects.length &&
          prev.every((p, i) => p.id === availableProjects[i]?.id)
        ) {
          return prev;
        }
        return availableProjects;
      });

      const currentId = selectedProjectIdRef.current;

      // Scenario A: No projects exist in the platform
      if (availableProjects.length === 0) {
        if (currentId) {
          localStorage.removeItem(LOCAL_STORAGE_KEY);
          selectedProjectIdRef.current = null;
          justSelectedProjectIdRef.current = null;
          setSelectedProjectIdState(null);
          setSelectedProjectState(null);
          setIsProjectStale(true);
          setStaleProjectNotice('That project is no longer available.');
        }
        return;
      }

      // If we just explicitly selected or created a project, and availableProjects doesn't have it yet:
      // DO NOT overwrite it with a stale list!
      if (currentId && justSelectedProjectIdRef.current === currentId) {
        const matching = availableProjects.find((p) => p.id === currentId);
        if (matching) {
          setSelectedProjectState((prev) => (prev?.id === matching.id && prev?.updated_at === matching.updated_at ? prev : matching));
          justSelectedProjectIdRef.current = null;
        }
        return;
      }

      // Scenario B: Current project ID exists in availableProjects
      if (currentId) {
        const matching = availableProjects.find((p) => p.id === currentId);
        if (matching) {
          setSelectedProjectState((prev) => (prev?.id === matching.id && prev?.updated_at === matching.updated_at ? prev : matching));
          setIsProjectStale(false);
        } else {
          // STALE PROJECT DETECTED!
          const fallback = availableProjects[0];
          localStorage.setItem(LOCAL_STORAGE_KEY, fallback.id);
          selectedProjectIdRef.current = fallback.id;
          setSelectedProjectIdState(fallback.id);
          setSelectedProjectState((prev) => (prev?.id === fallback.id ? prev : fallback));
          setIsProjectStale(true);
          setStaleProjectNotice(
            `That project is no longer available. Switched to ${fallback.name}.`
          );
        }
      } else {
        // Scenario C: No project was previously selected, default to first available
        const defaultProj = availableProjects[0];
        localStorage.setItem(LOCAL_STORAGE_KEY, defaultProj.id);
        selectedProjectIdRef.current = defaultProj.id;
        setSelectedProjectIdState(defaultProj.id);
        setSelectedProjectState((prev) => (prev?.id === defaultProj.id ? prev : defaultProj));
        setIsProjectStale(false);
      }
    },
    []
  );

  // Gracefully handle a stale project ID detected via 404 or runtime error
  const handleStaleProject = useCallback(
    async (staleId?: string) => {
      const targetStaleId = staleId || selectedProjectIdRef.current;
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      setIsProjectStale(true);

      try {
        const freshProjects = await projectsApi.list();
        const validProjects = targetStaleId
          ? freshProjects.filter((p) => p.id !== targetStaleId)
          : freshProjects;

        validateAndSyncProjects(validProjects);

        if (validProjects.length === 0 && openCreateProjectRef.current) {
          openCreateProjectRef.current();
        }
      } catch {
        setSelectedProjectIdState(null);
        setSelectedProjectState(null);
        setStaleProjectNotice('That project is no longer available.');
      }
    },
    [validateAndSyncProjects]
  );

  // Listen for global project:not-found event from QueryCache or API clients
  useEffect(() => {
    const handleProjectNotFoundEvent = (event: Event) => {
      const customEvent = event as CustomEvent;
      const staleId = customEvent.detail?.projectId || selectedProjectIdRef.current;
      handleStaleProject(staleId);
    };

    window.addEventListener('project:not-found', handleProjectNotFoundEvent);
    return () => {
      window.removeEventListener('project:not-found', handleProjectNotFoundEvent);
    };
  }, [handleStaleProject]);

  const clearStaleProjectNotice = useCallback(() => {
    setStaleProjectNotice(null);
    setIsProjectStale(false);
  }, []);

  const openCreateProject = useCallback(() => {
    if (openCreateProjectRef.current) {
      openCreateProjectRef.current();
    }
  }, []);

  const registerOpenCreateProject = useCallback((fn: () => void) => {
    openCreateProjectRef.current = fn;
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        selectedProjectId,
        setSelectedProjectId,
        selectedProject,
        setSelectedProject,
        selectProject,
        projects,
        setProjects: setProjectsState,
        validateAndSyncProjects,
        handleStaleProject,
        isProjectStale,
        staleProjectNotice,
        clearStaleProjectNotice,
        openCreateProject,
        registerOpenCreateProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export function useProject(): ProjectContextValue {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}

export function useProjectSafe(): ProjectContextValue | null {
  return useContext(ProjectContext) || null;
}
