"""Tests for the checker itself.

The ``replace_in_string()`` check is the one that matters, so it gets the
awkward inputs: commas inside strings, nested calls, and the comment that looks
like a call but isn't.

``check_search_type()`` is the other one with teeth. Every searching subroutine
falls back to ``"literal"``, which is the search with the Case Sensitive box
unticked, so the default is the unsafe answer and saying nothing is the same
bug as saying the wrong thing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit.checks import (
    check_formatting,
    check_library_prefix,
    check_replace_in_string_copy,
    check_search_type,
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
    body = "\n".join(
        [
            "# replace_in_string(a, b, c) in a comment",
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


#: One call to each searching subroutine, with ``%s`` where the trailing
#: arguments go. All six default to ``"literal"`` when they are not told
#: otherwise, so the same rule covers all six.
SEARCH_CALLS = {
    "search": 'search("a", 0%s)',
    "search_string": 'x = search_string(t, "a", 0%s)',
    "replace_all": 'replace_all("a", "b"%s)',
    "replace_in_selection": 'replace_in_selection("a", "b"%s)',
    "replace_in_string": 'x = replace_in_string(t, "a", "b"%s)',
    "split": 'x = split(t, ","%s)',
}

#: Trailing arguments a search can be given that are not search types. XNEdit
#: reads the trailing arguments as a set rather than by position, so one of
#: these in the slot does not make the search case sensitive: it leaves the
#: search type unsaid, and unsaid means ``"literal"``.
NOT_A_SEARCH_TYPE = ('"wrap"', '"nowrap"', '"forward"', '"backward"', '"copy"')


def searched(name: str, *trailing: str) -> list:
    """Findings for one call to ``name`` with those trailing arguments."""
    call = SEARCH_CALLS[name] % "".join(", " + argument for argument in trailing)
    return check_search_type(Path("fake.nm"), call)


def assert_one_finding(findings: list, name: str) -> None:
    """One finding, saying which call it is about and what to write instead."""
    assert len(findings) == 1, f"{name}: {findings}"
    assert findings[0].message.startswith(f"{name}()"), findings[0].message
    assert '"case"' in findings[0].message, findings[0].message


@pytest.mark.parametrize("name", sorted(SEARCH_CALLS))
def test_a_search_with_no_type_at_all_is_reported(name: str) -> None:
    assert_one_finding(searched(name), name)


@pytest.mark.parametrize("name", sorted(SEARCH_CALLS))
@pytest.mark.parametrize("search_type", ['"case"', '"regex"'])
def test_a_case_sensitive_search_is_accepted(name: str, search_type: str) -> None:
    assert searched(name, search_type) == []


@pytest.mark.parametrize("name", sorted(SEARCH_CALLS))
@pytest.mark.parametrize("search_type", ['"literal"', '"word"', '"regexNoCase"'])
def test_a_search_type_that_folds_case_is_reported(name: str, search_type: str) -> None:
    findings = searched(name, search_type)
    assert len(findings) == 1, f"{name}: {findings}"
    assert search_type in findings[0].message


@pytest.mark.parametrize("trailing", NOT_A_SEARCH_TYPE)
def test_a_trailing_argument_that_is_not_a_search_type_is_still_no_search_type(
    trailing: str,
) -> None:
    """``search_string(s, pat, 0, "backward")`` says nothing about case.

    XNEdit does not read the trailing arguments by position: it takes whichever
    of them it recognises as a direction, a wrap setting or a search type, in
    any order. So a call whose only trailing argument is a direction has left
    the search type unsaid and is folding case, and a checker that looked at a
    fixed argument index would see ``"backward"``, decide it was not on the
    case-folding list, and pass it.
    """
    assert_one_finding(searched("search_string", trailing), "search_string")


def test_a_search_type_behind_another_trailing_argument_is_still_found() -> None:
    """The arguments are a set, so the search type does not have to come first."""
    assert searched("search_string", '"backward"', '"case"') == []


def test_replace_in_string_needs_a_search_type_as_well_as_its_copy() -> None:
    """``"copy"`` in the fourth slot is the mistake worth its own case.

    It looks like the call is fully specified, and it satisfies the separate
    check that ``replace_in_string()`` was given a fifth argument at all, while
    leaving the search folding case.
    """
    assert_one_finding(searched("replace_in_string", '"copy"'), "replace_in_string")
    assert searched("replace_in_string", '"case"', '"copy"') == []


def test_a_search_type_held_in_a_variable_is_left_alone() -> None:
    """A known blind spot, and the safe direction to be blind in.

    The checker only sees string literals, and a variable there could hold
    ``"case"`` as easily as ``"literal"``. Reporting it would put a finding on
    a macro doing nothing wrong, and a check that cries wolf gets skimmed.
    """
    assert (
        check_search_type(Path("fake.nm"), 'x = search_string(t, "a", 0, mode)') == []
    )


def test_a_folding_type_next_to_a_variable_is_still_reported() -> None:
    """Blind to what it cannot see, not blind to what it can."""
    findings = check_search_type(
        Path("fake.nm"), 'x = search_string(t, "a", 0, mode, "literal")'
    )
    assert len(findings) == 1, findings
    assert '"literal"' in findings[0].message


def test_a_search_in_a_comment_or_a_string_is_not_a_call() -> None:
    text = "\n".join(
        [
            '# search_string(t, "a", 0)',
            'msg = "search_string(t, \\"a\\", 0)"',
            'x = search_string(t, "a", 0, "case")',
        ]
    )
    assert check_search_type(Path("fake.nm"), text) == []


def test_every_search_in_a_file_is_reported_not_just_the_first() -> None:
    text = 'x = search_string(t, "a", 0)\ny = search_string(t, "b", 0, "word")\n'
    assert [finding.line for finding in check_search_type(Path("fake.nm"), text)] == [
        1,
        2,
    ]


def test_the_finding_points_at_the_line_the_search_is_on() -> None:
    """A command's body sits under its header, so the offset is what makes the
    reported line one you can jump to."""
    text = 'a = 1\nb = 2\nx = search_string(t, "a", 0)'
    findings = check_search_type(Path("fake.nm"), text, 15)
    assert [finding.line for finding in findings] == [17]


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
