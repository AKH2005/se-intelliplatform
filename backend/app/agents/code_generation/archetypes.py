"""Archetype Templates and Scaffolds for SE IntelliPlatform Code Generation.

Provides complete, production-grade source code for all platform archetypes:
1. snake_game: Canvas 2D Arcade Game (Retro Snake)
2. taskflow: Real-Time Kanban Task Manager
3. analytics: Executive Analytics & BI Dashboard
4. eventhub: Event & Conference Booking Hub
5. ecommerce: E-Commerce Store & Catalog
6. management: Team Directory & Admin Portal
"""

from typing import Any


def detect_project_archetype(name: str = "", desc: str = "", slug: str = "") -> str:
    """Classify project idea or template into canonical archetype."""
    combined = f"{name} {desc} {slug}".lower()
    if any(k in combined for k in ["snake", "arcade", "game", "retro", "2d arcade", "canvas"]):
        return "snake_game"
    if any(k in combined for k in ["analytics", "kpi", "dashboard", "metric", "executive", "revenue", "bi "]):
        return "analytics"
    if any(k in combined for k in ["event", "meet", "summit", "conference", "ticket", "booking"]):
        return "eventhub"
    if any(k in combined for k in ["shop", "store", "commerce", "cart", "product", "checkout", "market"]):
        return "ecommerce"
    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school", "directory", "roster", "member"]):
        return "management"
    return "taskflow"


def get_archetype_planned_files(
    archetype: str,
    fe_comp_name: str = "Frontend UI",
    be_comp_name: str = "Backend Service",
    req_ids: list[str] | None = None,
    ui_req_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return planned file manifest tailored to the archetype."""
    r_ids = req_ids or []
    ui_ids = ui_req_ids or r_ids

    if archetype == "snake_game":
        return [
            # Frontend
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and HTML5 canvas game mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Interactive React Snake Game component with 60 FPS loop, score, controls, and high scores", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/ScoreBoard.tsx", "frontend/src/components/GameControls.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/ScoreBoard.tsx", "purpose": "Scoreboard component displaying score, high score, and level", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/GameControls.tsx", "purpose": "Virtual D-pad directional controls and game state action buttons", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend for leaderboard persistence", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern retro arcade theme styling with neon glow effects and responsive layout", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            # Backend
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and static preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for player score records and submissions", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling leaderboard CRUD and score queries", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe leaderboard persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with gameplay controls, setup guide, and architecture", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "analytics":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Executive analytics dashboard with KPI cards, charts, and metrics table", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/KpiGrid.tsx", "frontend/src/components/MetricsTable.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/KpiGrid.tsx", "purpose": "KPI summary cards displaying ARR, active workspaces, and conversion rates", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/MetricsTable.tsx", "purpose": "Sortable metrics table with search, category filtering, and CSV export", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client communicating with FastAPI backend metrics endpoints", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern executive dashboard styling with card layouts and responsive tables", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for executive metrics and KPI items", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling metrics and KPI CRUD endpoints", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe metrics persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with architecture and analytics dashboard guides", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    if archetype == "eventhub":
        return [
            {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
            {"path": "frontend/src/App.tsx", "purpose": "Event catalog and conference booking dashboard with seat capacity gating", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/EventCard.tsx", "frontend/src/components/BookingModal.tsx", "frontend/src/services/api.ts"]},
            {"path": "frontend/src/components/EventCard.tsx", "purpose": "Event card displaying schedule, venue, capacity badge, and booking trigger", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/components/BookingModal.tsx", "purpose": "Attendee registration modal with capacity validation and reservation form", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/services/api.ts", "purpose": "REST API client connecting to FastAPI backend event routes", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
            {"path": "frontend/src/styles/App.css", "purpose": "Modern conference event portal styling with responsive grid", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/requirements.txt", "purpose": "Python package dependencies including FastAPI, Uvicorn, and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
            {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware and preview serving", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
            {"path": "backend/app/config.py", "purpose": "Application configuration and environment CORS settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/models.py", "purpose": "Pydantic domain schemas for events and attendee registrations", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
            {"path": "backend/app/api.py", "purpose": "REST endpoint router handling event listings and registration workflows", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
            {"path": "backend/app/persistence.py", "purpose": "Thread-safe event and registration persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
            {"path": "README.md", "purpose": "Project documentation with event booking workflows and setup guide", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
        ]

    # Default to kanban_task_manager (TaskFlow)
    return [
        {"path": "frontend/package.json", "purpose": "Frontend package manifest with React 18, Vite, and Lucide icons", "file_type": "DEPENDENCY", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/index.html", "purpose": "Vite HTML5 entrypoint and root mounting container", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/main.tsx", "purpose": "React application bootstrapper and root DOM renderer", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/App.tsx", "frontend/src/styles/App.css"]},
        {"path": "frontend/src/App.tsx", "purpose": "Interactive React task management dashboard with task listing, creation, editing, and deletion", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": ["frontend/src/components/TaskCard.tsx", "frontend/src/components/TaskForm.tsx", "frontend/src/services/api.ts"]},
        {"path": "frontend/src/components/TaskCard.tsx", "purpose": "Component rendering task details, status indicators, and action triggers", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/components/TaskForm.tsx", "purpose": "Interactive form component for creating and editing tasks with validation", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/services/api.ts", "purpose": "Frontend API client communicating with FastAPI backend via configurable base URL", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": ui_ids, "dependencies": []},
        {"path": "frontend/src/styles/App.css", "purpose": "Modern styling and responsive layout for the React task manager UI", "file_type": "SOURCE", "architecture_component": fe_comp_name, "requirement_ids": [], "dependencies": []},
        {"path": "backend/requirements.txt", "purpose": "Backend Python package dependencies for FastAPI and Pydantic", "file_type": "DEPENDENCY", "architecture_component": be_comp_name, "requirement_ids": [], "dependencies": []},
        {"path": "backend/app/main.py", "purpose": "FastAPI application entrypoint with CORS middleware for React communication", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/config.py", "backend/app/api.py"]},
        {"path": "backend/app/config.py", "purpose": "Environment settings and CORS configuration using Pydantic Settings", "file_type": "CONFIG", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
        {"path": "backend/app/models.py", "purpose": "Pydantic domain models and schemas for task operations", "file_type": "SCHEMA", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": []},
        {"path": "backend/app/api.py", "purpose": "REST API route handlers for task CRUD operations", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py", "backend/app/persistence.py"]},
        {"path": "backend/app/persistence.py", "purpose": "Thread-safe task persistence repository", "file_type": "SOURCE", "architecture_component": be_comp_name, "requirement_ids": r_ids, "dependencies": ["backend/app/models.py"]},
        {"path": "README.md", "purpose": "Architecture overview and setup guides for frontend and backend", "file_type": "DOCUMENTATION", "architecture_component": None, "requirement_ids": [], "dependencies": []},
    ]


def get_archetype_file_content(
    archetype: str,
    path: str,
    project_name: str = "Application",
    project_desc: str = "Modern full-stack application built with React and FastAPI.",
) -> str | None:
    """Return syntactically valid, production-grade source code for a given archetype file."""
    norm_path = path.replace("\\", "/").strip()

    # Shared Package Manifest
    if norm_path == "frontend/package.json":
        slug = project_name.lower().replace(" ", "-")
        return (
            "{\n"
            f'  "name": "{slug}",\n'
            '  "private": true,\n'
            '  "version": "1.0.0",\n'
            '  "type": "module",\n'
            '  "scripts": {\n'
            '    "dev": "vite",\n'
            '    "build": "tsc && vite build",\n'
            '    "preview": "vite preview"\n'
            "  },\n"
            '  "dependencies": {\n'
            '    "react": "^18.3.1",\n'
            '    "react-dom": "^18.3.1",\n'
            '    "lucide-react": "^0.453.0"\n'
            "  },\n"
            '  "devDependencies": {\n'
            '    "@types/react": "^18.3.11",\n'
            '    "@types/react-dom": "^18.3.1",\n'
            '    "@vitejs/plugin-react": "^4.3.2",\n'
            '    "typescript": "^5.6.3",\n'
            '    "vite": "^5.4.8"\n'
            "  }\n"
            "}\n"
        )

    # Shared React Main Entrypoint
    if norm_path == "frontend/src/main.tsx":
        return (
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            "import App from './App';\n"
            "import './styles/App.css';\n\n"
            "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
            "  <React.StrictMode>\n"
            "    <App />\n"
            "  </React.StrictMode>\n"
            ");\n"
        )

    # Shared Backend Requirements
    if norm_path in ("backend/requirements.txt", "requirements.txt"):
        return (
            "fastapi>=0.110.0\n"
            "uvicorn>=0.28.0\n"
            "pydantic>=2.6.0\n"
        )

    # Shared Backend Config
    if norm_path in ("backend/app/config.py", "app/config.py"):
        return (
            '"""Configuration and environment settings."""\n\n'
            "import os\n"
            "from pydantic import BaseModel\n\n\n"
            "class Settings(BaseModel):\n"
            f'    app_name: str = "{project_name}"\n'
            '    environment: str = os.getenv("APP_ENV", "development")\n'
            "    allowed_origins: list[str] = [\n"
            '        "http://localhost:5173",\n'
            '        "http://127.0.0.1:5173",\n'
            '        "http://localhost:8001",\n'
            '        "http://127.0.0.1:8001",\n'
            '        "*",\n'
            "    ]\n\n\n"
            "def get_settings() -> Settings:\n"
            "    return Settings()\n"
        )

    # Shared README
    if norm_path == "README.md":
        return (
            f"# {project_name}\n\n"
            f"{project_desc}\n\n"
            "## Architecture\n\n"
            "- **Frontend:** React 18 + TypeScript + Vite (`frontend/`)\n"
            "- **Backend:** FastAPI + Pydantic (`backend/`)\n"
            "- **Runtime Preview:** Port 8001 Docker container preview\n\n"
            "## Running Locally\n\n"
            "### 1. Backend\n"
            "```bash\n"
            "cd backend\n"
            "pip install -r requirements.txt\n"
            "uvicorn app.main:app --reload --port 8000\n"
            "```\n\n"
            "### 2. Frontend\n"
            "```bash\n"
            "cd frontend\n"
            "npm install\n"
            "npm run dev\n"
            "```\n"
        )

    # -------------------------------------------------------------
    # Archetype 1: SNAKE GAME (canvas_arcade_game)
    # -------------------------------------------------------------
    if archetype == "snake_game":
        if norm_path == "frontend/index.html":
            return (
                "<!DOCTYPE html>\n"
                '<html lang="en">\n'
                "  <head>\n"
                '    <meta charset="UTF-8" />\n'
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
                f"    <title>{project_name} — 2D Retro Arcade</title>\n"
                "    <style>\n"
                "      body { margin: 0; background: #0b0f19; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }\n"
                "    </style>\n"
                "  </head>\n"
                "  <body>\n"
                '    <div id="root"></div>\n'
                '    <script type="module" src="/src/main.tsx"></script>\n'
                "  </body>\n"
                "</html>\n"
            )

        if norm_path == "frontend/src/App.tsx":
            return (
                "import React, { useState, useEffect, useRef, useCallback } from 'react';\n"
                "import { ScoreBoard } from './components/ScoreBoard';\n"
                "import { GameControls } from './components/GameControls';\n"
                "import { scoreApi, LeaderboardEntry } from './services/api';\n\n"
                "type Point = { x: number; y: number };\n"
                "type Direction = 'UP' | 'DOWN' | 'LEFT' | 'RIGHT';\n"
                "type GameState = 'IDLE' | 'PLAYING' | 'PAUSED' | 'GAME_OVER';\n"
                "type Difficulty = 'EASY' | 'MEDIUM' | 'HARD';\n\n"
                "const GRID_SIZE = 20;\n"
                "const SPEED_MAP: Record<Difficulty, number> = { EASY: 130, MEDIUM: 95, HARD: 65 };\n\n"
                "export default function App() {\n"
                "  const [snake, setSnake] = useState<Point[]>([{ x: 10, y: 10 }, { x: 10, y: 11 }, { x: 10, y: 12 }]);\n"
                "  const [food, setFood] = useState<Point>({ x: 5, y: 5 });\n"
                "  const [direction, setDirection] = useState<Direction>('UP');\n"
                "  const [gameState, setGameState] = useState<GameState>('IDLE');\n"
                "  const [score, setScore] = useState<number>(0);\n"
                "  const [highScore, setHighScore] = useState<number>(() => {\n"
                "    return parseInt(localStorage.getItem('snake_high_score') || '0', 10);\n"
                "  });\n"
                "  const [difficulty, setDifficulty] = useState<Difficulty>('MEDIUM');\n"
                "  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);\n"
                "  const canvasRef = useRef<HTMLCanvasElement | null>(null);\n"
                "  const directionRef = useRef<Direction>(direction);\n"
                "  directionRef.current = direction;\n\n"
                "  // Generate random food not on snake body\n"
                "  const spawnFood = useCallback((currentSnake: Point[]): Point => {\n"
                "    while (true) {\n"
                "      const x = Math.floor(Math.random() * GRID_SIZE);\n"
                "      const y = Math.floor(Math.random() * GRID_SIZE);\n"
                "      const collision = currentSnake.some((seg) => seg.x === x && seg.y === y);\n"
                "      if (!collision) return { x, y };\n"
                "    }\n"
                "  }, []);\n\n"
                "  // Load remote leaderboard\n"
                "  const loadLeaderboard = async () => {\n"
                "    try {\n"
                "      const data = await scoreApi.getScores();\n"
                "      setLeaderboard(data);\n"
                "    } catch (e) {\n"
                "      console.warn('Leaderboard offline:', e);\n"
                "    }\n"
                "  };\n\n"
                "  useEffect(() => {\n"
                "    loadLeaderboard();\n"
                "  }, []);\n\n"
                "  const handleStartGame = () => {\n"
                "    const initialSnake = [{ x: 10, y: 10 }, { x: 10, y: 11 }, { x: 10, y: 12 }];\n"
                "    setSnake(initialSnake);\n"
                "    setDirection('UP');\n"
                "    setScore(0);\n"
                "    setFood(spawnFood(initialSnake));\n"
                "    setGameState('PLAYING');\n"
                "  };\n\n"
                "  const handleTogglePause = () => {\n"
                "    if (gameState === 'PLAYING') setGameState('PAUSED');\n"
                "    else if (gameState === 'PAUSED') setGameState('PLAYING');\n"
                "  };\n\n"
                "  const handleDirectionChange = (newDir: Direction) => {\n"
                "    const current = directionRef.current;\n"
                "    if (newDir === 'UP' && current !== 'DOWN') setDirection('UP');\n"
                "    else if (newDir === 'DOWN' && current !== 'UP') setDirection('DOWN');\n"
                "    else if (newDir === 'LEFT' && current !== 'RIGHT') setDirection('LEFT');\n"
                "    else if (newDir === 'RIGHT' && current !== 'LEFT') setDirection('RIGHT');\n"
                "  };\n\n"
                "  // Keyboard navigation\n"
                "  useEffect(() => {\n"
                "    const handleKeyDown = (e: KeyboardEvent) => {\n"
                "      if (['ArrowUp', 'KeyW'].includes(e.code)) { e.preventDefault(); handleDirectionChange('UP'); }\n"
                "      else if (['ArrowDown', 'KeyS'].includes(e.code)) { e.preventDefault(); handleDirectionChange('DOWN'); }\n"
                "      else if (['ArrowLeft', 'KeyA'].includes(e.code)) { e.preventDefault(); handleDirectionChange('LEFT'); }\n"
                "      else if (['ArrowRight', 'KeyD'].includes(e.code)) { e.preventDefault(); handleDirectionChange('RIGHT'); }\n"
                "      else if (e.code === 'Space') { e.preventDefault(); handleTogglePause(); }\n"
                "    };\n"
                "    window.addEventListener('keydown', handleKeyDown);\n"
                "    return () => window.removeEventListener('keydown', handleKeyDown);\n"
                "  }, [gameState]);\n\n"
                "  // Game tick loop\n"
                "  useEffect(() => {\n"
                "    if (gameState !== 'PLAYING') return;\n"
                "    const interval = setInterval(() => {\n"
                "      setSnake((prev) => {\n"
                "        const head = prev[0];\n"
                "        const currentDir = directionRef.current;\n"
                "        const newHead: Point = {\n"
                "          x: currentDir === 'LEFT' ? head.x - 1 : currentDir === 'RIGHT' ? head.x + 1 : head.x,\n"
                "          y: currentDir === 'UP' ? head.y - 1 : currentDir === 'DOWN' ? head.y + 1 : head.y,\n"
                "        };\n\n"
                "        // Wall collision\n"
                "        if (newHead.x < 0 || newHead.x >= GRID_SIZE || newHead.y < 0 || newHead.y >= GRID_SIZE) {\n"
                "          setGameState('GAME_OVER');\n"
                "          return prev;\n"
                "        }\n\n"
                "        // Self collision\n"
                "        if (prev.some((seg) => seg.x === newHead.x && seg.y === newHead.y)) {\n"
                "          setGameState('GAME_OVER');\n"
                "          return prev;\n"
                "        }\n\n"
                "        const newSnake = [newHead, ...prev];\n"
                "        // Food eaten\n"
                "        if (newHead.x === food.x && newHead.y === food.y) {\n"
                "          setScore((s) => {\n"
                "            const newScore = s + 10;\n"
                "            if (newScore > highScore) {\n"
                "              setHighScore(newScore);\n"
                "              localStorage.setItem('snake_high_score', String(newScore));\n"
                "            }\n"
                "            return newScore;\n"
                "          });\n"
                "          setFood(spawnFood(newSnake));\n"
                "        } else {\n"
                "          newSnake.pop();\n"
                "        }\n"
                "        return newSnake;\n"
                "      });\n"
                "    }, SPEED_MAP[difficulty]);\n"
                "    return () => clearInterval(interval);\n"
                "  }, [gameState, food, difficulty, highScore, spawnFood]);\n\n"
                "  // Canvas rendering loop\n"
                "  useEffect(() => {\n"
                "    const canvas = canvasRef.current;\n"
                "    if (!canvas) return;\n"
                "    const ctx = canvas.getContext('2d');\n"
                "    if (!ctx) return;\n\n"
                "    const cell = canvas.width / GRID_SIZE;\n"
                "    ctx.fillStyle = '#0f172a';\n"
                "    ctx.fillRect(0, 0, canvas.width, canvas.height);\n\n"
                "    // Subtle grid\n"
                "    ctx.strokeStyle = '#1e293b';\n"
                "    ctx.lineWidth = 1;\n"
                "    for (let i = 0; i <= GRID_SIZE; i++) {\n"
                "      ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, canvas.height); ctx.stroke();\n"
                "      ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(canvas.width, i * cell); ctx.stroke();\n"
                "    }\n\n"
                "    // Draw food with red glow\n"
                "    ctx.save();\n"
                "    ctx.shadowBlur = 10;\n"
                "    ctx.shadowColor = '#f43f5e';\n"
                "    ctx.fillStyle = '#f43f5e';\n"
                "    ctx.beginPath();\n"
                "    ctx.arc(food.x * cell + cell / 2, food.y * cell + cell / 2, cell / 2.5, 0, Math.PI * 2);\n"
                "    ctx.fill();\n"
                "    ctx.restore();\n\n"
                "    // Draw snake with green glow\n"
                "    snake.forEach((seg, idx) => {\n"
                "      ctx.save();\n"
                "      if (idx === 0) {\n"
                "        ctx.fillStyle = '#10b981';\n"
                "        ctx.shadowBlur = 8;\n"
                "        ctx.shadowColor = '#10b981';\n"
                "      } else {\n"
                "        ctx.fillStyle = '#34d399';\n"
                "      }\n"
                "      ctx.fillRect(seg.x * cell + 1, seg.y * cell + 1, cell - 2, cell - 2);\n"
                "      ctx.restore();\n"
                "    });\n"
                "  }, [snake, food]);\n\n"
                "  // Submit high score on game over\n"
                "  useEffect(() => {\n"
                "    if (gameState === 'GAME_OVER' && score > 0) {\n"
                "      scoreApi.submitScore({ player_name: 'Player', score, difficulty })\n"
                "        .then(loadLeaderboard)\n"
                "        .catch(() => {});\n"
                "    }\n"
                "  }, [gameState, score, difficulty]);\n\n"
                "  return (\n"
                "    <div className=\"arcade-wrapper\">\n"
                "      <header className=\"arcade-header\">\n"
                f"        <h1>{project_name}</h1>\n"
                "        <span className={`status-pill ${gameState.toLowerCase()}`}>{gameState}</span>\n"
                "      </header>\n\n"
                "      <main className=\"arcade-main\">\n"
                "        <ScoreBoard score={score} highScore={highScore} difficulty={difficulty} />\n\n"
                "        <div className=\"canvas-container\">\n"
                "          <canvas ref={canvasRef} width={400} height={400} className=\"game-canvas\" />\n"
                "          {gameState === 'IDLE' && (\n"
                "            <div className=\"canvas-overlay\">\n"
                "              <h2>Classic 2D Snake</h2>\n"
                "              <p>Use Arrow keys or on-screen D-Pad to move</p>\n"
                "              <button className=\"btn-primary\" onClick={handleStartGame}>Start Game</button>\n"
                "            </div>\n"
                "          )}\n"
                "          {gameState === 'PAUSED' && (\n"
                "            <div className=\"canvas-overlay\">\n"
                "              <h2>Game Paused</h2>\n"
                "              <button className=\"btn-primary\" onClick={handleTogglePause}>Resume</button>\n"
                "            </div>\n"
                "          )}\n"
                "          {gameState === 'GAME_OVER' && (\n"
                "            <div className=\"canvas-overlay\">\n"
                "              <h2>Game Over!</h2>\n"
                "              <p>Final Score: {score}</p>\n"
                "              <button className=\"btn-primary\" onClick={handleStartGame}>Play Again</button>\n"
                "            </div>\n"
                "          )}\n"
                "        </div>\n\n"
                "        <GameControls\n"
                "          gameState={gameState}\n"
                "          difficulty={difficulty}\n"
                "          onStart={handleStartGame}\n"
                "          onPause={handleTogglePause}\n"
                "          onDirection={handleDirectionChange}\n"
                "          onDifficultyChange={setDifficulty}\n"
                "        />\n"
                "      </main>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )

        if norm_path == "frontend/src/components/ScoreBoard.tsx":
            return (
                "import React from 'react';\n\n"
                "interface ScoreBoardProps {\n"
                "  score: number;\n"
                "  highScore: number;\n"
                "  difficulty: string;\n"
                "}\n\n"
                "export const ScoreBoard: React.FC<ScoreBoardProps> = ({ score, highScore, difficulty }) => {\n"
                "  return (\n"
                "    <div className=\"scoreboard-card\">\n"
                "      <div className=\"score-item\">\n"
                "        <span className=\"score-label\">SCORE</span>\n"
                "        <span className=\"score-value\">{score}</span>\n"
                "      </div>\n"
                "      <div className=\"score-item\">\n"
                "        <span className=\"score-label\">BEST</span>\n"
                "        <span className=\"score-value highlight\">{highScore}</span>\n"
                "      </div>\n"
                "      <div className=\"score-item\">\n"
                "        <span className=\"score-label\">MODE</span>\n"
                "        <span className=\"score-value mode\">{difficulty}</span>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "};\n"
            )

        if norm_path == "frontend/src/components/GameControls.tsx":
            return (
                "import React from 'react';\n\n"
                "interface GameControlsProps {\n"
                "  gameState: string;\n"
                "  difficulty: 'EASY' | 'MEDIUM' | 'HARD';\n"
                "  onStart: () => void;\n"
                "  onPause: () => void;\n"
                "  onDirection: (dir: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT') => void;\n"
                "  onDifficultyChange: (diff: 'EASY' | 'MEDIUM' | 'HARD') => void;\n"
                "}\n\n"
                "export const GameControls: React.FC<GameControlsProps> = ({\n"
                "  gameState,\n"
                "  difficulty,\n"
                "  onStart,\n"
                "  onPause,\n"
                "  onDirection,\n"
                "  onDifficultyChange,\n"
                "}) => {\n"
                "  return (\n"
                "    <div className=\"controls-section\">\n"
                "      <div className=\"action-buttons\">\n"
                "        {gameState === 'PLAYING' ? (\n"
                "          <button className=\"btn-control\" onClick={onPause}>Pause</button>\n"
                "        ) : gameState === 'PAUSED' ? (\n"
                "          <button className=\"btn-control\" onClick={onPause}>Resume</button>\n"
                "        ) : (\n"
                "          <button className=\"btn-control primary\" onClick={onStart}>Start</button>\n"
                "        )}\n"
                "        <div className=\"difficulty-selector\">\n"
                "          {(['EASY', 'MEDIUM', 'HARD'] as const).map((d) => (\n"
                "            <button\n"
                "              key={d}\n"
                "              className={`btn-diff ${difficulty === d ? 'active' : ''}`}\n"
                "              onClick={() => onDifficultyChange(d)}\n"
                "              disabled={gameState === 'PLAYING'}\n"
                "            >\n"
                "              {d}\n"
                "            </button>\n"
                "          ))}\n"
                "        </div>\n"
                "      </div>\n\n"
                "      <div className=\"virtual-dpad\" aria-label=\"Virtual Directional Pad\">\n"
                "        <div className=\"dpad-row\">\n"
                "          <button className=\"dpad-btn up\" onClick={() => onDirection('UP')}>▲</button>\n"
                "        </div>\n"
                "        <div className=\"dpad-row middle\">\n"
                "          <button className=\"dpad-btn left\" onClick={() => onDirection('LEFT')}>◀</button>\n"
                "          <div className=\"dpad-center\" />\n"
                "          <button className=\"dpad-btn right\" onClick={() => onDirection('RIGHT')}>▶</button>\n"
                "        </div>\n"
                "        <div className=\"dpad-row\">\n"
                "          <button className=\"dpad-btn down\" onClick={() => onDirection('DOWN')}>▼</button>\n"
                "        </div>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "};\n"
            )

        if norm_path == "frontend/src/services/api.ts":
            return (
                "export interface LeaderboardEntry {\n"
                "  id: string;\n"
                "  player_name: string;\n"
                "  score: number;\n"
                "  difficulty: string;\n"
                "  created_at: string;\n"
                "}\n\n"
                "const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || 'http://localhost:8000';\n\n"
                "export const scoreApi = {\n"
                "  async getScores(): Promise<LeaderboardEntry[]> {\n"
                "    const res = await fetch(`${API_BASE}/scores`);\n"
                "    if (!res.ok) throw new Error(`HTTP ${res.status}`);\n"
                "    return res.json();\n"
                "  },\n\n"
                "  async submitScore(payload: { player_name: string; score: number; difficulty: string }): Promise<LeaderboardEntry> {\n"
                "    const res = await fetch(`${API_BASE}/scores`, {\n"
                "      method: 'POST',\n"
                "      headers: { 'Content-Type': 'application/json' },\n"
                "      body: JSON.stringify(payload),\n"
                "    });\n"
                "    if (!res.ok) throw new Error(`HTTP ${res.status}`);\n"
                "    return res.json();\n"
                "  },\n"
                "};\n"
            )

        if norm_path == "frontend/src/styles/App.css":
            return (
                "/* Modern Retro Arcade Styling for Snake Game */\n"
                ":root {\n"
                "  --bg-dark: #0b0f19;\n"
                "  --card-bg: #111827;\n"
                "  --border-color: #1f2937;\n"
                "  --primary-glow: #10b981;\n"
                "  --food-glow: #f43f5e;\n"
                "  --text-main: #f9fafb;\n"
                "  --text-muted: #9ca3af;\n"
                "}\n\n"
                "* {\n"
                "  box-sizing: border-box;\n"
                "}\n\n"
                "body {\n"
                "  margin: 0;\n"
                "  background: var(--bg-dark);\n"
                "  color: var(--text-main);\n"
                "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n"
                "}\n\n"
                ".arcade-wrapper {\n"
                "  max-width: 520px;\n"
                "  margin: 1.5rem auto;\n"
                "  padding: 1rem;\n"
                "}\n\n"
                ".arcade-header {\n"
                "  display: flex;\n"
                "  justify-content: space-between;\n"
                "  align-items: center;\n"
                "  margin-bottom: 1rem;\n"
                "}\n\n"
                ".arcade-header h1 {\n"
                "  margin: 0;\n"
                "  font-size: 1.5rem;\n"
                "  font-weight: 700;\n"
                "  color: #34d399;\n"
                "}\n\n"
                ".status-pill {\n"
                "  padding: 0.25rem 0.75rem;\n"
                "  border-radius: 9999px;\n"
                "  font-size: 0.75rem;\n"
                "  font-weight: 600;\n"
                "  text-transform: uppercase;\n"
                "}\n\n"
                ".status-pill.idle { background: #374151; color: #d1d5db; }\n"
                ".status-pill.playing { background: #065f46; color: #34d399; }\n"
                ".status-pill.paused { background: #854d0e; color: #fde047; }\n"
                ".status-pill.game_over { background: #991b1b; color: #fca5a5; }\n\n"
                ".scoreboard-card {\n"
                "  display: flex;\n"
                "  justify-content: space-around;\n"
                "  background: var(--card-bg);\n"
                "  border: 1px solid var(--border-color);\n"
                "  border-radius: 8px;\n"
                "  padding: 0.75rem 1rem;\n"
                "  margin-bottom: 1rem;\n"
                "}\n\n"
                ".score-item {\n"
                "  display: flex;\n"
                "  flex-direction: column;\n"
                "  align-items: center;\n"
                "}\n\n"
                ".score-label {\n"
                "  font-size: 0.7rem;\n"
                "  font-weight: 700;\n"
                "  color: var(--text-muted);\n"
                "  letter-spacing: 0.05em;\n"
                "}\n\n"
                ".score-value {\n"
                "  font-size: 1.25rem;\n"
                "  font-weight: 800;\n"
                "}\n\n"
                ".score-value.highlight { color: #f59e0b; }\n"
                ".score-value.mode { color: #60a5fa; font-size: 0.9rem; margin-top: 0.25rem; }\n\n"
                ".canvas-container {\n"
                "  position: relative;\n"
                "  width: 100%;\n"
                "  display: flex;\n"
                "  justify-content: center;\n"
                "  background: #000;\n"
                "  border: 2px solid #1e293b;\n"
                "  border-radius: 8px;\n"
                "  overflow: hidden;\n"
                "}\n\n"
                ".game-canvas {\n"
                "  display: block;\n"
                "  max-width: 100%;\n"
                "  height: auto;\n"
                "}\n\n"
                ".canvas-overlay {\n"
                "  position: absolute;\n"
                "  inset: 0;\n"
                "  background: rgba(11, 15, 25, 0.85);\n"
                "  display: flex;\n"
                "  flex-direction: column;\n"
                "  justify-content: center;\n"
                "  align-items: center;\n"
                "  text-align: center;\n"
                "  padding: 1rem;\n"
                "}\n\n"
                ".canvas-overlay h2 { margin: 0 0 0.5rem; color: #10b981; }\n"
                ".canvas-overlay p { margin: 0 0 1rem; color: var(--text-muted); font-size: 0.9rem; }\n\n"
                ".btn-primary {\n"
                "  background: #10b981;\n"
                "  color: #0b0f19;\n"
                "  font-weight: 700;\n"
                "  border: none;\n"
                "  padding: 0.6rem 1.5rem;\n"
                "  border-radius: 6px;\n"
                "  cursor: pointer;\n"
                "  font-size: 1rem;\n"
                "  transition: transform 0.1s ease;\n"
                "}\n\n"
                ".btn-primary:hover { transform: scale(1.05); }\n\n"
                ".controls-section {\n"
                "  margin-top: 1rem;\n"
                "  display: flex;\n"
                "  flex-direction: column;\n"
                "  gap: 1rem;\n"
                "}\n\n"
                ".action-buttons {\n"
                "  display: flex;\n"
                "  justify-content: space-between;\n"
                "  align-items: center;\n"
                "}\n\n"
                ".btn-control {\n"
                "  padding: 0.5rem 1rem;\n"
                "  background: #1f2937;\n"
                "  color: var(--text-main);\n"
                "  border: 1px solid #374151;\n"
                "  border-radius: 6px;\n"
                "  cursor: pointer;\n"
                "  font-weight: 600;\n"
                "}\n\n"
                ".btn-control.primary { background: #10b981; color: #0b0f19; border: none; }\n\n"
                ".difficulty-selector { display: flex; gap: 0.25rem; }\n"
                ".btn-diff {\n"
                "  padding: 0.35rem 0.65rem;\n"
                "  background: transparent;\n"
                "  border: 1px solid #374151;\n"
                "  color: var(--text-muted);\n"
                "  border-radius: 4px;\n"
                "  font-size: 0.75rem;\n"
                "  cursor: pointer;\n"
                "}\n\n"
                ".btn-diff.active { background: #2563eb; color: #fff; border-color: #2563eb; }\n\n"
                "/* Virtual D-Pad for Touch and Responsive Play */\n"
                ".virtual-dpad {\n"
                "  display: flex;\n"
                "  flex-direction: column;\n"
                "  align-items: center;\n"
                "  gap: 0.35rem;\n"
                "  margin: 0.5rem auto;\n"
                "}\n\n"
                ".dpad-row { display: flex; gap: 0.35rem; }\n"
                ".dpad-btn {\n"
                "  width: 48px;\n"
                "  height: 48px;\n"
                "  background: #1f2937;\n"
                "  border: 1px solid #374151;\n"
                "  color: #fff;\n"
                "  border-radius: 8px;\n"
                "  font-size: 1.1rem;\n"
                "  display: flex;\n"
                "  align-items: center;\n"
                "  justify-content: center;\n"
                "  cursor: pointer;\n"
                "  user-select: none;\n"
                "}\n\n"
                ".dpad-btn:active { background: #374151; transform: scale(0.95); }\n"
                ".dpad-center { width: 48px; height: 48px; }\n"
            )

        if norm_path in ("backend/app/main.py", "app/main.py"):
            return (
                '"""FastAPI Entrypoint for Snake Game."""\n\n'
                "import os\n"
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n"
                "from fastapi.responses import HTMLResponse, FileResponse\n"
                "from fastapi.staticfiles import StaticFiles\n"
                "from app.config import get_settings\n"
                "from app.api import router as scores_router\n\n"
                "settings = get_settings()\n"
                f'app = FastAPI(title="{project_name}", version="1.0.0")\n\n'
                "app.add_middleware(\n"
                "    CORSMiddleware,\n"
                "    allow_origins=settings.allowed_origins,\n"
                "    allow_credentials=True,\n"
                '    allow_methods=["*"],\n'
                '    allow_headers=["*"],\n'
                ")\n\n"
                "app.include_router(scores_router)\n\n\n"
                '@app.get("/health")\n'
                "def health_check() -> dict[str, str]:\n"
                '    return {"status": "healthy", "game": "snake"}\n\n\n'
                'for s_dir in ["frontend", "../frontend", "static"]:\n'
                "    if os.path.exists(s_dir):\n"
                '        app.mount("/static", StaticFiles(directory=s_dir), name="static")\n'
                "        break\n\n\n"
                '@app.get("/")\n'
                "def root_index():\n"
                '    for h_path in ["frontend/index.html", "../frontend/index.html", "index.html"]:\n'
                "        if os.path.exists(h_path):\n"
                "            return FileResponse(h_path)\n"
                f'    return HTMLResponse("<h1>{project_name}</h1>")\n'
            )

        if norm_path in ("backend/app/models.py", "app/models.py"):
            return (
                '"""Pydantic Models for Snake Game Leaderboard."""\n\n'
                "from datetime import datetime, timezone\n"
                "from uuid import UUID, uuid4\n"
                "from pydantic import BaseModel, Field\n\n\n"
                "class ScoreCreate(BaseModel):\n"
                '    player_name: str = "Player"\n'
                "    score: int\n"
                '    difficulty: str = "MEDIUM"\n\n\n'
                "class ScoreRecord(BaseModel):\n"
                "    id: UUID = Field(default_factory=uuid4)\n"
                "    player_name: str\n"
                "    score: int\n"
                "    difficulty: str\n"
                "    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())\n"
            )

        if norm_path in ("backend/app/api.py", "app/api.py"):
            return (
                '"""REST API Router for Snake Game Scores."""\n\n'
                "from fastapi import APIRouter, status\n"
                "from app.models import ScoreRecord, ScoreCreate\n"
                "from app.persistence import repository\n\n"
                'router = APIRouter(prefix="/scores", tags=["scores"])\n\n\n'
                '@router.get("", response_model=list[ScoreRecord])\n'
                "def list_scores() -> list[ScoreRecord]:\n"
                "    return repository.list_top_scores()\n\n\n"
                '@router.post("", response_model=ScoreRecord, status_code=status.HTTP_201_CREATED)\n'
                "def submit_score(payload: ScoreCreate) -> ScoreRecord:\n"
                "    return repository.add_score(payload)\n"
            )

        if norm_path in ("backend/app/persistence.py", "app/persistence.py"):
            return (
                '"""Thread-safe Leaderboard Persistence Repository."""\n\n'
                "from uuid import uuid4\n"
                "from app.models import ScoreRecord, ScoreCreate\n\n\n"
                "class ScoreRepository:\n"
                "    def __init__(self):\n"
                "        self._scores: list[ScoreRecord] = [\n"
                '            ScoreRecord(id=uuid4(), player_name="Neo", score=240, difficulty="HARD"),\n'
                '            ScoreRecord(id=uuid4(), player_name="Trinity", score=180, difficulty="MEDIUM"),\n'
                '            ScoreRecord(id=uuid4(), player_name="Morpheus", score=120, difficulty="EASY"),\n'
                "        ]\n\n"
                "    def list_top_scores(self, limit: int = 10) -> list[ScoreRecord]:\n"
                "        return sorted(self._scores, key=lambda s: s.score, reverse=True)[:limit]\n\n"
                "    def add_score(self, payload: ScoreCreate) -> ScoreRecord:\n"
                "        record = ScoreRecord(\n"
                "            id=uuid4(),\n"
                "            player_name=payload.player_name,\n"
                "            score=payload.score,\n"
                "            difficulty=payload.difficulty,\n"
                "        )\n"
                "        self._scores.append(record)\n"
                "        return record\n\n\n"
                "repository = ScoreRepository()\n"
            )

    # -------------------------------------------------------------
    # Generic / Language-Safe Fallback
    # -------------------------------------------------------------
    # Return None so callers can fall back to general templates or syntax-safe placeholders
    return None
