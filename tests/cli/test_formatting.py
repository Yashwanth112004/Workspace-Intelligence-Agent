"""Unit tests for CLI formatting utilities."""

from wia.cli.formatting import format_bytes, format_kv, format_error, format_header


def test_format_bytes():
    """Verify human-readable byte formatting across sizes."""
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1536) == "1.5 KB"
    assert format_bytes(1048576) == "1.0 MB"
    assert format_bytes(1073741824) == "1.0 GB"


def test_format_kv():
    """Verify key-value display formatting."""
    formatted = format_kv("Status", "Indexed", indent=4)
    assert "Status:" in formatted
    assert "Indexed" in formatted
    assert formatted.startswith("    ")


def test_format_error():
    """Verify error string formatting."""
    formatted = format_error("Path does not exist")
    assert "Error:" in formatted
    assert "Path does not exist" in formatted


def test_format_header():
    """Verify section header formatting."""
    header = format_header("Workspace Summary")
    assert "=== Workspace Summary ===" in header
