"""What the commands tell the person running them.

The fixtures in ``test_commands.py`` settle what lands in the buffer. This
covers the other half: the ``t_print()`` summary and, for the cases that need a
human to look at something, the dialog.

A real dialog would block forever with no one to click OK, so the harness
shadows ``dialog()`` with a subroutine that prints instead. See
``nedkit.runner.DIALOG_STUB``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

pytestmark = pytest.mark.xnedit


def body(name: str) -> str:
    return parse(COMMANDS / f"{name}.nm").body


def with_setup(name: str, setup: str) -> str:
    """A command body behind the macro a fixture's ``setup.nm`` would run first.

    The piping commands read the cursor and, in one case, an answer to a
    prompt, so neither says anything worth reading without one.
    """
    return setup.rstrip() + "\n" + body(name)


def asked(columns: str, button: int) -> str:
    """Canned answers for the ``string_dialog()`` stub. See ``nedkit.runner``."""
    return (
        f'$ned_string_dialog_answer = "{columns}"\n'
        f"$ned_string_dialog_button = {button}\n"
    )


def test_align_columns_reports_row_and_column_counts(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        body("align-columns"),
        b"NGC 4472\tz=0.003326\nIC 3583\tz=0.001155\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "2 row(s), 2 column(s)" in run.messages
    assert run.dialogs == []


def test_align_columns_does_not_count_header_lines_as_rows(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        body("align-columns"),
        b"##refcode 2024ApJ...900...1X\n\nNGC 4472\tz=0.003326\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "1 row(s)" in run.messages


def test_align_columns_says_so_when_there_is_nothing_to_align(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(body("align-columns"), b"##refcode only\n", tmp_path)
    assert run.ok, run.describe()
    assert "no data rows" in run.messages


def test_align_columns_reports_ragged_rows(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """A short row means a value went missing upstream, so it must not pass quietly."""
    run = runner.run_on_bytes(
        body("align-columns"),
        b"NGC 4472\tz=0.003326\tSy2\nNGC 4486\tz=0.004283\nIC 3583\tz=0.001155\tHII\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "1 row(s) whose field count differs" in message
    assert "on line 2" in message


def test_normalize_characters_is_quiet_when_there_is_nothing_to_do(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        body("normalize-characters"), b"NGC 4472 z=0.003326\n", tmp_path
    )
    assert run.ok, run.describe()
    assert "nothing to change" in run.messages
    assert run.dialogs == []


def test_normalize_characters_names_what_it_changed(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        body("normalize-characters"),
        "NGC 4472 – 4486 ‘Virgo’\n".encode("utf-8"),
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "U+2013 EN DASH" in run.messages
    assert "U+2018 LEFT SINGLE QUOTATION MARK" in run.messages


def test_normalize_characters_reports_what_it_left_alone(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Characters with no ASCII spelling are kept, counted, and pointed at."""
    run = runner.run_on_bytes(
        body("normalize-characters"),
        "T = 15000 K, α = 2.1, α again\n".encode("utf-8"),
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "1 kind(s) of non-ASCII character left, 2 in all" in message
    assert "2x" in message


def test_normalize_characters_reports_nothing_left_when_all_is_mapped(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        body("normalize-characters"), "NGC 4472 – 4486\n".encode("utf-8"), tmp_path
    )
    assert run.ok, run.describe()
    assert run.dialogs == []


AT_COLUMN_10 = "set_cursor_pos(10)"

TWO_ROWS = b"NGC 4472   12:29:46.7\nIC 3583    12:36:44.0\n"


def test_pipe_at_cursor_column_reports_the_pipes_and_the_rows(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10), TWO_ROWS, tmp_path
    )
    assert run.ok, run.describe()
    assert "2 pipe(s) into 2 row(s)" in run.messages
    assert run.dialogs == []


def test_pipe_at_cursor_column_does_not_count_header_lines_as_rows(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10),
        b"##refcode 2024ApJ...900...1X\n\nNGC 4472   12:29:46.7\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "1 pipe(s) into 1 row(s)" in run.messages


def test_pipe_at_cursor_column_says_so_when_there_is_nothing_to_pipe(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10), b"##refcode only\n", tmp_path
    )
    assert run.ok, run.describe()
    assert "no data rows" in run.messages


def test_pipe_at_cursor_column_refuses_column_zero_and_says_why(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Right-clicking does not move the caret, so landing on column 0 is easy."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", "set_cursor_pos(0)"), TWO_ROWS, tmp_path
    )
    assert run.ok, run.describe()
    assert "nothing changed" in run.messages
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"
    assert "column 0" in run.dialogs[0]


def test_pipe_refuses_a_buffer_with_a_tab_and_points_at_align_columns(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """A tab is one character and however many columns, so no column arithmetic
    on the buffer means anything until Align Columns has taken the tabs out."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10),
        b"NGC 4472\t12:29:46.7\nIC 3583\t12:36:44.0\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "nothing changed" in run.messages
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "has a tab in it" in message
    assert "Run Align Columns first" in message


def test_pipe_reports_the_rows_it_could_not_overwrite(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """A column blank on most rows can land inside a name on one, and that row
    is the only sign the column is a place or two off."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10),
        b"NGC 4472   12:29:46.7\nESO 137-006 12:36:44.0\nNGC 4486   12:30:49.4\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "1 row(s) holding something other than a space" in message
    assert "The first is on line 2" in message


def test_pipe_reports_the_rows_that_end_before_the_column(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Nothing is padded out to reach the column, so a short row is a value
    that went missing upstream and has to be said out loud."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10),
        b"NGC 4472   12:29:46.7\nIC 3583\nNGC 4486   12:30:49.4\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "1 row(s) that end before" in message
    assert "The first is on line 2" in message


def test_pipe_puts_both_kinds_of_skipped_row_in_one_dialog(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """One dialog, however many things went wrong. Two would mean clicking OK
    twice for one run of one command."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-cursor-column", AT_COLUMN_10),
        b"NGC 4472   12:29:46.7\nESO 137-006 12:36:44.0\nIC 3583\n",
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "1 row(s) holding something other than a space" in message
    assert "1 row(s) that end before" in message


def test_pipe_at_columns_asks_once_and_names_the_column_the_cursor_is_in(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """string_dialog() takes no default text, so the prompt is the only place
    the current column can be put, and reading one off it is how a user answers
    without counting."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-columns", "set_cursor_pos(12)\n" + asked("10", 1)),
        TWO_ROWS,
        tmp_path,
    )
    assert run.ok, run.describe()
    assert len(run.prompts) == 1, f"expected one prompt, got {run.prompts}"

    prompt = run.prompts[0]
    assert "the cursor is in column 12 right now" in prompt
    assert "They count from 0" in prompt
    assert run.dialogs == []


def test_pipe_at_columns_says_nothing_when_the_answer_names_no_columns(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """An answer with no numbers in it is a change of mind, not a mistake."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-columns", asked("", 1)), TWO_ROWS, tmp_path
    )
    assert run.ok, run.describe()
    assert "nothing changed" in run.messages
    assert run.dialogs == []


def test_pipe_at_columns_names_the_word_it_could_not_read_as_a_column(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(
        with_setup("pipe-at-columns", asked("10, twelve", 1)), TWO_ROWS, tmp_path
    )
    assert run.ok, run.describe()
    assert "nothing changed" in run.messages
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"
    assert '"twelve" is not a column number' in run.dialogs[0]


def test_pipe_at_columns_refuses_column_zero_without_piping_the_rest(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Column 10 is accepted before column 0 is read, so this also pins that
    the refusal throws away the columns already collected."""
    run = runner.run_on_bytes(
        with_setup("pipe-at-columns", asked("10, 0", 1)), TWO_ROWS, tmp_path
    )
    assert run.ok, run.describe()
    assert "nothing changed" in run.messages
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"
    assert "Column 0 is not a place a pipe can go" in run.dialogs[0]
