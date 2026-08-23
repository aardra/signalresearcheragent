"""Entry point to run the full pipeline: Signal Researcher → Scoring Engine."""

from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

load_dotenv()

import os

PLACEHOLDER_VALUES = {
    "your-serper-key-here",
    "sk-ant-your-key-here",
    "sk-your-key-here",
}


def validate_env() -> None:
    """Fail fast when required API keys are missing or still placeholders."""
    missing = []
    for key in ("OPENAI_API_KEY", "SERPER_API_KEY"):
        value = os.getenv(key, "").strip()
        if not value or value in PLACEHOLDER_VALUES:
            missing.append(key)
    if missing:
        print(
            "Missing or placeholder API keys: "
            + ", ".join(missing)
            + ".\nCopy .env.example to .env and set real values.",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    validate_env()

    from scoring_engine import run_scoring_engine
    from signal_researcher import run_signal_researcher

    company = {
        "company_name": "Revolut",
        "industry": "Financial Services / Fintech",
        "headcount": 8000,
        "domain": "revolut.com",
        "linkedin_url": "https://www.linkedin.com/company/revolut",
    }

    if len(sys.argv) > 1:
        company["company_name"] = sys.argv[1]
    if len(sys.argv) > 2:
        company["industry"] = sys.argv[2]
    if len(sys.argv) > 3:
        company["headcount"] = sys.argv[3]

    # ── Stage 1: Signal Research ────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"AGENT 1 — Signal Researcher: {company['company_name']}")
    print(f"{'='*60}\n")

    signal_output = run_signal_researcher(company)

    print(f"\nSignals found: {signal_output.signal_count}")
    print(f"Data sparse: {signal_output.data_sparse}")

    for i, signal in enumerate(signal_output.signals, 1):
        print(f"\n  Signal {i}: [{signal.type.value}] {signal.summary}")
        print(f"            Source: {signal.source_url}")
        print(f"            Date: {signal.date} | Confidence: {signal.confidence.value}")

    # ── Stage 2: Scoring & Prioritisation ───────────────────────────────
    print(f"\n{'='*60}")
    print(f"AGENT 2 — Scoring Engine: {company['company_name']}")
    print(f"{'='*60}\n")

    scoring_output = run_scoring_engine(company, signal_output)

    # ── Final output ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    print(json.dumps(scoring_output.model_dump(), indent=2))

    tier = scoring_output.tier_assignment
    score = scoring_output.scoring

    print(f"\n  Company:    {scoring_output.company_name}")
    print(f"  Industry:   {scoring_output.industry}")
    print(f"  Headcount:  {scoring_output.headcount}")
    print(f"\n  Scores:")
    print(f"    Regulatory:   {score.regulatory_score}/40")
    print(f"    Supporting:   {score.supporting_score}/30")
    print(f"    ICP fit:      {score.icp_fit_score}/20")
    print(f"    Freshness:    {score.recency_score}/10")
    print(f"    TOTAL:        {score.total_score}/100")
    print(f"\n  Rationale:  {score.scoring_rationale}")
    print(f"\n  *** {tier.tier.value} ***")
    print(f"  Reason:     {tier.reason}")
    print(f"  Primary:    {tier.primary_signal_used}")
    print(f"  Confidence: {tier.confidence_in_tier.value}")

    if tier.flag_for_review:
        print(f"\n  ⚠ FLAGGED FOR REVIEW: {tier.flag_reason}")


if __name__ == "__main__":
    main()
