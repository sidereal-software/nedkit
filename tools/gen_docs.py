#!/usr/bin/env python3
"""Regenerate the parts of the docs that are derived from the macros.

Three regions are generated, each marked off in its page by a pair of HTML
comments. Everything outside the markers is hand-written prose and is never
touched:

    docs/commands.md                 one section per macros/commands/*.nm
    docs/subroutines.md              one section per subroutine in macros/lib/*.nm
    docs/character-replacements.md   the table inside normalize-characters.nm

Run it after changing a macro:

    uv run python tools/gen_docs.py

CI runs ``--check``, which regenerates into memory and fails if the committed
pages have drifted.

Header parsing lives in :mod:`nedkit.macro`, which the test suite also uses, so
there is one definition of what a macro header is rather than two that can
disagree.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

from nedkit.macro import MacroFile, command_files, library_files, parse

REPO = Path(__file__).resolve().parents[1]

BEGIN = "<!-- BEGIN GENERATED: %s -->"
END = "<!-- END GENERATED: %s -->"

# Characters that would leave an empty or broken table cell if printed as
# themselves: separators, formatting characters and controls.
UNPRINTABLE = ("Zs", "Zl", "Zp", "Cf", "Cc")

# What a replacement string looks like in the "Becomes" column.
NAMED_REPLACEMENTS = {
    "": "removed",
    " ": "a space",
    "\n": "a newline",
}

FIX_RE = re.compile(r'^fix\["([^"]*)"\]\s*=\s*"(.*)"\s*$')
NAM_RE = re.compile(r'^nam\["([^"]*)"\]\s*=\s*"(.*)"\s*$')
COMMENT_RE = re.compile(r"^#\s?(.*)$")
DEFINE_RE = re.compile(r"^define\s+(\w+)\s*\{")


# --------------------------------------------------------------------------
# reading the macros


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def unescape(literal):
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
            while j < len(literal) and len(digits) < 2 and literal[j] in "0123456789abcdefABCDEF":
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


def parse_subroutines(text):
    """Pull each ``define`` out of a library file with the comment above it."""
    found = []
    lines = text.split("\n")
    comment = []
    for line in lines:
        match = COMMENT_RE.match(line)
        if match is not None:
            comment.append(match.group(1).rstrip())
            continue
        define = DEFINE_RE.match(line)
        if define is not None:
            found.append((define.group(1), "\n".join(comment).strip("\n")))
        comment = []
    return found


def parse_character_table(text):
    """Read the fix/nam table out of normalize-characters.nm.

    A group starts at the comment line directly above a ``fix[...]`` line, with
    no blank line between the two. That is the only thing separating a group
    heading from ordinary prose earlier in the header, so keep the table
    formatted the way it already is.
    """
    groups = []
    pending = None
    names = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == "":
            pending = None
            continue
        comment = COMMENT_RE.match(line)
        if comment is not None:
            pending = comment.group(1).strip()
            continue
        fix = FIX_RE.match(line)
        if fix is not None:
            if pending is not None or not groups:
                groups.append((pending or "", []))
                pending = None
            groups[-1][1].append((unescape(fix.group(1)), unescape(fix.group(2))))
            continue
        nam = NAM_RE.match(line)
        if nam is not None:
            names[unescape(nam.group(1))] = unescape(nam.group(2))
            pending = None
    return groups, names


# --------------------------------------------------------------------------
# writing the generated regions


def fence(body, language=""):
    return "```%s\n%s\n```" % (language, body)


def collapsed(summary, body, language=""):
    """A pymdownx.details block, so long macro bodies start folded away."""
    indented = "\n".join(("    " + l).rstrip() for l in fence(body, language).split("\n"))
    return '??? example "%s"\n\n%s' % (summary, indented)


def as_prose(text: str) -> str:
    r"""Make a macro's header comment safe to drop into a Markdown page.

    Stripping the comment marker off ``# ##refcode is left alone`` leaves
    ``##refcode is left alone``, which Markdown reads as a heading: a banner
    mid-paragraph and a phantom entry in the table of contents. A backslash in
    the first column keeps it as text.

    Indented lines are left alone. Four spaces already makes them a code
    block, where a hash is only ever a hash.
    """
    return "\n".join("\\" + line if line.startswith("#") else line
                     for line in text.split("\n"))


def source_link(macro: MacroFile) -> str:
    path = rel(macro.path)
    return "[`%s`](%s/%s)" % (path, REPO_URL_BLOB, path)


def gen_commands():
    out = []
    for path in command_files(REPO):
        macro = parse(path)
        out.append("## %s" % macro.title)
        out.append("")
        out.append("| Setting | Value |")
        out.append("| --- | --- |")
        out.append("| Menu entry | `%s` |" % macro.menu_entry)
        out.append("| Accelerator | %s |" % (macro.fields.get("Accelerator") or "(none)"))
        out.append("| Requires a selection | %s |"
                   % ("yes" if macro.requires_selection else "no"))
        out.append("| Source | %s |" % source_link(macro))
        out.append("")
        out.append(as_prose(macro.prose))
        out.append("")
        out.append(collapsed("The macro body, ready to paste", macro.body))
        out.append("")
    return "\n".join(out).strip("\n")


def gen_subroutines():
    out = []
    for path in library_files(REPO):
        out.append("## `%s`" % path.name)
        out.append("")
        out.append("From [`%s`](%s/%s)." % (rel(path), REPO_URL_BLOB, rel(path)))
        out.append("")
        for subroutine, comment in parse_subroutines(path.read_text(encoding="utf-8")):
            out.append("### `%s()`" % subroutine)
            out.append("")
            out.append(as_prose(comment))
            out.append("")
    return "\n".join(out).strip("\n")


def describe(replacement):
    named = NAMED_REPLACEMENTS.get(replacement)
    if named is not None:
        return named
    return "`%s`" % replacement


def gen_character_table():
    groups, names = parse_character_table(read("macros/commands/normalize-characters.nm"))
    total = sum(len(entries) for _, entries in groups)
    out = ["%d characters, every one of them replaced by plain ASCII." % total, ""]
    for title, entries in groups:
        out.append("### %s" % (title[0].upper() + title[1:] if title else "Other"))
        out.append("")
        out.append("| Character | Code point | Name | Becomes |")
        out.append("| --- | --- | --- | --- |")
        for char, replacement in entries:
            shown = "(not printable)"
            if unicodedata.category(char) not in UNPRINTABLE:
                shown = "`%s`" % char
            label = names.get(char, "")
            label = re.sub(r"^U\+[0-9A-F]{4,6}\s+", "", label)
            out.append("| %s | U+%04X | %s | %s |"
                       % (shown, ord(char), label, describe(replacement)))
        out.append("")
    return "\n".join(out).strip("\n")


REPO_URL_BLOB = "https://github.com/sidereal-software/nedkit/blob/main"

REGIONS = {
    "docs/commands.md": [("commands", gen_commands)],
    "docs/subroutines.md": [("subroutines", gen_subroutines)],
    "docs/character-replacements.md": [("character-table", gen_character_table)],
}


def splice(page, marker, generated):
    begin, end = BEGIN % marker, END % marker
    if begin not in page or end not in page:
        raise SystemExit("%s markers missing from the page" % marker)
    head = page.split(begin)[0]
    tail = page.split(end)[1]
    return "%s%s\n\n%s\n\n%s%s" % (head, begin, generated, end, tail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if a committed page is out of date")
    args = parser.parse_args()

    stale = []
    for page, regions in sorted(REGIONS.items()):
        current = read(page)
        updated = current
        for marker, generator in regions:
            updated = splice(updated, marker, generator())
        if updated == current:
            continue
        if args.check:
            stale.append(page)
            diff = difflib.unified_diff(current.split("\n"), updated.split("\n"),
                                        fromfile="%s (committed)" % page,
                                        tofile="%s (regenerated)" % page, lineterm="")
            sys.stderr.write("\n".join(list(diff)[:40]) + "\n")
        else:
            (REPO / page).write_text(updated, encoding="utf-8", newline="\n")
            sys.stderr.write("updated %s\n" % page)

    if stale:
        sys.stderr.write(
            "\n%d page(s) out of date with the macros. Run:\n\n"
            "    uv run python tools/gen_docs.py\n\n" % len(stale))
        return 1
    if args.check:
        sys.stderr.write("docs are in step with the macros\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
