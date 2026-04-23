from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "src/rag_support/ingest.py",
    "src/rag_support/retrieval.py",
    "src/rag_support/routing.py",
    "src/rag_support/workflow.py",
    "src/rag_support/hitl.py",
    "src/rag_support/cli.py",
    "docs/HLD.md",
    "docs/LLD.md",
    "docs/TECHNICAL_DOCUMENTATION.md",
]


def check_required_files() -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_FILES:
        if not (ROOT / rel_path).exists():
            failures.append(f"Missing file: {rel_path}")
    return failures


def check_workflow_runtime() -> list[str]:
    failures: list[str] = []

    try:
        from rag_support.config import Settings
        from rag_support.retrieval import RetrievalResult
        from rag_support.workflow import SupportAssistant
    except Exception as exc:
        return [f"Import failure: {exc}"]

    class DummyRetriever:
        def retrieve(self, query: str) -> RetrievalResult:
            return RetrievalResult(chunks=[], context="", top_score=0.0)

    try:
        settings = Settings.from_env(ROOT)
        assistant = SupportAssistant(
            settings=settings,
            retriever=DummyRetriever(),
            human_responder=lambda _q, _r: "Handled by human agent",
        )
        state = assistant.run("I need legal support now")
        if state.get("route") != "escalate":
            failures.append("Expected escalate route in runtime smoke check")
        if "answer" not in state:
            failures.append("Workflow did not produce answer field")
    except Exception as exc:
        failures.append(f"Workflow runtime failure: {exc}")

    return failures


def main() -> None:
    checks = {
        "files": check_required_files(),
        "runtime": check_workflow_runtime(),
    }

    error_count = 0
    for name, failures in checks.items():
        if failures:
            error_count += len(failures)
            print(f"[FAIL] {name}")
            for issue in failures:
                print(f"  - {issue}")
        else:
            print(f"[PASS] {name}")

    if error_count:
        raise SystemExit(f"Crosscheck failed with {error_count} issue(s)")

    print("All crosschecks passed.")


if __name__ == "__main__":
    main()
