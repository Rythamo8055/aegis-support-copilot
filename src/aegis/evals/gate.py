import argparse
import json
import sys
from pathlib import Path

BASELINE_PATH = Path("evals/baseline.json")
CORE_METRICS = (
    "triage_category_accuracy",
    "priority_accuracy",
    "escalation_agreement_accuracy",
    "citation_recall",
)
FLOORED_METRICS = ("grounding_violation_rate",)
DEFAULT_THRESHOLD = 0.02


def compare(current: dict, baseline: dict, threshold: float = DEFAULT_THRESHOLD) -> list[str]:
    failures: list[str] = []
    cur = current["metrics"]
    base = baseline["metrics"]

    for key in CORE_METRICS:
        drop = base.get(key, 0.0) - cur.get(key, 0.0)
        if drop > threshold:
            failures.append(
                f"{key}: {base[key]:.4f} -> {cur[key]:.4f} (dropped {drop:.4f} > {threshold})"
            )

    for key in FLOORED_METRICS:
        rise = cur.get(key, 0.0) - base.get(key, 0.0)
        if rise > threshold:
            failures.append(
                f"{key}: {base[key]:.4f} -> {cur[key]:.4f} (rose {rise:.4f} > {threshold})"
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, help="path to freshly produced report JSON")
    parser.add_argument("--baseline", default=str(BASELINE_PATH))
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    current = json.loads(Path(args.current).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    failures = compare(current, baseline, args.threshold)

    print("metric | baseline | current")
    for key in CORE_METRICS + FLOORED_METRICS:
        b, c = baseline["metrics"].get(key), current["metrics"].get(key)
        flag = " <-- REGRESSION" if any(f.startswith(key) for f in failures) else ""
        print(f"{key} | {b} | {c}{flag}")

    if failures:
        print("\nEVAL GATE: BLOCKED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nEVAL GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
