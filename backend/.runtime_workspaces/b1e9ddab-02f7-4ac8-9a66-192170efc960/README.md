# Simple Task Manager

A lightweight task management app that lets users create, complete, delete, and filter tasks with a clear counter. It offers a clean, responsive interface for efficient task tracking on any device.

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
