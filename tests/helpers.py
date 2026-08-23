TRIAGE_ESCALATE = (
    '{"category": "billing", "priority": "high", '
    '"needs_escalation": true, "reason": "refund above limit"}'
)
TRIAGE_NORMAL = (
    '{"category": "technical", "priority": "low", '
    '"needs_escalation": false, "reason": "how to question"}'
)
RESOLUTION_OK = '{"draft_reply": "Auto draft.", "citations": []}'
ESCALATION_OK = '{"escalation_reason": "policy", "recommended_action": "verify identity"}'


class ScriptedRouter:
    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._replies.pop(0)
