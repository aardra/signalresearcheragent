"""Shared CrewAI memory configuration for multi-agent crews."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from crewai.memory.unified_memory import Memory

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_MEMORY_DIR = PROJECT_ROOT / ".crewai" / "memory"
DEFAULT_ROOT_SCOPE = "/crew/pipeline"


def build_shared_memory(crew_name: str = "pipeline") -> Memory:
    """Create persistent crew memory backed by LanceDB on disk.

    Args:
        crew_name: Logical crew name used as the root scope.
                   Each crew gets its own memory partition so agents
                   across crews (signal_researcher, scoring_engine,
                   dossier_compiler) can share context.
    """
    storage_path = Path(os.getenv("CREW_MEMORY_STORAGE", str(DEFAULT_MEMORY_DIR)))
    storage_path.mkdir(parents=True, exist_ok=True)

    memory_llm = (
        os.getenv("MEMORY_LLM_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
        or "gpt-5.1"
    )

    root_scope = f"/crew/{crew_name}"

    kwargs: dict[str, Any] = {
        "storage": str(storage_path),
        "root_scope": root_scope,
        "llm": memory_llm,
    }

    embedder_provider = os.getenv("MEMORY_EMBEDDER_PROVIDER", "").strip()
    if embedder_provider:
        embedder_model = os.getenv("MEMORY_EMBEDDER_MODEL", "").strip()
        config: dict[str, Any] = {}
        if embedder_model:
            config["model"] = embedder_model
        kwargs["embedder"] = {"provider": embedder_provider, "config": config}

    return Memory(**kwargs)
