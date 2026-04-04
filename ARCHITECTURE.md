# Newato - Development Architecture & Flow

## Project Overview
Newato is a full-stack application with a **Python backend**, **React frontend**, and **Electron desktop wrapper**. It provides AI-powered task automation with multiple LLM provider support.

---

## 📁 Directory Structure & Roles

### **Root Level Configuration**
```
├── docker-compose.yml     # Docker orchestration for services
├── Dockerfile             # Backend container configuration
├── package.json           # Root project metadata
├── README.md              # Project documentation
└── MASTER.md              # Master documentation file
```

---

## **1. Backend Layer** 🐍
**Location:** `backend/`  
**Language:** Python  
**Purpose:** Core application logic, task management, AI integration, database operations

### Core Modules

#### **`backend/core/`** - Application Core
- **`agent.py`** - AI agent orchestration logic
- **`task_manager.py`** - Task execution and lifecycle management
- **`broadcaster.py`** - Event broadcasting and real-time updates
- **`router.py`** - API routing and request handling

#### **`backend/db/`** - Database Layer
- **`database.py`** - Database connection and initialization
- **`models.py`** - Data models and schemas
- **`queries.py`** - Database query operations

#### **`backend/providers/`** - LLM Providers
AI model integration layer supporting multiple providers:
- **`anthropic_provider.py`** - Claude AI integration
- **`deepseek_provider.py`** - DeepSeek model integration
- **`groq_provider.py`** - Groq API integration
- **`base.py`** - Base provider interface
- **`registry.py`** - Provider registration and selection

#### **`backend/tools/`** - Tool Integration
Integrated tools for task execution:
- **`browser_tools.py`** - Browser automation (Selenium, Playwright, etc.)
- **`code_tools.py`** - Code execution and manipulation
- **`screen_tools.py`** - Screen capture and analysis
- **`registry.py`** - Tool registration and management

#### **`backend/utils/`** - Utilities
- **`logger.py`** - Logging configuration
- **`sanitizer.py`** - Input/output sanitization

#### **Configuration & Entry Point**
- **`main.py`** - Application entry point and server initialization
- **`config.py`** - Configuration management
- **`requirements.txt`** - Python dependencies
- **`test_runner.py`** - Test execution script

---

## **2. Frontend Layer** ⚛️
**Location:** `frontend/`  
**Framework:** React + Vite  
**Styling:** Tailwind CSS  
**Purpose:** Web UI for task creation, monitoring, and management

### Frontend Structure

#### **`frontend/src/`** - Source Code

**Pages & Components:**
- **`App.jsx`** - Main application component
- **`main.jsx`** - React entry point
- **`index.css`** - Global styles

**`components/`** - Reusable UI Components
- **`Overlay/`** - Full-page overlay component for modals/dialogs
- **`Sidebar/`** - Main navigation sidebar
  - **`TaskCard.jsx`** - Individual task display
  - **`TaskDetail.jsx`** - Detailed task information view
- **`shared/`** - Shared utility components
  - **`ProgressBar.jsx`** - Task progress visualization
  - **`StatusBadge.jsx`** - Status indicator component

**`hooks/`** - Custom React Hooks
- **`useTasks.js`** - Task state management hook
- **`useWebSocket.js`** - WebSocket connection management

**`store/`** - State Management
- **`taskStore.js`** - Task data store (Zustand or similar)

#### **Configuration Files**
- **`vite.config.js`** - Vite build configuration
- **`tailwind.config.js`** - Tailwind CSS customization
- **`postcss.config.js`** - PostCSS configuration
- **`package.json`** - Frontend dependencies
- **`index.html`** - HTML entry point

---

## **3. Electron Desktop App** 🖥️
**Location:** `electron/`  
**Purpose:** Cross-platform desktop application wrapper using Chromium

### Files
- **`main.js`** - Electron main process (window management, IPC)
- **`preload.js`** - Secure preload script for IPC communication
- **`package.json`** - Electron app configuration and dependencies
- **`assets/`** - App icons and resources

---

## **4. Scripts & Automation** ⚙️
**Location:** `scripts/`  
**Purpose:** Development setup and testing utilities

### Files
- **`start-dev.ps1`** - PowerShell script to start development environment
- **`setup.ps1`** - Project initialization and setup script
- **`smoke_test.py`** - Basic integration tests

---

## **5. Documentation Files** 📖
- **`README.md`** - Project overview and quick start
- **`MASTER.md`** - Master documentation
- **`files.txt`** & **`files2.txt`** - File listings/notes

---

## 🔄 Development Flow

### **Architecture Overview**
```
┌─────────────────────────────────────────────────────────────┐
│                     ELECTRON DESKTOP APP                     │
│                     (Chromium Wrapper)                       │
│                        electron/                              │
└─────────────────────────────────────────────────────────────┘
                              ↕ (IPC)
┌─────────────────────────────────────────────────────────────┐
│              REACT FRONTEND (Vite + Tailwind)                │
│  frontend/ - UI Components, Hooks, State Management         │
└─────────────────────────────────────────────────────────────┘
                              ↕ (WebSocket/HTTP)
┌─────────────────────────────────────────────────────────────┐
│                   PYTHON BACKEND API                         │
│            backend/ - Core Logic & Integrations             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AI Providers (Claude, DeepSeek, Groq)               │  │
│  │ Task Management & Orchestration                     │  │
│  │ Tools (Browser, Code, Screen)                       │  │
│  │ Database Operations                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES & DATABASES                   │
│  LLM APIs, Database Server, File Storage                    │
└─────────────────────────────────────────────────────────────┘
```

### **Data Flow**

1. **User Interaction** 👤
   - User creates/modifies task in React UI (`frontend/`)
   - Electron desktop wrapper renders the interface

2. **Request Processing** 📤
   - Frontend sends request to Python backend via WebSocket/HTTP
   - Backend routes request through `core/router.py`

3. **Task Processing** ⚙️
   - Task Manager (`core/task_manager.py`) processes the task
   - AI Agent (`core/agent.py`) invokes appropriate LLM provider
   - Tools (`tools/`) execute based on task requirements

4. **Data Persistence** 💾
   - Results stored in database via `db/queries.py`
   - Models defined in `db/models.py`

5. **Real-time Updates** 🔄
   - Broadcaster (`core/broadcaster.py`) sends updates back to frontend
   - Frontend updates via WebSocket hooks (`frontend/hooks/useWebSocket.js`)
   - UI updates via React state management (`frontend/store/`)

---

## 🚀 Development Commands

- **Setup:** `scripts/setup.ps1`
- **Start Development:** `scripts/start-dev.ps1`
- **Run Tests:** `scripts/smoke_test.py`
- **Docker:** `docker-compose up` (uses `docker-compose.yml` and `Dockerfile`)

---

## 📊 Technology Stack

| Layer | Technology | Location |
|-------|-----------|----------|
| **Frontend** | React, Vite, Tailwind CSS | `frontend/` |
| **Desktop** | Electron | `electron/` |
| **Backend** | Python, Flask/FastAPI | `backend/` |
| **Database** | SQL (Likely PostgreSQL/SQLite) | `backend/db/` |
| **AI** | Multiple LLM Providers (Claude, DeepSeek, Groq) | `backend/providers/` |
| **Automation** | Browser, Code, Screen Tools | `backend/tools/` |
| **Containerization** | Docker | `docker-compose.yml` |

---

## 🔐 Key Responsibilities by Directory

| Directory | Primary Responsibility | Secondary Role |
|-----------|----------------------|-----------------|
| `backend/core/` | Task orchestration & AI logic | Event broadcasting |
| `backend/db/` | Data persistence | Schema management |
| `backend/providers/` | LLM integration | Model selection logic |
| `backend/tools/` | Task execution | External service integration |
| `backend/utils/` | Code quality | Security (sanitization) |
| `frontend/src/components/` | User interface | User experience |
| `frontend/src/hooks/` | State & side effects | API communication |
| `frontend/src/store/` | Global state | Data consistency |
| `electron/` | Desktop experience | System integration |
| `scripts/` | Development automation | Testing & setup |

---

## 💡 Development Workflow

1. **Local Development Start:**
   - Run `scripts/start-dev.ps1`
   - Starts backend API server (port 8765)
   - Starts frontend dev server (Vite, port 5173)
   - **Waits for backend health check** (/ping endpoint)
   - Starts Electron with `--dev` flag
   - Electron loads frontend from `http://localhost:5173?window=overlay`

2. **Making Changes:**
   - **Backend changes:** Edit `backend/` files, changes auto-reload via Uvicorn
   - **Frontend changes:** Edit `frontend/` files, hot-reload via Vite
   - **Electron changes:** Edit `electron/` files, requires Electron restart

3. **Testing:**
   - Run `scripts/smoke_test.py` for integration tests
   - Manual testing via desktop overlay (Ctrl+Shift+Space)

4. **Deployment:**
   - Backend packaged in Docker container (see `Dockerfile`)
   - Frontend built as static assets
   - Electron packaged as desktop application

---

## 🚨 Electron Integration Flow & Debugging

### Expected Flow
```
User launches: .\scripts\start-dev.ps1
     ↓
[Step 1] Start Python Backend (port 8765)
     ↓
[Step 2] Start React Frontend Dev Server (port 5173)
     ↓
[Step 3] Wait for /ping health check from backend
     ↓
[Step 4] Launch Electron with --dev flag
     ↓
Electron main.js checks for --dev flag → IS_DEV = true
     ↓
IS_DEV = true → Load frontend from http://localhost:5173?window=overlay
     ↓
Electron creates overlay + sidebar windows
     ↓
Overlay loads at http://localhost:5173/?window=overlay
     ↓
Sidebar loads at http://localhost:5173/?window=sidebar
     ↓
Websocket connection to ws://localhost:8765 via useWebSocket.js
     ↓
✅ READY - Press Ctrl+Shift+Space to toggle overlay
```

### Common Issues & Fixes

#### ❌ Issue: Electron fails to start
**Cause:** Missing `npm run dev` command in start-dev.ps1  
**Fix:** The script should call `& npm run dev` after setting `$env:ELECTRON_DEV = "true"`  
**Status:** ✅ FIXED in start-dev.ps1

#### ❌ Issue: Electron doesn't recognize dev mode
**Cause:** `--dev` flag not passed to Electron  
**How Electron should be called:**
```bash
npm run dev              # This runs: electron . --dev
```
**Not:**
```bash
npm start               # This runs: electron . (without --dev flag)
```
**Status:** ✅ FIXED - start-dev.ps1 now uses `npm run dev`

#### ❌ Issue: Overlay loads blank or wrong URL
**Cause:** IS_DEV is false, trying to load from production path  
**Solution:** Verify Electron is launched with `--dev` flag  
**Location check:** [electron/main.js](electron/main.js#L13)
```javascript
const IS_DEV = process.argv.includes('--dev');
const FRONTEND_URL = IS_DEV 
  ? 'http://localhost:5173' 
  : `file://${path.join(__dirname, '../frontend/dist/index.html')}`;
```

#### ❌ Issue: Backend health check failing
**Symptom:** "Backend is slow. Continuing to Electron..." message  
**Cause:** `/ping` endpoint missing from [backend/main.py](backend/main.py) or backend not starting  
**Fix:** Verify backend has `/ping` endpoint implemented  
**Location:** Check [backend/main.py](backend/main.py) for `@app.get("/ping")`

#### ❌ Issue: Websocket connection fails
**Symptom:** Overlay loads but no data flows from frontend  
**Cause:** 
  1. Backend not accessible at `ws://localhost:8765`
  2. CORS/WSGI issues
  3. WebSocket not initialized in frontend
**Check:**
  - Is backend running? `curl http://localhost:8765/ping`
  - Is frontend hook initialized? [frontend/hooks/useWebSocket.js](frontend/hooks/useWebSocket.js)
  - Is Electron preload script properly exposing APIs? [electron/preload.js](electron/preload.js)

### Electron Window Architecture

**Two Window System:**
- **Overlay Window:** Global hotkey overlay (Ctrl+Shift+Space)
- **Sidebar Window:** Main task management interface

**Window Parameters via URL Query:**
```
/?window=overlay   → Loads as floating overlay
/?window=sidebar   → Loads as sidebar
```

**Implementation in React:**
- [frontend/src/App.jsx](frontend/src/App.jsx) should detect `window` query parameter
- Render different UI based on query parameter
- Use WebSocket hook to stream data from backend

### Electron IPC (Inter-Process Communication)

**Preload Script Exposes:** [electron/preload.js](electron/preload.js)
```javascript
window.aria = {
  submitTask(description),           // Send task to backend
  windowAction(action),              // Minimize/close window
  openFile(filepath),                // Open file with default app
  getBackendStatus(),                // Check if backend is ready
  onOverlayFocus(callback),          // Listen for overlay show
  onTaskSubmitted(callback)          // Listen for new tasks
}
```

**Frontend React must use these APIs:**
- Example: `window.aria.submitTask(description)` to send data
- Example: `window.aria.onTaskSubmitted((task) => { ... })`

---

## 🔄 Data Flow During Task Execution

### From Overlay to Execution:
```
1. User types in Overlay → "Do X"
2. Overlay calls window.aria.submitTask("Do X")
3. React component sends to backend via WebSocket
4. Backend router processes request → core/router.py
5. Task Manager orchestrates → core/task_manager.py
6. AI Agent calls LLM provider → core/agent.py + providers/*
7. Tools execute if needed → tools/*
8. Result stored in database → db/queries.py
9. Broadcaster sends update → core/broadcaster.py (WebSocket)
10. Frontend receives update via useWebSocket hook
11. UI re-renders with new task status
12. Sidebar shows updated task
```

---

## 🔗 Integration Points

- **Frontend ↔ Backend:** WebSocket (real-time) / HTTP REST API
- **Electron ↔ Frontend:** IPC (Inter-Process Communication) for system calls
- **Backend ↔ External APIs:** LLM providers, tool executors
- **Backend ↔ Database:** ORM/SQL queries via `db/` module

---

## 📝 Notes

- Multiple LLM provider support allows flexibility in model selection
- Tool registry pattern allows easy extension of automation capabilities
- Broadcaster pattern ensures real-time UI updates
- Docker containerization enables consistent deployment
