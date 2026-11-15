# Carrom Master

A digital carrom board game that lets players enjoy realistic gameplay, compete online, and track scores in real time. It offers immersive physics, customizable boards, and engaging multiplayer features.

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
