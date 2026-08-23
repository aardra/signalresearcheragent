"""Test script — run the full four-agent pipeline for 5 companies.

Companies: JPMorgan Chase, Compass Pathways PLC, Anthem, Inc., Bank of America, UnitedHealth Group

Usage:
    source .venv/bin/activate
    python test_five_companies.py
"""

from __future__ import annotations

import json
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from orchestrator import run_pipeline

COMPANIES = [
    {
        "company_name": "JPMorgan Chase",
        "industry": "Banking / Financial Services",
        "headcount": 310000,
        "domain": "jpmorganchase.com",
        "linkedin_url": "https://www.linkedin.com/company/jpmorganchase",
    },
    {
        "company_name": "Compass Pathways PLC",
        "industry": "Healthcare / Biotech / Pharmaceuticals",
        "headcount": 200,
        "domain": "compasspathways.com",
        "linkedin_url": "https://www.linkedin.com/company/compass-pathways",
    },
    {
        "company_name": "Anthem, Inc.",
        "industry": "Healthcare / Insurance",
        "headcount": 100000,
        "domain": "elevancehealth.com",
        "linkedin_url": "https://www.linkedin.com/company/elevance-health",
    },
    {
        "company_name": "Bank of America",
        "industry": "Banking / Financial Services",
        "headcount": 213000,
        "domain": "bankofamerica.com",
        "linkedin_url": "https://www.linkedin.com/company/bank-of-america",
    },
    {
        "company_name": "UnitedHealth Group",
        "industry": "Healthcare / Insurance",
        "headcount": 440000,
        "domain": "unitedhealthgroup.com",
        "linkedin_url": "https://www.linkedin.com/company/unitedhealth-group",
    },
]


def main():
    print("=" * 60)
    print("Deal Intelligence — Full Pipeline Test")
    print("=" * 60)
    print(f"Companies: {', '.join(c['company_name'] for c in COMPANIES)}")
    print(f"Batch size: 5 (all in parallel)")
    print(f"Pipeline: Agent 1 → Agent 2 → Agent 3 (Dossier) → Agent 4 (Outreach)")
    print("=" * 60)

    t0 = time.time()

    result = run_pipeline(
        companies=COMPANIES,
        batch_size=5,
        max_workers=5,
    )

    elapsed = time.time() - t0

    # ── Per-company results ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("PER-COMPANY RESULTS")
    print(f"{'='*60}")

    for so in sorted(
        result["scored_results"],
        key=lambda x: ("Tier 1", "Tier 2", "Tier 3").index(x.tier_assignment.tier.value),
    ):
        tier = so.tier_assignment
        score = so.scoring
        flag = " ⚠ FLAGGED" if tier.flag_for_review else ""
        print(f"\n  {so.company_name} — {tier.tier.value}{flag}")
        print(f"    Industry:   {so.industry}")
        print(f"    Score:      {score.total_score}/100 "
              f"(reg={score.regulatory_score} sup={score.supporting_score} "
              f"icp={score.icp_fit_score} fresh={score.recency_score})")
        print(f"    Reason:     {tier.reason}")
        print(f"    Signals:    {so.signals_evaluated} found")
        print(f"    Confidence: {tier.confidence_in_tier.value}")
        if tier.flag_for_review:
            print(f"    Flag:       {tier.flag_reason}")

    # ── Summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Tier 1 (Act this week):  {result['tier_counts']['Tier 1']}")
    print(f"  Tier 2 (Nurture):        {result['tier_counts']['Tier 2']}")
    print(f"  Tier 3 (Monitor):        {result['tier_counts']['Tier 3']}")
    print(f"  Errors:                  {len(result['errors'])}")
    print(f"  Total time:              {elapsed:.0f}s ({elapsed/60:.1f}m)")
    print(f"  Research+Scoring:        {result['timing']['research_and_scoring_seconds']}s")
    print(f"  Dossier compilation:     {result['timing']['dossier_seconds']}s")
    print(f"  Outreach drafting:       {result['timing'].get('outreach_seconds', 0)}s")

    if result["report_path"]:
        print(f"\n  Dossier report saved to: {result['report_path']}")
    if result.get("outreach_path"):
        print(f"  Outreach messages saved to: {result['outreach_path']}")

    if result["errors"]:
        print(f"\n  ERRORS:")
        for err in result["errors"]:
            print(f"    - {err['company']}: {err['error']}")

    # Save full scored results as JSON for inspection
    scored_json = "output/scored_results.json"
    import os
    os.makedirs("output", exist_ok=True)
    with open(scored_json, "w") as f:
        json.dump(
            [so.model_dump() for so in result["scored_results"]],
            f,
            indent=2,
            default=str,
        )
    print(f"  Scored results JSON:     {scored_json}")

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")

    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
