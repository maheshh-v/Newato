"""
ARIA Agent — ReAct Loop
The core intelligence: think → act → observe → repeat until task is done or limit hit.
"""
import asyncio
import json
import time
from typing import Any, Optional

import anthropic
import groq
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import settings
from core.broadcaster import broadcaster
from core.router import classify_task
from db.database import get_db
from db import queries
from db.models import Step, Task
from tools.registry import TOOL_REGISTRY
from tools.browser_tools import BROWSER_TOOLS
from tools.code_tools import CODE_TOOLS
from utils.logger import get_logger
from utils.sanitizer import truncate_result

logger = get_logger("aria.agent")

_SYSTEM_PROMPT = """You are ARIA — an Autonomous Reasoning and Intelligence Agent running locally on the user's computer.

Your job is to complete tasks autonomously using the tools available to you. You operate in a ReAct loop: you think, you act, you observe, you think again.

CORE PRINCIPLES:
- Always make progress. Do not repeat the same failed action twice.
- Prefer efficiency. If a task can be done with code, do it with code. Browser automation is for when you need to interact with a web interface.
- Save results. Any data extracted, any file created — write it to disk.
- Use your scratchpad. Track your progress explicitly so you don't lose state.
- Be decisive. Pick the best approach and execute it. Do not hedge.

APPROACH PRIORITY (always choose the highest available):
1. Direct API call (if the service has an API, use it)
2. Code execution (if it can be done in Python, do it in Python)
3. Browser automation (if it requires web interaction)
4. Screen control (only as absolute last resort)

FAILURE HANDLING:
- If a browser action fails, wait 1 second and try once more with a different selector
- If it fails again, take a screenshot to understand the page state
- If fundamentally blocked, try a completely different approach
- After 3 consecutive failures, call task_failed with a clear explanation

OUTPUT STANDARDS:
- Always save extracted data to a file, never just return it as text
- Name files descriptively: "ai_companies_research.json", "nexusai_landing_page.html"
- When writing code files, make them actually runnable
- Confirm file creation at the end of each task

CURRENT TASK: {task_description}
TASK ID: {task_id}
SCRATCHPAD: {scratchpad}"""


def _make_step_text(tool_name: str, inputs: dict) -> str:
    """Generate a human-readable description of the current action."""
    msgs = {
        "browser_navigate": lambda i: f"Navigating to {i.get('url', '')}",
        "browser_click": lambda i: f"Clicking '{i.get('selector', '')}'",
        "browser_type": lambda i: f"Typing into '{i.get('selector', '')}'",
        "browser_extract": lambda i: "Extracting page content",
        "browser_screenshot": lambda _: "Taking screenshot",
        "browser_scroll": lambda i: f"Scrolling {i.get('direction', 'down')}",
        "browser_wait": lambda i: f"Waiting for '{i.get('selector', '')}'",
        "run_python": lambda _: "Running Python code",
        "write_file": lambda i: f"Writing file '{i.get('filename', '')}'",
        "read_file": lambda i: f"Reading file '{i.get('filename', '')}'",
        "update_scratchpad": lambda i: f"Saving '{i.get('key', '')}' to memory",
        "task_complete": lambda _: "Task completed ✓",
        "task_failed": lambda _: "Task failed ✗",
    }
    fn = msgs.get(tool_name)
    return fn(inputs) if fn else tool_name


async def run_agent(task: Task) -> None:
    """
    Execute the full ReAct loop for a single task.
    Runs in its own asyncio task — isolated from other tasks.
    """
    db = await get_db()
    task_id = task.id

    # Classify task type
    task_type = classify_task(task.description)
    await queries.update_task_status(db, task_id, "running", task_type=task_type)

    await broadcaster.broadcast("task_started", task_id, {
        "task_type": task_type,
        "status": "running",
    })

    if settings.LLM_PROVIDER == "anthropic":
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    elif settings.LLM_PROVIDER == "groq":
        client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

    # Build Groq compatible tool list once
    GROQ_TOOLS = []
    for tool in TOOL_REGISTRY:
        GROQ_TOOLS.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        })

    # State
    scratchpad: dict[str, str] = {}
    messages: list[dict] = []
    groq_messages: list[dict] = []
    step_number = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE = 3
    output_files: list[str] = []

    # Browser context (created lazily for web tasks)
    playwright_ctx = None
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    async def _ensure_browser() -> Page:
        nonlocal playwright_ctx, browser, context, page
        if page is not None:
            return page
        playwright_ctx = await async_playwright().start()
        browser = await playwright_ctx.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        logger.info("Browser context created", task_id=task_id)
        return page

    async def _cleanup_browser() -> None:
        nonlocal playwright_ctx, browser, context, page
        try:
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright_ctx:
                await playwright_ctx.stop()
        except Exception:
            pass
        playwright_ctx = browser = context = page = None

    async def _execute_tool(tool_name: str, inputs: dict) -> dict:
        """Dispatch tool call to the correct implementation."""
        tool_context: dict[str, Any] = {
            "task_id": task_id,
            "scratchpad": scratchpad,
        }

        if tool_name in BROWSER_TOOLS:
            tool_context["page"] = await _ensure_browser()
            return await BROWSER_TOOLS[tool_name](inputs, tool_context)
        elif tool_name in CODE_TOOLS:
            return await CODE_TOOLS[tool_name](inputs, tool_context)
        elif tool_name == "task_complete":
            return {"done": True, "summary": inputs.get("summary", ""), "files": inputs.get("output_files", [])}
        elif tool_name == "task_failed":
            return {"failed": True, "reason": inputs.get("reason", ""), "attempted": inputs.get("attempted", "")}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    try:
        task_start = time.time()

        while step_number < settings.MAX_STEPS_PER_TASK:
            # Check wall-clock timeout
            if time.time() - task_start > settings.TASK_TIMEOUT_SECONDS:
                logger.warning("Task timeout", task_id=task_id, elapsed=time.time() - task_start)
                await _finalize_failure(task_id, db, "Task exceeded maximum time limit", "Time limit reached")
                return

            # Build system prompt with current scratchpad
            if settings.LLM_PROVIDER == "anthropic":
                system = _SYSTEM_PROMPT.format(
                    task_description=task.description,
                    task_id=task_id,
                    scratchpad=json.dumps(scratchpad, indent=2) if scratchpad else "{}",
                )
            else:
                # Simpler prompt for Groq
                system = _GROQ_SYSTEM_PROMPT.format(
                    task_description=task.description,
                    scratchpad=json.dumps(scratchpad) if scratchpad else "",
                )

            # Call LLM based on provider
            tool_calls = []
            if settings.LLM_PROVIDER == "anthropic":
                try:
                    response = await client.messages.create(
                        model=settings.CLAUDE_MODEL,
                        max_tokens=4096,
                        system=system,
                        tools=TOOL_REGISTRY,
                        messages=messages,
                    )
                except anthropic.APIError as e:
                    logger.error("Claude API error", task_id=task_id, error=str(e))
                    await _finalize_failure(task_id, db, f"API error: {str(e)[:200]}", "Claude API call")
                    return

                # Add assistant response to history
                messages.append({"role": "assistant", "content": response.content})

                # Process response blocks
                tool_calls_raw = [b for b in response.content if b.type == "tool_use"]
                
                if not tool_calls_raw:
                    # No tool call — agent is done thinking without acting
                    if response.stop_reason == "end_turn":
                        logger.info("Agent stopped without tool call", task_id=task_id)
                        await _finalize_failure(task_id, db, "Agent stopped without completing task", "No tool calls")
                        return
                    messages.append({
                        "role": "user",
                        "content": "Please continue with the task by calling a tool.",
                    })
                    continue
                
                # Normalize tool_calls
                for b in tool_calls_raw:
                    tool_calls.append({"id": b.id, "name": b.name, "input": b.input})
                    
            elif settings.LLM_PROVIDER == "groq":
                if not groq_messages:
                    groq_messages.append({"role": "system", "content": system})
                else:
                    groq_messages[0] = {"role": "system", "content": system}
                
                try:
                    response = await client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=groq_messages,
                        tools=GROQ_TOOLS,
                        tool_choice="auto",
                    )
                except Exception as e:
                    error_msg = str(e)
                    # Try to extract more detail from Groq's failed generation if available
                    if hasattr(e, "body") and isinstance(e.body, dict):
                        failed_gen = e.body.get("error", {}).get("failed_generation")
                        if failed_gen:
                            print(f"\n[GROQ DEBUG] FAILED GENERATION: {failed_gen}\n")
                            logger.error("Groq Tool Failure Detail", detail=failed_gen, task_id=task_id)
                            error_msg += f" | Details: {failed_gen}"

                    logger.error("Groq API error", task_id=task_id, error=error_msg)
                    await _finalize_failure(task_id, db, f"API error: {error_msg[:250]}", "Groq API call")
                    return
                
                msg = response.choices[0].message
                
                # Append assistant message
                # Groq/OpenAI compatible formatting: content must be None if there are tool calls
                content = msg.content
                if msg.tool_calls and not content:
                    content = None
                
                assistant_msg = {"role": "assistant", "content": content}
                if msg.tool_calls:
                    assistant_msg["tool_calls"] = []
                    for tc in msg.tool_calls:
                        assistant_msg["tool_calls"].append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        })
                groq_messages.append(assistant_msg)
                
                if not msg.tool_calls:
                    if response.choices[0].finish_reason == "stop":
                        logger.info("Agent stopped without tool call", task_id=task_id)
                        await _finalize_failure(task_id, db, "Agent stopped without completing task", "No tool calls")
                        return
                    groq_messages.append({
                        "role": "user",
                        "content": "Please continue with the task by calling a tool.",
                    })
                    continue
                
                # Normalize tool_calls
                for b in msg.tool_calls:
                    tool_calls.append({"id": b.id, "name": b.function.name, "input": json.loads(b.function.arguments)})

            # Execute all tool calls in the response (usually one)
            tool_results_anthropic = []
            for tool_call in tool_calls:
                step_number += 1
                tool_name: str = tool_call["name"]
                inputs: dict = tool_call["input"] or {}
                step_text = _make_step_text(tool_name, inputs)

                logger.info("Tool call", task_id=task_id, step=step_number, tool=tool_name)

                # Broadcast step update before executing
                await broadcaster.broadcast("step_update", task_id, {
                    "step_text": step_text,
                    "tool_name": tool_name,
                    "step_number": step_number,
                    "progress": min(step_number / settings.MAX_STEPS_PER_TASK, 0.95),
                })

                # Handle terminal tools before execution
                if tool_name == "task_complete":
                    files: list[str] = inputs.get("output_files", [])
                    summary: str = inputs.get("summary", "")
                    duration = int(time.time() - task_start)

                    await queries.update_task_status(
                        db, task_id, "completed",
                        summary=summary,
                        output_files=files,
                    )
                    await broadcaster.broadcast("task_completed", task_id, {
                        "summary": summary,
                        "output_files": files,
                        "duration_seconds": duration,
                        "total_steps": step_number,
                    })
                    logger.info("Task completed", task_id=task_id, steps=step_number, duration=duration)
                    return

                if tool_name == "task_failed":
                    reason = inputs.get("reason", "Unknown failure")
                    attempted = inputs.get("attempted", "")
                    await _finalize_failure(task_id, db, reason, attempted, step_number)
                    return

                # Execute the tool
                try:
                    result = await _execute_tool(tool_name, inputs)
                    success = result.get("success", True)  # Default true for browser tools
                    result_text = truncate_result(json.dumps(result, default=str), 1000)
                    consecutive_failures = 0 if success else consecutive_failures + 1
                except Exception as e:
                    logger.error("Tool execution error", task_id=task_id, tool=tool_name, exc_info=True)
                    result = {"success": False, "error": str(e)[:200], "recoverable": True}
                    result_text = json.dumps(result)
                    consecutive_failures += 1

                # Persist step to DB
                step_record = Step(
                    task_id=task_id,
                    step_number=step_number,
                    tool_name=tool_name,
                    step_text=step_text,
                    tool_input=json.dumps(inputs, default=str)[:500],
                    tool_result=result_text[:500],
                )
                await queries.insert_step(db, step_record)
                await queries.increment_step_count(db, task_id)

                # Handle scratchpad updates in DB
                if tool_name == "update_scratchpad":
                    key = inputs.get("key", "")
                    value = inputs.get("value", "")
                    if key:
                        scratchpad[key] = value
                        await queries.upsert_scratchpad(db, task_id, key, value)

                # Broadcast screenshot if captured
                if tool_name == "browser_screenshot" and result.get("image_b64"):
                    await broadcaster.broadcast("screenshot_update", task_id, {
                        "image_b64": result["image_b64"]
                    })

                if settings.LLM_PROVIDER == "anthropic":
                    tool_results_anthropic.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result_text,
                    })
                elif settings.LLM_PROVIDER == "groq":
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": result_text,
                    })

                # Check consecutive failure limit
                if consecutive_failures >= MAX_CONSECUTIVE:
                    logger.warning("Max consecutive failures", task_id=task_id)
                    await _finalize_failure(
                        task_id, db,
                        f"Reached {MAX_CONSECUTIVE} consecutive tool failures",
                        f"Last failing tool: {tool_name}",
                        step_number,
                    )
                    return

            # Append tool results for next iteration
            if settings.LLM_PROVIDER == "anthropic":
                messages.append({"role": "user", "content": tool_results_anthropic})

        # Exceeded max steps
        await _finalize_failure(
            task_id, db,
            f"Reached maximum step limit ({settings.MAX_STEPS_PER_TASK})",
            "All steps exhausted",
            step_number,
        )

    except asyncio.CancelledError:
        logger.warning("Agent task cancelled", task_id=task_id)
        await _finalize_failure(task_id, db, "Task was cancelled", "Cancelled")
    except Exception as e:
        logger.error("Unexpected agent error", task_id=task_id, exc_info=True)
        await _finalize_failure(task_id, db, f"Unexpected error: {str(e)[:200]}", "Agent loop crash")
    finally:
        await _cleanup_browser()


async def _finalize_failure(
    task_id: str,
    db: Any,
    reason: str,
    attempted: str,
    step_number: int = 0,
) -> None:
    """Mark task as failed and broadcast the event."""
    await queries.update_task_status(
        db, task_id, "failed", error_reason=reason
    )
    await broadcaster.broadcast("task_failed", task_id, {
        "reason": reason,
        "attempted": attempted,
        "step_number": step_number,
    })
    logger.warning("Task failed", task_id=task_id, reason=reason)
