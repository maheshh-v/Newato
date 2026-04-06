/**
 * ARIA Electron Preload Script
 * Provides a safe context bridge between renderer (React) and main process.
 * contextIsolation: true — no direct Node.js access in renderer.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aria', {
  /**
   * Submit a task from the overlay input.
   * @param {string} description
   */
  submitTask: (description) => {
    ipcRenderer.send('task-submitted', description);
  },

  /**
   * Set sidebar collapsed state
   * @param {boolean} isCollapsed
   */
  setSidebarCollapsed: (isCollapsed) => {
    ipcRenderer.send('set-sidebar-collapsed', isCollapsed);
  },

  /**
   * Inform main process whether assistant panel is active.
   * @param {boolean} isActive
   */
  setOverlayActive: (isActive) => {
    ipcRenderer.send('set-overlay-active', isActive);
  },

  /**
   * Set ignore mouse events mode for the window.
   * @param {boolean} ignore
   * @param {{forward?: boolean}} options
   */
  setIgnoreMouseEvents: (ignore, options) => {
    ipcRenderer.send('set-ignore-mouse-events', ignore, options);
  },

  /**
   * Control current window (minimize/close) from renderer.
   * @param {'minimize'|'close'} action
   */
  windowAction: (action) => {
    ipcRenderer.send('window-action', action);
  },

  /**
   * Open a file with the system default application.
   * @param {string} filePath
   */
  openFile: (filePath) => {
    ipcRenderer.send('open-file', filePath);
  },

  /**
   * Get the backend connection status.
   * @returns {Promise<{ready: boolean}>}
   */
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),

  /**
   * Listen for overlay focus event (called when overlay becomes visible).
   * @param {() => void} callback
   */
  onOverlayFocus: (callback) => {
    ipcRenderer.on('overlay-focus', () => callback());
  },

  /**
   * Listen for explicit assistant panel open command.
   * @param {() => void} callback
   */
  onAssistantOpenPanel: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('assistant-open-panel', handler);
    return () => ipcRenderer.removeListener('assistant-open-panel', handler);
  },

  /**
   * Listen for collapse-to-dot requests from main process.
   * @param {() => void} callback
   */
  onAssistantCollapseToDot: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('assistant-collapse-to-dot', handler);
    return () => ipcRenderer.removeListener('assistant-collapse-to-dot', handler);
  },

  /**
   * Listen for task submitted event (forwarded from overlay to sidebar).
   * @param {(description: string) => void} callback
   */
  onTaskSubmitted: (callback) => {
    const handler = (event, description) => callback(description);
    ipcRenderer.on('task-submitted', handler);
    return () => ipcRenderer.removeListener('task-submitted', handler);
  },

  /**
   * Listen for expand sidebar command from main process.
   * @param {() => void} callback
   */
  onExpandSidebar: (callback) => {
    const handler = () => callback();
    ipcRenderer.on('expand-sidebar', handler);
    return () => ipcRenderer.removeListener('expand-sidebar', handler);
  },

  /**
   * Determine which window we're running in from the URL param.
   * @returns {'overlay' | 'sidebar'}
   */
  getWindowType: () => {
    const params = new URLSearchParams(window.location.search);
    return params.get('window') || 'overlay';
  },
});
