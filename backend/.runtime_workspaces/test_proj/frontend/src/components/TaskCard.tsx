import React from 'react';
import { Task } from '../services/api';

interface TaskCardProps {
  task: Task;
  onToggleComplete: (task: Task) => void;
  onDelete: (id: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onToggleComplete,
  onDelete,
}) => {
  const isCompleted = task.status === 'COMPLETED';
  const priorityClass = `priority-${task.priority.toLowerCase()}`;

  return (
    <div className={`task-card ${isCompleted ? 'completed' : ''}`}>
      <div className="task-header">
        <label className="task-checkbox-label">
          <input
            type="checkbox"
            checked={isCompleted}
            onChange={() => onToggleComplete(task)}
          />
          <span className="task-title">{task.title}</span>
        </label>
        <span className={`priority-badge ${priorityClass}`}>
          {task.priority}
        </span>
      </div>
      {task.description && (
        <p className="task-description">{task.description}</p>
      )}
      <div className="task-footer">
        {task.due_date && (
          <span className="task-due-date">Due: {task.due_date}</span>
        )}
        <button
          type="button"
          className="btn-delete"
          onClick={() => onDelete(task.id)}
          aria-label={`Delete task ${task.title}`}
        >
          Delete
        </button>
      </div>
    </div>
  );
};
