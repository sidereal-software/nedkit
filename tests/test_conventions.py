"""The static checks, applied to the macros actually in the repo.

None of this needs XNEdit, so it runs everywhere and is the first thing to look
at when the suite goes red.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import parse
from nedkit.checks import check_command, check_library, find_definitions
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


def _subroutines() -> list[str]:
    return sorted(
        name
        for path in library_files(REPO_ROOT)
        for _, name in find_definitions(path.read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("name", _subroutines())
def test_every_subroutine_is_named_in_a_test(name: str) -> None:
    """A subroutine nobody calls from a test is a subroutine nobody checks.

    Commands get this from their fixtures. Subroutines have no fixtures, so
    this looks for the name in tests/ instead. It proves a test mentions the
    subroutine, not that the test is any good, which is the most a check like
    this can honestly claim.
    """
    tests = Path(__file__).parent
    mentioned = any(
        name in path.read_text(encoding="utf-8")
        for path in tests.glob("test_*.py")
        if path.name != Path(__file__).name
    )
    assert mentioned, (
        f"{name}() has no test. Add one to tests/test_lib_{name.removeprefix('ned_')}.py "
        "or to the existing test module for its library."
    )
