/**
 * ARIA Zustand Task Store
 * Single source of truth for all task state in the frontend.
 */
import { create } from 'zustand';

/**
 * @typedef {Object} Step
 * @property {number} step_number
 * @property {string} tool_name
 * @property {string} step_text
 * @property {number} timestamp
 * @property {string|null} tool_result
 */

/**
 * @typedef {Object} Task
 * @property {string} id
 * @property {string} description
 * @property {'queued'|'running'|'completed'|'failed'} status
 * @property {string|null} task_type
 * @property {number} created_at
 * @property {number|null} started_at
 * @property {number|null} completed_at
 * @property {string|null} summary
 * @property {string|null} error_reason
 * @property {string[]} output_files
 * @property {number} step_count
 * @property {Step[]} steps
 * @property {number} progress
 * @property {string|null} current_step_text
 * @property {string|null} latest_screenshot
 */

const useTaskStore = create((set, get) => ({
  /** @type {Task[]} tasks ordered newest first */
  tasks: [],

  /** @type {string|null} Currently expanded task ID */
  expandedTaskId: null,

  /** @type {boolean} Whether sidebar is visible */
  sidebarVisible: false,

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Add or update a task (upsert by id). */
  upsertTask: (taskData) => set((state) => {
    const existing = state.tasks.find((t) => t.id === taskData.id);
    if (existing) {
      return {
        tasks: state.tasks.map((t) =>
          t.id === taskData.id ? { ...t, ...taskData } : t
        ),
      };
    }
    // New task — prepend
    const newTask = {
      steps: [],
      progress: 0,
      current_step_text: null,
      latest_screenshot: null,
      output_files: [],
      ...taskData,
    };
    return { tasks: [newTask, ...state.tasks] };
  }),

  /** Append a step to a task and update progress/current step text. */
  addStep: (taskId, stepData) => set((state) => ({
    tasks: state.tasks.map((t) => {
      if (t.id !== taskId) return t;
      return {
        ...t,
        steps: [...t.steps, stepData],
        current_step_text: stepData.step_text || t.current_step_text,
        progress: stepData.progress ?? t.progress,
        step_count: (t.step_count || 0) + 1,
      };
    }),
  })),

  /** Update screenshot for a task. */
  setScreenshot: (taskId, imageB64) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === taskId ? { ...t, latest_screenshot: imageB64 } : t
    ),
  })),

  /** Mark task complete. */
  completeTask: (taskId, data) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === taskId
        ? {
            ...t,
            status: 'completed',
            summary: data.summary,
            output_files: data.output_files || [],
            completed_at: Date.now(),
            progress: 1,
            current_step_text: 'Completed',
          }
        : t
    ),
  })),

  /** Mark task failed. */
  failTask: (taskId, data) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === taskId
        ? {
            ...t,
            status: 'failed',
            error_reason: data.reason,
            completed_at: Date.now(),
            current_step_text: 'Failed',
          }
        : t
    ),
  })),

  /** Remove a task from the list. */
  deleteTask: (taskId) => set((state) => ({
    tasks: state.tasks.filter((t) => t.id !== taskId),
    expandedTaskId: state.expandedTaskId === taskId ? null : state.expandedTaskId,
  })),

  setExpandedTaskId: (id) => set({ expandedTaskId: id }),

  setSidebarVisible: (visible) => set({ sidebarVisible: visible }),
}));

export default useTaskStore;
