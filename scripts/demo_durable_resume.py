import logging
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from aegis.graph.builder import build_graph
from aegis.kb.retriever import KBRetriever
from aegis.llm.router import LLMRouter

DB = "checkpoints.db"
TICKET = {
    "ticket_id": "demo-durable-1",
    "subject": "Refund of Rs 8000 not received",
    "body": (
        "Promised refund 12 days ago, nothing in my account. "
        "Very frustrated, this keeps getting delayed."
    ),
}


def build(router):
    saver = SqliteSaver(sqlite3.connect(DB, check_same_thread=False))
    return build_graph(router, retriever=KBRetriever(), checkpointer=saver, hitl=True)


def main() -> None:
    logging.disable(logging.WARNING)
    config = {"configurable": {"thread_id": TICKET["ticket_id"]}}

    print("== phase 1: run until human review gate ==")
    router1 = LLMRouter()
    app1 = build(router1)
    paused = app1.invoke(TICKET, config=config)
    assert "__interrupt__" in paused, "expected pause at review gate"
    state = app1.get_state(config)
    payload = state.tasks[0].interrupts[0].value
    print(f"paused at: {state.next}")
    print(f"draft: {payload['draft_reply'][:120]}...")
    print(f"reason: {payload['escalation_reason']}")

    del app1, router1
    print("\n== process 'crashed'. restarting fresh from sqlite checkpoint ==")

    router2 = LLMRouter()
    app2 = build(router2)
    resumed_state = app2.get_state(config)
    print(f"recovered pending node from disk: {resumed_state.next}")

    final = app2.invoke(Command(resume={"action": "approve"}), config=config)
    print("\n== phase 2: human approved ==")
    print(f"status: {final['approval_status']}")
    print(f"final reply sent to customer:\n{final['final_reply'][:400]}")


if __name__ == "__main__":
    main()
