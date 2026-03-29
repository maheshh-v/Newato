/**
 * ProgressBar — animated progress indicator for task cards.
 * @param {{ progress: number, status: string }} props
 */
export default function ProgressBar({ progress = 0, status = 'queued' }) {
  const colorMap = {
    queued: 'bg-yellow-500',
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };

  const barColor = colorMap[status] || colorMap.queued;
  const pct = Math.round(Math.max(0, Math.min(1, progress)) * 100);

  return (
    <div className="w-full h-0.5 bg-bg-border rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ease-out ${barColor} ${status === 'running' ? 'animate-shimmer' : ''}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
