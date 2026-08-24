import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from aegis.evals.dataset import load_golden
from aegis.evals.judge import JUDGE_VERSIONS, judge_faithfulness, judge_needs_human
from aegis.evals.runner import evaluate_case
from aegis.kb.retriever import KBRetriever
from aegis.llm.router import LLMRouter

TARGET_AGREEMENT = 0.8


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cases = load_golden()
    if args.limit:
        cases = cases[: args.limit]
    router = LLMRouter()
    retriever = KBRetriever()

    esc_correct = 0
    faith_scores: list[int] = []
    details = []

    for index, case in enumerate(cases, start=1):
        try:
            predicted_human = judge_needs_human(router, case.subject, case.body)
        except Exception as exc:
            predicted_human = not case.needs_escalation
            details.append({"case_id": case.id, "error": str(exc)[:100]})
        if predicted_human == bool(case.needs_escalation):
            esc_correct += 1

        result = evaluate_case(case, router, retriever)
        if result.draft_reply and result.retrieved_ids and not result.error:
            chunks = retriever.retrieve(case.query, k=3)
            snippets = [f"[{chunk.id}] {chunk.text}" for chunk in chunks]
            try:
                verdict = judge_faithfulness(
                    router, case.subject, case.body, result.draft_reply, snippets
                )
                faith_scores.append(1 if verdict["verdict"] == "faithful" else 0)
            except Exception as exc:
                details.append({"case_id": case.id, "faithfulness_error": str(exc)[:100]})

        if index % 5 == 0:
            print(f"  calibrated {index}/{len(cases)}", flush=True)

    agreement = esc_correct / len(cases) if cases else 0.0
    faithfulness_rate = (
        sum(faith_scores) / len(faith_scores) if faith_scores else 0.0
    )

    payload = {
        "judge_versions": JUDGE_VERSIONS,
        "n_cases": len(cases),
        "escalation_agreement": round(agreement, 4),
        "target_agreement": TARGET_AGREEMENT,
        "meets_target": agreement >= TARGET_AGREEMENT,
        "faithfulness_pass_rate": round(faithfulness_rate, 4),
        "n_faithfulness_judged": len(faith_scores),
        "generated_at": datetime.now(UTC).isoformat(),
        "details": details,
    }
    out = Path("evals/reports/judge_calibration.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in payload.items() if k != "details"}, indent=2))
    print(f"saved -> {out}")
    return 0 if payload["meets_target"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
