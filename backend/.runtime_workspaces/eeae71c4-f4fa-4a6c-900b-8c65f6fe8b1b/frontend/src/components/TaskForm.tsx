import React, { useState } from 'react';
import { TaskCreateInput } from '../services/api';

interface TaskFormProps {
  onSubmit: (task: TaskCreateInput) => Promise<void>;
  onClearCompleted: () => Promise<void>;
}

export const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, onClearCompleted }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      await onSubmit({
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        due_date: dueDate || undefined,
      });
      setTitle('');
      setDescription('');
      setDueDate('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <h3>Create New Task</h3>
      <div className="form-row">
        <input
          type="text"
          placeholder="What needs to be done?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as any)}
        >
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
        </select>
      </div>
      <div className="form-row">
        <input
          type="text"
          placeholder="Optional description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
        />
        <button type="submit" disabled={isSubmitting || !title.trim()}>
          {isSubmitting ? 'Adding...' : 'Add Task'}
        </button>
      </div>
      <div className="form-actions">
        <button type="button" onClick={onClearCompleted} className="btn-clear-completed">
          Clear Completed
        </button>
      </div>
    </form>
  );
};
