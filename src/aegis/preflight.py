import sys

from langchain_core.messages import HumanMessage

from aegis.llm.router import build_providers

PROMPT = "Connectivity check. Reply with exactly: OK"


def main() -> int:
    providers = build_providers()
    failures = 0
    for name, model in providers.items():
        try:
            reply = model.invoke([HumanMessage(content=PROMPT)])
            print(f"{name}: OK ({type(model).__name__}) reply={reply.text!r:.80}")
        except Exception as exc:
            failures += 1
            print(f"{name}: FAIL ({type(exc).__name__}: {exc})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
