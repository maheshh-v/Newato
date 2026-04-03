"""
ARIA Agent — ReAct Loop
The core intelligence: think → act → observe → repeat until task is done or limit hit.
"""
import asyncio
import json
import re
import time
from typing import Any, Optional
from urllib.parse import quote_plus

import anthropic
import httpx
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
from tools.screen_tools import SCREEN_TOOLS
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

VISIBLE TASK RULE:
- If the user explicitly asks to open Chrome, show the browser live, move the cursor, or use the real desktop, prefer screen tools or a visible browser instead of hidden browsing.
- For live screen tasks, take screenshots after major visual changes so the sidebar can show progress.
- If the user gives a direct site like skillwyn.com, prefer opening it as a URL instead of typing it as a search query.

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

# Simplified prompt for Groq/OpenAI-style chat models.
_GROQ_SYSTEM_PROMPT = """You are ARIA, a local autonomous agent.

You must complete the user's task by calling tools. Use the available tools
to navigate, extract data, run code, and write files. Always make progress.

Rules:
- Prefer code over browser if possible.
- Always save results to a file.
- If an action fails twice, try a different approach.
- After 3 consecutive failures, call task_failed with a clear reason.
- When calling tools, use the tool call interface (no <function=...> tags).
- If the user asks for Chrome, a visible browser, live actions, cursor movement, or screen control, prefer screen tools or a visible browser flow.
- For live screen tasks, call take_screenshot after major visual changes.
- If the target is a direct website like skillwyn.com, pass it as `url` instead of `query`.

CURRENT TASK: {task_description}
SCRATCHPAD: {scratchpad}"""

_SCREEN_TOOL_NAMES = set(SCREEN_TOOLS.keys())
_BROWSER_TOOL_NAMES = set(BROWSER_TOOLS.keys())
_CODE_TOOL_NAMES = set(CODE_TOOLS.keys())
_TERMINAL_TOOL_NAMES = {"task_complete", "task_failed", "write_file", "read_file", "update_scratchpad"}
_EXTRACTION_KEYWORDS = (
    "extract",
    "heading",
    "headline",
    "title",
    "content",
    "text",
    "read",
    "tell me",
    "h1",
)
_SCREEN_POINTER_KEYWORDS = ("mouse", "cursor", "click", "desktop")


def _extract_youtube_play_query(description: str) -> Optional[str]:
    """Return search query when user asks to play the first YouTube video."""
    desc = description.lower()
    if "youtube" not in desc:
        return None

    if not any(marker in desc for marker in ("play first", "first video", "first vid", "1st video")):
        return None

    patterns = [
        r"search\s+(?:for\s+)?(.+?)\s+(?:on\s+)?youtube",
        r"youtube\s+and\s+then\s+search\s+(?:for\s+)?(.+?)(?:\s+and\s+play|\s+then\s+play|$)",
        r"search\s+youtube\s+(?:for\s+)?(.+?)(?:\s+and\s+play|\s+then\s+play|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, flags=re.IGNORECASE)
        if match:
            query = match.group(1).strip(" \t\n\r\"'.,!?:;")
            if query:
                return query

    # Fallback for prompts like: "go to chrome search youtube ... play first video"
    fallback = re.search(r"search\s+(?:for\s+)?(.+?)(?:\s+and\s+play\s+first|\s+play\s+first|$)", description, flags=re.IGNORECASE)
    if fallback:
        query = fallback.group(1).replace("youtube", "").strip(" \t\n\r\"'.,!?:;")
        return query or None

    return None


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
        "screen_open_browser": lambda i: f"Opening visible {i.get('browser', 'browser')}",
        "screen_move_mouse": lambda i: f"Moving cursor to ({i.get('x', '?')}, {i.get('y', '?')})",
        "screen_click": lambda i: f"Clicking screen at ({i.get('x', 'current')}, {i.get('y', 'current')})",
        "screen_type": lambda i: f"Typing '{str(i.get('text', ''))[:30]}...' with keyboard",
        "screen_press": lambda i: f"Pressing key '{i.get('key', '')}'",
        "screen_hotkey": lambda i: f"Pressing shortcut {'+'.join(i.get('keys', []))}",
        "screen_wait": lambda i: f"Waiting {i.get('wait_ms', 1000)}ms",
        "take_screenshot": lambda _: "Capturing desktop screenshot",
        "run_python": lambda _: "Running Python code",
        "write_file": lambda i: f"Writing file '{i.get('filename', '')}'",
        "read_file": lambda i: f"Reading file '{i.get('filename', '')}'",
        "update_scratchpad": lambda i: f"Saving '{i.get('key', '')}' to memory",
        "task_complete": lambda _: "Task completed ✓",
        "task_failed": lambda _: "Task failed ✗",
    }
    fn = msgs.get(tool_name)
    return fn(inputs) if fn else tool_name


def _repair_tool_json(raw: str) -> str:
    """Best-effort repair for malformed JSON in tool calls."""
    fixed = raw.strip()
    # Remove a trailing ")" before the final brace if present.
    fixed = re.sub(r"\)\s*}$", "}", fixed)
    # If summary field is missing a closing quote, add it before final }.
    if '"summary":"' in fixed and fixed.rstrip().endswith("}"):
        idx = fixed.find('"summary":"')
        if idx != -1:
            tail = fixed[idx + len('"summary":"'):]
            if '"' not in tail:
                fixed = fixed[:-1] + '"}'
    return fixed


def _parse_failed_tool_call(text: str) -> Optional[dict]:
    """Parse Groq failed_generation tool call.

    Supports:
    - <function=tool>{json}</function>
    - <function=tool={json}></function>
    """
    if not text:
        return None
    match = re.search(r"<function=([^>]+)>(.*)</function>", text, re.DOTALL)
    if not match:
        return None
    header = match.group(1).strip()
    body = match.group(2).strip()
    tool_name = header
    raw_json = body
    if not body and "={" in header:
        tool_name, raw_json = header.split("=", 1)
        tool_name = tool_name.strip()
        raw_json = raw_json.strip()
    try:
        inputs = json.loads(raw_json)
    except json.JSONDecodeError:
        try:
            inputs = json.loads(_repair_tool_json(raw_json))
        except json.JSONDecodeError:
            return None
    return {"id": f"failed_{int(time.time() * 1000)}", "name": tool_name, "input": inputs}


def _task_wants_visible_browser(description: str) -> bool:
    desc = description.lower()
    keywords = (
        "chrome",
        "show me",
        "live",
        "cursor",
        "mouse",
        "desktop",
        "screen",
        "visible browser",
        "browser window",
        "real browser",
    )
    return any(keyword in desc for keyword in keywords)


def _tool_list_to_groq(tools: list[dict]) -> list[dict]:
    groq_tools = []
    for tool in tools:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        })
    return groq_tools


def _select_tools(task_type: str, description: str, visible_browser: bool) -> list[dict]:
    desc = description.lower()
    allowed = set(_TERMINAL_TOOL_NAMES)

    if task_type == "code":
        allowed |= _CODE_TOOL_NAMES
    elif task_type == "api":
        allowed |= {"run_python", "write_file", "read_file"}
    elif visible_browser or task_type == "screen":
        allowed |= {
            "screen_open_browser",
            "screen_hotkey",
            "screen_type",
            "screen_press",
            "screen_wait",
            "take_screenshot",
        }
        if any(keyword in desc for keyword in _SCREEN_POINTER_KEYWORDS):
            allowed |= {"screen_move_mouse", "screen_click"}
        if any(keyword in desc for keyword in _EXTRACTION_KEYWORDS):
            allowed |= {"browser_navigate", "browser_wait", "browser_extract"}
    else:
        allowed |= _BROWSER_TOOL_NAMES
        if "python" in desc or "script" in desc:
            allowed.add("run_python")

    return [tool for tool in TOOL_REGISTRY if tool["name"] in allowed]


def _sanitize_result_for_llm(result: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(result)
    if "image_b64" in sanitized:
        image_b64 = sanitized.pop("image_b64")
        if isinstance(image_b64, str):
            sanitized["image_preview"] = f"<base64_png:{len(image_b64)} chars>"
    return sanitized


async def run_agent(task: Task) -> None:
    """
    Execute the full ReAct loop for a single task.
    Runs in its own asyncio task — isolated from other tasks.
    """
    db = await get_db()
    task_id = task.id

    # Classify task type
    task_type = classify_task(task.description)
    visible_browser = task_type == "screen" or _task_wants_visible_browser(task.description)
    active_tools = _select_tools(task_type, task.description, visible_browser)
    logger.info(
        "Toolset selected",
        task_id=task_id,
        task_type=task_type,
        visible_browser=visible_browser,
        tool_count=len(active_tools),
    )
    await queries.update_task_status(db, task_id, "running", task_type=task_type)

    await broadcaster.broadcast("task_started", task_id, {
        "task_type": task_type,
        "status": "running",
    })

    if settings.LLM_PROVIDER == "anthropic":
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    elif settings.LLM_PROVIDER == "groq":
        # Lazy import so missing groq package doesn't crash backend startup.
        import groq
        client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    elif settings.LLM_PROVIDER == "openrouter":
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        if settings.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_APP_NAME:
            headers["X-Title"] = settings.OPENROUTER_APP_NAME
        client = httpx.AsyncClient(
            base_url=settings.OPENROUTER_BASE_URL.rstrip("/"),
            headers=headers,
            timeout=60.0,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

    # Build provider-specific tool list once for this task to reduce token usage.
    GROQ_TOOLS = _tool_list_to_groq(active_tools)

    # State
    scratchpad: dict[str, str] = {}
    last_extract_text: Optional[str] = None
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
        launch_kwargs: dict[str, Any] = {
            "headless": not visible_browser,
        }
        if visible_browser:
            launch_kwargs["slow_mo"] = 120
            launch_kwargs["channel"] = "chrome"
        try:
            browser = await playwright_ctx.chromium.launch(**launch_kwargs)
        except Exception:
            if visible_browser and launch_kwargs.get("channel") == "chrome":
                launch_kwargs.pop("channel", None)
                browser = await playwright_ctx.chromium.launch(**launch_kwargs)
            else:
                raise
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        logger.info("Browser context created", task_id=task_id, visible=visible_browser)
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
        elif tool_name in SCREEN_TOOLS:
            return await SCREEN_TOOLS[tool_name](inputs, tool_context)
        elif tool_name in CODE_TOOLS:
            return await CODE_TOOLS[tool_name](inputs, tool_context)
        elif tool_name == "task_complete":
            return {"done": True, "summary": inputs.get("summary", ""), "files": inputs.get("output_files", [])}
        elif tool_name == "task_failed":
            return {"failed": True, "reason": inputs.get("reason", ""), "attempted": inputs.get("attempted", "")}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def _run_tool_step(step_number: int, tool_name: str, inputs: dict) -> tuple[dict, str]:
        """Execute a single tool step with persistence and broadcasting."""
        step_text = _make_step_text(tool_name, inputs)
        await broadcaster.broadcast("step_update", task_id, {
            "step_text": step_text,
            "tool_name": tool_name,
            "step_number": step_number,
            "progress": min(step_number / settings.MAX_STEPS_PER_TASK, 0.95),
        })

        result = await _execute_tool(tool_name, inputs)
        llm_result = _sanitize_result_for_llm(result)
        result_limit = 600 if settings.LLM_PROVIDER == "openrouter" else 1000
        result_text = truncate_result(json.dumps(llm_result, default=str), result_limit)

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

        if result.get("image_b64"):
            await broadcaster.broadcast("screenshot_update", task_id, {
                "image_b64": result["image_b64"]
            })

        return result, result_text

    try:
        task_start = time.time()

        async def _finalize_success(summary: str, files: list[str]) -> None:
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

        # Deterministic shortcut for frequent live-browser command.
        youtube_query = _extract_youtube_play_query(task.description)
        if youtube_query:
            logger.info("Using YouTube fast path", task_id=task_id, query=youtube_query)
            step_number += 1
            await _run_tool_step(
                step_number,
                "browser_navigate",
                {"url": f"https://www.youtube.com/results?search_query={quote_plus(youtube_query)}"},
            )

            step_number += 1
            wait_result, _ = await _run_tool_step(
                step_number,
                "browser_wait",
                {"selector": "ytd-video-renderer a#video-title", "timeout_ms": 20000},
            )
            if wait_result.get("success", True) is False or wait_result.get("error"):
                await _finalize_failure(task_id, db, "Could not find YouTube results", "youtube fast path", step_number)
                return

            step_number += 1
            click_result, _ = await _run_tool_step(
                step_number,
                "browser_click",
                {"selector": "ytd-video-renderer a#video-title", "method": "css"},
            )
            if click_result.get("success", True) is False or click_result.get("error"):
                await _finalize_failure(task_id, db, "Could not open first YouTube video", "youtube fast path", step_number)
                return

            step_number += 1
            await _run_tool_step(
                step_number,
                "browser_wait",
                {"selector": "#movie_player", "timeout_ms": 15000},
            )

            await _finalize_success(
                f"Opened YouTube, searched '{youtube_query}', and played the first video.",
                output_files,
            )
            return

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
                        tools=active_tools,
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
                        if output_files:
                            summary = (
                                f"Wrote file: {output_files[0]}"
                                if len(output_files) == 1
                                else f"Wrote files: {', '.join(output_files)}"
                            )
                            await _finalize_success(summary, output_files)
                            return
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
                    
            elif settings.LLM_PROVIDER in {"groq", "openrouter"}:
                if not groq_messages:
                    groq_messages.append({"role": "system", "content": system})
                else:
                    groq_messages[0] = {"role": "system", "content": system}
                
                groq_error_salvaged = False
                try:
                    if settings.LLM_PROVIDER == "groq":
                        response = await client.chat.completions.create(
                            model=settings.GROQ_MODEL,
                            messages=groq_messages,
                            tools=GROQ_TOOLS,
                            tool_choice="auto",
                            max_tokens=384,
                        )
                    else:
                        response = await client.post("/chat/completions", json={
                            "model": settings.OPENROUTER_MODEL,
                            "messages": groq_messages,
                            "tools": GROQ_TOOLS,
                            "tool_choice": "auto",
                            "max_tokens": 384,
                        })
                        response.raise_for_status()
                except Exception as e:
                    error_msg = str(e)
                    failed_gen = None
                    if settings.LLM_PROVIDER == "groq":
                        # Try to extract more detail from Groq's failed generation if available
                        if hasattr(e, "body") and isinstance(e.body, dict):
                            failed_gen = e.body.get("error", {}).get("failed_generation")
                            if failed_gen:
                                print(f"\n[GROQ DEBUG] FAILED GENERATION: {failed_gen}\n")
                                logger.error("Groq Tool Failure Detail", detail=failed_gen, task_id=task_id)
                                error_msg += f" | Details: {failed_gen}"
                    elif isinstance(e, httpx.HTTPStatusError):
                        try:
                            error_body = e.response.json()
                        except Exception:
                            error_body = {"error": {"message": e.response.text[:300]}}
                        error_detail = error_body.get("error", {}).get("message")
                        if error_detail:
                            error_msg += f" | {error_detail}"
                        failed_gen = error_body.get("error", {}).get("failed_generation")
                        if failed_gen:
                            logger.error("OpenRouter Tool Failure Detail", detail=failed_gen, task_id=task_id)
                            error_msg += f" | Details: {failed_gen}"

                    # Best-effort salvage if provider returned a malformed tool call
                    salvaged = _parse_failed_tool_call(failed_gen or "")
                    if salvaged:
                        tool_calls.append(salvaged)
                        groq_error_salvaged = True
                    else:
                        logger.error(
                            "LLM API error",
                            task_id=task_id,
                            provider=settings.LLM_PROVIDER,
                            error=error_msg,
                        )
                        await _finalize_failure(
                            task_id,
                            db,
                            f"API error: {error_msg[:250]}",
                            f"{settings.LLM_PROVIDER} API call",
                        )
                        return
                
                if not groq_error_salvaged:
                    if settings.LLM_PROVIDER == "groq":
                        msg = response.choices[0].message
                        finish_reason = response.choices[0].finish_reason
                    else:
                        payload = response.json()
                        choice = payload["choices"][0]
                        msg = choice["message"]
                        finish_reason = choice.get("finish_reason")
                
                if not groq_error_salvaged:
                    # Append assistant message
                    # Groq/OpenAI compatible formatting: content must be None if there are tool calls
                    if settings.LLM_PROVIDER == "groq":
                        content = msg.content
                        raw_tool_calls = msg.tool_calls
                    else:
                        content = msg.get("content")
                        raw_tool_calls = msg.get("tool_calls") or []

                    if raw_tool_calls and not content:
                        content = None
                    
                    assistant_msg = {"role": "assistant", "content": content}
                    if raw_tool_calls:
                        assistant_msg["tool_calls"] = []
                        for tc in raw_tool_calls:
                            if settings.LLM_PROVIDER == "groq":
                                tool_id = tc.id
                                tool_name = tc.function.name
                                tool_args = tc.function.arguments
                            else:
                                tool_id = tc["id"]
                                tool_name = tc["function"]["name"]
                                tool_args = tc["function"]["arguments"]
                            assistant_msg["tool_calls"].append({
                                "id": tool_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_args
                                }
                            })
                    groq_messages.append(assistant_msg)
                    
                    if not raw_tool_calls:
                        if finish_reason == "stop":
                            if output_files:
                                summary = (
                                    f"Wrote file: {output_files[0]}"
                                    if len(output_files) == 1
                                    else f"Wrote files: {', '.join(output_files)}"
                                )
                                await _finalize_success(summary, output_files)
                                return
                            logger.info("Agent stopped without tool call", task_id=task_id)
                            await _finalize_failure(task_id, db, "Agent stopped without completing task", "No tool calls")
                            return
                        groq_messages.append({
                            "role": "user",
                            "content": "Please continue with the task by calling a tool.",
                        })
                        continue
                    
                    # Normalize tool_calls
                    for b in raw_tool_calls:
                        if settings.LLM_PROVIDER == "groq":
                            tool_calls.append({
                                "id": b.id,
                                "name": b.function.name,
                                "input": json.loads(b.function.arguments),
                            })
                        else:
                            tool_calls.append({
                                "id": b["id"],
                                "name": b["function"]["name"],
                                "input": json.loads(b["function"]["arguments"]),
                            })

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
                    await _finalize_success(summary, files)
                    return

                if tool_name == "task_failed":
                    reason = inputs.get("reason", "Unknown failure")
                    attempted = inputs.get("attempted", "")
                    await _finalize_failure(task_id, db, reason, attempted, step_number)
                    return

                # Execute the tool
                try:
                    # If the model used a placeholder, replace with last extracted text.
                    if tool_name == "write_file":
                        content = inputs.get("content")
                        if last_extract_text and (not content or str(content).strip().startswith("<EXTRACTED_TEXT")):
                            inputs["content"] = last_extract_text
                    result = await _execute_tool(tool_name, inputs)
                    success = result.get("success", True)  # Default true for browser tools
                    llm_result = _sanitize_result_for_llm(result)
                    result_limit = 600 if settings.LLM_PROVIDER == "openrouter" else 1000
                    result_text = truncate_result(json.dumps(llm_result, default=str), result_limit)
                    consecutive_failures = 0 if success else consecutive_failures + 1
                except Exception as e:
                    logger.error("Tool execution error", task_id=task_id, tool=tool_name, exc_info=True)
                    result = {"success": False, "error": str(e)[:200], "recoverable": True}
                    result_text = json.dumps(result)
                    consecutive_failures += 1

                # Cache last extracted text for placeholder write_file calls.
                if tool_name == "browser_extract":
                    last_extract_text = result.get("text") or last_extract_text
                if tool_name == "write_file" and result.get("success", True):
                    written = result.get("filename") or inputs.get("filename")
                    if written and written not in output_files:
                        output_files.append(written)

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

                # Broadcast screenshots from browser or desktop tools.
                if result.get("image_b64"):
                    await broadcaster.broadcast("screenshot_update", task_id, {
                        "image_b64": result["image_b64"]
                    })

                if settings.LLM_PROVIDER == "anthropic":
                    tool_results_anthropic.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result_text,
                    })
                elif settings.LLM_PROVIDER in {"groq", "openrouter"}:
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result_text,
                    }
                    if settings.LLM_PROVIDER == "groq":
                        tool_message["name"] = tool_name
                    groq_messages.append(tool_message)

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
        if settings.LLM_PROVIDER == "openrouter":
            await client.aclose()
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
