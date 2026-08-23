# Aegis: Production Support Copilot

Multi-agent customer-support copilot with **durable execution**, **human-in-the-loop approvals**,
and an **LLM-as-a-judge eval suite wired as a CI quality gate**.

[![tests-and-eval-gate](https://github.com/Rythamo8055/aegis-support-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/Rythamo8055/aegis-support-copilot/actions/workflows/ci.yml)

## Architecture

```
Ticket ──> Triage agent ──> RAG resolution (ChromaDB + citations) ──> Escalation agent ──> [HITL review gate] ──> Reply
                │                                                            │
                └──────────── critical tickets skip drafting ────────────────┘
```

- **Orchestration:** LangGraph (`StateGraph`, conditional edges, `interrupt()`/`Command(resume=)`)
- **Models:** Groq `openai/gpt-oss-120b` primary → Google `gemma-4-31b-it` fallback (router with automatic failover)
- **RAG:** embedded ChromaDB, 12-doc support KB, citation grounding filter (hallucinated citations dropped at runtime)
- **Durability:** SQLite checkpointer — runs pause/resume across process restarts
- **HITL:** escalated tickets pause at a review gate; Streamlit console for approve / edit / reject

## Eval gate (the differentiator)

`datasets/golden_v1.jsonl` holds **60 human-labeled tickets** including edge cases (vague,
angry, non-English, legal holds, breaches). Every PR is scored against the committed baseline:

| Metric | Baseline |
|---|---|
| Triage category accuracy | 86.7% |
| Escalation agreement accuracy | 81.7% |
| Citation recall | 53.4% |
| Grounding violations | 0.0 |

CI blocks any regression > 2 points (`.github/workflows/ci.yml`, `src/aegis/evals/gate.py`).

## Quickstart

```bash
uv sync                                  # install (Python 3.12)
cp .env.example .env                     # add GROQ_API_KEY / GEMINI_API_KEY
uv run python -m aegis.preflight         # verify provider connectivity (fail fast)
uv run python -m aegis.kb.seed           # index the knowledge base
uv run streamlit run app/approval_ui.py  # open the review console
```

## Demo scripts

```bash
uv run python scripts/demo_durable_resume.py   # pause -> "crash" -> resume from disk
uv run python scripts/run_evals.py             # full eval vs golden dataset
uv run python scripts/calibrate_judge.py       # LLM-judge vs human labels (target >= 0.8)
```

## Tests

36 offline unit tests — no network needed: routing/failover, graph branches, HITL
pause/resume/approve/edit/reject, durability across restarts, citation filtering,
dataset validity, metric math, judge parsing.

## Docs

- [PLAN.md](./PLAN.md) — architecture, stack rationale, milestones
- [DEVLOG.md](./DEVLOG.md) — every session: what was built, why, and what broke
