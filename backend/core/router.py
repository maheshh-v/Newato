"""
ARIA Task Router
Classifies incoming task descriptions into task types.
Uses a fast heuristic pass to avoid an extra LLM call.
"""
import re
from utils.logger import get_logger

logger = get_logger("aria.router")

_WEB_PATTERNS = [
    r"\b(search|find|look up|browse|visit|scrape|extract|google|navigate|website|webpage|url|http)\b",
    r"\b(research|read|download|fetch|crawl|monitor)\b",
]

_CODE_PATTERNS = [
    r"\b(write|create|generate|build|code|script|program|file|folder|directory)\b",
    r"\b(python|javascript|html|css|json|csv|markdown|text)\b",
]

_API_PATTERNS = [
    r"\b(api|request|post|get|webhook|endpoint|json|rest|graphql)\b",
    r"\b(send|call|fetch|query)\b",
]


def classify_task(description: str) -> str:
    """
    Classify a task description into one of: web | code | api | screen.
    Returns the most likely type based on keyword heuristics.
    """
    desc_lower = description.lower()

    web_score = sum(
        1 for p in _WEB_PATTERNS if re.search(p, desc_lower)
    )
    code_score = sum(
        1 for p in _CODE_PATTERNS if re.search(p, desc_lower)
    )
    api_score = sum(
        1 for p in _API_PATTERNS if re.search(p, desc_lower)
    )

    scores = {"web": web_score, "code": code_score, "api": api_score}
    best = max(scores, key=lambda k: scores[k])

    if scores[best] == 0:
        # Default: most tasks need web access
        result = "web"
    else:
        result = best

    logger.info("Task classified", description=description[:60], type=result, scores=scores)
    return result
