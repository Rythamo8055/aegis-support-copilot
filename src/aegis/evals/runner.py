import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aegis.evals.dataset import DEFAULT_DATASET, GoldenCase, load_golden
from aegis.graph.builder import build_graph

DEFAULT_REPORT_DIR = Path("evals/reports")


@dataclass
class CaseResult:
    case_id: str
    predicted_category: str
    predicted_priority: str
    predicted_escalation: bool
    citations: list[str]
    retrieved_ids: list[str]
    draft_reply: str
    error: str = ""


@dataclass
class EvalReport:
    dataset: str
    n_cases: int
    prompt_versions: dict
    models: dict
    generated_at: str
    metrics: dict = field(default_factory=dict)


def evaluate_case(case: GoldenCase, router, retriever=None) -> CaseResult:
    app = build_graph(router, retriever=retriever, hitl=False)
    try:
        state = app.invoke(
            {"ticket_id": case.id, "subject": case.subject, "body": case.body}
        )
        return CaseResult(
            case_id=case.id,
            predicted_category=state.get("category", ""),
            predicted_priority=state.get("priority", ""),
            predicted_escalation=bool(state.get("needs_escalation", False)),
            citations=list(state.get("citations", [])),
            retrieved_ids=list(state.get("retrieved_ids", [])),
            draft_reply=str(state.get("draft_reply", "")),
        )
    except Exception as exc:
        return CaseResult(
            case_id=case.id,
            predicted_category="",
            predicted_priority="",
            predicted_escalation=False,
            citations=[],
            retrieved_ids=[],
            draft_reply="",
            error=f"{type(exc).__name__}: {exc}",
        )


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def compute_metrics(cases: list[GoldenCase], results: list[CaseResult]) -> dict:
    by_id = {r.case_id: r for r in results}
    paired = [(c, by_id[c.id]) for c in cases if c.id in by_id]

    errors = sum(1 for _, r in paired if r.error)

    cat_acc = _mean(r.predicted_category == c.category for c, r in paired)
    prio_acc = _mean(r.predicted_priority == c.priority for c, r in paired)

    esc_pairs = [(bool(c.needs_escalation), r.predicted_escalation) for c, r in paired]
    tp = sum(1 for g, p in esc_pairs if g and p)
    fp = sum(1 for g, p in esc_pairs if not g and p)
    fn = sum(1 for g, p in esc_pairs if g and not p)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    recalls = []
    violations = 0
    checked = 0
    for c, r in paired:
        if c.expected_kb_ids:
            exp = set(c.expected_kb_ids)
            got = set(r.citations)
            recalls.append(len(exp & got) / len(exp))
        if r.citations and r.retrieved_ids:
            checked += 1
            if not set(r.citations) <= set(r.retrieved_ids):
                violations += 1

    return {
        "n_evaluated": len(paired),
        "pipeline_errors": errors,
        "triage_category_accuracy": round(cat_acc, 4),
        "priority_accuracy": round(prio_acc, 4),
        "escalation_agreement_accuracy": round(_mean(g == p for g, p in esc_pairs), 4),
        "escalation_f1": round(f1, 4),
        "citation_recall": round(_mean(recalls), 4),
        "n_citation_cases": len(recalls),
        "grounding_violation_rate": round(violations / checked, 4) if checked else 0.0,
    }


def run_evaluation(
    router,
    retriever=None,
    dataset_path=None,
    limit=None,
    progress=True,
) -> tuple[EvalReport, list[CaseResult]]:
    from aegis.config import get_settings
    from aegis.graph.prompts import PROMPT_VERSIONS

    settings = get_settings()
    cases = load_golden(dataset_path or DEFAULT_DATASET)
    if limit:
        cases = cases[:limit]

    results = []
    start = time.monotonic()
    for index, case in enumerate(cases, start=1):
        results.append(evaluate_case(case, router, retriever))
        if progress and index % 10 == 0:
            elapsed = time.monotonic() - start
            print(f"  {index}/{len(cases)} cases ({elapsed:.0f}s)", flush=True)

    metrics = compute_metrics(cases, results)
    report = EvalReport(
        dataset=Path(str(dataset_path or "datasets/golden_v1.jsonl")).name,
        n_cases=len(cases),
        prompt_versions=dict(PROMPT_VERSIONS),
        models={
            "primary": settings.groq_model,
            "fallback": settings.google_model,
        },
        generated_at=datetime.now(UTC).isoformat(),
        metrics=metrics,
    )
    return report, results


def save_report(report: EvalReport, out_dir: Path = DEFAULT_REPORT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"report_{report.dataset.replace('.jsonl', '')}_{stamp}.json"
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return path
