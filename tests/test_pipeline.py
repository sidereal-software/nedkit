"""The commands run together.

``tests/fixtures/`` exercises one command at a time on input written to isolate
a single behaviour. This runs them in sequence, which is where they interact.

The sequence:

    Normalize Characters, Fold Letters to ASCII, pipe the columns, Pad Columns.
    Then Trim Trailing Blanks, if the rows should not all end in the same
    place.

Two facts fix that order, and each has a pair of tests below showing what the
other order costs. A replacement that changes how many characters are on a line
moves every column to its right, so the letters get sorted out before the
boundaries are chosen. And every edit changes a width, so the padding goes
last.

Trim Trailing Blanks is the one command that cannot move a boundary, since it
only ever takes spaces off the end of a line. It is also the one that undoes
part of what Pad Columns just did, which is why it is optional and why it comes
after rather than before.

Inline bytes throughout. ``samples/`` holds one real job, and that job arrives
tab separated, which none of these commands will touch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

#: Fix the characters, put the boundaries in, square the file up. See the
#: module docstring. Trim Trailing Blanks is deliberately not in it: it is
#: optional, it runs after all of these, and what it trades away is pinned on
#: its own further down.
PIPELINE = [
    "normalize-characters",
    "fold-letters-to-ascii",
    "pipe-at-columns",
    "pad-columns",
]

#: The commands in the sequence that take no aim. Re-runnable on anything,
#: which the piping is not: its column numbers describe the file it was pointed
#: at, and padding moves every one of them.
CLEANUP = ["normalize-characters", "fold-letters-to-ascii", "pad-columns"]

#: A paste with no delimiter in it and an en dash standing in for a minus sign.
#: The middle redshift is a digit short of the others so that the last column
#: needs padding, which is what gives Trim Trailing Blanks something to take
#: back off.
PASTE = (
    "NGC 4472   12 29 46.7   –0.003326\n"
    "IC 3583    12 36 44.0   –0.00115\n"
    "NGC 4486   12 30 49.4   –0.004283\n"
).encode()

#: PASTE with the characters fixed and the boundaries in, but not yet padded.
#: Written out rather than produced by running the first three commands, so a
#: test about the last two costs two editor starts instead of five.
PIPED = (
    b"NGC 4472  |12 29 46.7  |-0.003326\n"
    b"IC 3583   |12 36 44.0  |-0.00115\n"
    b"NGC 4486  |12 30 49.4  |-0.004283\n"
)

#: Two rows of 25 characters each, with column 14 blank on both. ``ﬀ`` is one
#: character that Normalize Characters turns into two, so the first row is the
#: one that grows.
LIGATURE = "Griﬀin         12:29:46.7\nSmith          12:36:44.0\n".encode()

#: Already delimited, and holding the one letter Fold Letters to ASCII cannot
#: answer in a single character: ``ß`` becomes ``ss`` and widens the field.
SHARP_S = "Weiß|12:29:46.7\nSmith|12:36:44.0\n".encode()

pytestmark = pytest.mark.xnedit


def asked(columns: str) -> str:
    """The answer a fixture's ``setup.nm`` gives Pipe at Columns, in Overwrite.

    See ``nedkit.runner.PROMPT_STUB`` for the globals these feed.
    """
    return f'$ned_string_dialog_answer = "{columns}"\n$ned_string_dialog_button = 1\n'


#: The columns of the fixed-width paste above that are blank on every row.
COLUMNS = asked("10, 23")


def apply(
    runner: XNEditRunner,
    names: list[str],
    data: bytes,
    workdir: Path,
    setup: dict[str, str] | None = None,
) -> bytes:
    """Run each command in turn, feeding one command's output into the next.

    ``setup`` maps a command name to a macro run ahead of its body, the way a
    fixture's ``setup.nm`` does. A command that puts a question to the user
    needs one, or it gets the harness's default empty answer and no-ops. See
    ``nedkit.runner.PROMPT_STUB``.
    """
    setup = setup or {}
    for name in names:
        macro = parse(COMMANDS / f"{name}.nm").body
        if name in setup:
            macro = setup[name].rstrip() + "\n" + macro
        run = runner.run_on_bytes(macro, data, workdir, name="table.txt")
        assert run.ok, f"{name}: {run.describe()}"
        data = run.output or b""
    return data


def fields(data: bytes) -> list[int]:
    return [len(line.split(b"|")) for line in data.split(b"\n") if b"|" in line]


def pipe_columns(data: bytes) -> list[list[int]]:
    """Where the pipes sit on each row, so a shift shows up as a changed list.

    Counted in characters, because a column is what the eye and the statistics
    line count. Rows that are still holding a multi-byte character would give a
    different set of numbers by byte.
    """
    return [
        [index for index, character in enumerate(line) if character == "|"]
        for line in data.decode("utf-8").split("\n")
        if "|" in line
    ]


def widths(data: bytes) -> set[int]:
    """How wide each row is on screen. One entry means the file is square."""
    return {len(line) for line in data.decode("utf-8").split("\n") if "|" in line}


def test_a_fixed_width_paste_becomes_a_square_pipe_delimited_table(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The whole sequence, on a paste with neither a tab nor a pipe in it."""
    result = apply(
        runner, PIPELINE, PASTE, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )

    assert fields(result) == [3, 3, 3]
    assert b"12 29 46.7" in result, (
        f"the position should have stayed one field: {result!r}"
    )
    assert "–".encode() not in result, "the en dashes should be gone"
    assert b"|-0.003326" in result, f"en dash should be a minus sign: {result!r}"
    assert widths(result) == {29}, (
        f"every row should end in the same column: {result!r}"
    )


def test_normalizing_after_the_piping_pulls_the_pipes_out_of_line(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The wrong order, and the reason the right one is what it is.

    ``ﬀ`` is one character before Normalize Characters and two after it, so the
    row holding it grows by one and everything on it moves right, the pipe
    included. The other row does not move. There is then no single column
    number that finds the boundary on both rows, and the next one has to be
    aimed at twice.

    The rule holds on either editor; these numbers do not. ``ﬀ`` is three bytes
    and NEdit 5.7 counts bytes, so column 14 lands two characters earlier on the
    row holding it and the pipes are out of line before Normalize Characters
    even runs.
    """
    if not runner.is_xnedit:
        pytest.skip(
            "the setup needs a multi-byte character to be one column, which is "
            f"XNEdit's Unicode handling; NEdit 5.7 predates it (running "
            f"{runner.version})"
        )

    piped = apply(
        runner,
        ["pipe-at-columns"],
        LIGATURE,
        tmp_path,
        setup={"pipe-at-columns": asked("14")},
    )
    assert pipe_columns(piped) == [[14], [14]], "both pipes should start in column 14"

    normalized = apply(runner, ["normalize-characters"], piped, tmp_path)
    assert pipe_columns(normalized) == [[15], [14]], (
        "normalizing after the piping should have dragged the widened row's "
        f"pipe into column 15: {normalized!r}"
    )


def test_normalizing_before_the_piping_leaves_every_pipe_in_one_column(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The same file, the same column, the other order.

    The row that grew is still a character wider than the other one, and Pad
    Columns is what settles that. What this buys is a boundary that is a column
    number again, on the same input the test above pulls apart.
    """
    result = apply(
        runner,
        ["normalize-characters", "pipe-at-columns"],
        LIGATURE,
        tmp_path,
        setup={"pipe-at-columns": asked("14")},
    )

    assert pipe_columns(result) == [[14], [14]], (
        f"both pipes should be in column 14: {result!r}"
    )


def test_a_replacement_that_keeps_the_character_count_moves_no_pipe(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """An en dash is one character and a minus sign is one character.

    This is the replacement a NED paste actually needs, and it survives either
    order, which is how the old sequence got away with piping first. It is not
    a reason to go back to it: the table has ligatures and an ellipsis in it
    too, and the pair of tests above is what those do.
    """
    piped = apply(
        runner, ["pipe-at-columns"], PASTE, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )
    normalized = apply(runner, ["normalize-characters"], piped, tmp_path)

    assert pipe_columns(normalized) == pipe_columns(piped)


def test_folding_after_the_padding_pushes_the_row_it_widened_out_of_line(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Padding measures the columns, and the measurement is true until the next
    edit.

    ``ß`` becomes ``ss``, so the field it is in gets a character wider than the
    width Pad Columns just measured for that column, and the row it is on ends
    up a character longer than the rest.

    The rule holds on either editor; this setup does not. ``ß`` is two bytes, so
    NEdit 5.7 measures ``Weiß`` as exactly as wide as ``Smith``, pads neither,
    and there is no measurement for the fold to invalidate.
    """
    if not runner.is_xnedit:
        pytest.skip(
            "the setup needs a multi-byte character to be one column, which is "
            f"XNEdit's Unicode handling; NEdit 5.7 predates it (running "
            f"{runner.version})"
        )

    result = apply(runner, ["pad-columns", "fold-letters-to-ascii"], SHARP_S, tmp_path)

    assert pipe_columns(result) == [[6], [5]], (
        f"folding after the padding should have widened the first row: {result!r}"
    )


def test_padding_after_the_folding_leaves_the_pipes_in_one_column(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The same two commands the other way round, which is the documented order."""
    result = apply(runner, ["fold-letters-to-ascii", "pad-columns"], SHARP_S, tmp_path)

    assert pipe_columns(result) == [[5], [5]], (
        f"both pipes should be in column 5: {result!r}"
    )
    assert widths(result) == {16}, f"the rows should be the same width: {result!r}"


def test_trimming_after_the_padding_moves_no_pipe(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Trim Trailing Blanks only ever takes from the end of a line.

    It is the one command in the sequence that cannot move a boundary, which is
    what makes it safe to run after everything else. What it does take is the
    padding off the last column, so the rows stop lining up at the right.
    """
    padded = apply(runner, ["pad-columns"], PIPED, tmp_path)
    trimmed = apply(runner, ["trim-trailing-blanks"], padded, tmp_path)

    assert trimmed != padded, (
        "this table should have had a padded last column for Trim Trailing "
        f"Blanks to take off, or the test proves nothing: {padded!r}"
    )
    assert pipe_columns(trimmed) == pipe_columns(padded)
    assert widths(padded) == {29}, f"padding should square the rows up: {padded!r}"
    assert widths(trimmed) == {28, 29}, (
        f"trimming should leave the short row short: {trimmed!r}"
    )


def test_padding_again_after_a_trim_puts_the_last_column_back(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The two pull opposite ways, and Pad Columns is the one that wins.

    So the pair does not settle, and running them in a loop would flip the file
    between two states forever. That is why Trim Trailing Blanks is the last
    thing that happens rather than a step in the middle: whatever it takes off,
    the next padding puts back.
    """
    padded = apply(runner, ["pad-columns"], PIPED, tmp_path)
    trimmed = apply(runner, ["trim-trailing-blanks"], padded, tmp_path)
    repadded = apply(runner, ["pad-columns"], trimmed, tmp_path)

    assert repadded == padded, (
        f"padding a trimmed file should square it up again: {repadded!r}"
    )


def test_running_the_cleanup_commands_again_changes_nothing(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Every command that takes no aim is re-runnable, so the run of them is.

    The piping step is left out because its answer is a set of column numbers,
    and those describe the file it was pointed at. Once the padding has closed
    the columns up, the same numbers point at the middle of a value, and the
    command refuses those rows rather than moving them. Feeding it stale
    numbers here would prove only that it refuses, which
    ``tests/test_pipe_columns.py`` already covers with numbers that still mean
    something.
    """
    settled = apply(
        runner, PIPELINE, PASTE, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )
    again = apply(runner, CLEANUP, settled, tmp_path)

    assert again == settled
