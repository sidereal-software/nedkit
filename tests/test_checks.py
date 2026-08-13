"""Tests for the checker itself.

The ``replace_in_string()`` check is the one that matters, so it gets the
awkward inputs: commas inside strings, nested calls, and the comment that looks
like a call but isn't.
"""

from __future__ import annotations

from pathlib import Path

from nedkit.checks import (
    check_formatting,
    check_library_prefix,
    check_replace_in_string_copy,
    find_calls,
    find_definitions,
    split_args,
)
from nedkit.macro import MacroFile, parse, slug


def _macro(body: str) -> MacroFile:
    return MacroFile(
        path=Path("fake.nm"),
        title="Fake",
        prose="",
        fields={},
        body=body,
        body_offset=1,
    )


def test_split_args_ignores_commas_in_strings() -> None:
    assert split_args('a, "b, c", d') == ["a", '"b, c"', "d"]


def test_split_args_ignores_commas_in_nested_calls() -> None:
    assert split_args("f(1, 2), g[3, 4], h") == ["f(1, 2)", "g[3, 4]", "h"]


def test_split_args_handles_escaped_quotes() -> None:
    assert split_args(r'"a\"b, c", d') == [r'"a\"b, c"', "d"]


def test_split_args_of_nothing() -> None:
    assert split_args("") == []
    assert split_args("   ") == []


def test_find_calls_skips_comments_and_strings() -> None:
    body = '\n'.join(
        [
            '# replace_in_string(a, b, c) in a comment',
            'msg = "replace_in_string(a, b, c)"',
            'x = replace_in_string(t, "p", "", "regex", "copy")',
        ]
    )
    calls = find_calls(body, "replace_in_string")
    assert len(calls) == 1
    assert calls[0].line == 3
    assert len(calls[0].args) == 5


def test_missing_copy_argument_is_reported() -> None:
    findings = check_replace_in_string_copy(
        _macro('out = replace_in_string(text, "[ \\t]+$", "", "regex")')
    )
    assert len(findings) == 1
    assert "fifth" in findings[0].message


def test_copy_argument_present_is_accepted() -> None:
    findings = check_replace_in_string_copy(
        _macro('out = replace_in_string(text, "[ \\t]+$", "", "regex", "copy")')
    )
    assert findings == []


def test_missing_copy_is_reported_at_the_right_line() -> None:
    macro = MacroFile(
        path=Path("fake.nm"),
        title="Fake",
        prose="",
        fields={},
        body="a = 1\nb = 2\nc = replace_in_string(a, b, c)",
        body_offset=15,
    )
    assert check_replace_in_string_copy(macro)[0].line == 17


def test_find_definitions() -> None:
    assert find_definitions("define ned_trim {\n}\ndefine helper {\n}") == [
        (1, "ned_trim"),
        (3, "helper"),
    ]


def test_library_prefix_is_enforced() -> None:
    findings = check_library_prefix(Path("lib.nm"), "define helper {\n}\n")
    assert len(findings) == 1
    assert "ned_helper" in findings[0].message


def test_formatting_catches_trailing_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "x.nm"
    path.write_bytes(b"a = 1   \nb = 2\n")
    assert [f.message for f in check_formatting(path)] == ["trailing whitespace"]


def test_formatting_catches_crlf_and_missing_newline(tmp_path: Path) -> None:
    path = tmp_path / "x.nm"
    path.write_bytes(b"a = 1\r\nb = 2")
    messages = [f.message for f in check_formatting(path)]
    assert any("carriage return" in message for message in messages)
    assert any("no newline at end" in message for message in messages)


def test_formatting_accepts_a_clean_file(tmp_path: Path) -> None:
    path = tmp_path / "x.nm"
    path.write_bytes(b"a = 1\n    b = 2\n")
    assert check_formatting(path) == []


def test_slug() -> None:
    assert slug("Trim Trailing Blanks") == "trim-trailing-blanks"
    assert slug("Fill Sel. w/Char") == "fill-sel-wchar"


def test_parse_reads_header_and_body(tmp_path: Path) -> None:
    path = tmp_path / "example.nm"
    path.write_text(
        "# Example\n"
        "#\n"
        "#   Menu Entry:         NED>Example\n"
        "#   Accelerator:        (none)\n"
        "#   Mnemonic:           (none)\n"
        "#   Requires Selection: yes\n"
        "\n"
        "x = 1\n",
        encoding="utf-8",
    )
    macro = parse(path)
    assert macro.title == "Example"
    assert macro.menu_entry == "NED>Example"
    assert macro.command_name == "Example"
    assert macro.requires_selection is True
    assert macro.fields["Accelerator"] == ""
    assert macro.body == "x = 1"
    assert macro.body_offset == 8


def test_parse_survives_a_file_with_no_body(tmp_path: Path) -> None:
    path = tmp_path / "empty.nm"
    path.write_text("# nothing here\n", encoding="utf-8")
    macro = parse(path)
    assert macro.body == ""
