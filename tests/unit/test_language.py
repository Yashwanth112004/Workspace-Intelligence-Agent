"""Unit tests for LanguageDetector core engine."""

from pathlib import Path
from wia.core.language import LanguageDetector


def test_detect_by_extension():
    """Verify language detection by extension."""
    assert LanguageDetector.detect_language("main.py") == "Python"
    assert LanguageDetector.detect_language("index.ts") == "TypeScript"
    assert LanguageDetector.detect_language("app.jsx") == "JavaScript React"
    assert LanguageDetector.detect_language("lib.rs") == "Rust"
    assert LanguageDetector.detect_language("server.go") == "Go"


def test_detect_by_filename():
    """Verify language detection by known filenames."""
    assert LanguageDetector.detect_language("Dockerfile") == "Docker"
    assert LanguageDetector.detect_language("Makefile") == "Makefile"
    assert LanguageDetector.detect_language("CMakeLists.txt") == "CMake"


def test_detect_by_shebang(tmp_path: Path):
    """Verify language detection by shebang line analysis."""
    script_file = tmp_path / "script_without_ext"
    script_file.write_text("#!/usr/bin/env python3\nprint('hello')", encoding="utf-8")

    assert LanguageDetector.detect_language(script_file) == "Python"


def test_detect_unknown_file():
    """Verify unmapped extension returns 'Unknown'."""
    assert LanguageDetector.detect_language("custom.xyz123") == "Unknown"
