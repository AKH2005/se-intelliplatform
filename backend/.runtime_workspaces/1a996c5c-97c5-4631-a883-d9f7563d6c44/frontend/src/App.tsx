import React, { useState, useEffect } from 'react';
import './styles/App.css';

export default function App() {
  const [isLight, setIsLight] = useState(() => localStorage.getItem('taskflow_theme') === 'light');

  useEffect(() => {
    document.body.className = isLight ? 'light-theme' : '';
    localStorage.setItem('taskflow_theme', isLight ? 'light' : 'dark');
  }, [isLight]);

  const toggleTheme = () => setIsLight((prev) => !prev);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>TaskFlow</h1>
        <button id="btn-theme-toggle" className="btn-secondary" onClick={toggleTheme}>
          {isLight ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>
      </header>
    </div>
  );
}
