# Deal Intelligence Agent

A multi-agent pipeline that discovers B2B sales leads by monitoring global events — regulatory actions, compliance hiring, M&A activity, leadership changes, and technology procurement — then scores each company's risk profile and generates personalised outreach.

Built as a passion project to explore how autonomous AI agents can collaborate on a complex, multi-stage workflow: researching public signals, quantifying risk, comparing companies, and drafting actionable communications — all without human intervention.

## What it does

Given a list of company names, the pipeline:

1. **Researches** each company across public sources for verifiable buying signals
2. **Scores** each company 0–100 on regulatory pressure, supporting signals, ICP fit, and signal freshness
3. **Ranks** companies into action tiers (Tier 1: act now, Tier 2: nurture, Tier 3: monitor)
4. **Compiles** a comparative executive dossier across all companies
5. **Drafts** personalised outreach emails for Tier 1 and Tier 2 companies

A batch of 5 companies runs end-to-end in under 10 minutes.

## Architecture

Four specialised agents, coordinated by an orchestrator:

| Agent | Role | Key capability |
|-------|------|----------------|
| **Signal Researcher** | Two-stage web search → structured extraction | SerperDevTool, quality gates G1–G9 |
| **Scoring Engine** | Quantitative 0–100 scoring → tier assignment | 4-dimension rubric, flag-for-review logic |
| **Dossier Compiler** | Cross-company comparison → executive report | Batch intelligence summary, data quality notes |
| **Outreach Drafter** | Personalised email drafting | Signal-specific hooks, tier-appropriate tone |

The **orchestrator** runs Agent 1 and Agent 2 in parallel across all companies using `ThreadPoolExecutor`, then sequentially feeds results to Agent 3 and Agent 4. Individual company failures don't stop the batch.

### Memory layer

Every agent shares a persistent institutional knowledge store (LanceDB-backed via CrewAI Memory) containing 21 entries across 7 categories: ICP definitions, deal patterns, competitive intelligence, scoring calibration, outreach messaging, regulatory landscape, and industry-specific insights. This acts as a human-in-the-loop — agents recall relevant knowledge during execution to make better-calibrated decisions.

## Tech stack

- **[CrewAI](https://docs.crewai.com/)** — agent orchestration framework
- **LLMs** — OpenAI GPT-5.1 (research, dossier, outreach), Claude Sonnet (scoring)
- **SerperDevTool** — web search for signal discovery
- **LanceDB** — vector storage for institutional knowledge memory
- **fpdf2** — PDF report generation (pure Python, no system dependencies)
- **Pydantic** — typed data contracts for all agent inputs/outputs

## Setup

```bash
# Create virtual environment (Python 3.12+ required)
uv venv --python 3.12 .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY, SERPER_API_KEY, and optionally ANTHROPIC_API_KEY

# Seed institutional knowledge (run once)
python seed_knowledge.py
```

## Usage

```bash
# Run the full pipeline for 5 companies
python test_five_companies.py

# Run signal research only
python run_signal_researcher.py

# Run research + scoring
python run_scoring_engine.py

# Generate architecture diagram PDF
python generate_diagram.py
```

## Output

- `output/scored_results.json` — structured scoring data for all companies
- `output/dossier_report.md` — executive comparison report
- `output/outreach_messages.md` — draft outreach emails
- `output/architecture_diagram.pdf` — pipeline architecture and sample run results

## Project structure

```
├── orchestrator.py          # Coordinates all 4 agents, parallel batch processing
├── signal_researcher.py     # Agent 1: two-stage web search → structured signals
├── scoring_engine.py        # Agent 2: 0-100 scoring → tier assignment
├── dossier_compiler.py      # Agent 3: cross-company executive report
├── outreach_drafter.py      # Agent 4: personalised outreach emails
├── models.py                # Pydantic schemas for all data contracts
├── memory_config.py         # CrewAI Memory configuration (LanceDB)
├── seed_knowledge.py        # 21 institutional knowledge entries
├── output_logger.py         # Structured logging for agent outputs
├── generate_diagram.py      # Architecture diagram PDF generator
├── config/
│   ├── agents.yaml          # Signal researcher agent definitions
│   ├── tasks.yaml           # Signal research task prompts
│   ├── scoring_agents.yaml  # Scoring engine agent definitions
│   ├── scoring_tasks.yaml   # Scoring rubric and tier decision rules
│   ├── dossier_agents.yaml  # Dossier compiler agent definition
│   ├── dossier_tasks.yaml   # Report format specification
│   ├── outreach_agents.yaml # Outreach drafter agent definition
│   └── outreach_tasks.yaml  # Outreach task prompt
├── test_five_companies.py   # Full pipeline test script
├── requirements.txt
└── .env.example
```

## Why this project

I wanted to understand how multiple AI agents can divide a complex, judgment-heavy task — the kind that normally requires a team of analysts and SDRs — into discrete, composable steps. The interesting parts:

- **Signal quality matters more than signal quantity.** Two enforcement actions from named regulators are worth more than ten generic news articles. The quality gates (G1–G9) enforce this programmatically.
- **Scoring needs calibration, not just rules.** The institutional knowledge memory gives agents the equivalent of "I've seen 500 of these" judgment without fine-tuning.
- **Parallel execution with fault tolerance** is essential for batch workflows. One company timing out shouldn't block four others.
- **The memory layer is the closest thing to human-in-the-loop** without actually requiring a human at runtime. It encodes organisational wisdom that would otherwise live in a senior salesperson's head.
