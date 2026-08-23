import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult

from aegis.llm.router import LLMRouter, RouterError


class ExplodingModel(BaseChatModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        raise RuntimeError("boom")

    @property
    def _llm_type(self) -> str:
        return "exploding"


def fake_model(*replies: str) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter(AIMessage(content=r) for r in replies))


def test_primary_answer_used() -> None:
    router = LLMRouter(primary=fake_model("primary says hi"), fallback=fake_model("nope"))
    assert router.invoke("q") == "primary says hi"


def test_fallback_engages_on_primary_failure() -> None:
    router = LLMRouter(primary=ExplodingModel(), fallback=fake_model("gemma saved us"))
    assert router.invoke("q") == "gemma saved us"


def test_router_error_when_all_fail() -> None:
    router = LLMRouter(primary=ExplodingModel(), fallback=ExplodingModel())
    with pytest.raises(RouterError):
        router.invoke("q")
