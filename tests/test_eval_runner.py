import pytest

from aegis.evals.dataset import GoldenCase
from aegis.evals.runner import CaseResult, compute_metrics, evaluate_case
from aegis.graph.builder import build_graph


def make_case(cid="c1", **kw):
    base = dict(
        id=cid,
        subject="s",
        body="b",
        category="billing",
        priority="medium",
        needs_escalation=False,
        expected_kb_ids=[],
    )
    base.update(kw)
    return GoldenCase(**base)


class PerfectRouter:
    def __init__(self, escalate=False):
        self.escalate = escalate

    def invoke(self, prompt: str) -> str:
        if "triage agent" in prompt:
            esc = self.escalate
            prio = "high" if esc else "medium"
            return (
                '{"category": "billing", "priority": "'
                + prio
                + '", "needs_escalation": '
                + str(esc).lower()
                + ', "reason": "x"}'
            )
        if "resolution agent" in prompt:
            return '{"draft_reply": "d", "citations": ["KB-001"]}'
        if "escalation agent" in prompt:
            return '{"escalation_reason": "r", "recommended_action": "a"}'
        raise AssertionError("unexpected prompt")


def test_evaluate_case_extracts_predictions() -> None:
    case = make_case()
    result = evaluate_case(case, PerfectRouter())
    assert result.predicted_category == "billing"
    assert result.predicted_priority == "medium"
    assert result.predicted_escalation is False
    assert result.error == ""


def test_evaluate_case_fails_open_on_router_boom() -> None:
    class Boom:
        def invoke(self, prompt):
            raise RuntimeError("nope")

    result = evaluate_case(make_case(), Boom())
    assert result.error == ""
    assert result.predicted_category == "other"
    assert result.predicted_priority == "medium"
    assert result.predicted_escalation is False


def test_compute_metrics_perfect_run() -> None:
    cases = [
        make_case("a", expected_kb_ids=["KB-001"]),
        make_case("b", needs_escalation=True, priority="critical", expected_kb_ids=["KB-002"]),
    ]
    results = [
        CaseResult(
            case_id="a",
            predicted_category="billing",
            predicted_priority="medium",
            predicted_escalation=False,
            citations=["KB-001"],
            retrieved_ids=["KB-001"],
            draft_reply="d",
        ),
        CaseResult(
            case_id="b",
            predicted_category="billing",
            predicted_priority="critical",
            predicted_escalation=True,
            citations=["KB-002", "KB-003"],
            retrieved_ids=["KB-002", "KB-003"],
            draft_reply="",
        ),
    ]
    metrics = compute_metrics(cases, results)
    assert metrics["triage_category_accuracy"] == 1.0
    assert metrics["priority_accuracy"] == 1.0
    assert metrics["escalation_agreement_accuracy"] == 1.0
    assert metrics["citation_recall"] == 1.0
    assert metrics["grounding_violation_rate"] == 0.0


def test_compute_metrics_counts_violations_and_misses() -> None:
    cases = [
        make_case("a", expected_kb_ids=["KB-001", "KB-002"]),
    ]
    results = [
        CaseResult(
            case_id="a",
            predicted_category="other",
            predicted_priority="low",
            predicted_escalation=True,
            citations=["KB-999"],
            retrieved_ids=["KB-003"],
            draft_reply="d",
        ),
    ]
    metrics = compute_metrics(cases, results)
    assert metrics["triage_category_accuracy"] == 0.0
    assert metrics["citation_recall"] == 0.0
    assert metrics["grounding_violation_rate"] == 1.0


def test_graph_wiring_matches_router_contract() -> None:
    app = build_graph(PerfectRouter(), hitl=False)
    state = app.invoke({"ticket_id": "z", "subject": "s", "body": "b"})
    assert state["category"] == "billing"


@pytest.mark.parametrize(
    ("current_val", "expected_fail"),
    [(0.90, True), (0.93, False), (0.99, False)],
)
def test_gate_threshold_math(current_val, expected_fail, tmp_path):
    from aegis.evals.gate import compare

    baseline = {"metrics": {"citation_recall": 0.95}}
    current = {"metrics": {"citation_recall": current_val}}
    failures = compare(current, baseline, threshold=0.02)
    assert bool(failures) is expected_fail


def test_gate_blocks_rising_violations() -> None:
    from aegis.evals.gate import compare

    baseline = {"metrics": {"grounding_violation_rate": 0.01}}
    current = {"metrics": {"grounding_violation_rate": 0.05}}
    assert compare(current, baseline) != []
