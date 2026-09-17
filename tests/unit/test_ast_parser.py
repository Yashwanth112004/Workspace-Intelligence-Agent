"""Unit tests for ASTParser."""

from pathlib import Path
from wia.analyzers.code.ast_parser import ASTParser


def test_ast_parser_python():
    """Verify ASTParser extracts Python classes, functions, methods, and imports."""
    code = """
import os
from math import sqrt

class Calculator:
    \"\"\"Calculator class docstring.\"\"\"
    def add(self, a, b):
        return a + b

def main():
    calc = Calculator()
    print(calc.add(1, 2))
"""
    symbols = ASTParser.parse_python_content(code)
    names = {s.name: s.symbol_type for s in symbols}

    assert "os" in names
    assert names["os"] == "import"
    assert "math.sqrt" in names
    assert names["math.sqrt"] == "import"
    assert "Calculator" in names
    assert names["Calculator"] == "class"
    assert "add" in names
    assert names["add"] == "method"
    assert "main" in names
    assert names["main"] == "function"


def test_ast_parser_regex_fallback():
    """Verify regex fallback extracts symbols from non-Python or TS files."""
    code = """
import { useState } from 'react';

export class App {
}

export function render() {
}
"""
    symbols = ASTParser.parse_regex_fallback(code)
    names = {s.name: s.symbol_type for s in symbols}

    assert "App" in names
    assert names["App"] == "class"
    assert "render" in names
    assert names["render"] == "function"
