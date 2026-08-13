"""Run every menu command against its fixtures.

A command in ``macros/commands/<name>.nm`` is tested by the directories under
``tests/fixtures/<name>/``. Each of those is one case:

    tests/fixtures/trim-trailing-blanks/basic/
        input.txt       the buffer before
        expected.txt    the buffer after, byte for byte
        setup.nm        optional macro run first, e.g. select(0, 12)

Fixtures are compared as bytes, because NED's data files are not reliably
UTF-8 and the difference between a stripped tab and a stripped space is the
entire point of some of these commands.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse
from nedkit.macro import command_files

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _cases() -> list[tuple[Path, Path]]:
    cases = []
    for command in command_files(REPO_ROOT):
        case_root = FIXTURE_ROOT / command.stem
        if not case_root.is_dir():
            continue
        cases.extend(
            (command, case)
            for case in sorted(case_root.iterdir())
            if case.is_dir() and (case / "input.txt").is_file()
        )
    return cases


def _readable(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").replace(" ", "·").replace("\t", "→")


@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_every_command_has_fixtures(command: Path) -> None:
    """A command with no fixtures is untested, which should be loud."""
    case_root = FIXTURE_ROOT / command.stem
    cases = (
        [case for case in case_root.iterdir() if case.is_dir()]
        if case_root.is_dir()
        else []
    )
    assert cases, (
        f"{command.name} has no fixtures. Add at least one case under "
        f"tests/fixtures/{command.stem}/<case>/ with input.txt and expected.txt."
    )


@pytest.mark.xnedit
@pytest.mark.parametrize(
    ("command", "case"), _cases(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_command_against_fixture(
    command: Path, case: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    macro = parse(command)
    setup = case / "setup.nm"
    body = macro.body
    if setup.is_file():
        body = setup.read_text(encoding="utf-8").rstrip() + "\n" + body

    run = runner.run_on_bytes(
        body, (case / "input.txt").read_bytes(), tmp_path, name="input.txt"
    )
    assert run.ok, f"{command.name} on {case.name}: {run.describe()}"

    expected = (case / "expected.txt").read_bytes()
    assert run.output == expected, (
        f"{command.name} on {case.name} produced the wrong buffer "
        "(· is a space, → a tab)\n"
        f"expected: {_readable(expected)!r}\n"
        f"     got: {_readable(run.output or b'')!r}"
    )


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_command_is_idempotent(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """Running a command twice does the same as running it once.

    Not a law of nature, but it holds for every cleanup command written so far,
    and a command that fails it is worth a second look before it ships.
    """
    case_root = FIXTURE_ROOT / command.stem
    cases = sorted(case_root.glob("*/expected.txt")) if case_root.is_dir() else []
    if not cases:
        pytest.skip("no fixtures")

    macro = parse(command)
    for expected_file in cases:
        settled = expected_file.read_bytes()
        run = runner.run_on_bytes(
            macro.body, settled, tmp_path, name=f"{expected_file.parent.name}.txt"
        )
        assert run.ok, f"{command.name} on settled input: {run.describe()}"
        assert run.output == settled, (
            f"{command.name} changed {expected_file.parent.name} on a second run, "
            "so it is not idempotent"
        )


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_command_does_not_corrupt_a_non_utf8_file(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """Whatever a command does to a latin-1 file, the bytes have to survive.

    NED's data files are not reliably UTF-8, and the damage worth guarding
    against is a character quietly re-encoded or dropped on save.

    Whether the buffer locks first is a different question, and a
    locale-dependent one: a file that is entirely latin-1 decodes cleanly under
    a latin-1 locale and is an error under a UTF-8 one. The
    unconvertible-byte-locks-the-file fixture pins the lock with a file that is
    an error either way. This test drops that question and keeps the invariant
    that holds everywhere, classic NEdit included.
    """
    source = "NGC 4151 café   \nsecond   \n".encode("latin-1")
    run = runner.run_on_bytes(parse(command).body, source, tmp_path, name="latin1.txt")

    assert run.ok, f"{command.name}: {run.describe()}"
    assert run.output is not None
    assert b"\xe9" in run.output, (
        f"{command.name} lost the latin-1 byte: {run.output!r}"
    )
