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
