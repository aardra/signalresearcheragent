"""Entry point to run the Signal Researcher agent for a target company."""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from signal_researcher import run_signal_researcher

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

    print(f"\n{'='*60}")
    print(f"Signal Researcher — Researching: {company['company_name']}")
    print(f"{'='*60}\n")

    result = run_signal_researcher(company)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(json.dumps(result.model_dump(), indent=2))

    print(f"\nSignals found: {result.signal_count}")
    print(f"Data sparse: {result.data_sparse}")
    print(f"Retries: {result.retry_count}")

    for i, signal in enumerate(result.signals, 1):
        print(f"\n--- Signal {i} ---")
        print(f"  Type:       {signal.type.value}")
        print(f"  Summary:    {signal.summary}")
        print(f"  Source:     {signal.source_url}")
        print(f"  Date:       {signal.date}")
        print(f"  Confidence: {signal.confidence.value}")


if __name__ == "__main__":
    main()
