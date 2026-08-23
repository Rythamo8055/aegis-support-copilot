from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from aegis.graph.builder import build_graph
from helpers import (
    ESCALATION_OK,
    RESOLUTION_OK,
    TRIAGE_ESCALATE,
    TRIAGE_NORMAL,
    ScriptedRouter,
)


def escalated_ticket(tid: str) -> dict:
    return {"ticket_id": tid, "subject": "sue you", "body": "lawyer incoming"}


def test_hitl_pauses_before_review_gate() -> None:
    router = ScriptedRouter([TRIAGE_ESCALATE, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router, checkpointer=MemorySaver(), hitl=True)
    config = {"configurable": {"thread_id": "h1"}}

    result = app.invoke(escalated_ticket("h1"), config=config)

    assert "__interrupt__" in result
    state = app.get_state(config)
    assert state.next == ("review_gate",)
    payload = state.tasks[0].interrupts[0].value
    assert payload["ticket_id"] == "h1"
    assert payload["draft_reply"] == "Auto draft."


def test_resume_approve_keeps_draft() -> None:
    router = ScriptedRouter([TRIAGE_ESCALATE, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router, checkpointer=MemorySaver(), hitl=True)
    config = {"configurable": {"thread_id": "h2"}}
    app.invoke(escalated_ticket("h2"), config=config)

    final = app.invoke(Command(resume={"action": "approve"}), config=config)

    assert final["approval_status"] == "approved"
    assert final["final_reply"] == "Auto draft."


def test_resume_reject_clears_reply() -> None:
    router = ScriptedRouter([TRIAGE_ESCALATE, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router, checkpointer=MemorySaver(), hitl=True)
    config = {"configurable": {"thread_id": "h3"}}
    app.invoke(escalated_ticket("h3"), config=config)

    final = app.invoke(Command(resume={"action": "reject"}), config=config)

    assert final["approval_status"] == "rejected"
    assert final["final_reply"] == ""


def test_resume_edit_overrides_reply() -> None:
    router = ScriptedRouter([TRIAGE_ESCALATE, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router, checkpointer=MemorySaver(), hitl=True)
    config = {"configurable": {"thread_id": "h4"}}
    app.invoke({"ticket_id": "h4", "subject": "help", "body": "stuck"}, config=config)

    final = app.invoke(
        Command(resume={"action": "edit", "reply": "Human wrote this."}), config=config
    )

    assert final["approval_status"] == "edited"
    assert final["final_reply"] == "Human wrote this."


def test_non_escalated_tickets_skip_gate() -> None:
    router = ScriptedRouter([TRIAGE_NORMAL, RESOLUTION_OK, ESCALATION_OK])
    app = build_graph(router, checkpointer=MemorySaver(), hitl=True)
    config = {"configurable": {"thread_id": "h6"}}

    result = app.invoke({"ticket_id": "h6", "subject": "?", "body": "?"}, config=config)

    assert "__interrupt__" not in result
    assert result.get("approval_status", "") == ""
