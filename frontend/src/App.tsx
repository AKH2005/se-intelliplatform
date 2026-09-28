import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from './services/projectsApi';
import { useProject } from './context/ProjectContext';
import { Header } from './components/layout/Header';
import { Sidebar, NavigationTab } from './components/layout/Sidebar';
import { ProjectWorkspace } from './views/ProjectWorkspace';
import { RequirementsWorkspace } from './views/RequirementsWorkspace';
import { WorkflowStudio } from './views/WorkflowStudio';
import { RunHistory } from './views/RunHistory';
import { CreateProjectModal } from './components/projects/CreateProjectModal';
import { ProjectCreate } from './types/project';

export const App: React.FC = () => {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId, setSelectedProject } = useProject();

  const [activeTab, setActiveTab] = useState<NavigationTab>('projects');
  const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);

  // Fetch all projects for the global header selector
  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

  // Global Project creation mutation
  const createProjectMutation = useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setSelectedProjectId(newProject.id);
      setSelectedProject(newProject);
    },
  });

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        hasActiveProject={Boolean(selectedProjectId)}
      />

      <div className="main-content">
        <Header
          projects={projects}
          onOpenCreateProject={() => setIsCreateProjectOpen(true)}
        />

        <main style={{ flex: 1, paddingBottom: '3rem' }}>
          {activeTab === 'projects' && <ProjectWorkspace />}
          {activeTab === 'requirements' && <RequirementsWorkspace />}
          {activeTab === 'workflows' && <WorkflowStudio />}
          {activeTab === 'history' && <RunHistory />}
        </main>
      </div>

      <CreateProjectModal
        isOpen={isCreateProjectOpen}
        onClose={() => setIsCreateProjectOpen(false)}
        onSubmit={async (data) => {
          await createProjectMutation.mutateAsync(data);
        }}
      />
    </div>
  );
};
