import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DATASET = Path("datasets/golden_v1.jsonl")

VALID_CATEGORIES = {"billing", "technical", "account", "other"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
REQUIRED_FIELDS = {
    "id",
    "subject",
    "body",
    "category",
    "priority",
    "needs_escalation",
    "expected_kb_ids",
    "tags",
}


@dataclass
class GoldenCase:
    id: str
    subject: str
    body: str
    category: str
    priority: str
    needs_escalation: bool
    expected_kb_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def query(self) -> str:
        return f"{self.subject} {self.body}".strip()


def load_golden(path: Path | str = DEFAULT_DATASET) -> list[GoldenCase]:
    path = Path(path)
    cases: list[GoldenCase] = []
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            absent = REQUIRED_FIELDS - record.keys()
            if absent:
                raise ValueError(f"record missing fields {sorted(absent)}: {line[:80]}")
            cases.append(
                GoldenCase(
                    id=record["id"],
                    subject=record["subject"],
                    body=record["body"],
                    category=record["category"],
                    priority=record["priority"],
                    needs_escalation=bool(record["needs_escalation"]),
                    expected_kb_ids=list(record.get("expected_kb_ids", [])),
                    tags=list(record.get("tags", [])),
                    notes=str(record.get("notes", "")),
                )
            )
    return cases


def validate_cases(cases: list[GoldenCase], valid_kb_ids: set[str]) -> None:
    seen: set[str] = set()
    for case in cases:
        if case.id in seen:
            raise ValueError(f"duplicate id: {case.id}")
        seen.add(case.id)
        if not case.body and not case.subject:
            raise ValueError(f"{case.id}: subject and body are both empty")
        if case.category not in VALID_CATEGORIES:
            raise ValueError(f"{case.id}: bad category {case.category!r}")
        if case.priority not in VALID_PRIORITIES:
            raise ValueError(f"{case.id}: bad priority {case.priority!r}")
        unknown_kb = set(case.expected_kb_ids) - valid_kb_ids
        if unknown_kb:
            raise ValueError(f"{case.id}: unknown KB ids {sorted(unknown_kb)}")
