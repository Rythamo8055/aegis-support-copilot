from aegis.graph.builder import build_graph
from aegis.graph.state import extract_json, route_after_triage

TRIAGE_OK = (
    '{"category": "billing", "priority": "high", '
    '"needs_escalation": false, "reason": "refund request"}'
)
RESOLUTION_OK = '{"draft_reply": "Refund initiated.", "citations": ["KB-101"]}'
ESCALATION_OK = (
    '{"escalation_reason": "high value refund", '
    '"recommended_action": "confirm amount"}'
)


class ScriptedRouter:
    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._replies.pop(0)


def test_extract_json_tolerates_prose() -> None:
    text = 'Sure! Here you go:\n{"a": 1}\nThanks'
    assert extract_json(text) == {"a": 1}


def test_route_after_triage_branches() -> None:
    assert route_after_triage({"priority": "critical"}) == "escalation"
    assert route_after_triage({"needs_escalation": True, "priority": "high"}) == "resolution"
    assert route_after_triage({"needs_escalation": False, "priority": "low"}) == "resolution"
    assert route_after_triage({}) == "resolution"


def test_happy_path_runs_all_three_nodes() -> None:
    router = ScriptedRouter([TRIAGE_OK, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router)
    result = app.invoke(
        {"ticket_id": "t-1", "subject": "refund please", "body": "I want my money back"}
    )

    assert len(router.calls) == 3
    assert result["category"] == "billing"
    assert result["priority"] == "high"
    assert result["draft_reply"] == "Refund initiated."
    assert result["citations"] == ["KB-101"]
    assert result["final_reply"] == "Refund initiated."
    assert result["needs_escalation"] is False


def test_critical_triage_skips_resolution() -> None:
    triage_critical = (
        '{"category": "technical", "priority": "critical", '
        '"needs_escalation": true, "reason": "outage"}'
    )
    router = ScriptedRouter([triage_critical, ESCALATION_OK])
    app = build_graph(router)
    result = app.invoke({"ticket_id": "t-2", "subject": "down", "body": "all down"})

    assert len(router.calls) == 2
    assert result["needs_escalation"] is True
    assert result["recommended_action"] == "confirm amount"
    assert "draft_reply" not in result


def test_triage_survives_garbage_output() -> None:
    router = ScriptedRouter(["total nonsense", RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router)
    result = app.invoke({"ticket_id": "t-3", "subject": "?", "body": "?"})

    assert result["category"] == "other"
    assert result["priority"] == "medium"
