"""
Tool Isolation Tests
Run each tool directly with hardcoded inputs (no AI).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Ensure subprocess support on Windows (Playwright + run_python need it).
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

from config import settings  # noqa: E402
from tools.browser_tools import browser_navigate, browser_extract  # noqa: E402
from tools.code_tools import write_file, run_python  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402


def _print_result(label: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} - {detail}")


async def _test_browser_navigate(context: dict) -> bool:
    label = "Browser navigate"
    try:
        result = await browser_navigate({"url": "https://www.google.com"}, context)
        title = (result.get("title") or "").strip()
        ok = bool(title)
        _print_result(label, ok, f"title='{title}'")
        return ok
    except Exception as exc:
        _print_result(label, False, f"error={exc}")
        return False


async def _test_browser_extract(context: dict) -> bool:
    label = "Browser extract"
    try:
        await browser_navigate({"url": "https://example.com"}, context)
        result = await browser_extract({"selector": "h1"}, context)
        heading = (result.get("text") or "").strip()
        ok = "Example" in heading
        _print_result(label, ok, f"heading='{heading}'")
        return ok
    except Exception as exc:
        _print_result(label, False, f"error={exc}")
        return False


async def _test_write_file(task_id: str) -> bool:
    label = "Write file"
    try:
        result = await write_file({"filename": "test.txt", "content": "hello"}, {"task_id": task_id})
        file_path = Path(result.get("path", ""))
        ok = result.get("success") and file_path.exists() and file_path.read_text(encoding="utf-8") == "hello"
        _print_result(label, ok, f"path='{file_path}'")
        return bool(ok)
    except Exception as exc:
        _print_result(label, False, f"error={exc}")
        return False


async def _test_run_python(task_id: str) -> bool:
    label = "Run python"
    try:
        result = await run_python({"code": "print(2+2)"}, {"task_id": task_id})
        output = (result.get("output") or "").strip()
        ok = result.get("success") and output.endswith("4")
        _print_result(label, ok, f"output='{output}'")
        return bool(ok)
    except Exception as exc:
        _print_result(label, False, f"error={exc}")
        return False


async def main() -> None:
    task_id = "tools_test"
    print(f"[INFO] Output dir: {settings.ARIA_OUTPUT_DIR / task_id}")
    results: list[bool] = []

    # Browser tools
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            browser_context = {"task_id": task_id, "page": page}

            results.append(await _test_browser_navigate(browser_context))
            results.append(await _test_browser_extract(browser_context))

            await browser.close()
    except Exception as exc:
        _print_result("Browser navigate", False, f"error={exc}")
        _print_result("Browser extract", False, f"error={exc}")
        results.extend([False, False])

    # Code tools
    results.append(await _test_write_file(task_id))
    results.append(await _test_run_python(task_id))

    all_ok = all(results)
    print(f"[SUMMARY] {'PASS' if all_ok else 'FAIL'} ({results.count(True)}/{len(results)} passed)")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
