"""Signal Researcher — Agent 1 in the multi-agent lead generation framework.

Two-stage architecture using CrewAI:
  Stage 1 (Retrieval): Web search for raw evidence using a frontier model.
  Stage 2 (Extraction): Extract, summarise, and validate structured signals.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from memory_config import build_shared_memory
from output_logger import log_stage_output, output_log_session
from models import (
    RAW_EXCERPT_MAX_CHARS,
    SUMMARY_MAX_CHARS,
    Confidence,
    ExtractSignalsOutput,
    Signal,
    SignalResearchOutput,
    SignalType,
)

SPARSE_THRESHOLD = int(os.getenv("SIGNAL_SPARSE_THRESHOLD", "2"))
MAX_RETRIES = int(os.getenv("SIGNAL_MAX_RETRIES", "2"))
STAGE2_MAX_TOKENS = int(os.getenv("STAGE2_MAX_TOKENS", "4096"))


@CrewBase
class SignalResearcherCrew:
    """Two-stage signal research crew for a single target company."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _shared_memory(self):
        """One persistent memory store; each agent gets its own scope slice."""
        if not hasattr(self, "_memory_instance"):
            self._memory_instance = build_shared_memory("signal_researcher")
        return self._memory_instance

    def _default_openai_model(self) -> str:
        model = os.getenv("OPENAI_MODEL", "gpt-5.1").strip()
        return model if model.startswith("openai/") else f"openai/{model}"

    def _retrieval_llm(self) -> LLM:
        return LLM(
            model=os.getenv("STAGE1_MODEL", self._default_openai_model()),
            temperature=0,
            max_tokens=2000,
        )

    def _extraction_llm(self) -> LLM:
        return LLM(
            model=os.getenv("STAGE2_MODEL", self._default_openai_model()),
            temperature=0,
            max_tokens=STAGE2_MAX_TOKENS,
        )

    @agent
    def signal_retriever(self) -> Agent:
        return Agent(
            config=self.agents_config["signal_retriever"],
            llm=self._retrieval_llm(),
            tools=[SerperDevTool()],
            memory=self._shared_memory().scope("agents/signal_retriever"),
            max_iter=15,
            max_retry_limit=2,
            verbose=True,
        )

    @agent
    def signal_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["signal_extractor"],
            llm=self._extraction_llm(),
            tools=[],
            memory=self._shared_memory().scope("agents/signal_extractor"),
            max_iter=5,
            max_retry_limit=1,
            verbose=True,
        )

    @task
    def retrieve_signals(self) -> Task:
        return Task(
            config=self.tasks_config["retrieve_signals"],
        )

    @task
    def extract_signals(self) -> Task:
        return Task(
            config=self.tasks_config["extract_signals"],
            context=[self.retrieve_signals()],
            output_json=ExtractSignalsOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=self._shared_memory(),
            name="signal_researcher",
            verbose=True,
        )


INFERENCE_WORDS = {"likely", "probably", "suggests", "implies", "may indicate"}


def apply_quality_gates(signals: List[Dict], current_date: str) -> List[Dict]:
    """Enforce quality gates G1–G9. Returns only passing signals."""
    cutoff = datetime.fromisoformat(current_date) - timedelta(days=365)
    valid_types = {t.value for t in SignalType}
    valid_confidences = {c.value for c in Confidence}
    passed = []

    for s in signals:
        if not s.get("source_url", "").startswith("https://"):
            continue
        date_str = s.get("date", "")
        if not date_str:
            continue
        try:
            if len(date_str) == 7:
                signal_date = datetime.strptime(date_str, "%Y-%m")
            else:
                signal_date = datetime.fromisoformat(date_str)
        except ValueError:
            continue
        if signal_date < cutoff:
            continue
        summary = s.get("summary", "")
        summary_lower = summary.lower()
        if any(w in summary_lower for w in INFERENCE_WORDS):
            continue
        if len(summary) > SUMMARY_MAX_CHARS:
            continue
        if s.get("type") not in valid_types:
            continue
        conf = s.get("confidence", "")
        if conf not in valid_confidences:
            continue
        excerpt = s.get("raw_excerpt", "")
        if len(excerpt) > RAW_EXCERPT_MAX_CHARS:
            continue
        if conf in ("High", "Medium") and not excerpt.strip():
            s["confidence"] = "Low"
        passed.append(s)

    return passed


def run_signal_researcher(company_input: Dict[str, Any]) -> SignalResearchOutput:
    """Run the full signal research pipeline for one company."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    company_name = company_input["company_name"]

    with output_log_session(
        label=f"signal_researcher:{company_name}",
        meta={"company": company_name},
    ):
        return _run_signal_researcher_impl(company_input, current_date)


def _run_signal_researcher_impl(
    company_input: Dict[str, Any],
    current_date: str,
) -> SignalResearchOutput:
    """Internal implementation for signal research."""

    inputs = {
        "company_name": company_input["company_name"],
        "industry": company_input["industry"],
        "headcount": str(company_input.get("headcount", "unknown")),
        "domain": company_input.get("domain") or "N/A",
        "linkedin_url": company_input.get("linkedin_url") or "N/A",
        "current_date": current_date,
    }

    research_crew = SignalResearcherCrew()
    retry_count = 0
    all_signals: List[Dict] = []
    search_log: List[str] = []

    result = research_crew.crew().kickoff(inputs=inputs)
    search_log.append(f"Pass 1 completed for {company_input['company_name']}")

    raw_signals = _parse_crew_output(result)
    validated = apply_quality_gates(raw_signals, current_date)
    all_signals = validated

    while len(all_signals) < SPARSE_THRESHOLD and retry_count < MAX_RETRIES:
        retry_count += 1
        search_log.append(f"Retry pass {retry_count} — broadening queries")

        retry_inputs = {**inputs}
        if retry_count == 1:
            retry_inputs["company_name"] = (
                f'{company_input["company_name"]} (broaden search: '
                f"drop site: filters, expand date range to 18 months)"
            )
        else:
            retry_inputs["company_name"] = (
                f'{company_input.get("domain", company_input["company_name"])} '
                f"(industry-level search for {company_input['industry']})"
            )

        retry_crew = SignalResearcherCrew()
        retry_result = retry_crew.crew().kickoff(inputs=retry_inputs)
        retry_signals = _parse_crew_output(retry_result)
        retry_validated = apply_quality_gates(retry_signals, current_date)

        existing_urls = {s["source_url"] for s in all_signals}
        for s in retry_validated:
            if s["source_url"] not in existing_urls:
                all_signals.append(s)

    data_sparse = len(all_signals) < SPARSE_THRESHOLD and retry_count >= MAX_RETRIES

    result_output = SignalResearchOutput(
        signals=[Signal(**s) for s in all_signals],
        signal_count=len(all_signals),
        data_sparse=data_sparse,
        retry_count=retry_count,
        search_log=search_log,
    )
    log_stage_output(
        "agent_1",
        "signal_researcher",
        result_output,
        company=company_input["company_name"],
    )
    return result_output


def _parse_crew_output(result) -> List[Dict]:
    """Extract signal dicts from crew output."""
    raw = result.raw if hasattr(result, "raw") else str(result)

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "signals" in parsed:
            return parsed["signals"]
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    import re

    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict) and "signals" in parsed:
                return parsed["signals"]
        except (json.JSONDecodeError, TypeError):
            pass

    if hasattr(result, "pydantic") and result.pydantic is not None:
        obj = result.pydantic
        if hasattr(obj, "signals"):
            return [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in obj.signals]

    return []
