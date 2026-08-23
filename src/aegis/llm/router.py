from langchain_core.language_models.chat_models import BaseChatModel

from aegis.config import Settings, get_settings


def build_providers(settings: Settings | None = None) -> dict[str, BaseChatModel]:
    settings = settings or get_settings()
    return {
        "groq": _build_groq(settings),
        "gemma": _build_gemma(settings),
    }


def _build_groq(settings: Settings) -> BaseChatModel:
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_tokens=2048,
        reasoning_effort="low",
    )


def _build_gemma(settings: Settings) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
        max_output_tokens=2048,
        request_options={"timeout": 45},
    )


class RouterError(RuntimeError):
    pass


class LLMRouter:
    def __init__(
        self,
        primary: BaseChatModel | None = None,
        fallback: BaseChatModel | None = None,
    ) -> None:
        if primary is None or fallback is None:
            providers = build_providers()
            primary = primary or providers["groq"]
            fallback = fallback or providers["gemma"]
        self._primary = primary
        self._fallback = fallback

    def invoke(self, prompt: str) -> str:
        errors: list[str] = []
        for name, model in (("groq", self._primary), ("gemma", self._fallback)):
            try:
                result = model.invoke(prompt)
                return result.text
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        raise RouterError("all providers failed -> " + " | ".join(errors))
