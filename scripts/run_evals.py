import argparse
import json
from dataclasses import asdict
from pathlib import Path

from aegis.evals.gate import BASELINE_PATH, DEFAULT_THRESHOLD, compare
from aegis.evals.runner import run_evaluation, save_report
from aegis.kb.retriever import KBRetriever
from aegis.llm.router import LLMRouter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    router = LLMRouter()
    retriever = KBRetriever()

    report, _ = run_evaluation(router, retriever=retriever, limit=args.limit)
    report_path = save_report(report)
    print(f"report -> {report_path}")
    print(json.dumps(report.metrics, indent=2))

    if args.write_baseline:
        Path(BASELINE_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(BASELINE_PATH).write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
        print(f"baseline written -> {BASELINE_PATH}")

    if args.gate:
        baseline = json.loads(Path(BASELINE_PATH).read_text(encoding="utf-8"))
        failures = compare(asdict(report), baseline, args.threshold)
        for failure in failures:
            print(f"REGRESSION: {failure}")
        return 1 if failures else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
