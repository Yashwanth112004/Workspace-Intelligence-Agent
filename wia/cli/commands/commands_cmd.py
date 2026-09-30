"""CLI command `wia commands` for inspecting runnable project developer commands."""

import json
from pathlib import Path
import click
from wia.cli.formatting import format_header
from wia.core.project_commands import ProjectCommandDetector
from wia.storage.repository import IndexRepository


@click.command("commands", help="Detect and display runnable build, dev, test, and run commands for the project.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option(
    "--json-output",
    "--json",
    is_flag=True,
    help="Output detected commands as JSON payload.",
)
@click.option(
    "--category",
    "-c",
    type=str,
    help="Filter by category (e.g., 'run', 'test', 'build', 'install').",
)
def commands_cmd(workspace: str | None, json_output: bool, category: str | None) -> None:
    """Detect and output developer commands for running, testing, and building the project."""
    ws_path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    index = IndexRepository.load_index(ws_path)

    cmds = ProjectCommandDetector.detect_commands(ws_path, index=index)

    if category:
        cat_lower = category.lower()
        cmds = [c for c in cmds if cat_lower in c["category"].lower() or cat_lower in c["desc"].lower()]

    if json_output:
        click.echo(json.dumps(cmds, indent=2))
        return

    click.echo(format_header(f"Runnable Project Commands — {ws_path.name}"))

    if not cmds:
        click.echo("No specific manifest scripts or runtime entrypoints detected.")
        return

    # Group commands by category
    categories: dict[str, list[dict]] = {}
    for c in cmds:
        cat = c["category"]
        categories.setdefault(cat, []).append(c)

    for cat_name, cat_cmds in categories.items():
        click.echo()
        click.echo(click.style(f"  {cat_name}", fg="cyan", bold=True))
        for item in cat_cmds:
            desc = item["desc"]
            cmd_str = item["command"]
            source = item.get("source", "")
            source_tag = f" ({source})" if source else ""

            click.echo(f"    • {desc}{click.style(source_tag, fg='bright_black')}")
            click.echo(f"      {click.style('$', fg='green', bold=True)} {click.style(cmd_str, bold=True)}")
    click.echo()
