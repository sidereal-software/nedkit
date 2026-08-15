"""Pad Columns, on the two things a fixture cannot say clearly.

The fixtures in ``tests/fixtures/pad-columns/`` settle what lands in the
buffer, byte for byte. Two properties are worth stating in their own terms as
well, because a byte comparison that fails on either one is a wall of escaped
bytes rather than an answer.

**Square means square on screen.** The requirement was "always have equal
space between", and equal is a thing the eye measures in characters. The
command this one replaces measured with ``length()``, which counts bytes, so a
column holding an accented name came out one place short for every extra byte
in it; that bug was pinned as a permanent xfail rather than fixed. The tests
below say what the fix is worth in the terms the bug was reported in.

**A long table is rebuilt in chunks.** The macro flushes its output every 200
lines to keep the string appends from going quadratic, and the newline between
two lines is written by a different branch from the newline inside a chunk. A
table longer than one chunk is the only input where that boundary exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

#: Three rows whose first and last columns hold values of different widths,
#: two of them with characters that take more than one byte. Padded, every row
#: is 26 characters wide and 26, 27 or 28 bytes long.
MIXED = (
    "Balázs|12:29:46.7|E2\nSmith|12:36:44.0|SB(s)m\nÅngström|12:30:49.4|S0\n"
).encode()

pytestmark = pytest.mark.xnedit


def pad(runner: XNEditRunner, data: bytes, workdir: Path) -> bytes:
    run = runner.run_on_bytes(
        parse(COMMANDS / "pad-columns.nm").body, data, workdir, name="table.txt"
    )
    assert run.ok, run.describe()
    assert run.output is not None, "Pad Columns left no file behind"
    return run.output


def rows(data: bytes) -> list[str]:
    """The data rows, decoded, so everything below counts characters."""
    return [line for line in data.decode("utf-8").split("\n") if "|" in line]


def only_xnedit(runner: XNEditRunner) -> None:
    if not runner.is_xnedit:
        pytest.skip(
            "widths are counted in characters, and only XNEdit's regex engine "
            "walks a UTF-8 string a character at a time. NEdit 5.7 counts the "
            f"bytes and pads these columns too wide (running {runner.version})"
        )


def test_every_row_comes_out_the_same_width_on_screen(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Counting bytes gives the accented rows fewer spaces than the plain one."""
    only_xnedit(runner)
    result = pad(runner, MIXED, tmp_path)

    widths = {row: len(row) for row in rows(result)}
    assert set(widths.values()) == {26}, (
        f"the rows came out different widths on screen: {widths}"
    )

    byte_widths = {len(row.encode()) for row in rows(result)}
    assert len(byte_widths) > 1, (
        "every row of this table is the same number of bytes, so it cannot "
        f"tell characters and bytes apart any more: {byte_widths}"
    )


def test_the_pipes_land_in_one_column_on_every_row(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """What "equal space between" means to the person reading the file."""
    only_xnedit(runner)
    result = pad(runner, MIXED, tmp_path)

    columns = [
        [index for index, character in enumerate(row) if character == "|"]
        for row in rows(result)
    ]
    assert columns == [[8, 19], [8, 19], [8, 19]], (
        f"the pipes are not in one column: {columns}"
    )


#: Long enough to cross the macro's 200-line flush twice, and not a multiple of
#: it, so the last chunk is a partial one.
LONG = 501


def test_a_table_longer_than_the_chunk_flush_comes_back_whole(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """No line lost, doubled, or run into the next at a chunk boundary."""
    source = "".join(f"NGC {number}|{number}\n" for number in range(LONG)).encode()
    name_width = max(len(f"NGC {number}") for number in range(LONG))
    value_width = max(len(str(number)) for number in range(LONG))
    expected = "".join(
        f"NGC {number}".ljust(name_width) + "|" + str(number).ljust(value_width) + "\n"
        for number in range(LONG)
    ).encode()

    result = pad(runner, source, tmp_path)

    got = result.split(b"\n")
    want = expected.split(b"\n")
    assert len(got) == len(want), (
        f"{LONG} rows went in and {len(got) - 1} came back out, so a line was "
        "lost or doubled at a chunk boundary"
    )
    for number, (line, wanted) in enumerate(zip(got, want), start=1):
        assert line == wanted, f"line {number} came back as {line!r}, not {wanted!r}"
