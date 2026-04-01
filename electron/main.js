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

// ─── Python Backend ───────────────────────────────────────────────────────────

function startPythonBackend() {
  if (IS_DEV) {
    console.log('[ARIA] Dev mode: expecting backend to be run externally');
    // Poll until backend is actually responding
    pollBackendHealth();
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

  // Poll until backend is responding
  pollBackendHealth();
}

// ─── Backend Health Check ─────────────────────────────────────────────────────

function pollBackendHealth(attempts = 0) {
  const http = require('http');
  const maxAttempts = 45; // 45 seconds max wait

  // Initial delay on first attempt to let the OS bind the port
  if (attempts === 0) {
    setTimeout(() => pollBackendHealth(1), 2000);
    return;
  }

  let retryCalled = false;
  const doRetry = () => {
    if (retryCalled) return;
    retryCalled = true;
    if (attempts >= maxAttempts) {
      console.error('[ARIA] Backend failed to start after', maxAttempts, 'seconds');
      return;
    }
    setTimeout(() => pollBackendHealth(attempts + 1), 1000);
  };

  const req = http.get(`http://127.0.0.1:${WS_PORT}/ping`, (res) => {
    if (res.statusCode === 200) {
      backendReady = true;
      console.log('[ARIA] Backend health check passed');
    } else {
      doRetry();
    }
  });

  req.on('error', () => {
    doRetry();
  });

  req.setTimeout(1500, () => {
    req.destroy();
    // destroy() triggers 'error' and thus doRetry()
  });
}

// ─── Overlay Window ───────────────────────────────────────────────────────────

function createOverlayWindow() {
  const { screen } = require('electron');
  const display = screen.getPrimaryDisplay();
  const { width, height } = display.bounds;

  overlayWindow = new BrowserWindow({
    width: 580,
    height: 56,
    x: Math.round(width / 2 - 290),
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

  const sidebarUrl = IS_DEV
    ? 'http://localhost:5173/?window=sidebar'
    : `file://${path.join(__dirname, '../frontend/dist/index.html')}?window=sidebar`;

  sidebarWindow.loadURL(sidebarUrl);
  sidebarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: false });

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
  if (sidebarWindow.isVisible()) {
    sidebarWindow.hide();
  } else {
    sidebarWindow.show();
  }
}

function showSidebar() {
  if (sidebarWindow && !sidebarWindow.isVisible()) {
    sidebarWindow.show();
  }
}

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

function setupIPC() {
  // Overlay → submit task → hide overlay → show sidebar
  ipcMain.on('task-submitted', (event, description) => {
    // Filter out dismiss signals — they are not real tasks
    if (!description || description === '__dismiss__') {
      if (overlayWindow) overlayWindow.hide();
      return;
    }
    console.log('[ARIA] Task submitted from overlay:', description);
    if (overlayWindow) overlayWindow.hide();
    showSidebar();
    // Forward to sidebar so it knows a task was submitted
    if (sidebarWindow) {
      sidebarWindow.webContents.send('task-submitted', description);
    }
  });

  // Overlay resize (for suggestions panel)
  ipcMain.on('overlay-resize', (event, height) => {
    if (overlayWindow) {
      overlayWindow.setSize(580, Math.max(56, height));
    }
  });

  // Open file externally
  ipcMain.on('open-file', (event, filePath) => {
    shell.openPath(filePath);
  });

  // Sidebar requests backend status
  ipcMain.handle('get-backend-status', () => ({ ready: backendReady }));
}

// ─── App Lifecycle ────────────────────────────────────────────────────────────

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
