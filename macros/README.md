# macros

XNEdit macros, split by how they get installed.

What each one does is on the documentation site rather than here, generated
from the files themselves so the two cannot disagree:
[commands](https://nedkit.sidereal.software/commands/) and
[subroutines](https://nedkit.sidereal.software/subroutines/). This page is the
conventions for writing them.

## `lib/`

Subroutine definitions, appended to `~/.xnedit/autoload.nm` and available to
every macro from startup onward. Nothing in here appears in a menu.

Prefix every subroutine `ned_` so it can't collide with a built-in or with
someone's personal macros. Note that the prefix is not decoration: a
user-defined subroutine silently shadows a built-in of the same name.

## `commands/`

One file per **Macro** menu command. Each file is a header comment followed by
the macro body, and the header carries everything needed to fill in the
Customize Menus dialog:

```
# Command Name
#
# What it does. This becomes the command's page on the site, so write it as
# documentation.
#
#   Menu Entry:         NED>Command Name
#   Accelerator:        Ctrl+Alt+K
#   Mnemonic:           (none)
#   Requires Selection: no
```

The body below the header is what gets pasted into **Macro Command to
Execute**. Keep it standalone, or state in the header which `lib/` subroutines
it depends on.

## Conventions

- Kebab-case filenames matching the command name.
- `.nm` extension, LF line endings, enforced by `.gitattributes`.
- Four-space indentation.
- One command per file, doing one thing.
- Anything that rewrites the whole buffer should compare against the original
  and do nothing when there is no change, so the undo history stays clean.

`uv run pytest -m "not xnedit"` checks all of that, plus the header fields and
the `replace_in_string()` trap, without needing an editor.

## Before you commit

Add fixtures. A command with none fails the suite. See
[running the tests](https://nedkit.sidereal.software/testing/), and
[the macro language reference](https://nedkit.sidereal.software/xnedit-macro-reference/)
for the behaviors that cause most of the bugs.

Then run `uv run python tools/gen_docs.py` so the generated pages match what
you changed, and commit those in the same commit.
