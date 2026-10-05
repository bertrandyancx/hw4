"""Small append-only audit trail for sanitized agent-loop activity."""
import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_PATH = Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"


def record(tool_name: str | None, short_args: str, short_result: str, stop_reason: str | None = None) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8")) if AUDIT_PATH.exists() else []
        if not isinstance(existing, list):
            existing = []
    except json.JSONDecodeError:
        existing = []
    existing.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "short_args": short_args[:240],
        "short_result": short_result[:300],
        "stop_reason": stop_reason,
    })
    AUDIT_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
