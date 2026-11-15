# Shadow Master Skill Builder

A web-based tool that lets game designers create, preview, and export custom skills for the Shadow Master game, streamlining the development workflow and ensuring consistency across the game’s skill system.

## Architecture

- **Frontend:** React 18 + TypeScript + Vite (`frontend/`)
- **Backend:** FastAPI + Pydantic (`backend/`)
- **Runtime Preview:** Port 8001 Docker container preview

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
