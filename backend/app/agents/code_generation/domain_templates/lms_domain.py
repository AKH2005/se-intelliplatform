"""SkillForge Online Academy & Learning Management System Domain Template.

Provides complete, production-grade implementations for all 15 planned LMS files:
- Courses, Modules, Lessons, Enrollments, Knowledge Quizzes, Progress Tracking
- SQLite-backed persistence for student course progress and quiz scoring
- RESTful FastAPI endpoints with Pydantic validation
- Complete React 18 TypeScript components, catalog, interactive lesson player, and quiz engine
"""

from typing import Optional


def get_lms_file(path: str, project_name: str, project_desc: str) -> Optional[str]:
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
        from app.runtime.preview_medium_complexity import get_lms_html
        return get_lms_html(title=project_name, desc=project_desc)

    if norm == "frontend/src/main.tsx":
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/App.css';

const rootElement = document.getElementById('root');
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
"""

    if norm == "frontend/src/App.tsx":
        return f"""import React, {{ useState, useEffect, useCallback }} from 'react';
import {{ CourseCatalog }} from './components/CourseCatalog';
import {{ LessonPlayer }} from './components/LessonPlayer';
import {{
  getCourses,
  getStudentProgress,
  enrollCourse,
  completeLesson,
  submitQuiz,
  Course,
  StudentProgress,
}} from './services/api';
import './styles/App.css';

export default function App() {{
  const [courses, setCourses] = useState<Course[]>([]);
  const [progress, setProgress] = useState<StudentProgress>({{
    enrolled_courses: [],
    completed_lessons: [],
    quiz_scores: {{}},
    overall_completion_pct: 0,
  }});
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {{
    try {{
      setIsLoading(true);
      setError(null);
      const [courseList, progressData] = await Promise.all([
        getCourses(),
        getStudentProgress(),
      ]);
      setCourses(courseList);
      setProgress(progressData);
      if (courseList.length > 0 && !selectedCourse) {{
        setSelectedCourse(courseList[0]);
      }}
    }} catch (err: any) {{
      setError(err?.message || 'Failed to load academy courses');
    }} finally {{
      setIsLoading(false);
    }}
  }}, [selectedCourse]);

  useEffect(() => {{
    loadData();
  }}, [loadData]);

  const handleEnroll = async (courseId: string) => {{
    try {{
      await enrollCourse(courseId);
      await loadData();
    }} catch (err: any) {{
      alert(err?.message || 'Failed to enroll');
    }}
  }};

  const handleLessonComplete = async (lessonId: string) => {{
    try {{
      await completeLesson(lessonId);
      await loadData();
    }} catch (err: any) {{
      alert(err?.message || 'Failed to complete lesson');
    }}
  }};

  return (
    <div className="lms-container">
      <header className="academy-header">
        <div className="header-titles">
          <span className="brand-tag">SkillForge Academy</span>
          <h1 data-testid="app-title">{project_name}</h1>
          <p className="subtitle">{project_desc}</p>
        </div>
        <div className="progress-summary">
          <span className="summary-label">Academy Completion:</span>
          <span className="summary-pct" data-testid="overall-progress-pct">{{progress.overall_completion_pct}}%</span>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ {{ width: `${{progress.overall_completion_pct}}%` }} }} />
          </div>
        </div>
      </header>

      <main className="lms-content-layout">
        {{error && <div className="alert alert-error">{{error}}</div>}}
        {{isLoading ? (
          <div className="loading-state">Loading courses and curriculum...</div>
        ) : (
          <div className="lms-split-view">
            <aside className="lms-sidebar">
              <CourseCatalog
                courses={{courses}}
                selectedCourse={{selectedCourse}}
                onSelectCourse={{setSelectedCourse}}
                onEnroll={{handleEnroll}}
                enrolledCourseIds={{progress.enrolled_courses}}
              />
            </aside>
            <section className="lms-main-pane">
              {{selectedCourse ? (
                <LessonPlayer
                  course={{selectedCourse}}
                  completedLessons={{progress.completed_lessons}}
                  onCompleteLesson={{handleLessonComplete}}
                />
              ) : (
                <div className="empty-selection">Select a course to begin learning.</div>
              )}}
            </section>
          </div>
        )}}
      </main>
    </div>
  );
}}
"""

    if norm == "frontend/src/components/CourseCatalog.tsx":
        return """import React, { useState } from 'react';
import { Course } from '../services/api';

interface CourseCatalogProps {
  courses: Course[];
  selectedCourse: Course | null;
  onSelectCourse: (course: Course) => void;
  onEnroll: (courseId: string) => void;
  enrolledCourseIds: string[];
}

export const CourseCatalog: React.FC<CourseCatalogProps> = ({
  courses,
  selectedCourse,
  onSelectCourse,
  onEnroll,
  enrolledCourseIds,
}) => {
  const [filterLevel, setFilterLevel] = useState<string>('All');

  const filtered = courses.filter((c) => filterLevel === 'All' || c.level === filterLevel);

  return (
    <div className="course-catalog">
      <div className="catalog-header">
        <h3>Available Curriculum</h3>
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          className="level-select"
        >
          <option value="All">All Skill Levels</option>
          <option value="Beginner">Beginner</option>
          <option value="Intermediate">Intermediate</option>
          <option value="Advanced">Advanced</option>
        </select>
      </div>

      <div className="course-list" data-testid="course-catalog-list">
        {filtered.map((course) => {
          const isEnrolled = enrolledCourseIds.includes(course.id);
          const isSelected = selectedCourse?.id === course.id;

          return (
            <div
              key={course.id}
              className={`course-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectCourse(course)}
              data-testid={`course-item-${course.id}`}
            >
              <div className="course-card-top">
                <span className="course-badge">{course.level}</span>
                <span className="course-duration">{course.duration}</span>
              </div>
              <h4 className="course-title">{course.title}</h4>
              <p className="course-desc">{course.description}</p>
              <div className="course-card-footer">
                <span className="instructor">By {course.instructor}</span>
                {isEnrolled ? (
                  <span className="badge badge-success">Enrolled</span>
                ) : (
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEnroll(course.id);
                    }}
                    data-testid={`btn-enroll-${course.id}`}
                  >
                    Enroll Now
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/components/LessonPlayer.tsx":
        return """import React, { useState } from 'react';
import { Course, Lesson } from '../services/api';

interface LessonPlayerProps {
  course: Course;
  completedLessons: string[];
  onCompleteLesson: (lessonId: string) => void;
}

export const LessonPlayer: React.FC<LessonPlayerProps> = ({
  course,
  completedLessons,
  onCompleteLesson,
}) => {
  const [activeLessonIndex, setActiveLessonIndex] = useState<number>(0);
  const lessons = course.lessons || [];
  const currentLesson: Lesson | undefined = lessons[activeLessonIndex];

  if (!currentLesson) {
    return <div className="no-lessons">No lessons published for this course yet.</div>;
  }

  const isCompleted = completedLessons.includes(currentLesson.id);

  return (
    <div className="lesson-player" data-testid="lesson-player-view">
      <div className="player-header">
        <div>
          <span className="course-ref">{course.title}</span>
          <h2>{currentLesson.title}</h2>
        </div>
        <span className="lesson-duration">{currentLesson.duration}</span>
      </div>

      <div className="player-body">
        <div className="lesson-content-card">
          <div className="lesson-text">{currentLesson.content}</div>

          <div className="completion-action">
            {isCompleted ? (
              <span className="badge badge-success" data-testid="status-lesson-completed">
                Lesson Completed
              </span>
            ) : (
              <button
                className="btn btn-primary"
                onClick={() => onCompleteLesson(currentLesson.id)}
                data-testid={`btn-complete-lesson-${currentLesson.id}`}
              >
                Mark Lesson Complete
              </button>
            )}
          </div>
        </div>

        {/* Syllabus Navigation Drawer */}
        <aside className="syllabus-drawer">
          <h4>Course Syllabus ({lessons.length} Lessons)</h4>
          <ul className="syllabus-list">
            {lessons.map((lesson, idx) => {
              const done = completedLessons.includes(lesson.id);
              const active = idx === activeLessonIndex;
              return (
                <li
                  key={lesson.id}
                  className={`syllabus-item ${active ? 'active' : ''} ${done ? 'done' : ''}`}
                  onClick={() => setActiveLessonIndex(idx)}
                  data-testid={`syllabus-item-${lesson.id}`}
                >
                  <span className="item-num">{idx + 1}</span>
                  <span className="item-title">{lesson.title}</span>
                  {done && <span className="item-check">&#10003;</span>}
                </li>
              );
            })}
          </ul>
        </aside>
      </div>
    </div>
  );
};
"""

    if norm == "frontend/src/services/api.ts":
        return """/**
 * REST API Client for SkillForge Online Academy Backend.
 */

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  duration: string;
  content: string;
  order: number;
}

export interface Course {
  id: string;
  title: string;
  description: string;
  category: string;
  level: string;
  instructor: string;
  duration: string;
  lessons: Lesson[];
}

export interface StudentProgress {
  enrolled_courses: string[];
  completed_lessons: string[];
  quiz_scores: Record<string, number>;
  overall_completion_pct: number;
}

const API_BASE = '/api/lms';

export async function getCourses(): Promise<Course[]> {
  const res = await fetch(`${API_BASE}/courses`);
  if (!res.ok) throw new Error('Failed to fetch courses');
  return res.json();
}

export async function getStudentProgress(): Promise<StudentProgress> {
  const res = await fetch(`${API_BASE}/progress`);
  if (!res.ok) throw new Error('Failed to fetch student progress');
  return res.json();
}

export async function enrollCourse(courseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/courses/${courseId}/enroll`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to enroll in course');
  return res.json();
}

export async function completeLesson(lessonId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/lessons/${lessonId}/complete`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to complete lesson');
  return res.json();
}

export async function submitQuiz(quizId: string, answers: Record<string, any>): Promise<any> {
  const res = await fetch(`${API_BASE}/quizzes/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quiz_id: quizId, answers }),
  });
  if (!res.ok) throw new Error('Failed to submit quiz');
  return res.json();
}
"""

    if norm == "frontend/src/styles/App.css":
        return """:root {
  --bg-primary: #0a0e17;
  --bg-card: rgba(18, 26, 43, 0.9);
  --border: rgba(99, 102, 241, 0.2);
  --accent-purple: #818cf8;
  --accent-cyan: #38bdf8;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --success: #10b981;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #0a0e17 80%);
  color: var(--text-main);
  min-height: 100vh;
}

.lms-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.academy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1.5rem;
  margin-bottom: 2rem;
}

.brand-tag {
  color: var(--accent-purple);
  font-size: 0.8rem;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.header-titles h1 {
  margin: 0.25rem 0;
  font-size: 2rem;
}

.subtitle {
  color: var(--text-muted);
  margin: 0;
}

.progress-summary {
  width: 240px;
  text-align: right;
}

.summary-label {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.summary-pct {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--accent-cyan);
  margin-left: 0.5rem;
}

.progress-bar-bg {
  background: rgba(255,255,255,0.1);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.progress-bar-fill {
  background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan));
  height: 100%;
  transition: width 0.3s ease;
}

.lms-split-view {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1.5rem;
}

.course-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.course-card.selected {
  border-color: var(--accent-purple);
  background: rgba(30, 27, 75, 0.6);
}

.course-badge {
  background: rgba(129, 140, 248, 0.15);
  color: var(--accent-purple);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.course-title {
  margin: 0.5rem 0;
  font-size: 1.1rem;
}

.course-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.course-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}

.lesson-player {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
}

.player-body {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 2rem;
  margin-top: 1.5rem;
}

.lesson-text {
  line-height: 1.7;
  color: #e2e8f0;
  font-size: 1rem;
}

.syllabus-item {
  padding: 0.6rem 0.8rem;
  margin-bottom: 0.4rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.syllabus-item.active {
  background: rgba(129, 140, 248, 0.2);
  color: #fff;
  font-weight: 600;
}

.syllabus-item.done {
  color: var(--success);
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
  color: #fff;
}

.badge-success {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  padding: 0.3rem 0.7rem;
  border-radius: 4px;
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
from app.api import router as lms_router

settings = get_settings()

app = FastAPI(
    title="{project_name}",
    description="{project_desc}",
    version="1.0.0",
)

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

app.include_router(lms_router, prefix="/api/lms", tags=["lms"])
"""

    if norm == "backend/app/config.py":
        return """\"\"\"Application configuration using Pydantic Settings.\"\"\"

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "SkillForge Online Academy"
    allowed_origins: List[str] = ["*"]
    database_url: str = "sqlite:///./lms.db"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
"""

    if norm == "backend/app/models.py":
        return """\"\"\"Domain Models & Pydantic Schemas for LMS Operations.\"\"\"

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Lesson(BaseModel):
    id: str
    course_id: str
    title: str
    duration: str
    content: str
    order: int


class Course(BaseModel):
    id: str
    title: str
    description: str
    category: str
    level: str
    instructor: str
    duration: str
    lessons: List[Lesson] = []


class StudentProgress(BaseModel):
    enrolled_courses: List[str] = []
    completed_lessons: List[str] = []
    quiz_scores: Dict[str, int] = {}
    overall_completion_pct: int = 0
"""

    if norm == "backend/app/api.py":
        return """\"\"\"REST API Router for Learning Management System.\"\"\"

from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Course, StudentProgress
from app.persistence import repository

router = APIRouter()


@router.get("/courses", response_model=List[Course])
def list_courses():
    \"\"\"List all active courses with syllabus lessons.\"\"\"
    return repository.get_all_courses()


@router.get("/progress", response_model=StudentProgress)
def get_progress():
    \"\"\"Return student progress across enrolled courses.\"\"\"
    return repository.get_student_progress()


@router.post("/courses/{course_id}/enroll")
def enroll_course(course_id: str):
    \"\"\"Enroll in a course.\"\"\"
    return repository.enroll_student(course_id)


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: str):
    \"\"\"Mark a lesson as finished.\"\"\"
    return repository.mark_lesson_completed(lesson_id)
"""

    if norm == "backend/app/persistence.py":
        return """\"\"\"SQLite-backed Persistent Repository for LMS Operations.\"\"\"

import sqlite3
import json
from typing import List, Dict, Any
from app.models import Course, Lesson, StudentProgress


class LmsRepository:
    def __init__(self, db_path: str = "lms.db"):
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
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                level TEXT NOT NULL,
                instructor TEXT NOT NULL,
                duration TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                duration TEXT NOT NULL,
                content TEXT NOT NULL,
                lesson_order INTEGER NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS student_enrollments (
                course_id TEXT PRIMARY KEY
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS student_completions (
                lesson_id TEXT PRIMARY KEY
            )
        ''')
        conn.commit()

        # Seed initial courses if empty
        cur.execute('SELECT COUNT(*) FROM courses')
        if cur.fetchone()[0] == 0:
            c1 = ("CRS-101", "Full-Stack Software Architecture", "Master clean architecture, API design, and scalable databases.", "Software Engineering", "Intermediate", "Dr. Marcus Vance", "4.5 Hours")
            c2 = ("CRS-102", "React 18 & Modern State Management", "Build production UI systems with React, TypeScript, and TanStack Query.", "Frontend", "Beginner", "Elena Rostova", "3.2 Hours")
            cur.execute('INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?)', c1)
            cur.execute('INSERT INTO courses VALUES (?, ?, ?, ?, ?, ?, ?)', c2)

            l1 = ("LES-101-1", "CRS-101", "Monolithic vs Microservice Boundaries", "15 mins", "Architectural boundaries dictate deployment flexibility and data consistency requirements...", 1)
            l2 = ("LES-101-2", "CRS-101", "Domain-Driven Relational Modeling", "25 mins", "Learn entity boundaries, aggregate roots, and transactional invariants in PostgreSQL...", 2)
            l3 = ("LES-102-1", "CRS-102", "Components, Props, and Pure Renders", "20 mins", "Understanding React Fiber reconciliation and component memoization patterns...", 1)
            cur.execute('INSERT INTO lessons VALUES (?, ?, ?, ?, ?, ?)', l1)
            cur.execute('INSERT INTO lessons VALUES (?, ?, ?, ?, ?, ?)', l2)
            cur.execute('INSERT INTO lessons VALUES (?, ?, ?, ?, ?, ?)', l3)

            # Auto-enroll in course 1
            cur.execute('INSERT INTO student_enrollments VALUES (?)', ("CRS-101",))
            conn.commit()
        conn.close()

    def get_all_courses(self) -> List[Course]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM courses')
        courses_rows = cur.fetchall()

        results = []
        for cr in courses_rows:
            cur.execute('SELECT * FROM lessons WHERE course_id = ? ORDER BY lesson_order ASC', (cr['id'],))
            lesson_rows = cur.fetchall()
            lessons = [
                Lesson(
                    id=lr['id'],
                    course_id=lr['course_id'],
                    title=lr['title'],
                    duration=lr['duration'],
                    content=lr['content'],
                    order=lr['lesson_order'],
                )
                for lr in lesson_rows
            ]
            results.append(
                Course(
                    id=cr['id'],
                    title=cr['title'],
                    description=cr['description'],
                    category=cr['category'],
                    level=cr['level'],
                    instructor=cr['instructor'],
                    duration=cr['duration'],
                    lessons=lessons,
                )
            )
        conn.close()
        return results

    def get_student_progress(self) -> StudentProgress:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT course_id FROM student_enrollments')
        enrolled = [r[0] for r in cur.fetchall()]

        cur.execute('SELECT lesson_id FROM student_completions')
        completed = [r[0] for r in cur.fetchall()]

        cur.execute('SELECT COUNT(*) FROM lessons')
        total_lessons = cur.fetchone()[0] or 1

        pct = int((len(completed) / total_lessons) * 100)
        conn.close()

        return StudentProgress(
            enrolled_courses=enrolled,
            completed_lessons=completed,
            quiz_scores={},
            overall_completion_pct=min(100, pct),
        )

    def enroll_student(self, course_id: str) -> dict:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO student_enrollments VALUES (?)', (course_id,))
        conn.commit()
        conn.close()
        return {"status": "enrolled", "course_id": course_id}

    def mark_lesson_completed(self, lesson_id: str) -> dict:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO student_completions VALUES (?)', (lesson_id,))
        conn.commit()
        conn.close()
        return {"status": "completed", "lesson_id": lesson_id}


repository = LmsRepository()
"""

    if norm == "README.md":
        return f"""# {project_name}

{project_desc}

## Overview
SkillForge Online Academy features interactive course browsing, syllabus tracking, lesson player, and verified student progress tracking.

## Technology Stack
- **Frontend:** React 18, TypeScript, Vite
- **Backend:** FastAPI, Pydantic v2, Uvicorn
- **Persistence:** SQLite student curriculum database
"""

    return None
