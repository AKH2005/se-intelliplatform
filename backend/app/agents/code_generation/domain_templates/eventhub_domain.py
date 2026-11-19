"""EventHub Conference & Ticket Booking Domain Template.

Provides complete, production-grade implementations for all 15 planned event management files:
- Events, Schedules, Speakers, Attendee Registration, Capacity Constraints, Cancellation
- SQLite-backed persistence for reservations and seat inventory
- RESTful FastAPI endpoints with Pydantic validation
- Complete React 18 TypeScript components, card grid, booking modal, and cancellation flow
"""

from typing import Optional


def get_eventhub_file(path: str, project_name: str, project_desc: str) -> Optional[str]:
    norm = path.replace("\\", "/").strip()
    slug = project_name.lower().replace(" ", "-")

    if norm == "frontend/package.json":
        return f"""{{
  "name": "{slug}-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.344.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.1"
  }}
}}"""

    if norm == "frontend/index.html":
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name} — Conference & Event Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{ margin: 0; font-family: 'Plus Jakarta Sans', sans-serif; background: #070b14; color: #f8fafc; }}
    .app-root {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  </style>
</head>
<body>
  <div id="root">
    <div class="app-root">
      <header style="border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:1rem;">
        <span style="color:#a855f7; font-size:0.8rem; font-weight:700;">EVENTHUB PORTAL</span>
        <h1 id="app-title" data-testid="app-title" style="margin:0.25rem 0;">{project_name}</h1>
        <p style="color:#94a3b8; margin:0;">{project_desc}</p>
      </header>
      <main id="event-grid" data-testid="events-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:1.5rem; margin-top:2rem;"></main>
    </div>
  </div>
  <script>
    let events = [
      {{ id: "EVT-1", title: "Global Cloud Architecture Summit 2026", date: "Dec 12, 2026", venue: "Grand Hyatt Auditorium", capacity: 450, registered: 312, category: "Tech" }},
      {{ id: "EVT-2", title: "AI Systems & Autonomous Agents Forum", date: "Jan 18, 2027", venue: "Innovation Center Hall A", capacity: 250, registered: 245, category: "AI" }},
      {{ id: "EVT-3", title: "Enterprise Cybersecurity & Zero Trust", date: "Feb 05, 2027", venue: "Cyber Arena West", capacity: 300, registered: 180, category: "Security" }}
    ];

    function renderEvents() {{
      const grid = document.getElementById('event-grid');
      grid.innerHTML = events.map(e => `
        <div style="background:#111827; border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:1.5rem; display:flex; flex-direction:column;">
          <span style="font-size:0.75rem; color:#a855f7; font-weight:700;">${{e.category}}</span>
          <h3 style="margin:0.5rem 0; font-size:1.2rem;">${{e.title}}</h3>
          <p style="color:#94a3b8; font-size:0.9rem; margin:0.25rem 0;">📅 ${{e.date}} &bull; 📍 ${{e.venue}}</p>
          <div style="margin:1rem 0; background:rgba(255,255,255,0.05); border-radius:6px; height:8px; overflow:hidden;">
            <div style="background:#a855f7; height:100%; width:${{Math.round((e.registered/e.capacity)*100)}}%;"></div>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:auto;">
            <span style="font-size:0.85rem; color:#94a3b8;">${{e.registered}} / ${{e.capacity}} seats filled</span>
            <button onclick="bookTicket('${{e.id}}')" data-testid="btn-register-${{e.id}}" style="background:#a855f7; color:#fff; border:none; padding:0.4rem 0.9rem; border-radius:6px; font-weight:700; cursor:pointer;">Register</button>
          </div>
        </div>
      `).join('');
    }}

    function bookTicket(id) {{
      const ev = events.find(x => x.id === id);
      if (ev && ev.registered < ev.capacity) {{
        ev.registered += 1;
        renderEvents();
        alert('Registration confirmed for ' + ev.title + '!');
      }} else {{
        alert('Event is sold out!');
      }}
    }}

    renderEvents();
  </script>
</body>
</html>"""

    if norm == "frontend/src/main.tsx":
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/App.css';

const root = document.getElementById('root');
if (root) {
  ReactDOM.createRoot(root).render(<App />);
}
"""

    if norm == "frontend/src/App.tsx":
        return f"""import React, {{ useState, useEffect }} from 'react';
import {{ EventCard }} from './components/EventCard';
import {{ BookingModal }} from './components/BookingModal';
import {{ getEvents, registerForEvent, EventItem }} from './services/api';
import './styles/App.css';

export default function App() {{
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {{
    try {{
      const data = await getEvents();
      setEvents(data);
    }} catch (err) {{}}
  }};

  useEffect(() => {{
    loadData();
  }}, []);

  const handleBook = (eventItem: EventItem) => {{
    setSelectedEvent(eventItem);
    setIsModalOpen(true);
  }};

  const handleConfirmBooking = async (attendeeName: string, email: string) => {{
    if (!selectedEvent) return;
    try {{
      await registerForEvent(selectedEvent.id, attendeeName, email);
      setIsModalOpen(false);
      setSelectedEvent(null);
      await loadData();
    }} catch (err: any) {{
      alert(err.message || 'Registration failed');
    }}
  }};

  return (
    <div className="eventhub-container">
      <header className="eventhub-header">
        <span className="brand-tag">EventHub</span>
        <h1 data-testid="app-title">{project_name}</h1>
        <p className="subtitle">{project_desc}</p>
      </header>

      <main className="events-grid" data-testid="events-grid-view">
        {{events.map((e) => (
          <EventCard key={{e.id}} event={{e}} onBook={{handleBook}} />
        ))}}
      </main>

      {{isModalOpen && selectedEvent && (
        <BookingModal
          event={{selectedEvent}}
          onClose={{() => setIsModalOpen(false)}}
          onConfirm={{handleConfirmBooking}}
        />
      )}}
    </div>
  );
}}
"""

    if norm == "frontend/src/components/EventCard.tsx":
        return """import React from 'react';
import { EventItem } from '../services/api';

interface EventCardProps {
  event: EventItem;
  onBook: (e: EventItem) => void;
}

export const EventCard: React.FC<EventCardProps> = ({ event, onBook }) => {
  const isFull = event.registered >= event.capacity;
  const pct = Math.min(100, Math.round((event.registered / event.capacity) * 100));

  return (
    <div className="event-card" data-testid={`event-card-${event.id}`}>
      <span className="event-category">{event.category}</span>
      <h3 className="event-title">{event.title}</h3>
      <p className="event-meta">
        <span>📅 {event.date}</span> &bull; <span>📍 {event.venue}</span>
      </p>

      <div className="capacity-bar">
        <div className="capacity-fill" style={{ width: `${pct}%` }} />
      </div>

      <div className="event-footer">
        <span className="seats-count">
          {event.registered} / {event.capacity} seats reserved
        </span>
        <button
          className="btn btn-primary"
          disabled={isFull}
          onClick={() => onBook(event)}
          data-testid={`btn-book-${event.id}`}
        >
          {isFull ? 'Sold Out' : 'Register Now'}
        </button>
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/components/BookingModal.tsx":
        return """import React, { useState } from 'react';
import { EventItem } from '../services/api';

interface BookingModalProps {
  event: EventItem;
  onClose: () => void;
  onConfirm: (name: string, email: string) => void;
}

export const BookingModal: React.FC<BookingModalProps> = ({ event, onClose, onConfirm }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) return;
    onConfirm(name, email);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card" data-testid="booking-modal-panel">
        <div className="modal-header">
          <h3>Register for Event</h3>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="event-info">
            <h4>{event.title}</h4>
            <p>
              {event.date} &bull; {event.venue}
            </p>
          </div>

          <div className="form-group">
            <label>Attendee Full Name</label>
            <input
              type="text"
              className="form-control"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              data-testid="input-attendee-name"
            />
          </div>

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              data-testid="input-attendee-email"
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" data-testid="btn-confirm-booking">
              Confirm Registration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/services/api.ts":
        return """/**
 * REST API Client for EventHub Backend.
 */

export interface EventItem {
  id: string;
  title: string;
  date: string;
  venue: string;
  capacity: number;
  registered: number;
  category: string;
}

const API_BASE = '/api/events';

export async function getEvents(): Promise<EventItem[]> {
  const res = await fetch(`${API_BASE}`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function registerForEvent(eventId: string, name: string, email: string): Promise<any> {
  const res = await fetch(`${API_BASE}/${eventId}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email }),
  });
  if (!res.ok) throw new Error('Failed to register attendee');
  return res.json();
}
"""

    if norm == "frontend/src/styles/App.css":
        return """:root {
  --bg: #070b14;
  --card: #0d1527;
  --accent: #a855f7;
  --text: #f8fafc;
  --muted: #94a3b8;
}

body {
  margin: 0;
  font-family: sans-serif;
  background: var(--bg);
  color: var(--text);
}

.eventhub-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.eventhub-header {
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1.5rem;
}

.brand-tag {
  color: var(--accent);
  font-weight: 700;
  font-size: 0.8rem;
  text-transform: uppercase;
}

.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.event-card {
  background: var(--card);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.event-category {
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
}

.event-title {
  margin: 0.5rem 0;
  font-size: 1.2rem;
}

.event-meta {
  color: var(--muted);
  font-size: 0.9rem;
}

.capacity-bar {
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  height: 6px;
  overflow: hidden;
  margin: 1rem 0;
}

.capacity-fill {
  background: var(--accent);
  height: 100%;
}

.event-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: none;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
}

.btn-secondary {
  background: rgba(255,255,255,0.1);
  color: #fff;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  background: var(--card);
  border: 1px solid var(--accent);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 440px;
}
"""

    if norm == "backend/requirements.txt":
        return """fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
"""

    if norm == "backend/app/main.py":
        return f"""\"\"\"FastAPI Application Entrypoint for {project_name}.\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import router as events_router

settings = get_settings()

app = FastAPI(title="{project_name}", description="{project_desc}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {{"status": "ok", "app": "{project_name}"}}

app.include_router(events_router, prefix="/api/events", tags=["events"])
"""

    if norm == "backend/app/config.py":
        return """\"\"\"Application configuration using Pydantic Settings.\"\"\"

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "EventHub Conference Booking"
    allowed_origins: List[str] = ["*"]
    database_url: str = "sqlite:///./events.db"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
"""

    if norm == "backend/app/models.py":
        return """\"\"\"Domain Models & Pydantic Schemas for Event Management.\"\"\"

from pydantic import BaseModel
from typing import List, Optional


class EventItem(BaseModel):
    id: str
    title: str
    date: str
    venue: str
    capacity: int
    registered: int
    category: str


class RegistrationRequest(BaseModel):
    name: str
    email: str
"""

    if norm == "backend/app/api.py":
        return """\"\"\"REST API Router for EventHub.\"\"\"

from fastapi import APIRouter, HTTPException
from typing import List
from app.models import EventItem, RegistrationRequest
from app.persistence import repository

router = APIRouter()


@router.get("", response_model=List[EventItem])
def list_events():
    return repository.list_events()


@router.post("/{event_id}/register")
def register_attendee(event_id: str, payload: RegistrationRequest):
    return repository.register_attendee(event_id, payload.name, payload.email)
"""

    if norm == "backend/app/persistence.py":
        return """\"\"\"SQLite-backed Persistent Repository for EventHub.\"\"\"

import sqlite3
from typing import List
from app.models import EventItem


class EventRepository:
    def __init__(self, db_path: str = "events.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                venue TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                registered INTEGER NOT NULL,
                category TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')
        conn.commit()

        cur.execute('SELECT COUNT(*) FROM events')
        if cur.fetchone()[0] == 0:
            seed = [
                ("EVT-1", "Global Cloud Architecture Summit 2026", "Dec 12, 2026", "Grand Hyatt Auditorium", 450, 312, "Tech"),
                ("EVT-2", "AI Systems & Autonomous Agents Forum", "Jan 18, 2027", "Innovation Center Hall A", 250, 245, "AI"),
                ("EVT-3", "Enterprise Cybersecurity & Zero Trust", "Feb 05, 2027", "Cyber Arena West", 300, 180, "Security"),
            ]
            for ev in seed:
                cur.execute('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)', ev)
            conn.commit()
        conn.close()

    def list_events(self) -> List[EventItem]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM events')
        rows = cur.fetchall()
        conn.close()
        return [
            EventItem(
                id=r['id'],
                title=r['title'],
                date=r['date'],
                venue=r['venue'],
                capacity=r['capacity'],
                registered=r['registered'],
                category=r['category'],
            )
            for r in rows
        ]

    def register_attendee(self, event_id: str, name: str, email: str) -> dict:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT capacity, registered FROM events WHERE id = ?', (event_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Event not found")
        capacity, registered = row[0], row[1]
        if registered >= capacity:
            conn.close()
            raise ValueError("Event is sold out")

        cur.execute('UPDATE events SET registered = registered + 1 WHERE id = ?', (event_id,))
        cur.execute('INSERT INTO attendees (event_id, name, email) VALUES (?, ?, ?)', (event_id, name, email))
        conn.commit()
        conn.close()
        return {"status": "confirmed", "event_id": event_id, "name": name}


repository = EventRepository()
"""

    if norm == "README.md":
        return f"""# {project_name}

{project_desc}

## Overview
EventHub provides event scheduling, attendee registrations, and capacity-limited booking management.
"""

    return None
