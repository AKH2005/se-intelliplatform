import React, { useState, useEffect } from 'react';
import { Task, TaskCreateInput, taskApi } from './services/api';
import { TaskCard } from './components/TaskCard';
import { TaskForm } from './components/TaskForm';

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'COMPLETED'>('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await taskApi.listTasks();
      setTasks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleCreateTask = async (input: TaskCreateInput) => {
    const created = await taskApi.createTask(input);
    setTasks((prev) => [created, ...prev]);
  };

  const handleToggleComplete = async (task: Task) => {
    const newStatus = task.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    const updated = await taskApi.updateTask(task.id, { status: newStatus });
    setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)));
  };

  const handleDeleteTask = async (id: string) => {
    await taskApi.deleteTask(id);
    setTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const handleClearCompleted = async () => {
    const completedTasks = tasks.filter((task) => task.status === 'COMPLETED');
    for (const task of completedTasks) {
      await taskApi.deleteTask(task.id);
    }
    setTasks((prev) => prev.filter((t) => t.status !== 'COMPLETED'));
  };

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'PENDING') return t.status !== 'COMPLETED';
    if (filter === 'COMPLETED') return t.status === 'COMPLETED';
    return true;
  });

  const completedCount = tasks.filter((t) => t.status === 'COMPLETED').length;

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Task Item Manager d0db83b4</h1>
        <div className="task-stats">
          <span>Total: {tasks.length}</span>
          <span>Completed: {completedCount}</span>
          <span>Pending: {tasks.length - completedCount}</span>
        </div>
      </header>

      <main>
        <TaskForm onSubmit={handleCreateTask} onClearCompleted={handleClearCompleted} />

        <div className="filter-bar">
          <button
            className={filter === 'ALL' ? 'active' : ''}
            onClick={() => setFilter('ALL')}
          >
            All ({tasks.length})
          </button>
          <button
            className={filter === 'PENDING' ? 'active' : ''}
            onClick={() => setFilter('PENDING')}
          >
            Pending ({tasks.length - completedCount})
          </button>
          <button
            className={filter === 'COMPLETED' ? 'active' : ''}
            onClick={() => setFilter('COMPLETED')}
          >
            Completed ({completedCount})
          </button>
        </div>

        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={loadTasks}>Retry</button>
          </div>
        )}

        {isLoading ? (
          <div className="loading-state">Loading tasks...</div>
        ) : filteredTasks.length === 0 ? (
          <div className="empty-state">
            <p>No tasks found. Create your first task above!</p>
          </div>
        ) : (
          <div className="task-list">
            {filteredTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onToggleComplete={handleToggleComplete}
                onDelete={handleDeleteTask}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
