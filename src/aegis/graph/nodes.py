import logging

from langgraph.types import interrupt

from aegis.graph.prompts import (
    ESCALATION_PROMPT_V1,
    RESOLUTION_PROMPT_V1,
    TRIAGE_PROMPT_V1,
)
from aegis.graph.state import TicketState, extract_json

logger = logging.getLogger(__name__)

CATEGORIES = {"billing", "technical", "account", "other"}
PRIORITIES = {"low", "medium", "high", "critical"}


def make_triage_node(router):
    def triage_node(state: TicketState) -> dict:
        prompt = TRIAGE_PROMPT_V1.format(subject=state["subject"], body=state["body"])
        try:
            data = extract_json(router.invoke(prompt))
        except Exception as exc:
            logger.warning("triage fallback to defaults: %s", exc)
            data = {}
        category = data.get("category") if data.get("category") in CATEGORIES else "other"
        priority = data.get("priority") if data.get("priority") in PRIORITIES else "medium"
        needs_escalation = priority == "critical" or bool(data.get("needs_escalation"))
        return {
            "category": category,
            "priority": priority,
            "needs_escalation": needs_escalation,
            "triage_reason": str(data.get("reason", "")),
        }

    return triage_node


def make_resolution_node(router, retriever=None):
    def resolution_node(state: TicketState) -> dict:
        context = "(none indexed yet)"
        valid_ids: set[str] = set()
        if retriever is not None:
            query = f'{state.get("subject", "")} {state.get("body", "")}'.strip()
            chunks = retriever.retrieve(query, k=3)
            valid_ids = {chunk.id for chunk in chunks}
            context = "\n".join(f"[{c.id}] {c.text}" for c in chunks) or "(no matches)"

        prompt = RESOLUTION_PROMPT_V1.format(
            subject=state.get("subject", ""),
            body=state.get("body", ""),
            context=context,
        )
        try:
            data = extract_json(router.invoke(prompt))
        except Exception as exc:
            logger.warning("resolution fallback to stub: %s", exc)
            data = {}

        cited = [c for c in data.get("citations", []) if c in valid_ids]
        if not valid_ids:
            cited = list(data.get("citations", []))
        return {
            "draft_reply": str(data.get("draft_reply", "")),
            "citations": list(dict.fromkeys(cited)),
            "retrieved_ids": sorted(valid_ids),
        }

    return resolution_node


def make_escalation_node(router):
    def escalation_node(state: TicketState) -> dict:
        prompt = ESCALATION_PROMPT_V1.format(
            subject=state.get("subject", ""),
            category=state.get("category", ""),
            priority=state.get("priority", ""),
            draft_reply=state.get("draft_reply", ""),
            needs_escalation=state.get("needs_escalation", False),
        )
        try:
            data = extract_json(router.invoke(prompt))
        except Exception as exc:
            logger.warning("escalation fallback to defaults: %s", exc)
            data = {}
        escalated = state.get("needs_escalation", False) or state.get("priority") == "critical"
        return {
            "escalation_reason": str(data.get("escalation_reason", "")),
            "recommended_action": str(data.get("recommended_action", "")),
            "final_reply": state.get("draft_reply", ""),
            "needs_escalation": escalated,
        }

    return escalation_node


def make_review_gate_node():
    def review_gate_node(state: TicketState) -> dict:
        decision = interrupt(
            {
                "ticket_id": state.get("ticket_id", ""),
                "subject": state.get("subject", ""),
                "category": state.get("category", ""),
                "priority": state.get("priority", ""),
                "draft_reply": state.get("draft_reply", ""),
                "escalation_reason": state.get("escalation_reason", ""),
                "recommended_action": state.get("recommended_action", ""),
            }
        )
        action = decision.get("action")
        if action == "edit":
            return {
                "approval_status": "edited",
                "final_reply": str(decision.get("reply", "")).strip(),
            }
        if action == "reject":
            return {"approval_status": "rejected", "final_reply": ""}
        return {
            "approval_status": "approved",
            "final_reply": state.get("draft_reply", ""),
        }

    return review_gate_node
