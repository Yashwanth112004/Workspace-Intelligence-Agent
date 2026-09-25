"""Main CLI entrypoint module for WIA."""

import sys
import traceback
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure package root is in sys.path dynamically
_pkg_root = Path(__file__).resolve().parent.parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

_backend_dir = _pkg_root / "backend"
if str(_backend_dir) not in sys.path and _backend_dir.exists():
    sys.path.insert(0, str(_backend_dir))


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
from wia.cli.commands.config_cmd import config_cmd, auth_cmd
from wia.cli.commands.flow_cmd import flow_cmd
from wia.cli.commands.diff_cmd import diff_cmd
from wia.cli.commands.export_cmd import export_cmd
from wia.cli.commands.serve_cmd import serve_cmd
from wia.cli.commands.decide_cmd import decide_cmd
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
  init          Initialize WIA workspace metadata (.wia directory)
  index / scan  Build/update the repository index with parallel processing
  status        Show current workspace indexing status
  files         List indexed workspace files
  info          Display workspace language & framework metadata
  search        Search workspace symbols, files, and relationships
  ask / query   Ask AI reasoning agent questions grounded in codebase context
  explain       Explain specific files, notebooks, or declared AST symbols
  architecture  View system architecture, boundaries & dependency cycles
  flow          Trace code execution call flow hierarchy
  impact        Analyze refactoring blast radius and caller impact
  diff          Inspect git diff and affected symbols
  summary       Generate structured facts & intelligence summary
  config        Configure AI providers, models, and credentials
  auth          Interactive setup wizard for AI provider API keys
  doctor        Run system diagnostics and verify environment health
  export        Export workspace graph and intelligence schema
  serve         Launch local backend server daemon
  version       Show WIA version information
""",
    epilog="For detailed command usage, run: wia <command> --help",
)
@click.version_option(
    version=wia.__version__,
    prog_name="wia",
    message="%(prog)s version %(version)s",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose diagnostic output.")
@click.option(
    "--summary",
    is_flag=True,
    help="Generate workspace intelligence summary (alias for 'wia summary').",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, summary: bool = False) -> None:
    """WIA CLI root entrypoint."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["logger"] = setup_logger(verbose=verbose)

    if summary:
        ctx.invoke(summary_cmd)
        return

    if ctx.invoked_subcommand is None:
        click.echo(f"WIA — Workspace Intelligence Agent (v{wia.__version__})")
        click.echo("Use 'wia --help' for usage and available commands.")


# Register core CLI subcommands
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
main.add_command(auth_cmd)
main.add_command(flow_cmd)
main.add_command(diff_cmd)
main.add_command(export_cmd)
main.add_command(serve_cmd)
main.add_command(decide_cmd)

# Register command aliases for compatibility
main.add_command(ask_cmd, name="query")
main.add_command(index_cmd, name="scan")


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
