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

## 2026-08-24 · Session 5 — M2 done: GitHub live, durable runs, HITL approval UI

**Time:** 00:45 – 02:00 IST · **Phase:** Production patterns land · **Milestone:** M2 ✅ · **Repo public** 🎉

### What shipped

| Item | Detail |
|---|---|
| **GitHub remote** | `github.com/Rythamo8055/aegis-support-copilot` — created via `gh`, all commits pushed to `main` |
| `graph/nodes.py` | New `review_gate` node: fires LangGraph `interrupt()` with ticket+draft+reason payload; applies approve / reject / edit decisions |
| `graph/builder.py` | `hitl` flag wires gate conditionally; escalation → *(needs review?)* → review_gate / END |
| `state.py` routing change | Only `priority=critical` skips resolution now; flagged-but-non-critical tickets get a draft **and** the human gate |
| `pipeline.run_ticket()` | Default `hitl=True` — production entry point is safe by default |
| `scripts/demo_durable_resume.py` | Live demo: pause at gate → "crash" → fresh process recovers pending node from SQLite → resume approve |
| `app/approval_ui.py` | Streamlit review console: submit ticket → pause screen (category/priority/reason/draft) → Approve / Edit / Reject → final outcome |
| tests | +6 offline (`test_hitl`, `test_durability`); shared fakes extracted to `tests/helpers.py`. **20 passing total** |

### Live durability proof (real LLMs, real SQLite)

| Phase | What happened |
|---|---|
| 1. Run | Refund-overdue ticket drafted (grounded in KB-002 timelines), escalated → **paused at `review_gate`** |
| 2. Crash | Graph objects destroyed; only `checkpoints.db` survives |
| 3. Restart | Fresh process, new graph instance → `get_state` recovered pending node `('review_gate',)` from disk |
| 4. Resume | `Command(resume=approve)` → status `approved`, grounded reply finalized |

### Why

- **Gate after drafting, not instead of it:** first version skipped resolution for *any* escalated ticket — the human then had nothing to review. Fixed semantics: critical/security cases skip auto-drafting (per KB-003 dispute policy); everything else gets agent-assisted draft + mandatory sign-off.
- **Separate `review_gate` node** rather than `interrupt()` inside the escalation node: avoids re-running the escalation LLM call on resume (nodes replay from the top).
- **SQLite checkpointer now:** same API as Postgres later; durability demo works on a laptop.

### Gotchas

| Gotcha | Fix |
|---|---|
| `SqliteSaver.from_conn_string(...)` returns a context manager, not a saver — passing it to `compile()` explodes deep inside pregel | Use explicit `sqlite3.connect()` or a `with` block |
| `Command(resume=...)` with no pending interrupt silently re-runs the graph from START | Tests must assert the pause actually happened first |
| Cross-test imports (`from tests.test_hitl import ...`) fail — tests dir isn't a package | Shared fakes moved to `tests/helpers.py` |

### Next

- [ ] **M3a** — golden dataset v1 (~60–100 tickets incl. edge cases) + labeling
- [ ] **M3b** — Ragas/DeepEval harness: faithfulness/citation metrics per prompt version
- [ ] **M3c** — judge calibration ≥0.8 agreement vs human labels
- [ ] **M4** — CI eval gate + deploy + demo video

---

## 2026-08-24 · Session 4 — M1c: RAG retrieval, citation grounding, tracing hooks

**Time:** 00:00 – 00:40 IST · **Phase:** Pipeline gets its knowledge · **Milestone:** M1c ✅ (tracing wired, server deferred)

### What shipped

| File | Purpose |
|---|---|
| `kb/documents.py` | 12-doc mini-KB: refund/duplicate-charge policy, chargeback handling, escalation matrix, de-escalation script |
| `kb/retriever.py` | `KBRetriever` over embedded ChromaDB (`PersistentClient`), returns scored `Chunk`s |
| `kb/seed.py` | `uv run python -m aegis.kb.seed` → upserts KB into `./chroma` (12 docs seeded) |
| `graph/prompts.py` | All prompts versioned (`*_V1`) + `PROMPT_VERSIONS` registry — changes require a bump + devlog entry |
| `graph/nodes.py` | Resolution node now retrieval-grounded; **citation filter drops LLM-cited ids not present in retrieved set** |
| `graph/builder.py` / `pipeline.py` | Retriever injection through to graph; `run_ticket()` convenience entry with callbacks + thread_id |
| `observability.py` | Env-gated Langfuse callback handler; **no-ops silently when keys absent** |
| tests | 4 new offline tests (14 total): hallucinated-citation filtering, context formatting, KB integrity |

### Live E2E results (both paths proven)

| Ticket | Triage | Route taken | Retrieval | Outcome |
|---|---|---|---|---|
| "Refund not received in 10 days… disputing with bank" | billing/high/**escalate** | triage → escalation (RAG skipped by design) | — | Escalation reason + first action for human; matches KB-003 dispute policy |
| "Need GST invoice copies from last year" | billing/medium/normal | triage → resolution → escalation | pulled `KB-001`, `KB-010`, `KB-012` | Draft grounded in KB-012 only; citations = `["KB-012"]`; correct self-service answer |

### Why

- **Citation grounding filter:** the eval suite (M3) needs faithfulness we can enforce mechanically — if the model cites a doc it wasn't shown, that's a bug we catch at runtime, not just at eval time.
- **Escalation-first routing validated live:** dispute-threat tickets never get an auto-drafted reply — exactly what the KB's chargeback policy demands. The conditional edge is doing policy work, not just demo work.
- **Tracing degrades gracefully:** no Docker on this machine for self-hosted Langfuse; env-gated no-op keeps local dev clean, real Langfuse lands with docker-compose at deploy (M2/M4).

### Decisions log (new)

| # | Decision | Rationale | Alternatives rejected |
|---|---|---|---|
| D12 | Versioned prompts (`*_V1` registry) | M3 compares prompt versions; CI gate diffs against baseline | Free-floating prompt strings |
| D13 | Citation filter (LLM ids ∩ retrieved ids) | Runtime faithfulness enforcement; feeds M3 metrics | Trusting raw model citations |
| D14 | Langfuse env-gated optional tracing | No local Docker today; zero-friction offline tests | Blocking startup on missing Langfuse |

### Gotchas

- Chroma default embedding downloads an ONNX model on first seed (~1 min) — expected, one-time.
- Escalated tickets legitimately have `draft_reply=None` — UI (M2) must render "routed to human" state distinctly.

### Next

- [ ] Create GitHub remote + push (**D9 gate now satisfied**: M1 compiles, 14 tests green)
- [ ] **M2a** — SQLite checkpointer via `run_ticket(thread_id=...)`; kill-and-resume demo
- [ ] **M2b** — Streamlit approval UI consuming `interrupt()`

---

## 2026-08-23 · Session 3 — M1b: router, preflight, agent graph skeleton

**Time:** 23:00 – 23:30 IST · **Phase:** First real code · **Milestone:** M1b ✅

### What

- `config.py` — pydantic-settings loading `.env` (groq/gemini keys, both model names, Gemma-only per owner policy).
- `llm/router.py` — `LLMRouter`: Groq primary → Gemma fallback, provider-agnostic `invoke(prompt) -> str`; providers built via `build_providers()` so tests inject fakes.
- `preflight.py` — D11 implemented: `uv run python -m aegis.preflight` pings **both** providers before any app usage; exits non-zero on failure. Live run: groq OK, gemma OK.
- `graph/` — LangGraph skeleton: `TicketState`, triage → (conditional) → resolution → escalation → END; nodes are factories taking the router; strict-JSON prompts with tolerant `extract_json` + safe fallbacks (fail-open with defaults, never crash on bad model output).
- Tests: **10 passed, offline only** — scripted `ScriptedRouter` + langchain fake models prove routing, conditional branch skipping resolution, and garbage-output resilience without touching the network.
- Live E2E acceptance: a double-charge billing ticket ran through the real graph — triaged `billing/high/escalate`, conditional edge correctly skipped resolution, escalation agent returned reason + recommended action.

### Why

- **Nodes as factories over injected routers:** keeps graph logic testable offline and later swappable for eval harness mocks (M3) — no monkeypatching needed.
- **Fail-open parsing:** support pipeline should degrade to defaults + human review rather than die mid-run; ties into M2's HITL gate.
- **Checkpointer left out of `build_graph` defaults:** MemorySaver forces `thread_id` config on every invoke; durable persistence arrives properly in M2 (SQLite), so skeleton stays friction-free.

### Gotchas discovered (worth remembering)

1. `reasoning_effort` is now an explicit first-class `ChatGroq` field — passing it via `model_kwargs` raises a pydantic error.
2. `GenericFakeChatModel` takes `messages=` iterator, not `responses=`.
3. gpt-oss reasoning eats token budget: always budget `max_completion_tokens` generously or set `reasoning_effort=low`.
4. `langchain_google_genai` emits a noisy "AFC not recommended" warning from google-genai internals — harmless; revisit if it pollutes traces in M1c.

### Next

- [ ] **M1c** — Langfuse tracing on every node; ChromaDB retriever + seeded mini-KB wired into resolution prompt; prompt versioning convention
- [ ] Create GitHub remote + push (D9 gate: M1 compiles + tests green ✅ — can push after M1c)
- [ ] **M2** — SQLite checkpointer + kill-and-resume demo; Streamlit approval UI via `interrupt()`

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

### Addendum 2 · 23:55 IST — Model policy update

- **Owner directive:** no `gemini-*` models; Google side must use **`gemma-4-31b-it`** only (confirmed available on our key alongside `gemma-4-26b-a4b-it`). Router becomes **Groq `openai/gpt-oss-120b` → Google `gemma-4-31b-it`**.
- **New convention (D11):** *preflight connectivity test before any model is used by the app* — config load pings both providers and fails fast with a clear error. Implemented as part of M1c router work.
- Live tests passed: gpt-oss-120b needs `max_completion_tokens` head-room for hidden reasoning (`reasoning_effort=low` keeps it cheap); gemma-4-31b-it responds normally via `generateContent`.
- Process note: a malformed tool call briefly overwrote this devlog; restored from HEAD within a minute — no history lost, and the incident is logged here on principle.

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
