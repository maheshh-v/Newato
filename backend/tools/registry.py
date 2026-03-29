"""
ARIA Tool Registry
Defines all tools available to the agent and sent to the Claude API.
"""

TOOL_REGISTRY: list[dict] = [
    {
        "name": "browser_navigate",
        "description": "Navigate the browser to a URL. Use this to open websites, go to specific pages, or follow links. Always use full URLs including https://",
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
        "description": "Click an element on the current page. Prefer CSS selectors. If selector fails, try visible text content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector or visible text of the element to click",
                },
                "method": {
                    "type": "string",
                    "enum": ["css", "text", "xpath"],
                    "description": "How to locate the element",
                },
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field or textarea on the current page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "text": {"type": "string"},
                "clear_first": {
                    "type": "boolean",
                    "description": "Clear existing content before typing",
                    "default": True,
                },
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "browser_extract",
        "description": "Extract text content from the current page. Use selector to target specific sections, or leave empty for full page text. Returns cleaned text, not raw HTML.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector to target. Leave empty for full page.",
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Also return all links found",
                    "default": False,
                },
            },
            "required": [],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page state. Returns base64 image. Use when you need to visually verify what the page looks like.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the page up or down.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down"]},
                "amount": {
                    "type": "integer",
                    "description": "Pixels to scroll",
                    "default": 500,
                },
            },
            "required": ["direction"],
        },
    },
    {
        "name": "browser_wait",
        "description": "Wait for an element to appear on the page. Use after clicking buttons that trigger loading.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
                "timeout_ms": {"type": "integer", "default": 5000},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "run_python",
        "description": "Execute a Python code snippet and return its stdout output. Use for data processing, calculations, API calls, or any logic that doesn't require browser interaction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Valid Python code to execute"}
            },
            "required": ["code"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Files are saved to the ARIA output directory. Use for saving results, creating code files, writing reports.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename with extension. Do not include path.",
                },
                "content": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "default": "write",
                },
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
        "description": "Save important information to your working memory for this task. Use to track progress, store intermediate results, remember what you've done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key"},
                "value": {"type": "string", "description": "Value to store"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "task_complete",
        "description": "Call this ONLY when the task is fully completed. Provide a clear summary of what was accomplished and what output was produced.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "What was done and what output was produced",
                },
                "output_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files created",
                },
            },
            "required": ["summary"],
        },
    },
    {
        "name": "task_failed",
        "description": "Call this if the task cannot be completed after trying multiple approaches. Explain clearly what was attempted and why it failed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "attempted": {
                    "type": "string",
                    "description": "What approaches were tried",
                },
            },
            "required": ["reason"],
        },
    },
]
