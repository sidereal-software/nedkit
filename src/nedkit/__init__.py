"""Tooling for the NED team's XNEdit macros.

This package is the test harness, not a deliverable. Nothing the NED team runs
depends on it, which is why it is free to use a current Python while their own
scripts stay on 3.9.
"""

from nedkit.chartable import character_tables, label_for, parse_character_table
from nedkit.checks import Finding
from nedkit.macro import MacroFile, command_files, library_files, parse
from nedkit.runner import MacroRun, XNEditRunner, XNEditUnavailable, find_binary

__all__ = [
    "Finding",
    "MacroFile",
    "MacroRun",
    "XNEditRunner",
    "XNEditUnavailable",
    "character_tables",
    "command_files",
    "find_binary",
    "label_for",
    "library_files",
    "parse",
    "parse_character_table",
]
