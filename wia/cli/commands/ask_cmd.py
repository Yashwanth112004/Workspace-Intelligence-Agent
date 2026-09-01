"""WIA CLI `ask` command for grounded AI reasoning queries."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header
from wia.llm.service import LLMService
from wia.storage.repository import IndexRepository


@click.command(name="ask", help="Ask AI reasoning agent a question grounded in workspace context.")
@click.argument("question")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def ask_cmd(question: str, workspace: str | None) -> None:
    """Query workspace reasoning agent with user prompt."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"WIA Workspace Reasoning for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before running reasoning queries."
            )
        )
        return

    service = LLMService()
    answer = service.ask_question(question, index)

    click.echo(f"\n{click.style('Question:', bold=True)} {question}\n")
    click.echo(answer)
