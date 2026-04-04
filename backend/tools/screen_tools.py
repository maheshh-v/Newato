"""
ARIA Screen Tools
Screenshot capture using mss and mouse/keyboard control via PyAutoGUI.
"""
import base64
import io
import subprocess
import time
from urllib.parse import quote_plus
from typing import Any

from utils.logger import get_logger

logger = get_logger("aria.tools.screen")


async def take_screenshot(inputs: dict[str, Any], context: dict) -> dict:
    """Capture a screenshot of the entire screen."""
    try:
        import mss
        import mss.tools

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            sct_img = sct.grab(monitor)
            png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)

        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return {"success": True, "image_b64": b64, "width": sct_img.size[0], "height": sct_img.size[1]}
    except ImportError:
        return {"success": False, "error": "mss not installed. Run: pip install mss"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_move_mouse(inputs: dict[str, Any], context: dict) -> dict:
    """Move mouse to coordinates."""
    try:
        import pyautogui
        x: int = inputs.get("x", 0)
        y: int = inputs.get("y", 0)
        duration: float = inputs.get("duration", 0.5)
        
        pyautogui.moveTo(x, y, duration=duration)
        time.sleep(0.2)
        return {"success": True, "position": (x, y)}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed. Run: pip install pyautogui"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_click(inputs: dict[str, Any], context: dict) -> dict:
    """Click at screen coordinates."""
    try:
        import pyautogui
        x: int = inputs.get("x", 0)
        y: int = inputs.get("y", 0)
        button: str = inputs.get("button", "left")
        
        pyautogui.click(x, y, button=button)
        time.sleep(0.3)
        return {"success": True, "clicked": (x, y), "button": button}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_type(inputs: dict[str, Any], context: dict) -> dict:
    """Type text via keyboard."""
    try:
        import pyautogui
        text: str = inputs.get("text", "")
        interval: float = inputs.get("interval", 0.05)

        # Use pyautogui.write for reliable visible typing.
        pyautogui.write(str(text), interval=float(interval))
        time.sleep(0.2)
        return {"success": True, "typed": len(text), "text_length": len(text)}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_open_app(inputs: dict[str, Any], context: dict) -> dict:
    """Open an application."""
    try:
        app_name: str = inputs.get("app", "").lower()
        
        # Map common apps to their executables
        app_map = {
            "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        }
        
        exe_path = app_map.get(app_name, app_name)
        subprocess.Popen(exe_path)
        time.sleep(2)
        return {"success": True, "app": app_name, "launched": True}
    except FileNotFoundError:
        return {"success": False, "error": f"App '{app_name}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_key_press(inputs: dict[str, Any], context: dict) -> dict:
    """Press keyboard keys."""
    try:
        import pyautogui
        keys: str = inputs.get("keys", "")
        
        # Can be multiple keys like "ctrl+c" or "enter" or "tab+a"
        key_sequence = keys.split("+")
        
        for key in key_sequence:
            pyautogui.press(key)
        time.sleep(0.2)
        return {"success": True, "keys_pressed": keys}
    except ImportError:
        return {"success": False, "error": "pyautogui not installed"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_search_web(inputs: dict[str, Any], context: dict) -> dict:
    """Open browser directly with a web search URL to avoid random UI typing/clicking."""
    try:
        app_name: str = inputs.get("app", "brave").lower()
        query: str = inputs.get("query", "").strip()
        if not query:
            return {"success": False, "error": "query is required"}

        app_map = {
            "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        }

        exe_path = app_map.get(app_name, app_name)
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        subprocess.Popen([exe_path, search_url])
        time.sleep(2)
        return {
            "success": True,
            "app": app_name,
            "query": query,
            "url": search_url,
            "launched": True,
        }
    except FileNotFoundError:
        return {"success": False, "error": f"App '{app_name}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


async def screen_search_human(inputs: dict[str, Any], context: dict) -> dict:
    """Human-like search: open browser, move cursor, focus address bar, type query, press enter.

    Primary behavior for search tasks. Falls back to direct URL search if requested.
    """
    try:
        import pyautogui

        app_name: str = inputs.get("app", "brave").lower()
        query: str = inputs.get("query", "").strip()
        interval: float = float(inputs.get("interval", 0.05))
        fallback_to_url: bool = bool(inputs.get("fallback_to_url", True))

        if not query:
            return {"success": False, "error": "query is required"}

        open_result = await screen_open_app({"app": app_name}, context)
        if not open_result.get("success"):
            return open_result

        # Make cursor movement visible first (user requirement).
        screen_w, screen_h = pyautogui.size()
        target_x = max(50, int(screen_w * 0.5))
        target_y = max(50, int(screen_h * 0.08))
        pyautogui.moveTo(target_x, target_y, duration=0.5)
        time.sleep(0.15)

        # Focus browser address/search bar in a deterministic way.
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.15)

        # Type query visibly and submit.
        pyautogui.write(query, interval=interval)
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.8)

        # Optional lightweight verification: read address bar URL via clipboard.
        verified_url = ""
        query_in_url = None
        try:
            import pyperclip  # Optional dependency
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.1)
            verified_url = str(pyperclip.paste() or "")
            query_in_url = quote_plus(query).lower() in verified_url.lower() if verified_url else False
        except Exception:
            # Keep running even if clipboard verification is unavailable.
            verified_url = ""
            query_in_url = None

        return {
            "success": True,
            "mode": "human",
            "app": app_name,
            "query": query,
            "typed": True,
            "submitted": True,
            "cursor_moved": True,
            "verified_url": verified_url,
            "query_in_url": query_in_url,
        }
    except Exception as e:
        if bool(inputs.get("fallback_to_url", True)):
            fallback_result = await screen_search_web(
                {
                    "app": inputs.get("app", "brave"),
                    "query": inputs.get("query", ""),
                },
                context,
            )
            fallback_result["fallback_used"] = True
            fallback_result["fallback_reason"] = str(e)[:200]
            return fallback_result
        return {"success": False, "error": str(e)[:200]}


SCREEN_TOOLS: dict[str, Any] = {
    "take_screenshot": take_screenshot,
    "screen_move_mouse": screen_move_mouse,
    "screen_click": screen_click,
    "screen_type": screen_type,
    "screen_open_app": screen_open_app,
    "screen_key_press": screen_key_press,
    "screen_search_human": screen_search_human,
    "screen_search_web": screen_search_web,
}
