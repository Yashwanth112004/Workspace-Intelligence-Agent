"""WIA CLI `doctor` command for environment diagnostic health checks."""

import os
import sys
import sysconfig
from pathlib import Path
import click
import wia
from wia.cli.formatting import format_header, format_kv
from wia.storage.sqlite_store import SQLiteStore
from wia.llm.service import _load_env_file


@click.command(name="doctor", help="Run system diagnostics and verify environment health.")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to workspace directory.",
)
def doctor_cmd(workspace: str | None) -> None:
    """Perform diagnostic health checks on workspace, dependencies, and storage."""
    _load_env_file()
    path = Path(workspace).resolve() if workspace else Path.cwd().resolve()
    click.echo(format_header("WIA System Diagnostics & Doctor Health Check"))

    # 1. Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    py_mark = click.style("[OK]", fg="green") if py_ok else click.style("[WARN] (Requires Python >= 3.10)", fg="yellow")
    click.echo(f"  Python Version:        {py_ver} ({py_mark})")

    # 2. WIA version
    click.echo(f"  WIA Package Version:   {wia.__version__} ({click.style('[OK]', fg='green')})")

    # 3. System PATH Diagnostics
    scripts_dir = sysconfig.get_path("scripts")
    path_env = os.environ.get("PATH", "")
    in_path = scripts_dir.lower() in path_env.lower() if scripts_dir else False

    if in_path:
        click.echo(f"  Python Scripts in PATH: {click.style('[OK]', fg='green')}")
    else:
        click.echo(f"  Python Scripts in PATH: {click.style('[WARN] Missing from PATH', fg='yellow')}")
        click.echo(f"    • Scripts Directory: {scripts_dir}")
        if sys.platform == "win32":
            click.echo("    • Fix (PowerShell): " + click.style(f'[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{scripts_dir}", "User")', fg="cyan"))
        else:
            click.echo("    • Fix (Bash/Zsh):   " + click.style(f'export PATH="{scripts_dir}:$PATH"', fg="cyan"))

    # 4. Workspace Writable Check
    wia_dir = path / ".wia"
    writable = os.access(path, os.W_OK)
    w_mark = click.style("[OK]", fg="green") if writable else click.style("[ERROR] (Directory not writable)", fg="red")
    init_str = click.style("[Initialized]", fg="green") if wia_dir.exists() else click.style("[Not Initialized] (Run wia init)", fg="yellow")
    click.echo(f"  Workspace Path:        {path} ({w_mark})")
    click.echo(f"  WIA Metadata Dir:      {wia_dir} ({init_str})")

    # 5. SQLite Storage accessibility
    try:
        db_file = wia_dir / "workspace.db"
        conn = SQLiteStore.get_connection(db_file)
        SQLiteStore.init_schema(conn)
        conn.close()
        db_mark = click.style("[OK]", fg="green")
    except Exception as err:
        db_mark = click.style(f"[ERROR] ({err})", fg="red")
    click.echo(f"  SQLite Store:          {db_mark}")

    # 6. Git CLI availability
    import subprocess
    try:
        git_res = subprocess.run(["git", "--version"], capture_output=True, text=True)
        git_mark = click.style(f"[OK] {git_res.stdout.strip()}", fg="green") if git_res.returncode == 0 else click.style("[WARN] Not available", fg="yellow")
    except Exception:
        git_mark = click.style("[WARN] Git CLI not found in PATH", fg="yellow")
    click.echo(f"  Git CLI:               {git_mark}")

    # 7. AI Key Diagnostics
    ai_keys = {
        "NVIDIA NIM": os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Gemini": os.getenv("GEMINI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Groq": os.getenv("GROQ_API_KEY"),
    }
    configured_ais = [k for k, v in ai_keys.items() if v]
    if configured_ais:
        ai_status = click.style(f"[OK] ({', '.join(configured_ais)})", fg="green")
    else:
        ai_status = click.style("[Local Offline Only] (Set key via 'wia auth' or .env)", fg="yellow")
    click.echo(f"  AI Reasoning Layer:    {ai_status}")

    click.echo("\nDoctor health check complete.")
