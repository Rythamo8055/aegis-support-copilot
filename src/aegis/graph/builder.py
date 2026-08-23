from langgraph.graph import END, START, StateGraph

from aegis.graph.nodes import make_escalation_node, make_resolution_node, make_triage_node
from aegis.graph.state import TicketState, route_after_triage


def build_graph(router, checkpointer=None):
    builder = StateGraph(TicketState)
    builder.add_node("triage", make_triage_node(router))
    builder.add_node("resolution", make_resolution_node(router))
    builder.add_node("escalation", make_escalation_node(router))

    builder.add_edge(START, "triage")
    builder.add_conditional_edges(
        "triage",
        route_after_triage,
        {"resolution": "resolution", "escalation": "escalation"},
    )
    builder.add_edge("resolution", "escalation")
    builder.add_edge("escalation", END)

    return builder.compile(checkpointer=checkpointer)
