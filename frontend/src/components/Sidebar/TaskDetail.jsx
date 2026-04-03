/**
 * TaskDetail — expanded view of a task showing step log and screenshot.
 * @param {{ task: import('../../store/taskStore').Task, onClose: () => void }} props
 */
import useTaskStore from '../../store/taskStore.js';
import StatusBadge from '../shared/StatusBadge.jsx';

function formatDuration(startMs, endMs) {
  const ms = (endMs || Date.now()) - startMs;
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export default function TaskDetail({ task, onClose }) {
  const outputDir = useTaskStore((s) => s.outputDir);
  const description = typeof task.description === 'string' ? task.description : '';
  const outputFiles = Array.isArray(task.output_files) ? task.output_files : [];
  const steps = Array.isArray(task.steps) ? task.steps : [];

  const handleOpenFile = (filename) => {
    const base = outputDir || '';
    const fullPath = `${base}/${task.id}/${filename}`;
    if (window.aria?.openFile) {
      window.aria.openFile(fullPath);
    } else {
      console.log('Open file:', fullPath);
    }
  };

  return (
    <div className="task-detail animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-3 gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-text-primary text-sm font-medium leading-tight break-words">
            {description}
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            <StatusBadge status={task.status} />
            {task.started_at && (
              <span className="text-text-muted text-xs font-mono">
                {formatDuration(task.started_at, task.completed_at)}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-secondary transition-colors flex-shrink-0 p-1"
          title="Collapse"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Summary */}
      {task.summary && (
        <div className="mb-3 p-2.5 bg-green-500/5 border border-green-500/15 rounded-lg">
          <p className="text-green-400 text-xs leading-relaxed">{task.summary}</p>
        </div>
      )}

      {/* Error */}
      {task.error_reason && (
        <div className="mb-3 p-2.5 bg-red-500/5 border border-red-500/15 rounded-lg">
          <p className="text-red-400 text-xs leading-relaxed">{task.error_reason}</p>
        </div>
      )}

      {/* Screenshot */}
      {task.latest_screenshot && (
        <div className="mb-3 rounded-lg overflow-hidden border border-bg-border">
          <img
            src={`data:image/png;base64,${task.latest_screenshot}`}
            alt="Browser preview"
            className="w-full object-cover"
            style={{ maxHeight: 140 }}
          />
        </div>
      )}

      {/* Output files */}
      {outputFiles.length > 0 && (
        <div className="mb-3">
          <p className="text-text-muted text-[10px] font-semibold tracking-widest mb-1.5">OUTPUT FILES</p>
          <div className="flex flex-col gap-1">
            {outputFiles.map((f) => (
              <button
                key={f}
                onClick={() => handleOpenFile(f)}
                className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-xs transition-colors text-left"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                {f}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step log */}
      <div>
        <p className="text-text-muted text-[10px] font-semibold tracking-widest mb-1.5">
          STEPS ({steps.length})
        </p>
        <div className="step-log">
          {steps.map((step, i) => (
            <div key={i} className="step-item">
              <span className="step-number">{step.step_number}</span>
              <span className="step-text">{step.step_text}</span>
            </div>
          ))}
          {steps.length === 0 && (
            <p className="text-text-muted text-xs italic">No steps yet...</p>
          )}
        </div>
      </div>
    </div>
  );
}
