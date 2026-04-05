const { app, BrowserWindow, globalShortcut, Tray, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const IS_DEV = process.argv.includes('--dev') || !app.isPackaged;

const FRONTEND_PATH = IS_DEV
  ? 'http://localhost:5173'
  : `file://${path.join(__dirname, 'dist/index.html')}`;

const SHORTCUT = process.platform === 'darwin'
  ? 'Command+Shift+Space'
  : 'Control+Shift+Space';

const getWindowUrl = (winName) => {
  return IS_DEV
    ? `http://localhost:5173/?window=${winName}`
    : `${FRONTEND_PATH}?window=${winName}`;
};

let overlayWindow = null;
let sidebarWindow = null;
let tray = null;

// ───────────────── Overlay ─────────────────
function createOverlayWindow() {
  const { screen } = require('electron');
  const { width, height } = screen.getPrimaryDisplay().bounds;

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
    },
  });

  overlayWindow.loadURL(getWindowUrl('overlay'));

  let justShown = false;
  overlayWindow._setJustShown = () => {
    justShown = true;
    setTimeout(() => (justShown = false), 300);
  };

  overlayWindow.on('blur', () => {
    if (justShown) return;
    overlayWindow.hide();
  });
}

// ───────────────── Sidebar (FIXED) ─────────────────
function createSidebarWindow() {
  const { screen } = require('electron');
  const { width, height } = screen.getPrimaryDisplay().bounds;

  sidebarWindow = new BrowserWindow({
    width: 320,
    height: height,
    x: width - 320,
    y: 0,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    show: false, // 👈 important (start hidden)
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  sidebarWindow.loadURL(getWindowUrl('sidebar'));
}

// ───────────────── FIXED SHOW SIDEBAR ─────────────────
function showSidebar() {
  if (!sidebarWindow) return;

  sidebarWindow.show();     // 👈 force visible
  sidebarWindow.focus();    // 👈 bring front
}

// ───────────────── Toggle Overlay ─────────────────
function toggleOverlay() {
  if (!overlayWindow) return;

  if (overlayWindow.isVisible()) {
    overlayWindow.hide();
  } else {
    overlayWindow._setJustShown();
    overlayWindow.show();
    overlayWindow.focus();
    overlayWindow.webContents.send('overlay-focus');
  }
}

// ───────────────── IPC ─────────────────
let backendProcess = null;

function spawnBackend() {
  if (IS_DEV) {
    console.log('Skipping backend spawn in dev mode');
    return;
  }

  const backendDir = path.join(process.resourcesPath, 'backend');
  const pythonExe = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
  
  if (!fs.existsSync(pythonExe)) {
    console.error('[ARIA] Python executable not found in packaged app:', pythonExe);
    return;
  }

  console.log('[ARIA] Spawning packaged backend...', pythonExe);
  // Spawn the backend using uvicorn
  backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'main:app', '--port', '8765'], {
    cwd: backendDir,
    env: { ...process.env, PYTHONPATH: backendDir }
  });

  backendProcess.stdout.on('data', (data) => console.log(`[Backend] ${data}`));
  backendProcess.stderr.on('data', (data) => console.error(`[Backend ERR] ${data}`));
  backendProcess.on('close', (code) => console.log(`[Backend] exited with code ${code}`));
}

function setupIPC() {
  ipcMain.on('task-submitted', (event, description) => {
    if (!description || description === '__dismiss__') {
      overlayWindow?.hide();
      return;
    }

    console.log('[ARIA] Task:', description);

    overlayWindow?.hide();
    showSidebar();

    sidebarWindow?.webContents.send('task-submitted', description);
  });

  ipcMain.on('window-action', (event, action) => {
   const win = BrowserWindow.fromWebContents(event.sender);
  if (!win) return;

  if (action === 'minimize') {
    if (win === sidebarWindow) {
      sidebarWindow.minimize();   // ✅ actual minimize
    } else {
      win.hide(); // overlay hide
    }
  }

  if (action === 'close') {
    if (win === overlayWindow) {
      overlayWindow.hide();
    } else if (win === sidebarWindow) {
      sidebarWindow.minimize();   // ✅ better UX
    } else {
      win.hide();
    }
  }
});
}

// ───────────────── Tray ─────────────────
function createTray() {
  tray = new Tray(path.join(__dirname, 'assets/icon.png'));

  const menu = Menu.buildFromTemplate([
    { label: 'Open Overlay', click: toggleOverlay },
    { label: 'Open Sidebar', click: showSidebar },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() },
  ]);

  tray.setContextMenu(menu);
}

// ───────────────── App Start ─────────────────
app.whenReady().then(() => {
  spawnBackend();
  createOverlayWindow();
  createSidebarWindow();
  createTray();
  setupIPC();

  globalShortcut.register(SHORTCUT, toggleOverlay);

  console.log('🚀 ARIA Ready');
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (backendProcess) {
    console.log('[ARIA] Killing backend process...');
    backendProcess.kill();
  }
});