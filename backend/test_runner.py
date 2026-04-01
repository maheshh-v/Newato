"""
ARIA Test Runner
Quick smoke test that submits a task through the agent loop.
Usage: python test_runner.py
"""
import asyncio
import os
import sys
import time

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings, validate_config
from core.agent import run_agent
from db.database import init_db, close_db, get_db
from db import queries
from db.models import Task
from utils.logger import get_logger

logger = get_logger("test_runner")


async def test_agent():
    """Run a single test task through the agent loop."""
    # Validate config first
    errors = validate_config()
    if errors:
        for err in errors:
            logger.error(f"Config error: {err}")
        logger.error("Fix your .env file and try again.")
        return

    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Output dir: {settings.ARIA_OUTPUT_DIR}")

    # Initialize database
    await init_db()
    db = await get_db()

    # Create a test task using the correct API
    task = Task(
        id="test001",
        description="Go to example.com and save the page title to test.txt",
        created_at=int(time.time() * 1000),
    )
    await queries.create_task(db, task)
    logger.info(f"Task created: {task.id} — {task.description}")

    # Run the agent
    try:
        await run_agent(task)
    except Exception as e:
        logger.error(f"Agent crashed: {e}", exc_info=True)

    # Check result
    result = await queries.get_task(db, task.id)
    if result:
        logger.info(f"Final status: {result.status}")
        if result.summary:
            logger.info(f"Summary: {result.summary}")
        if result.error_reason:
            logger.error(f"Error: {result.error_reason}")
    else:
        logger.error("Task not found in DB after execution!")

    await close_db()
    logger.info("Test complete.")


if __name__ == "__main__":
    asyncio.run(test_agent())
