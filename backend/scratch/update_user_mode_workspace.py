# Helper script to update UserModeWorkspace.tsx with the 5-tab dedicated Beginner Mode shell

with open('frontend/src/views/UserModeWorkspace.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add state variables right after promptInput/isPlanning/createdProject definitions
state_insert_target = "  const [conversationId, setConversationId] = useState<string | null>(null);"

new_state_code = """  const [conversationId, setConversationId] = useState<string | null>(null);

  // Beginner Mode 5-Option Navigation Architecture
  type BeginnerTab = 'projects' | 'overview' | 'code-studio' | 'preview' | 'assistant';
  const [activeTab, setActiveTab] = useState<BeginnerTab>('projects');

  // Code Studio inspection state
  const [studioFiles, setStudioFiles] = useState<FileNode[]>([]);
  const [selectedStudioPath, setSelectedStudioPath] = useState<string>('frontend/index.html');
  const [studioCodeContent, setStudioCodeContent] = useState<string>('');
  const [isStudioLoading, setIsStudioLoading] = useState<boolean>(false);
  const [isDownloadingZip, setIsDownloadingZip] = useState<boolean>(false);
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);

  // Active project resolution
  const currentProject = createdProject || selectedProject || (projects.length > 0 ? projects[0] : null);

  useEffect(() => {
    if (!selectedProject && projects.length > 0) {
      selectProject(projects[0]);
    }
  }, [projects, selectedProject, selectProject]);

  function findFirstFileNode(nodes: FileNode[]): FileNode | null {
    for (const node of nodes) {
      if (node.type === 'file') return node;
      if (node.children) {
        const found = findFirstFileNode(node.children);
        if (found) return found;
      }
    }
    return null;
  }

  function getFallbackFileTree(): FileNode[] {
    return [
      {
        id: 'dir-frontend',
        name: 'frontend',
        path: 'frontend',
        type: 'directory',
        children: [
          { id: 'f-index', name: 'index.html', path: 'frontend/index.html', type: 'file', language: 'html' },
          { id: 'f-app', name: 'App.tsx', path: 'frontend/src/App.tsx', type: 'file', language: 'typescript' },
          { id: 'f-pkg', name: 'package.json', path: 'frontend/package.json', type: 'file', language: 'json' },
        ],
      },
      {
        id: 'dir-backend',
        name: 'backend',
        path: 'backend',
        type: 'directory',
        children: [
          { id: 'f-main', name: 'main.py', path: 'backend/main.py', type: 'file', language: 'python' },
          { id: 'f-req', name: 'requirements.txt', path: 'backend/requirements.txt', type: 'file', language: 'text' },
        ],
      },
      { id: 'f-readme', name: 'README.md', path: 'README.md', type: 'file', language: 'markdown' },
    ];
  }

  function getFallbackFileContent(filePath: string, appName: string = 'Application'): string {
    if (filePath.endsWith('index.html')) {
      return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${appName}</title>
  <link rel="stylesheet" href="./styles.css" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="./src/App.tsx"></script>
</body>
</html>`;
    }
    if (filePath.endsWith('main.py')) {
      return `\"\"\"FastAPI Backend Application for ${appName}.\"\"\"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="${appName}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "${appName}"}
`;
    }
    if (filePath.endsWith('package.json')) {
      return JSON.stringify(
        {
          name: appName.toLowerCase().replace(/\\s+/g, '-'),
          version: '1.0.0',
          private: true,
          scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
          dependencies: { react: '^18.3.1', 'react-dom': '^18.3.1', 'lucide-react': '^0.460.0' },
        },
        null,
        2
      );
    }
    return `# ${appName}

Synthesized by SE IntelliPlatform autonomous AI software engineering engine.

## Getting Started
1. Run \\`npm install\\` inside \\`frontend/\\`
2. Run \\`pip install -r requirements.txt\\` inside \\`backend/\\`
3. Launch development server with \\`npm run dev\\`
`;
  }

  const loadStudioFiles = async (projId: string) => {
    setIsStudioLoading(true);
    try {
      const tree = await codeStudioApi.getFileTree(projId);
      if (tree.root_nodes && tree.root_nodes.length > 0) {
        setStudioFiles(tree.root_nodes);
        const first = findFirstFileNode(tree.root_nodes);
        if (first) {
          setSelectedStudioPath(first.path);
          try {
            const content = await codeStudioApi.getFileContent(projId, first.path);
            setStudioCodeContent(content.content || '');
          } catch {
            setStudioCodeContent(getFallbackFileContent(first.path, currentProject?.name));
          }
        }
      } else {
        setStudioFiles(getFallbackFileTree());
        setStudioCodeContent(getFallbackFileContent('frontend/index.html', currentProject?.name));
      }
    } catch {
      setStudioFiles(getFallbackFileTree());
      setStudioCodeContent(getFallbackFileContent('frontend/index.html', currentProject?.name));
    } finally {
      setIsStudioLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'code-studio' && currentProject?.id) {
      loadStudioFiles(currentProject.id);
    }
  }, [activeTab, currentProject?.id]);

  const handleDownloadZip = async (proj?: ProjectResponse | null) => {
    const target = proj || currentProject;
    if (!target) return;
    setIsDownloadingZip(true);
    setDownloadNotice(null);
    try {
      const filename = `${target.slug || 'project'}-source.zip`;
      await projectsApi.download(target.id, filename);
      setDownloadNotice(`✓ Downloaded ${filename} successfully!`);
    } catch (err: any) {
      setDownloadNotice(`Download notice: ${err?.message || 'Could not download ZIP'}`);
    } finally {
      setIsDownloadingZip(false);
    }
  };"""

if state_insert_target in content:
    content = content.replace(state_insert_target, new_state_code, 1)
    print("State code inserted successfully.")
else:
    print("State target not found.")

with open('frontend/src/views/UserModeWorkspace.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

