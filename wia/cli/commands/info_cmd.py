"""CLI command for `wia info`."""

import click
from wia.cli.formatting import format_kv, format_error, format_header
from wia.services.inspection_service import InspectionService


@click.command("info", help="Display workspace summary information.")
@click.argument("path", type=click.Path(exists=False), required=False)
@click.pass_context
def info_cmd(ctx: click.Context, path: str | None) -> None:
    """Display high-level metadata, statistics, languages, and frameworks from WIA index."""
    result = InspectionService.get_info(target_path=path)

    if not result.success:
        click.echo(format_error(result.message), err=True)
        ctx.exit(1)

    data = result.data or {}
    stats = data.get("stats", {})
    languages = data.get("languages", [])
    frameworks = data.get("frameworks", [])

    click.echo(format_header("WIA Workspace Information"))
    click.echo(format_kv("Workspace", data.get("workspace_path", "")))
    click.echo(format_kv("WIA Version", data.get("wia_version", "")))
    click.echo(format_kv("Index Schema Version", data.get("index_version", "")))
    click.echo(format_kv("Last Indexed", data.get("indexed_at", "")))

    click.echo()
    click.echo(click.style("  File Statistics:", bold=True))
    click.echo(format_kv("Discovered Files", str(stats.get("total_discovered", 0)), indent=4))
    click.echo(format_kv("Indexed Files", str(stats.get("total_indexed", 0)), indent=4))
    click.echo(format_kv("Ignored Files", str(stats.get("total_ignored", 0)), indent=4))

    if languages:
        click.echo()
        click.echo(click.style("  Language Distribution:", bold=True))
        for item in languages:
            lang = item["language"]
            cnt = item["count"]
            pct = item["percentage"]
            click.echo(format_kv(lang, f"{cnt} files ({pct}%)", indent=4))

    if frameworks:
        click.echo()
        click.echo(click.style("  Frameworks & Development Tools:", bold=True))
        for fw in frameworks:
            click.echo(f"    - {fw}")
