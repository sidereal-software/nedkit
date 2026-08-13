"""The static checks, applied to the macros actually in the repo.

None of this needs XNEdit, so it runs everywhere and is the first thing to look
at when the suite goes red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import parse
from nedkit.checks import check_command, check_library
from nedkit.macro import command_files, library_files

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", command_files(REPO_ROOT), ids=lambda p: p.name)
def test_command_conventions(path: Path) -> None:
    findings = check_command(parse(path))
    assert not findings, "\n".join(str(finding) for finding in findings)


@pytest.mark.parametrize("path", library_files(REPO_ROOT), ids=lambda p: p.name)
def test_library_conventions(path: Path) -> None:
    findings = check_library(path)
    assert not findings, "\n".join(str(finding) for finding in findings)


def test_there_are_macros_to_check() -> None:
    """Guard against the parametrised tests above silently collecting nothing."""
    assert command_files(REPO_ROOT), "no commands found in macros/commands/"
    assert library_files(REPO_ROOT), "no libraries found in macros/lib/"
