"""Generate the Deal Intelligence pipeline architecture diagram as a PDF.

Two pages:
  Page 1 — Pipeline architecture with all 4 agents + memory layer
  Page 2 — Legends: tier definitions, signal type definitions
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

# ── Colours ─────────────────────────────────────────────────────────────

WHITE = (255, 255, 255)
DARK = (15, 23, 42)
NAVY = (30, 64, 175)
LIGHT_NAVY = (59, 130, 246)
SLATE = (100, 116, 139)
BLUE_BG = (239, 246, 255)
BLUE_BORDER = (147, 197, 253)
GREEN = (22, 163, 74)
GREEN_BG = (240, 253, 244)
GREEN_BORDER = (134, 239, 172)
AMBER = (217, 119, 6)
AMBER_BG = (255, 251, 235)
AMBER_BORDER = (253, 224, 71)
PURPLE = (126, 34, 206)
PURPLE_BG = (250, 245, 255)
PURPLE_BORDER = (196, 181, 253)
GREY_BG = (248, 250, 252)
BORDER = (203, 213, 225)
TEAL = (13, 148, 136)
TEAL_BG = (240, 253, 250)
TEAL_BORDER = (94, 234, 212)
ROSE = (190, 18, 60)
ROSE_BG = (255, 241, 242)
ROSE_BORDER = (253, 164, 175)
ORANGE = (234, 88, 12)
ORANGE_BG = (255, 247, 237)
ORANGE_BORDER = (253, 186, 116)
RED_ACCENT = (220, 38, 38)
YELLOW_ACCENT = (202, 138, 4)
SLATE_LIGHT = (148, 163, 184)

FONT_PATH = ""
for p in ["/Library/Fonts/Arial Unicode.ttf",
          "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"]:
    if Path(p).exists():
        FONT_PATH = p
        break

FONT = "ArialUni"
_ACTIVE_FONT = FONT


class DiagramPDF(FPDF):
    def __init__(self):
        global _ACTIVE_FONT
        super().__init__(orientation="L", unit="mm", format="A4")
        if FONT_PATH:
            self.add_font(FONT, "", FONT_PATH)
            self.add_font(FONT, "B", FONT_PATH)
            self.add_font(FONT, "I", FONT_PATH)
            _ACTIVE_FONT = FONT
        else:
            _ACTIVE_FONT = "Helvetica"


def _box(pdf, x, y, w, h, fill, border_color):
    pdf.set_fill_color(*fill)
    pdf.set_draw_color(*border_color)
    pdf.set_line_width(0.5)
    pdf.rect(x, y, w, h, style="DF")


def _text(pdf, x, y, text, size=10, bold=False, color=DARK, w=0):
    pdf.set_font(_ACTIVE_FONT, "B" if bold else "", size)
    pdf.set_text_color(*color)
    pdf.set_xy(x, y)
    pdf.cell(w, size * 0.4, text)


def _multiline(pdf, x, y, text, size=7, color=SLATE, w=80):
    pdf.set_font(_ACTIVE_FONT, "", size)
    pdf.set_text_color(*color)
    pdf.set_xy(x, y)
    pdf.multi_cell(w, size * 0.5, text)


def _arrow_right(pdf, x1, y, x2, color=SLATE):
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.6)
    pdf.line(x1, y, x2, y)
    pdf.line(x2 - 2.5, y - 1.5, x2, y)
    pdf.line(x2 - 2.5, y + 1.5, x2, y)


def _arrow_down(pdf, x, y1, y2, color=SLATE):
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.6)
    pdf.line(x, y1, x, y2)
    pdf.line(x - 1.5, y2 - 2.5, x, y2)
    pdf.line(x + 1.5, y2 - 2.5, x, y2)


def _arrow_up(pdf, x, y1, y2, color=SLATE):
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.6)
    pdf.line(x, y1, x, y2)
    pdf.line(x - 1.5, y2 + 2.5, x, y2)
    pdf.line(x + 1.5, y2 + 2.5, x, y2)


# ── Page 1: Architecture ────────────────────────────────────────────────

def _draw_page1(pdf):
    pdf.add_page()

    # Title
    _text(pdf, 15, 8, "Deal Intelligence", size=18, bold=True, color=NAVY)
    _text(pdf, 15, 16, "Multi-Agent Pipeline Architecture", size=12, color=DARK)
    _text(pdf, 15, 22, "CrewAI  |  4 Agents  |  6 Sub-Agents  |  Parallel Batch  |  Institutional Knowledge Memory", size=7.5, color=SLATE)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.7)
    pdf.line(15, 25.5, 282, 25.5)

    # Layout
    col1_x = 15
    col2_x = 82
    col3_x = 149
    col4_x = 216
    box_w = 62
    sub_w = box_w - 6

    # ── ORCHESTRATOR ────────────────────────────────────────────────
    orch_y = 28
    _box(pdf, 15, orch_y, 267, 12, GREY_BG, BORDER)
    _text(pdf, 20, orch_y + 1.5, "ORCHESTRATOR", size=9, bold=True, color=DARK)
    _text(pdf, 85, orch_y + 1.5, "orchestrator.py  |  ThreadPoolExecutor  |  5 companies in parallel  |  Agent 1 -> 2 -> 3 -> 4", size=6.5, color=SLATE)

    for cx in [col1_x, col2_x, col3_x, col4_x]:
        _arrow_down(pdf, cx + box_w / 2, orch_y + 12, orch_y + 16, NAVY)

    agent_top = orch_y + 18
    a_h = 60

    # ── AGENT 1 — Signal Researcher ────────────────────────────────
    _box(pdf, col1_x, agent_top, box_w, a_h, BLUE_BG, BLUE_BORDER)
    _text(pdf, col1_x + 3, agent_top + 1, "AGENT 1", size=7, bold=True, color=LIGHT_NAVY)
    _text(pdf, col1_x + 3, agent_top + 5.5, "Signal Researcher", size=10, bold=True, color=NAVY)
    _text(pdf, col1_x + 3, agent_top + 11, "signal_researcher.py", size=6, color=SLATE)

    s1_y = agent_top + 16
    _box(pdf, col1_x + 3, s1_y, sub_w, 16, WHITE, BLUE_BORDER)
    _text(pdf, col1_x + 5.5, s1_y + 1, "Stage 1: Retriever", size=7.5, bold=True, color=DARK)
    _text(pdf, col1_x + 5.5, s1_y + 6, "LLM: Sonnet / GPT-4o-mini", size=6, color=SLATE)
    _text(pdf, col1_x + 5.5, s1_y + 10, "Tool: SerperDevTool", size=6, color=SLATE)

    _arrow_down(pdf, col1_x + box_w / 2, s1_y + 16, s1_y + 19, NAVY)

    s2_y = s1_y + 21
    _box(pdf, col1_x + 3, s2_y, sub_w, 16, WHITE, BLUE_BORDER)
    _text(pdf, col1_x + 5.5, s2_y + 1, "Stage 2: Extractor", size=7.5, bold=True, color=DARK)
    _text(pdf, col1_x + 5.5, s2_y + 6, "LLM: Haiku / GPT-4o-mini", size=6, color=SLATE)
    _text(pdf, col1_x + 5.5, s2_y + 10, "Structured JSON extraction", size=6, color=SLATE)

    _arrow_right(pdf, col1_x + box_w, agent_top + a_h / 2, col2_x, NAVY)
    _text(pdf, col1_x + box_w + 1, agent_top + a_h / 2 - 3.5, "signals[]", size=6, bold=True, color=NAVY)

    # ── AGENT 2 — Scoring Engine ───────────────────────────────────
    _box(pdf, col2_x, agent_top, box_w, a_h, GREEN_BG, GREEN_BORDER)
    _text(pdf, col2_x + 3, agent_top + 1, "AGENT 2", size=7, bold=True, color=GREEN)
    _text(pdf, col2_x + 3, agent_top + 5.5, "Scoring Engine", size=10, bold=True, color=(21, 128, 61))
    _text(pdf, col2_x + 3, agent_top + 11, "scoring_engine.py", size=6, color=SLATE)

    sc_y = agent_top + 16
    _box(pdf, col2_x + 3, sc_y, sub_w, 16, WHITE, GREEN_BORDER)
    _text(pdf, col2_x + 5.5, sc_y + 1, "Signal Scorer", size=7.5, bold=True, color=DARK)
    _text(pdf, col2_x + 5.5, sc_y + 6, "LLM: Claude Sonnet", size=6, color=SLATE)
    _text(pdf, col2_x + 5.5, sc_y + 10, "Rubric: 0-100 scoring", size=6, color=SLATE)

    _arrow_down(pdf, col2_x + box_w / 2, sc_y + 16, sc_y + 19, GREEN)

    pr_y = sc_y + 21
    _box(pdf, col2_x + 3, pr_y, sub_w, 16, WHITE, GREEN_BORDER)
    _text(pdf, col2_x + 5.5, pr_y + 1, "Tier Prioritiser", size=7.5, bold=True, color=DARK)
    _text(pdf, col2_x + 5.5, pr_y + 6, "LLM: Claude Sonnet", size=6, color=SLATE)
    _text(pdf, col2_x + 5.5, pr_y + 10, "Tier 1 / 2 / 3 + flags", size=6, color=SLATE)

    _arrow_right(pdf, col2_x + box_w, agent_top + a_h / 2, col3_x, NAVY)
    _text(pdf, col2_x + box_w + 1, agent_top + a_h / 2 - 3.5, "scored[]", size=6, bold=True, color=NAVY)

    # ── AGENT 3 — Dossier Compiler ─────────────────────────────────
    _box(pdf, col3_x, agent_top, box_w, a_h, PURPLE_BG, PURPLE_BORDER)
    _text(pdf, col3_x + 3, agent_top + 1, "AGENT 3", size=7, bold=True, color=PURPLE)
    _text(pdf, col3_x + 3, agent_top + 5.5, "Dossier Compiler", size=10, bold=True, color=(88, 28, 135))
    _text(pdf, col3_x + 3, agent_top + 11, "dossier_compiler.py", size=6, color=SLATE)

    dc_y = agent_top + 16
    _box(pdf, col3_x + 3, dc_y, sub_w, 16, WHITE, PURPLE_BORDER)
    _text(pdf, col3_x + 5.5, dc_y + 1, "Report Compiler", size=7.5, bold=True, color=DARK)
    _text(pdf, col3_x + 5.5, dc_y + 6, "LLM: GPT-5.1", size=6, color=SLATE)
    _text(pdf, col3_x + 5.5, dc_y + 10, "Batch comparison report", size=6, color=SLATE)

    do_y = dc_y + 21
    _box(pdf, col3_x + 3, do_y, sub_w, 16, WHITE, PURPLE_BORDER)
    _text(pdf, col3_x + 5.5, do_y + 1, "Output", size=7.5, bold=True, color=DARK)
    _text(pdf, col3_x + 5.5, do_y + 6, "dossier_report.md", size=6, color=SLATE)
    _text(pdf, col3_x + 5.5, do_y + 10, "dossier_report.pdf", size=6, color=SLATE)

    _arrow_right(pdf, col3_x + box_w, agent_top + a_h / 2, col4_x, NAVY)
    _text(pdf, col3_x + box_w + 1, agent_top + a_h / 2 - 3.5, "report", size=6, bold=True, color=NAVY)

    # ── AGENT 4 — Outreach Drafter ─────────────────────────────────
    _box(pdf, col4_x, agent_top, box_w, a_h, ORANGE_BG, ORANGE_BORDER)
    _text(pdf, col4_x + 3, agent_top + 1, "AGENT 4", size=7, bold=True, color=ORANGE)
    _text(pdf, col4_x + 3, agent_top + 5.5, "Outreach Drafter", size=10, bold=True, color=(194, 65, 12))
    _text(pdf, col4_x + 3, agent_top + 11, "outreach_drafter.py", size=6, color=SLATE)

    od_y = agent_top + 16
    _box(pdf, col4_x + 3, od_y, sub_w, 16, WHITE, ORANGE_BORDER)
    _text(pdf, col4_x + 5.5, od_y + 1, "Email Writer", size=7.5, bold=True, color=DARK)
    _text(pdf, col4_x + 5.5, od_y + 6, "LLM: GPT-5.1", size=6, color=SLATE)
    _text(pdf, col4_x + 5.5, od_y + 10, "Tier 1 + Tier 2 emails", size=6, color=SLATE)

    oo_y = od_y + 21
    _box(pdf, col4_x + 3, oo_y, sub_w, 16, WHITE, ORANGE_BORDER)
    _text(pdf, col4_x + 5.5, oo_y + 1, "Output", size=7.5, bold=True, color=DARK)
    _text(pdf, col4_x + 5.5, oo_y + 6, "outreach_messages.md", size=6, color=SLATE)
    _text(pdf, col4_x + 5.5, oo_y + 10, "Personalised per company", size=6, color=SLATE)

    # ── INSTITUTIONAL KNOWLEDGE & MEMORY ───────────────────────────
    mem_y = agent_top + a_h + 5
    mem_h = 32
    _box(pdf, 15, mem_y, 267, mem_h, TEAL_BG, TEAL_BORDER)
    _text(pdf, 20, mem_y + 1.5, "INSTITUTIONAL KNOWLEDGE & LONG-TERM MEMORY", size=9, bold=True, color=TEAL)
    _text(pdf, 20, mem_y + 7, "seed_knowledge.py  |  memory_config.py  |  LanceDB  |  21 entries / 7 categories  |  Scoped per crew + agent", size=6.5, color=SLATE)

    # Arrows up from memory to each agent
    for cx in [col1_x, col2_x, col3_x, col4_x]:
        _arrow_up(pdf, cx + box_w / 2, mem_y, agent_top + a_h, TEAL)

    # Knowledge sub-boxes
    cat_y = mem_y + 12
    cat_h = 16
    cat_w = 83
    gap = 6

    cx1 = 19
    _box(pdf, cx1, cat_y, cat_w, cat_h, WHITE, TEAL_BORDER)
    _text(pdf, cx1 + 3, cat_y + 1.5, "ICP, Product & Deal Patterns", size=7.5, bold=True, color=TEAL)
    _text(pdf, cx1 + 3, cat_y + 6.5, "Win conditions, buyer personas, pricing,", size=6, color=SLATE)
    _text(pdf, cx1 + 3, cat_y + 10.5, "deal velocity triggers, loss reasons", size=6, color=SLATE)

    cx2 = cx1 + cat_w + gap
    _box(pdf, cx2, cat_y, cat_w, cat_h, WHITE, TEAL_BORDER)
    _text(pdf, cx2 + 3, cat_y + 1.5, "Competitive & Scoring Calibration", size=7.5, bold=True, color=TEAL)
    _text(pdf, cx2 + 3, cat_y + 6.5, "Competitor map (OneTrust, Diligent, SAP),", size=6, color=SLATE)
    _text(pdf, cx2 + 3, cat_y + 10.5, "displacement signals, score calibration", size=6, color=SLATE)

    cx3 = cx2 + cat_w + gap
    _box(pdf, cx3, cat_y, cat_w, cat_h, WHITE, TEAL_BORDER)
    _text(pdf, cx3 + 3, cat_y + 1.5, "Regulatory & Outreach Intel", size=7.5, bold=True, color=TEAL)
    _text(pdf, cx3 + 3, cat_y + 6.5, "SEC/FCA/OCC, 2025-26 trends,", size=6, color=SLATE)
    _text(pdf, cx3 + 3, cat_y + 10.5, "outreach timing, messaging hooks", size=6, color=SLATE)

    # ── SUPPORTING COMPONENTS ──────────────────────────────────────
    sup_y = mem_y + mem_h + 4
    comp_w = 85

    _box(pdf, 15, sup_y, comp_w, 15, AMBER_BG, AMBER_BORDER)
    _text(pdf, 18, sup_y + 1.5, "Quality Gates (G1-G9)", size=8, bold=True, color=AMBER)
    _text(pdf, 18, sup_y + 7, "URL | date | recency | inference | type | confidence", size=6, color=SLATE)

    _box(pdf, 15 + comp_w + 4, sup_y, comp_w + 6, 15, GREY_BG, BORDER)
    _text(pdf, 18 + comp_w + 4, sup_y + 1.5, "Data Models (models.py)", size=8, bold=True, color=DARK)
    _text(pdf, 18 + comp_w + 4, sup_y + 7, "Signal, ScoringOutput, TierAssignment, BatchResult", size=6, color=SLATE)

    _box(pdf, 15 + 2 * (comp_w + 4) + 2, sup_y, comp_w - 2, 15, GREY_BG, BORDER)
    _text(pdf, 18 + 2 * (comp_w + 4) + 2, sup_y + 1.5, "PDF Report (pdf_report.py)", size=8, bold=True, color=DARK)
    _text(pdf, 18 + 2 * (comp_w + 4) + 2, sup_y + 7, "Markdown to branded PDF | fpdf2", size=6, color=SLATE)

    # ── FOOTER: key files ──────────────────────────────────────────
    fy = sup_y + 19
    _text(pdf, 15, fy, "KEY FILES", size=7.5, bold=True, color=DARK)
    files = [
        "orchestrator.py", "signal_researcher.py", "scoring_engine.py",
        "dossier_compiler.py", "outreach_drafter.py", "seed_knowledge.py",
        "memory_config.py", "models.py", "pdf_report.py", "config/*.yaml",
    ]
    _text(pdf, 50, fy, "  |  ".join(files), size=6, color=SLATE)


# ── Page 2: Legends ─────────────────────────────────────────────────────

def _draw_page2(pdf):
    pdf.add_page()

    _text(pdf, 15, 8, "Deal Intelligence", size=18, bold=True, color=NAVY)
    _text(pdf, 15, 16, "Reference: Tier Definitions & Signal Taxonomy", size=12, color=DARK)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.7)
    pdf.line(15, 21, 282, 21)

    # ================================================================
    # SECTION 1: TIER DEFINITIONS
    # ================================================================
    sec1_y = 25
    _text(pdf, 15, sec1_y, "SALES TIER DEFINITIONS", size=11, bold=True, color=NAVY)

    tier_w = 85
    tier_h = 48
    tier_y = sec1_y + 6

    # TIER 1
    t1_x = 15
    _box(pdf, t1_x, tier_y, tier_w, tier_h, (254, 242, 242), (252, 129, 129))
    _box(pdf, t1_x, tier_y, tier_w, 9, RED_ACCENT, RED_ACCENT)
    _text(pdf, t1_x + 3, tier_y + 1.5, "TIER 1 — ACT THIS WEEK", size=8.5, bold=True, color=WHITE)
    _text(pdf, t1_x + 3, tier_y + 11, "Criteria:", size=7.5, bold=True, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 16, "- Regulatory signal < 60 days old", size=6.5, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 20.5, "- High confidence, primary source", size=6.5, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 25, "- Directly relevant to GRC pain", size=6.5, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 29.5, "- Company fits ICP", size=6.5, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 35, "Action:", size=7.5, bold=True, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 39.5, "Full outreach push. Personalised email", size=6.5, color=DARK)
    _text(pdf, t1_x + 3, tier_y + 43.5, "drafted by Agent 4.", size=6.5, color=DARK)

    # TIER 2
    t2_x = t1_x + tier_w + 6
    _box(pdf, t2_x, tier_y, tier_w, tier_h, (255, 251, 235), (253, 224, 71))
    _box(pdf, t2_x, tier_y, tier_w, 9, YELLOW_ACCENT, YELLOW_ACCENT)
    _text(pdf, t2_x + 3, tier_y + 1.5, "TIER 2 — NURTURE (30 DAYS)", size=8.5, bold=True, color=WHITE)
    _text(pdf, t2_x + 3, tier_y + 11, "Criteria:", size=7.5, bold=True, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 16, "- Real signal but moderate urgency", size=6.5, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 20.5, "- Event older, or medium confidence", size=6.5, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 25, "- Or partial ICP fit", size=6.5, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 29.5, "- Worth warm touch, not full push", size=6.5, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 35, "Action:", size=7.5, bold=True, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 39.5, "Nurture email drafted by Agent 4.", size=6.5, color=DARK)
    _text(pdf, t2_x + 3, tier_y + 43.5, "Re-evaluate in 30 days.", size=6.5, color=DARK)

    # TIER 3
    t3_x = t2_x + tier_w + 6
    _box(pdf, t3_x, tier_y, tier_w, tier_h, GREY_BG, BORDER)
    _box(pdf, t3_x, tier_y, tier_w, 9, SLATE, SLATE)
    _text(pdf, t3_x + 3, tier_y + 1.5, "TIER 3 — MONITOR ONLY", size=8.5, bold=True, color=WHITE)
    _text(pdf, t3_x + 3, tier_y + 11, "Criteria:", size=7.5, bold=True, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 16, "- Signals weak, stale, or low confidence", size=6.5, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 20.5, "- Company is poor ICP fit", size=6.5, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 25, "- No regulatory signal found", size=6.5, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 29.5, "- Evidence too thin to act on", size=6.5, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 35, "Action:", size=7.5, bold=True, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 39.5, "No outreach. Flag for next pipeline", size=6.5, color=DARK)
    _text(pdf, t3_x + 3, tier_y + 43.5, "cycle. Re-evaluate in 60 days.", size=6.5, color=DARK)

    # ================================================================
    # SECTION 2: SIGNAL TYPE DEFINITIONS
    # ================================================================
    sec2_y = tier_y + tier_h + 8
    _text(pdf, 15, sec2_y, "SIGNAL TYPE TAXONOMY", size=11, bold=True, color=NAVY)

    sig_y = sec2_y + 6
    sig_h = 38

    signals = [
        {
            "num": "1",
            "name": "Regulatory Action",
            "key": "regulatory_action",
            "color": RED_ACCENT,
            "bg": (254, 242, 242),
            "border": (252, 129, 129),
            "desc": "Fine, audit, enforcement notice, consent order, or new compliance mandate affecting the company's sector.",
            "sources": "SEC EDGAR, FCA register, regulator press releases, Reuters, FT, Bloomberg, Law360",
            "weight": "Primary signal. Scores 0-40 pts. Drives tier assignment.",
        },
        {
            "num": "2",
            "name": "Compliance Headcount",
            "key": "headcount_growth",
            "color": LIGHT_NAVY,
            "bg": BLUE_BG,
            "border": BLUE_BORDER,
            "desc": "Net increase in open roles for compliance, risk, GRC, legal, or regulatory affairs in the past 90 days.",
            "sources": "LinkedIn Jobs, Greenhouse, Lever, Workday career pages, Indeed, Glassdoor",
            "weight": "Supporting. Reinforces regulatory pressure. Budget allocation indicator.",
        },
        {
            "num": "3",
            "name": "M&A / Funding",
            "key": "ma_funding",
            "color": GREEN,
            "bg": GREEN_BG,
            "border": GREEN_BORDER,
            "desc": "Acquisition, merger, Series B+ raise, IPO filing, SPAC, or material restructuring in past 6 months.",
            "sources": "Crunchbase, PitchBook, SEC EDGAR (S-1, 8-K, 13D), TechCrunch, Bloomberg",
            "weight": "Supporting. Signals growth, new regulatory obligations, or platform consolidation.",
        },
        {
            "num": "4",
            "name": "Leadership Change",
            "key": "leadership_change",
            "color": PURPLE,
            "bg": PURPLE_BG,
            "border": PURPLE_BORDER,
            "desc": "New CCO, CFO, CRO, General Counsel, CPO, or CISO appointment in past 6 months.",
            "sources": "LinkedIn profiles, company press releases, regulatory filings listing officers",
            "weight": "Supporting. New leaders often re-evaluate tools. Strong when paired with regulatory signal.",
        },
        {
            "num": "5",
            "name": "Tech Procurement",
            "key": "tech_procurement",
            "color": ORANGE,
            "bg": ORANGE_BG,
            "border": ORANGE_BORDER,
            "desc": "Vendor announcement, RFP, integration launch, or platform replacement in adjacent GRC/risk category.",
            "sources": "G2, Capterra reviews, company blog, press releases, job postings requiring tool expertise",
            "weight": "Supporting. Indicates active tool evaluation cycle. Competitor displacement opportunity.",
        },
    ]

    card_w = 51.4
    card_gap = 2.5

    for i, sig in enumerate(signals):
        sx = 15 + i * (card_w + card_gap)
        _box(pdf, sx, sig_y, card_w, sig_h, sig["bg"], sig["border"])

        # Number badge
        _box(pdf, sx, sig_y, 12, 8, sig["color"], sig["color"])
        _text(pdf, sx + 4.5, sig_y + 1.5, sig["num"], size=8, bold=True, color=WHITE)

        # Name
        _text(pdf, sx + 14, sig_y + 1.5, sig["name"], size=8, bold=True, color=sig["color"])

        # Key
        _text(pdf, sx + 3, sig_y + 9.5, sig["key"], size=5.5, color=SLATE)

        # Description
        _text(pdf, sx + 3, sig_y + 14, sig["desc"][:55], size=5.5, color=DARK)
        if len(sig["desc"]) > 55:
            _text(pdf, sx + 3, sig_y + 17.5, sig["desc"][55:110], size=5.5, color=DARK)
            if len(sig["desc"]) > 110:
                _text(pdf, sx + 3, sig_y + 21, sig["desc"][110:], size=5.5, color=DARK)

        # Sources
        _text(pdf, sx + 3, sig_y + 25.5, "Sources:", size=5.5, bold=True, color=SLATE)
        _text(pdf, sx + 3, sig_y + 29, sig["sources"][:55], size=5, color=SLATE)
        if len(sig["sources"]) > 55:
            _text(pdf, sx + 3, sig_y + 32, sig["sources"][55:], size=5, color=SLATE)

        # Weight
        _text(pdf, sx + 3, sig_y + 35, sig["weight"][:60], size=5, bold=True, color=sig["color"])

    # ================================================================
    # SECTION 3: SCORING RUBRIC SUMMARY
    # ================================================================
    rub_y = sig_y + sig_h + 8
    _text(pdf, 15, rub_y, "SCORING RUBRIC (0-100)", size=11, bold=True, color=NAVY)

    # Table header
    tab_y = rub_y + 6
    cols = [
        ("Dimension", 50),
        ("Points", 20),
        ("35-40 / 25-30 / 17-20 / 8-10", 70),
        ("25-34 / 15-24 / 10-16 / 5-7", 70),
        ("0-9 / 0-4 / 0-9 / 0-1", 57),
    ]
    headers = ["Dimension", "Max Pts", "Strong", "Moderate", "Weak"]

    # Header row
    hx = 15
    for header, cw in zip(headers, cols):
        _box(pdf, hx, tab_y, cw[1], 7, NAVY, NAVY)
        _text(pdf, hx + 2, tab_y + 1.5, header, size=7, bold=True, color=WHITE)
        hx += cw[1]

    # Data rows
    rows = [
        ("Regulatory Signal", "40", "Primary source, < 60 days, directly relevant", "Within 6 months, medium confidence", "Stale, tangential, or none"),
        ("Supporting Signals", "30", "Multiple signals reinforce regulatory", "One strong complementary signal", "None, or contradicts regulatory"),
        ("ICP Fit", "20", "Core industry, 500+ employees, has CCO", "Right industry but small, or large but lightly regulated", "Wrong industry or too small"),
        ("Signal Freshness", "10", "Most recent signal < 30 days", "30-90 days old", "All signals > 180 days"),
    ]

    for ri, (dim, pts, strong, moderate, weak) in enumerate(rows):
        ry = tab_y + 7 + ri * 7
        bg = WHITE if ri % 2 == 0 else GREY_BG
        rx = 15
        vals = [dim, pts, strong, moderate, weak]
        for vi, (_, cw) in enumerate(cols):
            _box(pdf, rx, ry, cw, 7, bg, BORDER)
            bold = vi == 0
            _text(pdf, rx + 2, ry + 1.5, vals[vi], size=6, bold=bold, color=DARK)
            rx += cw

    # Score-to-tier mapping
    map_y = tab_y + 7 + len(rows) * 7 + 4
    _text(pdf, 15, map_y, "SCORE-TO-TIER MAPPING", size=9, bold=True, color=DARK)
    mappings = [
        ("Total >= 70 AND Regulatory >= 30", "Tier 1", RED_ACCENT),
        ("Total 45-69 OR Regulatory 15-29", "Tier 2", YELLOW_ACCENT),
        ("Total < 45", "Tier 3", SLATE),
    ]
    for j, (rule, tier, color) in enumerate(mappings):
        mx = 15 + j * 92
        my = map_y + 5
        _box(pdf, mx, my, 8, 5, color, color)
        _text(pdf, mx + 10, my + 0.5, f"{tier}:  {rule}", size=7, color=DARK)


# ── Page 3: Project Overview ────────────────────────────────────────────

def _draw_page3_overview(pdf):
    """Page 3: Non-technical project overview with orchestrator and memory details."""
    pdf.add_page()

    _text(pdf, 15, 8, "Deal Intelligence", size=18, bold=True, color=NAVY)
    _text(pdf, 15, 16, "Project Overview", size=12, color=DARK)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.7)
    pdf.line(15, 21, 282, 21)

    y = 25

    # ── WHAT THIS PROJECT DOES ──────────────────────────────────────
    _text(pdf, 15, y, "WHAT THIS PROJECT DOES", size=11, bold=True, color=NAVY)
    y += 6
    pdf.set_font(_ACTIVE_FONT, "", 9)
    pdf.set_text_color(*DARK)
    pdf.set_xy(15, y)
    pdf.multi_cell(260, 4.5,
        "This system turns a simple list of company names into prioritised, ready-to-send "
        "sales outreach — with no human research required. A sales leader provides a batch "
        "of target companies (name, industry, and size), and the pipeline autonomously "
        "researches each company for buying signals, scores them against our ideal customer "
        "profile, ranks them into action tiers, produces an executive dossier comparing all "
        "companies, and drafts personalised outreach emails for the strongest prospects.\n\n"
        "The entire process runs in under 10 minutes for a batch of 5 companies. What would "
        "take an SDR team a full day of manual research is completed automatically, with "
        "every finding traceable to a public, dated source.")
    y = pdf.get_y() + 6

    # ── THE FOUR AGENTS ─────────────────────────────────────────────
    _text(pdf, 15, y, "THE FOUR AGENTS", size=11, bold=True, color=NAVY)
    y += 7

    agents = [
        ("1", "Signal Researcher", BLUE_BG, BLUE_BORDER, NAVY,
         "Searches public sources (regulatory filings, news, job boards, press releases) for five types of buying "
         "signals: regulatory actions, compliance hiring, M&A activity, leadership changes, and technology "
         "procurement. Every signal must have a verifiable URL and a concrete date — if the source cannot be "
         "cited, the signal does not exist. This agent runs twice internally: first a broad search, then a "
         "precise extraction step that converts raw evidence into structured data."),
        ("2", "Scoring Engine", GREEN_BG, GREEN_BORDER, GREEN,
         "Evaluates each company on a 100-point scale across four dimensions: regulatory signal strength "
         "(0-40 points), supporting signal reinforcement (0-30), ICP fit (0-20), and signal freshness (0-10). "
         "Then assigns a sales tier: Tier 1 (act this week), Tier 2 (nurture for 30 days), or Tier 3 (monitor "
         "only). Flags borderline cases for human review rather than guessing."),
        ("3", "Dossier Compiler", PURPLE_BG, PURPLE_BORDER, PURPLE,
         "Compares all companies in the batch side by side and produces a polished executive report. Includes "
         "a scorecard table, individual write-ups for Tier 1 and Tier 2 companies, a batch intelligence "
         "summary highlighting cross-company patterns, and data quality notes. Written for a reader with "
         "4 minutes — every section is skimmable."),
        ("4", "Outreach Drafter", ORANGE_BG, ORANGE_BORDER, ORANGE,
         "Reads the dossier and writes personalised outreach emails for every Tier 1 and Tier 2 company. "
         "Each email references the specific signal that triggered it — the recipient knows immediately why "
         "this was sent to them, today. Tier 1 emails are direct and urgent; Tier 2 emails are warm and "
         "patient. Tier 3 companies receive no outreach."),
    ]

    for num, name, bg, border, color, desc in agents:
        _box(pdf, 15, y, 267, 18, bg, border)
        _box(pdf, 15, y, 10, 18, color, color)
        _text(pdf, 17, y + 5, num, size=10, bold=True, color=WHITE)
        _text(pdf, 28, y + 1.5, name, size=9, bold=True, color=color)
        pdf.set_font(_ACTIVE_FONT, "", 6.5)
        pdf.set_text_color(*DARK)
        pdf.set_xy(28, y + 7)
        pdf.multi_cell(250, 3.3, desc)
        y += 21

    y += 2

    # ── THE ORCHESTRATOR ────────────────────────────────────────────
    _text(pdf, 15, y, "THE ORCHESTRATOR: HOW IT ALL RUNS TOGETHER", size=11, bold=True, color=NAVY)
    y += 6
    pdf.set_font(_ACTIVE_FONT, "", 8.5)
    pdf.set_text_color(*DARK)
    pdf.set_xy(15, y)
    pdf.multi_cell(130, 4.2,
        "The orchestrator is the control layer that coordinates the four agents. It does not "
        "research, score, or write — it manages the workflow.\n\n"
        "When given a batch of companies, the orchestrator splits them into groups of five and "
        "processes each group in parallel. For every company in a group, it runs Agent 1 (research) "
        "and Agent 2 (scoring) simultaneously in separate threads. Once all companies in the batch "
        "are scored, it hands the complete set to Agent 3 (dossier), then Agent 4 (outreach).\n\n"
        "If any company fails during research or scoring, the orchestrator logs the error and "
        "continues with the remaining companies — one failure does not stop the batch. It tracks "
        "timing for each phase and produces a summary at the end showing how many companies "
        "reached each tier, how long each stage took, and whether any errors occurred.")
    y_left = pdf.get_y()

    # Orchestrator characteristics on the right
    right_x = 152
    chars = [
        ("Parallel processing", "5 companies researched simultaneously, not one at a time."),
        ("Fault tolerance", "If one company fails, the rest continue. Errors are logged, not fatal."),
        ("Phase gating", "Agent 3 waits for all companies to be scored before compiling. Agent 4 waits for the dossier."),
        ("Configurable", "Batch size, worker count, and which agents to skip are all adjustable."),
        ("Transparent timing", "Reports exactly how long each phase took — research, scoring, dossier, outreach."),
    ]

    cy = y
    for title, desc in chars:
        _text(pdf, right_x, cy, title, size=7.5, bold=True, color=NAVY)
        _text(pdf, right_x, cy + 4, desc, size=6.5, color=DARK)
        cy += 11

    y = max(y_left, cy) + 4

    # ── INSTITUTIONAL KNOWLEDGE ─────────────────────────────────────
    _box(pdf, 15, y, 267, 38, TEAL_BG, TEAL_BORDER)
    _text(pdf, 18, y + 2, "THE MEMORY LAYER: INSTITUTIONAL KNOWLEDGE AS A HUMAN IN THE LOOP", size=10, bold=True, color=TEAL)

    pdf.set_font(_ACTIVE_FONT, "", 8)
    pdf.set_text_color(*DARK)
    pdf.set_xy(18, y + 9)
    pdf.multi_cell(120, 4,
        "Every agent in the pipeline has access to a shared memory layer that contains the "
        "company's institutional knowledge — the kind of insight that normally lives in a "
        "senior salesperson's head.\n\n"
        "This is not just a database. It acts as a persistent human-in-the-loop: when the "
        "scoring agent evaluates a financial services company, it recalls that \"companies "
        "with 1,000+ employees in this sector should score 18-20 on ICP fit.\" When the "
        "outreach drafter writes an email, it recalls that \"outreach within 14 days of a "
        "regulatory action has 5x the response rate.\" The agents make better decisions "
        "because they carry the organisation's accumulated sales wisdom.")

    # Knowledge categories on the right side
    kx = 145
    ky = y + 9
    categories = [
        ("21 knowledge entries across 7 categories:", TEAL, True),
        ("- ICP definitions and industry weights", DARK, False),
        ("- Deal win/loss patterns and velocity triggers", DARK, False),
        ("- Competitor positioning (OneTrust, Diligent, SAP)", DARK, False),
        ("- Scoring calibration benchmarks", DARK, False),
        ("- Outreach timing and messaging hooks", DARK, False),
        ("- Regulator profiles (SEC, FCA, OCC, DOJ)", DARK, False),
        ("- Industry-specific compliance pain points", DARK, False),
        ("", DARK, False),
        ("This knowledge persists across runs and grows", TEAL, True),
        ("over time as the pipeline learns from results.", TEAL, False),
    ]
    for text, color, bold in categories:
        if text:
            _text(pdf, kx, ky, text, size=7, bold=bold, color=color)
        ky += 4


# ── Pages 4-7: Sample Run Results ───────────────────────────────────────

def _page_header(pdf, subtitle):
    _text(pdf, 15, 8, "Deal Intelligence", size=18, bold=True, color=NAVY)
    _text(pdf, 15, 16, subtitle, size=12, color=DARK)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.7)
    pdf.line(15, 21, 282, 21)


def _section_label(pdf, y, label, color=NAVY):
    _text(pdf, 15, y, label, size=11, bold=True, color=color)
    return y + 6


def _para(pdf, x, y, text, size=8, color=DARK, w=250, bold=False):
    pdf.set_font(_ACTIVE_FONT, "B" if bold else "", size)
    pdf.set_text_color(*color)
    pdf.set_xy(x, y)
    pdf.multi_cell(w, size * 0.5, text)
    return pdf.get_y()


def _draw_page4_inputs(pdf):
    """Page 4: What we put in — the 5 companies."""
    pdf.add_page()
    _page_header(pdf, "Sample Run: What Goes In")

    y = 25
    y = _section_label(pdf, y, "THE SCENARIO")
    y = _para(pdf, 15, y,
        "A sales leader wants to evaluate five companies for potential outreach. "
        "The only information provided is each company's name, industry, and approximate size. "
        "The pipeline takes this minimal input and — without any human research — produces "
        "a prioritised, scored dossier with draft outreach emails ready for review.",
        size=9, w=260)
    y += 3

    y = _section_label(pdf, y, "INPUT: 5 COMPANIES")
    y += 1

    # Input table
    cols_w = [55, 75, 35, 50, 52]
    headers = ["Company", "Industry", "Headcount", "Domain", "LinkedIn"]
    companies = [
        ("JPMorgan Chase", "Banking / Financial Services", "310,000", "jpmorganchase.com", "linkedin.com/.../jpmorganchase"),
        ("Compass Pathways", "Healthcare / Biotech / Pharma", "200", "compasspathways.com", "linkedin.com/.../compass-pathways"),
        ("Anthem, Inc.", "Healthcare / Insurance", "100,000", "elevancehealth.com", "linkedin.com/.../elevance-health"),
        ("Bank of America", "Banking / Financial Services", "213,000", "bankofamerica.com", "linkedin.com/.../bank-of-america"),
        ("UnitedHealth Group", "Healthcare / Insurance", "440,000", "unitedhealthgroup.com", "linkedin.com/.../unitedhealth-group"),
    ]

    hx = 15
    for h, cw in zip(headers, cols_w):
        _box(pdf, hx, y, cw, 7, NAVY, NAVY)
        _text(pdf, hx + 2, y + 1.5, h, size=7, bold=True, color=WHITE)
        hx += cw

    for ri, row in enumerate(companies):
        ry = y + 7 + ri * 7
        bg = WHITE if ri % 2 == 0 else GREY_BG
        rx = 15
        for ci, cw in enumerate(cols_w):
            _box(pdf, rx, ry, cw, 7, bg, BORDER)
            _text(pdf, rx + 2, ry + 1.5, row[ci], size=6.5, color=DARK)
            rx += cw

    y = y + 7 + len(companies) * 7 + 4

    _para(pdf, 15, y,
        "That is everything the system receives. No prior research, no signal lists, no scoring hints. "
        "From here, the pipeline runs fully autonomously.",
        size=8, color=SLATE, w=260)
    y = pdf.get_y() + 8

    # What happens next
    y = _section_label(pdf, y, "WHAT HAPPENS NEXT")
    y += 1

    steps = [
        ("Agent 1: Signal Researcher", "Searches the public web for buying signals — regulatory actions, compliance hiring, M&A events, leadership changes, and technology procurement activity. Each signal must have a verifiable source URL and a concrete date."),
        ("Agent 2: Scoring Engine", "Scores each company on a 0-100 rubric across four dimensions: regulatory signal strength (0-40), supporting signal reinforcement (0-30), ICP fit (0-20), and signal freshness (0-10). Then assigns a sales tier: Tier 1 (act now), Tier 2 (nurture), or Tier 3 (monitor)."),
        ("Agent 3: Dossier Compiler", "Compares all five companies side by side and produces an executive report with a batch scorecard, individual company write-ups, a batch intelligence summary, and data quality notes."),
        ("Agent 4: Outreach Drafter", "Writes personalised outreach emails for every Tier 1 and Tier 2 company. Each email references the specific signal that triggered the outreach — no generic templates."),
    ]

    for label, desc in steps:
        _box(pdf, 15, y, 267, 14, GREY_BG, BORDER)
        _text(pdf, 18, y + 1, label, size=8, bold=True, color=NAVY)
        _text(pdf, 18, y + 6.5, desc, size=6.5, color=DARK)
        y += 17


def _draw_page5_signals(pdf):
    """Page 5: Agent 1 output — Tier 1 vs Tier 3 comparison."""
    pdf.add_page()
    _page_header(pdf, "Sample Run: Agent 1 — Signal Research")

    y = 25
    y = _para(pdf, 15, y,
        "Agent 1 searched the public web for each company and returned verified buying signals. "
        "Below is a side-by-side comparison of what the system found for the strongest company "
        "(Anthem — eventual Tier 1) versus the weakest (Compass Pathways — eventual Tier 3).",
        size=8.5, color=DARK, w=260)
    y += 4

    # Two-column layout
    left_x = 15
    right_x = 150
    col_w = 127

    # Anthem (Tier 1)
    _box(pdf, left_x, y, col_w, 8, RED_ACCENT, RED_ACCENT)
    _text(pdf, left_x + 3, y + 1.5, "ANTHEM, INC. — Strong signals found (eventual Tier 1)", size=8, bold=True, color=WHITE)
    ay = y + 10

    signals_anthem = [
        ("REGULATORY ACTION  |  High confidence  |  April 2026",
         "NAIC Consent Order",
         "Anthem is subject to a public regulatory action reported to the National Association "
         "of Insurance Commissioners. This is a formal enforcement event — exactly the type of "
         "regulatory pressure that creates buying urgency for compliance tools."),
        ("REGULATORY ACTION  |  High confidence  |  June 2026",
         "$16M HIPAA Fine",
         "Anthem paid $16 million to the U.S. Department of Health and Human Services for a "
         "HIPAA violation — the largest health data breach fine in U.S. history. A second "
         "enforcement action within 60 days of the first."),
        ("COMPLIANCE HIRING  |  High confidence  |  June 2026",
         "32 Open Compliance Roles",
         "32 Compliance Consultant positions posted on Indeed, confirming active investment in "
         "building out the compliance function — a strong signal of budget allocation."),
    ]

    for meta, title, desc in signals_anthem:
        _text(pdf, left_x + 2, ay, meta, size=5.5, color=SLATE)
        ay += 4
        _text(pdf, left_x + 2, ay, title, size=8, bold=True, color=DARK)
        ay += 5
        ay = _para(pdf, left_x + 2, ay, desc, size=7, color=DARK, w=col_w - 6)
        ay += 2

    # Compass (Tier 3)
    _box(pdf, right_x, y, col_w, 8, SLATE, SLATE)
    _text(pdf, right_x + 3, y + 1.5, "COMPASS PATHWAYS — Weak signals found (eventual Tier 3)", size=8, bold=True, color=WHITE)
    cy = y + 10

    signals_compass = [
        ("REGULATORY ACTION  |  High confidence  |  June 2026",
         "Routine SEC IPO Filing",
         "An SEC F-1/A registration filing describing nominal early-stage activity. This is a "
         "standard IPO disclosure — not an enforcement action, fine, or consent order. It does "
         "not indicate compliance pressure."),
        ("COMPLIANCE HIRING  |  Medium confidence  |  June 2026",
         "VP of Compliance Opening",
         "One VP of Compliance role posted on LinkedIn. A single hire at a 200-person company "
         "indicates a nascent compliance function being built from scratch — not the scaled "
         "program that typically buys enterprise GRC tools."),
        ("M&A / FUNDING  |  High confidence  |  June 2026",
         "$150M Public Offering",
         "Compass Pathways launched a $150 million public offering. Capital raises are common "
         "for biotech companies and do not, on their own, signal compliance tool buying intent."),
    ]

    for meta, title, desc in signals_compass:
        _text(pdf, right_x + 2, cy, meta, size=5.5, color=SLATE)
        cy += 4
        _text(pdf, right_x + 2, cy, title, size=8, bold=True, color=DARK)
        cy += 5
        cy = _para(pdf, right_x + 2, cy, desc, size=7, color=DARK, w=col_w - 6)
        cy += 2

    # Takeaway
    y = max(ay, cy) + 4
    _box(pdf, 15, y, 267, 18, BLUE_BG, BLUE_BORDER)
    _text(pdf, 18, y + 1.5, "Key takeaway:", size=8.5, bold=True, color=NAVY)
    _para(pdf, 18, y + 7,
        "Both companies returned 3 signals, but the quality is dramatically different. Anthem has two "
        "genuine enforcement actions from named regulators (NAIC, HHS) plus active compliance hiring. "
        "Compass Pathways has a routine SEC filing, one job posting, and a capital raise — none of which "
        "indicate compliance pain. The pipeline correctly distinguishes between these.",
        size=7.5, color=DARK, w=258)


def _draw_page6_scoring(pdf):
    """Page 6: Agent 2 scoring + Agent 3 dossier summary."""
    pdf.add_page()
    _page_header(pdf, "Sample Run: Agent 2 — Scoring & Agent 3 — Dossier")

    y = 25
    y = _section_label(pdf, y, "AGENT 2: HOW THE SCORING ENGINE EVALUATED EACH COMPANY")

    # Scorecard table
    cols_w = [50, 28, 28, 28, 28, 22, 22, 22, 45]
    headers = ["Company", "Regulatory", "Supporting", "ICP Fit", "Freshness", "TOTAL", "Tier", "Conf.", "Primary Signal"]
    rows = [
        ("Anthem, Inc.", "38/40", "26/30", "20/20", "9/10", "93", "Tier 1", "High", "NAIC order + HIPAA fine"),
        ("Bank of America", "28/40", "16/30", "20/20", "9/10", "73", "Tier 2", "High", "CFPB order terminated"),
        ("UnitedHealth Group", "28/40", "13/30", "20/20", "8/10", "69", "Tier 2", "High", "DOJ merger settlement"),
        ("JPMorgan Chase", "4/40", "12/30", "20/20", "9/10", "45", "Tier 2", "Med", "Compliance hiring"),
        ("Compass Pathways", "5/40", "13/30", "11/20", "9/10", "38", "Tier 3", "Med", "SEC filing (routine)"),
    ]

    hx = 15
    for h, cw in zip(headers, cols_w):
        _box(pdf, hx, y, cw, 7, NAVY, NAVY)
        _text(pdf, hx + 1.5, y + 1.5, h, size=6, bold=True, color=WHITE)
        hx += cw

    tier_colors = {"Tier 1": (254, 226, 226), "Tier 2": (255, 251, 235), "Tier 3": GREY_BG}
    for ri, row in enumerate(rows):
        ry = y + 7 + ri * 7
        tier = row[6]
        bg = tier_colors.get(tier, GREY_BG)
        rx = 15
        for ci, cw in enumerate(cols_w):
            _box(pdf, rx, ry, cw, 7, bg, BORDER)
            bold = ci == 0 or ci == 5 or ci == 6
            clr = RED_ACCENT if ci == 6 and tier == "Tier 1" else (YELLOW_ACCENT if ci == 6 and tier == "Tier 2" else DARK)
            _text(pdf, rx + 1.5, ry + 1.5, row[ci], size=6, bold=bold, color=clr)
            rx += cw

    y = y + 7 + len(rows) * 7 + 6

    # Scoring narrative for Anthem
    _box(pdf, 15, y, 130, 36, (254, 242, 242), (252, 129, 129))
    _text(pdf, 18, y + 1.5, "Why Anthem scored 93/100 (Tier 1)", size=8.5, bold=True, color=RED_ACCENT)
    _para(pdf, 18, y + 8,
        "Anthem earned 38/40 on regulatory strength because it faces two enforcement "
        "actions from named regulators (NAIC, HHS) within 60 days — exactly the buying "
        "trigger that drives fastest deal cycles. The 32 open compliance roles confirmed "
        "budget allocation (26/30 supporting). Healthcare/Insurance with 100,000 employees "
        "is a perfect ICP match (20/20). All signals are from the last 60 days (9/10 freshness).",
        size=7, color=DARK, w=118)

    # Scoring narrative for Compass
    _box(pdf, 152, y, 130, 36, GREY_BG, BORDER)
    _text(pdf, 155, y + 1.5, "Why Compass scored 38/100 (Tier 3)", size=8.5, bold=True, color=SLATE)
    _para(pdf, 155, y + 8,
        "Compass scored just 5/40 on regulatory strength because its SEC filing is a "
        "routine IPO disclosure, not an enforcement action. A single compliance hire at a "
        "200-person biotech does not indicate scaled GRC need (13/30 supporting). At 200 "
        "employees in biotech, it falls below the enterprise threshold for the platform's core "
        "market (11/20 ICP). No outreach recommended — monitor only.",
        size=7, color=DARK, w=118)

    y += 42

    # Agent 3 summary
    y = _section_label(pdf, y, "AGENT 3: DOSSIER COMPILER — EXECUTIVE SUMMARY")
    _box(pdf, 15, y, 267, 32, PURPLE_BG, PURPLE_BORDER)
    _para(pdf, 18, y + 3,
        "The Dossier Compiler compared all five companies and produced a polished executive report. "
        "Here is the summary it generated:",
        size=7.5, color=SLATE, w=258)
    _para(pdf, 18, y + 12,
        '"5 companies were evaluated: 1 Tier 1, 3 Tier 2, and 1 Tier 3. The single strongest opportunity '
        'is Anthem, Inc., with dual, recent enforcement actions and active compliance hiring. Tier 2 '
        'contains 3 perfect-ICP megacaps with meaningful but lower-urgency signals that justify structured '
        'nurture. Overall signal quality is strong and recent, with primary-source regulatory events at '
        'the top of the batch and only 1 true outlier on ICP fit and urgency."',
        size=8, color=DARK, w=258, bold=False)


def _draw_page7_outreach(pdf):
    """Page 7: Agent 4 output — draft outreach emails."""
    pdf.add_page()
    _page_header(pdf, "Sample Run: Agent 4 — Outreach Emails")

    y = 25
    y = _para(pdf, 15, y,
        "Agent 4 read the dossier report and drafted personalised outreach emails for every Tier 1 and "
        "Tier 2 company. Each email references the specific signal that triggered it — no generic templates. "
        "Below are the actual emails the system produced.",
        size=8.5, color=DARK, w=260)
    y += 4

    # Anthem email (Tier 1)
    _box(pdf, 15, y, 267, 8, RED_ACCENT, RED_ACCENT)
    _text(pdf, 18, y + 1.5, "TIER 1 EMAIL: Anthem, Inc.", size=9, bold=True, color=WHITE)
    y += 10

    _text(pdf, 15, y, "To:", size=7.5, bold=True, color=SLATE)
    _text(pdf, 25, y, "Chief Compliance Officer / Chief Privacy Officer", size=7.5, color=DARK)
    y += 5
    _text(pdf, 15, y, "Subject:", size=7.5, bold=True, color=SLATE)
    _text(pdf, 33, y, "NAIC consent order and HIPAA settlement -- Anthem", size=7.5, bold=True, color=DARK)
    y += 6

    y = _para(pdf, 15, y,
        "The NAIC Consent Order in April and the $16M HIPAA settlement in June put Anthem's privacy "
        "and incident-response controls under simultaneous state and federal scrutiny.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "Remediation under dual actions like this usually forces your team to rebuild reporting, policy, "
        "and training controls while regulators expect faster, cleaner evidence.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "We work with large health insurers to give compliance leadership a single, auditable view of "
        "incidents, policies, and training so enforcement-driven remediation doesn't depend on stitching "
        "together siloed systems.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "Is consolidating breach response, policy attestations, and training data into one place something "
        "you're actively driving as part of the current remediation plan?",
        size=8, bold=True, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "We recently helped a national health insurer harden its HIPAA incident workflow and cut audit "
        "prep time by roughly half during a similar enforcement cycle.",
        size=8, color=SLATE, w=260)
    y += 1
    _text(pdf, 15, y, "Alex, Enterprise Account Executive", size=7.5, color=SLATE)
    y += 8

    # Bank of America email (Tier 2)
    _box(pdf, 15, y, 267, 8, YELLOW_ACCENT, YELLOW_ACCENT)
    _text(pdf, 18, y + 1.5, "TIER 2 EMAIL: Bank of America", size=9, bold=True, color=WHITE)
    y += 10

    _text(pdf, 15, y, "To:", size=7.5, bold=True, color=SLATE)
    _text(pdf, 25, y, "Chief Compliance Officer / VP Compliance", size=7.5, color=DARK)
    y += 5
    _text(pdf, 15, y, "Subject:", size=7.5, bold=True, color=SLATE)
    _text(pdf, 33, y, "CFPB consent order exit at Bank of America", size=7.5, bold=True, color=DARK)
    y += 6

    y = _para(pdf, 15, y,
        "The CFPB's early termination of Bank of America's consent order in June signals that your "
        "remediation work met the bar three years ahead of schedule.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "Coming out of a long-running order, many banks find that the controls, reporting, and training "
        "infrastructure built for remediation are hard to sustain efficiently once the formal oversight ends.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "We help large banks keep a real-time, consolidated view of conduct, policy, and training data "
        "so post-order programs stay exam-ready without maintaining \"war room\" levels of manual effort.",
        size=8, color=DARK, w=260)
    y += 1
    y = _para(pdf, 15, y,
        "As you transition from remediation mode to steady state, are you looking at ways to reduce "
        "manual evidence collection while keeping your CFPB-era control rigor?",
        size=8, bold=True, color=DARK, w=260)
    y += 1
    _text(pdf, 15, y, "Alex, Enterprise Account Executive", size=7.5, color=SLATE)
    y += 10

    # Takeaway
    _box(pdf, 15, y, 267, 20, BLUE_BG, BLUE_BORDER)
    _text(pdf, 18, y + 1.5, "What to notice:", size=8.5, bold=True, color=NAVY)
    _para(pdf, 18, y + 7,
        "The Tier 1 email (Anthem) is direct and urgent — it names both enforcement actions by date and "
        "regulator. The Tier 2 email (Bank of America) is warmer and more patient — it acknowledges the "
        "positive news (early order exit) and positions the product as a way to sustain what they built. "
        "Neither email sounds like a template. Both pass the test: the recipient knows immediately why "
        "this was sent to them, specifically, today.",
        size=7.5, color=DARK, w=255)


# ── Main ────────────────────────────────────────────────────────────────

def generate():
    pdf = DiagramPDF()
    pdf.set_auto_page_break(auto=False)

    _draw_page1(pdf)
    _draw_page2(pdf)
    _draw_page3_overview(pdf)
    _draw_page4_inputs(pdf)
    _draw_page5_signals(pdf)
    _draw_page6_scoring(pdf)
    _draw_page7_outreach(pdf)

    out = Path("output/architecture_diagram.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    print(f"Architecture diagram saved to: {out.resolve()}")
    return str(out.resolve())


if __name__ == "__main__":
    generate()
