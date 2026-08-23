from aegis.graph.builder import build_graph
from aegis.graph.state import TicketState
from aegis.observability import get_callbacks


def run_ticket(
    ticket: dict,
    router,
    retriever=None,
    checkpointer=None,
    thread_id: str | None = None,
) -> TicketState:
    app = build_graph(router, retriever=retriever, checkpointer=checkpointer)
    config: dict = {"callbacks": get_callbacks()}
    if thread_id is not None:
        config["configurable"] = {"thread_id": thread_id}
    return app.invoke(ticket, config=config)
