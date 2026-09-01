#!/usr/bin/env python3
"""Regenerate the parts of the docs that are derived from the macros.

Three regions are generated, each marked off in its page by a pair of HTML
comments. Everything outside the markers is hand-written prose and is never
touched:

    docs/commands.md                 one section per macros/commands/*.nm
    docs/subroutines.md              one section per subroutine in macros/lib/*.nm
    docs/character-replacements.md   the table inside every command that has one

One whole file is generated as well, and it is a download rather than a page:

    docs/nedkit-macros.rc            every command, ready for xnedit -import
    docs/samples/A13L.mod.*          the worked example's input and output

Run it after changing a macro:

    uv run python tools/gen_docs.py

CI runs ``--check``, which regenerates into memory and fails if the committed
pages have drifted.

Header parsing lives in :mod:`nedkit.macro`, character-table parsing in
:mod:`nedkit.chartable` and the resource-file format in :mod:`nedkit.rcfile`,
all of which the test suite also uses, so there is one definition of each
rather than two that can disagree.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

from nedkit.chartable import character_tables
from nedkit.macro import MacroFile, command_files, library_files, parse
from nedkit.rcfile import fragment

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

COMMENT_RE = re.compile(r"^#\s?(.*)$")
DEFINE_RE = re.compile(r"^define\s+(\w+)\s*\{")


# --------------------------------------------------------------------------
# reading the macros


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


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


# --------------------------------------------------------------------------
# writing the generated regions


def fence(body, language="", classes=(), title=None):
    """A fenced block, in pymdownx's brace form when it carries attributes.

    ``classes`` and ``title`` reach the rendered page through ``attr_list``:
    the classes land on the wrapping ``div.highlight``, which is where Material
    looks for ``.copy`` when deciding whether to hang a copy button on a block,
    and the title becomes the block's caption.
    """
    info = language
    if classes or title is not None:
        parts = ["." + name for name in (language, *classes) if name]
        if title is not None:
            parts.append('title="%s"' % title)
        info = "{ %s }" % " ".join(parts)
    return "```%s\n%s\n```" % (info, body)


def collapsed(summary, body, language="", classes=(), title=None):
    """A pymdownx.details block, so long macro bodies start folded away."""
    indented = "\n".join(
        ("    " + line).rstrip()
        for line in fence(body, language, classes, title).split("\n")
    )
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
    return "\n".join(
        "\\" + line if line.startswith("#") else line for line in text.split("\n")
    )


def source_link(macro: MacroFile) -> str:
    path = rel(macro.path)
    return "[`%s`](%s/%s)" % (path, REPO_URL_BLOB, path)


def gen_commands():
    out = []
    for path in command_files(REPO):
        macro = parse(path)
        out.append("## %s" % macro.title)
        out.append("")
        # Directly under the heading, because a collapsed block emitted after
        # the prose renders hard against the *next* command's heading, and a
        # reader reasonably reads it as belonging to that one.
        out.append(
            collapsed(
                "Macro body, only if you are installing this one command by hand",
                macro.body,
                language="text",
                classes=("copy",),
                title="Paste into Macro Command to Execute",
            )
        )
        out.append("")
        out.append("| Setting | Value |")
        out.append("| --- | --- |")
        out.append("| Menu entry | `%s` |" % macro.menu_entry)
        out.append("| Installed in | %s |" % (", ".join(macro.menus) or "(nowhere)"))
        out.append(
            "| Accelerator | %s |" % (macro.fields.get("Accelerator") or "(none)")
        )
        out.append(
            "| Requires a selection | %s |"
            % ("yes" if macro.requires_selection else "no")
        )
        out.append("| Source | %s |" % source_link(macro))
        out.append("")
        out.append(as_prose(macro.prose))
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
    """One section per command that carries a table, groups nested inside.

    The command has to be named, because a reader looking a character up needs
    to know which command to run to get it replaced.
    """
    out = []
    for path, groups, names in character_tables(REPO):
        macro = parse(path)
        total = sum(len(entries) for _, entries in groups)
        out.append("### %s" % macro.title)
        out.append("")
        out.append(
            "%d characters, every one of them replaced by plain ASCII. From %s."
            % (total, source_link(macro))
        )
        out.append("")
        for title, entries in groups:
            out.append("#### %s" % (title[0].upper() + title[1:] if title else "Other"))
            out.append("")
            out.append("| Character | Code point | Name | Becomes |")
            out.append("| --- | --- | --- | --- |")
            for char, replacement in entries:
                shown = "(not printable)"
                if unicodedata.category(char) not in UNPRINTABLE:
                    shown = "`%s`" % char
                label = re.sub(r"^U\+[0-9A-F]{4,6}\s+", "", names.get(char, ""))
                out.append(
                    "| %s | U+%04X | %s | %s |"
                    % (shown, ord(char), label, describe(replacement))
                )
            out.append("")
    return "\n".join(out).strip("\n")


REPO_URL_BLOB = "https://github.com/sidereal-software/nedkit/blob/main"

REGIONS = {
    "docs/commands.md": [("commands", gen_commands)],
    "docs/subroutines.md": [("subroutines", gen_subroutines)],
    "docs/character-replacements.md": [("character-table", gen_character_table)],
}

#: The sample files the worked example is written against, published so that a
#: reader who installed by downloading rather than by cloning can actually run
#: it. Copying them beats linking to the repo: the example is about tab
#: characters, and a reader who copies the listing off the rendered page gets
#: spaces, so the first command reports nothing to do and the column numbers on
#: the page land inside the data.
SAMPLES = ("A13L.mod.before", "A13L.mod.after")

#: Files written whole, as against regions spliced into a hand-written page.
#: MkDocs copies anything in ``docs/`` that is not Markdown to the built site,
#: so each of these is downloadable at https://nedkit.sidereal.software/ under
#: its own path.
FILES = {
    "docs/nedkit-macros.rc": lambda: fragment(REPO),
    **{
        "docs/samples/%s" % name: (lambda n=name: read("samples/%s" % n))
        for name in SAMPLES
    },
}


def splice(page, marker, generated):
    begin, end = BEGIN % marker, END % marker
    if begin not in page or end not in page:
        raise SystemExit("%s markers missing from the page" % marker)
    head = page.split(begin)[0]
    tail = page.split(end)[1]
    return "%s%s\n\n%s\n\n%s%s" % (head, begin, generated, end, tail)


def regenerate(path):
    """What ``path`` holds now, and what it should hold."""
    if path in REGIONS:
        current = read(path)
        updated = current
        for marker, generator in REGIONS[path]:
            updated = splice(updated, marker, generator())
        return current, updated
    # A generated file need not exist yet, and treating a missing one as empty
    # is what makes --check report it as out of date rather than crash.
    target = REPO / path
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    return current, FILES[path]()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if a committed file is out of date"
    )
    args = parser.parse_args()

    stale = []
    for path in sorted({**REGIONS, **FILES}):
        current, updated = regenerate(path)
        if updated == current:
            continue
        if args.check:
            stale.append(path)
            diff = difflib.unified_diff(
                current.split("\n"),
                updated.split("\n"),
                fromfile="%s (committed)" % path,
                tofile="%s (regenerated)" % path,
                lineterm="",
            )
            sys.stderr.write("\n".join(list(diff)[:40]) + "\n")
        else:
            (REPO / path).parent.mkdir(parents=True, exist_ok=True)
            (REPO / path).write_text(updated, encoding="utf-8", newline="\n")
            sys.stderr.write("updated %s\n" % path)

    if stale:
        sys.stderr.write(
            "\n%d file(s) out of date with the macros. Run:\n\n"
            "    uv run python tools/gen_docs.py\n\n" % len(stale)
        )
        return 1
    if args.check:
        sys.stderr.write("docs are in step with the macros\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
