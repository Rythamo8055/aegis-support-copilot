# Project 1 — Aegis: Production Support Copilot (Multi-Agent + CI-Gated Evals)

> **One-liner:** A multi-agent customer-support copilot with durable execution, human-in-the-loop
> approval, and an LLM-as-a-judge eval suite that **blocks regressions in CI** — the exact shape of
> system enterprises deploy in production.

**Status:** 📋 Planning
**Target duration:** 3–4 weeks part-time
**Repo name (when published):** `aegis-support-copilot`

---

## Why this project (market evidence)

| Signal | Evidence |
|---|---|
| Agents = #1 skill by job count | 2,894 postings mention "agents" vs 2,775 for "LLM" (aidevboard 2026) |
| LangGraph is the enterprise default | 22.1% of agentic listings; used by Klarna, Uber, LinkedIn, JPMorgan |
| Evals = scarcest skill | Required in ~40% of AI-eng postings, "sharply up from near-zero"; eval engineers $160–240K |
| Interview reality | Google/Netflix/OpenAI take-homes now expect: architecture → implementation → **eval suite w/ metrics** → safety tests → cost/latency numbers. "Chatbot demo with no evals" is explicitly rejected |

This project deliberately covers the **two scarcest, best-paid clusters in one artifact**: agents + evals.

---

## What we're building

A support copilot that handles inbound customer tickets end-to-end:

```
Ticket in → Triage agent → Knowledge lookup (RAG) → Resolution draft
                │                                        │
                ▼                                        ▼
        Escalation agent ────────────────► Human-in-the-loop review gate
                                                         │
                                                         ▼
                                              Response sent + logged
```

### Core capabilities

1. **Triage agent** — classifies intent/severity/priority, routes to the right sub-agent.
2. **RAG resolution agent** — answers from a knowledge base (reuse patterns proven in docuqa-rag:
   hybrid search + reranking + citations), drafts a reply with `[source]` citations.
3. **Escalation agent** — detects refund/legal/angry-customer cases, writes escalation summary for humans.
4. **Human-in-the-loop gate** — LangGraph `interrupt` before any response is "sent"; reviewer approves / edits / rejects via a small web UI.
5. **Durable execution** — every run checkpointed; a crashed run resumes where it stopped (LangGraph checkpointer + Postgres/SQLite).
6. **Observability** — full traces per run in Langfuse: tokens, cost, latency, tool calls, retries.

### The differentiator: evals as a CI quality gate

- **Golden dataset**: ~60–100 labeled tickets (intents, expected behaviors, grounded-answer pairs) built from a public dataset (e.g., Banking77 / customer-support tickets on HF) + synthetic cases.
- **Metrics**:
  - Retrieval: hit-rate@k, MRR (separate from generation)
  - Generation: faithfulness, answer-relevance, citation correctness (Ragas)
  - Agent behavior: routing accuracy, tool-call correctness, refusal rate on out-of-scope
  - Safety: prompt-injection resistance score on adversarial ticket set
  - Ops: p95 latency, cost per resolved ticket
- **LLM-as-a-judge** calibrated against a human-labeled subset (report judge-vs-human agreement ≥ 0.8).
- **CI gate**: GitHub Actions runs the eval suite on every PR touching agent code/prompts;
  PR fails if faithfulness drops > 2% or routing accuracy < threshold vs baseline stored in repo.
- **Prompt regression tracking**: every prompt version pinned; eval scores reported per version.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph (Python) | Enterprise default, durable checkpoints, interrupts |
| LLMs | Groq/Gemini primary + OpenAI fallback (router pattern from docuqa-rag) | Cost + resilience story |
| RAG store | ChromaDB or pgvector + BM25 hybrid | Proven pattern already shipped |
| Evals | Ragas + DeepEval + pytest | Default stack in job postings |
| Observability | Langfuse (self-hosted docker-compose) | Traces + cost per run, no vendor lock-in |
| HITL UI | FastAPI + minimal Next.js/Streamlit review screen | Speed over beauty |
| Infra | Docker Compose, GH Actions | Deployment + CI gate |

---

## Milestones

- [ ] **M1 (week 1)** — Repo scaffold, LangGraph graph skeleton, triage + RAG agents working locally, Langfuse tracing wired.
- [ ] **M2 (week 2)** — Checkpointer + interrupt-based HITL review UI; durable resume demo (kill mid-run, restart).
- [ ] **M3 (week 3)** — Golden dataset v1 (~60 tickets), eval harness (Ragas/DeepEval), judge calibration report.
- [ ] **M4 (week 4)** — CI gate in GitHub Actions, baseline JSON committed, README with metrics table, demo video, deploy (Render/Fly free tier).

## Definition of done

- [ ] Live deployed instance + demo video (kill/resume shown)
- [ ] Eval report in README: table of metrics across ≥3 prompt/model versions
- [ ] Red PR example: a PR that degrades faithfulness visibly fails CI (screenshot)
- [ ] Cost-per-ticket and p95 latency documented

## Resume bullets this earns us

- "Built multi-agent support copilot (LangGraph) with durable execution and human-in-the-loop approvals; resumed crashed runs without state loss."
- "Designed CI-gated LLM eval pipeline (Ragas/DeepEval, calibrated LLM-judge at ≥0.8 human agreement) blocking regressions on every PR."
- "Cut hallucinated answers X% via hybrid retrieval + reranking + grounding checks; tracked cost/ticket and p95 latency."

## Out of scope (v1)

Telephony/voice, multi-tenant auth, fine-tuning (stretch: QLoRA'd small model for triage classification later).
