from __future__ import annotations

from typing import Callable

from rich.console import Console
from rich.prompt import Prompt


HumanResponder = Callable[[str, str], str]


def default_human_responder(query: str, reason: str) -> str:
    console = Console()
    console.print("\n[bold yellow]HITL escalation triggered[/bold yellow]")
    console.print(f"Reason: {reason}")
    console.print(f"User question: {query}")
    return Prompt.ask("Type the human agent response")
