# Aegis: Production Support Copilot

A multi-agent customer-support copilot with durable execution and an LLM-as-a-judge
eval suite that runs as a **CI quality gate**.

- Triage agent → RAG resolution (hybrid search + citations) → escalation agent → human-in-the-loop approval
- Checkpointed runs that resume after crashes
- Eval gate blocks PRs on quality regressions (e.g. faithfulness drop > 2%)

**Status:** 🚧 bootstrap — see [PLAN.md](./PLAN.md) for architecture, stack, and milestones,
and [DEVLOG.md](./DEVLOG.md) for the running build log.
