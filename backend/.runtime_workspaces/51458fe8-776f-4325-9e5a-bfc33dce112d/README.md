# Executive Analytics Dashboard

A real-time executive analytics dashboard that presents KPI summary cards, filterable metric tables, and CSV export capabilities, enabling senior leaders to quickly assess business performance and make data-driven decisions.

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
