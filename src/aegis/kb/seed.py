import sys

from aegis.kb.documents import KB_DOCS
from aegis.kb.retriever import KBRetriever


def main() -> int:
    retriever = KBRetriever()
    retriever._collection.upsert(
        ids=[doc["id"] for doc in KB_DOCS],
        documents=[f'{doc["title"]}. {doc["text"]}' for doc in KB_DOCS],
    )
    print(f"seeded {retriever.count} docs into chroma")
    return 0


if __name__ == "__main__":
    sys.exit(main())
