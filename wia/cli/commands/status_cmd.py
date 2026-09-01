"""CLI command for `wia status`."""

import click
from wia.cli.formatting import format_kv, format_error, format_header
from wia.core.metadata import WorkspaceStatusState
from wia.services.status_service import StatusService


@click.command("status", help="Show workspace indexing status.")
@click.argument("path", type=click.Path(exists=False), required=False)
@click.pass_context
def status_cmd(ctx: click.Context, path: str | None) -> None:
    """Display current workspace index status and pending changes."""
    result = StatusService.get_status(target_path=path)

    if not result.success:
        click.echo(format_error(result.message), err=True)
        ctx.exit(1)

    data = result.data or {}
    status_code = data.get("status_code", "")
    workspace_path = data.get("workspace_path", "")

    click.echo(format_header("WIA Workspace Status"))
    click.echo(format_kv("Workspace", workspace_path))

    if status_code == WorkspaceStatusState.NOT_INITIALIZED:
        click.echo(format_kv("Status", click.style("Not Initialized", fg="yellow")))
        click.echo()
        click.echo("WIA has not been initialized in this workspace.")
        click.echo("Run 'wia init' first.")
        return

    if status_code == WorkspaceStatusState.NO_INDEX:
        click.echo(format_kv("Status", click.style("Initialized — Not Indexed", fg="yellow")))
        click.echo()
        click.echo("The workspace has been initialized but has not been indexed yet.")
        click.echo("Run 'wia index' to build the workspace index.")
        return

    if status_code == WorkspaceStatusState.UP_TO_DATE:
        click.echo(format_kv("Status", click.style("Up to Date", fg="green")))
    else:
        click.echo(format_kv("Status", click.style("Changes Detected", fg="yellow")))

    click.echo(format_kv("Last Indexed", data.get("indexed_at", "")))
    click.echo(format_kv("Indexed Files", str(data.get("indexed_files_count", 0))))

    changes = data.get("changes", {})
    click.echo()
    click.echo(click.style("  Changes Since Last Index:", bold=True))
    click.echo(format_kv("Added", str(changes.get("added", 0)), indent=4))
    click.echo(format_kv("Modified", str(changes.get("modified", 0)), indent=4))
    click.echo(format_kv("Deleted", str(changes.get("deleted", 0)), indent=4))
    click.echo(format_kv("Unchanged", str(changes.get("unchanged", 0)), indent=4))

    if status_code == WorkspaceStatusState.CHANGES_DETECTED:
        click.echo()
        click.echo("The workspace has changed since the last index.")
        click.echo("Run 'wia index' to update the workspace intelligence.")
