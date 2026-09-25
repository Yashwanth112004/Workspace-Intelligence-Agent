"""Terminal formatting and output helper utilities for WIA CLI."""

import click


_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")
_THRESHOLDS = tuple(1024 ** i for i in range(len(_UNITS)))


def format_bytes(num_bytes: int) -> str:
    """Format raw byte counts into human-friendly strings (B, KB, MB, GB) with O(1) threshold calculation."""
    if num_bytes <= 0:
        return "0 B"
    for i in range(len(_UNITS) - 1, 0, -1):
        thresh = _THRESHOLDS[i]
        if num_bytes >= thresh:
            return f"{num_bytes / thresh:.1f} {_UNITS[i]}"
    return f"{int(num_bytes)} B"


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
