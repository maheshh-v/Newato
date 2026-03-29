"""
ARIA Task Manager
Orchestrates all tasks — accepts new tasks, manages asyncio semaphore for concurrency.
"""
import asyncio
import time
import uuid
from typing import Optional

from config import settings
from core.agent import run_agent
from core.broadcaster import broadcaster
from db.database import get_db
from db import queries
from db.models import Task
from utils.logger import get_logger

logger = get_logger("aria.task_manager")


class TaskManager:
    """Manages the lifecycle of all ARIA tasks with concurrency control."""

    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)
        self._running: dict[str, asyncio.Task] = {}

    async def submit_task(self, description: str) -> Task:
        """
        Accept a new task, persist it, broadcast creation, and schedule execution.
        Returns immediately with the Task object.
        """
        task_id = uuid.uuid4().hex[:8]
        task = Task(
            id=task_id,
            description=description,
            created_at=int(time.time() * 1000),
        )

        db = await get_db()
        await queries.create_task(db, task)

        logger.info("Task submitted", task_id=task_id, description=description[:60])

        await broadcaster.broadcast("task_created", task_id, {
            "description": description,
            "status": "queued",
        })

        # Schedule async execution (non-blocking)
        asyncio_task = asyncio.create_task(self._run_with_semaphore(task))
        self._running[task_id] = asyncio_task

        # Cleanup handle when done
        asyncio_task.add_done_callback(lambda _: self._running.pop(task_id, None))

        return task

    async def _run_with_semaphore(self, task: Task) -> None:
        """Acquire semaphore slot then run the agent."""
        async with self._semaphore:
            logger.info("Starting agent", task_id=task.id)
            await run_agent(task)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task by ID. Returns True if cancelled."""
        if asyncio_task := self._running.get(task_id):
            asyncio_task.cancel()
            logger.info("Task cancelled", task_id=task_id)
            return True
        return False

    @property
    def running_count(self) -> int:
        return len(self._running)


# Singleton
task_manager = TaskManager()
