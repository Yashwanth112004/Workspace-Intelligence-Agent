"""WIA CLI `doctor` command for environment diagnostic health checks."""

import os
from pathlib import Path
import sys
import click
import wia
from wia.cli.formatting import format_header
from wia.storage.sqlite_store import SQLiteStore


@click.command(name="doctor", help="Run system diagnostics and verify environment health.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def doctor_cmd(workspace: str | None) -> None:
    """Perform diagnostic health checks on workspace, dependencies, and storage."""
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header("WIA System Diagnostics & Doctor Health Check"))

    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    py_mark = click.style("[OK]", fg="green") if py_ok else click.style("[WARN] (Requires Python >= 3.10)", fg="yellow")
    click.echo(f"  Python Version: {py_ver} ({py_mark})")

    # 2. WIA version
    click.echo(f"  WIA Package Version: {wia.__version__} ({click.style('[OK]', fg='green')})")

    # 3. Workspace Writable Check
    wia_dir = path / ".wia"
    writable = os.access(path, os.W_OK)
    w_mark = click.style("[OK]", fg="green") if writable else click.style("[ERROR] (Directory not writable)", fg="red")
    init_str = click.style("[Initialized]", fg="green") if wia_dir.exists() else click.style("[Not Initialized] (Run wia init)", fg="yellow")
    click.echo(f"  Workspace Path: {path} ({w_mark})")
    click.echo(f"  WIA Metadata Dir: {wia_dir} ({init_str})")

    # 4. SQLite Storage accessibility
    try:
        db_file = wia_dir / "workspace.db"
        conn = SQLiteStore.get_connection(db_file)
        SQLiteStore.init_schema(conn)
        conn.close()
        db_mark = click.style("[OK]", fg="green")
    except Exception as err:
        db_mark = click.style(f"[ERROR] ({err})", fg="red")
    click.echo(f"  SQLite Store: {db_mark}")

    # 5. Git CLI availability
    import subprocess
    try:
        git_res = subprocess.run(["git", "--version"], capture_output=True, text=True)
        git_mark = click.style(f"[OK] {git_res.stdout.strip()}", fg="green") if git_res.returncode == 0 else click.style("[WARN] Not available", fg="yellow")
    except Exception:
        git_mark = click.style("[WARN] Git CLI not found in PATH", fg="yellow")
    click.echo(f"  Git CLI: {git_mark}")

    click.echo("\nDoctor health check complete.")
