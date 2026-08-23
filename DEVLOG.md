# DEVLOG — Aegis: Production Support Copilot

Running build log for the project described in [PLAN.md](./PLAN.md).
Newest sessions first. Each entry captures **what we built, why we made those
decisions, a summary of the working session (conversations included), and what
is queued next** — with timestamps.

Entry format:

- **What** — concrete work done
- **Why** — the reasoning / trade-offs behind it
- **Session notes** — condensed summary of the human + agent conversation that led here
- **Next** — queue for the next session, with checkboxes

---

## 2026-08-23 · Session 2 — Harness research + stack decisions locked

**Time:** 22:30 – 23:00 IST · **Phase:** Planning → Requirements frozen · **Milestone:** M0 → M1

### What

- Confirmed scope: **multi-agent pipeline** (triage → RAG resolution → escalation → HITL gate), explicitly *not* a chatbot.
- Settled the "do we build a harness?" question: **LangGraph is the harness** (graph execution, state, tool loop, checkpointing, `interrupt`/resume). We build the app layer: agent nodes, tools, state schema, LLM router — and the **eval harness**, which is genuinely ours.
- Researched the freshly released **DeepSeek Harness (`dsh`)** + its underlying **Cordis paper** (*"A Programming Paradigm for Spatiotemporal Composability"*, PKU + DeepSeek): MIT-licensed, everything-is-a-plugin agent harness, dev preview since 2026-08-13.
- Locked remaining stack decisions via Q&A with the project owner (see D5–D9).

### Why

- **dsh considered → not adopted:** TypeScript/Node, day-old preview with promised breaking changes; Aegis needs Python-side durable checkpointing + `interrupt()` HITL that LangGraph ships today. Kept as *reference architecture* for plugin-style boundaries between our nodes/tools/approval UI.
- Frozen decisions remove all ambiguity before scaffolding; each maps to a concrete milestone task.

### Decisions log (new)

| # | Decision | Rationale | Alternatives rejected |
|---|---|---|---|
| D5 | Router order: **Groq primary → Gemini fallback** | Keys actually on hand; matches plan's intent | OpenAI-first (no key yet); DeepSeek in router |
| D6 | **ChromaDB embedded** for RAG v1 | Zero infra for a 60–100 ticket demo; swappable behind a retriever interface | pgvector+Postgres from day 1 (infra overhead) |
| D7 | **Streamlit** approval UI (M2) | Ships in hours; differentiator is eval/CI gate, not pixels | Next.js minimal (deferred; revisit if time allows) |
| D8 | **uv** for Python tooling | Fast resolver + lockfile; 2026 default for new projects | pip+venv, poetry |
| D9 | GitHub remote **after** M1 scaffold lands | First pushed commit shows real code, cleaner history | Pushing bootstrap-only repo now |
| D10 | dsh/Cordis → reference reading only | See above | Adopting dsh as our harness |

### Addendum · 23:40 IST — API keys verified

- Both provider keys received and stored in local `.env` (gitignored, never committed); verified via live API calls: Groq `200`, Gemini `200`.
- **Router defaults chosen from actually-available models:** Groq → `openai/gpt-oss-120b`; Gemini → `gemini-2.5-flash`. Note: this Groq account exposes gpt-oss/compound/qwen models but *not* `llama-3.3-70b-versatile` — plan text updated accordingly at implementation time.
- No further keys needed until Langfuse (self-hosted, generates its own) or optional OpenAI fallback.

### Next

- [x] **M1a** — install uv; scaffold package (`aegis` src-layout, pyproject, ruff, pytest)
      *(done 23:10 IST — uv 0.12.5, Python 3.12 venv, 2 tests passing, ruff clean)*
- [ ] **M1b/c** — LangGraph skeleton + Groq/Gemini router + Langfuse tracing
- [ ] Create remote `aegis-support-copilot` and push once M1 compiles + tests pass (D9)

---

## 2026-08-23 · Session 1 — Bootstrap: skills, git repo, devlog

**Time:** 22:00 – 22:30 IST · **Phase:** Planning → Repo initialized · **Milestone:** M0 (setup)

### What

- Explored the workspace via an agent sweep; confirmed the directory contained
  only `PLAN.md` — no code, no deps, no git history of its own.
- Used the open skills ecosystem (`npx skills`, https://skills.sh) to curate and
  install 5 agent skills matched to our planned stack.
- Initialized a standalone git repository (`main` branch) inside
  `01-agentic-support-copilot/`.
- Created this devlog as the first-class artifact of the project.

### Why

- **Standalone repo instead of committing into the parent `development_walkins`
  repo:** PLAN.md targets a published repo named `aegis-support-copilot`; an
  isolated history keeps commits clean and makes `gh repo create` trivial later.
- **Skills committed into the repo (`.agents/skills/`) rather than installed
  globally:** they become part of the project's context — anyone (or any agent)
  cloning the repo gets the same LangGraph/FastAPI/testing guidance.
- **Devlog-first workflow:** decisions are cheap to make and expensive to
  reconstruct. Logging *why* now preserves the rationale for the eval report,
  README narrative, and demo video later (all required by PLAN.md's definition
  of done).

### Session notes (conversation summary)

1. Asked the explore agent to survey the project; result: pre-implementation,
   single-file plan ("Aegis"), all 4 milestones unchecked.
2. User directive: bootstrap properly before writing code — (a) pull the latest
   community agent-skills for vibecoding, (b) init git, (c) keep a devlog from
   day one covering decisions, session summaries, and next steps.
3. Ran skill discovery across `python`, `langgraph`, `fastapi`,
   `github actions ci-cd`, and `docker compose`.
4. Applied quality bar (official source or ≥1K installs):
   - ✅ Installed 5 skills (table below)
   - ❌ Skipped CI/CD and docker-compose skills — best options were <3K installs
     from unknown authors; we'll write the GitHub Actions workflow ourselves in M4.
5. Initialized repo on `main`, wrote `.gitignore`, README stub, and this devlog;
   made the initial commit.

### Skills installed → `.agents/skills/`

| Skill | Source | Installs | Maps to plan |
|---|---|---|---|
| `langgraph-persistence` | langchain-ai (official) | 13.7K | checkpointer / durable runs (M2) |
| `langgraph-human-in-the-loop` | langchain-ai (official) | 13.1K | HITL review gate via `interrupt` (M2) |
| `langgraph-docs` | langchain-ai/deepagents (official) | 4.5K | graph skeleton, agents (M1) |
| `fastapi` | fastapi (official) | 8.1K | approval API/UI backend (M2) |
| `python-testing-patterns` | wshobson/agents | 30.6K | pytest eval harness (M3) |

### Decisions log

| # | Decision | Rationale | Alternatives rejected |
|---|---|---|---|
| D1 | Standalone git repo in this folder | Target published repo; clean history | Committing under parent walkins repo |
| D2 | Python (per PLAN.md), LangGraph orchestration | Plan already fixed stack; official skills reinforce it | TS/LangGraph.js |
| D3 | Curated skills over "install everything" | Trust = official source or high installs; fewer stale instructions | Bulk-installing search results |
| D4 | Devlog committed from commit #1 | Rationale capture is part of deliverable, not an afterthought | Local-only notes |

### Next

- [ ] **M1a** — scaffold Python project (`pyproject.toml`, src layout, ruff, pytest)
- [ ] **M1b** — LangGraph skeleton: triage → resolution → escalation nodes, Langfuse tracing
- [ ] **M1c** — LLM router (Groq/Gemini primary, OpenAI fallback) + `.env.example`
- [ ] **M2** — checkpointer + HITL approval UI + kill-and-resume demo
- [ ] **M3** — golden dataset v1 (~60–100 tickets), Ragas/DeepEval harness, judge calibration ≥ 0.8 agreement
- [ ] **M4** — CI eval gate (blocks regressions > 2%), baseline metrics JSON, deploy + demo video

---
