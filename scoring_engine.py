"""Scoring Engine — Agent 2 in the multi-agent lead generation framework.

Two-agent architecture using CrewAI:
  Agent A (Signal Scorer):  Quantitative scoring of signal strength (0-100).
  Agent B (Tier Prioritiser): Maps score + context to a sales tier with reasoning.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from memory_config import build_shared_memory
from output_logger import log_stage_output, output_log_session
from models import (
    Confidence,
    ScoringEngineOutput,
    ScoringOutput,
    Signal,
    SignalResearchOutput,
    SignalType,
    Tier,
    TierAssignment,
)


SCORING_MAX_RETRIES = int(os.getenv("SCORING_MAX_RETRIES", "2"))
SCORER_MAX_TOKENS = int(os.getenv("SCORER_MAX_TOKENS", "2048"))


class ScoringParseError(Exception):
    """Agent 2 could not produce parseable score output after retries."""

    def __init__(
        self,
        company_name: str,
        message: str,
        *,
        attempts: int,
        raw_preview: str | None = None,
    ) -> None:
        self.company_name = company_name
        self.attempts = attempts
        self.raw_preview = raw_preview
        detail = f"{company_name}: {message} (after {attempts} attempt(s))"
        if raw_preview:
            detail += f"\nRaw output preview: {raw_preview[:500]}"
        super().__init__(detail)


def _format_signals_text(signals: List[Signal]) -> str:
    """Format signal objects into readable text for prompt injection."""
    if not signals:
        return "No signals found."

    # Separate regulatory from supporting
    regulatory = [s for s in signals if s.type == SignalType.REGULATORY_ACTION]
    supporting = [s for s in signals if s.type != SignalType.REGULATORY_ACTION]

    parts = []

    parts.append("### Primary signal (regulatory)")
    if regulatory:
        for s in regulatory:
            parts.append(f"Type: {s.type.value}")
            parts.append(f"Summary: {s.summary}")
            parts.append(f"Source: {s.source_url}")
            parts.append(f"Date: {s.date}")
            parts.append(f"Confidence: {s.confidence.value}")
            parts.append(f"Excerpt: {s.raw_excerpt}")
            parts.append("")
    else:
        parts.append("None found")
        parts.append("")

    parts.append("### Supporting signals")
    if supporting:
        for s in supporting:
            parts.append(
                f"- [{s.type.value}] {s.summary} ({s.date}, "
                f"{s.confidence.value} confidence)"
            )
    else:
        parts.append("- None found")

    return "\n".join(parts)


def format_company_scoring_table(output: ScoringEngineOutput) -> str:
    """Render one company's Agent 2 scores as markdown tables (verbatim from structured output)."""
    score = output.scoring
    tier = output.tier_assignment
    flag = " ⚠" if tier.flag_for_review else ""

    lines = [
        f"### {output.company_name}",
        "",
        f"Industry: {output.industry} | Headcount: {output.headcount}",
        "",
        "| Dimension | Score | Max |",
        "|-----------|------:|----:|",
        f"| Regulatory signal strength | {score.regulatory_score} | 40 |",
        f"| Supporting signal reinforcement | {score.supporting_score} | 30 |",
        f"| ICP fit | {score.icp_fit_score} | 20 |",
        f"| Signal freshness | {score.recency_score} | 10 |",
        f"| **Total** | **{score.total_score}** | **100** |",
        "",
        "| Tier assignment | Value |",
        "|-----------------|-------|",
        f"| Tier | {tier.tier.value}{flag} |",
        f"| Primary signal used | {tier.primary_signal_used} |",
        f"| Confidence in tier | {tier.confidence_in_tier.value} |",
        f"| Flag for review | {'yes' if tier.flag_for_review else 'no'} |",
        "",
        f"**Scoring rationale:** {score.scoring_rationale}",
        "",
        f"**Tier reason:** {tier.reason}",
    ]
    if tier.flag_for_review and tier.flag_reason:
        lines.extend(["", f"**Flag reason:** {tier.flag_reason}"])
    lines.append("")
    return "\n".join(lines)


def format_batch_scoring_section(scored_outputs: List[ScoringEngineOutput]) -> str:
    """Render the full Agent 2 scoring breakdown for all companies in a batch."""
    if not scored_outputs:
        return ""

    tier_order = {"Tier 1": 0, "Tier 2": 1, "Tier 3": 2}
    sorted_outputs = sorted(
        scored_outputs,
        key=lambda o: (
            tier_order.get(o.tier_assignment.tier.value, 99),
            -o.scoring.total_score,
            o.company_name,
        ),
    )

    parts = [
        "## AGENT 2 SCORING BREAKDOWN",
        "",
        "Tabular scores copied verbatim from the Scoring Engine (Agent 2). "
        "These values are not rewritten by the Dossier Compiler.",
        "",
        "### Batch scoring summary",
        "",
        "| Company | Regulatory (/40) | Supporting (/30) | ICP Fit (/20) | "
        "Freshness (/10) | Total (/100) | Tier | Primary Signal |",
        "|---------|-----------------:|-----------------:|--------------:|"
        "----------------:|-------------:|------|----------------|",
    ]

    for output in sorted_outputs:
        score = output.scoring
        tier = output.tier_assignment
        parts.append(
            f"| {output.company_name} | {score.regulatory_score} | "
            f"{score.supporting_score} | {score.icp_fit_score} | "
            f"{score.recency_score} | {score.total_score} | "
            f"{tier.tier.value} | {tier.primary_signal_used} |"
        )

    parts.extend(["", "### Per-company scoring detail", ""])
    for output in sorted_outputs:
        parts.append(format_company_scoring_table(output))

    return "\n".join(parts).rstrip() + "\n"


@CrewBase
class ScoringEngineCrew:
    """Two-agent scoring crew: scorer → prioritiser."""

    agents_config = "config/scoring_agents.yaml"
    tasks_config = "config/scoring_tasks.yaml"

    def _shared_memory(self):
        if not hasattr(self, "_memory_instance"):
            self._memory_instance = build_shared_memory("scoring_engine")
        return self._memory_instance

    # ── LLMs ────────────────────────────────────────────────────────────

    def _scorer_llm(self) -> LLM:
        return LLM(
            model=os.getenv("SCORER_MODEL", "openai/gpt-5.1"),
            temperature=0,
            max_tokens=SCORER_MAX_TOKENS,
        )

    def _prioritiser_llm(self) -> LLM:
        return LLM(
            model=os.getenv("PRIORITISER_MODEL", "openai/gpt-5.1"),
            temperature=0,
            max_tokens=1000,
        )

    # ── Agents ──────────────────────────────────────────────────────────

    @agent
    def signal_scorer(self) -> Agent:
        return Agent(
            config=self.agents_config["signal_scorer"],
            llm=self._scorer_llm(),
            tools=[],
            memory=self._shared_memory().scope("agents/signal_scorer"),
            max_iter=5,
            max_retry_limit=1,
            verbose=True,
        )

    @agent
    def tier_prioritiser(self) -> Agent:
        return Agent(
            config=self.agents_config["tier_prioritiser"],
            llm=self._prioritiser_llm(),
            tools=[],
            memory=self._shared_memory().scope("agents/tier_prioritiser"),
            max_iter=5,
            max_retry_limit=1,
            verbose=True,
        )

    # ── Tasks ───────────────────────────────────────────────────────────

    @task
    def score_signals(self) -> Task:
        return Task(
            config=self.tasks_config["score_signals"],
            output_json=ScoringOutput,
        )

    @task
    def assign_tier(self) -> Task:
        return Task(
            config=self.tasks_config["assign_tier"],
            context=[self.score_signals()],
            output_json=TierAssignment,
        )

    # ── Crew ────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=self._shared_memory(),
            name="scoring_engine",
            verbose=True,
        )


# ── Runner ──────────────────────────────────────────────────────────────


def run_scoring_engine(
    company_input: Dict[str, Any],
    signal_output: SignalResearchOutput,
) -> ScoringEngineOutput:
    """Run the scoring pipeline on signals from Agent 1."""
    company_name = company_input["company_name"]

    with output_log_session(
        label=f"scoring_engine:{company_name}",
        meta={"company": company_name},
    ):
        return _run_scoring_engine_impl(company_input, signal_output)


def _run_scoring_engine_impl(
    company_input: Dict[str, Any],
    signal_output: SignalResearchOutput,
) -> ScoringEngineOutput:
    """Internal implementation for scoring."""
    company_name = company_input["company_name"]
    signals_text = _format_signals_text(signal_output.signals)
    inputs = {
        "company_name": company_name,
        "industry": company_input["industry"],
        "headcount": str(company_input.get("headcount", "unknown")),
        "signals_text": signals_text,
        "scoring_text": "",
    }

    last_raw: str | None = None
    max_attempts = SCORING_MAX_RETRIES + 1

    for attempt in range(1, max_attempts + 1):
        try:
            output, last_raw = _run_scoring_crew_once(
                company_input, signal_output, inputs
            )
            return output
        except ScoringParseError as exc:
            last_raw = exc.raw_preview
            if attempt < max_attempts:
                print(
                    f"  Agent 2 parse failed for {company_name} "
                    f"(attempt {attempt}/{max_attempts}) — retrying scoring crew..."
                )
                continue
            raise ScoringParseError(
                company_name,
                "Scoring output could not be parsed",
                attempts=max_attempts,
                raw_preview=last_raw,
            ) from exc

    raise ScoringParseError(
        company_name,
        "Scoring output could not be parsed",
        attempts=max_attempts,
        raw_preview=last_raw,
    )


def _run_scoring_crew_once(
    company_input: Dict[str, Any],
    signal_output: SignalResearchOutput,
    inputs: Dict[str, str],
) -> tuple[ScoringEngineOutput, str | None]:
    """Run one scoring crew kickoff and parse structured outputs."""
    scoring_crew = ScoringEngineCrew()
    crew = scoring_crew.crew()
    result = crew.kickoff(inputs=inputs)

    score_task = _find_crew_task(crew, "score_signals")
    raw_preview = _task_raw_output(score_task) or (
        result.raw if hasattr(result, "raw") else str(result)
    )

    scoring = _parse_scoring_output(score_task, company_input["company_name"])
    tier = _parse_tier_output(result, company_input["company_name"])

    output = ScoringEngineOutput(
        company_name=company_input["company_name"],
        industry=company_input["industry"],
        headcount=company_input.get("headcount", "unknown"),
        scoring=scoring,
        tier_assignment=tier,
        signals_evaluated=signal_output.signal_count,
        data_sparse=signal_output.data_sparse,
        signals=signal_output.signals,
    )
    log_stage_output(
        "agent_2",
        "scoring_engine",
        output,
        company=company_input["company_name"],
    )
    return output, raw_preview


def _find_crew_task(crew: Crew, task_name: str) -> Task | None:
    """Return the executed task from a crew instance by config key / name."""
    for task in crew.tasks:
        name = getattr(task, "name", None) or getattr(task, "description", "")
        if task_name in str(name):
            return task
    return None


def _task_raw_output(task_obj: Task | None) -> str | None:
    if task_obj is None or not hasattr(task_obj, "output") or task_obj.output is None:
        return None
    return task_obj.output.raw if hasattr(task_obj.output, "raw") else str(task_obj.output)


def _parse_scoring_output(
    task_obj: Task | None,
    company_name: str,
) -> ScoringOutput:
    """Extract ScoringOutput from the score_signals task."""
    raw_preview: str | None = None

    if task_obj is not None and hasattr(task_obj, "output") and task_obj.output is not None:
        if hasattr(task_obj.output, "pydantic") and task_obj.output.pydantic:
            obj = task_obj.output.pydantic
            if isinstance(obj, ScoringOutput):
                return obj
            return ScoringOutput(**obj.model_dump())

        if hasattr(task_obj.output, "json_dict") and task_obj.output.json_dict:
            return ScoringOutput(**task_obj.output.json_dict)

        raw = task_obj.output.raw if hasattr(task_obj.output, "raw") else str(task_obj.output)
        raw_preview = raw
        parsed = _safe_json_parse(raw)
        if parsed:
            return ScoringOutput(**parsed)

    raise ScoringParseError(
        company_name,
        "score_signals task returned no parseable ScoringOutput JSON",
        attempts=1,
        raw_preview=raw_preview,
    )


def _parse_tier_output(result, company_name: str) -> TierAssignment:
    """Extract TierAssignment from crew result."""
    raw_preview: str | None = None

    if hasattr(result, "pydantic") and result.pydantic is not None:
        obj = result.pydantic
        if isinstance(obj, TierAssignment):
            return obj
        return TierAssignment(**obj.model_dump())

    raw = result.raw if hasattr(result, "raw") else str(result)
    raw_preview = raw
    parsed = _safe_json_parse(raw)
    if parsed:
        return TierAssignment(**parsed)

    raise ScoringParseError(
        company_name,
        "assign_tier task returned no parseable TierAssignment JSON",
        attempts=1,
        raw_preview=raw_preview,
    )


def _safe_json_parse(text: str) -> Optional[Dict]:
    """Try to parse JSON from text, handling markdown fences and trailing JSON."""
    import re

    if not text or not isinstance(text, str):
        return None

    stripped = text.strip()

    # Direct parse
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        pass

    # Markdown fence
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if match:
        parsed = _loads_json_object(match.group(1))
        if parsed:
            return parsed

    # Last JSON object embedded in prose (common when the model narrates first)
    parsed = _extract_last_json_object(stripped)
    if parsed:
        return parsed

    return None


def _loads_json_object(text: str) -> Optional[Dict]:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_last_json_object(text: str) -> Optional[Dict]:
    """Find and parse the last top-level {...} block in mixed LLM output."""
    start = text.rfind("{")
    while start != -1:
        candidate = text[start:]
        depth = 0
        for idx, char in enumerate(candidate):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    parsed = _loads_json_object(candidate[: idx + 1])
                    if parsed and _looks_like_scoring_or_tier(parsed):
                        return parsed
                    break
        start = text.rfind("{", 0, start)
    return None


def _looks_like_scoring_or_tier(data: Dict) -> bool:
    scoring_keys = {
        "regulatory_score",
        "supporting_score",
        "icp_fit_score",
        "recency_score",
        "total_score",
    }
    tier_keys = {"tier", "reason", "primary_signal_used", "confidence_in_tier"}
    keys = set(data.keys())
    return bool(keys & scoring_keys or keys & tier_keys)
