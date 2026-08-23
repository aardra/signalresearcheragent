"""Standalone runner for Agent 4 — Outreach Drafter.

Usage:
    source .venv/bin/activate
    python run_outreach_drafter.py                          # from output/dossier_report.md
    python run_outreach_drafter.py path/to/dossier_report.md
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DOSSIER_PATH = "output/dossier_report.md"


def main() -> int:
    dossier_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DOSSIER_PATH

    try:
        with open(dossier_path) as f:
            dossier_report = f.read()
    except FileNotFoundError:
        print(f"Dossier not found: {dossier_path}", file=sys.stderr)
        print("Run the full pipeline first, or pass a dossier markdown path.", file=sys.stderr)
        return 1

    from outreach_drafter import run_outreach_drafter

    print(f"Drafting outreach from: {dossier_path}")
    outreach = run_outreach_drafter(dossier_report)

    output_path = "output/outreach_messages.md"
    with open(output_path, "w") as f:
        f.write(outreach)

    print(f"Outreach messages saved to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
