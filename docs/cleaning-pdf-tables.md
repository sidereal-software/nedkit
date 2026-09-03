# Cleaning up a pasted table

Text copied out of a journal PDF arrives with two problems. The columns are
separated by whatever the PDF happened to emit, and many of the characters are
not the ASCII characters they look like. A declination that reads
`-00:46:03.66` on screen often starts with U+2013 EN DASH, and nothing
downstream that expects a minus sign will match it.

The order to work in:

1. get rid of the tabs, with **Expand Tabs**
2. **Normalize Characters**
3. **Fold Letters to ASCII**, if the accented and Greek letters should go too
4. read the file through and fix what needs fixing by hand
5. put the field boundaries in with **Pipe at Cursor Column** or **Pipe at
   Columns**
6. **RA to NED Form** and **Dec to NED Form** on the coordinate columns
7. **Pad Columns**
8. **Trim Trailing Blanks**, if you would rather the rows did not all end in
   the same place

The coordinates come after the pipes rather than before. Converting one
shortens it, which moves every column to its right, so doing it first would
mean reading the column positions off the screen twice.

Two facts fix that order. A replacement that changes how many characters are on
a line moves every column to its right, so the letters get sorted out before
the boundaries are chosen. And every edit changes a width, so the padding goes
last.

## Where the pipes go

You say where the fields begin, because nothing here can work it out. Turn on
**Preferences > Statistics Line**: the `C:` field is the column the cursor is
in, counting from 0, and that is the number both commands take.

Put the cursor on a blank column and run **Pipe at Cursor Column** to do that
one boundary on every line at once:

```
SDSS001009      00:10:09.97
SDSS004054      00:40:54.33
```

with the cursor in column 15 becomes

```
SDSS001009     |00:10:09.97
SDSS004054     |00:40:54.33
```

It is on the right-click menu as well as the Macro menu. Right-clicking does
not move the cursor, though, so left-click the column first.

**Pipe at Columns** asks for the numbers instead, in any order and separated by
spaces or commas, and does the lot in one pass. Its prompt tells you which
column the cursor is in, so you can read one off the screen without the
statistics line.

### Overwrite or insert

Pipe at Columns offers both, on the two buttons of its prompt. Pipe at Cursor
Column always overwrites.

| What happens to | Overwrite | Insert |
| --- | --- | --- |
| The character at that column | Written over, and only where it is a space | Pushed right, along with the rest of the line |
| A row holding something else there | Left as it is, counted and reported | Piped anyway |
| Row width | Unchanged | One character wider per pipe |
| A second run over the same columns | Finds the pipe already there and leaves it | Adds a fresh pipe at every column but the leftmost |

Overwrite is the one for a table already laid out in fixed-width columns, since
it cannot move anything. Insert loses nothing, so it reaches a row with no
blank column to spare:

```
NGC4472 12:29:46.7
IC3583  12:36:44.0
```

Answering `7` and choosing Insert gives

```
NGC4472| 12:29:46.7
IC3583 | 12:36:44.0
```

### Read the report

Both commands print a line per run in the terminal that launched `xnedit`, and
print a marked report there when some rows did not get their pipe. Two cases
are counted and left alone rather than guessed at:

| The row | Why it was skipped |
| --- | --- |
| Holds something other than a space where an overwrite would go | Writing there would destroy a character |
| Ends before the column | Padding it out would invent data |

The report gives a count and the line number of the first one, and either case
usually means the column is a place or two off.

Watch the first one. A column that is blank on almost every row can land inside
a name like `NGC 4472` on the one row where it isn't, and nothing can tell that
apart from a column you meant.

## Squaring the table up

Once the pipes are in, **Pad Columns** makes the file square. It splits every
line on `|`, trims the spaces around each field, and pads the field back out to
the width of the widest value in its column, so

```
Griffin        |12:29:46.7
Smith         |12:36:44.0
```

becomes

```
Griffin|12:29:46.7
Smith  |12:36:44.0
```

It splits on `|` and nothing else. A line with no pipe in it is not a table row
and passes through verbatim, along with blank lines and the `##refcode` header
block, so a file nobody has piped yet comes back untouched. Reading a boundary
out of a run of spaces is the one thing it will not do.

Widths are counted in characters rather than bytes, so `Balázs` is six wide
though it takes seven, and a column holding an accented name comes out as wide
as it looks on screen.

Every column is padded, the last one included, so each row ends in the same
place. A row whose field count differs from the first data row is padded as far
as it goes and then reported, by count and first line number; no empty field is
invented to make it fit.

Run it last. It measures the widest value in each column, and that measurement
holds only until the next edit, whether the edit comes from a command or from
typing. Trim Trailing Blanks is optional and comes after it, trading rows that
all end in the same place for lines that stop at the last real character. It is
also the one command here that cannot move a boundary, since it only ever takes
spaces and tabs off the end of a line.

## Tabs have to go first

The two pipe commands and Pad Columns all refuse a buffer with a tab anywhere
in it. A tab is one character and however many columns it takes to reach the
next tab stop, so on a line holding one there is no answer to what is in column
15, or to how wide a field is.

**Expand Tabs** writes the spaces the tab was already displaying, at the tab
width set in **Preferences > Tab Stops**, so the columns end up where they sit
on screen. Nothing moves.

That is why it comes before Normalize Characters rather than after. Normalize
takes tabs out too, but it writes one space for each, which closes the columns
up.

`expand` through **Shell > Filter Selection** does the same job and is still
there if you want it. The reason to prefer the command is that it counts a
column in characters, so an accented name carries the following tab to the stop
it appears to reach rather than the one its byte count suggests.

The columns come back where they were only because `expand` and XNEdit both put
a tab stop every 8 columns. If **Preferences > Tab Stops** has been changed,
pass the same number, as in `expand -t 4`, or the file comes back with every
column somewhere new.

!!! warning "`expand` needs a UTF-8 locale"

    Under `LANG=C` it does not count a character like an en dash at all, and
    pads as though it were not there. Everything to the right of one on that
    line then lands a column too far over, once per non-ASCII character.

## Why the letters get fixed first

A replacement that changes how many characters are on a line moves every column
to its right. Most are one character for one and move nothing: an en dash
becomes a minus sign, and Greek is deliberately one letter for one. The ones
that widen a row are the ligatures, the ellipsis and `ß` to `ss`.

```
Griﬀin         12:29:46.7
Smith          12:36:44.0
```

Both rows are 25 characters wide, because `ﬀ` is one character, and column 14
is blank on both. Pipe there and then normalize, and the pipe on the widened
row travels right along with everything else on it:

```
Griffin        |12:29:46.7
Smith         |12:36:44.0
```

Those pipes are in columns 15 and 14, so the boundary is no longer a column at
all. Normalize first and the two rows still differ in width, but one column
number finds the boundary on both, which is all the pipe commands need. Pad
Columns squares the rest up afterwards.

## A worked example

The file to run this on is
[A13L.mod.before](samples/A13L.mod.before){ download }, a real paste, tab
separated, with an en dash standing in for the minus sign on the southern
declinations. It is 14 rows long, and the blocks below show the first three of
them. A [clone of the repository](installing-macros.md#getting-the-repository)
has it under `samples/`.

Download it rather than copying the listing. A rendered web page holds no tab
characters at all, so a copy of the block below arrives with spaces where the
file has tabs, and tabs are what this example is about. Expand Tabs then finds
nothing to expand. The fields land at 0, 12, 24 and 40 on the first row and 0,
12, 24 and 36 on the second, so the column numbers used further down fall
inside the data. The listing shows what the file looks like; it is not the
file.

```
##refcode = 2026A+A...707A..13L

SDSS001009	00:10:09.97	–00:46:03.66	0.2431
SDSS004054	00:40:54.33	15:34:09.66	0.2832
SDSS005527	00:55:27.46	–00:21:48.71	0.1674
```

While those tabs are in it, Pipe at Columns and Pad Columns both refuse it. So
run **Expand Tabs**, which reports `42 tab(s) expanded at width 8`, then
**Normalize Characters**, which names what it replaced in the terminal:

```
normalize: A13L.mod.before:
  U+2013 EN DASH
```

An en dash and a minus sign are one character each, so nothing has moved and
the columns are where Expand Tabs left them: the fields start at 0, 16, 32 and 48,
and columns 15, 31 and 47 are blank on every row. Answering `15, 31, 47` in
**Pipe at Columns** and choosing Overwrite:

```
##refcode = 2026A+A...707A..13L

SDSS001009     |00:10:09.97    |-00:46:03.66   |0.2431
SDSS004054     |00:40:54.33    |15:34:09.66    |0.2832
SDSS005527     |00:55:27.46    |-00:21:48.71   |0.1674
```

with `pipe: A13L.mod.before: 42 pipe(s) into 14 row(s)` in the terminal. The
blank line and the `##refcode` header pass through untouched, and neither
counts as a row.

Now the coordinates. Select the declination column with a rectangular selection,
holding Ctrl while dragging, starting at the first data row so the `##refcode`
line stays out of it. Run **Dec to NED Form**, then do the right ascension
column with **RA to NED Form**:

```
##refcode = 2026A+A...707A..13L

SDSS001009     |001009.97|-004603.66|0.2431
SDSS004054     |004054.33|+153409.66|0.2832
SDSS005527     |005527.46|-002148.71|0.1674
```

They report `14 declination(s) converted` and `14 right ascension(s)
converted`. Declination first, because converting a column shortens it and
shifts every column to its right, so the right ascension would have to be found
again. Note what happened to row 2: the paper prints `15:34:09.66` unsigned and
a ptable never does, so it comes out `+153409.66`.

If a rectangle catches something that is not a coordinate, neither command
converts anything at all. It names the line and the value and stops, because a
column half in one format and half in the other is harder to spot than one that
was never touched.

**Pad Columns** then measures the columns and pads each field to fit, which on
this file means closing up the space the conversion left behind:

```
##refcode = 2026A+A...707A..13L

SDSS001009|001009.97|-004603.66|0.2431
SDSS004054|004054.33|+153409.66|0.2832
SDSS005527|005527.46|-002148.71|0.1674
```

It reports `pad: A13L.mod.before: 14 row(s), 4 column(s)`. The declination
column is 10 wide and needs no padding at all, because writing the sign out has
made every value in it the same length. Every row is now 38 characters long,
and stays that way until the next edit.

**Trim Trailing Blanks** has nothing to do on this paste and leaves the buffer
alone, since every redshift here is six characters and the last column needed
no padding. It says `trim: A13L.mod.before: nothing to trim`, where a run that
did something would say `N line(s) trimmed`.

### What is still done by hand

The buffer now holds 16 lines: the `##refcode` line, the blank line under it,
and 14 data rows of four fields, each 38 characters wide. The listing above is
the thing to check your own run against.

It is not a NED file yet.
[A13L.mod.after](samples/A13L.mod.after){ download } is the finished file for
the same data, 23 lines with five columns where this has four, and getting from
one to the other is work no command here attempts:

| Still to do | Why no command does it |
| --- | --- |
| `2026A+A...707A..13L` → `2026A&A...707A..13L` | A blanket `+` to `&` would destroy every positive declination in the file |
| Seven `##` lines under the refcode, and the blank line goes: `##type1`, `##coordx_unit1`, `##coordy_unit1`, `##coord_equinox1`, `##coord_system1`, `##vz_flag1`, `##vz_unit1` | Nothing in the paste says what belongs in them |
| A column heading row above the data | Same |
| `SDSS001009` becomes the full designation, filling two columns where the paste has one short name | The designation has to be looked up |

The heading row names one column each: `ap_name1`, `name1`, `coordx1`,
`coordy1`, `vz1`. The first two both take the designation, and looking it up is
the step that cannot come out of the file. Row 2 is named
`SDSS J004054.31+153409.8` while its `coordx1` is `004054.33`: different
digits, not a rounding of them, because the designation comes from SDSS's own
astrometry and the paper's measured position is a separate quantity landing
nearby. A name built from the coordinates would be a plausible identifier for
the wrong object.

`samples/README.md` in a clone is the repo's own version of that list.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no substitute
it can pick on its own, and guessing at one would corrupt the data quietly,
which is worse than leaving a character that at least looks wrong. Leaving them
costs nothing downstream here, since the pipe commands and Pad Columns count
characters as they are displayed.

Rather than fail silently, the command counts what it left, puts the cursor on
the first one and lists them in the terminal with a count per character.
[Character replacements](character-replacements.md) has the full table of what
it does and does not touch.

One case worth knowing about: a `##refcode` of `2026A+A...707A..13L` should
read `2026A&A...707A..13L`. That is a plain ASCII `+` standing in for `&`, and
it is deliberately not automated, since a blanket `+` to `&` replacement would
destroy every positive declination in the file.

## Flattening the letters

The report above is also where you find out whether you want the next command.
If it lists accented or Greek letters and you would rather have plain ASCII,
run **Fold Letters to ASCII**.

`Balázs` becomes `Balazs` and `α` becomes `a`, keeping upper and lower case.
Ten letters have no one-letter answer and widen the line instead, so `Weiß`
becomes `Weiss` and `Æ` becomes `AE`; those shift everything to their right the
same way a ligature does, which is the reason this runs before the boundaries
are chosen.

The Greek fold is the one to read the report on. Several letters share an
answer, `ε` and `η` both giving `e` among them, so once it has run nothing can
tell which letter was there. The command lists every one it replaced with the
line and column it was on and parks the cursor on the first.

An accent fold gets no such list, only a one-line summary. It is still
irreversible, and `Balazs` is not a name anyone can put the accent back into,
so decide before you run it rather than after.

## When the file is locked

A locked buffer takes no writes, so every command checks for one before it does
anything else. What you get instead of an edit is the usual one-line summary
and a marked report, both in the terminal that launched `xnedit`:

```
trim: A13L.mod.before: nothing changed

=== nedkit ===
A13L.mod.before is locked, so nothing was changed.

XNEdit locks a file it cannot read as UTF-8, which is the usual reason. File > Read Only locks a buffer too, and so does a file with no write permission.
=== end ===
```

The `=== nedkit ===` markers are there so a report can be found again in a
terminal that has scrolled.

## Turning the dialog back on

A report used to go in a dialog, which is easier to read than terminal output
you have to go looking for. It is off because a modal Motif dialog crashes the
X server on some macOS and XQuartz combinations, taking every open window with
it, and the crash is in XQuartz rather than in anything the macros do.

The dialog is switched off rather than removed. Launch `xnedit` with
`NEDKIT_DIALOGS=1` in its environment and every report goes to a dialog as well
as to the terminal:

```{ .sh .copy }
NEDKIT_DIALOGS=1 xnedit A283R.mod
```

| `NEDKIT_DIALOGS` | What a report does |
| --- | --- |
| unset, or anything but `1` | prints to the terminal only |
| `1` | prints to the terminal and opens a dialog |

Off is the default because an unset variable reads as empty, so a copy of
XNEdit started from the Dock, where no shell has set anything, cannot raise a
dialog by accident. Once the XQuartz bug is fixed, setting the variable in a
shell profile turns the dialogs back on for good.

All nine commands print the summary line, under eight prefixes: `dec:`, `expand:`, `fold:`,
`normalize:`, `pad:`, `pipe:`, `ra:` and `trim:`, the two pipe commands sharing
`pipe:`. The buffer was not touched, so there is nothing to undo.

NED's data files are not reliably UTF-8, so the encoding lock is the one you
will meet. XNEdit read a byte it could not decode, put U+FFFD REPLACEMENT
CHARACTER in the buffer where that byte was, and locked the buffer. The text on
screen is therefore not the file on disk: saving it would write those
replacement characters over the bytes they stand in for, and the originals
would be gone. That is what the lock prevents.

The window says so twice over. The title bar carries `(locked)` after the
filename, and a bar under the menus reads:

```
1 non-convertible characters skipped: file locked to prevent accidental changes
```

Two dropdowns sit in that bar. **Errors**, on the left, lists each byte XNEdit
could not convert, as `0xE9` and so on; picking one selects that spot in the
text and scrolls to it, which is the fastest way to find them. On the right is
the encoding it read the file as. Choose another and click **Reload**, and it
re-reads the file from disk as that instead. A reading that decodes cleanly
comes back unlocked and the commands run normally.

Which encoding is right is a question about your data, and nothing here can
answer it. Worth knowing before you start trying things: unticking **File >
Read Only** releases the encoding lock along with the tick, and the next save
then puts those replacement characters on disk for real.
