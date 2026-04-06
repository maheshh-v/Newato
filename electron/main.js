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

const SIDEBAR_SHORTCUT = process.platform === 'darwin'
  ? 'Command+Shift+S'
  : 'Control+Shift+S';

const getWindowUrl = (winName) => {
  return IS_DEV
    ? `http://localhost:5173/?window=${winName}`
    : `${FRONTEND_PATH}?window=${winName}`;
};

let overlayWindow = null;
let sidebarWindow = null;
let tray = null;
let isOverlayActive = false;

// ───────────────── Overlay ─────────────────
function createOverlayWindow() {
  const { screen } = require('electron');
  const { width, height } = screen.getPrimaryDisplay().bounds;

  overlayWindow = new BrowserWindow({
    width: 430,
    height: Math.min(560, height - 24),
    x: width - 430 - 12,
    y: 12,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    type: 'toolbar',
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
  overlayWindow.setAlwaysOnTop(true, 'screen-saver');

  let justShown = false;
  overlayWindow._setJustShown = () => {
    justShown = true;
    setTimeout(() => (justShown = false), 300);
  };

  overlayWindow.once('ready-to-show', () => {
    if (!overlayWindow) return;
    overlayWindow.setIgnoreMouseEvents(true, { forward: true });
    overlayWindow.setFocusable(false);
    overlayWindow.showInactive();
    overlayWindow.webContents.send('assistant-collapse-to-dot');
  });

  overlayWindow.on('blur', () => {
    if (justShown) return;
    overlayWindow.webContents.send('assistant-collapse-to-dot');
    if (overlayWindow) overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    overlayWindow.showInactive();
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
    transparent: true,
    thickFrame: false, // Prevents Windows DWM invisible bounds
    alwaysOnTop: true,
      type: 'toolbar',
      skipTaskbar: true,
    resizable: false,
    show: false, // 👈 important (start hidden)
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  sidebarWindow.setAlwaysOnTop(true, 'screen-saver');
  sidebarWindow.on('blur', () => { 
    if (sidebarWindow) {
      sidebarWindow.setAlwaysOnTop(true, 'screen-saver');
    } 
  });
  if (process.platform === 'darwin') {
    sidebarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  }
  sidebarWindow.loadURL(getWindowUrl('sidebar'));
}

// ───────────────── FIXED SHOW SIDEBAR ─────────────────
function showSidebar() {
  if (!sidebarWindow) return;

  const { screen } = require('electron');
  const { width, height } = screen.getPrimaryDisplay().bounds;

  sidebarWindow.setBounds({
    width: 320,
    height: height,
    x: width - 320,
    y: 0
  });

  sidebarWindow.show();     // 👈 force visible
  sidebarWindow.focus();    // 👈 bring front
  sidebarWindow.webContents.send('expand-sidebar'); // tell react to expand
}

// ───────────────── Toggle Overlay ─────────────────
let lastToggleTime = 0;
function toggleOverlay() {
  if (!overlayWindow) return;

  const now = Date.now();
  if (now - lastToggleTime < 500) return; // Prevent spamming/bouncing
  lastToggleTime = now;

  if (isOverlayActive) {
    overlayWindow.webContents.send('assistant-collapse-to-dot');
  } else {
    overlayWindow._setJustShown();
    if (!overlayWindow.isVisible()) {
      overlayWindow.show();
    }
    overlayWindow.focus();
    overlayWindow.webContents.send('assistant-open-panel');
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
      overlayWindow?.webContents.send('assistant-collapse-to-dot');
      return;
    }

    if (description === '__open_sidebar__') {
      overlayWindow?.webContents.send('assistant-collapse-to-dot');
      showSidebar();
      return;
    }

    console.log('[ARIA] Task:', description);

    overlayWindow?.webContents.send('assistant-collapse-to-dot');
    showSidebar();

    // Tell UI to expand sidebar if it's collapsed
    sidebarWindow?.webContents.send('expand-sidebar');
    sidebarWindow?.webContents.send('task-submitted', description);
  });

  ipcMain.on('set-sidebar-collapsed', (event, isCollapsed) => {
    if (!sidebarWindow) return;
    const { screen } = require('electron');
    const { width, height } = screen.getPrimaryDisplay().bounds;
    
    if (isCollapsed) {
      if (process.platform === 'win32') sidebarWindow.setFocusable(false);
      sidebarWindow.hide();
    } else {
      if (process.platform === 'win32') sidebarWindow.setFocusable(true);
      // Full sidebar on the right
      sidebarWindow.setBounds({
        width: 320,
        height: height,
        x: width - 320,
        y: 0
      });
      sidebarWindow.show();
    }
    // Re-enforce always-on-top so Windows doesn't push it back on resize
      sidebarWindow.setAlwaysOnTop(true, 'screen-saver');
      if (process.platform === 'darwin') {
        sidebarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
      }
  });

  ipcMain.on('window-action', (event, action) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;

    if (action === 'minimize') {
      if (win === sidebarWindow) {
        sidebarWindow.hide();   // revert back to hide to prevent offset
      } else {
        win.hide();
      }
    }

    if (action === 'close') {
    if (win === overlayWindow) {
      overlayWindow.hide();
    } else if (win === sidebarWindow) {
      sidebarWindow.hide();   // revert back
    } else {
      win.hide();
    }
  }
});

  ipcMain.on('set-overlay-active', (event, isActive) => {
    if (!overlayWindow) return;
    isOverlayActive = isActive;

    if (isActive) {
      overlayWindow.setIgnoreMouseEvents(false);
      overlayWindow.setFocusable(true);
      overlayWindow.setAlwaysOnTop(true, 'screen-saver');
      overlayWindow.show();
      overlayWindow.focus();
      return;
    }

    overlayWindow.setIgnoreMouseEvents(true, { forward: true });
    overlayWindow.setFocusable(false);
    overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    overlayWindow.showInactive();
  });

  ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (!win) return;
    win.setIgnoreMouseEvents(ignore, options);
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
  globalShortcut.register(SIDEBAR_SHORTCUT, showSidebar);

  console.log('🚀 ARIA Ready');
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (backendProcess) {
    console.log('[ARIA] Killing backend process...');
    backendProcess.kill();
  }
});
