# nedkit

Small tools for the NED team at IPAC.

**Documentation: <https://nedkit.sidereal.software>**

Most of it is XNEdit macros. Reshaping a data file by hand is slow and easy to
get subtly wrong, and a macro does the same edit the same way every time.
Python utilities live here too, for the jobs too big to run inside the editor.

## Installing the macros

Every command is in one file that XNEdit imports in a single pass. The import
calls `xnedit`, so build one and put it on your `$PATH` first:
[Requirements](#requirements) below has the build, and
[getting started](https://nedkit.sidereal.software/getting-started/) walks it
with the `PATH` line spelled out.

```sh
curl -O https://nedkit.sidereal.software/nedkit-macros.rc
xnedit -import nedkit-macros.rc
```

From a checkout the file is already on disk, so the download step drops out:

```sh
xnedit -import docs/nedkit-macros.rc
```

That opens an editor window and holds the terminal until you close it. Run
**Preferences > Save Defaults** in the window, click **OK**, and the commands
are installed for good.

Menu commands need the import step because XNEdit keeps them inside its
preferences file rather than as loose files on disk, and importing merges them
into whatever is installed already. The file is generated from
`macros/commands/`, so it carries whatever the macros currently say. One
command at a time still works too, through
**Preferences > Default Settings > Customize Menus > Macro Menu**.

The shared subroutines in `macros/lib/` install separately, and no command
here calls one:

```sh
cat macros/lib/*.nm >> ~/.xnedit/autoload.nm
```

[Getting started](https://nedkit.sidereal.software/getting-started/) walks the
same route from a machine with no XNEdit on it, and [installing
macros](https://nedkit.sidereal.software/installing-macros/) covers both paths
properly, including where the config directory actually lives.

## Cleaning up a table pasted from a PDF

1. **Expand Tabs** writes the spaces each tab stands for, leaving the columns
   where they sit on screen.
2. **Normalize Characters** rewrites the dashes, quotes, spaces and ligatures
   that only look like their ASCII counterparts, and reports whatever non-ASCII
   it deliberately left alone.
3. **Fold Letters to ASCII**, if the accented and Greek letters should go too.
   `Balázs` becomes `Balazs` and `α` becomes `a`, keeping case. Both folds are
   irreversible.
4. Read the file through and fix whatever needs fixing by hand.
5. Put the field boundaries in with **Pipe at Cursor Column**, one column at a
   time, or **Pipe at Columns**, several in one pass.
6. **RA to NED Form** and **Dec to NED Form** on the two coordinate columns,
   picked out with a rectangular selection. `00:10:09.97` becomes `001009.97`,
   and `15:34:09.66` becomes `+153409.66` with the sign written out. Do the
   rightmost column first, since converting one shortens it and shifts
   everything to its right.
7. **Pad Columns** pads every field out to the width of the widest value in its
   column, so the finished file is square.
8. **Trim Trailing Blanks**, if you would rather the rows did not all end in
   the same place.

You name the columns yourself, because nothing here works them out for you. The
letters get fixed before the boundaries are chosen, since a replacement that
changes how many characters are on a line moves every column to its right, and
the padding goes last because every edit before it changes a width.

[Cleaning up a pasted table](https://nedkit.sidereal.software/cleaning-pdf-tables/)
works the sequence through on a real file, and
[Character replacements](https://nedkit.sidereal.software/character-replacements/)
lists every character the two rewriting commands touch.

## Layout

| Path | Contents |
| --- | --- |
| `macros/commands/` | One file per XNEdit **Macro** menu command |
| `macros/lib/` | Shared subroutines, loaded at startup through `autoload.nm` |
| `python/` | `ned-transients`, which prepares the monthly SNe, FRB and GRB load |
| `docs/` | Sources for the documentation site |
| `samples/` | A real job, before and after, and the list of what is still done by hand |
| `tools/` | `gen_docs.py`, which regenerates the reference pages, the install file and the sample downloads from the sources |
| `src/nedkit/`, `tests/` | The test harness, which nobody on the team runs |

## ned-transients

Fetches the new supernovae, fast radio bursts and gamma-ray bursts from the
Transient Name Server and Swift XRT, and writes the loadstatus file, the
ptables, the directory tree and the Jira ticket body that the procedure
otherwise asks someone to build by copying last year's.

One command per step, so you can run the parts that help:

```sh
NT=~/nedkit/python/ned-transients      # wherever you copied python/ to
cd /nedefs/Project/Production/dev/data.tables

python3 $NT scaffold   --root . --batch a
python3 $NT fetch      --root . --batch a --since 2025-08-01 --until 2026-02-05
python3 $NT ptable     --root . --batch a
python3 $NT loadstatus --root . --batch a
python3 $NT jira       --root . --batch a
```

`prepare` runs all five at once. They chain through the batch directory, so any
one can be re-run alone or skipped and done by hand, and only `fetch` touches
the network.

Nothing needs installing: copy the `python/` directory and run it. It loads
nothing and chooses nothing, which matters most for FRBs, where a human keeps
roughly a quarter of the candidates for reasons the source data does not
record. [Full guide](https://nedkit.sidereal.software/transients/).

## Writing macros

[The macro language reference](https://nedkit.sidereal.software/xnedit-macro-reference/)
covers the built-in subroutines and variables, the action routines, and the
behaviors that will waste an afternoon if you don't know about them. Read its
"Read this first" section before writing anything that touches the whole
buffer.

`macros/commands/trim-trailing-blanks.nm` and `macros/lib/text.nm` are the
smallest working examples of each kind, so copy their shape.

## Requirements

| Requirement | Detail |
| --- | --- |
| Platform | macOS. Nothing else is in scope |
| Editor | [XNEdit](https://github.com/unixwork/xnedit), built from source. 1.6 or newer works; the instructions and CI both pin `v1.6.3`, which is what gets tested |
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

cd ~
git clone https://github.com/unixwork/xnedit.git
cd xnedit
git checkout v1.6.3
make macos

export PATH="$HOME/xnedit/source:$PATH"
```

`v1.6.3` is the release the tests and CI are pinned to. Checking a tag out
makes git answer with a paragraph about being in "detached HEAD" state, which
it says for any tag and which means nothing has gone wrong. `make macos` leaves
the binary at `source/xnedit` and puts nothing on your `$PATH`, hence the
`export`, and the `cd ~` is what makes that line name the right directory. It
lasts until you close the terminal, so put the same line in `~/.zshrc` to keep
`xnedit` past this shell.

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
