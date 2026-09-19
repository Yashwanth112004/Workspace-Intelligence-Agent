"""WIA CLI `serve` command for starting the local API backend server daemon."""

import os
import sys
from pathlib import Path
import click
from wia.cli.formatting import format_error, format_header


@click.command(name="serve", help="Start the local WIA backend server daemon.")
@click.option("--host", "-h", default="127.0.0.1", help="Host address to bind.")
@click.option("--port", "-p", default=8000, type=int, help="Port number.")
@click.option("--reload", is_flag=True, help="Enable auto-reloading for development.")
def serve_cmd(host: str, port: int, reload: bool) -> None:
    """Start local FastAPI backend server."""
    click.echo(format_header(f"Starting WIA Daemon Server on http://{host}:{port}"))

    # Ensure backend directory is in sys.path
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    backend_dir = root_dir / "backend"
    if str(backend_dir) not in sys.path and backend_dir.exists():
        sys.path.insert(0, str(backend_dir))

    try:
        import uvicorn
        uvicorn.run("app.main:app", host=host, port=port, reload=reload)
    except ImportError:
        click.echo(format_error("Uvicorn is not installed. Install with 'pip install uvicorn'."))
    except Exception as err:
        click.echo(format_error(f"Failed to start server: {err}"))
