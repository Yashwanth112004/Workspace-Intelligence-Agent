"""CLI command for `wia index`."""

import click
from wia.cli.formatting import format_kv, format_error, format_header
from wia.services.indexing_service import IndexingService


@click.command("index", help="Index the workspace repository.")
@click.argument("path", type=click.Path(exists=False), required=False)
@click.option(
    "--force-reindex",
    "-f",
    is_flag=True,
    help="Force complete re-indexing of all files.",
)
@click.pass_context
def index_cmd(ctx: click.Context, path: str | None, force_reindex: bool) -> None:
    """Run the WIA repository indexing pipeline."""
    result = IndexingService.index_workspace(target_path=path, force_reindex=force_reindex)

    if not result.success:
        click.echo(format_error(result.message), err=True)
        ctx.exit(1)

    data = result.data or {}
    click.echo(format_header("WIA Repository Indexing"))
    click.echo(format_kv("Repository", data.get("workspace_path", "")))
    click.echo()
    click.echo(format_kv("Files Discovered", str(data.get("total_discovered", 0))))
    click.echo(format_kv("Files Indexed", str(data.get("total_indexed", 0))))
    click.echo(format_kv("Files Ignored", str(data.get("total_ignored", 0))))

    changes = data.get("changes", {})
    click.echo()
    click.echo(click.style("  Changes:", bold=True))
    click.echo(format_kv("Added", str(changes.get("added", 0)), indent=4))
    click.echo(format_kv("Modified", str(changes.get("modified", 0)), indent=4))
    click.echo(format_kv("Deleted", str(changes.get("deleted", 0)), indent=4))
    click.echo(format_kv("Unchanged", str(changes.get("unchanged", 0)), indent=4))

    languages = data.get("languages", {})
    if languages:
        click.echo()
        click.echo(click.style("  Languages:", bold=True))
        for lang, count in languages.items():
            click.echo(format_kv(lang, str(count), indent=4))

    frameworks = data.get("frameworks", [])
    if frameworks:
        click.echo()
        click.echo(click.style("  Frameworks & Tools:", bold=True))
        for fw in frameworks:
            click.echo(f"    - {fw}")

    click.echo()
    click.echo(format_kv("Duration", f"{data.get('duration_seconds', 0.0)}s"))
