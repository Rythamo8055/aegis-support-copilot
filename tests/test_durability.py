from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from aegis.graph.builder import build_graph
from helpers import (
    ESCALATION_OK,
    RESOLUTION_OK,
    TRIAGE_ESCALATE,
    ScriptedRouter,
)


def test_state_survives_process_restart(tmp_path) -> None:
    db_path = str(tmp_path / "checkpoints.db")

    router_a = ScriptedRouter([TRIAGE_ESCALATE, RESOLUTION_OK, ESCALATION_OK])
    with SqliteSaver.from_conn_string(db_path) as saver_a:
        app_a = build_graph(router_a, checkpointer=saver_a, hitl=True)
        config = {"configurable": {"thread_id": "restart-1"}}
        paused = app_a.invoke(
            {"ticket_id": "restart-1", "subject": "s", "body": "b"}, config=config
        )
        assert "__interrupt__" in paused

    router_b = ScriptedRouter([])
    with SqliteSaver.from_conn_string(db_path) as saver_b:
        app_b = build_graph(router_b, checkpointer=saver_b, hitl=True)
        config = {"configurable": {"thread_id": "restart-1"}}
        state = app_b.get_state(config)
        assert state.next == ("review_gate",)

        final = app_b.invoke(Command(resume={"action": "approve"}), config=config)
        assert final["approval_status"] == "approved"
        assert final["final_reply"] == "Auto draft."
