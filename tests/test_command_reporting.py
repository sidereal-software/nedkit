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


#: Appended to a command body to get the cursor back out. Where a command
#: leaves the cursor is part of what it reports: it is the difference between
#: being told something needs a decision and being shown the thing.
CURSOR_PROBE = 't_print("cursor=" $cursor "\\n")'


def asked(columns: str, button: int) -> str:
    """Canned answers for the ``string_dialog()`` stub. See ``nedkit.runner``."""
    return (
        f'$ned_string_dialog_answer = "{columns}"\n'
        f"$ned_string_dialog_button = {button}\n"
    )


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


FOLD = "fold-letters-to-ascii"


def test_fold_letters_is_quiet_when_there_is_nothing_to_do(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(body(FOLD), b"NGC 4472 z=0.003326\n", tmp_path)
    assert run.ok, run.describe()
    assert "nothing to change" in run.messages
    assert run.dialogs == []


def test_fold_letters_names_each_accent_it_folded(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(body(FOLD), "Balázs and Löwe\n".encode(), tmp_path)
    assert run.ok, run.describe()
    assert "á -> a" in run.messages
    assert "ö -> o" in run.messages


def test_fold_letters_does_not_put_an_accent_in_front_of_anyone(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The dialog is for the readings that collide, and an accent has none.

    Dropping an accent is still data loss, and it goes in the terminal summary
    for that reason. It does not stop the person running the command, because
    there is nothing for them to decide.
    """
    run = runner.run_on_bytes(body(FOLD), "Balázs and Löwe\n".encode(), tmp_path)
    assert run.ok, run.describe()
    assert run.dialogs == []


def test_fold_letters_gives_the_line_and_column_of_each_greek_letter(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Lines count from 1 and columns from 0, as on the statistics line.

    Both numbers come from XNEdit's own arithmetic, by parking the cursor on
    the letter and reading ``$line`` and ``$column``, so this pins the offset
    the macro handed it rather than any counting of its own.
    """
    run = runner.run_on_bytes(
        body(FOLD), "NGC 4472\nT = 15000 K, α = 2.1\n".encode(), tmp_path
    )
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"
    assert "line 2, column 13    α -> a" in run.dialogs[0]


def test_fold_letters_counts_the_column_after_an_expansion_on_the_same_line(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """``ß`` becomes two characters, so everything after it has moved.

    The accented letters are folded before the Greek letters are looked for,
    which is what makes the recorded offsets offsets in the finished text.
    Scanning first would put every column on this line one place to the left.
    """
    run = runner.run_on_bytes(body(FOLD), "Weiß 24 µm α=2.1 Löwe\n".encode(), tmp_path)
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "line 1, column 9    µ -> u" in message
    assert "line 1, column 12    α -> a" in message


def test_fold_letters_counts_the_column_past_a_character_it_left_alone(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """A degree sign is two bytes and one column, and the macro counts bytes.

    ``25° α`` leaves the alpha at byte 5 of the finished line and column 4 of
    it. Getting column 4 out is what says the byte offset went to the editor
    and the character column came back.
    """
    if not runner.is_xnedit:
        pytest.skip(
            "the answer here is what $column counts, and only XNEdit's is "
            f"pinned: NEdit 5.7 predates its Unicode handling (running "
            f"{runner.version})"
        )

    run = runner.run_on_bytes(body(FOLD), "25° α end\n".encode(), tmp_path)
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"
    assert "line 1, column 4    α -> a" in run.dialogs[0]


#: The five readings more than one Greek letter folds to, and what each of them
#: could have started as. ``tests/test_character_table.py`` derives this set
#: from the table; the dialog is the only place a person ever sees it, and a
#: pair missing from it is a pair somebody will assume is still recoverable.
COLLISIONS = (
    "e epsilon, eta",
    "o omicron, omega",
    "s sigma, final sigma",
    "t tau, theta",
    "u upsilon, mu, micro sign",
)


def flattened(message: str) -> str:
    """A dialog with its runs of whitespace and its escaped newlines squashed.

    Lets a row be matched on what it says rather than on how it is laid out.
    """
    return " ".join(message.replace("\\n", " ").split())


def test_fold_letters_names_every_reading_two_greek_letters_share(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Which Greek letter was there is unrecoverable once the file is folded.

    So the dialog names every reading more than one letter produces, whether or
    not this particular file happened to hold the pair: the person reading it
    is deciding whether to go back to the original.
    """
    run = runner.run_on_bytes(body(FOLD), "θ τ σ ς\n".encode(), tmp_path)
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = flattened(run.dialogs[0])
    missing = [collision for collision in COLLISIONS if collision not in message]
    assert missing == [], f"readings the dialog does not warn about: {missing}"


def test_fold_letters_lists_twenty_greek_letters_without_saying_there_are_more(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    run = runner.run_on_bytes(body(FOLD), ("α" * 20 + "\n").encode(), tmp_path)
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "had 20 Greek letter(s)" in message
    assert "line 1, column 19    α -> a" in message
    assert "...and" not in message, "twenty is the whole list, so nothing is left"


def test_fold_letters_says_how_many_greek_letters_it_did_not_list(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The count is of every occurrence; only the positions are capped.

    A dialog of hundreds of rows is unreadable, and a count that stopped at the
    cap would understate what the command just did.
    """
    run = runner.run_on_bytes(body(FOLD), ("α" * 21 + "\n").encode(), tmp_path)
    assert run.ok, run.describe()
    assert len(run.dialogs) == 1, f"expected one dialog, got {run.dialogs}"

    message = run.dialogs[0]
    assert "had 21 Greek letter(s)" in message
    assert "...and 1 more" in message
    assert "column 20" not in message, "the twenty-first position is not listed"


def test_fold_letters_leaves_the_cursor_on_the_first_greek_letter(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The dialog says the cursor is there, so it has to be there.

    Two Greek letters, because working out each one's line and column means
    parking the cursor on it, which leaves the cursor on the last one. The
    alpha is at byte 4 of ``abc a def o`` and the omega at byte 10, so getting
    4 back is the only answer that says the macro went back for the first.
    """
    run = runner.run_on_bytes(
        body(FOLD) + "\n" + CURSOR_PROBE, "abc α def ω\n".encode(), tmp_path
    )
    assert run.ok, run.describe()
    assert "cursor=4" in run.messages, run.messages


def test_fold_letters_leaves_the_cursor_alone_when_there_is_no_greek(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Folding an accent asks for no decision, so it does not move anyone."""
    run = runner.run_on_bytes(
        with_setup(FOLD, "set_cursor_pos(6)") + "\n" + CURSOR_PROBE,
        "abcdeféghij\n".encode(),
        tmp_path,
    )
    assert run.ok, run.describe()
    assert "cursor=6" in run.messages, run.messages


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


def test_pipe_refuses_a_buffer_with_a_tab_and_says_how_to_get_rid_of_them(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """A tab is one character and however many columns, so no column arithmetic
    on the buffer means anything until the tabs are gone.

    XNEdit has no untabify of its own, so the message points at ``expand``
    through Shell > Filter Selection, which is the only route that keeps the
    columns where they are on screen.
    """
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
    assert "Shell > Filter Selection" in message


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
