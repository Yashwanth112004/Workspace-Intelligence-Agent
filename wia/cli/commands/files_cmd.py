"""CLI command for `wia files`."""

import click
from wia.cli.formatting import format_bytes, format_kv, format_error, format_header
from wia.services.inspection_service import InspectionService


@click.command("files", help="Display indexed workspace files.")
@click.argument("path", type=click.Path(exists=False), required=False)
@click.option(
    "--language",
    "-l",
    type=str,
    help="Filter files by programming language (e.g. Python, TypeScript).",
)
@click.pass_context
def files_cmd(ctx: click.Context, path: str | None, language: str | None) -> None:
    """List files recorded in the current WIA workspace index."""
    result = InspectionService.list_files(target_path=path, language=language)

    if not result.success:
        click.echo(format_error(result.message), err=True)
        ctx.exit(1)

    data = result.data or {}
    files = data.get("files", [])
    filter_lang = data.get("language_filter")

    subtitle = f"Filter: Language='{filter_lang}'" if filter_lang else None
    click.echo(format_header("WIA Indexed Files", subtitle=subtitle))
    click.echo(format_kv("Workspace", data.get("workspace_path", "")))
    click.echo(format_kv("Total Matching Files", str(len(files))))
    click.echo()

    if not files:
        click.echo("No matching indexed files found.")
        return

    for rec in files:
        rel_path = rec.get("relative_path", "")
        lang = rec.get("language", "Unknown")
        size = format_bytes(rec.get("file_size", 0))

        click.echo(f"  {click.style(rel_path, fg='bright_white')} ({lang}, {size})")
