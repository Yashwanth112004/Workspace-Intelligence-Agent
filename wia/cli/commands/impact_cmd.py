"""WIA CLI `impact` command for evaluating symbol refactoring impact."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv, format_warning
from wia.core.impact import ImpactAnalyzer
from wia.storage.repository import IndexRepository


@click.command(name="impact", help="Evaluate downstream impact and risk of modifying a symbol.")
@click.argument("symbol")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def impact_cmd(symbol: str, workspace: str | None) -> None:
    """Analyze downstream dependency impact of modifying target symbol."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Impact Analysis for '{symbol}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before running impact analysis."
            )
        )
        return

    report = ImpactAnalyzer.analyze_symbol_impact(symbol, index)

    if not report.found:
        click.echo(format_error(f"Symbol '{symbol}' was not found in the indexed workspace."))
        click.echo(f"Run `wia search {symbol}` to find matching symbols.")
        return

    risk_style = (
        "red" if report.risk_level == "HIGH" else "yellow" if report.risk_level == "MEDIUM" else "green"
    )
    click.echo(format_kv("Target Entity", report.target_symbol))
    if report.defining_file:
        click.echo(format_kv("Defined In", report.defining_file))
    click.echo(format_kv("Target Type", report.target_type))
    click.echo(format_kv("Risk Classification", click.style(report.risk_level, fg=risk_style, bold=True)))
    click.echo(format_kv("Explanation", report.explanation))

    if report.candidates:
        click.echo("\n" + format_header("Matching Candidate Symbols"))
        for cand in report.candidates:
            click.echo(f"  * {cand}")

    if report.direct_dependents:
        click.echo("\n" + format_header("Direct Symbol Callers"))
        for dep in report.direct_dependents:
            click.echo(f"  * {dep}")

    if report.file_dependents:
        click.echo("\n" + format_header(f"File-Level Dependents ({len(report.file_dependents)} modules import defining file)"))
        for fdep in report.file_dependents[:10]:
            click.echo(f"  * {fdep}")
        if len(report.file_dependents) > 10:
            click.echo(f"  ... and {len(report.file_dependents) - 10} additional consuming modules.")

    click.echo("\n" + format_header(f"Affected Files ({len(report.affected_files)})"))
    if report.affected_files:
        for f in report.affected_files[:10]:
            click.echo(f"  * {f}")
        if len(report.affected_files) > 10:
            click.echo(f"  ... and {len(report.affected_files) - 10} additional affected files.")
    else:
        click.echo("  * No affected files identified")

    click.echo("\n" + format_header("Evidence"))
    for ev in report.evidence:
        click.echo(f"  * {ev}")
