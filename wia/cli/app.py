"""Main CLI entrypoint module for WIA."""

import sys
import traceback
import click
import wia
from wia.cli.commands.version_cmd import version_cmd
from wia.cli.commands.init_cmd import init_cmd
from wia.cli.commands.index_cmd import index_cmd
from wia.cli.commands.status_cmd import status_cmd
from wia.cli.commands.files_cmd import files_cmd
from wia.cli.commands.info_cmd import info_cmd
from wia.cli.commands.analyze_cmd import analyze_group
from wia.cli.commands.report_cmd import report_cmd
from wia.cli.commands.search_cmd import search_cmd
from wia.cli.commands.summary_cmd import summary_cmd
from wia.cli.commands.architecture_cmd import architecture_cmd
from wia.cli.commands.impact_cmd import impact_cmd
from wia.cli.commands.ask_cmd import ask_cmd
from wia.cli.commands.explain_cmd import explain_cmd
from wia.cli.commands.doctor_cmd import doctor_cmd
from wia.cli.commands.config_cmd import config_cmd
from wia.cli.formatting import format_error
from wia.exceptions import WIAError
from wia.utils.logger import setup_logger

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    help="""WIA — Workspace Intelligence Agent.

WIA inspects, indexes, and understands software workspaces.
Use WIA to build a persistent, incremental intelligence index of your repository.

\b
Common Commands:
  init       Initialize WIA workspace metadata (.wia directory)
  index      Build/update the repository index
  status     Show current workspace indexing status
  files      List indexed workspace files
  info       Display workspace language & framework metadata
  search     Search workspace symbols, files, and relationships
  explain    Explain workspace files, notebooks, or symbols
  impact     Analyze downstream blast radius and affected tests
  summary    Generate structured facts & intelligence summary
  ask        Ask AI reasoning queries grounded in codebase evidence
  config     Configure AI providers, models, and credentials
  version    Show WIA version information
""",
    epilog="For detailed command usage, run: wia <command> --help",
)
@click.version_option(
    version=wia.__version__,
    prog_name="wia",
    message="%(prog)s version %(version)s",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose diagnostic output.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """WIA CLI root entrypoint."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["logger"] = setup_logger(verbose=verbose)

    if ctx.invoked_subcommand is None:
        click.echo(f"WIA — Workspace Intelligence Agent (v{wia.__version__})")
        click.echo("Use 'wia --help' for usage and available commands.")


# Register CLI subcommands
main.add_command(version_cmd)
main.add_command(init_cmd)
main.add_command(index_cmd)
main.add_command(status_cmd)
main.add_command(files_cmd)
main.add_command(info_cmd)
main.add_command(analyze_group)
main.add_command(report_cmd)
main.add_command(search_cmd)
main.add_command(summary_cmd)
main.add_command(architecture_cmd)
main.add_command(impact_cmd)
main.add_command(ask_cmd)
main.add_command(explain_cmd)
main.add_command(doctor_cmd)
main.add_command(config_cmd)


def cli_entrypoint():
    """Execution entrypoint wrapping unhandled exceptions cleanly."""
    try:
        main(standalone_mode=True)
    except WIAError as err:
        click.echo(format_error(str(err)), err=True)
        sys.exit(1)
    except Exception as err:
        if "--verbose" in sys.argv or "-v" in sys.argv:
            traceback.print_exc()
        else:
            click.echo(
                format_error(
                    f"An unexpected error occurred: {err}. Use '--verbose' for tracebacks."
                ),
                err=True,
            )
        sys.exit(1)


if __name__ == "__main__":
    cli_entrypoint()
