# NEWATO / ARIA — Complete Project Documentation

> **Repo:** [github.com/maheshh-v/Newato](https://github.com/maheshh-v/Newato)
> **Last Synced:** April 2026
> **Build Phase:** Phase 1 — Foundation Complete → Prototype Validation Active

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [The Big Picture — Vision](#2-the-big-picture--vision)
3. [How It Works — Full Architecture](#3-how-it-works--full-architecture)
4. [The ReAct Brain — Deep Dive](#4-the-react-brain--deep-dive)
5. [Every File Explained](#5-every-file-explained)
6. [Complete File Tree](#6-complete-file-tree)
7. [What Is Built Right Now](#7-what-is-built-right-now)
8. [What Is In Progress](#8-what-is-in-progress)
9. [The Full Journey — Step by Step](#9-the-full-journey--step-by-step)
10. [Roadmap — What Comes Next](#10-roadmap--what-comes-next)
11. [Edge Cases & How They're Handled](#11-edge-cases--how-theyre-handled)
12. [Environment Variables — Full Reference](#12-environment-variables--full-reference)
13. [How to Run the Project](#13-how-to-run-the-project)
14. [The Demo Script](#14-the-demo-script)
15. [Architectural Decisions Log](#15-architectural-decisions-log)
16. [Team Ownership Map](#16-team-ownership-map)
17. [Tech Stack](#17-tech-stack)

---

## 1. What Is This?

**ARIA** (Autonomous Reasoning & Intelligence Agent) is a **local AI agent desktop application**.

It lives in your system tray. You summon it with a keyboard shortcut (`Ctrl+Shift+Space`) from anywhere on your computer — any app, any window. An overlay pops up. You type a task in plain English. You press Enter. It disappears. The AI takes over.

A sidebar slides in showing the agent thinking and working in real time — navigating websites, extracting data, running code, writing files — step by step, all autonomous. When it's done, a green card appears with a link to the output file. You never left what you were doing.

**The core difference from ChatGPT or Copilot:** Those tools are passive. They answer questions and wait. ARIA is active — it executes, browses, creates, and delivers completed work. It's not a conversation tool. It's a delegation tool.

### What A User Actually Experiences

```
[User is working in VS Code]

   → Presses Ctrl+Shift+Space

[Sleek overlay slides in from center of screen]

   → Types: "Go to news.ycombinator.com, get top 5 story titles, 
             save them to hn_top.json"
   
   → Presses Enter

[Overlay disappears. User goes back to VS Code.]

[Sidebar slides in from the right, subtle]

   ARIA Working...
   ├── Step 1: Navigating to news.ycombinator.com
   ├── Step 2: Waiting for page to load...
   ├── Step 3: Extracting story titles from .storylink elements
   ├── Step 4: Found 5 titles. Formatting as JSON array.
   └── Step 5: Writing to ~/ARIA/outputs/hn_top.json

   ✅ DONE — hn_top.json  [click to open]

[User never switched windows. Never prompted again. Task: complete.]
```

---

## 2. The Big Picture — Vision
## 5. FULL FILE STRUCTURE WITH EXPLANATIONS
- **`MASTER.md`**: The single source of truth for the project, tracking vision, architecture, and task status.
- **`README.md`**: Standard brief overview for git repositories.
- **`.env`** / **`.env.example`**: Configuration variables, including API keys and ports.
- **`.gitignore`**: Excludes `node_modules`, `venv`, compiled files, and secrets from version control.
- **`backend/main.py`**: The FastAPI entry point containing REST endpoints and the WebSocket server for real-time updates.
- **`backend/config.py`**: Loads environment variables and provides typed, validated settings for the backend.
- **`backend/requirements.txt`**: Specifies Python dependencies (FastAPI, uvicorn, playwright, anthropic, etc).
- **`backend/core/agent.py`**: The core ReAct loop that makes Claude think, use tools, and observe results iteratively.
- **`backend/core/broadcaster.py`**: Manages active WebSocket connections and broadcasts real-time task updates to the UI.
- **`backend/core/router.py`**: Uses heuristics to classify raw user task descriptions (e.g., "web", "code", "api") for optimized routing.
- **`backend/core/task_manager.py`**: Orchestrates concurrency with an asyncio semaphore to limit running tasks.
- **`backend/db/database.py`**: Initializes the SQLite database and provides connection contexts.
- **`backend/db/models.py`**: Pydantic/dataclass definitions representing Tasks and execution Steps.
- **`backend/db/queries.py`**: Encapsulates all SQL statements for inserting and retrieving tasks and steps.
- **`backend/tools/__init__.py`**: Tool package initializer.
- **`backend/tools/registry.py`**: The central registry defining the JSON schema for every tool available to the LLM.
- **`backend/tools/browser_tools.py`**: Implements Playwright functions for web navigation, clicking, typing, and extraction.
- **`backend/tools/code_tools.py`**: Safety-restricted functions for executing Python code strings and writing files.
- **`backend/tools/screen_tools.py`**: Desktop interaction tools for screenshots, visible browser launch, and real mouse/keyboard control.
- **`backend/utils/logger.py`**: Custom structured logging configuration for the backend.
- **`backend/utils/sanitizer.py`**: Utilities to truncate large string outputs (like huge HTML blobs) before saving/sending.
- **`electron/main.js`**: The main Node process managing Electron windows, system tray, global shortcuts, and launching Python.
- **`electron/preload.js`**: Context bridge allowing secure IPC communication between the React frontend and Electron main process.
- **`electron/package.json`**: NPM configuration, scripts, and dependencies for the Electron shell.
- **`frontend/package.json`**: NPM configuration, scripts, and React/Tailwind/Vite dependencies for the frontend.
- **`frontend/vite.config.js`**: Configuration for the Vite bundler.
- **`frontend/tailwind.config.js`**: Tailwind CSS theme and styling configuration.
- **`frontend/postcss.config.js`**: PostCSS plugins configuration used by Tailwind.
- **`frontend/index.html`**: The root HTML file serving the React application.
- **`frontend/src/main.jsx`**: The React DOM mounting script.
- **`frontend/src/App.jsx`**: The root React component that routes between the Overlay and Sidebar window modes.
- **`frontend/src/index.css`**: Global CSS imports and base Tailwind directives.
- **`frontend/src/store/taskStore.js`**: Zustand store managing local state for tasks, steps, and UI visibility.
- **`frontend/src/hooks/useTasks.js`**: React hook for querying and manipulating tasks.
- **`frontend/src/hooks/useWebSocket.js`**: React hook that connects to the backend WebSocket and hydrates the Redux/Zustand store.
- **`frontend/src/components/Overlay/Overlay.jsx`**: The search-bar-like command input UI that appears globally.
- **`frontend/src/components/Overlay/Overlay.css`**: Animations and specific styles for the overlay.
- **`frontend/src/components/Sidebar/Sidebar.jsx`**: The sliding right-hand panel displaying all active and complete tasks.
- **`frontend/src/components/Sidebar/Sidebar.css`**: Animations and styling for the sidebar.
- **`frontend/src/components/Sidebar/TaskCard.jsx`**: A summary card for a distinct task in the sidebar list.
- **`frontend/src/components/Sidebar/TaskDetail.jsx`**: A detailed view showing every internal thought and step of a specific task.
- **`frontend/src/components/shared/ProgressBar.jsx`**: Reusable component for displaying task execution progress.
- **`frontend/src/components/shared/StatusBadge.jsx`**: UI element indicating if a task is running, complete, or failed.
- **`scripts/setup.ps1`**: Automated script to create Python venv, install Python/Node deps, and setup Playwright.
- **`scripts/smoke_test.py`**: Basic automated tests to verify core logic without UI overhead.
- **`scripts/start-dev.ps1`**: Development script firing up FastAPI, Vite, and Electron simultaneously locally.

ARIA is being built in phases. Here is the complete vision:

### Phase 1 — Local AI Worker (Current)
A desktop app that runs AI agents locally, takes natural language tasks, executes them using web browsing and code execution, and returns real files and results. Runs on one machine. Uses Claude or Groq APIs.
## 7. WHAT IS IN PROGRESS
- [ ~ ] End-to-End Task Validation
  - Core logic and UI exist and function up until LLM execution.
  - Missing: Needs a valid `ANTHROPIC_API_KEY` to actually ping Claude and verify tool usage accuracy.
  - Exact file to open and what to add: Open `.env` and add a valid api key for `ANTHROPIC_API_KEY`.
- [ ~ ] Tool Isolation Testing
  - `scripts/tools_test.py` created; run to verify all tools print PASS.
- [ ~ ] Live Desktop Control
  - Screen tools now include visible browser launch plus mouse/keyboard automation for tasks that explicitly ask for Chrome or live cursor movement.
  - Added task-specific tool filtering in the agent loop to reduce Groq token usage for live desktop tasks.
  - Sidebar renderer now uses safer task normalization and an error boundary to avoid full white-screen crashes from malformed payloads or oversized screenshots.
  - Missing: end-to-end validation of a real live desktop task through the overlay.
- [ ~ ] OpenRouter Fallback
  - Backend now supports `LLM_PROVIDER=openrouter` with OpenRouter chat completions for tool-calling tasks.
  - Missing: real API-key validation in the local environment.

### Phase 2 — Offline + Free AI
Full **Ollama integration** — AI runs entirely on your GPU/CPU. Zero API cost. Zero data leaving the machine. Switch between Claude, Groq, and local models from a settings panel.

### Phase 3 — Skill Marketplace
A plugin system where developers drop `.py` files into a `/plugins` folder and the agent gains new abilities — Slack posting, Notion updates, Gmail sending, AWS management, etc. Users can download published skills without writing code.

### Phase 4 — Multi-Step Chained Workflows
Agent A outputs a file → Agent B reads it and writes a report → Agent C sends the report by email. Full dependency chains in plain language: "Research competitors → write comparison → email to boss."

### Phase 5 — Vision and Screen Control
The agent can see the screen (screenshot + LLM), move the mouse, click buttons, type in any app — including apps with no API. Full computer-use capability.

### Phase 6 — Enterprise & Teams
Shared agent memory across a team. Role-based task routing. Organizational deployment. Audit logs for every agent action.

### Phase 7 — Cross-Platform Native Installers
Clean `.exe` (Windows NSIS), `.dmg` (macOS), and `.AppImage` (Linux) — download and double-click, no terminal needed.
### TASK: Configure Anthropic API Key & Verify Agent Loop
Priority: High
Depends on: None
Estimated complexity: Small
Files to create or edit: `.env`, `backend/core/agent.py` (if tweaking needed)
What to build: Inject a valid `ANTHROPIC_API_KEY` into `.env`, submit a real test command (e.g. "Go to example.com and extract header"), and observe the ReAct loop handle it perfectly.
Definition of done: The agent successfully completes a web browsing task autonomously, extracts knowledge, and outputs a file or summary.

### TASK: Local LLM (Ollama) Support
Priority: Medium
Depends on: Configure Anthropic API Key & Verify Agent Loop
Estimated complexity: Large
Files to create or edit: `backend/core/agent.py`, `backend/config.py`
What to build: Modify the agent loop to add an alternative client utilizing the `ollama` Python library, allowing execution entirely locally on hardware instead of relying on Claude. Ensure tool definitions are compatible with open weights models.
Definition of done: User can select a local model via config to execute a simple task completely offline.

### TASK: Skill / Plugin Marketplace Architecture
Priority: Medium
Depends on: Configure Anthropic API Key & Verify Agent Loop
Estimated complexity: Large
Files to create or edit: `backend/tools/dynamic_loader.py`, `backend/models/plugin.py`
What to build: Create a system for dynamically loading python files as "skills" that extend the `TOOL_REGISTRY`. Allow the Frontend to display available skills.
Definition of done: A user can drop a `.py` skill file into a plugins folder, restart, and the agent can suddenly use a new external service tool without hardcoded changes.

### TASK: Scheduled / Recurring Tasks
Priority: Low
Depends on: End-to-End Validation
Estimated complexity: Medium
Files to create or edit: `backend/core/scheduler.py`, DB schema updates
What to build: Add a cron-like scheduler loop that periodically reads the DB for recurring tasks and submits them to the `task_manager` queue.
Definition of done: User can define a task to "Run every hour", and ARIA logs the execution automatically.

## TEAM OWNERSHIP

| Module | Owner | Files Owned |
|--------|-------|-------------|
| Agent Core & LLM Loop | Backend Dev 1 | backend/core/agent.py, backend/core/router.py, backend/core/task_manager.py |
| Tools & Browser Automation | Backend Dev 2 | backend/tools/*, backend/core/broadcaster.py |
| Frontend & Electron UI | Frontend Dev | frontend/src/*, electron/main.js, electron/preload.js |
| Infrastructure & Testing | Generalist | backend/db/*, backend/utils/*, scripts/*, MASTER.md |
| Architecture & Integration | Lead | All files — review only, no direct module ownership |

Rules:
- You make all decisions inside your module
- You ask Lead before changing anything outside your module
- You update MASTER.md every time you complete or start something

## 9. THE DEMO SCRIPT
1. Ensure the machine is fresh and `scripts/setup.ps1` has been run.
2. Provide a valid `.env` with `ANTHROPIC_API_KEY`.
3. Run `.\scripts\start-dev.ps1`. Wait for "App ready. Press Control+Shift+Space" in terminal.
4. Press `Ctrl+Shift+Space` (or Cmd+Shift+Space on Mac). Verify the sleek Overlay appears centered on screen.
5. Search bar: type "Go to hacker news, get the top 3 stories, and save them to a file named hn_top.json" and press Enter.
6. Verify the Overlay vanishes immediately.
7. Verify the Sidebar slides in from the right. A new task appears labeled "running".
8. In the sidebar, click the task to expand steps.
9. Watch as steps populate in real-time: "Navigating to ...", "Extracting ...", "Writing file ...".
10. Wait ~15 seconds. Verify the task state updates to "Complete".
11. Right click system tray -> "Open Output Folder".
12. Verify `hn_top.json` exists locally containing accurate data.

## 10. HOW TO RUN THE PROJECT
1. Fresh Machine Setup: Open a PowerShell terminal as Administrator (or standard user with execution bypass rights).
2. Navigate to project root: `cd \path\to\ARIA` (or `Newato` in this environment)
3. Run the setup: `.\scripts\setup.ps1` (This creates the Python venv, installs NPM packages, installs Playwright browsers, and creates a `.env` file).
4. Configuration: Open `.env` and paste your valid `ANTHROPIC_API_KEY`.
5. Start Dev Server: Run `.\scripts\start-dev.ps1`. This spins up the FastAPI backend, the Vite frontend dev server, and launches Electron.
6. The app minimizes to the system tray. Use `Ctrl+Shift+Space` to summon the agent.

## 11. ENVIRONMENT VARIABLES
- `ANTHROPIC_API_KEY` (Required): The API key for Claude. Tasks fail fast with 401 if missing or invalid.
- `ARIA_OUTPUT_DIR` (Optional): Where agents write physical files. Default: `~/ARIA/outputs`.
- `ARIA_MAX_CONCURRENT_TASKS` (Optional): Limits simultaneous parallel task execution. Default: `4`.
- `ARIA_WEBSOCKET_PORT` (Optional): Port for IPC. Default: `8765`.
- `ARIA_MAX_STEPS_PER_TASK` (Optional): Hard limit on agent loop steps. Default: `40`.
- `ARIA_TASK_TIMEOUT_SECONDS` (Optional): Wall-clock guardrail. Default: `300`.
- `LOG_LEVEL` (Optional): Logging verbosity. Default: `INFO`.

## 12. KNOWN ISSUES AND BLOCKERS
No current blockers.

## 13. DECISIONS LOG
- **LLM Provider:** `LLM_PROVIDER=groq` is now the default provider. It's free and incurs no cost, utilizing Groq's high-speed LLaMA 3.3 model. Anthropic Claude remains supported via configuration.
- **Visible Browser Tasks:** Requests that explicitly mention Chrome, live browsing, or cursor movement now prefer headed browser or desktop-control tools instead of only hidden Playwright automation.
- **OpenRouter Support:** Added OpenRouter as an OpenAI-compatible fallback provider so ARIA can switch away from Groq when Groq quota is exhausted.
- **Electron over Native (Swift/C++):** Decided heavily in favor of Electron for rapid, cross-platform iteration and because standard web tech combined with Python covers all required capability.
- **Python over Node for Backend:** Python chosen for backend despite Electron using Node due to Python's undeniably superior ecosystem for data extraction (Playwright), AI engineering (LangChain/Anthropic SDK), and numerical reasoning.
- **SQLite Database:** Decided against PostgreSQL to ensure the app is a 100% self-contained local desktop application with zero external infrastructure dependencies.
- **WebSocket IPC rather than normal Electron IPCMain:** Keeps the python backend entirely decoupled from Electron. The backend could theoretically be hosted on a separate server without code changes.

## 14. TEAM WORKING RULES
- Always read MASTER.md before starting any work
- Always update MASTER.md before ending any session
- Never mark a task complete unless it runs
- Every new file created must be added to the file structure section with its explanation
- Every architectural decision must be logged in the Decisions Log

---

## 3. How It Works — Full Architecture

ARIA is three decoupled systems that talk to each other:

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER'S MACHINE                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  ELECTRON SHELL (Node.js)                 │   │
│  │                                                           │   │
│  │  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │   │
│  │  │  System     │   │  Overlay     │   │  Sidebar     │  │   │
│  │  │  Tray       │   │  Window      │   │  Window      │  │   │
│  │  │             │   │  (React UI)  │   │  (React UI)  │  │   │
│  │  └─────────────┘   └──────┬───────┘   └──────┬───────┘  │   │
│  │                           │                   │           │   │
│  │              Global Shortcut: Ctrl+Shift+Space│           │   │
│  │              Spawns Python backend on startup │           │   │
│  └───────────────────────────┼───────────────────┼───────────┘   │
│                              │ REST API + WebSocket               │
│                              ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 PYTHON BACKEND (FastAPI)                   │   │
│  │                                                           │   │
│  │  ┌────────────────┐    ┌──────────────────────────────┐  │   │
│  │  │  REST Endpoints │    │  WebSocket Broadcaster       │  │   │
│  │  │  POST /tasks   │    │  Pushes live step updates    │  │   │
│  │  │  GET /tasks    │    │  to frontend in real time    │  │   │
│  │  └───────┬────────┘    └──────────────────────────────┘  │   │
│  │          │                                                │   │
│  │          ▼                                                │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │              REACT AGENT CORE                     │    │   │
│  │  │                                                   │    │   │
│  │  │  THINK → DECIDE TOOL → EXECUTE → OBSERVE → REPEAT│    │   │
│  │  │                                                   │    │   │
│  │  │  ┌──────────────┐   ┌──────────────────────────┐ │    │   │
│  │  │  │  Claude API  │   │  Tool Registry            │ │    │   │
│  │  │  │  or Groq API │   │  ┌─────────────────────┐ │ │    │   │
│  │  │  │  (LLM brain) │   │  │ browser_navigate    │ │ │    │   │
│  │  │  └──────────────┘   │  │ browser_extract     │ │ │    │   │
│  │  │                     │  │ browser_click       │ │ │    │   │
│  │  │                     │  │ write_file          │ │ │    │   │
│  │  │                     │  │ run_python          │ │ │    │   │
│  │  │                     │  └─────────────────────┘ │ │    │   │
│  │  │                     └──────────────────────────┘ │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │              SQLite DATABASE                       │    │   │
│  │  │  Tasks table + Steps table (local, no cloud)      │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────┐   ┌───────────────────────────────┐   │
│  │  Playwright Browser   │   │  ~/ARIA/outputs/              │   │
│  │  (headless Chromium)  │   │  All agent-created files land │   │
│  │  Runs invisibly       │   │  here. Clickable from UI.     │   │
│  └──────────────────────┘   └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow — A Single Task

```
1. User presses Ctrl+Shift+Space
        ↓
2. Electron shows Overlay window (React)
        ↓
3. User types task, presses Enter
        ↓
4. Frontend sends POST /tasks to FastAPI backend
        ↓
5. Backend creates task record in SQLite (status: queued)
        ↓
6. Task Manager picks it up (asyncio semaphore, max 4 concurrent)
        ↓
7. Agent.py starts the ReAct loop with the task description
        ↓
8. Agent sends task + tool definitions to Claude/Groq API
        ↓
9. LLM returns: thought + tool choice + tool arguments
        ↓
10. Agent executes the chosen tool (e.g. browser_navigate)
        ↓
11. Tool returns result (page HTML, extracted text, etc.)
        ↓
12. Broadcaster pushes step update via WebSocket → Frontend
        ↓
13. Frontend sidebar updates live with new step text
        ↓
14. Step saved to SQLite
        ↓
15. Agent sends updated history back to LLM → next step
        ↓
16. Loop repeats until LLM says "DONE" or timeout/max steps hit
        ↓
17. Task status updated to done/failed in SQLite
        ↓
18. Final WebSocket push → task card turns green, file link shown
```

---

## 4. The ReAct Brain — Deep Dive

The agent uses the **ReAct pattern** (Reason + Act), which is a well-established method for LLM-based agents.

### The Loop

```python
# Simplified pseudocode of backend/core/agent.py

async def run_task(task_description: str):
    history = []
    step_count = 0
    
    while step_count < MAX_STEPS:
        # THINK: Ask the LLM what to do next
        response = await llm.complete(
            system_prompt = AGENT_SYSTEM_PROMPT,
            tools = TOOL_REGISTRY,
            messages = [
                {"role": "user", "content": task_description},
                *history  # Full conversation history so far
            ]
        )
        
        # Is the LLM done?
        if response.stop_reason == "end_turn":
            await mark_task_done(task_id)
            break
        
        # ACT: Extract the tool call
        tool_name = response.tool_use.name
        tool_args = response.tool_use.input
        
        # Execute the tool
        try:
            result = await TOOLS[tool_name](**tool_args)
        except Exception as e:
            result = f"ERROR: {str(e)}"
            # Agent sees the error and decides what to do — retry, skip, or fail
        
        # OBSERVE: Log what happened
        step = {"tool": tool_name, "args": tool_args, "result": result}
        history.append(step)
        await save_step(task_id, step)
        await broadcast_step(task_id, step)  # → Frontend sidebar updates
        
        step_count += 1
    
    else:
        # Hit MAX_STEPS without finishing — timeout
        await mark_task_failed(task_id, "Max steps exceeded")
```

### Why This Pattern Works

The LLM never executes code directly. Instead:
- It **reasons** about what to do next (in natural language)
- It **chooses** from a defined set of tools (the registry)
- The Python backend **executes** the tool safely
- The LLM **sees** the result and decides the next step

This separation means:
- The LLM can't do anything not in the tool registry
- Each tool can have its own safety constraints
- Errors are observable and the LLM can reason about recovery

### Task Router

Before the ReAct loop starts, `backend/core/router.py` classifies the task:

| Classification | Example Input | Optimized For |
|----------------|--------------|---------------|
| `web` | "go to google.com and..." | Browser tools first |
| `code` | "write a python script that..." | run_python tool first |
| `file` | "create a file with..." | write_file tool first |
| `api` | "fetch data from the API..." | run_python with requests |
| `general` | anything else | All tools equally |

This lets the agent start with the right tool context instead of fumbling.

### Task Manager & Concurrency

`backend/core/task_manager.py` uses an `asyncio.Semaphore` set to `ARIA_MAX_CONCURRENT_TASKS` (default 4):

```python
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def run_with_limit(task):
    async with semaphore:
        await agent.run_task(task)
```

This means:
- Submit 10 tasks at once → first 4 start immediately, rest queue
- One task finishing frees a slot → next queued task starts automatically
- No task can block or crash another (each runs in isolated async context)

---

## 5. Every File Explained

### Root Level

| File | Purpose |
|------|---------|
| `MASTER.md` | Single source of truth. Architecture, decisions, task status. Read before every session. |
| `README.md` | Brief project overview for GitHub visitors |
| `.env.example` | Template showing all required/optional env vars with descriptions |
| `.gitignore` | Excludes `node_modules/`, `venv/`, `*.env`, `outputs/`, compiled files |
| `files.txt` | Full list of all project files (reference/documentation use) |
| `files2.txt` | Extended file manifest with additional context |

### `electron/`

| File | Purpose |
|------|---------|
| `main.js` | Main Electron process. Registers `Ctrl+Shift+Space` global shortcut. Creates two frameless browser windows (overlay + sidebar). Creates system tray icon with context menu. Spawns Python FastAPI backend as a child process on app start. Kills Python on app close. |
| `preload.js` | Runs in the renderer process with Node access. Exposes safe IPC methods to the React app via `contextBridge.exposeInMainWorld`. Keeps the frontend sandboxed — it can only call what preload explicitly allows. |
| `package.json` | Electron app config, npm scripts (`start`, `build`), and dependencies (`electron`, `electron-builder`). |

### `frontend/`

| File | Purpose |
|------|---------|
| `src/main.jsx` | React entry point. Mounts `<App />` to DOM. |
| `src/App.jsx` | Root component. Checks which window mode it's in (overlay vs sidebar) and renders the right component. |
| `src/index.css` | Global CSS. Tailwind directives. Base resets. |
| `src/components/Overlay/Overlay.jsx` | The command bar UI. A single text input centered on screen. Handles `Enter` to submit task, `Escape` to close, autofocus on open. Calls `POST /tasks` to backend. |
| `src/components/Overlay/Overlay.css` | Slide-in/fade-in animations. Glass morphism or dark styling. |
| `src/components/Sidebar/Sidebar.jsx` | The right-panel progress view. Lists all tasks. Shows live updating step text per task. Handles empty state. |
| `src/components/Sidebar/Sidebar.css` | Slide-in from right animation. Card styles. |
| `src/components/Sidebar/TaskCard.jsx` | A single task summary card. Shows: task title (truncated), status badge (queued/running/done/failed), latest step text, output file link when done. Clickable to expand. |
| `src/components/Sidebar/TaskDetail.jsx` | Expanded view of a task. Shows every single step as a log entry with timestamp and tool name. |
| `src/components/shared/ProgressBar.jsx` | Visual progress bar used inside task cards during running state. |
| `src/components/shared/StatusBadge.jsx` | Small colored badge: `⚪ queued`, `🔵 running`, `✅ done`, `🔴 failed`. |
| `src/store/taskStore.js` | Zustand global state. Holds: all tasks array, currently selected task ID, sidebar visibility flag. Actions: `addTask`, `updateTask`, `updateStep`, `setVisible`. |
| `src/hooks/useTasks.js` | React hook. Fetches initial task list from `GET /tasks` on mount. Returns tasks array and loading state. |
| `src/hooks/useWebSocket.js` | React hook. Opens WebSocket connection to `ws://localhost:8765`. Listens for events: `task_created`, `step_added`, `task_completed`, `task_failed`. Dispatches to Zustand store on each event. |
| `vite.config.js` | Vite bundler config. Sets dev server port. Configures path aliases. |
| `tailwind.config.js` | Tailwind theme config. Custom colors, fonts, animation timings if any. |
| `postcss.config.js` | PostCSS plugins. Autoprefixer + Tailwind. Required for Tailwind to work. |
| `index.html` | Root HTML shell. Single `<div id="root">` where React mounts. |
| `package.json` | Frontend npm config. Dependencies: React 18, Vite, Tailwind, Zustand. Scripts: `dev`, `build`. |

### `backend/`

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point. Defines REST routes (`POST /tasks`, `GET /tasks`, `GET /tasks/{id}`). Defines WebSocket endpoint at `/ws`. On startup: initializes DB, starts task manager queue. |
| `config.py` | Reads `.env` using `pydantic-settings`. Exports a typed `Settings` object used everywhere. Validates that required vars (API keys) are present at startup. |
| `requirements.txt` | All Python dependencies: `fastapi`, `uvicorn`, `playwright`, `anthropic`, `groq`, `aiosqlite`, `pydantic-settings`, `python-dotenv`. |

| File | Purpose |
|------|---------|
| `core/agent.py` | The ReAct loop. Manages conversation history. Calls LLM with tools. Parses tool use responses. Dispatches to tool functions. Handles retries on tool failure. Enforces step limit and timeout. Broadcasts each step. Marks task done/failed. |
| `core/broadcaster.py` | Maintains a set of active WebSocket connections. `broadcast(event_type, data)` sends JSON to all connected clients. Used by agent to push live updates. |
| `core/router.py` | Classifies task descriptions into types (`web`, `code`, `file`, `api`, `general`). Uses keyword heuristics. Output used to prime the agent with the most relevant tool context. |
| `core/task_manager.py` | asyncio semaphore-based concurrency manager. Queue of pending tasks. Picks up tasks FIFO. Limits parallel execution to `ARIA_MAX_CONCURRENT_TASKS`. |

| File | Purpose |
|------|---------|
| `db/database.py` | Async SQLite setup using `aiosqlite`. Creates tables on startup (`tasks`, `steps`). Provides `get_db()` async context manager. |
| `db/models.py` | Pydantic models / dataclasses for `Task` (id, description, status, created\_at, output\_path) and `Step` (id, task\_id, tool\_name, input, output, timestamp). |
| `db/queries.py` | All SQL as named async functions: `create_task()`, `update_task_status()`, `add_step()`, `get_task()`, `get_all_tasks()`, `get_steps_for_task()`. No raw SQL in business logic. |

| File | Purpose |
|------|---------|
| `tools/__init__.py` | Package init. Imports all tool functions for easy access. |
| `tools/registry.py` | The JSON schema that gets sent to the LLM with every prompt. Defines each tool's name, description, and input parameters. LLM reads this to know what tools are available and how to call them. |
| `tools/browser_tools.py` | Playwright-based functions. `browser_navigate(url)` opens a URL in headless Chromium and returns page HTML. `browser_extract(url, selector)` extracts text from matched elements. `browser_click(selector)` clicks an element. All functions handle timeouts and return structured error messages on failure. |
| `tools/code_tools.py` | `write_file(filename, content)` writes to `ARIA_OUTPUT_DIR`. `run_python(code_string)` executes Python in a restricted subprocess, captures stdout/stderr, returns result. Hard-coded deny list blocks dangerous operations (`import os`, `subprocess`, `shutil.rmtree`, etc.). |
| `tools/screen_tools.py` | Placeholder for future screen capture and mouse control tools. Currently empty stubs. |
| `utils/logger.py` | Configures Python's `logging` module with structured format. Log level from `LOG_LEVEL` env var. Used across all backend modules. |
| `utils/sanitizer.py` | `truncate_output(text, max_chars)` — prevents huge HTML blobs or stdout walls from overflowing the LLM's context window. Cuts at `max_chars` and appends `[TRUNCATED]`. |

### `scripts/`

| File | Purpose |
|------|---------|
| `setup.ps1` | Run once on a fresh machine. Creates Python `venv`. Installs from `requirements.txt`. Runs `playwright install chromium`. Installs npm packages in both `electron/` and `frontend/`. Creates `.env` from `.env.example` if `.env` doesn't exist. |
| `start-dev.ps1` | Starts all three processes in parallel: `uvicorn` (Python backend), `vite` (React dev server), `electron` (desktop shell). All logs printed to one terminal with color-coded prefixes. |
| `smoke_test.py` | Basic validation script. Imports tools and calls them with hardcoded inputs without going through LLM. Prints PASS/FAIL per test. |

---

## 6. Complete File Tree

```
Newato/
│
├── MASTER.md                          ← Architecture + task board (READ THIS FIRST)
├── README.md                          ← GitHub overview
├── .env.example                       ← Env var template
├── .gitignore
├── files.txt                          ← Full file manifest
├── files2.txt                         ← Extended file manifest
│
├── electron/
│   ├── main.js                        ← OS shell, tray, shortcut, window mgmt
│   ├── preload.js                     ← Secure IPC bridge
│   └── package.json
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx                   ← React entry
│       ├── App.jsx                    ← Root, routes overlay/sidebar
│       ├── index.css
│       ├── store/
│       │   └── taskStore.js           ← Zustand global state
│       ├── hooks/
│       │   ├── useTasks.js            ← Fetch tasks from REST
│       │   └── useWebSocket.js        ← WebSocket live updates
│       └── components/
│           ├── Overlay/
│           │   ├── Overlay.jsx        ← Command bar input
│           │   └── Overlay.css
│           ├── Sidebar/
│           │   ├── Sidebar.jsx        ← Task list panel
│           │   ├── Sidebar.css
│           │   ├── TaskCard.jsx       ← Single task summary card
│           │   └── TaskDetail.jsx     ← Expanded step log view
│           └── shared/
│               ├── ProgressBar.jsx
│               └── StatusBadge.jsx
│
├── backend/
│   ├── main.py                        ← FastAPI app, REST + WS endpoints
│   ├── config.py                      ← Env var loader (pydantic-settings)
│   ├── requirements.txt
│   ├── core/
│   │   ├── agent.py                   ← THE BRAIN — ReAct loop
│   │   ├── broadcaster.py             ← WebSocket push to frontend
│   │   ├── router.py                  ← Task classifier
│   │   └── task_manager.py            ← Concurrency control
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py                ← Tool schemas sent to LLM
│   │   ├── browser_tools.py           ← Playwright: navigate/extract/click
│   │   ├── code_tools.py              ← write_file, run_python
│   │   └── screen_tools.py            ← Placeholder: future screen control
│   ├── db/
│   │   ├── database.py                ← SQLite init, connection context
│   │   ├── models.py                  ← Task & Step data models
│   │   └── queries.py                 ← All SQL operations
│   └── utils/
│       ├── logger.py                  ← Structured logging setup
│       └── sanitizer.py               ← Output truncation utility
│
├── scripts/
│   ├── setup.ps1                      ← First-time machine setup
│   ├── start-dev.ps1                  ← Start all 3 processes
│   └── smoke_test.py                  ← Tool validation tests
│
└── outputs/                           ← All agent-created files land here
    └── (gitignored)
```

---

## 7. What Is Built Right Now

These are complete and verified to exist (structure is confirmed):

| Component | Status | Verified How |
|-----------|--------|-------------|
| Electron shell — global shortcut, tray, two windows | ✅ Complete | Run start-dev.ps1, tray icon appears |
| React Overlay component | ✅ Complete | UI renders on shortcut press |
| React Sidebar + TaskCard + TaskDetail | ✅ Complete | Visual render confirmed |
| Zustand task store | ✅ Complete | State management wired up |
| WebSocket hooks | ✅ Complete | Connects to backend, receives events |
| FastAPI server — REST + WebSocket endpoints | ✅ Complete | Server starts, endpoints respond |
| SQLite database + all queries | ✅ Complete | Tasks persist across restarts |
| ReAct agent loop (code logic) | ✅ Complete | Syntactically correct, logically sound |
| Tool registry (Claude-compatible schemas) | ✅ Complete | Matches Anthropic tool\_use format |
| Playwright browser tools | ✅ Complete | navigate/extract/click implemented |
| write_file + run_python tools | ✅ Complete | With safety restrictions |
| WebSocket broadcaster | ✅ Complete | Pushes events to all connected clients |
| Task router (classifier) | ✅ Complete | Keyword-based classification |
| Task manager (concurrency) | ✅ Complete | asyncio semaphore wired |
| Dev scripts (setup + start) | ✅ Complete | One-command setup and start |
| .env.example | ✅ Complete | All vars documented |

**The one thing needed to make it live:** A valid `ANTHROPIC_API_KEY` or `GROQ_API_KEY` in `.env`. The entire codebase is wired — it just needs an API key to actually call the LLM.

---

## 8. What Is In Progress

### End-to-End Validation (CRITICAL — Do First)

```
Status: Not Started
Owner: Backend Dev 1
Blocker: Need real API key in .env
```

The acceptance test:
1. Add `GROQ_API_KEY` to `.env`
2. Run `.\scripts\start-dev.ps1`
3. Press `Ctrl+Shift+Space`
4. Type: `"Go to news.ycombinator.com, get the top 5 story titles, save them to hn_test.json"`
5. Watch terminal. Fix every error until:
   - `~/ARIA/outputs/hn_test.json` exists with 5 real titles
   - Task card shows green
   - Zero terminal errors

### Tool Isolation Testing (CRITICAL — Run In Parallel)

```
Status: Not Started
Owner: Backend Dev 2
File to create: scripts/tools_test.py
```

Each tool tested independently with hardcoded input:

| Tool | Input | Expected |
|------|-------|----------|
| `browser_navigate` | `"https://google.com"` | Page title contains "Google" → PASS |
| `browser_extract` | `"https://example.com"`, `"h1"` | Returns "Example Domain" → PASS |
| `write_file` | `"test.txt"`, `"hello"` | File exists on disk → PASS |
| `run_python` | `"print(2+2)"` | Output is "4" → PASS |

---

## 9. The Full Journey — Step by Step

This is the complete journey from first day to shipped product.

### Step 1 — Validate Core Loop ✅ (complete soon)
```
Add API key → submit real task → agent completes it → file exists on disk
```
This proves the entire system works end to end. Nothing else matters until this works.

### Step 2 — Validate All Tools ✅ (complete soon)
```
scripts/smoke_test.py → every tool prints PASS
```
Ensures no tool silently fails when the LLM tries to use it.

### Step 3 — UI Quality Audit
```
Manually check all 6 task card states look production-quality
Fix any broken/ugly state
```
The standard: if an investor saw this right now, would it look like a real shipped product?

The 6 states to verify:
- Empty sidebar (no tasks yet)
- Task queued (submitted but not running)
- Task running (live step text updating in real time)
- Task done (green, output file link visible)
- Task failed (red, failure reason shown)
- Expanded task (full step-by-step log)

### Step 4 — Parallel Demo
```
Submit 3 tasks simultaneously → all 3 show as "running" at same time → all 3 complete with separate files
```
This is ARIA's biggest differentiator. Must work visually and correctly.

### Step 5 — Polish to Linear/Raycast Standard
```
Open Linear app side by side with ARIA
Every card, animation, color, spacing must feel equally premium
```
Specific things to audit: transition animations, typography hierarchy, color contrast, spacing consistency.

### Step 6 — README Update + Prototype Demo
```
README with real screenshots → record 60-second demo video → prototype complete
```
"Done" = demo runs perfectly 3 times in a row without any errors.

---

After prototype is complete, the roadmap begins:

### Step 7 — Groq as Default (Free Mode)
```
GROQ_API_KEY = default LLM provider
No cost per task during development
Claude remains available via config
```

### Step 8 — Ollama Integration
```
Files: backend/core/agent.py, backend/config.py
New config option: LLM_PROVIDER=ollama
AI runs entirely offline, on local GPU/CPU
Zero cost, zero data leaving machine
```
Implementation: Add an `ollama` Python client branch in `agent.py`. Detect `LLM_PROVIDER` from config. Route LLM calls to either `anthropic`, `groq`, or `ollama` client accordingly.

### Step 9 — Settings Panel
```
In-app UI to configure:
  - API key (Anthropic / Groq / Ollama endpoint)
  - LLM model selection
  - Max concurrent tasks
  - Output folder path
  - Hotkey customization
```

### Step 10 — Task History Viewer
```
New screen: see every task ever run
- Task description
- All steps with timestamps
- Files created (clickable)
- Duration
- Outcome (done/failed)
- Retry button on failed tasks
```

### Step 11 — Pre-Built Templates
```
Built-in task library. One click + fill in variable + run.
Examples:
  - "Research [company name] and save a brief profile to [filename]"
  - "Extract all email addresses from [url]"
  - "Create an HTML landing page for [product name]"
  - "Summarize the main points from [url] to [filename]"
  - "Generate a cold email for [prospect] about [product]"
```

### Step 12 — Plugin System
```
Files to create: backend/tools/dynamic_loader.py, backend/models/plugin.py
Drop any .py file into /plugins folder
Restart ARIA → agent can use the new tool
Community can publish skills (Slack, Gmail, Notion, AWS...)
```
Implementation: On startup, scan `/plugins` directory. For each `.py` file, import it, validate it exports `TOOL_DEFINITION` (schema) and `execute()` (function). Add to `TOOL_REGISTRY` dynamically.

### Step 13 — Scheduled Tasks
```
Files to create: backend/core/scheduler.py + DB schema update
New task field: recurrence (cron expression or plain English)
Scheduler loop runs every minute, checks DB for due tasks
Submits them to task_manager queue automatically
```

### Step 14 — Workflow Chains
```
Chain tasks: output of task A → input of task B → input of task C
Example chain:
  Task 1: "Research top 5 AI startups → save to startups.json"
  Task 2: "Read startups.json → write comparison report → report.md"
  Task 3: "Read report.md → send email to boss@company.com"
Trigger all 3 with one command. Full autopilot.
```

### Step 15 — Vision & Screen Control
```
Files: backend/tools/screen_tools.py (currently placeholder)
Screenshot the screen → send to LLM → LLM instructs mouse/keyboard actions
Works on ANY app including ones with no API
Full computer-use capability
```

### Step 16 — Installers
```
Windows: electron-builder → NSIS .exe installer
macOS: electron-builder → .dmg
Linux: electron-builder → .AppImage
User experience: download → double-click → ARIA runs
No terminal. No scripts. Just works.
```

---

## 10. Roadmap — What Comes Next

| Priority | Feature | Complexity | Depends On |
|----------|---------|------------|-----------|
| 🔴 CRITICAL | End-to-end validation | Small | API key |
| 🔴 CRITICAL | Tool isolation tests | Small | Nothing |
| 🔴 High | UI state audit | Small | Nothing |
| 🔴 High | Parallel demo | Small | E2E validation |
| 🟠 High | Ollama offline AI | Large | E2E validation |
| 🟠 High | Settings panel | Medium | E2E validation |
| 🟠 High | Task history viewer | Medium | E2E validation |
| 🟠 Medium | Pre-built templates | Medium | Settings panel |
| 🟠 Medium | Windows + Mac installers | Medium | UI polish done |
| 🟡 Medium | Plugin system | Large | E2E validation |
| 🟡 Low | Scheduled tasks | Medium | E2E validation |
| 🟡 Low | Workflow chains | Large | Plugin system |
| 🟡 Low | Vision / screen control | Very Large | Workflow chains |
| 🟡 Low | Enterprise & teams | Very Large | Everything else |

---

## 11. Edge Cases & How They're Handled

### Agent Goes Infinite Loop
**Problem:** LLM keeps choosing tools without finishing.
**Solution:** `ARIA_MAX_STEPS_PER_TASK` (default 40) — hard cap on loop iterations. If exceeded, task is marked `failed` with reason "Max steps exceeded."

### Task Takes Too Long
**Problem:** Browser hangs, slow website, LLM latency spikes.
**Solution:** `ARIA_TASK_TIMEOUT_SECONDS` (default 300 = 5 min) — wall-clock timeout. Cancels the entire task and marks it failed.

### Tool Throws an Exception
**Problem:** Playwright crashes, page doesn't load, selector finds nothing.
**Solution:** Every tool is wrapped in try/catch. Returns structured error string: `"ERROR: [tool_name] failed — [reason]"`. LLM sees this as an observation and can decide to retry, use a different approach, or give up.

### LLM Returns Malformed Tool Call
**Problem:** LLM response doesn't match expected schema.
**Solution:** `agent.py` validates the tool call against `TOOL_REGISTRY`. If validation fails, logs the error, broadcasts it as a failed step, marks task failed.

### Frontend Disconnects Mid-Task
**Problem:** User closes the sidebar or window crashes during a running task.
**Solution:** Task continues running in Python backend regardless. Steps are saved to SQLite. When frontend reconnects, it fetches full task history via `GET /tasks/{id}` and shows the complete step log.

### Multiple Tabs / Windows
**Problem:** Playwright opens a browser — what if user already has Chrome open?
**Solution:** Playwright runs in a separate isolated Chromium instance (headless). It never touches the user's actual browser. Completely sandboxed.

### Output File Already Exists
**Problem:** Agent tries to write `hn_test.json` but it already exists from a previous run.
**Solution:** `write_file` in `code_tools.py` overwrites by default. No silent data loss — step log shows "Wrote X bytes to [file]".

### Python Code Execution Safety
**Problem:** LLM might generate dangerous Python code (delete files, exfiltrate data).
**Solution:** `run_python` has a hardcoded deny list. Any code containing `import os`, `import subprocess`, `shutil`, `open(..., 'w')` outside of `outputs/` dir, network requests outside defined tools — is blocked and returns an error instead of executing.

### Large Page HTML Overflows LLM Context
**Problem:** `browser_extract` returns 50,000 characters of HTML that blows up the token limit.
**Solution:** `utils/sanitizer.py` `truncate_output()` caps all tool outputs at configurable max chars (default ~8000 tokens). Appends `[TRUNCATED — X chars removed]` so the LLM knows data was cut.

### API Key Missing / Invalid
**Problem:** `.env` is missing or has wrong key.
**Solution:** `config.py` validates on startup using pydantic-settings. Missing required key → server refuses to start with a clear error message: `"Missing required env var: ANTHROPIC_API_KEY"`. Invalid key → first LLM call returns 401, caught in `agent.py`, task immediately marked failed with "API key invalid".

### Task Manager Queue Overflow
**Problem:** 100 tasks submitted at once, all queue up.
**Solution:** Queue is unbounded (intentionally — tasks don't get dropped). They wait in `asyncio.Queue()`. Display in sidebar shows `⚪ queued` correctly. First `MAX_CONCURRENT_TASKS` run, rest wait their turn.

### Browser Navigation Fails (Site Down / Blocked)
**Problem:** Playwright can't reach a URL — 404, 503, bot detection, etc.
**Solution:** `browser_navigate` has a `timeout` parameter (default 30s). On failure returns: `"ERROR: Navigation failed — [HTTP status or timeout reason]"`. LLM sees this, can try alternate URL or mark it unable to complete.

---

## 12. Environment Variables — Full Reference

Create a `.env` file in the project root. Copy from `.env.example`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | If using Claude | — | API key from console.anthropic.com |
| `GROQ_API_KEY` | If using Groq | — | API key from console.groq.com (free) |
| `LLM_PROVIDER` | No | `groq` | Which LLM to use: `anthropic` or `groq` |
| `ARIA_OUTPUT_DIR` | No | `~/ARIA/outputs` | Where agent writes output files |
| `ARIA_MAX_CONCURRENT_TASKS` | No | `4` | Max tasks running at same time |
| `ARIA_WEBSOCKET_PORT` | No | `8765` | Port for WebSocket IPC |
| `ARIA_MAX_STEPS_PER_TASK` | No | `40` | Hard cap on ReAct loop iterations |
| `ARIA_TASK_TIMEOUT_SECONDS` | No | `300` | Kill task after this many seconds |
| `LOG_LEVEL` | No | `INFO` | Logging: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**Minimum `.env` to get started (free option):**
```env
GROQ_API_KEY=your_groq_key_here
LLM_PROVIDER=groq
```

---

## 13. How to Run the Project

### Prerequisites
- Windows (Mac support planned)
- Node.js 20+
- Python 3.11+
- PowerShell (comes with Windows)

### First Time Setup
```powershell
# 1. Clone the repo
git clone https://github.com/maheshh-v/Newato
cd Newato

# 2. Run setup (creates venv, installs all deps, installs Playwright)
.\scripts\setup.ps1

# 3. Configure your API key
# Open .env and add:
# GROQ_API_KEY=your_key_here
notepad .env
```

### Start Development
```powershell
.\scripts\start-dev.ps1
```

This starts all three processes:
1. **Python FastAPI** — `uvicorn main:app --port 8000`
2. **React dev server** — `vite --port 3000`
3. **Electron** — loads from `http://localhost:3000`

Terminal shows color-coded logs from all three processes simultaneously.

### Use ARIA
```
Press Ctrl+Shift+Space → type a task → press Enter → watch sidebar
```

Output files appear in `~/ARIA/outputs/` (or whatever `ARIA_OUTPUT_DIR` is set to).

---

## 14. The Demo Script

The exact steps to run the perfect demo:

```
1. Fresh machine with setup.ps1 already run
2. .env has valid API key
3. Run: .\scripts\start-dev.ps1
4. Wait for: "App ready. Press Ctrl+Shift+Space" in terminal
5. Press Ctrl+Shift+Space
   → Verify: Overlay appears centered on screen, input focused
6. Type: "Go to news.ycombinator.com, get the top 3 story titles, 
           save them to a file named hn_top.json"
7. Press Enter
   → Verify: Overlay disappears instantly
   → Verify: Sidebar slides in from the right
   → Verify: Task card appears with "running" state
8. Click the task card to expand
   → Verify: Steps populate live as agent works
   → Steps should include: "Navigating to...", "Extracting...", "Writing..."
9. Wait ~15-20 seconds
   → Verify: Task card turns green
   → Verify: File link "hn_top.json" is clickable in the card
10. Right-click system tray → "Open Output Folder"
    → Verify: hn_top.json exists with real Hacker News story titles
```

**Prototype is done when this runs perfectly 3 times in a row.**

---

## 15. Architectural Decisions Log

### Why Electron (not Swift/C++/Qt)?
Chosen for rapid cross-platform iteration. Web tech (React + Tailwind) covers all UI needs. Python handles all AI/data work. The combination reaches 95% of the capability at 20% of the development time.

### Why Python Backend (not Node)?
Python's ecosystem for AI engineering is unmatched — `anthropic`, `groq`, `playwright`, `aiosqlite`, `pydantic`. All best-in-class. Node equivalents are either inferior or nonexistent for some of these.

### Why SQLite (not PostgreSQL)?
ARIA is a 100% local desktop app. No internet dependency. No server to run. SQLite is a file on disk. `aiosqlite` makes it async-compatible. Scales fine for thousands of task records.

### Why WebSocket (not Electron IPC)?
Keeps Python backend completely decoupled from Electron. Backend could theoretically run on a remote server without code changes. Also easier to debug — any WebSocket client can connect and watch events.

### Why Groq as Default LLM?
Free tier. Fast (Llama 3.3 at ~800 tokens/second). No cost during development. Anthropic Claude remains supported via `LLM_PROVIDER=anthropic` config switch. Ollama support coming for fully offline operation.

### Why Zustand (not Redux)?
Redux is overkill for this scale. Zustand is minimal, hook-based, and requires zero boilerplate. The task store has ~5 actions. Zustand handles it in 30 lines. Redux would need 200+.

### Why Vite (not Create React App)?
CRA is deprecated. Vite has 10x faster HMR and build times. Standard choice in 2025+.

---

## 16. Team Ownership Map

| Module | Owner | Files Owned |
|--------|-------|------------|
| Agent Core & LLM Loop | Backend Dev 1 | `backend/core/agent.py`, `backend/core/router.py`, `backend/core/task_manager.py` |
| Tools & Browser Automation | Backend Dev 2 | `backend/tools/*`, `backend/core/broadcaster.py` |
| Frontend & Electron UI | Frontend Dev | `frontend/src/*`, `electron/main.js`, `electron/preload.js` |
| Infrastructure & Testing | Generalist | `backend/db/*`, `backend/utils/*`, `scripts/*`, `MASTER.md` |
| Architecture & Integration | Lead | All files — review only, no direct module ownership |

**Rules:**
- You make all decisions inside your module
- Ask Lead before changing anything outside your module
- Update `MASTER.md` every time you complete or start something
- **Never mark a task done unless it actually runs**
- Stuck more than 30 minutes → tell the lead immediately

---

## 17. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Desktop Shell | Electron | Cross-platform, rapid dev, web tech |
| UI Framework | React 18 | Component model, hooks, ecosystem |
| Styling | Tailwind CSS | Utility-first, fast iteration |
| State | Zustand | Minimal, no boilerplate |
| Build Tool | Vite | Fast HMR, modern standard |
| Backend | Python 3.11 + FastAPI | Best AI tooling ecosystem |
| LLM | Claude (Anthropic) / Llama 3.3 (Groq) | Powerful + free option |
| Browser Automation | Playwright | Most reliable, async-native |
| Database | SQLite + aiosqlite | Local, zero-dependency, async |
| Real-time | WebSockets | Decoupled, debuggable |
| Config | pydantic-settings | Typed, validated, env-aware |
| Dev Scripts | PowerShell | Windows-native automation |

**Languages breakdown (from GitHub):**
- Python: 56.6% — Backend, agent, tools
- JavaScript: 30.7% — Electron + React frontend
- CSS: 7.2% — Component styles
- PowerShell: 5.0% — Dev scripts
- HTML: 0.5% — Root index.html

---

*ARIA — Because your computer should work for you, not the other way around.*

*Built by the Newato team. Repo: [github.com/maheshh-v/Newato](https://github.com/maheshh-v/Newato)*