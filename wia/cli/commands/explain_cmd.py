"""WIA CLI `explain` command for explaining files or code symbols."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header
from wia.llm.service import LLMService
from wia.storage.repository import IndexRepository


@click.command(name="explain", help="Explain structure and purpose of a file or code symbol.")
@click.argument("target")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def explain_cmd(target: str, workspace: str | None) -> None:
    """Explain code structure or symbol in workspace."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"WIA Code Explanation for '{target}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before running explanations."
            )
        )
        return

    service = LLMService()
    explanation = service.explain_target(target, index)

    click.echo(explanation)
