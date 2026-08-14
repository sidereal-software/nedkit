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

#: The piping commands carry the same column arithmetic verbatim, because the
#: audience pastes a command body into a dialog and a shared subroutine would
#: have to be installed separately. The markers are what makes the copy
#: checkable.
SHARED_START = b"# --- shared: column arithmetic ---"
SHARED_END = b"# --- end shared ---"


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


def _shared_blocks() -> dict[str, bytes]:
    """The shared column-arithmetic block from every command carrying one.

    Read as bytes rather than text. This is a byte-identity check, and a lost
    trailing space or a stray CR is exactly the drift it exists to catch.
    """
    blocks = {}
    for path in command_files(REPO_ROOT):
        raw = path.read_bytes()
        start = raw.find(SHARED_START)
        end = raw.find(SHARED_END, start)
        if start != -1 and end != -1:
            blocks[path.name] = raw[start : end + len(SHARED_END)]
    return blocks


def _first_difference(left: bytes, right: bytes) -> str:
    left_lines = left.split(b"\n")
    right_lines = right.split(b"\n")
    for number, (a, b) in enumerate(zip(left_lines, right_lines), start=1):
        if a != b:
            return f"first difference at line {number} of the block:\n  {a!r}\n  {b!r}"
    return f"the block is {len(left_lines)} lines in one and {len(right_lines)} in the other"


def test_a_command_that_opens_the_shared_block_also_closes_it() -> None:
    """Half a marker pair would let the identity check below read the wrong text."""
    for path in command_files(REPO_ROOT):
        raw = path.read_bytes()
        if SHARED_START in raw:
            assert SHARED_END in raw, (
                f"{path.name} opens the shared column arithmetic with "
                f"{SHARED_START.decode()} and never closes it. Add "
                f"{SHARED_END.decode()} at the end of the copied block."
            )


def test_the_shared_column_arithmetic_is_copied_verbatim() -> None:
    """The piped copies of the column arithmetic have to stay byte-identical.

    Nothing else holds them together. Fix a bug in one command and forget the
    other and the forgotten one ships the bug, with no symptom until someone
    runs the command that was not touched.
    """
    blocks = _shared_blocks()
    assert len(blocks) > 1, (
        "fewer than two commands carry the shared column arithmetic, so there "
        "is nothing left for this test to hold together. If only one command "
        "needs the block now, move it into a macros/lib/ subroutine and delete "
        f"this test. Found: {sorted(blocks) or 'none'}"
    )

    reference, *others = sorted(blocks)
    for name in others:
        assert blocks[name] == blocks[reference], (
            f"the shared column arithmetic in {name} has drifted from "
            f"{reference}. Both commands carry the same block on purpose, and "
            "this test is the only thing stopping a fix landing in one and not "
            f"the other. Copy the whole block from {reference}, markers "
            f"included.\n{_first_difference(blocks[reference], blocks[name])}"
        )


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
