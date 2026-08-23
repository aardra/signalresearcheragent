"""Dossier Compiler — Agent 3 in the multi-agent lead generation framework.

Receives the scored and tiered output for a batch of companies and produces
a single polished executive report in markdown.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from memory_config import build_shared_memory
from output_logger import log_stage_output, output_log_session
from scoring_engine import format_batch_scoring_section
from models import (
    BatchResult,
    EvaluatedCompany,
    ScoringEngineOutput,
    Signal,
)


def build_batch_result(
    scored_outputs: List[ScoringEngineOutput],
) -> BatchResult:
    """Convert a list of ScoringEngineOutput into a BatchResult for Agent 3."""
    companies = []
    for so in scored_outputs:
        companies.append(
            EvaluatedCompany(
                name=so.company_name,
                industry=so.industry,
                headcount=so.headcount,
                tier=so.tier_assignment.tier,
                confidence_in_tier=so.tier_assignment.confidence_in_tier,
                flag_for_review=so.tier_assignment.flag_for_review,
                flag_reason=so.tier_assignment.flag_reason,
                reason=so.tier_assignment.reason,
                primary_signal_used=so.tier_assignment.primary_signal_used,
                scoring=so.scoring,
                signals=so.signals,
                data_sparse=so.data_sparse,
            )
        )
    return BatchResult(
        companies=companies,
        batch_size=len(companies),
        batch_date=datetime.now().strftime("%Y-%m-%d"),
    )


def _format_batch_text(batch: BatchResult) -> str:
    """Format the full batch into the text block the dossier prompt expects."""
    parts = []
    for c in batch.companies:
        parts.append("---")
        parts.append(f"Company:          {c.name}")
        parts.append(f"Industry:         {c.industry}")
        parts.append(f"Headcount:        {c.headcount}")
        parts.append(f"Tier:             {c.tier.value}")
        parts.append(f"Confidence:       {c.confidence_in_tier.value}")
        flag_str = "yes" if c.flag_for_review else "no"
        if c.flag_for_review and c.flag_reason:
            flag_str += f" — {c.flag_reason}"
        parts.append(f"Flag for review:  {flag_str}")
        parts.append(f"Tier reason:      {c.reason}")
        parts.append(f"Primary signal:   {c.primary_signal_used}")
        parts.append(f"Score breakdown:  regulatory={c.scoring.regulatory_score}/40, "
                      f"supporting={c.scoring.supporting_score}/30, "
                      f"icp_fit={c.scoring.icp_fit_score}/20, "
                      f"freshness={c.scoring.recency_score}/10, "
                      f"total={c.scoring.total_score}/100")
        parts.append(f"Data sparse:      {'yes' if c.data_sparse else 'no'}")
        parts.append("")
        parts.append("Signals:")
        if c.signals:
            for s in c.signals:
                parts.append(
                    f"  [{s.type.value}] {s.summary} ({s.date}, "
                    f"{s.confidence.value} confidence)"
                )
                parts.append(f"  Source: {s.source_url}")
        else:
            parts.append("  None found")
        parts.append("")

    return "\n".join(parts)


def _append_scoring_section(report: str, scored_outputs: List[ScoringEngineOutput]) -> str:
    """Append Agent 2 tabular scoring as a separate dossier section."""
    scoring_section = format_batch_scoring_section(scored_outputs)
    if not scoring_section:
        return report
    report = report.rstrip()
    return f"{report}\n\n---\n\n{scoring_section}"


@CrewBase
class DossierCompilerCrew:
    """Single-agent crew that produces the executive report."""

    agents_config = "config/dossier_agents.yaml"
    tasks_config = "config/dossier_tasks.yaml"

    def _shared_memory(self):
        if not hasattr(self, "_memory_instance"):
            self._memory_instance = build_shared_memory("dossier_compiler")
        return self._memory_instance

    def _compiler_llm(self) -> LLM:
        return LLM(
            model=os.getenv("DOSSIER_MODEL", "openai/gpt-5.1"),
            temperature=0.2,  # Slight creativity for report writing
            max_completion_tokens=8000,
        )

    @agent
    def dossier_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config["dossier_compiler"],
            llm=self._compiler_llm(),
            tools=[],
            memory=self._shared_memory().scope("agents/dossier_compiler"),
            max_iter=5,
            max_retry_limit=1,
            verbose=True,
        )

    @task
    def compile_dossier(self) -> Task:
        return Task(
            config=self.tasks_config["compile_dossier"],
            output_file="output/dossier_report.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=self._shared_memory(),
            name="dossier_compiler",
            verbose=True,
        )


# ── Runner ──────────────────────────────────────────────────────────────


def run_dossier_compiler(
    scored_outputs: List[ScoringEngineOutput],
) -> str:
    """Compile the executive dossier from all scored companies.

    Returns:
        The markdown report as a string.
    """
    with output_log_session(
        label="dossier_compiler",
        meta={"company_count": len(scored_outputs)},
    ):
        batch = build_batch_result(scored_outputs)
        batch_text = _format_batch_text(batch)

        today = datetime.now()
        re_evaluate_tier2 = (today + timedelta(days=30)).strftime("%d %B %Y")
        re_evaluate_tier3 = (today + timedelta(days=60)).strftime("%d %B %Y")

        inputs = {
            "batch_size": str(batch.batch_size),
            "batch_date": today.strftime("%d %B %Y"),
            "batch_text": batch_text,
            "re_evaluate_tier2": re_evaluate_tier2,
            "re_evaluate_tier3": re_evaluate_tier3,
        }

        compiler_crew = DossierCompilerCrew()
        result = compiler_crew.crew().kickoff(inputs=inputs)

        report = result.raw if hasattr(result, "raw") else str(result)
        report = _append_scoring_section(report, scored_outputs)
        log_stage_output(
            "agent_3",
            "dossier_compiler",
            {"report_length": len(report), "batch_size": batch.batch_size},
            extra={"report_preview": report[:2000]},
        )
        return report
