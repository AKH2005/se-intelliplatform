# Shadow Duel

A fast‑paced 2D fighting game where players control shadow avatars in dynamic arenas, combining fluid combat mechanics with strategic power‑ups. The game offers single‑player and online multiplayer modes, delivering an immersive experience across mobile and web platforms.

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
