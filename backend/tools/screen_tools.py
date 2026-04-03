"""
ARIA Screen Tools
Desktop-level automation for visible browser and screen interaction tasks.
"""
import asyncio
import base64
import ctypes
import io
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger("aria.tools.screen")

_CHROME_CANDIDATES = [
    os.getenv("ARIA_CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
]


def _get_pyautogui():
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    return pyautogui


def _find_chrome_executable() -> str | None:
    for candidate in _CHROME_CANDIDATES:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _looks_like_url(text: str) -> bool:
    if not text or " " in text:
        return False
    return "." in text or text.startswith(("http://", "https://", "www."))


def _find_window_handle_for_pid(pid: int, timeout_ms: int = 6000) -> int | None:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    end_time = kernel32.GetTickCount64() + timeout_ms
    found_hwnd = ctypes.c_void_p(0)

    while kernel32.GetTickCount64() < end_time:
        def _enum_proc(hwnd: int, lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            target_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))
            if target_pid.value != pid:
                return True
            if user32.GetWindow(hwnd, 4):
                return True
            found_hwnd.value = hwnd
            return False

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(_enum_proc)
        user32.EnumWindows(enum_proc, 0)
        if found_hwnd.value:
            return int(found_hwnd.value)
        import time
        time.sleep(0.15)

    return None


def _activate_window(hwnd: int | None) -> bool:
    if not hwnd:
        return False
    try:
        import pygetwindow

        window = pygetwindow.Win32Window(hwnd)
        if window.isMinimized:
            window.restore()
        window.activate()
        window.maximize()
        return True
    except Exception:
        return False


def _activate_window_by_title(title: str) -> bool:
    if not title:
        return False
    try:
        import pygetwindow

        windows = pygetwindow.getWindowsWithTitle(title)
        for window in windows:
            try:
                if window.isMinimized:
                    window.restore()
                window.activate()
                window.maximize()
                return True
            except Exception:
                continue
    except Exception:
        return False
    return False


async def _sleep_ms(wait_ms: int) -> None:
    await asyncio.sleep(max(wait_ms, 0) / 1000)


async def take_screenshot(inputs: dict[str, Any], context: dict) -> dict:
    """Capture a screenshot of the entire screen."""
    try:
        import mss
        import mss.tools
        from PIL import Image

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            image = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            max_width = int(inputs.get("max_width", 900))
            if image.width > max_width:
                new_height = int(image.height * (max_width / image.width))
                image = image.resize((max_width, new_height))

            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            png_bytes = buffer.getvalue()

        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return {
            "success": True,
            "image_b64": b64,
            "width": image.width,
            "height": image.height,
        }
    except ImportError:
        return {"success": False, "error": "mss not installed. Run: pip install mss"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_open_browser(inputs: dict[str, Any], context: dict) -> dict:
    """
    Open a visible browser window.

    If `query` is provided, Chrome is focused and the query is typed into the
    address bar so the user can see the live keyboard interaction.
    """
    browser = str(inputs.get("browser", "chrome")).lower()
    url = str(inputs.get("url", "")).strip()
    query = str(inputs.get("query", "")).strip()
    new_window = bool(inputs.get("new_window", True))
    wait_ms = int(inputs.get("wait_ms", 1500))
    maximize = bool(inputs.get("maximize", True))

    if url and not url.startswith(("http://", "https://")) and " " not in url:
        url = f"https://{url}"

    if not url and _looks_like_url(query):
        url = query if query.startswith(("http://", "https://")) else f"https://{query}"

    launch_target = url or "about:blank"

    def _launch() -> dict[str, Any]:
        chrome_path = _find_chrome_executable() if browser == "chrome" else None
        if chrome_path:
            args = [chrome_path]
            if new_window:
                args.append("--new-window")
            if maximize:
                args.append("--start-maximized")
            args.append(launch_target)
            proc = subprocess.Popen(args)
            return {"method": "chrome", "target": launch_target, "pid": proc.pid}

        if os.name == "nt":
            os.startfile(launch_target)
            return {"method": "startfile", "target": launch_target}

        webbrowser.open(launch_target, new=1 if new_window else 0)
        return {"method": "webbrowser", "target": launch_target}

    try:
        launched = await asyncio.to_thread(_launch)
        await _sleep_ms(wait_ms)

        hwnd = None
        if launched.get("pid"):
            hwnd = await asyncio.to_thread(_find_window_handle_for_pid, int(launched["pid"]))
            if hwnd:
                await asyncio.to_thread(_activate_window, hwnd)
                await _sleep_ms(350)
            elif browser == "chrome":
                activated = await asyncio.to_thread(_activate_window_by_title, "Chrome")
                if activated:
                    await _sleep_ms(350)

        should_type_query = bool(query) and not url
        if should_type_query:
            await screen_hotkey({"keys": ["ctrl", "l"]}, context)
            await _sleep_ms(180)
            await screen_hotkey({"keys": ["ctrl", "a"]}, context)
            await _sleep_ms(100)
            await screen_type({"text": query, "interval_ms": 35}, context)
            await _sleep_ms(120)
            await screen_press({"key": "enter"}, context)
            await _sleep_ms(wait_ms)

        logger.info(
            "Visible browser opened",
            task_id=context.get("task_id"),
            browser=browser,
            url=url or "",
            query=query or "",
            maximized=maximize,
        )
        result = {
            "success": True,
            "browser": browser,
            "url": url,
            "query": query,
            "maximized": maximize,
            **launched,
        }
        screenshot = await take_screenshot({}, context)
        if screenshot.get("success"):
            result["image_b64"] = screenshot["image_b64"]
        return result
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_move_mouse(inputs: dict[str, Any], context: dict) -> dict:
    """Move the real mouse cursor to screen coordinates."""
    x = int(inputs["x"])
    y = int(inputs["y"])
    duration = max(float(inputs.get("duration_ms", 400)) / 1000, 0)

    def _move() -> None:
        pyautogui = _get_pyautogui()
        pyautogui.moveTo(x, y, duration=duration)

    try:
        await asyncio.to_thread(_move)
        return {"success": True, "x": x, "y": y}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_click(inputs: dict[str, Any], context: dict) -> dict:
    """Click the real mouse at the given coordinates or current cursor position."""
    x = inputs.get("x")
    y = inputs.get("y")
    button = str(inputs.get("button", "left"))
    clicks = int(inputs.get("clicks", 1))
    interval = max(float(inputs.get("interval_ms", 120)) / 1000, 0)
    move_duration = max(float(inputs.get("duration_ms", 200)) / 1000, 0)

    def _click() -> tuple[int, int]:
        pyautogui = _get_pyautogui()
        if x is not None and y is not None:
            pyautogui.moveTo(int(x), int(y), duration=move_duration)
        pyautogui.click(
            x=None if x is None else int(x),
            y=None if y is None else int(y),
            clicks=clicks,
            interval=interval,
            button=button,
        )
        return pyautogui.position()

    try:
        pos = await asyncio.to_thread(_click)
        return {"success": True, "x": pos[0], "y": pos[1], "button": button, "clicks": clicks}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_type(inputs: dict[str, Any], context: dict) -> dict:
    """Type text using the real keyboard into the focused app."""
    text = str(inputs["text"])
    interval = max(float(inputs.get("interval_ms", 20)) / 1000, 0)
    press_enter = bool(inputs.get("press_enter", False))

    def _type() -> None:
        pyautogui = _get_pyautogui()
        pyautogui.write(text, interval=interval)
        if press_enter:
            pyautogui.press("enter")

    try:
        await asyncio.to_thread(_type)
        return {"success": True, "typed": len(text), "press_enter": press_enter}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_press(inputs: dict[str, Any], context: dict) -> dict:
    """Press a single key one or more times."""
    key = str(inputs["key"])
    presses = int(inputs.get("presses", 1))
    interval = max(float(inputs.get("interval_ms", 100)) / 1000, 0)

    def _press() -> None:
        pyautogui = _get_pyautogui()
        pyautogui.press(key, presses=presses, interval=interval)

    try:
        await asyncio.to_thread(_press)
        return {"success": True, "key": key, "presses": presses}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_hotkey(inputs: dict[str, Any], context: dict) -> dict:
    """Press a keyboard shortcut such as Ctrl+L."""
    keys = [str(key) for key in inputs["keys"]]

    def _hotkey() -> None:
        pyautogui = _get_pyautogui()
        pyautogui.hotkey(*keys)

    try:
        await asyncio.to_thread(_hotkey)
        return {"success": True, "keys": keys}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_wait(inputs: dict[str, Any], context: dict) -> dict:
    """Pause before the next desktop action."""
    wait_ms = int(inputs.get("wait_ms", 1000))
    await _sleep_ms(wait_ms)
    return {"success": True, "wait_ms": wait_ms}


SCREEN_TOOLS: dict[str, Any] = {
    "take_screenshot": take_screenshot,
    "screen_open_browser": screen_open_browser,
    "screen_move_mouse": screen_move_mouse,
    "screen_click": screen_click,
    "screen_type": screen_type,
    "screen_press": screen_press,
    "screen_hotkey": screen_hotkey,
    "screen_wait": screen_wait,
}
