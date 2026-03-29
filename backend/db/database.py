"""
ARIA SQLite Database Connection
Manages the async SQLite connection pool via aiosqlite.
"""
import aiosqlite
from pathlib import Path
from config import settings
from utils.logger import get_logger

logger = get_logger("aria.db")

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Get the shared database connection."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def init_db() -> None:
    """Initialize the SQLite database and create tables."""
    global _db
    db_path: Path = settings.DB_PATH
    logger.info("Initializing database", db_path=str(db_path))
    _db = await aiosqlite.connect(str(db_path))
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL;")
    await _db.execute("PRAGMA foreign_keys=ON;")
    await _create_tables(_db)
    await _db.commit()
    logger.info("Database initialized")


async def _create_tables(db: aiosqlite.Connection) -> None:
    """Create all required tables if they don't exist."""
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            task_type TEXT,
            created_at INTEGER NOT NULL,
            started_at INTEGER,
            completed_at INTEGER,
            summary TEXT,
            error_reason TEXT,
            output_files TEXT,
            step_count INTEGER DEFAULT 0,
            total_steps_estimate INTEGER DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL REFERENCES tasks(id),
            step_number INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            tool_input TEXT,
            tool_result TEXT,
            step_text TEXT,
            timestamp INTEGER NOT NULL,
            screenshot_path TEXT
        );

        CREATE TABLE IF NOT EXISTS scratchpad (
            task_id TEXT NOT NULL REFERENCES tasks(id),
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (task_id, key)
        );
    """)


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Database connection closed")
