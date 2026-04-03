"""
ARIA Code & File System Tools
Python execution and file I/O for the agent sandbox.
"""
import asyncio
import io
import json
import sys
import textwrap
from pathlib import Path
from typing import Any

from config import settings
from utils.logger import get_logger
from utils.sanitizer import is_code_safe, truncate_result, sanitize_filename

logger = get_logger("aria.tools.code")


def _get_output_dir(task_id: str) -> Path:
    """Return (and create) the task-specific output directory."""
    output_dir = settings.ARIA_OUTPUT_DIR / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


async def run_python(inputs: dict[str, Any], context: dict) -> dict:
    """Execute Python code in a sandboxed subprocess."""
    code: str = inputs["code"]
    task_id: str = context.get("task_id", "unknown")

    safe, reason = is_code_safe(code)
    if not safe:
        return {"success": False, "error": f"Code blocked: {reason}"}

    # Inject the output directory as a known path
    output_dir = _get_output_dir(task_id)
    preamble = f"ARIA_OUTPUT_DIR = {repr(str(output_dir))}\n"
    full_code = preamble + textwrap.dedent(code)

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", full_code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=30.0
        )

        out = stdout.decode("utf-8", errors="replace")
        err = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            return {
                "success": False,
                "error": truncate_result(err or "Non-zero exit code", 500),
                "stdout": truncate_result(out, 500),
            }

        return {
            "success": True,
            "output": truncate_result(out, 3000),
        }

    except asyncio.TimeoutError:
        return {"success": False, "error": "Code execution timed out after 30 seconds"}
    except Exception as e:
        logger.error("run_python error", exc_info=True, task_id=task_id)
        return {"success": False, "error": str(e)[:200]}


async def write_file(inputs: dict[str, Any], context: dict) -> dict:
    """Write content to a sandboxed output file."""
    task_id: str = context.get("task_id", "unknown")
    filename: str = sanitize_filename(inputs["filename"])
    content: str = inputs["content"]
    mode: str = inputs.get("mode", "write")

    output_dir = _get_output_dir(task_id)
    file_path = output_dir / filename

    write_mode = "a" if mode == "append" else "w"
    try:
        file_path.write_text(content, encoding="utf-8") if write_mode == "w" \
            else file_path.open("a", encoding="utf-8").write(content)
        # Avoid reserved LogRecord keys like "filename".
        logger.info("File written", output_file=filename, task_id=task_id, bytes=len(content))
        return {
            "success": True,
            "filename": filename,
            "path": str(file_path),
            "bytes": len(content),
        }
    except OSError as e:
        return {"success": False, "error": str(e)}


async def read_file(inputs: dict[str, Any], context: dict) -> dict:
    """Read a file from the task's output directory."""
    task_id: str = context.get("task_id", "unknown")
    filename: str = sanitize_filename(inputs["filename"])
    output_dir = _get_output_dir(task_id)
    file_path = output_dir / filename

    if not file_path.exists():
        return {"success": False, "error": f"File not found: {filename}"}

    try:
        content = file_path.read_text(encoding="utf-8")
        return {
            "success": True,
            "filename": filename,
            "content": truncate_result(content, 3000),
        }
    except OSError as e:
        return {"success": False, "error": str(e)}


async def update_scratchpad(inputs: dict[str, Any], context: dict) -> dict:
    """Update the agent's working memory (persisted via DB in agent.py)."""
    key: str = inputs["key"]
    value: str = inputs["value"]
    # The actual DB write happens in agent.py after this returns
    context.setdefault("scratchpad", {})[key] = value
    return {"success": True, "key": key}


CODE_TOOLS: dict[str, Any] = {
    "run_python": run_python,
    "write_file": write_file,
    "read_file": read_file,
    "update_scratchpad": update_scratchpad,
}
