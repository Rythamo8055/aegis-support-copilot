from pathlib import Path

from aegis.evals.dataset import load_golden, validate_cases
from aegis.kb.documents import KB_DOCS

DATASET = Path("datasets/golden_v1.jsonl")


def test_dataset_loads_and_is_valid() -> None:
    cases = load_golden(DATASET)
    assert 60 <= len(cases) <= 100
    valid_kb_ids = {doc["id"] for doc in KB_DOCS}
    validate_cases(cases, valid_kb_ids)


def test_distribution_covers_all_categories_and_priorities() -> None:
    cases = load_golden(DATASET)
    categories = {c.category for c in cases}
    priorities = {c.priority for c in cases}
    assert {"billing", "technical", "account", "other"} <= categories
    assert {"low", "medium", "high", "critical"} <= priorities


def test_edge_cases_present() -> None:
    cases = load_golden(DATASET)
    tags = {tag for case in cases for tag in case.tags}
    expected_edge_tags = {
        "edge-vague",
        "edge-angry",
        "edge-multi-issue",
        "edge-non-english",
        "edge-breach",
        "edge-legal",
        "edge-bereavement",
    }
    assert expected_edge_tags <= tags
    escalations = [c for c in cases if c.needs_escalation]
    assert len(escalations) >= 10


def test_expected_kb_references_exist_in_kb() -> None:
    from aegis.kb.documents import KB_DOCS as DOCS

    kb_ids = {doc["id"] for doc in DOCS}
    for case in load_golden(DATASET):
        assert set(case.expected_kb_ids) <= kb_ids, case.id
