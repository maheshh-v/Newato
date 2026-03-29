"""
ARIA Output Sanitizer
Cleans LLM output and provides safe code execution utilities.
"""
import re
from typing import Any


BLOCKED_IMPORTS = {
    "subprocess", "os.system", "eval", "exec", "__import__",
    "shutil.rmtree", "ctypes", "socket",
}

BLOCKED_PATTERNS = [
    r"os\.system\s*\(",
    r"subprocess\.(?:call|run|Popen|check_output)\s*\(.*shell\s*=\s*True",
    r"__import__\s*\(",
    r"eval\s*\(",
    r"exec\s*\(",
    r"open\s*\(.*['\"]w['\"].*\)\s*\.write",  # direct open() writes outside sandbox
]


def is_code_safe(code: str) -> tuple[bool, str]:
    """
    Check if Python code is safe to execute in the agent sandbox.
    Returns (is_safe, reason_if_unsafe).
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Blocked pattern detected: {pattern}"
    return True, ""


def truncate_result(text: str, max_chars: int = 2000) -> str:
    """Truncate tool result to avoid overwhelming the LLM context."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n... [truncated {len(text) - max_chars} chars] ...\n" + text[-half:]


def clean_llm_output(text: str) -> str:
    """Strip common LLM artifacts from output."""
    # Remove markdown code fences if the entire response is wrapped
    if text.startswith("```") and text.endswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    return text.strip()


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    safe = safe.strip(". ")
    return safe[:200] or "output"
