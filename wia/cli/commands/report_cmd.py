"""WIA CLI `report` command for generating HTML workspace reports."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv, format_success
from wia.storage.repository import IndexRepository
from wia.utils.report_generator import ReportGenerator


@click.command(name="report", help="Generate a standalone HTML intelligence report for the workspace.")
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
    help="Output HTML filepath (default: wia-report.html in workspace root).",
)
def report_cmd(workspace: str | None, output: str | None) -> None:
    """Generate HTML workspace intelligence report."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Generating Workspace Report for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before generating a report."
            )
        )
        return

    out_file = ReportGenerator.generate_html_report(index, output_path=output)
    completed_b = len([b for b in index.batches if b.status == "COMPLETED"])
    click.echo(format_kv("Accumulated Batches", f"{completed_b} / {len(index.batches)} completed"))
    click.echo(format_success(f"Report generated successfully!"))
    click.echo(format_kv("Report File", str(out_file)))
