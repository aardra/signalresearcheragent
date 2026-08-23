"""Pydantic schemas for the Signal Researcher agent (Agent 1)."""

from __future__ import annotations

import os
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field

SUMMARY_MAX_CHARS = int(os.getenv("SIGNAL_SUMMARY_MAX_CHARS", "280"))
RAW_EXCERPT_MAX_CHARS = int(os.getenv("SIGNAL_EXCERPT_MAX_CHARS", "400"))


class SignalType(str, Enum):
    REGULATORY_ACTION = "regulatory_action"
    HEADCOUNT_GROWTH = "headcount_growth"
    MA_FUNDING = "ma_funding"
    LEADERSHIP_CHANGE = "leadership_change"
    TECH_PROCUREMENT = "tech_procurement"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CompanyInput(BaseModel):
    company_name: str
    industry: str
    headcount: Union[str, int]
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None


class Signal(BaseModel):
    type: SignalType
    summary: str = Field(
        max_length=SUMMARY_MAX_CHARS,
        description=f"Factual summary of what the source says. Max {SUMMARY_MAX_CHARS} characters. No inference.",
    )
    source_url: str = Field(description="Full URL. Must be accessible.")
    date: str = Field(description="ISO 8601: YYYY-MM-DD or YYYY-MM")
    confidence: Confidence
    raw_excerpt: str = Field(
        default="",
        max_length=RAW_EXCERPT_MAX_CHARS,
        description=f"Verbatim excerpt from source, max {RAW_EXCERPT_MAX_CHARS} characters. Required for High/Medium.",
    )


class ExtractSignalsOutput(BaseModel):
    """Slim schema for the extract_signals CrewAI task (avoids oversized JSON output)."""

    signals: List[Signal] = Field(default_factory=list)
    signal_count: int = 0


class SignalResearchOutput(BaseModel):
    signals: List[Signal] = Field(default_factory=list)
    signal_count: int = 0
    data_sparse: bool = False
    retry_count: int = 0
    search_log: List[str] = Field(default_factory=list)


# ── Agent 2: Scoring & Prioritisation ──────────────────────────────────


class Tier(str, Enum):
    TIER_1 = "Tier 1"
    TIER_2 = "Tier 2"
    TIER_3 = "Tier 3"


class ScoringOutput(BaseModel):
    """Output of the scoring task — raw score breakdown per signal."""

    regulatory_score: int = Field(
        description="Score 0-40 for regulatory signal strength and recency."
    )
    supporting_score: int = Field(
        description="Score 0-30 for supporting signals reinforcing or contradicting regulatory."
    )
    icp_fit_score: int = Field(
        description="Score 0-20 for ICP alignment (industry, headcount, buyer profile)."
    )
    recency_score: int = Field(
        description="Score 0-10 for overall signal freshness."
    )
    total_score: int = Field(description="Sum of all sub-scores (0-100).")
    scoring_rationale: str = Field(
        description="2-3 sentences explaining the score breakdown."
    )


class TierAssignment(BaseModel):
    """Final output of Agent 2 — tier assignment with reasoning."""

    tier: Tier
    reason: str = Field(
        description=(
            "One sentence. Name the specific signal, its recency, and why it "
            "places this company in this tier."
        )
    )
    primary_signal_used: str = Field(
        description="regulatory_action | headcount_growth | ma_funding | "
        "leadership_change | tech_procurement | none"
    )
    confidence_in_tier: Confidence
    flag_for_review: bool = False
    flag_reason: Optional[str] = None


class ScoringEngineOutput(BaseModel):
    """Combined output from the full scoring pipeline."""

    company_name: str
    industry: str
    headcount: Union[str, int]
    scoring: ScoringOutput
    tier_assignment: TierAssignment
    signals_evaluated: int = 0
    data_sparse: bool = False
    signals: List[Signal] = Field(default_factory=list)


# ── Agent 3: Dossier Compiler ──────────────────────────────────────────


class EvaluatedCompany(BaseModel):
    """All data for one company after Agent 1 + Agent 2 — input to Agent 3."""

    name: str
    industry: str
    headcount: Union[str, int]
    tier: Tier
    confidence_in_tier: Confidence
    flag_for_review: bool = False
    flag_reason: Optional[str] = None
    reason: str
    primary_signal_used: str
    scoring: ScoringOutput
    signals: List[Signal] = Field(default_factory=list)
    data_sparse: bool = False


class BatchResult(BaseModel):
    """Full batch payload passed to Agent 3."""

    companies: List[EvaluatedCompany]
    batch_size: int
    batch_date: str
