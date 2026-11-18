# SE IntelliPlatform — Project Setup & Execution Guide
**Local-First, Zero-Cloud Installation and Running Manual**

---

## 1. Prerequisites

Ensure the following runtimes are installed on your host workstation (Windows, macOS, or Linux):

- **Python**: Version 3.12 or newer (`python --version`)
- **Node.js**: Version 18.x or 20.x LTS (`node --version`)
- **npm**: Version 9.x or newer (`npm --version`)
- **Git**: (`git --version`)
- *(Optional)* **Docker Desktop**: If containerized runtime sandbox execution is desired. If Docker is not running, the platform smoothly uses local in-process fallback executors.

> [!NOTE]
> **Zero-Cloud Guarantee**: This capstone project requires **no paid cloud hosting, no cloud subscriptions, and no credit card registration**. All databases, services, and agent execution engines run entirely on `localhost`.

---

## 2. Directory Structure Overview

```text
SE-IntelliPlatform/
├── backend/                  # FastAPI Python backend application
│   ├── app/                  # Application core, models, endpoints, services, agents
│   ├── migrations/           # Alembic migration revisions 0001–0010
│   ├── scripts/              # Migration runner (migrate.py)
│   ├── tests/                # Pytest unit and integration test suites
│   ├── alembic.ini           # Alembic database configuration
│   └── requirements.txt      # Python package dependencies
├── frontend/                 # React 18 TypeScript SPA
│   ├── src/                  # Components, 3D scenes, views, context, hooks
│   ├── public/               # Static assets and SPA routing redirects
│   ├── package.json          # Node dependencies and scripts
│   └── vite.config.ts        # Vite configuration with chunk splitting
└── docs/                     # Capstone technical documentation
    └── capstone/             # Phase 6D comprehensive architecture docs
```

---

## 3. Backend Setup & Startup

### Step 3.1: Create Python Virtual Environment
Navigate to the `backend` directory and initialize a virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### Step 3.2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3.3: Configure Environment Variables
Copy the template configuration file:

```bash
cp .env.example .env
```

The default `.env` is pre-configured for instant zero-configuration local development:
- `ENVIRONMENT=development`
- `DATABASE_URL=sqlite+aiosqlite:///./se_intelliplatform.db`
- `LLM_PROVIDER=mock` (enables instant offline test simulation; set to `groq` or `gemini` if API keys are available)

### Step 3.4: Apply Database Migrations
Run the authoritative migration runner:

```bash
python scripts/migrate.py --action upgrade
```

### Step 3.5: Start FastAPI Backend Server
Launch Uvicorn ASGI server on port `8000`:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify backend health by navigating to [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health). OpenAPI interactive documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 4. Frontend Setup & Startup

### Step 4.1: Install Node Dependencies
In a new terminal window, navigate to the `frontend` directory:

```bash
cd frontend
npm install
```

### Step 4.2: Configure Frontend Environment
Ensure `frontend/.env` contains the local backend API URL:

```ini
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

### Step 4.3: Start Vite Development Server
Launch the development server on port `5173`:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open your browser to [http://127.0.0.1:5173](http://127.0.0.1:5173) to access SE IntelliPlatform.

---

## 5. Port Allocation Reference

| Port | Service | Description |
| :--- | :--- | :--- |
| **5173** | React Frontend SPA | Vite local development server with HMR. |
| **8000** | FastAPI Backend API | Core ASGI service, REST endpoints, WebSocket & SSE streams. |
| **8001** | Live Preview Runtime | Sandboxed application preview container manager. |
| **4173** | Vite Preview Server | Production build preview runner (`npm run preview`). |

---

## 6. Running Test Suites

Verify platform integrity by executing the automated test suites:

### Frontend Verification (Vitest + TypeScript)
```bash
cd frontend
npx tsc --noEmit          # Expected: 0 errors
npm test -- --run         # Expected: 42 test files passed (259/259 tests)
npm run build             # Expected: clean production build
```

### Backend Verification (Pytest)
```bash
cd backend
pytest                    # Runs full backend unit and integration tests
```
