from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from .config import Settings
from .hitl import HumanResponder
from .ingest import ingest_pdf
from .retrieval import KnowledgeRetriever
from .workflow import SupportAssistant


app = typer.Typer(help="RAG customer support assistant")
console = Console()


def cli_human_responder(query: str, reason: str) -> str:
    console.print("\n[bold yellow]Escalation required[/bold yellow]")
    console.print(f"Reason: {reason}")
    console.print(f"Original query: {query}")
    return Prompt.ask("Enter human agent reply")


@app.command()
def ingest(
    pdf: Path = typer.Option(Path("data/customer_support_kb.pdf"), help="Path to PDF knowledge base"),
    reset: bool = typer.Option(True, help="Reset existing Chroma collection before ingest"),
) -> None:
    settings = Settings.from_env()
    pages, chunks = ingest_pdf(pdf, settings, reset_collection=reset)
    console.print(f"Ingested {pages} pages and stored {chunks} chunks in ChromaDB.")


@app.command()
def ask(
    query: str = typer.Argument(..., help="Customer question"),
    human_reply: str = typer.Option("", help="Optional non-interactive human reply for escalation"),
) -> None:
    settings = Settings.from_env()

    if not settings.groq_api_key:
        raise typer.BadParameter("GROQ_API_KEY is missing. Add it to .env first.")

    responder: HumanResponder
    if human_reply:
        responder = lambda _query, _reason: human_reply
    else:
        responder = cli_human_responder

    assistant = SupportAssistant(
        settings=settings,
        retriever=KnowledgeRetriever(settings),
        human_responder=responder,
    )

    result = assistant.run(query)

    console.print("\n[bold]Answer[/bold]")
    console.print(result.get("answer", "No answer generated."))

    console.print("\n[bold]Debug details[/bold]")
    console.print(f"intent={result.get('intent', 'unknown')}")
    console.print(f"route={result.get('route', 'unknown')}")
    console.print(f"confidence={result.get('confidence', 0.0):.2f}")
    console.print(f"reason={result.get('escalation_reason', 'n/a')}")


@app.command()
def chat() -> None:
    settings = Settings.from_env()

    if not settings.groq_api_key:
        raise typer.BadParameter("GROQ_API_KEY is missing. Add it to .env first.")

    assistant = SupportAssistant(
        settings=settings,
        retriever=KnowledgeRetriever(settings),
        human_responder=cli_human_responder,
    )

    console.print("Type your customer support question. Type 'exit' to stop.")

    while True:
        query = Prompt.ask("\nYou")
        if query.strip().lower() in {"exit", "quit"}:
            console.print("Session ended.")
            break

        result = assistant.run(query)
        console.print("\n[bold cyan]Assistant[/bold cyan]")
        console.print(result.get("answer", "No answer generated."))
        console.print(
            f"[dim]intent={result.get('intent')} route={result.get('route')} confidence={result.get('confidence', 0.0):.2f}[/dim]"
        )


if __name__ == "__main__":
    app()
