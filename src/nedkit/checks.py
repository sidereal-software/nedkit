"""Static checks over the ``.nm`` files, run without XNEdit.

These catch the mistakes that are cheap to make and expensive to notice: a
header that doesn't match what the install dialog needs, a file named after
something other than its menu entry, a ``replace_in_string()`` that forgets its
``"copy"`` argument and so erases the buffer whenever the pattern happens not to
match, and a search left on the case-insensitive default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from nedkit.macro import HEADER_FIELDS, MENUS, MacroFile, slug

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

#: How many arguments each searching subroutine takes before its optional ones
#: begin. The search type is not a fixed slot: XNEdit scans every argument past
#: these for a token it recognises, so ``"case"`` can sit anywhere after them.
SEARCH_TYPE_FUNCTIONS = {
    "search": 2,
    "search_string": 3,
    "replace_all": 2,
    "replace_in_selection": 2,
    "replace_in_string": 3,
    "split": 2,
}

#: Every token ``StringToSearchType()`` accepts, from ``searchTypeStrings`` in
#: search.c. Anything else in the optional arguments is a direction, a wrap
#: setting or ``"copy"``, none of which selects a search type.
SEARCH_TYPES = frozenset(
    {"literal", "case", "regex", "word", "caseWord", "regexNoCase"}
)

#: Of those, the ones that fold case. ``"literal"`` is the search with the Case
#: Sensitive box unticked, not the byte-for-byte search its name suggests.
CASE_FOLDING_SEARCH_TYPES = frozenset({"literal", "word", "regexNoCase"})

#: A macro string literal, whole and on its own. Escapes are allowed through
#: because no search type token contains one, so an argument that has any is
#: still readable as "not a search type".
_STRING_LITERAL = re.compile(r'^"((?:[^"\\]|\\.)*)"$')


@dataclass(frozen=True)
class Finding:
    """One problem, located precisely enough to jump to."""

    path: Path
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class Call:
    """A call site found in macro source."""

    line: int
    args: list[str]


def _scan(text: str):
    """Yield ``(index, char)`` for characters that are real code.

    Skips string literals and ``#`` comments, so a ``#`` inside a string or a
    parenthesis inside a comment doesn't confuse the callers below.
    """
    in_string = False
    in_comment = False
    escaped = False

    for index, char in enumerate(text):
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "#":
            in_comment = True
            continue
        yield index, char


def _code_positions(text: str) -> set[int]:
    return {index for index, _ in _scan(text)}


def split_args(text: str) -> list[str]:
    """Split a macro argument list on its top-level commas.

    Commas inside nested calls, subscripts, or string literals don't count.
    """
    if not text.strip():
        return []

    code = _code_positions(text)
    args: list[str] = []
    depth = 0
    start = 0

    for index, char in enumerate(text):
        if index not in code:
            continue
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "," and depth == 0:
            args.append(text[start:index].strip())
            start = index + 1

    args.append(text[start:].strip())
    return args


def find_calls(text: str, name: str) -> list[Call]:
    """Every call to ``name`` in ``text``, with its arguments split out.

    Unterminated calls are skipped rather than reported; a body that doesn't
    parse fails the execution tests loudly enough on its own.
    """
    code = _code_positions(text)
    calls: list[Call] = []

    for match in re.finditer(rf"\b{re.escape(name)}\s*\(", text):
        open_paren = match.end() - 1
        if match.start() not in code or open_paren not in code:
            continue

        depth = 0
        close_paren = None
        for index in range(open_paren, len(text)):
            if index not in code:
                continue
            if text[index] in "([":
                depth += 1
            elif text[index] in ")]":
                depth -= 1
                if depth == 0:
                    close_paren = index
                    break

        if close_paren is None:
            continue

        calls.append(
            Call(
                line=text.count("\n", 0, match.start()) + 1,
                args=split_args(text[open_paren + 1 : close_paren]),
            )
        )

    return calls


def find_definitions(text: str) -> list[tuple[int, str]]:
    """Every ``define name`` in ``text``, as ``(line, name)``."""
    code = _code_positions(text)
    found = []
    for match in re.finditer(r"\bdefine\s+([A-Za-z_][A-Za-z0-9_]*)", text):
        if match.start() in code:
            found.append((text.count("\n", 0, match.start()) + 1, match.group(1)))
    return found


def check_header(macro: MacroFile) -> list[Finding]:
    """The header has to carry everything the Customize Menus dialog asks for."""
    findings = []

    for field in HEADER_FIELDS:
        if field not in macro.fields:
            findings.append(
                Finding(macro.path, 1, f"header is missing the {field!r} field")
            )

    if "Menu Entry" in macro.fields and not macro.menu_entry:
        findings.append(Finding(macro.path, 1, "'Menu Entry' is empty"))

    selection = macro.fields.get("Requires Selection", "").strip().lower()
    if "Requires Selection" in macro.fields and selection not in {
        "yes",
        "no",
        "true",
        "false",
    }:
        findings.append(
            Finding(
                macro.path,
                1,
                f"'Requires Selection' should be yes or no, not {selection!r}",
            )
        )

    if "Install In" in macro.fields:
        if not macro.menus:
            findings.append(
                Finding(
                    macro.path,
                    1,
                    "'Install In' is empty; name at least one of "
                    + ", ".join(repr(menu) for menu in MENUS),
                )
            )
        findings.extend(
            Finding(
                macro.path,
                1,
                f"'Install In' names {menu!r}, which is not a menu. Use "
                + " or ".join(repr(known) for known in MENUS),
            )
            for menu in macro.menus
            if menu not in MENUS
        )

    if not macro.body.strip():
        findings.append(Finding(macro.path, 1, "file has a header but no macro body"))

    return findings


def check_filename(macro: MacroFile) -> list[Finding]:
    """The filename is the kebab-cased command name, per macros/README.md."""
    if not macro.command_name:
        return []

    expected = slug(macro.command_name)
    if macro.path.stem != expected:
        return [
            Finding(
                macro.path,
                1,
                f"menu entry {macro.menu_entry!r} implies the filename "
                f"{expected}.nm, but this is {macro.path.name}",
            )
        ]
    return []


def check_replace_in_string_copy(macro: MacroFile) -> list[Finding]:
    """``replace_in_string()`` needs its fifth argument.

    Without ``"copy"`` it returns the empty string when the pattern matches
    nothing, so a whole-buffer rewrite deletes the file on the very inputs that
    needed no work.
    """
    findings = []
    for call in find_calls(macro.body, "replace_in_string"):
        if len(call.args) < 5:
            findings.append(
                Finding(
                    macro.path,
                    macro.body_offset + call.line - 1,
                    "replace_in_string() called with "
                    f'{len(call.args)} arguments; pass "copy" as the fifth or it '
                    'returns "" when the pattern doesn\'t match',
                )
            )
    return findings


def _literal_arguments(args: list[str]) -> tuple[list[str], bool]:
    """Split arguments into readable string literals and everything else.

    Returns the contents of each literal, and whether any argument was
    something this can't read.
    """
    literals = []
    opaque = False
    for arg in args:
        match = _STRING_LITERAL.match(arg)
        if match is None:
            opaque = True
        else:
            literals.append(match.group(1))
    return literals, opaque


def check_search_type(path: Path, text: str, offset: int = 1) -> list[Finding]:
    """Every search has to name a case-sensitive type.

    ``"literal"`` is the search with the Case Sensitive box unticked, and it is
    also the default, so leaving the type out picks the unsafe one. XNEdit folds
    case over UTF-8 rather than over bytes, which makes that worse than it
    sounds: uppercasing the ``fi`` ligature U+FB01 yields the two characters
    ``FI``, and a ``"literal"`` search for lower-case alpha matches capital
    Alpha, so a character table would rewrite letters it never named.

    The type is not a positional argument. ``readSearchArgs()`` (macro.c) and
    ``searchType()`` (menu.c) both walk every argument past the required ones
    looking for a recognised token, mixed in with ``"wrap"``, ``"nowrap"``,
    ``"backward"``, ``"forward"`` and ``"copy"``. So checking one slot proves
    nothing: ``search_string(s, "abc", 0, "backward")`` has an argument in the
    slot, names no type, and case-folds. Match the C and scan the lot.

    An argument that is not a plain string literal is a variable, and a variable
    could hold ``"case"``. Those suppress the "names no type" finding rather
    than risk a false positive on a macro doing something legitimate; a wrong
    type spelled out is still reported, since that one is certain.

    ``offset`` is the line the text starts on in the file, so findings point at
    the right line of a command whose body sits under a header.
    """
    findings = []

    for name, required in sorted(SEARCH_TYPE_FUNCTIONS.items()):
        for call in find_calls(text, name):
            literals, opaque = _literal_arguments(call.args[required:])
            named = [token for token in literals if token in SEARCH_TYPES]
            folding = [token for token in named if token in CASE_FOLDING_SEARCH_TYPES]
            line = offset + call.line - 1

            if folding:
                findings.append(
                    Finding(
                        path,
                        line,
                        f'{name}() searches with "{folding[0]}", which folds '
                        'case; pass "case" for an exact match, or "regex"',
                    )
                )
            elif not named and not opaque:
                findings.append(
                    Finding(
                        path,
                        line,
                        f"{name}() names no search type, so it falls back to a "
                        'case-insensitive one; pass "case" for an exact match, '
                        'or "regex"',
                    )
                )

    return findings


def check_no_define(macro: MacroFile) -> list[Finding]:
    """``define`` is illegal inside a menu item; it belongs in macros/lib/."""
    return [
        Finding(
            macro.path,
            macro.body_offset + line - 1,
            f"'define {name}' cannot appear in a menu command; "
            "put shared subroutines in macros/lib/",
        )
        for line, name in find_definitions(macro.body)
    ]


def check_library_prefix(path: Path, text: str) -> list[Finding]:
    """Library subroutines are namespaced ``ned_``, per macros/README.md."""
    return [
        Finding(path, line, f"subroutine {name!r} should be named ned_{name}")
        for line, name in find_definitions(text)
        if not name.startswith("ned_")
    ]


def check_formatting(path: Path) -> list[Finding]:
    """The file conventions from .editorconfig and .gitattributes."""
    raw = path.read_bytes()
    findings = []

    if b"\r" in raw:
        line = raw[: raw.index(b"\r")].count(b"\n") + 1
        findings.append(Finding(path, line, "carriage return; .nm files are LF only"))

    if raw and not raw.endswith(b"\n"):
        findings.append(
            Finding(path, raw.count(b"\n") + 1, "no newline at end of file")
        )

    for number, line in enumerate(raw.split(b"\n"), start=1):
        if line != line.rstrip(b" \t"):
            findings.append(Finding(path, number, "trailing whitespace"))
        if line.startswith(b"\t"):
            findings.append(Finding(path, number, "tab indent; .nm files use 4 spaces"))

    return findings


def check_command(macro: MacroFile) -> list[Finding]:
    """Every check that applies to a file in macros/commands/."""
    return [
        *check_header(macro),
        *check_filename(macro),
        *check_replace_in_string_copy(macro),
        *check_search_type(macro.path, macro.body, macro.body_offset),
        *check_no_define(macro),
        *check_formatting(macro.path),
    ]


def check_library(path: Path) -> list[Finding]:
    """Every check that applies to a file in macros/lib/."""
    text = path.read_text(encoding="utf-8")
    return [
        *check_library_prefix(path, text),
        *check_search_type(path, text),
        *check_formatting(path),
    ]
