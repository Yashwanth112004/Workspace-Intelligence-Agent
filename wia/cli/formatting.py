"""Terminal formatting and output helper utilities for WIA CLI."""

import click


def format_bytes(num_bytes: int) -> str:
    """Format raw byte counts into human-friendly strings (B, KB, MB, GB)."""
    if num_bytes < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            if unit == "B":
                return f"{int(num_bytes)} B"
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_header(title: str, subtitle: str | None = None) -> str:
    """Format a standard WIA section header."""
    header = click.style(f"=== {title} ===", fg="cyan", bold=True)
    if subtitle:
        header += f"\n{click.style(subtitle, fg='bright_black')}"
    return header


def format_kv(key: str, value: str, indent: int = 2) -> str:
    """Format key-value status pair for CLI displays."""
    prefix = " " * indent
    formatted_key = click.style(f"{key}:", bold=True)
    return f"{prefix}{formatted_key} {value}"


def format_error(message: str) -> str:
    """Format error messages consistently."""
    prefix = click.style("Error:", fg="red", bold=True)
    return f"{prefix} {message}"


def format_warning(message: str) -> str:
    """Format warning messages consistently."""
    prefix = click.style("Warning:", fg="yellow", bold=True)
    return f"{prefix} {message}"


def format_success(message: str) -> str:
    """Format success messages consistently."""
    prefix = click.style("Success:", fg="green", bold=True)
    return f"{prefix} {message}"
