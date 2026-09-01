"""WIA CLI `summary` command for outputting RAG architecture context markdown."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_success
from wia.core.rag_context import RAGContextGenerator
from wia.storage.repository import IndexRepository


@click.command(name="summary", help="Generate Markdown architecture summary for LLM RAG context injection.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    help="Output Markdown file path (prints to stdout if omitted).",
)
def summary_cmd(workspace: str | None, output: str | None) -> None:
    """Generate Markdown workspace summary for LLM context."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before generating a summary."
            )
        )
        return

    summary_md = RAGContextGenerator.generate_rag_context(index)

    if output:
        out_p = Path(output)
        out_p.write_text(summary_md, encoding="utf-8")
        click.echo(format_success(f"Summary written to '{out_p}'"))
    else:
        click.echo(summary_md)
