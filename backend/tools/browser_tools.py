"""
ARIA Browser Tools
Playwright-based browser automation tools for the agent.
Each function receives the tool inputs dict and a context dict with the browser page.
"""
import asyncio
import base64
import re
from typing import Any

from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError,
)
from utils.logger import get_logger
from utils.sanitizer import truncate_result

logger = get_logger("aria.tools.browser")


def _humanize_step(tool_name: str, inputs: dict) -> str:
    """Generate a human-readable step description."""
    match tool_name:
        case "browser_navigate":
            return f"Navigating to {inputs.get('url', '')}"
        case "browser_click":
            return f"Clicking '{inputs.get('selector', '')}'"
        case "browser_type":
            text = inputs.get("text", "")[:30]
            return f"Typing '{text}...' into {inputs.get('selector', '')}"
        case "browser_extract":
            sel = inputs.get("selector") or "page"
            return f"Extracting content from {sel}"
        case "browser_screenshot":
            return "Taking screenshot"
        case "browser_scroll":
            return f"Scrolling {inputs.get('direction', 'down')} {inputs.get('amount', 500)}px"
        case "browser_wait":
            return f"Waiting for {inputs.get('selector', '')}"
        case _:
            return tool_name


async def browser_navigate(inputs: dict[str, Any], context: dict) -> dict:
    """Navigate to a URL."""
    page: Page = context["page"]
    url: str = inputs["url"]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    logger.info("Navigating", url=url, task_id=context.get("task_id"))
    response = await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    title = await page.title()
    status = response.status if response else 0
    return {"url": page.url, "title": title, "status": status}


async def browser_click(inputs: dict[str, Any], context: dict) -> dict:
    """Click an element using CSS selector or text."""
    page: Page = context["page"]
    selector: str = inputs["selector"]
    method: str = inputs.get("method", "css")

    try:
        if method == "text":
            await page.get_by_text(selector, exact=False).first.click(timeout=10_000)
        elif method == "xpath":
            await page.locator(f"xpath={selector}").first.click(timeout=10_000)
        else:
            await page.locator(selector).first.click(timeout=10_000)
        await page.wait_for_load_state("domcontentloaded", timeout=5_000)
        return {"clicked": selector, "url": page.url}
    except PlaywrightTimeoutError:
        # Fallback: try text-based click
        if method != "text":
            await page.get_by_text(selector, exact=False).first.click(timeout=8_000)
            return {"clicked": selector, "fallback": "text", "url": page.url}
        raise


async def browser_type(inputs: dict[str, Any], context: dict) -> dict:
    """Type text into an input field."""
    page: Page = context["page"]
    selector: str = inputs["selector"]
    text: str = inputs["text"]
    clear_first: bool = inputs.get("clear_first", True)

    locator = page.locator(selector).first
    if clear_first:
        await locator.clear(timeout=5_000)
    await locator.type(text, delay=30)
    return {"typed": len(text), "selector": selector}


async def browser_extract(inputs: dict[str, Any], context: dict) -> dict:
    """Extract text content from the page."""
    page: Page = context["page"]
    selector: str = inputs.get("selector", "")
    extract_links: bool = inputs.get("extract_links", False)

    if selector:
        elements = await page.locator(selector).all_inner_texts()
        text = "\n".join(elements)
    else:
        text = await page.inner_text("body")

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    result: dict[str, Any] = {"text": truncate_result(text, 4000)}

    if extract_links:
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({text: e.textContent.trim(), href: e.href}))"
        )
        result["links"] = links[:50]  # cap at 50 links

    return result


async def browser_screenshot(inputs: dict[str, Any], context: dict) -> dict:
    """Take a screenshot and return as base64."""
    page: Page = context["page"]
    png_bytes: bytes = await page.screenshot(type="png", full_page=False)
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    logger.info("Screenshot taken", task_id=context.get("task_id"), size=len(png_bytes))
    return {"image_b64": b64, "size": len(png_bytes)}


async def browser_scroll(inputs: dict[str, Any], context: dict) -> dict:
    """Scroll the page."""
    page: Page = context["page"]
    direction: str = inputs.get("direction", "down")
    amount: int = inputs.get("amount", 500)
    delta = amount if direction == "down" else -amount
    await page.mouse.wheel(0, delta)
    await asyncio.sleep(0.3)
    return {"scrolled": direction, "amount": amount}


async def browser_wait(inputs: dict[str, Any], context: dict) -> dict:
    """Wait for an element to appear."""
    page: Page = context["page"]
    selector: str = inputs["selector"]
    timeout_ms: int = inputs.get("timeout_ms", 5000)
    await page.wait_for_selector(selector, timeout=timeout_ms)
    return {"found": selector}


# Dispatcher — maps tool name → async function
BROWSER_TOOLS: dict[str, Any] = {
    "browser_navigate": browser_navigate,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_extract": browser_extract,
    "browser_screenshot": browser_screenshot,
    "browser_scroll": browser_scroll,
    "browser_wait": browser_wait,
}
