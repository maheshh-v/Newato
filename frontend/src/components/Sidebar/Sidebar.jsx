/**
 * Sidebar — right-edge task panel container.
 * Shows ARIA header + scrollable list of task cards.
 * Slides in from right on first task.
 * @param {{ onSubmitTask?: (desc: string) => void }} props
 */
import useTaskStore from '../../store/taskStore.js';
import { useTasks } from '../../hooks/useTasks.js';
import TaskCard from './TaskCard.jsx';
import './Sidebar.css';

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-logo">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      </div>
      <p className="empty-title">ARIA</p>
      <p className="empty-hint">Press Ctrl+Shift+Space to start</p>
    </div>
  );
}

export default function Sidebar() {
  const { tasks, expandedTaskId, setExpandedTaskId, runningCount, totalCount } = useTasks();
  const sidebarVisible = useTaskStore((s) => s.sidebarVisible);
  const clearAllTasks = useTaskStore((s) => s.clearAllTasks);

  const handleToggle = (taskId) => {
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
  };

  return (
    <div className={`sidebar ${sidebarVisible ? 'sidebar-visible animate-slide-in-right' : 'sidebar-hidden'}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
          <span className="sidebar-wordmark">ARIA</span>
        </div>
        <div className="sidebar-badge-group">
          {runningCount > 0 && (
            <span className="sidebar-running-badge">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse-dot" />
              {runningCount} running
            </span>
          )}
          {totalCount > 0 && (
            <span className="sidebar-count">{totalCount}</span>
          )}
          {tasks.length > 0 && (
            <button
              type="button"
              className="sidebar-clear-btn"
              title="Clear all tasks"
              onClick={clearAllTasks}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M3 6h18" />
                <path d="M8 6V4h8v2" />
                <path d="M6 6l1 14h10l1-14" />
              </svg>
            </button>
          )}

          <div className="sidebar-window-actions">
            <button
              className="sidebar-window-btn"
              title="Minimize"
              aria-label="Minimize window"
              onClick={() => window.aria?.windowAction?.('minimize')}
            >
              -
            </button>
            <button
              className="sidebar-window-btn sidebar-window-btn-close"
              title="Close"
              aria-label="Close window"
              onClick={() => window.aria?.windowAction?.('close')}
            >
              ×
            </button>
          </div>
        </div>
      </div>

      {/* Task list */}
      <div className="sidebar-task-list">
        {tasks.length === 0 ? (
          <EmptyState />
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              isExpanded={expandedTaskId === task.id}
              onToggle={() => handleToggle(task.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
