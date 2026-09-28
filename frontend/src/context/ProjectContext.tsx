import React, { createContext, useContext, useState, useEffect } from 'react';
import { ProjectResponse } from '../types/project';

interface ProjectContextValue {
  selectedProjectId: string | null;
  setSelectedProjectId: (id: string | null) => void;
  selectedProject: ProjectResponse | null;
  setSelectedProject: (project: ProjectResponse | null) => void;
}

const ProjectContext = createContext<ProjectContextValue | undefined>(undefined);

const LOCAL_STORAGE_KEY = 'se_intelliplatform_active_project_id';

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(() => {
    return localStorage.getItem(LOCAL_STORAGE_KEY) || null;
  });

  const [selectedProject, setSelectedProject] = useState<ProjectResponse | null>(null);

  const setSelectedProjectId = (id: string | null) => {
    setSelectedProjectIdState(id);
    if (id) {
      localStorage.setItem(LOCAL_STORAGE_KEY, id);
    } else {
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      setSelectedProject(null);
    }
  };

  useEffect(() => {
    if (selectedProject && selectedProject.id !== selectedProjectId) {
      setSelectedProjectId(selectedProject.id);
    }
  }, [selectedProject]);

  return (
    <ProjectContext.Provider
      value={{
        selectedProjectId,
        setSelectedProjectId,
        selectedProject,
        setSelectedProject,
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
