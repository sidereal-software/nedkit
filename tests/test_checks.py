"""Tests for the checker itself.

The ``replace_in_string()`` check is the one that matters, so it gets the
awkward inputs: commas inside strings, nested calls, and the comment that looks
like a call but isn't.

``check_search_type()`` is the other one with teeth. Every searching subroutine
falls back to ``"literal"``, which is the search with the Case Sensitive box
unticked, so the default is the unsafe answer and saying nothing is the same
bug as saying the wrong thing.

``check_read_only_guard()`` is the third, and the cases below are the shapes
the bug came in: a write with no lock test at all, and a lock test that names
``$locked`` rather than ``$read_only`` and so passes a file with no write
permission straight through.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit.checks import (
    BUFFER_WRITING_FUNCTIONS,
    check_formatting,
    check_header_separated,
    check_library_prefix,
    check_read_only_guard,
    check_replace_in_string_copy,
    check_resource_fields,
    check_search_type,
    find_calls,
    find_definitions,
    split_args,
)
from nedkit.macro import MacroFile, command_files, parse, slug

REPO_ROOT = Path(__file__).resolve().parents[1]


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


#: One call to each buffer-writing subroutine, spelled the way a command would
#: write it. Every one of them refuses a locked buffer by ringing the bell and
#: returning, so every one of them needs the same guard above it.
BUFFER_WRITES = {
    "replace_range": "replace_range(0, $text_length, out)",
    "replace_selection": "replace_selection(out)",
    "replace_all": 'replace_all("a", "b", "case")',
    "replace_in_selection": 'replace_in_selection("a", "b", "case")',
    "insert_string": "insert_string(out)",
}

GUARD = 'if ($read_only == 1) {\n    dialog("locked")\n    return\n}\n'


def test_every_buffer_write_has_a_case() -> None:
    """Adding a function to the constant without a case here proves nothing."""
    assert sorted(BUFFER_WRITES) == sorted(BUFFER_WRITING_FUNCTIONS)


@pytest.mark.parametrize("name", sorted(BUFFER_WRITES))
def test_a_write_under_a_read_only_guard_is_accepted(name: str) -> None:
    assert check_read_only_guard(_macro(GUARD + BUFFER_WRITES[name])) == []


@pytest.mark.parametrize("name", sorted(BUFFER_WRITES))
def test_a_write_with_no_guard_at_all_is_reported(name: str) -> None:
    findings = check_read_only_guard(_macro(BUFFER_WRITES[name]))
    assert len(findings) == 1, findings
    assert findings[0].message.startswith(f"{name}()"), findings[0].message
    assert "$read_only" in findings[0].message


@pytest.mark.parametrize("name", sorted(BUFFER_WRITES))
def test_a_guard_on_locked_alone_is_reported(name: str) -> None:
    """``$locked`` is ``IS_USER_LOCKED`` and the writes refuse on
    ``IS_ANY_LOCKED``, so a file with no write permission reads ``$locked`` 0,
    walks past the guard, and loses the write anyway. The message has to say
    which variable to write instead, because the command looks guarded."""
    body = "if ($locked == 1) {\n    return\n}\n" + BUFFER_WRITES[name]
    findings = check_read_only_guard(_macro(body))
    assert len(findings) == 1, findings
    assert "$locked" in findings[0].message
    assert "$read_only" in findings[0].message


def test_a_command_that_never_writes_needs_no_guard() -> None:
    """Reporting a read-only command would be a finding on a file doing nothing
    wrong, and a check that cries wolf gets skimmed."""
    body = 'if (search("a", 0, "case") == -1) {\n    dialog("nothing here")\n}'
    assert check_read_only_guard(_macro(body)) == []


def test_read_only_in_a_comment_does_not_count_as_a_guard() -> None:
    """The comment is how the six commands explain the guard, so a file that
    kept the explanation and lost the guard is exactly the shape to catch."""
    body = "# $read_only is tested above\nreplace_range(0, $text_length, out)"
    findings = check_read_only_guard(_macro(body))
    assert len(findings) == 1, findings
    assert findings[0].line == 2


def test_read_only_in_a_string_does_not_count_as_a_guard() -> None:
    body = 'dialog("this one ignores $read_only")\nreplace_range(0, $text_length, out)'
    assert len(check_read_only_guard(_macro(body))) == 1


def test_an_unguarded_command_is_reported_once_at_its_first_write() -> None:
    """One missing guard is one problem however many writes sit under it, and
    the first write is the line to jump to."""
    body = "replace_selection(a)\nreplace_range(0, $text_length, b)"
    findings = check_read_only_guard(_macro(body))
    assert len(findings) == 1, findings
    assert findings[0].line == 1
    assert findings[0].message.startswith("replace_selection()")


def test_the_guard_finding_points_at_a_line_in_the_file() -> None:
    """A command's body sits under its header, so the offset is what makes the
    reported line one you can jump to."""
    macro = MacroFile(
        path=Path("fake.nm"),
        title="Fake",
        prose="",
        fields={},
        body="a = 1\nb = 2\nreplace_range(0, $text_length, a)",
        body_offset=15,
    )
    assert check_read_only_guard(macro)[0].line == 17


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


#: A header with everything the install dialog asks for, ready to have a body
#: written under it. The blank line is the caller's to add or leave out.
HEADER = (
    "# Example\n"
    "#\n"
    "#   Menu Entry:         NED>Example\n"
    "#   Accelerator:        (none)\n"
    "#   Mnemonic:           (none)\n"
    "#   Requires Selection: yes\n"
)


def written(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "example.nm"
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_reads_header_and_body(tmp_path: Path) -> None:
    macro = parse(written(tmp_path, HEADER + "\nx = 1\n"))
    assert macro.title == "Example"
    assert macro.menu_entry == "NED>Example"
    assert macro.command_name == "Example"
    assert macro.requires_selection is True
    assert macro.fields["Accelerator"] == ""
    assert macro.body == "x = 1"
    assert macro.body_offset == 8
    assert macro.header_lines == 6


def test_parse_keeps_a_comment_the_body_opens_with(tmp_path: Path) -> None:
    """The divider the two piping commands open with is body, not header.

    It sits under the header rather than in it, and reading it as header drops
    it from ``macro.body``, which is the text ``tools/gen_docs.py`` publishes as
    the block to paste in. The published body would then be missing a line the
    file has.
    """
    macro = parse(written(tmp_path, HEADER + "\n# --- prologue ---\n\nx = 1\n"))
    assert macro.body == "# --- prologue ---\n\nx = 1"
    assert macro.body_offset == 8
    assert macro.prose == ""


def test_parse_counts_from_the_first_line_of_the_body(tmp_path: Path) -> None:
    """``body_offset`` is what turns a line in the body into a line in the file,
    so a body opening with a comment has to count from that comment."""
    macro = parse(written(tmp_path, HEADER + "\n# a comment\nx = 1\n"))
    lines = macro.path.read_text(encoding="utf-8").split("\n")
    assert lines[macro.body_offset - 1] == macro.body.split("\n")[0]


def test_parse_survives_a_file_with_no_body(tmp_path: Path) -> None:
    path = tmp_path / "empty.nm"
    path.write_text("# nothing here\n", encoding="utf-8")
    macro = parse(path)
    assert macro.body == ""


def test_a_blank_line_between_header_and_body_is_accepted(tmp_path: Path) -> None:
    assert check_header_separated(parse(written(tmp_path, HEADER + "\nx = 1\n"))) == []


def test_a_body_touching_the_header_is_reported(tmp_path: Path) -> None:
    """Nothing but the blank line says where the header stops.

    Without it the next line is header whatever it holds, so a comment there
    goes missing from the body and from the docs, and the file that lost it
    looks fine.
    """
    findings = check_header_separated(parse(written(tmp_path, HEADER + "x = 1\n")))
    assert len(findings) == 1, findings
    assert findings[0].line == 7
    assert "blank line" in findings[0].message


def test_a_file_that_is_all_body_is_accepted(tmp_path: Path) -> None:
    """A library file has no header, so there is nothing to separate."""
    assert check_header_separated(parse(written(tmp_path, "x = 1\n"))) == []


def test_a_file_that_is_all_header_is_left_to_the_header_check(tmp_path: Path) -> None:
    """``check_header()`` already says a command has no body. Saying it twice,
    in two voices, buries the one finding that names the real problem."""
    assert check_header_separated(parse(written(tmp_path, HEADER))) == []


def test_a_colon_in_a_resource_field_is_reported(tmp_path: Path) -> None:
    """It shifts every field after it along, and one bad entry fails the whole
    ``docs/nedkit-macros.rc`` rather than only its own command."""
    header = HEADER.replace("NED>Example", "NED>RA: to NED Form")
    findings = check_resource_fields(parse(written(tmp_path, header + "\nx = 1\n")))
    assert len(findings) == 1, findings
    assert "'Menu Entry' cannot contain a colon" in findings[0].message


def test_a_multi_letter_mnemonic_is_reported(tmp_path: Path) -> None:
    header = HEADER.replace("Mnemonic:           (none)", "Mnemonic:           Ex")
    findings = check_resource_fields(parse(written(tmp_path, header + "\nx = 1\n")))
    assert len(findings) == 1, findings
    assert "one letter or none" in findings[0].message


def test_the_shipped_headers_have_nothing_wrong_with_their_fields() -> None:
    for path in command_files(REPO_ROOT):
        assert check_resource_fields(parse(path)) == [], path.name
