# nedkit

Small tools for the NED team at IPAC.

**Documentation: <https://nedkit.sidereal.software>**

Most of it is XNEdit macros. Reshaping a data file by hand is slow and easy to
get subtly wrong, and a macro does the same edit the same way every time.
Python utilities live here too, for the jobs too big to run inside the editor.

## Layout

| Path | Contents |
| --- | --- |
| `macros/commands/` | One file per XNEdit **Macro** menu command |
| `macros/lib/` | Shared subroutines, loaded at startup through `autoload.nm` |
| `python/` | `ned-transients`, which prepares the monthly SNe, FRB and GRB load |
| `docs/` | Sources for the documentation site |
| `samples/` | A real job, before and after, and the list of what is still done by hand |
| `tools/` | `gen_docs.py`, which regenerates the reference pages from the macros |
| `src/nedkit/`, `tests/` | The test harness, which nobody on the team runs |

## ned-transients

Fetches the new supernovae, fast radio bursts and gamma-ray bursts from the
Transient Name Server and Swift XRT, and writes the loadstatus file, the
ptables, the directory tree and the Jira ticket body that the procedure
otherwise asks someone to build by copying last year's.

One command per step, so you can run the parts that help:

```sh
B="--root /nedefs/Project/Production/dev/data.tables --batch a"

python3 python/ned-transients scaffold   $B
python3 python/ned-transients fetch      $B --since 2025-08-01 --until 2026-02-05
python3 python/ned-transients ptable     $B
python3 python/ned-transients loadstatus $B
python3 python/ned-transients jira       $B
```

`prepare` runs all five at once. They chain through the batch directory, so any
one can be re-run alone or skipped and done by hand, and only `fetch` touches
the network.

Nothing needs installing: copy the `python/` directory and run it. It loads
nothing and chooses nothing, which matters most for FRBs, where a human keeps
roughly a quarter of the candidates for reasons the source data does not
record. [Full guide](https://nedkit.sidereal.software/transients/).

## Installing the macros

The short version, assuming a stock XNEdit:

```sh
# Shared subroutines, available in every macro from startup onward.
cat macros/lib/*.nm >> ~/.xnedit/autoload.nm
```

Menu commands are a separate step, because XNEdit keeps them inside its
preferences file rather than as loose files on disk. Open a `.nm` file from
`macros/commands/`, copy the body, and paste it into
**Preferences > Default Settings > Customize Menus > Macro Menu**, then
**Preferences > Save Defaults**.

[Installing macros](https://nedkit.sidereal.software/installing-macros/) covers both paths
properly, including where the config directory actually lives and how to
distribute a whole menu at once instead of pasting commands one by one.

## Writing macros

[The macro language reference](https://nedkit.sidereal.software/xnedit-macro-reference/)
covers the built-in subroutines and variables, the action routines, and the
behaviors that will waste an afternoon if you don't know about them. Read its
"Read this first" section before writing anything that touches the whole
buffer.

`macros/commands/trim-trailing-blanks.nm` and `macros/lib/text.nm` are the
smallest working examples of each kind, so copy their shape.

## Cleaning up a table pasted from a PDF

1. Get rid of the tabs: select the whole file and run it through `expand` with
   **Shell > Filter Selection**.
2. **Normalize Characters** rewrites the dashes, quotes, spaces and ligatures
   that only look like their ASCII counterparts, and reports whatever non-ASCII
   it deliberately left alone.
3. **Fold Letters to ASCII**, if the accented and Greek letters should go too.
   `Balázs` becomes `Balazs` and `α` becomes `a`, keeping case. Both folds are
   irreversible.
4. Read the file through and fix whatever needs fixing by hand.
5. Put the field boundaries in with **Pipe at Cursor Column**, one column at a
   time, or **Pipe at Columns**, several in one pass.
6. **Pad Columns** pads every field out to the width of the widest value in its
   column, so the finished file is square.
7. **Trim Trailing Blanks**, if you would rather the rows did not all end in
   the same place.

You name the columns yourself, because nothing here works them out for you. The
letters get fixed before the boundaries are chosen, since a replacement that
changes how many characters are on a line moves every column to its right, and
the padding goes last because every edit before it changes a width.

[Cleaning up a pasted table](https://nedkit.sidereal.software/cleaning-pdf-tables/)
works the sequence through on a real file, and
[Character replacements](https://nedkit.sidereal.software/character-replacements/)
lists every character the two rewriting commands touch.

## Requirements

| Requirement | Detail |
| --- | --- |
| Platform | macOS. Nothing else is in scope |
| Editor | [XNEdit](https://github.com/unixwork/xnedit) 1.6 or newer, built from source |
| X server | XQuartz |
| Python | 3.9, standard library only |

XNEdit is a fork of NEdit 5.7 with Unicode support and antialiased text. It is
a different program from classic NEdit and keeps its settings in `~/.xnedit/`
rather than `~/.nedit/`, so if a macro here misbehaves, check which editor is
running before you start debugging the macro.

There are no prebuilt macOS binaries, so XNEdit gets built from source. The
dependencies are all in Homebrew:

```sh
brew install --cask xquartz
brew install openmotif
make macos          # from a checkout of xnedit
```

3.9 is the newest interpreter on the team's machines, so no `match` statements,
no `X | Y` unions in annotations, and nothing that needs an install the team
can't perform.

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

It also fails when a macro has changed without
`uv run python tools/gen_docs.py` being run, so the documentation cannot drift
away from the macros it describes.

Tests that drive the editor need XNEdit on `$PATH`, or `NEDKIT_XNEDIT` pointing
at the binary, and an X display. Without either they skip, so set
`NEDKIT_REQUIRE_XNEDIT=1` when a green run has to mean something.
[Running the tests](https://nedkit.sidereal.software/testing/) covers building
an XNEdit to test against, and why the run flickers windows on screen.

A new command needs at least one case under `tests/fixtures/<command>/<case>/`,
holding `input.txt` and the `expected.txt` it should produce; the suite fails on
any command that has none. Harness code in `src/nedkit/` runs on current Python.
Everything else stays on 3.9, which `tests/test_python_version.py` checks
against a real 3.9 that uv fetches.

## License

MIT. See [LICENSE](LICENSE).
