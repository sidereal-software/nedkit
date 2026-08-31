# CLAUDE.md

Context for agents working in this repo.

## What this is

Tools for the NED team at IPAC (NASA/IPAC Extragalactic Database). Their work
is largely reading and reshaping text files by hand. Two kinds of deliverable:

1. **XNEdit macros** (the main one) in `macros/`
2. **Python utilities** in `python/`, for jobs too large to run inside the
   editor. So far one: `ned-transients`, which prepares the monthly SNe, FRB
   and GRB load. See [the transients page](docs/transients.md).

## The editor is XNEdit, not NEdit

XNEdit and classic NEdit share a macro language and get confused for each
other. They keep their settings in different directories:

| Editor | Config directory |
| --- | --- |
| **XNEdit** (this repo's target) | `~/.xnedit/` |
| NEdit 5.7 (classic) | `~/.nedit/` |

XNEdit is <https://github.com/unixwork/xnedit>, latest tagged release 1.6.3
(March 2025). It uses the same preferences format and the same `nedit` X
resource app-name as NEdit 5.7, so NEdit settings are drop-in compatible except
for font configuration.

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
- **`set_cursor_pos()` clamps for you.** Asking for position 100000 in a 6-byte
  buffer leaves `$cursor` at 6, on XNEdit and on NEdit 5.7 alike: both reach
  the same `TextDSetInsertPosition`. The `if (saved_cursor > $text_length)`
  guard in the four rewriting commands is therefore unreachable, and so is
  Fold's `gpos` clamp, which now sits below a guard that turns a locked buffer
  away before any offset is taken. All five sites say so in a comment now,
  because two audits in a row filed them as an untested coverage gap. They are
  unreachable, not untested.
- **`replace_range()` is a silent no-op on a locked buffer.** It rings the bell
  and returns, raising nothing, so a command that computes and then reports
  what it computed will report work that never happened. **`$read_only` is the
  test, not `$locked`.** `replaceRangeMS()` refuses on `IS_ANY_LOCKED`, which
  is exactly what `$read_only` returns, while `$locked` is only
  `IS_USER_LOCKED`:

  | buffer | `$locked` | `$read_only` | write lands |
  | --- | --- | --- | --- |
  | ordinary | 0 | 0 | yes |
  | cannot be read as UTF-8 | 1 | 1 | no |
  | no write permission | **0** | 1 | no |

  The encoding lock sets the user bit too (`file.c:886`), which is what makes
  `$locked` look right until someone opens a file they cannot write. All six
  commands guard on `$read_only` and refuse rather than compute.
- **A macro compiles into 4096 instructions and no more.** `PROGRAM_SIZE` in
  `interpret.c:63` sizes `static Inst Prog[PROGRAM_SIZE]` at `:182`, one fixed
  array, and every route into the editor goes through the same `ParseMacro()`:
  `-do`, a menu command out of `nedit.rc`, `autoload.nm`, Load Macro File. Over
  the limit you get `macro too large` at parse time, naming whichever line it
  stopped on. Measured against XNEdit 1.6.3:
  - An `arr["k"] = "v"` assignment costs **9 instructions**, so a body with no
    logic in it holds about **450** of them. Exactly: 455 assignments compile
    in a `-do` body and 456 do not, which pins the cost at 9 with no base
    overhead. Inside a `define` it is 454, the `return` taking the last slot.
  - `normalize-characters.nm` uses roughly 45% of its budget and
    `fold-letters-to-ascii.nm` roughly 69%. Do not trust a figure written down
    here for the margin: every edit to a command moves it, and the one above
    was already stale within a day. `test_command_has_room_to_grow` measures it
    against the editor instead, and fails while there is still room to act.
  - Each `define` is compiled separately and gets its own fresh 4096. 800
    assignments split over two subroutines load fine, so a table too big for a
    menu command could live in `macros/lib/` and fill a `$global` array. That
    costs a command its self-contained install, which is why the character
    tables were split across two commands instead.

  This is what a table has to be budgeted against. Measure with a throwaway
  bisect rather than guessing, and give the run the full timeout: XNEdit
  buffers stdout, so a run killed early loses its output and a slow-but-fine
  macro looks exactly like a rejected one.

  Five more fixed-size limits sit behind the macro language, none of them
  documented upstream and all of them inherited unchanged from NEdit 5.7. The
  dangerous one is `SEARCHMAX` 5119: a `"literal"` or `"case"` search whose
  pattern is 5119 bytes or longer returns -1, which is also the answer for a
  pattern that is not there, and the source comment admits that "returning
  search failure here is cheating users". Regex searches do not go through
  that path. The others are `MAX_ITEMS_PER_MENU` 400 per menu, `STACK_SIZE`
  1024, `MAX_SYM_LEN` 100 and `LOOP_STACK_SIZE` 200. The table is on
  [the macro language page](docs/xnedit-macro-reference.md).
- **`toupper()` and `tolower()` destroy non-ASCII text.** On 1.6.3 they walk
  the string with no locale guard, so the 8 bytes of `αβ Éx` come back from
  `toupper()` as 5 bytes and `tolower()` returns 1. Writing that into the
  buffer means the save stops on a modal dialog and the file is left empty. The
  `uppercase()` and `lowercase()` action routines are correct on the same text.
  Since NED data is full of accented names and Greek letters, treat both
  functions as ASCII-only.

## Distributing macros

Two different mechanisms, and mixing them up is the usual source of "the macro
isn't showing up":

- **Subroutine libraries** (`macros/lib/`) are plain `.nm` files appended to
  `~/.xnedit/autoload.nm`. They define reusable subroutines and add nothing to
  any menu.
- **Menu commands** (`macros/commands/`) have to end up inside `nedit.rc` as
  part of the `nedit.macroCommands` resource. Either paste them through
  **Preferences > Default Settings > Customize Menus > Macro Menu**, or ship an
  `.rc` fragment and load it with `xnedit -import file` followed by
  **Preferences > Save Defaults**.
- **Background menu commands** are the same thing in a different resource,
  `nedit.bgMenuCommands`, installed through **Customize Menus > Window
  Background Menu** and posted by a right-click in the text. Same entry format.
  Undo/Redo/Cut/Copy/Paste are not built in: they are that resource's default
  value, so they survive the dialog (which lists them) and an `-import` (which
  adds to the list already loaded), and they vanish the moment a hand-written
  `nedit.rc` sets the resource to something else. A command can live in both
  menus, which is what the `Install In:` header field records, and it is then
  pasted into both dialogs. Right-clicking does not move the insert cursor, so
  a command that reads `$column` needs a left-click first.

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

**No console entry points**, for the same reason. `python/ned-transients` is a
shim that puts its own directory on `sys.path` and calls `main()`, so the whole
`python/` directory copies anywhere and works. Tests import it by inserting
`python/` on the path, and mkdocstrings reaches it through `paths: [python]`
in `mkdocs.yml`.

**One command per step of the procedure**, so a step that does not help can be
skipped and done by hand: `scaffold`, `fetch`, `ptable`, `loadstatus`, `jira`,
with `prepare` calling the same five functions in order through the `STEPS`
table. They communicate through the batch directory rather than through each
other, which is what keeps them independently runnable:

- `fetch` records its date range in `_raw/window.txt`, and `ptable` reads it
  back. TNS filters server-side but Swift publishes one undated table, so a
  `ptable` run that guessed a different window would silently build the wrong
  file.
- `loadstatus` derives which refcodes to register from which `.mod` files
  exist. `--only` narrows that and never widens it: a refcode with no ptable
  behind it registers an empty load and then asks for a Jira ticket giving it
  an author.

When adding a step, put it in `STEPS` and give it a subparser; a test asserts
the two agree.

### What the transients tool learned the hard way

Four findings that cost real investigation and are not recoverable from the
code alone:

- **TNS blocks a few tool names by User-Agent, and nothing more.** `curl/*`
  and `python-requests/*` get 403; urllib's own default, an honest
  `nedkit/0.1 (+url)`, and a Chrome string all get 200. The first version of
  this code spoofed Chrome on the strength of a `curl` 403 generalised into
  "it wants a browser", which was never measured and was wrong. Do not
  reintroduce a fake User-Agent. Separately, TNS answers **429** past its
  60-second request quota, which `sources.fetch` reports as a quota rather
  than as an outage.
- **TNS paginates**, and taking the first page silently truncates. A
  ten-month window is thousands of rows against a 500-row page.
- **The refcode month is the download date, not the window.** The real
  `FRB.2026.03.31.mod` covers December 2024 to September 2025 and loads under
  `2026FRB...C...0000.`, where `C` is March.
- **Alternative sources were surveyed and rejected.** HEASARC's `swiftgrb`
  stops at December 2012; no other HEASARC GRB table is a live position feed;
  FRBSTATS is gone, its domain parked; the TNS bulk `tns_public_objects` files
  really do need credentials, unlike the search export. And the refcodes record
  provenance (`obtained from wis-tns.weizmann.ac.il`, credited to the TNS
  Collaboration and the Swift SDC), so reading the same objects off a broker
  would make NED's own record of their origin untrue. Full table in
  [the transients page](docs/transients.md).
- **There is no API key, so TNS has two scrape routes, not one.** The CSV
  export first, the ordinary results page second; the page marks its cells
  `class="cell-name"` and friends, and the two were checked against a live
  month at 132 records each, identical. The fallback announces itself and the
  cached file's extension records which route answered, so `_raw/tns-frb.html`
  is itself the sign that the CSV route broke. A 429 does not fall back: the
  quota covers both. [GOATS](https://github.com/gemini-hlsw/goats) scrapes TNS
  the same way and sends `GOATS.TNSClient/1.0`, which independently confirms
  the honest-User-Agent finding.
- **Do not replace the scraper with the TNS API, and do not extract it into a
  library.** The API is shaped for "tell me about this object": `get/search`
  takes a name or a position, `get/object` returns one object. There is no
  date-range-with-full-rows endpoint, so a month would cost one request per
  object against a quota. Only the bulk daily-delta files would replace
  scraping, and those need the bot account. As for a library,
  [`transientNamer`](https://github.com/thespacedoctor/transientNamer) already
  scrapes the same endpoint and is maintained, but it could not do this job
  even with `pip` available: its search takes no object-type filter, so it
  cannot ask for FRBs or for classified supernovae, and its window is
  `discInLastDays` rather than two dates, so it cannot rebuild a past batch.
  It also parses with one regex over the row, which fixes the column order;
  `sources.py` keys on each cell's class instead and has a test proving a
  reordered table still reads. **Installing BeautifulSoup would change
  nothing** - `transientNamer`'s TNS search uses `requests` and `re`, and the
  parser here needs no third-party anything.
- **FRB row selection cannot be derived from the TNS export.** The real file
  keeps 33 of 142 candidates and six candidate rules were tried and rejected;
  the list is in `sources.Cluster`'s docstring. Do not add a seventh on a
  hunch. GRBs, by contrast, need no selection at all: the real GRB file is a
  gapless contiguous slice of the Swift table.

## Tests

`uv run pytest`. Add `-m "not xnedit"` for the static checks alone.

Two markers, and both are backed by an environment variable rather than by the
marker alone. `xnedit` skips without a binary unless `NEDKIT_REQUIRE_XNEDIT=1`.
`network` reaches the live TNS and Swift sites and skips unless
`NEDKIT_NETWORK=1`:

```sh
NEDKIT_NETWORK=1 uv run pytest -m network
```

`.github/workflows/sources.yml` runs them nightly, and `tests/test_sources_live.py`
is where they live. They check the live sites against a corpus: the objects in
`tests/fixtures/transients/` came off a real load and are still published, so
re-fetching them and getting different values means an upstream format moved.

**"Cannot reach" is not "has changed."** A 403, a 429 or a timeout skips; only
a site that answers and says something different fails. A job that reddens for
someone else's outage is one people learn to ignore.

That distinction is load-bearing, because **TNS refuses GitHub's runners**.
Measured from a runner with the same `nedkit/0.1` User-Agent that gets 200 from
a laptop:

```
200  https://www.swift.ac.uk/xrt_positions/...
403  https://www.wis-tns.org/search?format=csv&num_page=1
```

So the block is by origin, not by client. The consequence is that **CI watches
Swift and cannot watch TNS**; the TNS half of the corpus is only checked when
somebody runs `NEDKIT_NETWORK=1 uv run pytest -m network` from an ordinary
network. A runner inside IPAC would close that gap if it ever matters enough.

**Do not deselect a marker through `addopts`.** It reads as though it works and
does not: a `-m` on the command line *replaces* the one in `addopts` rather than
combining with it, so `ci.yml`'s `pytest -m "not xnedit"` silently opted the
network test back in and CI went red. An explicit `pytest.skip` on an
environment variable is the thing no invocation can override, which is why both
markers use one.

### Getting an XNEdit to test against

The macro tests drive a real XNEdit through `xnedit -do '<macro>' file`, so
they need the binary and an X display. Without both they skip, and a run that
skips them proves nothing about the macros. **Set `NEDKIT_REQUIRE_XNEDIT=1`
when the result has to mean something**; the skips become errors.

There are no prebuilt macOS binaries, so build one once:

```sh
brew install --cask xquartz          # only needed the first time
brew install openmotif

git clone https://github.com/unixwork/xnedit.git
cd xnedit && git checkout v1.6.3 && make macos
```

That leaves the binary at `source/xnedit`. Point the suite at it:

```sh
export NEDKIT_XNEDIT=/path/to/xnedit/source/xnedit
export NEDKIT_REQUIRE_XNEDIT=1
uv run pytest
```

Anything on `$PATH` as `xnedit` is picked up without `NEDKIT_XNEDIT`.

XQuartz does not need starting by hand. `$DISPLAY` points at a launchd socket,
and connecting to it starts the server. What this does mean is that **the tests
are not headless**: each one opens a real XNEdit window for a second or two, so
a full run flickers windows on screen and steals focus. It is not a failure,
but do not run the suite in the middle of something else. There is no Xvfb on
macOS to hide behind.

A run takes a couple of minutes, nearly all of it XNEdit starting up once per
test. That figure tracks the number of editor-backed tests rather than staying
put, so treat it as an order of magnitude and not a target.

### Writing a test

Three things about the mechanism are worth knowing first:

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

Commands are covered by fixtures. Subroutines have none, so
`test_every_subroutine_is_named_in_a_test` checks that each `define ned_*` at
least gets mentioned somewhere in `tests/`. `tests/test_pipeline.py` runs the
commands in sequence, which is the only place their interaction shows up. It
works from inline bytes rather than from `samples/`, because the sample paste
is tab separated and the pipe commands refuse a buffer with a tab in it.

**A test that cannot fail is worse than no test**, because it is also a claim
that the thing is covered. Three turned up in one day: a blanket idempotency
check that was a no-op for two of the commands, a pipeline re-run that stayed
green because the command under it correctly refused to act, and the
byte-survival check described below. Every one was found by mutating a macro
and watching the suite stay green, and none by reading the test. So when a test
asserts that something *survived*, make it assert first that something
*happened*.

Encoding behaviour is where that bites, because the answer depends on the
locale as much as on the editor. A file that is *entirely* latin-1 decodes
cleanly under a latin-1 locale and is an error under a UTF-8 one, so a fixture
built on one is not portable. Three tests cover it from different ends:

- `unconvertible-byte-locks-the-file` pins the lock, using a file that is valid
  UTF-8 apart from one stray byte. That is an error under any locale, and the
  workflows pin `LANG` so the answer cannot drift.
- `test_command_keeps_a_non_ascii_character_when_it_rewrites_the_buffer` hands
  each command a buffer it genuinely edits, holding a UTF-8 degree sign that no
  table maps, and asserts the buffer changed **before** asserting the character
  survived. Its predecessor asserted only the second half, on a sample that was
  invalid UTF-8 under every locale: the editor locked the buffer,
  `replace_range()` no-opped, the byte survived because nothing was ever
  written, and it passed for all six commands whatever they did. Asserting a
  real rewrite costs the locale independence the old one appeared to have, so
  this test assumes the UTF-8 locale the workflows pin. Under a latin-1 one the
  degree sign decodes as two characters, one of which Fold Letters to ASCII has
  an answer for.
- `test_a_command_does_not_hang_on_a_buffer_xnedit_locked` keeps the old sample
  and asserts what it really proved: the editor locks the buffer, the macro
  comes back rather than raising a dialog nobody can dismiss, and the bytes are
  untouched. XNEdit only, since NEdit 5.7 has no lock to hit.

Do not read a command's own report to settle any of this. A report says what a
command decided to do, and only the bytes say what it did. The two came apart
once already: until all six learned to refuse a locked buffer, Trim Trailing
Blanks would announce two trimmed lines that were still sitting there.

The leading BOM is pinned the same way as the lock: XNEdit lifts it out of the
buffer and puts it back on save.

There are five `xnedit-only` fixtures, and only two of them are about encoding
(the lock and the BOM). The other three are Pad Columns, Pipe at Columns and
Pipe at Cursor Column, where the divergence is arithmetic: XNEdit counts a
column in characters and NEdit 5.7 counts it in bytes, in `$column` and in the
regex engine alike, so a line holding an accented name comes out a place too
wide there. Fold Letters to ASCII is the only command with no marker, which
does not make it fork-independent: the column it reports for a Greek letter is
XNEdit's, and the test pinning that skips on 5.7 in its own body rather than
through a fixture.

The suite skips a marked case when `runner.is_xnedit` is false, decided from
`<binary> -version` rather than from the filename. Reach for the marker only
when a case genuinely turns on the fork; every expected failure left unmarked
is one more reason to stop reading the NEdit job.

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
pages, plus one file it writes whole. Prose outside the markers is hand-written
and never touched. It parses headers with `nedkit.macro.parse`, the character
tables with `nedkit.chartable.character_tables` and the resource format with
`nedkit.rcfile`, all of which the tests use too, so there is one definition of
each rather than two that can disagree.

| Page | Generated from |
| --- | --- |
| `docs/commands.md` | the header comment and body of every `macros/commands/*.nm` |
| `docs/subroutines.md` | the comment above every `define` in `macros/lib/*.nm` |
| `docs/character-replacements.md` | the `fix[]` / `grk[]` / `nam[]` tables in every command that has one |
| `docs/nedkit-macros.rc` | every command, as the file `xnedit -import` reads |

`docs/nedkit-macros.rc` is the install route the docs lead with, and MkDocs
copies it to <https://nedkit.sidereal.software/nedkit-macros.rc>. It is written
for `xnedit -import` and not for `~/.xnedit/nedit.rc`, and the two are not
interchangeable: importing adds, a preferences file replaces. The mechanism,
with the XNEdit routines that decide it, is in `nedkit.rcfile`'s module
docstring. Read that before changing the format or telling anyone to install it
another way.

`nam[]` is optional. `fold-letters-to-ascii.nm` ships without labels because a
second line per entry would not fit in 4096 instructions, and
`nedkit.chartable.label_for` derives the same `U+XXXX NAME` string from the key
with `unicodedata.name()`. A label written in the macro wins, which is what
keeps hand-written text like the `(BOM)` suffix.

So: **change a macro, then run `uv run python tools/gen_docs.py` and commit the
regenerated pages in the same commit.** Both `uv run pytest` and CI fail when a
committed page has drifted from the macro it came from.

This puts two formatting contracts on the macro files. Breaking either one
silently produces wrong docs, so keep them:

- A command's header comment is the leading contiguous run of `#` lines, ending
  at the first line that is not one. The first line is the title, the prose
  runs from there to the `Menu Entry:` block, and everything after that block
  is install boilerplate the docs do not repeat. Write the prose so it reads as
  documentation, because it becomes the documentation.

    A blank line has to separate the header from the body, and
    `nedkit.checks.check_header_separated` enforces it. That blank line is the
    only thing marking where the header stops, so with it in place **a command
    body may open with a comment of its own**. Without it, that comment reads
    as more header and is dropped from the body, which is what silently ate two
    commands' opening divider line on the paste-in block in `docs/commands.md`.
- In the character table, a group heading is the comment line directly above a
  `fix[...]` or `grk[...]` line with no blank line between them. That is the
  only thing separating a heading from ordinary prose earlier in the file.

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

**Prefer a table to paragraphs whenever the content is really a list of facts.**
Two things compared, symptoms against causes, options against what each one
costs: all of those read faster as a table and are easier to keep true, because
a missing cell is obvious where a missing clause is not. Keep prose for
reasoning, where the connective tissue between sentences is the point. A table
of arguments is not a table.

**`>` separates menu levels and `→` means "becomes".** So
`Preferences > Default Settings > Customize Menus`, and `α → a`. Menus take the
plain character because a macro header cannot sensibly use anything else, and
`tools/gen_docs.py` publishes those headers as a third of the site: one
convention here means one convention everywhere. It is also how XNEdit spells a
menu path itself, in `NED>Pipe at Columns`. The arrow keeps its own glyph
because it says something different, and flattening the two would lose that.

## Git

**Every commit follows [Conventional Commits](https://www.conventionalcommits.org):
`type(scope): summary`.** The summary is imperative and lower case, with no
trailing period.

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`.
Scopes in this repo are usually `macros`, `docs`, `tools` or `ci`, or the name
of a single macro when a change is confined to one:

```
feat(macros): add pipe-at-columns for fixed-width tables
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

Closed: what the actual parsing tasks are. Six commands have shipped, and
`samples/README.md` states the rest of the job concretely, as the gap between
`A13L.mod.before` and `A13L.mod.after`. Anything added to `macros/commands/`
should close part of that list.
