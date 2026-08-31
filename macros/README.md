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
#   Install In:         Macro Menu
```

`Install In` is a comma-separated list of `Macro Menu` and
`Window Background Menu`, and a command can name both. The background menu is
the one a right-click opens, and it is a separate dialog rather than a tick box
on the first one.

The body below the header is what gets pasted into **Macro Command to
Execute**. Keep it standalone, or state in the header which `lib/` subroutines
it depends on.

### The header is not just documentation

Three of its fields are written into `docs/nedkit-macros.rc`, the file the
whole team installs from, and XNEdit reads them as a colon-separated list. So:

| Field | Constraint | What breaks without it |
| --- | --- | --- |
| `Menu Entry` | No colon and no `@`. `>` separates menu levels | A colon shifts everything after it into the accelerator field and the entry fails to load. XNEdit reads whatever follows an `@` as a language mode, so a command carrying one is hidden on every file that is not in that mode, silently |
| `Accelerator` | No colon. `Ctrl+Alt+K`, or `(none)` | Same |
| `Mnemonic` | One letter, or `(none)` | XNEdit rejects the entry with "mnemonic field too long" |
| `Install In` | Names the menus, so it decides which resources the command is written into | A command missing from a menu it belongs in, silently |

`nedkit.checks.check_resource_fields` covers part of that: it rejects a colon
in any of the first three fields and a mnemonic longer than one letter, so
`uv run pytest` catches those rather than the team discovering them. It does not
check that an accelerator is one XNEdit can read. `parseAcceleratorString()`
takes `Shift`, `Lock`, `Ctrl`, `Alt` and `Mod2` to `Mod5` joined with `+`, an X
keysym last, so `Ctrl-Alt-K` passes the check and then fails at load.

The reason to care is that a bad entry is not loud. XNEdit reports it on
stderr, which nobody is watching, then carries on with **that entry and every
entry after it in the same resource** dropped. One malformed header can cost
several unrelated commands, and the failure looks like "the macro didn't show
up" rather than like an error.

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

Then run `uv run python tools/gen_docs.py` so everything generated from the
macros matches what you changed, and commit it in the same commit:

| Regenerated | Why it matters |
| --- | --- |
| `docs/commands.md`, `docs/subroutines.md`, `docs/character-replacements.md` | The reference pages on the site |
| `docs/nedkit-macros.rc` | The install file. Adding a command does nothing for anybody until this is regenerated |

`uv run pytest` fails when a committed one has drifted, and so does CI, so this
is hard to forget. It is easy to forget that the `.rc` is a **deliverable**
rather than a build artifact: it is published at
<https://nedkit.sidereal.software/nedkit-macros.rc> and is what
[getting started](https://nedkit.sidereal.software/getting-started/) tells
people to download.

Two things about it that are worth knowing before you touch the format:

- **It is written for `xnedit -import`, not for `~/.xnedit/nedit.rc`.** The two
  look interchangeable and are not. `src/nedkit/rcfile.py`'s module docstring
  is the full version, naming the XNEdit routine on either side of the
  difference.
- **Never hand-edit it.** The escaping is unforgiving and silent: backslashes
  double, every line of a body ends `\n\`, and the closing brace has to land on
  its own line or a body ending in a comment closes inside that comment.
  `nedkit.rcfile` mirrors XNEdit's own writer so nobody has to get that right
  by hand.
