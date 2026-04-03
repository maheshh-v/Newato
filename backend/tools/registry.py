"""
ARIA Tool Registry
Defines all tools available to the agent.
Simplified for Groq/OpenAI compatibility.
"""

TOOL_REGISTRY: list[dict] = [
    {
        "name": "browser_navigate",
        "description": "Navigate the browser to a URL. Always use full URLs including https://",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to navigate to"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_click",
        "description": "Click an element on the current page. Prefer CSS selectors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector or text content",
                },
                "method": {
                    "type": "string",
                    "enum": ["css", "text", "xpath"],
                    "description": "Selector method (default: css)",
                },
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "clear_first": {"type": "boolean"},
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "browser_extract",
        "description": "Extract text content from the current page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "extract_links": {"type": "boolean"},
            },
            "required": [],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"}
            },
            "required": [],
        },
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the page up or down.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down"]},
                "amount": {"type": "integer"},
            },
            "required": ["direction"],
        },
    },
    {
        "name": "browser_wait",
        "description": "Wait for an element to appear.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "timeout_ms": {"type": "integer"},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "screen_open_browser",
        "description": "Open a visible maximized browser window. Use this when the user explicitly asks for Chrome, a live window, or visible browsing. Prefer `url` for direct sites like skillwyn.com; use `query` for search phrases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "browser": {"type": "string", "description": "Browser name, usually chrome"},
                "url": {"type": "string", "description": "Optional URL to open"},
                "query": {"type": "string", "description": "Optional text to type into the browser address bar"},
                "new_window": {"type": "boolean"},
                "maximize": {"type": "boolean"},
                "wait_ms": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "screen_move_mouse",
        "description": "Move the real mouse cursor to screen coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "duration_ms": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "screen_click",
        "description": "Click the real mouse on screen. Use coordinates when you know where to click.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "middle", "right"]},
                "clicks": {"type": "integer"},
                "interval_ms": {"type": "integer"},
                "duration_ms": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "screen_type",
        "description": "Type text using the real keyboard into the focused application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "interval_ms": {"type": "integer"},
                "press_enter": {"type": "boolean"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "screen_press",
        "description": "Press a single keyboard key, optionally multiple times.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "presses": {"type": "integer"},
                "interval_ms": {"type": "integer"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "screen_hotkey",
        "description": "Press a keyboard shortcut such as Ctrl+L or Alt+Tab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["keys"],
        },
    },
    {
        "name": "screen_wait",
        "description": "Wait briefly between visible desktop actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wait_ms": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Capture the current desktop screen as an image preview.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "run_python",
        "description": "Execute a Python code snippet and return its output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"}
            },
            "required": ["code"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the ARIA output directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "enum": ["write", "append"]},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the content of a previously written file.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
    {
        "name": "update_scratchpad",
        "description": "Save information to your working memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "task_complete",
        "description": "Call this ONLY when the task is fully completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "output_files": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["summary"],
        },
    },
    {
        "name": "task_failed",
        "description": "Call this if the task cannot be completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "attempted": {"type": "string"},
            },
            "required": ["reason"],
        },
    },
]
