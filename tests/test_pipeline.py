"""The commands run together.

``tests/fixtures/`` exercises one command at a time on input written to isolate
a single behaviour. This runs them in sequence, which is where they interact.

The sequence:

    pipe the columns, then Normalize Characters, then Trim Trailing Blanks.

Piping puts the delimiters in, Normalize fixes the characters, and Trim tidies
the ends. Trim goes last because it is the only one that cannot move a
boundary: it removes spaces from the end of a line and nothing else.

Nothing here pads the fields to a common width, so a finished file comes out
pipe delimited and ragged rather than pipe delimited and square.

Inline bytes throughout. ``samples/`` holds one real job, and that job arrives
tab separated, which none of these commands will touch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

#: Pipe, format, tidy. See the module docstring.
PIPELINE = ["pipe-at-columns", "normalize-characters", "trim-trailing-blanks"]

#: The columns of the fixed-width paste below that are blank on every row.
COLUMNS = '$ned_string_dialog_answer = "10, 23"\n$ned_string_dialog_button = 1\n'

#: A paste with no delimiter in it and an en dash standing in for a minus sign.
PASTE = (
    "NGC 4472   12 29 46.7   –0.003326\n"
    "IC 3583    12 36 44.0   –0.001155\n"
    "NGC 4486   12 30 49.4   –0.004283\n"
).encode()

pytestmark = pytest.mark.xnedit


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
    """Where the pipes sit on each row, so a shift shows up as a changed list."""
    return [
        [index for index, byte in enumerate(line) if byte == ord("|")]
        for line in data.split(b"\n")
        if b"|" in line
    ]


def test_a_fixed_width_paste_becomes_a_pipe_delimited_table(
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


def test_normalize_does_not_move_the_pipes(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """An en dash is one character before and after, so no boundary shifts.

    This is the property that lets the piping happen first. It holds for the
    replacements a NED file actually needs, and not for every replacement in
    the table: a ligature becomes two letters and an ellipsis becomes three
    dots, and either one moves everything to its right. Fix those by hand and
    look at the file again before choosing columns.
    """
    piped = apply(
        runner, ["pipe-at-columns"], PASTE, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )
    normalized = apply(runner, ["normalize-characters"], piped, tmp_path)

    assert pipe_columns(normalized) == pipe_columns(piped)


def test_trimming_last_moves_no_boundary(runner: XNEditRunner, tmp_path: Path) -> None:
    """Trim Trailing Blanks only ever takes from the end, so the pipes stay put."""
    ragged = apply(
        runner,
        ["pipe-at-columns", "normalize-characters"],
        PASTE,
        tmp_path,
        setup={"pipe-at-columns": COLUMNS},
    )
    trimmed = apply(runner, ["trim-trailing-blanks"], ragged, tmp_path)

    assert pipe_columns(trimmed) == pipe_columns(ragged)


def test_running_the_sequence_again_changes_nothing(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Every command in it is re-runnable, so the sequence is too.

    Overwrite is the mode that makes this true. It writes a "|" over a space
    and nothing shifts, so a second pass finds the pipe already there and
    leaves it. Insert would add a second set.
    """
    settled = apply(
        runner, PIPELINE, PASTE, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )
    again = apply(
        runner, PIPELINE, settled, tmp_path, setup={"pipe-at-columns": COLUMNS}
    )

    assert again == settled
