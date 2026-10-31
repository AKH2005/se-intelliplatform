# Simple Task Manager

A lightweight web app that lets users create, track, and manage tasks efficiently. It offers intuitive controls for adding, completing, and deleting tasks, along with filtering and real-time counters, all wrapped in a clean responsive UI.

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
