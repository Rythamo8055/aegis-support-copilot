import json
import re
from typing import Literal, TypedDict


class TicketState(TypedDict, total=False):
    ticket_id: str
    subject: str
    body: str
    category: str
    priority: str
    triage_reason: str
    citations_context: str
    draft_reply: str
    citations: list[str]
    retrieved_ids: list[str]
    needs_escalation: bool
    escalation_reason: str
    recommended_action: str
    approval_status: str
    final_reply: str


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match is None:
        raise ValueError("no JSON object found in model output")
    return json.loads(match.group(0))


Route = Literal["resolution", "escalation"]


def route_after_triage(state: TicketState) -> Route:
    if state.get("priority", "") == "critical":
        return "escalation"
    return "resolution"
