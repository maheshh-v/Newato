import asyncio
import os
import sys

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from core.agent import run_agent
from db.database import get_db
from db import queries
from db.models import Task
from utils.logger import get_logger

logger = get_logger("test_runner")

async def test_groq():
    logger.info(f"Testing with LLM_PROVIDER = {settings.LLM_PROVIDER}")
    if settings.LLM_PROVIDER == "groq" and not settings.GROQ_API_KEY:
        logger.error("Error: GROQ_API_KEY is missing in your .env file!")
        return

    db = await get_db()
    
    # Insert a dummy task for testing
    task_id = await queries.insert_task(db, "Go to example.com and save the page title to test.txt")
    task = await queries.get_task(db, task_id)
    
    if task:
        logger.info(f"Submitting task: {task.description}")
        await run_agent(task)
        logger.info("Task completed/failed. Check the outputs directory for test.txt")
    else:
        logger.error("Failed to insert testing task.")

if __name__ == "__main__":
    asyncio.run(test_groq())
