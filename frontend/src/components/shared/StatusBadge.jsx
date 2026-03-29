/**
 * StatusBadge — colored pill showing task status.
 * @param {{ status: 'queued'|'running'|'completed'|'failed' }} props
 */
export default function StatusBadge({ status }) {
  const configs = {
    queued: {
      label: 'QUEUED',
      className: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20',
    },
    running: {
      label: 'RUNNING',
      className: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
      dot: true,
    },
    completed: {
      label: 'DONE',
      className: 'bg-green-500/10 text-green-400 border border-green-500/20',
    },
    failed: {
      label: 'FAILED',
      className: 'bg-red-500/10 text-red-400 border border-red-500/20',
    },
  };

  const config = configs[status] || configs.queued;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-widest ${config.className}`}
    >
      {config.dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse-dot" />
      )}
      {config.label}
    </span>
  );
}
