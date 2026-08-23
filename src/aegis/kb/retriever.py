from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    text: str
    score: float = 0.0


class KBRetriever:
    def __init__(self, persist_dir: str = "./chroma", collection: str = "support_kb") -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(collection)

    @property
    def count(self) -> int:
        return self._collection.count()

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        result = self._collection.query(query_texts=[query], n_results=k)
        docs = result.get("documents", [[]])[0]
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[0.0] * len(docs)])[0]
        return [
            Chunk(id=doc_id, text=doc, score=1.0 - dist)
            for doc_id, doc, dist in zip(ids, docs, distances, strict=True)
        ]
