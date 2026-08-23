import logging

from aegis.graph.state import TicketState, extract_json

logger = logging.getLogger(__name__)

TRIAGE_PROMPT = """You are the triage agent for a production support team.
Classify the ticket and return STRICT JSON only, no prose.
Schema: {{"category": "billing"|"technical"|"account"|"other",
"priority": "low"|"medium"|"high"|"critical",
"needs_escalation": true|false, "reason": "<one sentence>"}}

Subject: {subject}
Body: {body}"""

RESOLUTION_PROMPT = """You are the resolution agent. Draft a concise support reply (max 150 words)
grounded ONLY on the knowledge snippets below. If snippets are insufficient, say what is missing.
Return STRICT JSON only: {{"draft_reply": "<text>", "citations": ["<snippet id>", ...]}}

Ticket subject: {subject}
Ticket body: {body}
Knowledge snippets: {context}"""

ESCALATION_PROMPT = """You are the escalation agent. Assess whether this ticket needs human
review and what the human should do first.
Return STRICT JSON only: {{"escalation_reason": "<one sentence>",
"recommended_action": "<first action for the human>"}}

Subject: {subject}
Category: {category}
Priority: {priority}
Draft reply so far: {draft_reply}
Triage escalation flag: {needs_escalation}"""

CATEGORIES = {"billing", "technical", "account", "other"}
PRIORITIES = {"low", "medium", "high", "critical"}


def make_triage_node(router):
    def triage_node(state: TicketState) -> dict:
        prompt = TRIAGE_PROMPT.format(subject=state["subject"], body=state["body"])
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


def make_resolution_node(router):
    def resolution_node(state: TicketState) -> dict:
        prompt = RESOLUTION_PROMPT.format(
            subject=state["subject"],
            body=state["body"],
            context=state.get("citations_context", "(none indexed yet)"),
        )
        try:
            data = extract_json(router.invoke(prompt))
        except Exception as exc:
            logger.warning("resolution fallback to stub: %s", exc)
            data = {"draft_reply": "We are looking into your issue.", "citations": []}
        return {
            "draft_reply": str(data.get("draft_reply", "")),
            "citations": list(data.get("citations", [])),
        }

    return resolution_node


def make_escalation_node(router):
    def escalation_node(state: TicketState) -> dict:
        prompt = ESCALATION_PROMPT.format(
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
