"""
ARIA Screen Tools
Screenshot capture using mss and fallback mouse/keyboard via PyAutoGUI.
Minimal usage — only when browser tools are insufficient.
"""
import base64
import io
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


SCREEN_TOOLS: dict[str, Any] = {
    "take_screenshot": take_screenshot,
}
