/**
 * Sidebar — right-edge task panel container.
 * Shows ARIA header + scrollable list of task cards.
 * Includes a settings panel toggled by a gear icon.
 * @param {{ onSubmitTask?: (desc: string) => void }} props
 */
import { useState } from 'react';
import useTaskStore from '../../store/taskStore.js';
import { useTasks } from '../../hooks/useTasks.js';
import TaskCard from './TaskCard.jsx';
import SettingsPanel from './SettingsPanel.jsx';
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
  const [showSettings, setShowSettings] = useState(false);

  const handleToggle = (taskId) => {
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
  };

  return (
    <div className={`sidebar ${sidebarVisible ? 'sidebar-visible animate-slide-in-right' : 'sidebar-hidden'}`}>
      {/* Header */}
      <div className="sidebar-header">
        {showSettings ? (
          /* Back arrow when settings is open */
          <div className="sidebar-logo" style={{ gap: '8px' }}>
            <button
              className="settings-back-btn"
              title="Back to tasks"
              aria-label="Back to tasks"
              onClick={() => setShowSettings(false)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 12H5" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
            </button>
            <span className="sidebar-wordmark">Settings</span>
          </div>
        ) : (
          /* Normal ARIA logo */
          <div className="sidebar-logo">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <span className="sidebar-wordmark">ARIA</span>
          </div>
        )}

        <div className="sidebar-badge-group">
          {!showSettings && runningCount > 0 && (
            <span className="sidebar-running-badge">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse-dot" />
              {runningCount} running
            </span>
          )}
          {!showSettings && totalCount > 0 && (
            <span className="sidebar-count">{totalCount}</span>
          )}

          {/* Gear icon */}
          <button
            className={`sidebar-settings-btn ${showSettings ? 'active' : ''}`}
            title="Settings"
            aria-label="Open settings"
            onClick={() => setShowSettings(!showSettings)}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>

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

      {/* Content: Settings or Task list */}
      {showSettings ? (
        <SettingsPanel />
      ) : (
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
      )}
    </div>
  );
}
