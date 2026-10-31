# Executive Analytics Dashboard

A real‑time executive dashboard that aggregates key performance indicators into concise summary cards, offers filterable metric tables for deeper analysis, and allows seamless CSV export for reporting. It empowers decision makers with instant insights and data portability.

## Architecture

- **Frontend:** React + TypeScript + Vite (`frontend/`)
- **Backend:** FastAPI + Pydantic (`backend/`)

## Running Locally

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
