/**
 * TaskCard — individual task card in the sidebar.
 * Collapsed: shows name, status, current step, elapsed time.
 * Expanded: shows TaskDetail.
 * @param {{ task: import('../../store/taskStore').Task, isExpanded: boolean, onToggle: () => void }} props
 */
import { useEffect, useState } from 'react';
import useTaskStore from '../../store/taskStore.js';
import StatusBadge from '../shared/StatusBadge.jsx';
import ProgressBar from '../shared/ProgressBar.jsx';
import TaskDetail from './TaskDetail.jsx';

function useElapsedTime(startMs, isRunning) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!isRunning || !startMs) return;
    const id = setInterval(() => setElapsed(Date.now() - startMs), 1000);
    return () => clearInterval(id);
  }, [startMs, isRunning]);
  if (!startMs) return '—';
  const s = Math.floor(elapsed / 1000);
  return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
}

const STATUS_BORDER = {
  queued: 'border-l-yellow-500',
  running: 'border-l-blue-500',
  completed: 'border-l-green-500',
  failed: 'border-l-red-500',
};

export default function TaskCard({ task, isExpanded, onToggle }) {
  const isRunning = task.status === 'running';
  const elapsed = useElapsedTime(task.started_at, isRunning);
  const borderClass = STATUS_BORDER[task.status] || STATUS_BORDER.queued;
  const deleteTask = useTaskStore((s) => s.deleteTask);

  const handleDelete = (e) => {
    e.stopPropagation();
    if (confirm(`Delete task: "${task.description.slice(0, 50)}..."?`)) {
      deleteTask(task.id);
    }
  };

  return (
    <div
      className={`
        task-card border-l-[3px] ${borderClass}
        ${isRunning ? 'running-shimmer' : ''}
        ${isExpanded ? 'expanded' : ''}
      `}
    >
      {/* Collapsed header — always visible, clickable */}
      <div
        className="task-card-header"
        onClick={onToggle}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onToggle()}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center justify-between mb-1.5">
          <StatusBadge status={task.status} />
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-[10px] font-mono">{elapsed}</span>
            <button
              className="task-card-delete-btn"
              onClick={handleDelete}
              title="Delete task"
              aria-label="Delete task"
            >
              ×
            </button>
          </div>
        </div>

        <p className="task-description text-white text-xs font-medium leading-snug line-clamp-2">
          {task.description.length > 90
            ? task.description.slice(0, 88) + '…'
            : task.description}
        </p>

        {task.current_step_text && !isExpanded && (
          <p className="text-gray-400 text-[10px] mt-1.5 truncate">
            {task.current_step_text}
          </p>
        )}

        <div className="mt-2">
          <ProgressBar progress={task.progress || 0} status={task.status} />
        </div>
      </div>

      {/* Expanded detail */}
      {isExpanded && (
        <div className="task-card-detail">
          <TaskDetail task={task} onClose={onToggle} />
        </div>
      )}
    </div>
  );
}
