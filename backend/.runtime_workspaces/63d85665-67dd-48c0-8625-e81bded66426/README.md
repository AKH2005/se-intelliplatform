# Carrom Master

A realistic digital carrom game that offers immersive gameplay, precise physics, and competitive multiplayer modes, allowing players to master the classic board game from any device.

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
