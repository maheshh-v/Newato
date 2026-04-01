/**
 * ARIA Electron Main Process
 * Manages: two windows (overlay + sidebar), global shortcuts, system tray,
 * Python backend subprocess, and WebSocket connection monitoring.
 */

const { app, BrowserWindow, globalShortcut, Tray, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// ─── Constants ────────────────────────────────────────────────────────────────
const IS_DEV = process.argv.includes('--dev');
const FRONTEND_URL = IS_DEV ? 'http://localhost:5173' : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;
const WS_PORT = 8765;
const SHORTCUT = process.platform === 'darwin' ? 'Command+Shift+Space' : 'Control+Shift+Space';

// ─── State ────────────────────────────────────────────────────────────────────
let overlayWindow = null;
let sidebarWindow = null;
let tray = null;
let pythonProcess = null;
let backendReady = false;

// Prevent multiple Electron instances in dev/prod. Multiple instances can
// cause inconsistent window behavior (e.g., old overlay size appearing again).
const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
}

app.on('second-instance', () => {
  if (sidebarWindow) {
    if (sidebarWindow.isMinimized()) sidebarWindow.restore();
    sidebarWindow.show();
    sidebarWindow.focus();
    return;
  }

  if (overlayWindow) {
    overlayWindow.show();
    overlayWindow.focus();
    overlayWindow.webContents.send('overlay-focus');
  }
});

// ─── Python Backend ───────────────────────────────────────────────────────────

function startPythonBackend() {
  if (IS_DEV) {
    console.log('[ARIA] Dev mode: expecting backend to be run externally');
    backendReady = true; // Assume external dev server is running
    return;
  }

  const backendDir = path.join(__dirname, '../backend');
  const venvPython = process.platform === 'win32'
    ? path.join(backendDir, 'venv', 'Scripts', 'python.exe')
    : path.join(backendDir, 'venv', 'bin', 'python');

  const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python';

  console.log('[ARIA] Starting Python backend...', pythonBin);

  pythonProcess = spawn(pythonBin, [
    '-m', 'uvicorn', 'main:app',
    '--host', '127.0.0.1',
    '--port', String(WS_PORT),
    '--log-level', 'info',
  ], {
    cwd: backendDir,
    env: { ...process.env },
  });

  pythonProcess.stdout.on('data', (data) => {
    const msg = data.toString();
    console.log('[backend]', msg.trim());
    if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
      backendReady = true;
      console.log('[ARIA] Backend ready');
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('[backend:err]', data.toString().trim());
  });

  pythonProcess.on('exit', (code) => {
    console.log('[ARIA] Backend exited with code', code);
    backendReady = false;
  });
}

// ─── Overlay Window ───────────────────────────────────────────────────────────

function createOverlayWindow() {
  const { screen } = require('electron');
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.bounds;

  overlayWindow = new BrowserWindow({
    width: 760,
    height: 96,
    x: Math.round(width / 2 - 380),
    y: Math.round(height * 0.4),
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  const overlayUrl = IS_DEV
    ? 'http://localhost:5173/?window=overlay'
    : `file://${path.join(__dirname, '../frontend/dist/index.html')}?window=overlay`;

  overlayWindow.loadURL(overlayUrl);
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });

  // Hide when loses focus
  overlayWindow.on('blur', () => {
    overlayWindow.hide();
  });

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });

  if (IS_DEV) {
    overlayWindow.webContents.openDevTools({ mode: 'detach' });
  }
}

// ─── Sidebar Window ───────────────────────────────────────────────────────────

function createSidebarWindow() {
  const { screen } = require('electron');
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.bounds;

  sidebarWindow = new BrowserWindow({
    width: 320,
    height: height,
    x: width - 320,
    y: 0,
    frame: false,
    transparent: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    resizable: false,
    show: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  const sidebarUrl = IS_DEV
    ? 'http://localhost:5173/?window=sidebar'
    : `file://${path.join(__dirname, '../frontend/dist/index.html')}?window=sidebar`;

  sidebarWindow.loadURL(sidebarUrl);
  sidebarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });

  // Start minimized so ARIA appears in taskbar without being intrusive on launch.
  sidebarWindow.once('ready-to-show', () => {
    sidebarWindow.minimize();
  });

  sidebarWindow.on('closed', () => {
    sidebarWindow = null;
  });
}

// ─── System Tray ──────────────────────────────────────────────────────────────

function createTray() {
  const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
  // Fallback to a default if icon not found
  tray = new Tray(fs.existsSync(iconPath) ? iconPath : path.join(__dirname, 'assets', 'icon.png'));

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show ARIA',
      click: () => toggleOverlay(),
    },
    {
      label: 'Toggle Sidebar',
      click: () => toggleSidebar(),
    },
    { type: 'separator' },
    {
      label: `Open Output Folder`,
      click: () => {
        const outputDir = path.join(require('os').homedir(), 'ARIA', 'outputs');
        shell.openPath(outputDir);
      },
    },
    { type: 'separator' },
    {
      label: 'Quit ARIA',
      click: () => app.quit(),
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.setToolTip('ARIA — Autonomous Agent');
  tray.on('click', () => toggleOverlay());
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toggleOverlay() {
  if (!overlayWindow) return;
  if (overlayWindow.isVisible()) {
    overlayWindow.hide();
  } else {
    overlayWindow.show();
    overlayWindow.focus();
    overlayWindow.webContents.send('overlay-focus');
  }
}

function toggleSidebar() {
  if (!sidebarWindow) return;
  if (sidebarWindow.isMinimized()) {
    sidebarWindow.restore();
    sidebarWindow.focus();
  } else if (sidebarWindow.isVisible()) {
    sidebarWindow.minimize();
  } else {
    sidebarWindow.show();
    sidebarWindow.focus();
  }
}

function showSidebar() {
  if (!sidebarWindow) return;
  if (sidebarWindow.isMinimized()) {
    sidebarWindow.restore();
  } else if (!sidebarWindow.isVisible()) {
    sidebarWindow.show();
  }
  sidebarWindow.focus();
}

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

function setupIPC() {
  // Overlay → submit task → hide overlay → show sidebar
  ipcMain.on('task-submitted', (event, description) => {
    console.log('[ARIA] Task submitted from overlay:', description);
    if (description === '__dismiss__') {
      if (overlayWindow) overlayWindow.hide();
      return;
    }
    if (overlayWindow) overlayWindow.hide();
    showSidebar();
    // Forward to sidebar so it knows a task was submitted
    if (sidebarWindow) {
      sidebarWindow.webContents.send('task-submitted', description);
    }
  });

  // Overlay resize disabled — overlay window size is fixed at 760x96
  // This prevents stale processes or runtime events from shrinking the prompt.
  // ipcMain.on('overlay-resize', (event, height) => {
  //   if (overlayWindow) {
  //     overlayWindow.setSize(760, Math.max(96, height));
  //   }
  // });

  // Open file externally
  ipcMain.on('open-file', (event, filePath) => {
    shell.openPath(filePath);
  });

  // Window controls for frameless renderer windows
  ipcMain.on('window-action', (event, action) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;

    if (action === 'minimize') {
      if (win === overlayWindow) {
        win.hide();
      } else if (win === sidebarWindow) {
        sidebarWindow.minimize();
      } else if (win.isMinimizable()) {
        win.minimize();
      } else {
        win.hide();
      }
      return;
    }

    if (action === 'close') {
      // Close should hide/minimize the current window
      if (win === overlayWindow) {
        // Overlay: just hide it
        overlayWindow.hide();
      } else if (win === sidebarWindow) {
        // Sidebar: minimize to taskbar (not fully close the app)
        sidebarWindow.minimize();
      } else {
        win.hide();
      }
      return;
    }
  });

  // Sidebar requests backend status
  ipcMain.handle('get-backend-status', () => ({ ready: backendReady }));
}

// ─── App Lifecycle ────────────────────────────────────────────────────────────

if (gotSingleInstanceLock) {
  app.whenReady().then(async () => {
    // Start Python backend (non-blocking)
    startPythonBackend();

  // Create windows
  createOverlayWindow();
  createSidebarWindow();

  // Create system tray
  createTray();

  // Setup IPC
  setupIPC();

  // Register global shortcut
  const registered = globalShortcut.register(SHORTCUT, () => {
    toggleOverlay();
  });

  if (!registered) {
    console.error('[ARIA] Failed to register global shortcut:', SHORTCUT);
  } else {
    console.log('[ARIA] Global shortcut registered:', SHORTCUT);
  }

  // Show sidebar initially (will slide in on first task)
  // Not shown immediately — appears when first task is submitted

    console.log('[ARIA] App ready. Press', SHORTCUT, 'to open overlay.');
  });
}

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
});

app.on('window-all-closed', (e) => {
  // Prevent quit when all windows closed (tray stays)
  e.preventDefault();
});

// Security: prevent new windows from being opened
app.on('web-contents-created', (event, contents) => {
  contents.setWindowOpenHandler(() => ({ action: 'deny' }));
});
