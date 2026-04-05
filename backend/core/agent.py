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
from openai import AsyncOpenAI
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
- If the task is unclear or ambiguous, do NOT call task_failed. Instead, do something simple like print a greeting or write a welcome file.
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
SCRATCHPAD: {scratchpad}

USER PROFILE:
{user_profile}

RELEVANT PAST WORK:
{past_memory}

Use this context silently. Do not mention it unless relevant."""

_GROQ_SYSTEM_PROMPT = """You are ARIA — an Autonomous Reasoning and Intelligence Agent.

Your job is to complete tasks by calling tools. 

IMPORTANT:
- If the task is unclear or ambiguous, do NOT call task_failed. Instead, do something simple like print a greeting or write a welcome file.
- Always try to make progress, even if the task is minimal.
- For text output → use run_python with print() or write_file
- For file operations → use write_file  
- For code execution → use run_python
- For browser tasks → use browser_* tools
- When task is done → call task_complete with summary

Do NOT use screen_* tools unless explicitly needed.

Task: {task_description}

USER PROFILE:
{user_profile}

RELEVANT PAST WORK:
{past_memory}

Next step: Call ONE tool now."""


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
        "screen_search_human": lambda i: f"Searching like human for '{i.get('query', '')}'",
        "screen_search_web": lambda i: f"Searching web for '{i.get('query', '')}'",
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

    # Load scratchpad from DB at task start
    scratchpad: dict[str, str] = await queries.get_scratchpad(db, task_id)

    # Load user profile
    profile = await queries.get_all_user_profile(db)
    profile_text = "\n".join([f"{k}: {v}" for k, v in profile.items()])
    if not profile_text:
        profile_text = "No profile yet"

    # Search past memory for relevant context
    keywords = [w for w in task.description.split() if len(w) > 4][:3]
    past_memories = await queries.search_memory(db, keywords, limit=3)
    memory_text = ""
    for m in past_memories:
        memory_text += f"- Past task: {m['summary']}\n"
    if not memory_text:
        memory_text = "No relevant past tasks"

    # Classify task type
    task_type = classify_task(task.description)
    await queries.update_task_status(db, task_id, "running", task_type=task_type)

    await broadcaster.broadcast("task_started", task_id, {
        "task_type": task_type,
        "status": "running",
    })

    if settings.LLM_PROVIDER == "anthropic":
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    elif settings.LLM_PROVIDER in ("groq", "deepseek", "openai"):
        if settings.LLM_PROVIDER == "groq":
            client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
        elif settings.LLM_PROVIDER == "deepseek":
            # DeepSeek is OpenAI-compatible. Set timeout to 60s for initial connection + request
            from httpx import Timeout
            timeout = Timeout(timeout=60.0, connect=30.0, read=60.0)
            client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY, 
                base_url="https://api.deepseek.com/v1",
                timeout=timeout
            )
        elif settings.LLM_PROVIDER == "openai":
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
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
    messages: list[dict] = []
    groq_messages: list[dict] = []
    step_number = 0
    consecutive_failures = 0
    MAX_CONSECUTIVE = 3
    output_files: list[str] = []
    had_successful_action = False

    # Browser context (created lazily for web tasks)
    playwright_ctx = None
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

    async def _ensure_browser() -> Page:
        nonlocal playwright_ctx, browser, context, page
        if page is not None:
            return page
        try:
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
        except Exception as e:
            logger.error("Browser launch failed", task_id=task_id, error=str(e), exc_info=True)
            raise RuntimeError(f"Browser launch failed: {str(e)}. Run 'playwright install chromium' to fix this.")

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
        elif tool_name in SCREEN_TOOLS:
            return await SCREEN_TOOLS[tool_name](inputs, tool_context)
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
                    user_profile=profile_text,
                    past_memory=memory_text,
                )
            elif settings.LLM_PROVIDER == "deepseek":
                system = _GROQ_SYSTEM_PROMPT.format(
                    task_description=task.description,
                    scratchpad=json.dumps(scratchpad) if scratchpad else "",
                    user_profile=profile_text,
                    past_memory=memory_text,
                )
            else:
                # For Groq and other providers
                system = _GROQ_SYSTEM_PROMPT.format(
                    task_description=task.description,
                    scratchpad=json.dumps(scratchpad) if scratchpad else "",
                    user_profile=profile_text,
                    past_memory=memory_text,
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
                    
            elif settings.LLM_PROVIDER in ("groq", "deepseek", "openai"):
                if not groq_messages:
                    groq_messages.append({"role": "system", "content": system})
                    groq_messages.append({"role": "user", "content": task.description})
                else:
                    groq_messages[0] = {"role": "system", "content": system}
                
                logger.info(f"Calling {settings.LLM_PROVIDER} API", task_id=task_id, model=settings.LLM_MODEL, messages_count=len(groq_messages))
                try:
                    response = await client.chat.completions.create(
                        model=settings.LLM_MODEL,
                        messages=groq_messages,
                        tools=GROQ_TOOLS,
                        tool_choice="auto",
                    )
                except Exception as e:
                    logger.error(f"{settings.LLM_PROVIDER.capitalize()} API error", task_id=task_id, error=str(e), exc_info=True)
                    await _finalize_failure(task_id, db, f"API error: {str(e)[:200]}", f"{settings.LLM_PROVIDER} API call")
                    return
                
                msg = response.choices[0].message
                
                # Log response for debugging
                logger.info(f"LLM response received", task_id=task_id, has_tool_calls=bool(msg.tool_calls), content_length=len(msg.content or ""))
                
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
                    logger.warning(f"No tool calls from {settings.LLM_PROVIDER}", task_id=task_id, finish_reason=response.choices[0].finish_reason)
                    if response.choices[0].finish_reason == "stop":
                        logger.info("Agent attempted to stop without tool call", task_id=task_id)
                        if step_number == 0 or not had_successful_action:
                            await _finalize_failure(
                                task_id,
                                db,
                                "No actionable result was produced",
                                "Model stopped without successful tool execution",
                                step_number,
                            )
                            return

                        # Force verification + explicit terminal tool call.
                        groq_messages.append({
                            "role": "user",
                            "content": "Do not stop yet. First verify the result (screenshot or URL evidence), then call task_complete with concrete proof. If goal not met, continue acting.",
                        })
                        continue
                    
                    # Limit retries to avoid infinite loops
                    if step_number > settings.MAX_STEPS_PER_TASK - 5:
                        logger.warning("Reached near max steps without tool calls", task_id=task_id)
                        await _finalize_failure(task_id, db, "Agent reached max steps without completing task", "No tool calls after multiple attempts", step_number)
                        return
                    
                    groq_messages.append({
                        "role": "user",
                        "content": "You must call a tool to make progress. Choose one of the available tools and call it now.",
                    })
                    continue
                
                # Normalize tool_calls
                for b in msg.tool_calls:
                    try:
                        tool_input = json.loads(b.function.arguments) if isinstance(b.function.arguments, str) else b.function.arguments
                        tool_calls.append({"id": b.id, "name": b.function.name, "input": tool_input})
                    except json.JSONDecodeError as e:
                        logger.error("Tool input parsing error", task_id=task_id, arguments=b.function.arguments, error=str(e))
                        tool_calls.append({"id": b.id, "name": b.function.name, "input": {}})

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

                    # Save to memory table
                    keywords_to_save = " ".join([
                        w for w in task.description.split() if len(w) > 4
                    ][:10])
                    await queries.save_memory(
                        db,
                        task_id=task_id,
                        summary=f"Task: {task.description[:100]} | Result: {summary[:200]}",
                        keywords=keywords_to_save,
                        output_files=json.dumps(files)
                    )

                    # Learn user profile from task via LLM
                    try:
                        profile_prompt = f"""
From this task, extract any facts about the user (name, company, 
preferences, tools they use). 
Task: {task.description}
Result: {summary}

Return JSON only: {{"key": "value"}} or {{}} if nothing learned.
Max 3 facts. Be specific. Example: {{"company_type": "B2B SaaS", "prefers_json_output": "true"}}
"""
                        if settings.LLM_PROVIDER == "anthropic":
                            profile_response = await client.messages.create(
                                model=settings.CLAUDE_MODEL,
                                max_tokens=500,
                                system="You extract user facts from task descriptions. Return ONLY valid JSON.",
                                messages=[{"role": "user", "content": profile_prompt}],
                            )
                            profile_text = profile_response.content[0].text if profile_response.content else "{}"
                        else:
                            profile_response = await client.chat.completions.create(
                                model=settings.LLM_MODEL,
                                messages=[
                                    {"role": "system", "content": "You extract user facts from task descriptions. Return ONLY valid JSON."},
                                    {"role": "user", "content": profile_prompt}
                                ],
                                max_tokens=500,
                            )
                            profile_text = profile_response.choices[0].message.content or "{}"
                        
                        # Parse JSON and upsert to user_profile
                        import re
                        json_match = re.search(r'\{[^{}]*\}', profile_text, re.DOTALL)
                        if json_match:
                            profile_data = json.loads(json_match.group())
                            for k, v in profile_data.items():
                                await queries.upsert_user_profile(db, k, str(v))
                                logger.info("Learned user profile", key=k, value=v)
                    except Exception as e:
                        logger.warning("Failed to learn user profile", error=str(e))

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
                    if success and tool_name not in ("update_scratchpad", "read_file"):
                        had_successful_action = True
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
                elif settings.LLM_PROVIDER in ("groq", "deepseek", "openai"):
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result_text,
                    })

                    # Self-monitoring nudge after UI-affecting actions.
                    if tool_name in {
                        "screen_search_human",
                        "screen_search_web",
                        "screen_open_app",
                        "screen_click",
                        "screen_type",
                        "browser_navigate",
                        "browser_click",
                        "browser_type",
                    }:
                        groq_messages.append({
                            "role": "user",
                            "content": "Self-check: verify this action matched the user intent. If mismatch, correct immediately. If objective is met, call task_complete with concrete evidence.",
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

            # Compress messages after 10 steps (every 5 steps after)
            if step_number > 10 and step_number % 5 == 0:
                if settings.LLM_PROVIDER == "anthropic" and len(messages) > 5:
                    old_msgs = messages[1:-4]
                    summary = "Previous steps: " + " → ".join([
                        m.get("content", "")[:50] if isinstance(m.get("content"), str)
                        else str(m.get("content", ""))[:50]
                        for m in old_msgs if m.get("role") == "assistant"
                    ])
                    messages = [messages[0]] + [{"role": "user", "content": summary}] + messages[-4:]
                elif settings.LLM_PROVIDER in ("groq", "deepseek", "openai") and len(groq_messages) > 5:
                    old_msgs = groq_messages[1:-4]
                    summary = "Previous steps: " + " → ".join([
                        m.get("content", "")[:50] if isinstance(m.get("content"), str)
                        else str(m.get("content", ""))[:50]
                        for m in old_msgs if m.get("role") == "assistant"
                    ])
                    groq_messages = [groq_messages[0]] + [{"role": "user", "content": summary}] + groq_messages[-4:]
                    logger.info("Compressed message history", task_id=task_id, step=step_number)

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
