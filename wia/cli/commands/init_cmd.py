"""CLI command for `wia init`."""

import sys
import click
from wia.cli.formatting import format_kv, format_error, format_header
from wia.services.init_service import InitService


@click.command("init", help="Initialize WIA in a software workspace.")
@click.argument("path", type=click.Path(exists=False), required=False)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force re-initialization if .wia directory already exists.",
)
@click.pass_context
def init_cmd(ctx: click.Context, path: str | None, force: bool) -> None:
    """Initialize WIA metadata directory (.wia) inside target workspace."""
    result = InitService.initialize_workspace(target_path=path, force=force)

    if not result.success:
        click.echo(format_error(result.message), err=True)
        ctx.exit(1)

    data = result.data or {}
    click.echo(format_header("WIA Initialization"))
    click.echo(format_kv("Workspace Path", data.get("workspace_path", "")))
    click.echo(format_kv("WIA Directory", data.get("wia_dir", "")))

    if data.get("gitignore_hint"):
        click.echo()
        click.echo(
            click.style(
                "Tip: Add '.wia/' to your root .gitignore to avoid committing index data.",
                fg="yellow",
            )
        )
