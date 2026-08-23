import json


def judge_faithfulness(router, subject: str, body: str, reply: str, snippets: list[str]) -> dict:
    prompt = FAITHFULNESS_PROMPT_V1.format(
        subject=subject, body=body, reply=reply, snippets="\n".join(snippets) or "(none)"
    )
    raw = router.invoke(prompt)
    data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
    verdict = data.get("verdict", "")
    if verdict not in {"faithful", "unfaithful"}:
        raise ValueError(f"bad judge verdict: {verdict!r}")
    return {"verdict": verdict, "reason": str(data.get("reason", ""))}


def judge_needs_human(router, subject: str, body: str) -> bool:
    prompt = ESCALATION_JUDGE_PROMPT_V1.format(subject=subject, body=body)
    raw = router.invoke(prompt)
    data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
    return bool(data.get("needs_human", False))


FAITHFULNESS_PROMPT_V1 = """You are a strict evaluation judge.
Decide whether the support reply below is grounded ONLY in the provided knowledge
snippets and actually addresses the ticket. Reply "unfaithful" if the reply asserts
facts not present in the snippets or ignores them.
Return STRICT JSON only: {{"verdict": "faithful"|"unfaithful", "reason": "<one sentence>"}}

Ticket subject: {subject}
Ticket body: {body}

Knowledge snippets:
{snippets}

Reply under test:
{reply}"""

ESCALATION_JUDGE_PROMPT_V1 = """You are simulating a support team lead.
Given the ticket, decide whether a HUMAN team member must handle it personally:
policy disputes, legal or security issues, angry customers, large refunds,
sensitive situations. Routine questions answerable from documentation are NOT escalations.
Return STRICT JSON only: {{"needs_human": true|false}}

Subject: {subject}
Body: {body}"""

JUDGE_VERSIONS = {
    "faithfulness": "v1",
    "escalation": "v1",
}
