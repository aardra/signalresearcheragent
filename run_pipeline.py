"""Entry point — run the full four-agent pipeline for a batch of companies.

Usage:
    python run_pipeline.py                         # default sample batch
    python run_pipeline.py companies.json          # load from JSON file
    python run_pipeline.py --company "Revolut" --industry "Fintech" --headcount 8000
"""

from __future__ import annotations

import argparse
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


SAMPLE_COMPANIES = [
    {
        "company_name": "Revolut",
        "industry": "Financial Services / Fintech",
        "headcount": 8000,
        "domain": "revolut.com",
        "linkedin_url": "https://www.linkedin.com/company/revolut",
    },
    {
        "company_name": "Deutsche Bank",
        "industry": "Banking / Financial Services",
        "headcount": 85000,
        "domain": "db.com",
        "linkedin_url": "https://www.linkedin.com/company/deutsche-bank",
    },
    {
        "company_name": "Teva Pharmaceutical",
        "industry": "Healthcare / Pharmaceuticals",
        "headcount": 37000,
        "domain": "tevapharm.com",
        "linkedin_url": "https://www.linkedin.com/company/teva-pharmaceutical-industries",
    },
    {
        "company_name": "Shell",
        "industry": "Energy / Oil & Gas",
        "headcount": 86000,
        "domain": "shell.com",
        "linkedin_url": "https://www.linkedin.com/company/shell",
    },
    {
        "company_name": "Coinbase",
        "industry": "Financial Services / Cryptocurrency",
        "headcount": 3500,
        "domain": "coinbase.com",
        "linkedin_url": "https://www.linkedin.com/company/coinbase",
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the four-agent lead generation pipeline."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="JSON file with a list of company objects.",
    )
    parser.add_argument(
        "--company", "-c",
        action="append",
        help="Company name (use with --industry and --headcount). Repeatable.",
    )
    parser.add_argument("--industry", "-i", action="append", help="Industry per company.")
    parser.add_argument("--headcount", "-n", action="append", help="Headcount per company.")
    parser.add_argument("--domain", "-d", action="append", help="Domain per company.")
    parser.add_argument(
        "--batch-size", type=int, default=5,
        help="Companies to process in parallel per batch (default: 5).",
    )
    parser.add_argument(
        "--max-workers", type=int, default=5,
        help="Max concurrent threads per batch (default: 5).",
    )
    parser.add_argument(
        "--skip-dossier", action="store_true",
        help="Skip Agent 3 dossier compilation (output scored results only).",
    )
    parser.add_argument(
        "--skip-outreach", action="store_true",
        help="Skip Agent 4 outreach drafting.",
    )
    return parser.parse_args()


def main():
    validate_env()
    args = parse_args()

    # Determine company list
    if args.input_file:
        with open(args.input_file) as f:
            companies = json.load(f)
        if not isinstance(companies, list):
            print("Input file must contain a JSON array of company objects.", file=sys.stderr)
            sys.exit(1)
    elif args.company:
        companies = []
        for idx, name in enumerate(args.company):
            companies.append({
                "company_name": name,
                "industry": (args.industry or [])[idx] if args.industry and idx < len(args.industry) else "Unknown",
                "headcount": (args.headcount or [])[idx] if args.headcount and idx < len(args.headcount) else "Unknown",
                "domain": (args.domain or [])[idx] if args.domain and idx < len(args.domain) else None,
            })
    else:
        print("No input provided — using sample batch of 5 companies.\n")
        companies = SAMPLE_COMPANIES

    from orchestrator import run_pipeline

    result = run_pipeline(
        companies,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        skip_dossier=args.skip_dossier,
        skip_outreach=args.skip_outreach,
    )

    # Print final JSON summary
    summary = {
        "companies_processed": len(result["scored_results"]),
        "tier_counts": result["tier_counts"],
        "errors": result["errors"],
        "timing": result["timing"],
        "report_path": result["report_path"],
        "outreach_path": result.get("outreach_path"),
    }
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
