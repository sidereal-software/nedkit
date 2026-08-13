# CLAUDE.md

Context for agents working in this repo.

## What this is

Tools for the NED team at IPAC (NASA/IPAC Extragalactic Database). Their work
is largely reading and reshaping text files by hand. Two kinds of deliverable:

1. **XNEdit macros** (the main one) in `macros/`
2. **Python utilities** for jobs too large to run inside the editor

## The editor is XNEdit, not NEdit

This matters more than it sounds. Three editors share the same macro language
and get confused for each other constantly:

| Editor | Config directory | Notes |
| --- | --- | --- |
| **XNEdit** (this repo's target) | `~/.xnedit/` | Motif/X11 fork of NEdit 5.7 |
| NEdit 5.7 (classic) | `~/.nedit/` | The original |
| nedit-ng | Qt config dir, `config.ini` | Qt rewrite, unrelated file format |

XNEdit is <https://github.com/unixwork/xnedit>, latest tagged release 1.6.3
(March 2025). It uses the same preferences format and the same `nedit` X
resource app-name as NEdit 5.7, so NEdit settings are drop-in compatible except
for font configuration.

Do not cite nedit-ng documentation for anything file-location related. The
macro language docs are close enough to be useful, the config layout is not.
Prefer XNEdit's own docs at <https://www.unixwork.de/xnedit/doc/html/>.

### Files in `~/.xnedit/`

- `nedit.rc` - preferences, in X resource file format. This is where Macro
  **menu** items live, under the `nedit.macroCommands` resource.
- `autoload.nm` - macros and subroutine definitions executed at startup. Not
  created automatically; you make it yourself.
- `nedit.history` - recently opened files.

`XNEDIT_HOME` overrides the directory, not `NEDIT_HOME` - XNEdit renamed the
variable and ignores the old one. The client program for server mode is `xnc`,
not `nc`.

## Macro language gotchas

The language is awk-like: dynamic strings, associative arrays, C-style control
flow. Full reference in `docs/xnedit-macro-reference.md`. The ones that cause
real bugs:

- **Integer arithmetic only.** 32-bit signed, range -2147483647 to 2147483647.
  There is no floating point at all. Anything involving coordinates, fluxes, or
  redshifts has to shell out or move to Python. Do not try to fake it with
  scaled integers unless the range is genuinely safe.
- **`replace_in_string()` returns `""` when it matches nothing.** Not the
  original string. Pass `"copy"` as the fifth argument to get the input back
  instead. Forgetting this in a whole-buffer rewrite deletes the file.
- **Backslashes double inside macro strings.** A regex `\s` is written
  `"\\s"`, because the string literal consumes one level of escaping first.
- **`define` cannot nest** and cannot appear inside a menu item definition.
- Variables starting with `$` are global and persist across calls. Plain
  identifiers are local to the subroutine or menu item.
- `^` and `$` anchor to line boundaries, not string boundaries, so multi-line
  buffer rewrites with `[ \t]+$` work as expected.
- Array element count is `arr[]` with no index. Iterate with `for (k in arr)`.

## Distributing macros

Two different mechanisms, and mixing them up is the usual source of "the macro
isn't showing up":

- **Subroutine libraries** (`macros/lib/`) are plain `.nm` files appended to
  `~/.xnedit/autoload.nm`. They define reusable subroutines and add nothing to
  any menu.
- **Menu commands** (`macros/commands/`) have to end up inside `nedit.rc` as
  part of the `nedit.macroCommands` resource. Either paste them through
  **Preferences → Default Settings → Customize Menus → Macro Menu**, or ship an
  `.rc` fragment and load it with `xnedit -import file` followed by
  **Preferences → Save Defaults**.

The `nedit.macroCommands` format is one entry per command:

```
nedit.macroCommands: \
	Menu>Item Name:Ctrl+Alt+C::R: {\n\
		macro_body()\n\
	}\n\
```

Fields are colon-separated: menu path (`>` for submenus), accelerator,
mnemonic, flags (`R` means requires a selection). Every line inside the macro
body ends with a literal `\n\` continuation, and the last line of the whole
resource drops the trailing backslash. Backslashes in the macro source double
on the way in, so `"[ \t]+$"` is written `"[ \\t]+$"` here. `-import` merges
with the commands already installed rather than replacing them.

## Python constraints

- **3.9 is the ceiling.** No `match`, no PEP 604 `X | Y` unions at runtime.
  PEP 585 builtin generics (`list[str]`) are fine in annotations.
- **Standard library only.** The team cannot reliably install packages.
- **macOS only** for now. Open text files with an explicit `encoding`, since
  NED data files are not reliably UTF-8 and 3.9 will happily guess wrong.

The one exception is `src/nedkit/`, the test harness, which nobody on the team
runs and which `pyproject.toml` puts on a current Python.
`tests/test_python_version.py` draws the line by location: every `.py` outside
`src/nedkit/` and `tests/` is compiled by a real 3.9 that uv fetches. Move the
harness and that test tells you to update it.

## Tests

`uv run pytest`. Add `-m "not xnedit"` for the static checks alone.

The macro tests drive a real XNEdit through `xnedit -do '<macro>' file`, so
they need the binary (on `$PATH` or in `NEDKIT_XNEDIT`) and an X display. They
skip without one unless `NEDKIT_REQUIRE_XNEDIT=1` is set. Three things about
that mechanism are worth knowing before writing a test:

- **A failing macro hangs.** The error goes into a modal dialog and waits
  forever, so every run has a timeout and the harness appends a sentinel to
  prove the macro reached its last line.
- **`dialog()` is shadowed.** A user-defined subroutine wins over the built-in
  of the same name, so the harness redefines `dialog()` in `autoload.nm` to
  print instead of block. `MacroRun.dialogs` is what the macro would have
  shown. Anything else interactive needs the same treatment before it can be
  tested.
- **Fixtures are bytes.** `tests/fixtures/<command>/<case>/` holds `input.txt`
  and `expected.txt`, compared without decoding, and `.gitattributes` marks the
  tree `-text` so git cannot normalise the whitespace under test. Every command
  needs at least one case; the suite fails on one that has none.

Two XNEdit behaviours the fixtures pin, because both are silent: a file that
is not valid UTF-8 gets locked rather than re-encoded, so a macro runs and
changes nothing, and a leading BOM lives outside the buffer, so a macro never
sees it and saving puts it back.

## Conventions

- One file per menu command in `macros/commands/`, named after the command in
  kebab-case, with a header comment giving the menu path, whether a selection is
  required, and what the command does.
- Macro files are `.nm` and stay LF-only, enforced by `.gitattributes`.
- Test destructive macros against a copy of a real file first.

## Documentation

The docs site is Material for MkDocs, built and deployed by
`.github/workflows/docs.yml` on every push to `main`, and served at
<https://nedkit.sidereal.software>. `mkdocs.yml` sets `strict: true`, so a
broken link or a page missing from the nav fails the build rather than going
quietly missing from the site.

Preview it locally with `uv run --group docs mkdocs serve`.

### Docs and code stay in step

**Generate documentation from the source whenever the source can carry it.**
Hand-copying anything out of a macro into a page is how the two drift apart.

`tools/gen_docs.py` reads the macros and rewrites the regions marked
`<!-- BEGIN GENERATED: name -->` ... `<!-- END GENERATED: name -->` in three
pages. Prose outside the markers is hand-written and never touched. It parses
headers with `nedkit.macro.parse`, the same function the tests use, so there is
one definition of what a macro header is rather than two that can disagree.

| Page | Generated from |
| --- | --- |
| `docs/commands.md` | the header comment and body of every `macros/commands/*.nm` |
| `docs/subroutines.md` | the comment above every `define` in `macros/lib/*.nm` |
| `docs/character-replacements.md` | the `fix[]` / `nam[]` table inside `normalize-characters.nm` |

So: **change a macro, then run `uv run python tools/gen_docs.py` and commit the
regenerated pages in the same commit.** Both `uv run pytest` and CI fail when a
committed page has drifted from the macro it came from.

This puts two formatting contracts on the macro files. Breaking either one
silently produces wrong docs, so keep them:

- A command's header comment is the run of `#` lines the file opens with. The
  first line is the title, the prose runs from there to the `Menu Entry:`
  block, and everything after that block is install boilerplate the docs do not
  repeat. Write the prose so it reads as documentation, because it becomes the
  documentation.
- In the character table, a group heading is the comment line directly above a
  `fix[...]` line with no blank line between them. That is the only thing
  separating a heading from ordinary prose earlier in the file.

When Python utilities land, document them with numpydoc docstrings and render
the API reference with `mkdocstrings`, rather than describing the functions
again by hand.

### Writing prose

**Use the `humanizer` skill on any prose written for the docs, the README, or a
macro header comment.** It strips the patterns that make writing read as
machine-generated. Reference and API text stays plain and neutral; that is the
correct human voice for it, so do not let the skill talk you into adding
personality there.

Never use an em dash. Headings are sentence case.

## Git

**Every commit follows [Conventional Commits](https://www.conventionalcommits.org):
`type(scope): summary`.** The summary is imperative and lower case, with no
trailing period.

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`.
Scopes in this repo are usually `macros`, `docs`, `tools` or `ci`, or the name
of a single macro when a change is confined to one:

```
feat(macros): add align-columns for pipe-delimited tables
fix(normalize-characters): use case-sensitive search for the table
docs: describe the two-macro workflow for pasted tables
ci: build the docs site on pull requests without deploying
```

A change to a macro and the pages `tools/gen_docs.py` regenerates from it
belong in the same commit, so `main` never has docs that disagree with the
macros.

Breaking changes take a `!` before the colon, as in `feat(macros)!: ...`, with
the detail in the body.

## Platform

**XNEdit runs locally on the Macs, on XQuartz.** It is not forwarded from a
remote Linux host, so `~/.xnedit/` is on the user's own machine and install
instructions point there.

There are no prebuilt macOS binaries, so it is built from source. XNEdit's
makefile has a `macos` build config, and the dependencies are in Homebrew:

```sh
brew install --cask xquartz
brew install openmotif
make macos
```

Being an X11 app under XQuartz explains some behavior that otherwise looks like
a bug: the menu bar is in the window rather than at the top of the screen,
copy and paste go through the X selection rather than the macOS clipboard, and
`t_print()` output lands in the terminal that launched `xnedit`.

macOS is the only platform in scope. Don't add Windows caveats to docs or code
unless asked.

## Open questions

- Whether the team wants a shared macro menu everyone syncs, or individuals
  picking commands à la carte.
- What the actual parsing tasks are, which is what should drive the first real
  macros.
