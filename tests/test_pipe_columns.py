"""Running the piping commands a second time.

Both commands are meant to be run once per boundary, so what a second run does
is the thing a user hits first and the thing the header prose promises. Three
of the four combinations settle to a fixed point, and one deliberately does
not.

This module is the only place either piping command's re-run behaviour is
tested. **``test_command_is_idempotent`` in ``test_commands.py`` is vacuous for
both of them**, and reading its two green ticks as coverage would be a mistake.
It runs a command body against settled fixture output with no ``setup.nm``,
which leaves each command in a state where it cannot pipe anything at all:

- ``Pipe at Columns`` gets the harness's default empty ``string_dialog()``
  answer, parses no columns out of it, and stops at the ``ncols == 0`` guard,
  exactly as the ``blank-answer-does-nothing`` fixture pins.
- ``Pipe at Cursor Column`` reads ``$column``, which is 0 on a freshly opened
  buffer, and refuses column 0.

Both are no-ops whatever the column arithmetic does, so running either one
twice there proves nothing. Everything below sets up a run that pipes for real
and then repeats it.

``test_command_does_not_corrupt_a_non_utf8_file`` is empty for the same two
reasons, so the byte-survival check is repeated here with an answer that makes
the command actually try to write.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

#: Three rows of a fixed-width paste. Column 10 and column 23 are blank on
#: every one of them, which is the case both modes are built for.
TABLE = (
    b"NGC 4472   12:29:46.7   0.003326\n"
    b"IC 3583    12:36:44.0   0.001155\n"
    b"NGC 4486   12:30:49.4   0.004283\n"
)

OVERWRITE = 1
INSERT = 2

pytestmark = pytest.mark.xnedit


def asked(columns: str, button: int) -> str:
    """The canned answer a fixture's ``setup.nm`` would carry.

    See ``nedkit.runner.PROMPT_STUB`` for the globals these feed.
    """
    return (
        f'$ned_string_dialog_answer = "{columns}"\n'
        f"$ned_string_dialog_button = {button}\n"
    )


def run(
    runner: XNEditRunner, command: str, setup: str, data: bytes, workdir: Path
) -> bytes:
    macro = setup.rstrip() + "\n" + parse(COMMANDS / f"{command}.nm").body
    result = runner.run_on_bytes(macro, data, workdir, name="table.txt")
    assert result.ok, f"{command}: {result.describe()}"
    assert result.output is not None, f"{command} left no file behind"
    return result.output


def twice(
    runner: XNEditRunner, command: str, setup: str, data: bytes, workdir: Path
) -> tuple[bytes, bytes]:
    first = run(runner, command, setup, data, workdir)
    return first, run(runner, command, setup, first, workdir)


def test_pipe_at_cursor_column_run_twice_pipes_the_column_once(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The pipe from the first run is left alone by the second."""
    first, second = twice(
        runner, "pipe-at-cursor-column", "set_cursor_pos(10)", TABLE, tmp_path
    )
    assert first != TABLE, "the first run should have piped column 10"
    assert second == first, (
        "Pipe at Cursor Column changed the buffer on a second run at the same "
        "column, so aiming twice at one boundary does not settle"
    )


def test_single_column_overwrite_run_twice_pipes_the_column_once(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    first, second = twice(
        runner, "pipe-at-columns", asked("10", OVERWRITE), TABLE, tmp_path
    )
    assert first != TABLE, "the first run should have piped column 10"
    assert second == first, "overwriting one column twice should settle"


def test_multi_column_overwrite_run_twice_pipes_each_column_once(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Overwrite leaves every row the width it was, so the columns keep meaning
    what they meant, and the second run finds a pipe already at each one."""
    first, second = twice(
        runner, "pipe-at-columns", asked("10, 23", OVERWRITE), TABLE, tmp_path
    )
    assert first.count(b"|") == 6, f"expected two pipes per row, got {first!r}"
    assert second == first, "overwriting several columns twice should settle"


def test_single_column_insert_run_twice_pipes_the_column_once(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Inserting shifts only the text to the right of the pipe, so the one
    column named still holds that pipe on the second run and is skipped."""
    first, second = twice(
        runner, "pipe-at-columns", asked("10", INSERT), TABLE, tmp_path
    )
    assert first.count(b"|") == 3, f"expected one pipe per row, got {first!r}"
    assert second == first, "inserting at one column twice should settle"


def test_multi_column_insert_run_twice_adds_a_second_set_of_pipes(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The one combination that does not settle, pinned rather than tolerated.

    Every insert pushes the rest of the line right, so after the first run the
    columns the user named no longer point at what they pointed at. The
    leftmost pipe is still found and skipped; every column after it has slid
    one place per pipe inserted to its left, so the second run puts a fresh
    pipe next to each of them.

    The header prose of Pipe at Columns says exactly this. If this test ever
    fails because the second run settled, the macro learned something new and
    both this test and that paragraph need rewriting.
    """
    first, second = twice(
        runner, "pipe-at-columns", asked("10, 23", INSERT), TABLE, tmp_path
    )
    assert first.count(b"|") == 6, f"expected two pipes per row, got {first!r}"
    assert second.count(b"|") == 9, (
        "a second multi-column insert should add one more pipe to every row, "
        f"got {second!r}"
    )


def test_pipe_at_columns_keeps_the_bytes_of_a_file_it_cannot_decode(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """NED's files are not reliably UTF-8, and a re-encoded byte is silent damage.

    XNEdit locks a buffer it cannot decode, so nothing lands here at all. What
    matters either way is that the bytes come back as they went in, which is
    the invariant ``test_command_does_not_corrupt_a_non_utf8_file`` asserts for
    the other commands and cannot reach for this one.
    """
    source = "NGC 4151   café   12:10:32\nIC 3583    plain  12:36:44\n".encode(
        "latin-1"
    )
    result = run(
        runner, "pipe-at-columns", asked("10, 23", OVERWRITE), source, tmp_path
    )
    assert b"\xe9" in result, f"the latin-1 byte did not survive: {result!r}"
