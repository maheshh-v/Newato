/**
 * ARIA Zustand Task Store
 * Single source of truth for all task state in the frontend.
 */
import { create } from 'zustand';

function asString(value, fallback = '') {
  return typeof value === 'string' ? value : fallback;
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeTask(taskData = {}) {
  return {
    id: asString(taskData.id),
    description: asString(taskData.description),
    status: ['queued', 'running', 'completed', 'failed'].includes(taskData.status) ? taskData.status : 'queued',
    task_type: typeof taskData.task_type === 'string' ? taskData.task_type : null,
    created_at: typeof taskData.created_at === 'number' ? taskData.created_at : Date.now(),
    started_at: typeof taskData.started_at === 'number' ? taskData.started_at : null,
    completed_at: typeof taskData.completed_at === 'number' ? taskData.completed_at : null,
    summary: typeof taskData.summary === 'string' ? taskData.summary : null,
    error_reason: typeof taskData.error_reason === 'string' ? taskData.error_reason : null,
    output_files: asArray(taskData.output_files),
    step_count: typeof taskData.step_count === 'number' ? taskData.step_count : 0,
    steps: asArray(taskData.steps),
    progress: typeof taskData.progress === 'number' ? taskData.progress : 0,
    current_step_text: typeof taskData.current_step_text === 'string' ? taskData.current_step_text : null,
    latest_screenshot: typeof taskData.latest_screenshot === 'string' ? taskData.latest_screenshot : null,
    total_steps_estimate: typeof taskData.total_steps_estimate === 'number' ? taskData.total_steps_estimate : 10,
  };
}

function normalizeStep(stepData = {}) {
  return {
    step_number: typeof stepData.step_number === 'number' ? stepData.step_number : 0,
    tool_name: asString(stepData.tool_name),
    step_text: asString(stepData.step_text),
    timestamp: typeof stepData.timestamp === 'number' ? stepData.timestamp : Date.now(),
    progress: typeof stepData.progress === 'number' ? stepData.progress : undefined,
  };
}

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
  sidebarVisible: true,

  /** @type {string|null} Backend output directory path */
  outputDir: null,

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Add or update a task (upsert by id). */
  upsertTask: (taskData) => set((state) => {
    const normalized = normalizeTask(taskData);
    const existing = state.tasks.find((t) => t.id === normalized.id);
    if (existing) {
      return {
        tasks: state.tasks.map((t) =>
          t.id === normalized.id ? { ...t, ...normalized, steps: asArray(t.steps) } : t
        ),
      };
    }
    return { tasks: [normalized, ...state.tasks] };
  }),

  /** Append a step to a task and update progress/current step text. */
  addStep: (taskId, stepData) => set((state) => ({
    tasks: state.tasks.map((t) => {
      if (t.id !== taskId) return t;
      const normalizedStep = normalizeStep(stepData);
      return {
        ...t,
        steps: [...asArray(t.steps), normalizedStep],
        current_step_text: normalizedStep.step_text || t.current_step_text,
        progress: normalizedStep.progress ?? t.progress,
        step_count: (t.step_count || 0) + 1,
      };
    }),
  })),

  /** Update screenshot for a task. */
  setScreenshot: (taskId, imageB64) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === taskId
        ? {
            ...t,
            latest_screenshot: typeof imageB64 === 'string' ? imageB64 : null,
          }
        : t
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

  /** Replace entire task list (used on initial load). */
  setTasks: (taskList) => set({
    tasks: taskList.map((t) => ({
      steps: [],
      progress: 0,
      current_step_text: null,
      latest_screenshot: null,
      output_files: [],
      ...t,
    })),
    sidebarVisible: taskList.length > 0, // Show sidebar if tasks exist
  }),
  /** Clear all tasks and reset sidebar state. */
  clearAllTasks: () => set({
    tasks: [],
    expandedTaskId: null,
    sidebarVisible: true,
  }),

  setOutputDir: (dir) => set({ outputDir: dir }),
}));

export default useTaskStore;
