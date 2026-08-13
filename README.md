# nedkit

Small tools for the NED team at IPAC.

**Documentation: <https://nedkit.sidereal.software>**

Most of what lives here is XNEdit macros. A lot of the team's day goes into
reading and reshaping text files by hand, and collapsing a fiddly ten-step edit
into one menu item saves that time back every day it gets used. Python
utilities belong here too, for the jobs that are too big to do inside the
editor.

## Layout

| Path | Contents |
| --- | --- |
| `macros/commands/` | One file per XNEdit **Macro** menu command |
| `macros/lib/` | Shared subroutines, loaded at startup through `autoload.nm` |
| `docs/` | Sources for the documentation site |
| `tools/` | `gen_docs.py`, which regenerates the reference pages from the macros |
| `src/nedkit/`, `tests/` | The test harness, which nobody on the team runs |

## Installing the macros

The short version, assuming a stock XNEdit:

```sh
# Shared subroutines, available in every macro from startup onward.
cat macros/lib/*.nm >> ~/.xnedit/autoload.nm
```

Menu commands are a separate step, because XNEdit keeps them inside its
preferences file rather than as loose files on disk. Open a `.nm` file from
`macros/commands/`, copy the body, and paste it into
**Preferences → Default Settings → Customize Menus → Macro Menu**, then
**Preferences → Save Defaults**.

[docs/installing-macros.md](docs/installing-macros.md) covers both paths
properly, including where the config directory actually lives and how to
distribute a whole menu at once instead of pasting commands one by one.

## Writing macros

[docs/xnedit-macro-reference.md](docs/xnedit-macro-reference.md) is a condensed
reference for the macro language: the built-in subroutines and variables, the
action routines you can call, and the handful of behaviors that will waste an
afternoon if you don't know about them. Read the gotchas section before you
write anything that touches the whole buffer.

`macros/commands/trim-trailing-blanks.nm` and `macros/lib/text.nm` are working
examples. They exist to pin down the conventions the docs describe, so copy
their shape.

## Cleaning up a table pasted from a PDF

Two commands, run in this order:

1. **Align Columns** (`macros/commands/align-columns.nm`) joins whitespace- or
   tab-separated fields with `|` and pads each column to its widest value, so
   the file reads as a table and every row is the same length. Blank lines and
   the `##refcode` header block pass through untouched. Run it again after
   editing a value and the columns tidy back up.
2. **Normalize Characters** (`macros/commands/normalize-characters.nm`) rewrites
   the dashes, quotes, spaces and ligatures that only look like their ASCII
   counterparts, turns tabs into spaces, and reports whatever non-ASCII it
   deliberately left alone rather than guessing at it.

[docs/character-replacements.md](docs/character-replacements.md) lists every
character the second one touches, what it becomes, and what it leaves alone and
why.

Either order works, but aligning first is safer on a tab-separated file:
Normalize turns each tab into a single space, and after that an empty field
between two tabs can no longer be told apart from ordinary spacing.

## Requirements

macOS is the only platform in scope, running XNEdit 1.6 or newer on XQuartz.

This repo targets [unixwork/xnedit](https://github.com/unixwork/xnedit), a fork
of NEdit 5.7 with Unicode support, antialiased text, and multi-cursor editing.
It is a different program from classic NEdit and from
[nedit-ng](https://github.com/eteran/nedit-ng), and the three keep their
settings in different places. If a macro here misbehaves, check which editor is
actually running before you start debugging the macro.

There are no prebuilt macOS binaries, so XNEdit gets built from source. The
dependencies are all in Homebrew:

```sh
brew install --cask xquartz
brew install openmotif
make macos          # from a checkout of xnedit
```

Python is capped at 3.9, standard library only. That is the newest interpreter
on the team's machines, so no `match` statements, no `X | Y` unions in
annotations, and nothing that needs an install the team can't perform.

## Contributing

Keep commands small and single purpose. One file per menu command, named after
the command, with a header comment explaining what it does and whether it needs
a selection.

Test on a copy of a real file before committing. XNEdit macros write straight
to the buffer with no confirmation step, so a regex that matches more than you
intended will take the file with it.

## Tests

The suite runs every macro through a real XNEdit and compares the buffer
afterwards, byte for byte, against fixtures.

```sh
uv run pytest                 # everything
uv run pytest -m "not xnedit" # conventions only, no editor needed
```

The suite also fails when a macro has changed without
`uv run python tools/gen_docs.py` being run, so the documentation site cannot
drift away from the macros it describes.

Tests that drive the editor need XNEdit on `$PATH`, or `NEDKIT_XNEDIT` pointing
at the binary, and an X display. Without either they skip, so set
`NEDKIT_REQUIRE_XNEDIT=1` when a green run has to mean something.

A new command needs at least one case under
`tests/fixtures/<command>/<case>/`, holding `input.txt` and the `expected.txt`
it should produce; the suite fails on any command that has none. Test harness
code lives in `src/nedkit/` and runs on current Python. Everything else stays
on 3.9, which `tests/test_python_version.py` checks against a real 3.9 that uv
fetches.

## License

MIT. See [LICENSE](LICENSE).
