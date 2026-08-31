r"""Writing the menu commands out as an X resource file XNEdit can import.

One file installs the whole set, which is the alternative to typing nine
commands into the Customize Menus dialog:

    xnedit -import nedkit-macros.rc

**Importing adds; a preferences file replaces.** ``loadMenuItemString()`` in
XNEdit's ``userCmds.c`` appends each entry to the list already loaded and
replaces only an entry whose menu path matches, so an import keeps XNEdit's own
commands and anything installed by hand. Dropping the same resource into
``~/.xnedit/nedit.rc`` does the opposite: ``readPrefs()`` in ``util/prefFile.c``
takes one source per resource and falls back to the compiled-in default only
when no file names it, so a hand-written file silently replaces every command
XNEdit ships with: Complete Word, Fill Sel. w/Char, the two mail-reply
commands, the Comments submenu and Make C Prototypes. That is why this file is
written for ``-import`` and not for ``nedit.rc``.

The format mirrors ``writeMenuItemString()``, the routine Save Defaults uses,
because the reader on the other side is unforgiving about every part of it: the
four colon-separated fields, the ``\n\`` that has to end every line of a body,
the two tabs of indentation the reader strips off again, and the backslashes
that double on the way in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from nedkit.macro import MacroFile, command_files, parse

#: The two resources a menu command can live in, one per menu.
MACRO_MENU_RESOURCE = "nedit.macroCommands"
BG_MENU_RESOURCE = "nedit.bgMenuCommands"

#: An escaped newline followed by the resource file's own line continuation.
#: Every line of a macro body ends with this, and the last line of a resource
#: keeps the escaped newline but drops the continuation.
LINE_END = "\\n\\\n"

#: What the reader strips back off the front of each body line, so a body
#: written at this indentation comes out at the indentation it went in at.
BODY_INDENT = "\t\t"

HEADER = """\
! XNEdit macro menu commands for the NED team at IPAC.
!
!     xnedit -import nedkit-macros.rc
!
! then Preferences > Save Defaults in the window that opens. Importing merges
! with the commands already installed rather than replacing them, so this will
! not disturb anything else in the Macro menu.
!
! Generated from macros/commands/*.nm by tools/gen_docs.py. Change a macro and
! regenerate; edits made here are overwritten.
!
! https://nedkit.sidereal.software/
"""


def escape(text: str) -> str:
    r"""One macro body as a resource value.

    Backslashes double, because the resource reader takes a level of escaping
    off before the macro parser ever sees the string, and each newline becomes
    ``LINE_END`` followed by ``BODY_INDENT``, not a bare ``\n``, so the body
    stays one logical line at the indentation the reader strips back off.
    """
    return text.replace("\\", "\\\\").replace("\n", LINE_END + BODY_INDENT)


def entry(macro: MacroFile) -> str:
    """One command, as the line block a ``nedit.macroCommands`` value is made of.

    The four fields are the ones the Customize Menus dialog asks for. An empty
    field still needs its colon, which is why a command with no accelerator and
    no mnemonic reads ``::::``.
    """
    name = macro.menu_entry.replace("\\", "\\\\")
    accelerator = macro.fields.get("Accelerator", "")
    mnemonic = macro.fields.get("Mnemonic", "")
    flags = "R" if macro.requires_selection else ""

    # The dialog terminates every body with a newline before writing it
    # (addTerminatingNewline), and the writer then takes one of the two tabs
    # back off so the closing brace sits one level in. Reproducing both is what
    # puts the brace where copyMacroToEnd looks for it, rather than on the end
    # of whatever the body's last line happens to be. A body ending in a
    # comment would otherwise close the macro inside that comment.
    body = escape(macro.body + "\n")[: -len("\t")]

    return (
        f"\t{name}:{accelerator}:{mnemonic}:{flags}: {{"
        f"{LINE_END}{BODY_INDENT}{body}}}{LINE_END}"
    )


def resource(name: str, macros: Sequence[MacroFile]) -> str:
    """One resource, holding every command in ``macros``."""
    entries = "".join(entry(macro) for macro in macros)
    # The value's last line keeps its escaped newline and loses the
    # continuation, otherwise the resource swallows whatever follows it.
    return f"{name}: \\\n" + entries[: -len("\\\n")]


def fragment(repo_root: Path) -> str:
    """The whole importable file: every command, in each menu it belongs to.

    A menu no command asks for is left out rather than written empty, since an
    empty value is a resource that says nothing and reads as an oversight.
    """
    macros = [parse(path) for path in command_files(repo_root)]
    in_menu = {
        MACRO_MENU_RESOURCE: [m for m in macros if m.in_macro_menu],
        BG_MENU_RESOURCE: [m for m in macros if m.in_background_menu],
    }
    resources = [resource(name, ms) for name, ms in in_menu.items() if ms]
    return HEADER + "\n" + "\n\n".join(resources) + "\n"
