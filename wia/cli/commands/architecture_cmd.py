"""WIA CLI `architecture` command for displaying workspace architecture maps."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv, format_success
from wia.core.architecture import ArchitectureAnalyzer
from wia.storage.repository import IndexRepository


@click.command(name="architecture", help="Display workspace architecture boundaries and component map.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def architecture_cmd(workspace: str | None) -> None:
    """Analyze and output workspace architecture overview."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Architecture Intelligence for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before running architecture analysis."
            )
        )
        return

    arch = ArchitectureAnalyzer.analyze_workspace(index)

    # 1. Architecture Summary
    click.echo(click.style("ARCHITECTURE SUMMARY", bold=True))
    click.echo(arch.summary)

    # 2. General Metrics
    click.echo()
    click.echo(format_kv("Total Indexed Files", str(arch.total_files)))
    click.echo(
        format_kv(
            "Total Symbols Extracted",
            f"{arch.total_symbols} ({arch.classes_count} classes, {arch.functions_count} functions/methods)",
        )
    )
    click.echo(
        format_kv("Frameworks & Tools", ", ".join(arch.frameworks) if arch.frameworks else "None")
    )

    # 3. Directory Hierarchy Tree
    click.echo("\n" + format_header("Directory Hierarchy Tree"))
    for line in arch.directory_tree:
        click.echo(f"  {line}")

    # 4. Architectural Components & Responsibilities
    click.echo("\n" + format_header("Architectural Components & Responsibilities"))
    for comp in arch.components:
        if comp.file_count > 0:
            click.echo(click.style(f"  * {comp.name} (`{comp.path_prefix}/`)", bold=True))
            click.echo(f"    - Role: {comp.role}")
            click.echo(f"    - Responsibility: {comp.responsibility}")
            click.echo(
                f"    - Files & Symbols: {comp.file_count} files, {comp.symbol_count} symbols"
            )
            if comp.internal_dependencies:
                click.echo(f"    - Component Dependencies: {', '.join(comp.internal_dependencies)}")
            if comp.internal_dependents:
                click.echo(f"    - Consumed By: {', '.join(comp.internal_dependents)}")
            click.echo()

    # 5. Inter-Component Dependency Flow
    click.echo(format_header("Inter-Component Dependency Flow"))
    for step in arch.dependency_flow:
        click.echo(f"  {step}")

    # 6. Application Entry Points
    click.echo("\n" + format_header("Application Entry Points"))
    for ep in arch.entry_points:
        click.echo(f"  * {ep}")

    # 7. Fan-In & Fan-Out Analysis
    click.echo("\n" + format_header("High Fan-In Components (Shared Utilities)"))
    if arch.high_fan_in:
        for item in arch.high_fan_in:
            click.echo(f"  * `{item[0]}` (Fan-In: {item[1]}) — {item[2]}")
    else:
        click.echo("  * None detected.")

    click.echo("\n" + format_header("High Fan-Out Components (Orchestrators)"))
    if arch.high_fan_out:
        for item in arch.high_fan_out:
            click.echo(f"  * `{item[0]}` (Fan-Out: {item[1]}) — {item[2]}")
    else:
        click.echo("  * None detected.")

    # 8. Circular Dependencies
    click.echo("\n" + format_header("Circular Dependencies"))
    if arch.circular_dependencies:
        for cycle in arch.circular_dependencies:
            click.echo(f"  [WARNING] Cycle: {cycle}")
    else:
        click.echo(format_success("None detected."))

    # 9. Architectural Hotspots
    click.echo("\n" + format_header("Architectural Hotspots & Risks"))
    if arch.hotspots:
        for spot in arch.hotspots:
            click.echo(f"  * `{spot[0]}` — {spot[1]}")
    else:
        click.echo("  * No significant structural risks detected by the current analysis.")

    # 10. Evidence
    click.echo("\n" + format_header("Evidence"))
    for ev in arch.evidence:
        click.echo(f"  * {ev}")
