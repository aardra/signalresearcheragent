"""Outreach Drafter — Agent 4 in the multi-agent lead generation framework.

Receives the compiled dossier report from Agent 3 and drafts personalised outreach
messages for every Tier 1 and Tier 2 company.
"""

from __future__ import annotations

import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from memory_config import build_shared_memory
from output_logger import log_stage_output, output_log_session

DEFAULT_PRODUCT = (
    "An AI-powered, integrated GRC (Governance, Risk & Compliance) "
    "platform covering whistleblowing/incident reporting, policy management, "
    "compliance training, third-party risk screening, and regulatory change "
    "management in a single unified system."
)
DEFAULT_BUYER_TITLE = (
    "Chief Compliance Officer (CCO), Chief Ethics & Compliance Officer, "
    "VP of Risk, or General Counsel"
)
DEFAULT_TARGET_INDUSTRY = (
    "Cross-industry (Financial Services, Healthcare, Energy, Manufacturing, "
    "and other heavily regulated multinational sectors)"
)
DEFAULT_CORE_PAIN = (
    "When GRC data lives in disconnected systems, risks get missed, reporting "
    "slows down, and the value of compliance to the bottom line gets obscured. "
    "Compliance leaders need a complete, auditable picture of enterprise risk "
    "without stitching together data from siloed tools."
)
DEFAULT_KEY_OUTCOMES = (
    "50% reduction in audit prep time, real-time compliance monitoring across "
    "speak-up programs and policy libraries, automated evidence collection for "
    "regulatory remediation"
)


def _outreach_inputs(dossier_report: str) -> dict[str, str]:
    """Build template inputs for the outreach drafter task."""
    return {
        "dossier_report": dossier_report,
        "product": os.getenv("OUTREACH_PRODUCT", DEFAULT_PRODUCT),
        "buyer_title": os.getenv("OUTREACH_BUYER_TITLE", DEFAULT_BUYER_TITLE),
        "target_industry": os.getenv("OUTREACH_TARGET_INDUSTRY", DEFAULT_TARGET_INDUSTRY),
        "core_pain": os.getenv("OUTREACH_CORE_PAIN", DEFAULT_CORE_PAIN),
        "key_outcomes": os.getenv("OUTREACH_KEY_OUTCOMES", DEFAULT_KEY_OUTCOMES),
        "sender_first_name": os.getenv("OUTREACH_SENDER_FIRST_NAME", "Alex"),
        "sender_title": os.getenv(
            "OUTREACH_SENDER_TITLE", "Enterprise Account Executive"
        ),
        "sender_company": os.getenv("OUTREACH_SENDER_COMPANY", "Acme GRC"),
    }


@CrewBase
class OutreachDrafterCrew:
    """Single-agent crew that drafts Tier 1 and Tier 2 outreach messages."""

    agents_config = "config/outreach_agents.yaml"
    tasks_config = "config/outreach_tasks.yaml"

    def _shared_memory(self):
        if not hasattr(self, "_memory_instance"):
            self._memory_instance = build_shared_memory("outreach_drafter")
        return self._memory_instance

    def _drafter_llm(self) -> LLM:
        return LLM(
            model=os.getenv("OUTREACH_MODEL", "openai/gpt-5.1"),
            temperature=0.3,
            max_completion_tokens=8000,
        )

    @agent
    def outreach_drafter(self) -> Agent:
        return Agent(
            config=self.agents_config["outreach_drafter"],
            llm=self._drafter_llm(),
            tools=[],
            memory=self._shared_memory().scope("agents/outreach_drafter"),
            max_iter=5,
            max_retry_limit=1,
            verbose=True,
        )

    @task
    def draft_outreach(self) -> Task:
        return Task(
            config=self.tasks_config["draft_outreach"],
            output_file="output/outreach_messages.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=self._shared_memory(),
            name="outreach_drafter",
            verbose=True,
        )


def run_outreach_drafter(dossier_report: str) -> str:
    """Draft outreach messages from the compiled dossier report.

    Returns:
        Markdown document with one message per Tier 1 and Tier 2 company.
    """
    with output_log_session(
        label="outreach_drafter",
        meta={"dossier_length": len(dossier_report)},
    ):
        inputs = _outreach_inputs(dossier_report)

        drafter_crew = OutreachDrafterCrew()
        result = drafter_crew.crew().kickoff(inputs=inputs)

        outreach = result.raw if hasattr(result, "raw") else str(result)
        log_stage_output(
            "agent_4",
            "outreach_drafter",
            {"message_length": len(outreach)},
            extra={"outreach_preview": outreach[:2000]},
        )
        return outreach


def run_outreach_from_file(
    dossier_path: str = "output/dossier_report.md",
) -> str:
    """Load an existing dossier report and draft outreach messages."""
    with open(dossier_path) as f:
        dossier_report = f.read()
    return run_outreach_drafter(dossier_report)
