"""WIA CLI `export` command for exporting knowledge packages or reports."""

import os
from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_success
from wia.storage.repository import IndexRepository


@click.command(name="export", help="Export architecture report or knowledge model.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json", "html"], case_sensitive=False),
    default="markdown",
    help="Output export format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False),
    default=None,
    help="Target output file path.",
)
def export_cmd(workspace: str | None, format: str, output: str | None) -> None:
    """Export workspace intelligence in the specified format."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"WIA Knowledge Export for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(format_error(f"No WIA index found at '{path}'. Run 'wia index' first."))
        return

    out_fmt = format.lower()
    if out_fmt == "markdown":
        from wia.core.rag_context import RAGContextGenerator
        content = RAGContextGenerator.generate_rag_context(index, max_files=50)
        out_path = Path(output) if output else (path / "wia-architecture-summary.md")
        out_path.write_text(content, encoding="utf-8")
        click.echo(format_success(f"Exported Markdown summary to {out_path}"))

    elif out_fmt == "json":
        from wia.utils.report_generator import ReportGenerator
        out_path = Path(output) if output else (path / ".wia" / "report_data.json")
        ReportGenerator.export_report_json(index, output_path=out_path)
        click.echo(format_success(f"Exported JSON intelligence data to {out_path}"))

    elif out_fmt == "html":
        from wia.utils.report_generator import ReportGenerator
        out_path = Path(output) if output else (path / "wia-report.html")
        ReportGenerator.generate_html_report(index, output_path=out_path)
        click.echo(format_success(f"Generated HTML report at {out_path}"))
