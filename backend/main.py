"""
ARIA FastAPI Backend Entry Point
Starts the WebSocket server and REST API.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from config import settings, validate_config, update_env_file
from core.broadcaster import broadcaster
from core.task_manager import task_manager
from db.database import init_db, close_db
from db import queries
from db.database import get_db
from utils.logger import get_logger

logger = get_logger("aria.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application startup and shutdown lifecycle."""
    # Startup
    errors = validate_config()
    if errors:
        for err in errors:
            logger.warning("Config warning", error=err)
    await init_db()
    logger.info("ARIA backend started", port=settings.WEBSOCKET_PORT)
    yield
    # Shutdown
    await close_db()
    logger.info("ARIA backend stopped")


app = FastAPI(title="ARIA Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Electron app uses file:// or localhost
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── REST Endpoints ───────────────────────────────────────────────────────────

class TaskSubmitRequest(BaseModel):
    description: str


@app.post("/tasks")
async def submit_task(body: TaskSubmitRequest) -> dict:
    """Submit a new task for autonomous execution."""
    if not body.description.strip():
        return {"error": "Task description cannot be empty"}
    task = await task_manager.submit_task(body.description.strip())
    logger.info("Task submitted via REST", task_id=task.id)
    return task.to_dict()


@app.get("/tasks")
async def list_tasks() -> list[dict]:
    """List all tasks (newest first)."""
    db = await get_db()
    tasks = await queries.get_all_tasks(db)
    return [t.to_dict() for t in tasks]


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Get a single task by ID."""
    db = await get_db()
    task = await queries.get_task(db, task_id)
    if not task:
        return {"error": "Task not found"}
    return task.to_dict()


@app.get("/tasks/{task_id}/steps")
async def get_task_steps(task_id: str) -> list[dict]:
    """Get all steps for a task."""
    db = await get_db()
    steps = await queries.get_steps(db, task_id)
    return [s.to_dict() for s in steps]


@app.delete("/tasks/{task_id}")
async def delete_task_endpoint(task_id: str) -> dict:
    """Delete a task and all its associated steps and scratchpad from the database."""
    try:
        db = await get_db()
        # Cancel if task is running
        await task_manager.cancel_task(task_id)
        # Then delete from database (cascade deletes steps and scratchpad)
        await queries.delete_task(db, task_id)
        logger.info("Task deleted successfully", task_id=task_id)
        return {"deleted": True, "task_id": task_id}
    except Exception as e:
        logger.error("Failed to delete task", task_id=task_id, error=str(e))
        return {"deleted": False, "task_id": task_id, "error": str(e)}


@app.get("/health")
async def health() -> dict:
    """Check backend health including DB."""
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/ping")
async def ping() -> dict:
    """Fast, DB-less ping for initial startup detection."""
    return {"status": "pong"}
    """Health check endpoint."""
    return {
        "status": "ok",
        "running_tasks": task_manager.running_count,
        "ws_clients": broadcaster.client_count,
    }


# ─── Settings Endpoints ──────────────────────────────────────────────────────

def _mask_key(key: str) -> str:
    """Show only the last 4 characters of an API key."""
    if not key or key.startswith("your_"):
        return ""
    if len(key) <= 4:
        return "••••"
    return "•" * (len(key) - 4) + key[-4:]


class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@app.get("/settings")
async def get_settings() -> dict:
    """Return current settings with masked API keys."""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "api_keys": {
            "anthropic": _mask_key(settings.ANTHROPIC_API_KEY),
            "groq": _mask_key(settings.GROQ_API_KEY),
            "deepseek": _mask_key(settings.DEEPSEEK_API_KEY),
            "openai": _mask_key(settings.OPENAI_API_KEY),
        },
    }


@app.put("/settings")
async def save_settings(body: SettingsUpdateRequest) -> dict:
    """Update settings: write to .env file and hot-reload.
    Auto-detects provider from whichever API key is provided."""
    env_updates: dict[str, str] = {}

    # Map API key fields to provider names and default models
    KEY_TO_PROVIDER = {
        "groq_api_key": ("groq", "llama-3.3-70b-versatile"),
        "anthropic_api_key": ("anthropic", "claude-sonnet-4-20250514"),
        "openai_api_key": ("openai", "gpt-4o"),
        "deepseek_api_key": ("deepseek", "deepseek-chat"),
    }

    # Collect any API keys the user sent
    detected_provider = None
    detected_model = None
    for field, (prov, default_model) in KEY_TO_PROVIDER.items():
        val = getattr(body, field, None)
        if val and val.strip():
            env_updates[field.upper()] = val.strip()
            detected_provider = prov
            detected_model = default_model

    # If user explicitly set provider/model, use those
    if body.llm_provider is not None and body.llm_provider.strip():
        env_updates["LLM_PROVIDER"] = body.llm_provider.strip()
    elif detected_provider:
        # Auto-detect: user entered a key, auto-set provider
        env_updates["LLM_PROVIDER"] = detected_provider

    if body.llm_model is not None and body.llm_model.strip():
        env_updates["LLM_MODEL"] = body.llm_model.strip()
    elif detected_model and "LLM_PROVIDER" in env_updates:
        # Auto-set default model for the detected provider
        env_updates["LLM_MODEL"] = detected_model

    if not env_updates:
        return {"saved": False, "error": "No settings provided"}

    try:
        update_env_file(env_updates)
        settings.reload()
        logger.info("Settings updated", keys=list(env_updates.keys()))
        return {
            "saved": True,
            "updated_keys": list(env_updates.keys()),
            "active_provider": settings.LLM_PROVIDER,
            "active_model": settings.LLM_MODEL,
        }
    except Exception as e:
        logger.error("Failed to save settings", error=str(e))
        return {"saved": False, "error": str(e)}


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    WebSocket endpoint for real-time task events.
    Clients connect here to receive all ARIA events.
    """
    await broadcaster.connect(ws)
    try:
        db = await get_db()

        # 1) Send backend settings so frontend knows the output dir
        await ws.send_json({
            "event_type": "settings",
            "data": {
                "output_dir": str(settings.ARIA_OUTPUT_DIR),
            },
        })

        # 2) Hydrate: send all tasks WITH their steps
        tasks = await queries.get_all_tasks(db)
        for task in tasks:
            await ws.send_json({
                "task_id": task.id,
                "event_type": "task_created",
                "timestamp": task.created_at,
                "data": task.to_dict(),
            })
            # Send steps for this task so expanded view works after reconnect
            steps = await queries.get_steps(db, task.id)
            for step in steps:
                await ws.send_json({
                    "task_id": task.id,
                    "event_type": "step_update",
                    "timestamp": step.timestamp,
                    "data": {
                        "step_number": step.step_number,
                        "tool_name": step.tool_name,
                        "step_text": step.step_text,
                        "progress": min(step.step_number / settings.MAX_STEPS_PER_TASK, 0.95),
                    },
                })

        # 3) Keep connection alive — listen for incoming messages
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=30.0)
                # Handle client → server messages (e.g., submit from overlay)
                if msg.get("type") == "submit_task":
                    description = msg.get("description", "").strip()
                    # Filter out the dismiss signal from the overlay
                    if description and description != "__dismiss__":
                        await task_manager.submit_task(description)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await ws.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info("WS client disconnected normally")
    except Exception as e:
        logger.error("WS error", error=str(e))
    finally:
        broadcaster.disconnect(ws)
