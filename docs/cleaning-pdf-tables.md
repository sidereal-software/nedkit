# Cleaning up a pasted table

Text copied out of a journal PDF arrives with two problems. The columns are
separated by whatever the PDF happened to emit, and many of the characters are
not the ASCII characters they look like. A declination that reads
`-00:46:03.66` on screen often starts with U+2013 EN DASH, and nothing
downstream that expects a minus sign will match it.

The order to work in:

1. get rid of the tabs, with `expand` through **Shell > Filter Selection**
2. **Normalize Characters**
3. **Fold Letters to ASCII**, if the accented and Greek letters should go too
4. read the file through and fix what needs fixing by hand
5. put the field boundaries in with **Pipe at Cursor Column** or **Pipe at
   Columns**
6. **Pad Columns**
7. **Trim Trailing Blanks**, if you would rather the rows did not all end in
   the same place

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

Pipe at Columns offers both. Overwrite writes the pipe over the character at
that column and only where that character is a space, so every row stays the
width it was. A second run finds the pipe already there and leaves it, which
makes overwriting safe to repeat. Pipe at Cursor Column always overwrites.

Insert puts the pipe in and pushes the rest of the line right. Nothing is lost,
so it reaches a row with no blank column to spare:

```
NGC4472 12:29:46.7
IC3583  12:36:44.0
```

Answering `7` and choosing Insert gives

```
NGC4472| 12:29:46.7
IC3583 | 12:36:44.0
```

The price is a character of width on every row it touches, and a second run
adds a second set of pipes.

### Read the report

Both commands print a line per run in the terminal that launched `xnedit`, and
raise a dialog when some rows did not get their pipe. Two cases are counted and
left alone rather than guessed at: a row holding something other than a space
at that column, because overwriting there would destroy a character, and a row
that ends before the column, because padding it out would invent data. The
dialog gives a count and the line number of the first one, and either case
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
place. `samples/A13L.mod.after` is laid out that way. A row whose field count
differs from the first data row is padded as far as it goes and then reported,
by count and first line number; no empty field is invented to make it fit.

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

XNEdit cannot expand a tab, so this goes through the shell. Select the whole
file and run `expand` through **Shell > Filter Selection**, which writes the
spaces the tab was already displaying and leaves the columns where they sit on
screen.

That is why `expand` comes before Normalize Characters rather than after.
Normalize takes tabs out too, but it writes one space for each, which closes
the columns up.

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

`samples/A13L.mod.before` is a real paste, tab separated, with an en dash
standing in for the minus sign on the southern declinations. It is 14 rows
long, and the blocks below show the first three of them.

```
##refcode = 2026A+A...707A..13L

SDSS001009	00:10:09.97	–00:46:03.66	0.2431
SDSS004054	00:40:54.33	15:34:09.66	0.2832
SDSS005527	00:55:27.46	–00:21:48.71	0.1674
```

While those tabs are in it, Pipe at Columns and Pad Columns both refuse it. So
select the whole file, filter it through `expand`, and run **Normalize
Characters**, which names what it replaced in the terminal:

```
normalize: A13L.mod.before:
  U+2013 EN DASH
```

An en dash and a minus sign are one character each, so nothing has moved and
the columns are where `expand` left them: the fields start at 0, 16, 32 and 48,
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

**Pad Columns** then measures the columns and pads each field to fit, which on
this file means closing up most of the space `expand` left:

```
##refcode = 2026A+A...707A..13L

SDSS001009|00:10:09.97|-00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66 |0.2832
SDSS005527|00:55:27.46|-00:21:48.71|0.1674
```

It reports `pad: A13L.mod.before: 14 row(s), 4 column(s)`. The declination
column is 12 wide because the southern rows carry a minus sign, so the northern
ones pick up a trailing space. Every row is now 42 characters long, and stays
that way until the next edit.

**Trim Trailing Blanks** has nothing to do on this paste and leaves the buffer
alone, since every redshift here is six characters and the last column needed
no padding. It says `trim: A13L.mod.before: nothing to trim`, where a run that
did something would say `N line(s) trimmed`.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no substitute
it can pick on its own, and guessing at one would corrupt the data quietly,
which is worse than leaving a character that at least looks wrong. Leaving them
costs nothing downstream here, since the pipe commands and Pad Columns count
characters as they are displayed.

Rather than fail silently, the command counts what it left, puts the cursor on
the first one and lists them in a dialog with a count per character.
[Character replacements](character-replacements.md) has the full table of what
it does and does not touch.

One case worth knowing about: a `##refcode` of `2026A+A...707A..13L` should
read `2026A&A...707A..13L`. That is a plain ASCII `+` standing in for `&`, and
it is deliberately not automated, since a blanket `+` to `&` replacement would
destroy every positive declination in the file.

## Flattening the letters

The dialog above is also where you find out whether you want the next command.
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

An accent fold gets no dialog, only a line in the terminal. It is still
irreversible, and `Balazs` is not a name anyone can put the accent back into,
so decide before you run it rather than after.

## When the file is locked

A locked buffer takes no writes, so every command checks for one before it does
anything else. What you get instead of an edit is a dialog:

```
A13L.mod.before is locked, so nothing was changed.

XNEdit locks a file it cannot read as UTF-8, which is the usual reason.
File > Read Only locks a buffer too, and so does a file with no write
permission.
```

and a line in the terminal where the count normally goes:

```
trim: A13L.mod.before: nothing changed
```

All six say it, under their own prefix: `normalize:`, `fold:`, `pipe:`, `pad:`,
`trim:`. The buffer was not touched, so there is nothing to undo.

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
