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

The order comes out of two facts. A replacement that changes how many
characters are on a line moves every column to its right, so the letters get
sorted out before the boundaries are chosen. And every edit changes a width, so
the padding goes last.

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

It is on the right-click menu as well as the Macro menu, so a boundary costs
nothing but a click and a menu pick. Right-clicking does not move the cursor,
though, so left-click the column first.

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
left as they are rather than guessed at: a row holding something other than a
space at that column, because overwriting there would destroy a character, and
a row that ends before the column, because padding it out would invent data.
The dialog gives a count and the line number of the first one. Either case
usually means the column is a place or two off.

The first case is the one to watch. A column that is blank on almost every row
can land inside a name like `NGC 4472` on the one row where it isn't, and the
command has no way to tell that apart from a column you meant.

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

## Tabs have to go first

The two pipe commands refuse a buffer with a tab anywhere in it, and so does
Pad Columns. A tab is one character and however many columns it takes to reach
the next tab stop, so on a line that contains one there is no answer to the
question of what is in column 15, or of how wide a field is.

XNEdit has nothing that expands a tab to the spaces it stands for, so this goes
through the shell. Select the whole file and run `expand` through
**Shell > Filter Selection**, which replaces each tab with the spaces it was
already displaying and leaves the columns where they sit on screen.

That is why `expand` comes before Normalize Characters rather than after it.
Normalize takes tabs out too, but it writes one space for each, which closes
the columns up and destroys the layout you were about to point at.

The columns landing where they already were is a coincidence worth knowing
about. `expand` puts a tab stop every 8 columns and XNEdit's tab distance is
also 8, so the two agree until somebody changes **Preferences > Tab Stops**. If
yours is not 8, pass the same number, as in `expand -t 4`, or the file comes
back with every column somewhere new.

!!! warning "`expand` needs a UTF-8 locale"

    Under `LANG=C` it does not count a character like an en dash at all, and
    pads as though it were not there. Everything to the right of one on that
    line then lands a column too far over, once per non-ASCII character.

## Why the letters get fixed first

A replacement that changes how many characters are on a line moves every column
to its right. Most of them do not: an en dash becomes a minus sign, one
character for one, and nothing moves. Greek is deliberately one letter for one
so that it cannot move anything either. A ligature becomes two letters, an
ellipsis becomes three dots, and `ß` becomes `ss`, and those push the rest of
their row right.

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
all. Normalize first and pipe afterwards and they stay together:

```
Griffin       | 12:29:46.7
Smith         |12:36:44.0
```

The row that grew is still a character wider than the other, so its second
field starts a place late. Pad Columns puts that right from either block. The
difference is what happens to the next boundary: in the first there is no
single column number that finds it on both rows, and in the second there is.

## Why the padding comes last

Pad Columns measures each column and pads every field out to the widest value
in it, and that measurement is true only until the next edit. Change a value
and you change the width of its column, whether the change came from a command
or from typing. So the padding goes after everything else, including anything
you fixed by hand, and gets run again after any later edit.

Trim Trailing Blanks is optional, and when it runs at all it runs after the
padding. Pad Columns pads the last column too, so every row ends in the same
place; Trim Trailing Blanks trades that for lines that stop at the last real
character. It is also the one command here that cannot move a boundary, since
it only ever takes spaces and tabs off the end of a line.

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

Pipe at Columns will not touch it while those tabs are in it, and neither will
Pad Columns:

> A13L.mod.before has a tab in it, so there is no telling which column anything
> is in: a tab is one character and however many columns it takes to reach the
> next tab stop.

So select the whole file and filter it through `expand`:

```
##refcode = 2026A+A...707A..13L

SDSS001009      00:10:09.97     –00:46:03.66    0.2431
SDSS004054      00:40:54.33     15:34:09.66     0.2832
SDSS005527      00:55:27.46     –00:21:48.71    0.1674
```

**Normalize Characters** replaces the en dashes and names what it did:

```
##refcode = 2026A+A...707A..13L

SDSS001009      00:10:09.97     -00:46:03.66    0.2431
SDSS004054      00:40:54.33     15:34:09.66     0.2832
SDSS005527      00:55:27.46     -00:21:48.71    0.1674
```

and in the terminal:

```
normalize: A13L.mod.before:
  U+2013 EN DASH
```

An en dash and a minus sign are one character each, so nothing has moved and
the columns are where `expand` left them. That is the point of doing this
before the pipes go in rather than after.

The fields start at columns 0, 16, 32 and 48, and columns 15, 31 and 47 are
blank on every row. Answering `15, 31, 47` in **Pipe at Columns** and choosing
Overwrite:

```
##refcode = 2026A+A...707A..13L

SDSS001009     |00:10:09.97    |-00:46:03.66   |0.2431
SDSS004054     |00:40:54.33    |15:34:09.66    |0.2832
SDSS005527     |00:55:27.46    |-00:21:48.71   |0.1674
```

with a line in the terminal to say what it did:

```
pipe: A13L.mod.before: 42 pipe(s) into 14 row(s)
```

The blank line and the `##refcode` header pass through untouched, and neither
counts as a row.

**Pad Columns** measures the columns and pads each field to fit, which on this
file means closing up most of the space `expand` left:

```
##refcode = 2026A+A...707A..13L

SDSS001009|00:10:09.97|-00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66 |0.2832
SDSS005527|00:55:27.46|-00:21:48.71|0.1674
```

and in the terminal:

```
pad: A13L.mod.before: 14 row(s), 4 column(s)
```

The declination column is 12 wide because the southern rows carry a minus sign,
so the northern ones pick up a trailing space. Every row is now 42 characters
long, and stays that way until the next edit.

**Trim Trailing Blanks** has nothing to do on this paste and leaves the buffer
alone: every redshift here is six characters, so the last column needed no
padding. It says so in the terminal:

```
trim: A13L.mod.before: nothing to trim
```

A run that did something would say `N line(s) trimmed` instead, so the two are
told apart without reading the file.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no substitute
it can pick on its own, and guessing at one would corrupt the data quietly,
which is worse than leaving a character that at least looks wrong.

That is not a problem for the pipe commands or for Pad Columns, all of which
count characters as they are displayed: `Balázs` is six wide to them, whatever
it takes in bytes. The count holds for anything XNEdit can decode, and a file
it cannot decode is locked against editing anyway.

Rather than fail silently, the command counts what it left, puts the cursor on
the first one and lists them in a dialog with a count per character.
[Character replacements](character-replacements.md) has the full table of what
it does and does not touch.

One case worth knowing about: a `##refcode` of `2026A+A...707A..13L` should
read `2026A&A...707A..13L`. That is a plain ASCII `+` standing in for `&`,
not an encoding problem, and it is deliberately not automated. A blanket `+`
to `&` replacement would destroy every positive declination in the file.

## Flattening the letters

The dialog above is also where you find out whether you want the next command.
If it lists accented or Greek letters and you would rather have plain ASCII,
run **Fold Letters to ASCII**.

`Balázs` becomes `Balazs` and `α` becomes `a`, keeping upper and lower case.
Ten letters have no one-letter answer and widen the line instead, so `Weiß`
becomes `Weiss` and `Æ` becomes `AE`; those shift everything to their right the
same way a ligature does, which is the reason this runs before the boundaries
are chosen. Nothing else in the command changes a width.

The Greek fold is the one to read the report on. Several letters share an
answer, `ε` and `η` both giving `e` among them, so once it has run nothing can
tell which letter was there. The command lists every one it replaced with the
line and column it was on and parks the cursor on the first.

An accent fold gets no dialog, only a line in the terminal. It is still
irreversible, and `Balazs` is not a name anyone can put the accent back into,
so decide before you run it rather than after.

It is a separate command partly because flattening a name is a decision about
your data rather than a typographic cleanup, and partly because a macro
compiles into 4096 instructions and the two tables do not fit in one.
