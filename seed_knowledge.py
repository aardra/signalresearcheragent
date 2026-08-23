"""Seed institutional knowledge into CrewAI long-term memory.

Run once before the first pipeline execution, or re-run to refresh
after updating the knowledge entries below.

Usage:
    source .venv/bin/activate
    python seed_knowledge.py          # seed all crews
    python seed_knowledge.py --reset  # wipe and re-seed
"""

from __future__ import annotations

import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from memory_config import build_shared_memory

# ── Knowledge entries ───────────────────────────────────────────────────
# Each entry: (content, scope, categories, importance)
# importance: 0.0–1.0, where 1.0 is always-relevant institutional fact

KNOWLEDGE: list[tuple[str, str, list[str], float]] = [

    # ── ICP & Product ───────────────────────────────────────────────

    (
        "Our platform is an AI-powered, integrated GRC solution covering "
        "whistleblowing/incident reporting, policy management, compliance "
        "training, third-party risk screening, and regulatory change "
        "management. It consolidates fragmented point solutions into a "
        "single system so compliance leaders get a complete, auditable "
        "picture of enterprise risk.",
        "institutional/product",
        ["product", "icp"],
        1.0,
    ),

    (
        "Core buyers for the platform: Chief Compliance Officer (CCO), "
        "Chief Ethics & Compliance Officer, VP of Risk, General Counsel. "
        "Typically at large enterprises (500+ employees) or multinationals "
        "in heavily regulated industries.",
        "institutional/product",
        ["icp", "buyer_persona"],
        1.0,
    ),

    (
        "Primary target industries in order of fit: Financial Services, "
        "Healthcare, Energy, Manufacturing, Government/Public Sector. "
        "Secondary targets: Technology (if regulated), Pharmaceuticals, "
        "Insurance, Telecommunications. Poor fit: pure consumer tech, "
        "early-stage startups, small e-commerce businesses.",
        "institutional/product",
        ["icp", "industry"],
        1.0,
    ),

    (
        "The platform is trusted by thousands of organisations across "
        "the Fortune 500. This scale means enterprise-grade references "
        "are available for nearly every regulated industry vertical.",
        "institutional/product",
        ["product", "social_proof"],
        0.9,
    ),

    # ── Deal patterns ───────────────────────────────────────────────

    (
        "The platform wins most often when the prospect has had a regulatory "
        "action within 90 days AND is replacing a legacy GRC tool like "
        "SAI Global, EthicsPoint, or a homegrown spreadsheet-based "
        "compliance tracking system. The combination of regulatory pressure "
        "plus tool dissatisfaction creates the strongest buying urgency.",
        "institutional/deal_patterns",
        ["deal_pattern", "win_condition"],
        1.0,
    ),

    (
        "Deals close fastest (under 60 days) when three conditions align: "
        "(1) a recent regulatory enforcement action or consent order, "
        "(2) a newly appointed CCO or VP of Risk in the past 6 months, "
        "(3) active compliance hiring indicating budget allocation. "
        "When all three are present, the win rate exceeds 70%.",
        "institutional/deal_patterns",
        ["deal_pattern", "velocity"],
        1.0,
    ),

    (
        "The most common reason we lose deals: the prospect decides to "
        "extend an existing vendor relationship (typically OneTrust, Diligent, "
        "or SAP GRC) rather than switch platforms. Counter this by "
        "emphasising our integrated approach versus the prospect's "
        "current multi-vendor complexity.",
        "institutional/deal_patterns",
        ["deal_pattern", "loss_reason", "competitive"],
        0.9,
    ),

    (
        "Average deal size for enterprise accounts: $180K-$350K ARR. "
        "Mid-market (200-1000 employees): $45K-$120K ARR. Deals involving "
        "regulatory remediation mandates tend to be 40% larger than "
        "standard procurement cycles because urgency compresses negotiation.",
        "institutional/deal_patterns",
        ["deal_pattern", "pricing"],
        0.8,
    ),

    # ── Competitive intelligence ────────────────────────────────────

    (
        "Key competitors and positioning: "
        "OneTrust — strong in privacy/data governance, weaker in "
        "whistleblowing and incident management. "
        "Diligent — strong in board governance, weaker in compliance "
        "training and policy management. "
        "SAP GRC — entrenched in SAP shops, expensive and rigid. "
        "SAI Global (now LRQA) — legacy player, many customers ready "
        "to migrate. Displacement playbook available. "
        "LogicGate — newer, flexible but lacks depth in "
        "hotline/incident management.",
        "institutional/competitive",
        ["competitive", "positioning"],
        0.95,
    ),

    (
        "Competitor displacement signals to watch for in research: "
        "Job postings mentioning SAI Global, EthicsPoint, ComplianceWire "
        "indicate the company uses legacy or competitor "
        "products. G2/Capterra reviews comparing GRC tools suggest active "
        "evaluation. RFPs mentioning 'compliance platform consolidation' "
        "are high-value signals.",
        "institutional/competitive",
        ["competitive", "signal_research"],
        0.9,
    ),

    # ── Scoring calibration ─────────────────────────────────────────

    (
        "Scoring calibration from historical data: regulatory fines above "
        "$1M from SEC, FCA, OCC, FDIC, or CFPB should score 35+ on the "
        "regulatory dimension. Consent orders with remediation deadlines "
        "are the strongest signal — score 38-40. Routine audits with no "
        "findings should score 0-5. Voluntary disclosures are not "
        "regulatory actions and should not score above 10.",
        "institutional/scoring",
        ["scoring", "calibration"],
        1.0,
    ),

    (
        "ICP scoring calibration: Financial Services companies with 1000+ "
        "employees should score 18-20 on ICP fit. Healthcare with 500+ "
        "should score 16-18. Technology companies score 10-14 unless they "
        "are in fintech or healthtech (then 15-17). Pure e-commerce or "
        "consumer internet companies should score 5-9 regardless of size.",
        "institutional/scoring",
        ["scoring", "icp", "calibration"],
        0.95,
    ),

    (
        "Supporting signal calibration: compliance headcount growth of 5+ "
        "roles in 90 days is strong (score 20-25). A new CCO appointment "
        "within 6 months combined with a regulatory signal should boost "
        "supporting score to 25-30. M&A activity only scores well (15+) "
        "if the acquisition brings the company into a more regulated "
        "sector or significantly increases headcount.",
        "institutional/scoring",
        ["scoring", "calibration"],
        0.9,
    ),

    # ── Outreach intelligence ───────────────────────────────────────

    (
        "Outreach that works: the highest-converting cold outreach references "
        "a specific regulatory event by name and date, not a generic "
        "'compliance challenges' hook. Example: 'Following the OCC consent "
        "order issued on [date], companies in your position typically...' "
        "converts 3x better than 'As compliance requirements increase...'",
        "institutional/outreach",
        ["outreach", "messaging"],
        0.9,
    ),

    (
        "Best entry points by title: CCO and VP of Risk respond best to "
        "regulatory-event-triggered outreach. General Counsel responds "
        "better to whistleblowing/hotline-specific messaging. CFO is "
        "rarely the first contact but is the budget holder — reference "
        "cost-of-compliance data when the deal reaches procurement.",
        "institutional/outreach",
        ["outreach", "buyer_persona"],
        0.85,
    ),

    (
        "Timing matters: outreach within 14 days of a public regulatory "
        "action has 5x the response rate compared to 60+ days after. "
        "The ideal window is 7-21 days — early enough that the event is "
        "top of mind, late enough that the initial crisis response has "
        "settled and the prospect is thinking about systemic fixes.",
        "institutional/outreach",
        ["outreach", "timing"],
        0.9,
    ),

    # ── Regulatory landscape ────────────────────────────────────────

    (
        "Key regulators and their relevance to GRC platforms: "
        "SEC (US securities) — enforcement actions signal need for "
        "whistleblowing and disclosure management. "
        "FCA (UK financial) — fines often trigger AML compliance overhaul. "
        "OCC (US banking) — consent orders require remediation plans that "
        "create GRC platform buying cycles. "
        "FDIC — bank examination failures drive compliance tool upgrades. "
        "DOJ (FCPA enforcement) — anti-bribery actions create demand for "
        "third-party risk screening and training.",
        "institutional/regulatory",
        ["regulatory", "signal_research"],
        0.95,
    ),

    (
        "Regulatory trends to watch in 2025-2026: EU AI Act compliance "
        "creating new GRC requirements for technology companies. SEC "
        "cybersecurity disclosure rules (adopted 2023) still driving "
        "compliance tool purchases. ESG reporting mandates expanding "
        "scope of compliance programs at multinationals. DORA (Digital "
        "Operational Resilience Act) enforcement starting in EU financial "
        "sector — creating new compliance platform demand.",
        "institutional/regulatory",
        ["regulatory", "trends"],
        0.85,
    ),

    # ── Industry-specific insights ──────────────────────────────────

    (
        "Financial Services specifics: banks and fintech companies have "
        "the most complex compliance requirements and the largest budgets. "
        "They typically run 3-5 separate compliance tools. The platform wins by "
        "consolidating whistleblowing, policy management, and training "
        "into one system. Key pain point: audit preparation takes weeks "
        "when data is spread across systems — consolidation reduces this to days.",
        "institutional/industry",
        ["industry", "financial_services"],
        0.9,
    ),

    (
        "Healthcare specifics: HIPAA compliance drives demand, but the "
        "real entry point is often whistleblower/incident reporting "
        "(False Claims Act exposure). Healthcare companies that receive "
        "CMS penalties or OIG investigations are strong Tier 1 candidates. "
        "The buyer is usually the Chief Compliance Officer or VP of "
        "Regulatory Affairs.",
        "institutional/industry",
        ["industry", "healthcare"],
        0.85,
    ),

    (
        "Energy & Manufacturing specifics: environmental compliance and "
        "worker safety regulations (EPA, OSHA) create the primary demand. "
        "These companies often have speak-up/hotline programs mandated "
        "by regulation. The consolidation pitch works well here because "
        "EHS (Environment, Health, Safety) and compliance are often run "
        "by different teams with different tools.",
        "institutional/industry",
        ["industry", "energy", "manufacturing"],
        0.8,
    ),
]


# ── Seeding logic ───────────────────────────────────────────────────────


def seed_all(reset: bool = False):
    """Seed institutional knowledge into all crew memory stores."""

    crew_names = ["signal_researcher", "scoring_engine", "dossier_compiler"]

    for crew_name in crew_names:
        print(f"\n{'─'*50}")
        print(f"Seeding memory for: {crew_name}")
        print(f"{'─'*50}")

        memory = build_shared_memory(crew_name)

        if reset:
            print("  Resetting existing memory...")
            try:
                memory.reset()
                print("  Memory reset complete.")
            except Exception as e:
                print(f"  Reset skipped (may be empty): {e}")

        seeded = 0
        for content, scope, categories, importance in KNOWLEDGE:
            try:
                memory.remember(
                    content=content,
                    scope=scope,
                    categories=categories,
                    importance=importance,
                    source="institutional_knowledge_seed",
                    metadata={
                        "seeded_at": datetime.now().isoformat(),
                        "version": "1.0",
                    },
                )
                seeded += 1
            except Exception as e:
                print(f"  Failed to seed entry: {e}")
                print(f"    Content preview: {content[:80]}...")

        print(f"  Seeded {seeded}/{len(KNOWLEDGE)} entries into {crew_name}")

    # Drain writes to ensure all entries are persisted
    for crew_name in crew_names:
        try:
            memory = build_shared_memory(crew_name)
            memory.drain_writes()
        except Exception:
            pass

    print(f"\n{'='*50}")
    print(f"SEEDING COMPLETE")
    print(f"{'='*50}")
    print(f"  Total entries: {len(KNOWLEDGE)}")
    print(f"  Crews seeded: {', '.join(crew_names)}")
    print(f"  Categories: {sorted(set(c for _, _, cats, _ in KNOWLEDGE for c in cats))}")


def verify_recall():
    """Quick verification that seeded knowledge is retrievable."""
    print(f"\n{'='*50}")
    print("VERIFICATION — Testing recall")
    print(f"{'='*50}")

    test_queries = [
        ("scoring_engine", "What are the key competitors?"),
        ("scoring_engine", "How should I score a financial services company?"),
        ("signal_researcher", "Which regulators are most relevant?"),
        ("dossier_compiler", "What outreach messaging works best?"),
    ]

    for crew_name, query in test_queries:
        memory = build_shared_memory(crew_name)
        results = memory.recall(query, limit=2)
        print(f"\n  [{crew_name}] '{query}'")
        if results:
            for r in results:
                content = r.content if hasattr(r, "content") else str(r)
                preview = content[:120].replace("\n", " ")
                score = f" (score: {r.score:.2f})" if hasattr(r, "score") else ""
                print(f"    → {preview}...{score}")
        else:
            print("    → No results (memory may need embedding time)")


if __name__ == "__main__":
    do_reset = "--reset" in sys.argv
    if do_reset:
        print("MODE: Reset and re-seed all institutional knowledge")
    else:
        print("MODE: Seed institutional knowledge (append to existing)")

    seed_all(reset=do_reset)
    verify_recall()
