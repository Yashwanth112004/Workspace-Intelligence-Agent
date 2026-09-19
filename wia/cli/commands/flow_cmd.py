"""WIA CLI `flow` command for tracing execution flow paths."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv
from wia.knowledge.graph import WorkspaceGraph
from wia.storage.repository import IndexRepository


@click.command(name="flow", help="Trace execution call flow starting from an entry point symbol.")
@click.argument("entry")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option("--max-depth", "-d", type=int, default=5, help="Maximum traversal call depth.")
def flow_cmd(entry: str, workspace: str | None, max_depth: int) -> None:
    """Trace code execution flow starting from a symbol or entry point."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Execution Call Flow Tracing for '{entry}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before tracing flow."
            )
        )
        return

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    # Search for entry node
    matching_nodes = [
        n for n in graph.nodes.values()
        if n.name.lower() == entry.lower() or n.node_id.endswith(f":{entry}")
    ]

    if not matching_nodes:
        # Fallback to partial search
        matching_nodes = [n for n in graph.nodes.values() if entry.lower() in n.name.lower()]

    if not matching_nodes:
        click.echo(format_error(f"No symbol matching '{entry}' found in workspace."))
        click.echo(f"Run 'wia search {entry}' to explore available symbols.")
        return

    root_node = matching_nodes[0]
    click.echo(format_kv("Root Entry", f"{root_node.name} ({root_node.file_path})"))
    click.echo("\n" + click.style("Execution Call Hierarchy:", bold=True))

    visited = set()
    step_count = 0

    def _traverse(node_id: str, depth: int):
        nonlocal step_count
        if depth > max_depth or node_id in visited:
            return
        visited.add(node_id)
        outgoing = graph.get_outgoing_edges(node_id)
        for edge in outgoing:
            target = graph.nodes.get(edge.target_id)
            if target and edge.relation_type in ("CALLS", "IMPORTS"):
                step_count += 1
                indent = "  " * depth
                rel_badge = click.style(f"[{edge.relation_type}]", fg="cyan")
                click.echo(f"{indent}Step {step_count}: {rel_badge} -> {target.name} ({target.file_path or 'external'})")
                _traverse(edge.target_id, depth + 1)

    _traverse(root_node.node_id, depth=1)

    if step_count == 0:
        click.echo("  * No downstream internal calls discovered for this symbol.")
    click.echo(f"\nTrace complete. Total flow steps: {step_count}\n")
