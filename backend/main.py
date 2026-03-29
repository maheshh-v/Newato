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

from config import settings, validate_config
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
async def cancel_task(task_id: str) -> dict:
    """Cancel a running task."""
    cancelled = await task_manager.cancel_task(task_id)
    return {"cancelled": cancelled, "task_id": task_id}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "running_tasks": task_manager.running_count,
        "ws_clients": broadcaster.client_count,
    }


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    WebSocket endpoint for real-time task events.
    Clients connect here to receive all ARIA events.
    """
    await broadcaster.connect(ws)
    try:
        # Send current task list on connect so UI can hydrate
        db = await get_db()
        tasks = await queries.get_all_tasks(db)
        for task in tasks:
            await ws.send_json({
                "task_id": task.id,
                "event_type": "task_created",
                "timestamp": task.created_at,
                "data": task.to_dict(),
            })

        # Keep connection alive — listen for incoming messages
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=30.0)
                # Handle client → server messages (e.g., submit from overlay)
                if msg.get("type") == "submit_task":
                    description = msg.get("description", "").strip()
                    if description:
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
