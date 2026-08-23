"""Append-only reference log for crew execution outputs.

Separate from CrewAI vector memory (LanceDB). Captures task and crew events
as they happen, plus structured pipeline results, to JSONL + markdown files.
"""

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crewai.events import crewai_event_bus
from crewai.events.types.crew_events import (
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
)
from crewai.events.types.task_events import TaskCompletedEvent, TaskFailedEvent

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_JSONL = PROJECT_ROOT / "output" / "crew_outputs.jsonl"
DEFAULT_MD = PROJECT_ROOT / "output" / "crew_outputs.md"

_lock = threading.Lock()
_session_depth = 0
_session_id: str | None = None
_jsonl_path: Path | None = None
_md_path: Path | None = None
_handlers_installed = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_paths() -> tuple[Path, Path]:
    jsonl = Path(os.getenv("CREW_OUTPUT_LOG", str(DEFAULT_JSONL)))
    md = Path(os.getenv("CREW_OUTPUT_MD", str(jsonl.with_suffix(".md"))))
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    return jsonl, md


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def _append_jsonl(record: dict[str, Any]) -> None:
    if _jsonl_path is None:
        return
    with _lock:
        with _jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")


def _append_md(section: str) -> None:
    if _md_path is None:
        return
    with _lock:
        with _md_path.open("a", encoding="utf-8") as f:
            f.write(section)
            if not section.endswith("\n"):
                f.write("\n")


def _write_record(event: str, payload: dict[str, Any]) -> None:
    record = {
        "timestamp": _utc_now(),
        "session_id": _session_id,
        "event": event,
        **payload,
    }
    _append_jsonl(record)


def log_stage_output(
    stage: str,
    name: str,
    output: Any,
    *,
    company: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Log a structured pipeline result (signals, scores, dossier metadata)."""
    if _session_depth == 0:
        return

    payload: dict[str, Any] = {
        "stage": stage,
        "name": name,
        "company": company,
        "output": _serialize(output),
    }
    if extra:
        payload["extra"] = _serialize(extra)
    _write_record("stage_output", payload)

    company_label = f" — {company}" if company else ""
    _append_md(
        f"\n## [{stage}] {name}{company_label}\n"
        f"_{_utc_now()}_\n\n"
        f"```json\n{json.dumps(payload['output'], indent=2, default=str, ensure_ascii=False)}\n```\n"
    )


def _on_crew_kickoff_started(_source: Any, event: CrewKickoffStartedEvent) -> None:
    _write_record(
        "crew_started",
        {
            "crew_name": event.crew_name,
            "inputs": _serialize(event.inputs or {}),
        },
    )
    _append_md(
        f"\n### Crew started: {event.crew_name or 'unknown'}\n"
        f"_{_utc_now()}_\n"
    )


def _on_crew_kickoff_completed(_source: Any, event: CrewKickoffCompletedEvent) -> None:
    raw = ""
    if event.output is not None:
        raw = getattr(event.output, "raw", None) or str(event.output)
    _write_record(
        "crew_completed",
        {
            "crew_name": event.crew_name,
            "total_tokens": event.total_tokens,
            "output_raw": raw,
        },
    )
    preview = raw[:2000] + ("..." if len(raw) > 2000 else "")
    _append_md(
        f"\n### Crew completed: {event.crew_name or 'unknown'}\n"
        f"_{_utc_now()}_\n\n"
        f"```\n{preview}\n```\n"
    )


def _on_crew_kickoff_failed(_source: Any, event: CrewKickoffFailedEvent) -> None:
    _write_record(
        "crew_failed",
        {"crew_name": event.crew_name, "error": event.error},
    )
    _append_md(
        f"\n### Crew failed: {event.crew_name or 'unknown'}\n"
        f"_{_utc_now()}_\n\n`{event.error}`\n"
    )


def _on_task_completed(_source: Any, event: TaskCompletedEvent) -> None:
    output = event.output
    raw = output.raw if output else ""
    json_dict = output.json_dict if output else None
    pydantic = None
    if output and output.pydantic is not None:
        pydantic = _serialize(output.pydantic)

    crew_name = getattr(_source, "name", None) if _source is not None else None

    _write_record(
        "task_completed",
        {
            "crew_name": crew_name,
            "task_name": event.task_name,
            "task_id": event.task_id,
            "agent": output.agent if output else None,
            "task_summary": output.summary if output else None,
            "output_raw": raw,
            "output_json": json_dict,
            "output_pydantic": pydantic,
        },
    )

    title = event.task_name or (output.summary if output else "task")
    agent = output.agent if output else "unknown agent"
    preview = raw[:1500] + ("..." if len(raw) > 1500 else "")
    _append_md(
        f"\n#### Task: {title}\n"
        f"Agent: {agent} | Crew: {crew_name or 'unknown'} | {_utc_now()}\n\n"
        f"```\n{preview}\n```\n"
    )


def _on_task_failed(_source: Any, event: TaskFailedEvent) -> None:
    crew_name = getattr(_source, "name", None) if _source is not None else None
    _write_record(
        "task_failed",
        {
            "crew_name": crew_name,
            "task_name": event.task_name,
            "task_id": event.task_id,
            "error": event.error,
        },
    )
    _append_md(
        f"\n#### Task failed: {event.task_name or 'unknown'}\n"
        f"Crew: {crew_name or 'unknown'} | {_utc_now()}\n\n`{event.error}`\n"
    )


def _install_handlers() -> None:
    global _handlers_installed
    if _handlers_installed:
        return
    crewai_event_bus.on(CrewKickoffStartedEvent)(_on_crew_kickoff_started)
    crewai_event_bus.on(CrewKickoffCompletedEvent)(_on_crew_kickoff_completed)
    crewai_event_bus.on(CrewKickoffFailedEvent)(_on_crew_kickoff_failed)
    crewai_event_bus.on(TaskCompletedEvent)(_on_task_completed)
    crewai_event_bus.on(TaskFailedEvent)(_on_task_failed)
    _handlers_installed = True


@contextmanager
def output_log_session(*, label: str = "run", meta: dict[str, Any] | None = None):
    """Start (or nest) an output logging session for crew execution."""
    global _session_depth, _session_id, _jsonl_path, _md_path

    _session_depth += 1
    owns_session = _session_depth == 1

    if owns_session:
        _session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        _jsonl_path, _md_path = _resolve_paths()
        _install_handlers()
        header = {
            "label": label,
            "meta": _serialize(meta or {}),
            "jsonl_path": str(_jsonl_path),
            "md_path": str(_md_path),
        }
        _write_record("session_start", header)
        _append_md(
            f"# Crew run log — {label}\n"
            f"Session: {_session_id}\n"
            f"Started: {_utc_now()}\n"
        )

    try:
        yield _session_id
    finally:
        if owns_session:
            _write_record("session_end", {"label": label})
            _append_md(f"\n---\nSession ended: {_utc_now()}\n")
            _session_id = None
            _jsonl_path = None
            _md_path = None
        _session_depth -= 1
