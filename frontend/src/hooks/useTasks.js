/**
 * useTasks — convenience hook for accessing task store.
 * Provides computed values like running task count.
 */
import useTaskStore from '../store/taskStore.js';

export function useTasks() {
  const tasks = useTaskStore((s) => s.tasks);
  const expandedTaskId = useTaskStore((s) => s.expandedTaskId);
  const setExpandedTaskId = useTaskStore((s) => s.setExpandedTaskId);

  const runningCount = tasks.filter((t) => t.status === 'running').length;
  const totalCount = tasks.length;

  return { tasks, expandedTaskId, setExpandedTaskId, runningCount, totalCount };
}
