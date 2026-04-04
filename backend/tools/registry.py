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
    {
        "name": "screen_open_app",
        "description": "Open an application like Brave, Chrome, Firefox, Edge. Useful for opening Brave browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app": {"type": "string", "enum": ["brave", "chrome", "firefox", "edge"]},
            },
            "required": ["app"],
        },
    },
    {
        "name": "screen_move_mouse",
        "description": "Move the mouse cursor to screen coordinates for visual feedback.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate in pixels"},
                "y": {"type": "integer", "description": "Y coordinate in pixels"},
                "duration": {"type": "number", "description": "Duration in seconds (default 0.5)"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "screen_click",
        "description": "Click at screen coordinates with visible cursor movement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "enum": ["left", "right", "middle"]},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "screen_type",
        "description": "Type text via keyboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "interval": {"type": "number"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "screen_key_press",
        "description": "Press keyboard keys (e.g., 'enter', 'ctrl+a', 'tab').",
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {"type": "string"},
            },
            "required": ["keys"],
        },
    },
    {
        "name": "screen_search_human",
        "description": "Option 1 (preferred): Human-like search with visible cursor movement and keyboard typing in browser search/address bar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "app": {"type": "string", "enum": ["brave", "chrome", "firefox", "edge"]},
                "interval": {"type": "number", "description": "Typing delay per character"},
                "fallback_to_url": {"type": "boolean", "description": "If true, fallback to direct URL search on failure"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "screen_search_web",
        "description": "Option 2 (fallback): Open browser directly on a Google search results page for the query when human-like search fails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "app": {"type": "string", "enum": ["brave", "chrome", "firefox", "edge"]},
            },
            "required": ["query"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Capture a full screenshot of the screen to see current state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
            },
            "required": [],
        },
    },
]
