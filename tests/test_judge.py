import json

from aegis.evals.judge import judge_faithfulness, judge_needs_human
from helpers import ScriptedRouter


def test_judge_faithfulness_parses_verdict() -> None:
    router = ScriptedRouter(['{"verdict": "faithful", "reason": "matches KB"}'])
    out = judge_faithfulness(router, "s", "b", "reply text", ["[KB-001] policy"])
    assert out["verdict"] == "faithful"
    assert router.calls and "[KB-001]" in router.calls[0]


def test_judge_faithfulness_rejects_bad_verdict() -> None:
    import pytest

    router = ScriptedRouter(['{"verdict": "kinda-fine", "reason": "meh"}'])
    with pytest.raises(ValueError):
        judge_faithfulness(router, "s", "b", "r", [])


def test_judge_needs_human_bool() -> None:
    router = ScriptedRouter([json.dumps({"needs_human": True})])
    assert judge_needs_human(router, "legal threat", "lawyer") is True
