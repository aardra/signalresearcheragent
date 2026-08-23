"""Orchestrator — runs the full four-agent pipeline for a batch of companies.

Flow:
  1. Accept N company inputs.
  2. Process companies in parallel batches of BATCH_SIZE (default 5).
     For each company: Agent 1 (Signal Researcher) → Agent 2 (Scoring Engine).
  3. Once all companies are scored, Agent 3 (Dossier Compiler) produces the report.
  4. Agent 4 (Outreach Drafter) writes personalised emails for Tier 1 and Tier 2.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from models import CompanyInput, ScoringEngineOutput, SignalResearchOutput
from output_logger import log_stage_output, output_log_session

BATCH_SIZE = int(os.getenv("ORCHESTRATOR_BATCH_SIZE", "5"))
MAX_WORKERS = int(os.getenv("ORCHESTRATOR_MAX_WORKERS", "5"))


def _process_single_company(
    company: Dict[str, Any],
    index: int,
    total: int,
) -> ScoringEngineOutput:
    """Run Agent 1 → Agent 2 for a single company. Thread-safe."""
    # Import here to avoid circular imports and ensure each thread
    # gets its own crew instances.
    from scoring_engine import run_scoring_engine
    from signal_researcher import run_signal_researcher

    name = company["company_name"]
    print(f"\n[{index}/{total}] Starting research: {name}")
    t0 = time.time()

    # Agent 1: Signal Research
    signal_output = run_signal_researcher(company)
    t1 = time.time()
    print(
        f"[{index}/{total}] {name} — Agent 1 done: "
        f"{signal_output.signal_count} signals in {t1 - t0:.1f}s"
    )

    # Agent 2: Scoring & Prioritisation
    scoring_output = run_scoring_engine(company, signal_output)
    t2 = time.time()
    print(
        f"[{index}/{total}] {name} — Agent 2 done: "
        f"{scoring_output.tier_assignment.tier.value} in {t2 - t1:.1f}s "
        f"(total {t2 - t0:.1f}s)"
    )

    return scoring_output


def run_pipeline(
    companies: List[Dict[str, Any]],
    batch_size: Optional[int] = None,
    max_workers: Optional[int] = None,
    skip_dossier: bool = False,
    skip_outreach: bool = False,
) -> Dict[str, Any]:
    """Run the full pipeline for a list of companies.

    Args:
        companies: List of company dicts (company_name, industry, headcount, etc.)
        batch_size: How many companies to process in each parallel batch.
        max_workers: Max concurrent threads per batch.
        skip_dossier: If True, skip Agent 3 and return scored results only.
        skip_outreach: If True, skip Agent 4 outreach drafting.

    Returns:
        Dict with keys:
          - "scored_results": List[ScoringEngineOutput]
          - "dossier_report": str (markdown) or None if skipped
          - "report_path": str or None
          - "outreach_report": str (markdown) or None if skipped
          - "outreach_path": str or None
          - "timing": dict with elapsed times
    """
    batch_size = batch_size or BATCH_SIZE
    max_workers = max_workers or MAX_WORKERS
    total = len(companies)

    with output_log_session(
        label="full_pipeline",
        meta={"company_count": total, "batch_size": batch_size},
    ):
        return _run_pipeline_impl(
            companies,
            batch_size,
            max_workers,
            skip_dossier,
            skip_outreach,
            total,
        )


def _run_pipeline_impl(
    companies: List[Dict[str, Any]],
    batch_size: int,
    max_workers: int,
    skip_dossier: bool,
    skip_outreach: bool,
    total: int,
) -> Dict[str, Any]:
    """Internal pipeline implementation (must run inside output_log_session)."""

    print(f"\n{'='*60}")
    print(f"ORCHESTRATOR — Processing {total} companies")
    print(f"Batch size: {batch_size} | Max workers: {max_workers}")
    print(f"{'='*60}")

    t_start = time.time()

    # ── Phase 1 + 2: Research + Score in parallel batches ───────────────
    all_scored: List[ScoringEngineOutput] = []
    errors: List[Dict[str, Any]] = []

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = companies[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"\n--- Batch {batch_num}/{total_batches} "
              f"(companies {batch_start + 1}-{batch_end}) ---")

        with ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
            futures = {
                executor.submit(
                    _process_single_company,
                    company,
                    batch_start + i + 1,
                    total,
                ): company
                for i, company in enumerate(batch)
            }

            for future in as_completed(futures):
                company = futures[future]
                try:
                    result = future.result()
                    all_scored.append(result)
                except Exception as e:
                    name = company.get("company_name", "unknown")
                    print(f"\n  ERROR processing {name}: {e}")
                    errors.append({"company": name, "error": str(e)})

    t_research = time.time()
    print(f"\n{'='*60}")
    print(f"Phase 1+2 complete: {len(all_scored)}/{total} companies scored "
          f"in {t_research - t_start:.1f}s")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors:
            print(f"    - {err['company']}: {err['error']}")
    print(f"{'='*60}")

    # ── Phase 3: Dossier Compilation ────────────────────────────────────
    dossier_report = None
    report_path = None
    outreach_report = None
    outreach_path = None
    t_dossier = t_research

    if not skip_dossier and all_scored:
        from dossier_compiler import run_dossier_compiler

        print(f"\nAGENT 3 — Dossier Compiler: {len(all_scored)} companies")
        dossier_report = run_dossier_compiler(all_scored)

        os.makedirs("output", exist_ok=True)
        report_path = "output/dossier_report.md"
        with open(report_path, "w") as f:
            f.write(dossier_report)
        print(f"\nDossier saved to: {report_path}")
        t_dossier = time.time()

    # ── Phase 4: Outreach Drafting ──────────────────────────────────────
    if not skip_outreach and dossier_report:
        tier_1_2_count = sum(
            1
            for so in all_scored
            if so.tier_assignment.tier.value in ("Tier 1", "Tier 2")
        )
        if tier_1_2_count:
            from outreach_drafter import run_outreach_drafter

            print(f"\nAGENT 4 — Outreach Drafter: {tier_1_2_count} Tier 1/2 companies")
            outreach_report = run_outreach_drafter(dossier_report)
            outreach_path = "output/outreach_messages.md"
            with open(outreach_path, "w") as f:
                f.write(outreach_report)
            print(f"Outreach messages saved to: {outreach_path}")
        else:
            print("\nAGENT 4 — Outreach Drafter: skipped (no Tier 1 or Tier 2 companies)")

    t_end = time.time()

    # ── Summary ─────────────────────────────────────────────────────────
    tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}
    for so in all_scored:
        tier_counts[so.tier_assignment.tier.value] += 1

    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Companies processed: {len(all_scored)}/{total}")
    print(f"  Tier 1 (Act):      {tier_counts['Tier 1']}")
    print(f"  Tier 2 (Nurture):  {tier_counts['Tier 2']}")
    print(f"  Tier 3 (Monitor):  {tier_counts['Tier 3']}")
    print(f"  Total time:        {t_end - t_start:.1f}s")
    if report_path:
        print(f"  Report:            {report_path}")
    if outreach_path:
        print(f"  Outreach:          {outreach_path}")

    pipeline_result = {
        "scored_results": all_scored,
        "dossier_report": dossier_report,
        "report_path": report_path,
        "outreach_report": outreach_report,
        "outreach_path": outreach_path,
        "errors": errors,
        "timing": {
            "research_and_scoring_seconds": round(t_research - t_start, 1),
            "dossier_seconds": round(t_dossier - t_research, 1) if dossier_report else 0,
            "outreach_seconds": round(t_end - t_dossier, 1) if outreach_report else 0,
            "total_seconds": round(t_end - t_start, 1),
        },
        "tier_counts": tier_counts,
    }
    log_stage_output(
        "pipeline",
        "run_pipeline",
        {
            "companies_processed": len(all_scored),
            "tier_counts": tier_counts,
            "errors": errors,
            "timing": pipeline_result["timing"],
            "report_path": report_path,
            "outreach_path": outreach_path,
        },
    )
    return pipeline_result
