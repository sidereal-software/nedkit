# macros

XNEdit macros, split by how they get installed.

## `lib/`

Subroutine definitions, appended to `~/.xnedit/autoload.nm` and available to
every macro from startup onward. Nothing in here appears in a menu.

Prefix every subroutine `ned_` so it can't collide with a built-in or with
someone's personal macros.

## `commands/`

One file per **Macro** menu command. Each file is a header comment followed by
the macro body, and the header carries everything needed to fill in the
Customize Menus dialog:

```
# Command Name
#
# What it does, in a sentence or two.
#
#   Menu Entry:         NED>Command Name
#   Accelerator:        Ctrl+Alt+K
#   Mnemonic:           (none)
#   Requires Selection: no
```

The body below the header is what gets pasted into **Macro Command to
Execute**. Keep it standalone, or state in the header which `lib/` subroutines
it depends on.

Current commands:

| File | Menu entry | What it does |
| --- | --- | --- |
| `align-columns.nm` | `NED>Align Columns` | Joins fields with `\|` and pads each column to its widest value. |
| `normalize-characters.nm` | `NED>Normalize Characters` | Rewrites non-ASCII lookalikes, tabs and stray carriage returns. See [../docs/character-replacements.md](../docs/character-replacements.md). |
| `trim-trailing-blanks.nm` | `NED>Trim Trailing Blanks` | Removes trailing spaces and tabs from every line. |

## Conventions

- Kebab-case filenames matching the command name.
- `.nm` extension, LF line endings, enforced by `.gitattributes`.
- Four-space indentation.
- One command per file, doing one thing.
- Anything that rewrites the whole buffer should compare against the original
  and do nothing when there is no change, so the undo history stays clean.

## Before you commit

Test on a copy of a real file first.

`docs/xnedit-macro-reference.md` has the language reference and the list of
behaviors that cause most bugs. `docs/installing-macros.md` covers installation
in full.
