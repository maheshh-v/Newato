# ARIA — Autonomous Reasoning & Intelligence Agent

A local AI agent platform that runs on your computer, accepts natural language commands, and executes real tasks autonomously — browsing the web, writing code, controlling applications, and managing files — all running in parallel.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+

### Setup
```powershell
.\scripts\setup.ps1
```

### Development
```powershell
.\scripts\start-dev.ps1
```

### Build Executable (Windows Installer)
To generate the `ARIA Setup 1.0.0.exe` installer for your system:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-installer.ps1
```
*(The generated .exe file will be available in the `dist-installer/` folder).*

### Usage
1. Press `Ctrl+Shift+Space` from anywhere
2. Type a task in plain English
3. Press Enter — ARIA executes it autonomously
4. Watch the sidebar for live progress

## Architecture
- **Electron** — Desktop shell, global shortcuts, system tray
- **React 18 + Tailwind** — Frontend UI
- **Python FastAPI** — Backend agent runtime
- **Claude claude-sonnet-4-20250514** — LLM powering the agent
- **Playwright** — Browser automation
- **SQLite** — Local task persistence

## Project Structure
See `MASTER.md` for the full project structure and architectural decisions.