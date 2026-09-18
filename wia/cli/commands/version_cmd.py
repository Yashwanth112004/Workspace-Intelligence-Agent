"""Version CLI command implementation."""

import click
import wia


@click.command("version", help="Show WIA version information.")
def version_cmd() -> None:
    """Display the installed WIA version."""
    click.echo(f"wia version {wia.__version__}")
