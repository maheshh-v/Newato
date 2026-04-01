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
   * Listen for task submitted event (forwarded from overlay to sidebar).
   * @param {(description: string) => void} callback
   */
  onTaskSubmitted: (callback) => {
    ipcRenderer.on('task-submitted', (event, description) => callback(description));
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
