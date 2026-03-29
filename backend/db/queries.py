"""
ARIA Database Query Helpers
All DB read/write operations are defined here — no raw SQL elsewhere.
"""
import json
import time
from typing import Optional

import aiosqlite

from db.models import Task, Step
from utils.logger import get_logger

logger = get_logger("aria.db.queries")


async def create_task(db: aiosqlite.Connection, task: Task) -> None:
    """Insert a new task into the database."""
    await db.execute(
        """
        INSERT INTO tasks (id, description, status, task_type, created_at,
                           step_count, total_steps_estimate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (task.id, task.description, task.status, task.task_type,
         task.created_at, task.step_count, task.total_steps_estimate),
    )
    await db.commit()


async def get_task(db: aiosqlite.Connection, task_id: str) -> Optional[Task]:
    """Retrieve a task by ID."""
    async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cur:
        row = await cur.fetchone()
        return Task.from_row(row) if row else None


async def get_all_tasks(db: aiosqlite.Connection) -> list[Task]:
    """Retrieve all tasks ordered by creation time descending."""
    async with db.execute("SELECT * FROM tasks ORDER BY created_at DESC") as cur:
        rows = await cur.fetchall()
        return [Task.from_row(r) for r in rows]


async def update_task_status(
    db: aiosqlite.Connection,
    task_id: str,
    status: str,
    *,
    summary: Optional[str] = None,
    error_reason: Optional[str] = None,
    output_files: Optional[list[str]] = None,
    task_type: Optional[str] = None,
) -> None:
    """Update task status and optional fields."""
    now = int(time.time() * 1000)
    started_at = now if status == "running" else None
    completed_at = now if status in ("completed", "failed") else None

    fields: list[str] = ["status = ?"]
    values: list = [status]

    if started_at:
        fields.append("started_at = ?")
        values.append(started_at)
    if completed_at:
        fields.append("completed_at = ?")
        values.append(completed_at)
    if summary is not None:
        fields.append("summary = ?")
        values.append(summary)
    if error_reason is not None:
        fields.append("error_reason = ?")
        values.append(error_reason)
    if output_files is not None:
        fields.append("output_files = ?")
        values.append(json.dumps(output_files))
    if task_type is not None:
        fields.append("task_type = ?")
        values.append(task_type)

    values.append(task_id)
    set_clause = ", ".join(fields)

    await db.execute(
        f"UPDATE tasks SET {set_clause} WHERE id = ?",
        values,
    )
    await db.commit()


async def increment_step_count(db: aiosqlite.Connection, task_id: str) -> None:
    """Atomically increment the step counter for a task."""
    await db.execute(
        "UPDATE tasks SET step_count = step_count + 1 WHERE id = ?",
        (task_id,),
    )
    await db.commit()


async def insert_step(db: aiosqlite.Connection, step: Step) -> None:
    """Insert an agent step into the steps table."""
    await db.execute(
        """
        INSERT INTO steps (task_id, step_number, tool_name, tool_input,
                           tool_result, step_text, timestamp, screenshot_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (step.task_id, step.step_number, step.tool_name, step.tool_input,
         step.tool_result, step.step_text, step.timestamp, step.screenshot_path),
    )
    await db.commit()


async def get_steps(db: aiosqlite.Connection, task_id: str) -> list[Step]:
    """Retrieve all steps for a task in order."""
    async with db.execute(
        "SELECT * FROM steps WHERE task_id = ? ORDER BY step_number ASC",
        (task_id,),
    ) as cur:
        rows = await cur.fetchall()
        return [
            Step(
                task_id=r["task_id"],
                step_number=r["step_number"],
                tool_name=r["tool_name"],
                step_text=r["step_text"] or "",
                timestamp=r["timestamp"],
                tool_input=r["tool_input"],
                tool_result=r["tool_result"],
                screenshot_path=r["screenshot_path"],
            )
            for r in rows
        ]


async def upsert_scratchpad(
    db: aiosqlite.Connection, task_id: str, key: str, value: str
) -> None:
    """Insert or replace a scratchpad entry."""
    now = int(time.time() * 1000)
    await db.execute(
        """
        INSERT INTO scratchpad (task_id, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(task_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (task_id, key, value, now),
    )
    await db.commit()


async def get_scratchpad(db: aiosqlite.Connection, task_id: str) -> dict[str, str]:
    """Get all scratchpad entries for a task."""
    async with db.execute(
        "SELECT key, value FROM scratchpad WHERE task_id = ?", (task_id,)
    ) as cur:
        rows = await cur.fetchall()
        return {r["key"]: r["value"] for r in rows}
