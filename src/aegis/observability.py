import logging
import os

logger = logging.getLogger(__name__)


def get_callbacks() -> list:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    if not (public_key and secret_key):
        return []
    try:
        from langfuse.langchain import CallbackHandler

        return [CallbackHandler()]
    except Exception as exc:
        logger.warning("langfuse unavailable, tracing disabled: %s", exc)
        return []
