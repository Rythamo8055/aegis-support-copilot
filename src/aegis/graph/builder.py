from langgraph.graph import END, START, StateGraph

from aegis.graph.nodes import (
    make_escalation_node,
    make_resolution_node,
    make_review_gate_node,
    make_triage_node,
)
from aegis.graph.state import TicketState, route_after_triage


def route_after_escalation(state: TicketState, hitl: bool) -> str:
    if hitl and state.get("needs_escalation", False):
        return "review_gate"
    return "end"


def build_graph(router, retriever=None, checkpointer=None, hitl: bool = False):
    builder = StateGraph(TicketState)
    builder.add_node("triage", make_triage_node(router))
    builder.add_node("resolution", make_resolution_node(router, retriever=retriever))
    builder.add_node("escalation", make_escalation_node(router))

    builder.add_edge(START, "triage")
    builder.add_conditional_edges(
        "triage",
        route_after_triage,
        {"resolution": "resolution", "escalation": "escalation"},
    )
    builder.add_edge("resolution", "escalation")

    if hitl:
        builder.add_node("review_gate", make_review_gate_node())
        builder.add_conditional_edges(
            "escalation",
            lambda state: route_after_escalation(state, hitl=True),
            {"review_gate": "review_gate", "end": END},
        )
        builder.add_edge("review_gate", END)
    else:
        builder.add_conditional_edges(
            "escalation",
            lambda state: route_after_escalation(state, hitl=False),
            {"end": END},
        )

    return builder.compile(checkpointer=checkpointer)
