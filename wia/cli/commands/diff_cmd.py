"""WIA CLI `diff` command for git diff and affected symbol analysis."""

from pathlib import Path
import click
from wia.analyzers.git.git_analyzer import GitAnalyzer
from wia.cli.formatting import format_error, format_header, format_kv


@click.command(name="diff", help="Analyze repository Git diff and affected symbols.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def diff_cmd(workspace: str | None) -> None:
    """Analyze Git status, changed files, and affected symbols."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header(f"Git Diff Analysis for '{path.name}'"))

    import subprocess
    try:
        res = subprocess.run(["git", "status", "--porcelain"], cwd=str(path), capture_output=True, text=True)
        if res.returncode != 0:
            click.echo(click.style(f"⚠️ '{path.name}' is not a Git repository or Git is unavailable.", fg="yellow"))
            return

        lines = [l for l in res.stdout.splitlines() if l.strip()]
        click.echo(format_kv("Git Repository", "Active"))
        click.echo(format_kv("Modified / Untracked Files", str(len(lines))))

        if lines:
            click.echo("\n" + click.style("Changed Files:", bold=True))
            for line in lines[:20]:
                status_code = line[:2].strip()
                f_path = line[3:].strip()
                color = "green" if "?" in status_code or "A" in status_code else "yellow" if "M" in status_code else "red"
                click.echo(f"  {click.style(status_code, fg=color):<4} {f_path}")
            if len(lines) > 20:
                click.echo(f"  ... and {len(lines) - 20} more files.")
        else:
            click.echo(click.style("✅ Working tree clean. No uncommitted changes.", fg="green"))
    except Exception as err:
        click.echo(format_error(f"Git diff failed: {err}"))
