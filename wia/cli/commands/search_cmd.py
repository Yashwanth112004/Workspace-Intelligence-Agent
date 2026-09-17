"""WIA CLI `search` command for querying workspace index symbols and files."""

from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header, format_kv, format_warning
from wia.core.search_engine import WorkspaceSearchEngine
from wia.storage.repository import IndexRepository


@click.command(name="search", help="Search workspace index for symbols, file paths, or languages.")
@click.argument("query", required=False, default="")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
@click.option("--language", "-l", help="Filter search results by programming language (e.g. Python, JavaScript).")
@click.option("--type", "-t", "symbol_type", help="Filter search results by symbol type (class, function, import).")
@click.option("--limit", "-n", default=10, type=int, help="Maximum number of results to display.")
def search_cmd(
    query: str, workspace: str | None, language: str | None, symbol_type: str | None, limit: int
) -> None:
    """Search workspace index for matching code symbols and files."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Workspace Search for '{path.name}'"))

    index = IndexRepository.load_index(path)
    if not index:
        click.echo(
            format_error(
                f"No WIA index found at '{path}'. Run 'wia index' first before searching."
            )
        )
        return

    results = WorkspaceSearchEngine.search(
        index,
        query=query,
        language_filter=language,
        symbol_type_filter=symbol_type,
        limit=limit,
    )

    if not results:
        click.echo(format_warning(f"No search results found matching query '{query}'."))
        return

    click.echo(format_kv("Query", query if query else "(all)"))
    click.echo(format_kv("Results Displayed", str(len(results))))
    click.echo("")

    for idx, res in enumerate(results, start=1):
        syms_str = f" | Symbols: {', '.join(res.matched_symbols)}" if res.matched_symbols else ""
        click.echo(f"  {idx}. {res.file_path} [{res.language}] (Score: {res.score:.1f}{syms_str})")
