# Simple Task Manager

A lightweight web app that lets users create, manage, and track tasks efficiently. It offers basic CRUD operations, filtering, and a live counter, all wrapped in a clean, responsive interface.

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
