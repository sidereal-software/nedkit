"""Reading the character tables out of the command macros.

Two commands carry one. ``normalize-characters.nm`` has the punctuation, and
``fold-letters-to-ascii.nm`` has the accented Latin and Greek letters. Together
they are hundreds of lines of pure data, too many to review by eye every time
one changes. ``tools/gen_docs.py`` renders them into
``docs/character-replacements.md`` and ``tests/test_character_table.py``
re-derives them from :mod:`unicodedata`, and both go through the functions here
so there is one definition of what a table is rather than two that can
disagree.

Two arrays carry entries. ``fix[]`` is applied first and its replacements can
be any length; ``grk[]`` is applied last and every replacement in it has to be
exactly one character, because the macro reports each Greek letter's line and
column by subtracting the bytes the earlier folds removed. The macro says the
same thing in a comment above the table.

``nam[]`` labels are optional. A macro compiles into 4096 instructions and a
label doubles what an entry costs, which the 240-entry fold table cannot
afford, so it ships without them and :func:`label_for` derives the same string
from the key's own bytes. Where a macro does write a label it wins, which is
what keeps hand-written text such as the ``(BOM)`` suffix.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from nedkit.macro import command_files

#: Macro arrays holding a character and what it is replaced by.
TABLE_ARRAYS = ("fix", "grk")

#: Macro arrays holding a character and the label the summary prints for it.
LABEL_ARRAYS = ("nam",)


def _array_re(names: tuple[str, ...]) -> re.Pattern[str]:
    alternation = "|".join(re.escape(name) for name in names)
    return re.compile(r'^(?:%s)\["([^"]*)"\]\s*=\s*"(.*)"\s*$' % alternation)


TABLE_RE = _array_re(TABLE_ARRAYS)
LABEL_RE = _array_re(LABEL_ARRAYS)
COMMENT_RE = re.compile(r"^#\s?(.*)$")


def unescape(literal: str) -> str:
    r"""Decode a macro string literal's escapes, as parse.y's lexer does.

    Only the escapes the macros actually use are handled: ``\xNN`` (at most two
    hex digits, the same limit the lexer applies), ``\n``, ``\"`` and ``\\``.
    """
    out = bytearray()
    i = 0
    while i < len(literal):
        char = literal[i]
        if char != "\\" or i + 1 >= len(literal):
            out.extend(char.encode("utf-8"))
            i += 1
            continue
        nxt = literal[i + 1]
        if nxt == "x":
            digits = ""
            j = i + 2
            while (
                j < len(literal)
                and len(digits) < 2
                and literal[j] in "0123456789abcdefABCDEF"
            ):
                digits += literal[j]
                j += 1
            out.append(int(digits, 16))
            i = j
        elif nxt == "n":
            out.append(0x0A)
            i += 2
        elif nxt in ('"', "\\"):
            out.extend(nxt.encode("utf-8"))
            i += 2
        else:
            out.extend(nxt.encode("utf-8"))
            i += 2
    return out.decode("utf-8")


def label_for(char: str) -> str:
    """``U+2013 EN DASH``, worked out from the character itself.

    What a macro would have written in ``nam[]`` if it had the instructions to
    spare.
    """
    try:
        return "U+%04X %s" % (ord(char), unicodedata.name(char))
    except ValueError:
        raise ValueError(
            "U+%04X has no Unicode name, so it needs a nam[] label written by "
            "hand in the macro" % ord(char)
        ) from None


def parse_character_table(text: str):
    """Read one macro's table.

    Returns ``(groups, names)``, where ``groups`` is a list of
    ``(heading, [(character, replacement), ...])`` in the order the macro
    writes them, and ``names`` maps every character in them to its label.
    A ``nam[]`` line in the macro supplies that label; anything without one
    gets :func:`label_for`.

    A group starts at the comment line directly above a ``fix[...]`` or
    ``grk[...]`` line, with no blank line between the two. That is the only
    thing separating a group heading from ordinary prose earlier in the header,
    so keep the table formatted the way it already is.
    """
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    pending: str | None = None
    names: dict[str, str] = {}

    for line in text.split("\n"):
        if line.strip() == "":
            pending = None
            continue

        comment = COMMENT_RE.match(line)
        if comment is not None:
            pending = comment.group(1).strip()
            continue

        entry = TABLE_RE.match(line)
        if entry is not None:
            if pending is not None or not groups:
                groups.append((pending or "", []))
                pending = None
            groups[-1][1].append((unescape(entry.group(1)), unescape(entry.group(2))))
            continue

        label = LABEL_RE.match(line)
        if label is not None:
            names[unescape(label.group(1))] = unescape(label.group(2))
            pending = None

    for _, entries in groups:
        for char, _ in entries:
            if char not in names:
                names[char] = label_for(char)

    return groups, names


def character_tables(repo_root: Path):
    """Every command that carries a table, as ``(path, groups, names)``.

    In the same order as :func:`nedkit.macro.command_files`, so adding a third
    command with a table of its own puts it in the docs without touching the
    generator. Commands with no table are skipped.
    """
    tables = []
    for path in command_files(repo_root):
        groups, names = parse_character_table(path.read_text(encoding="utf-8"))
        if groups:
            tables.append((path, groups, names))
    return tables
