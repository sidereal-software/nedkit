"""Exercise macros/lib/text.nm through XNEdit.

Subroutines don't touch a buffer, so these assert on ``t_print()`` output
instead of on a file. Everything in ``macros/lib/`` is loaded into the test
XNEdit's ``autoload.nm``, which is how it reaches a real installation too.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner

pytestmark = pytest.mark.xnedit


def call(runner: XNEditRunner, expression: str, workdir: Path) -> str:
    """Evaluate a macro expression and return it, delimited so spaces show."""
    return runner.evaluate(f't_print("[" {expression} "]\\n")', workdir)


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        ('"   padded   "', "[padded]"),
        ('"\\tleading tab"', "[leading tab]"),
        ('"trailing tab\\t"', "[trailing tab]"),
        ('"already clean"', "[already clean]"),
        ('""', "[]"),
        ('"     "', "[]"),
        # The reason "copy" matters: a string with nothing to strip must come
        # back whole rather than empty.
        ('"NGC4151"', "[NGC4151]"),
    ],
)
def test_ned_trim(
    argument: str, expected: str, lib_runner: XNEditRunner, tmp_path: Path
) -> None:
    assert call(lib_runner, f"ned_trim({argument})", tmp_path) == expected


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        (1, "[NGC]"),
        (2, "[4151]"),
        (3, "[Sy1.5]"),
        (4, "[]"),
        (0, "[]"),
        (-1, "[]"),
    ],
)
def test_ned_field(
    field: int, expected: str, lib_runner: XNEditRunner, tmp_path: Path
) -> None:
    row = '"NGC  4151   Sy1.5"'
    assert call(lib_runner, f"ned_field({row}, {field})", tmp_path) == expected


def test_ned_field_handles_tabs_and_padding(
    lib_runner: XNEditRunner, tmp_path: Path
) -> None:
    row = '"  NGC\\t4151  \\t Sy1.5  "'
    assert call(lib_runner, f"ned_field({row}, 2)", tmp_path) == "[4151]"


def test_ned_trim_is_multi_line_by_design(
    lib_runner: XNEditRunner, tmp_path: Path
) -> None:
    """^ and $ anchor to line boundaries, so every line gets trimmed.

    text.nm documents this; pinning it here means a future rewrite that
    "fixes" it has to be a deliberate decision.
    """
    result = lib_runner.evaluate(
        't_print("[" ned_trim("  a  \\n  b  ") "]\\n")', tmp_path
    )
    assert result == "[a\nb]"


def test_ned_current_line(lib_runner: XNEditRunner, tmp_path: Path) -> None:
    macro = (
        'replace_range(0, $text_length, "first line\\nsecond line\\nthird line")\n'
        "set_cursor_pos(15)\n"
        't_print("[" ned_current_line() "]\\n")'
    )
    run = lib_runner.run_on_bytes(macro, b"", tmp_path, name="lines.txt", save=False)
    assert run.ok, run.describe()
    assert "[second line]" in run.stdout


def test_ned_current_line_at_the_start_of_the_buffer(
    lib_runner: XNEditRunner, tmp_path: Path
) -> None:
    macro = (
        'replace_range(0, $text_length, "only line\\nnext")\n'
        "set_cursor_pos(0)\n"
        't_print("[" ned_current_line() "]\\n")'
    )
    run = lib_runner.run_on_bytes(macro, b"", tmp_path, name="lines.txt", save=False)
    assert run.ok, run.describe()
    assert "[only line]" in run.stdout
