from aegis.graph.builder import build_graph
from aegis.kb.documents import KB_DOCS
from aegis.kb.retriever import Chunk


class FakeRetriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self.queries: list[str] = []

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        self.queries.append(query)
        return self._chunks[:k]


TRIAGE_OK = (
    '{"category": "billing", "priority": "high", '
    '"needs_escalation": false, "reason": "refund request"}'
)
ESCALATION_OK = '{"escalation_reason": "r", "recommended_action": "a"}'


def resolution_reply(citations: list[str]) -> str:
    import json

    return json.dumps({"draft_reply": "Refund initiated per policy.", "citations": citations})


def test_resolution_filters_hallucinated_citations() -> None:
    retriever = FakeRetriever([Chunk(id="KB-001", text="dup charge policy")])
    router = ScriptedRouter([TRIAGE_OK, resolution_reply(["KB-001", "KB-999"]), ESCALATION_OK])
    app = build_graph(router, retriever=retriever)
    result = app.invoke({"ticket_id": "t-1", "subject": "double charged", "body": "refund me"})

    assert result["citations"] == ["KB-001"]
    assert result["retrieved_ids"] == ["KB-001"]


def test_resolution_receives_formatted_context() -> None:
    retriever = FakeRetriever(
        [Chunk(id="KB-002", text="timelines"), Chunk(id="KB-003", text="disputes")]
    )
    router = ScriptedRouter([TRIAGE_OK, resolution_reply(["KB-002"]), ESCALATION_OK])
    app = build_graph(router, retriever=retriever)
    result = app.invoke({"ticket_id": "t-2", "subject": "where is refund", "body": "10 days"})

    resolution_prompt = router.calls[1]
    assert "[KB-002] timelines" in resolution_prompt
    assert "[KB-003] disputes" in resolution_prompt
    assert "where is refund" in retriever.queries[0]
    assert result["citations"] == ["KB-002"]


def test_kb_documents_have_unique_ids() -> None:
    ids = [doc["id"] for doc in KB_DOCS]
    assert len(ids) == len(set(ids))
    assert all(doc["text"].strip() for doc in KB_DOCS)


class ScriptedRouter:
    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._replies.pop(0)


def test_no_retriever_keeps_llm_citations() -> None:
    router = ScriptedRouter([TRIAGE_OK, resolution_reply(["ANY-ID"]), ESCALATION_OK])
    app = build_graph(router)
    result = app.invoke({"ticket_id": "t-3", "subject": "s", "body": "b"})

    assert result["citations"] == ["ANY-ID"]
    assert result["retrieved_ids"] == []
