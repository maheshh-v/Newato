"""
ARIA Database Models
Python dataclass representations of the database schema.
"""
from dataclasses import dataclass, field
from typing import Optional
import json
import time


@dataclass
class Task:
    id: str
    description: str
    status: str = "queued"          # queued | running | completed | failed
    task_type: Optional[str] = None  # web | code | api | screen
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    summary: Optional[str] = None
    error_reason: Optional[str] = None
    output_files: list[str] = field(default_factory=list)
    step_count: int = 0
    total_steps_estimate: int = 10

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "task_type": self.task_type,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "summary": self.summary,
            "error_reason": self.error_reason,
            "output_files": self.output_files,
            "step_count": self.step_count,
            "total_steps_estimate": self.total_steps_estimate,
        }

    @classmethod
    def from_row(cls, row) -> "Task":
        output_files = []
        if row["output_files"]:
            try:
                output_files = json.loads(row["output_files"])
            except json.JSONDecodeError:
                output_files = []
        return cls(
            id=row["id"],
            description=row["description"],
            status=row["status"],
            task_type=row["task_type"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            summary=row["summary"],
            error_reason=row["error_reason"],
            output_files=output_files,
            step_count=row["step_count"] or 0,
            total_steps_estimate=row["total_steps_estimate"] or 10,
        )


@dataclass
class Step:
    task_id: str
    step_number: int
    tool_name: str
    step_text: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    tool_input: Optional[str] = None   # JSON string
    tool_result: Optional[str] = None  # Truncated result
    screenshot_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "step_number": self.step_number,
            "tool_name": self.tool_name,
            "step_text": self.step_text,
            "timestamp": self.timestamp,
            "tool_input": self.tool_input,
            "tool_result": self.tool_result,
            "screenshot_path": self.screenshot_path,
        }
