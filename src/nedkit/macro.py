"""Reading the ``.nm`` files in ``macros/``.

A menu command file is a header comment followed by the macro body:

    # Trim Trailing Blanks
    #
    # Removes trailing spaces and tabs from every line in the buffer.
    #
    #   Menu Entry:         NED>Trim Trailing Blanks
    #   Accelerator:        (none)
    #   Mnemonic:           (none)
    #   Requires Selection: no
    #   Install In:         Macro Menu

    original = get_range(0, $text_length)
    ...

The header is the leading run of comment and blank lines, so a body must not
open with a comment of its own or it gets read as part of the header. Every
command in ``macros/commands/`` starts with code, and
``tests/test_conventions.py`` keeps it that way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: Header fields, as they are spelled in the dialog they get typed into.
#: No name here may be a prefix of another, or the alternation in ``_FIELD_RE``
#: below stops being unambiguous.
HEADER_FIELDS = (
    "Menu Entry",
    "Accelerator",
    "Mnemonic",
    "Requires Selection",
    "Install In",
)

#: The menus a command can be installed into, spelled as the Customize Menus
#: dialog spells them. Each is a separate resource in ``nedit.rc``:
#: ``nedit.macroCommands`` and ``nedit.bgMenuCommands``. A command can be in
#: both, which is why ``Install In`` is a list rather than a yes/no field.
MENUS = ("Macro Menu", "Window Background Menu")

#: A value meaning "this field is deliberately empty".
NONE_VALUES = frozenset({"(none)", "none", "-", ""})

_FIELD_RE = re.compile(
    r"^#\s*(" + "|".join(re.escape(f) for f in HEADER_FIELDS) + r")\s*:\s*(.*?)\s*$"
)

#: The comment marker and the single space that conventionally follows it.
#: Only that one space comes off, so indentation inside the header survives.
_COMMENT_RE = re.compile(r"^#[ ]?")


@dataclass(frozen=True)
class MacroFile:
    """One ``.nm`` file, split into its header and its body."""

    path: Path
    title: str
    prose: str
    """The description between the title and the ``Menu Entry:`` block.

    Comment markers are stripped but indentation is kept, so an indented
    example in the header stays an indented code block once it reaches the
    docs. ``tools/gen_docs.py`` renders this as the command's description,
    which is why the header is worth writing as documentation.
    """

    fields: dict[str, str]
    body: str
    body_offset: int
    """Line number (1-based) the body starts on, for error messages."""

    @property
    def menu_entry(self) -> str:
        return self.fields.get("Menu Entry", "")

    @property
    def requires_selection(self) -> bool:
        return self.fields.get("Requires Selection", "").strip().lower() in {
            "yes",
            "true",
        }

    @property
    def menus(self) -> tuple[str, ...]:
        """The menus this command installs into, in the order written.

        Whether the names are ones :data:`MENUS` knows about is
        :func:`nedkit.checks.check_header`'s business, so a typo reaches the
        reader as a test failure naming the file rather than as a command that
        quietly stops appearing anywhere.
        """
        return tuple(
            name.strip()
            for name in self.fields.get("Install In", "").split(",")
            if name.strip()
        )

    @property
    def in_background_menu(self) -> bool:
        """True for a command that also answers a right-click."""
        return "Window Background Menu" in self.menus

    @property
    def command_name(self) -> str:
        """The last segment of the menu path: ``NED>Trim X`` -> ``Trim X``."""
        return self.menu_entry.rsplit(">", 1)[-1].strip()


def parse(path: Path) -> MacroFile:
    """Read a ``.nm`` file. Never raises on a malformed header.

    Structural problems are reported by :mod:`nedkit.checks` rather than here,
    so that a broken file produces a readable test failure instead of an
    exception during collection.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    fields: dict[str, str] = {}
    title = ""
    prose: list[str] = []
    body_start = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            body_start = index
            break

        match = _FIELD_RE.match(line)
        if match:
            value = match.group(2)
            fields[match.group(1)] = "" if value in NONE_VALUES else value
        elif not title and stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
        elif not fields and stripped.startswith("#"):
            # Everything after the fields is install boilerplate, identical in
            # every command, so prose collection stops once a field is seen.
            prose.append(_COMMENT_RE.sub("", line, count=1).rstrip())
    else:
        # Comments all the way down: no body at all.
        body_start = len(lines)

    body_lines = lines[body_start:]
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    return MacroFile(
        path=path,
        title=title,
        prose="\n".join(prose).strip("\n"),
        fields=fields,
        body="\n".join(body_lines),
        body_offset=body_start + 1,
    )


def command_files(repo_root: Path) -> list[Path]:
    """Every menu command in the repo, sorted."""
    return sorted((repo_root / "macros" / "commands").glob("*.nm"))


def library_files(repo_root: Path) -> list[Path]:
    """Every subroutine library in the repo, sorted."""
    return sorted((repo_root / "macros" / "lib").glob("*.nm"))


def slug(name: str) -> str:
    """Kebab-case a command name the way its filename is expected to be spelled.

    ``Trim Trailing Blanks`` -> ``trim-trailing-blanks``
    """
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[\s_]+", "-", cleaned)
