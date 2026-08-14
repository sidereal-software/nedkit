# Cleaning up a pasted table

Text copied out of a journal PDF arrives with two problems. The columns are
separated by whatever the PDF happened to emit, and many of the characters are
not the ASCII characters they look like. A declination that reads
`-00:46:03.66` on screen often starts with U+2013 EN DASH, and nothing
downstream that expects a minus sign will match it.

The order to work in:

1. put the field boundaries in with **Pipe at Cursor Column** or **Pipe at
   Columns**
2. **Normalize Characters**
3. **Fold Letters to ASCII**, if the accented and Greek letters should go too
4. read the file through and fix what needs fixing by hand
5. **Trim Trailing Blanks**, last

Nothing in that list pads a column. The file comes out pipe delimited and no
more square than it went in, and squaring it up is still done by hand or
somewhere outside the editor.

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

## Tabs have to go first

Both commands refuse a buffer with a tab anywhere in it. A tab is one character
and however many columns it takes to reach the next tab stop, so on a line that
contains one there is no answer to the question of what is in column 15.

XNEdit has nothing that expands a tab to the spaces it stands for, so this goes
through the shell. Select the whole file and run `expand` through
**Shell > Filter Selection**, which replaces each tab with the spaces it was
already displaying and leaves the columns where they sit on screen.

Normalize Characters takes tabs out too, but it writes one space for each,
which closes the columns up and destroys the layout you were about to point at.

!!! warning "`expand` needs a UTF-8 locale"

    Under `LANG=C` it does not count a character like an en dash at all, and
    pads as though it were not there. Everything to the right of one on that
    line then lands a column too far over, once per non-ASCII character.

## Why the pipes go in first

The boundaries have to be nailed down while the layout is still on screen,
which means before Normalize Characters turns the tabs into single spaces.

Piping first is also the more forgiving order when a replacement changes a
character count. Most of them do not: an en dash becomes a minus sign, one
character for one, and nothing moves. Greek is deliberately one letter for one
so that it cannot move anything either. A ligature becomes two letters, an
ellipsis becomes three dots, and `ß` becomes `ss`, and those push the rest of
their row right.

```
Griﬀin         |12:29:46.7
Smith          |12:36:44.0
```

After Normalize Characters:

```
Griffin         |12:29:46.7
Smith          |12:36:44.0
```

The pipe still separates the same two fields, so the table is intact. That row
is simply a character wider than the one below it now, and nothing puts it
back. Look at the file again after normalizing, before you pipe the next
boundary off a column number you read earlier.

## Why trimming comes last

Trim Trailing Blanks only ever takes spaces and tabs off the end of a line, so
it is the one command that cannot move a boundary. Anything else you do to the
file can, which is why it goes at the end and gets run again after any later
edit.

Nothing in the sequence creates trailing whitespace. What it removes is
whatever came in with the paste.

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

Pipe at Columns will not touch it while those tabs are in it:

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

The fields now start at columns 0, 16, 32 and 48, and columns 15, 31 and 47 are
blank on every row. Answering `15, 31, 47` and choosing Overwrite:

```
##refcode = 2026A+A...707A..13L

SDSS001009     |00:10:09.97    |–00:46:03.66   |0.2431
SDSS004054     |00:40:54.33    |15:34:09.66    |0.2832
SDSS005527     |00:55:27.46    |–00:21:48.71   |0.1674
```

with a line in the terminal to say what it did:

```
pipe: A13L.mod.before: 42 pipe(s) into 14 row(s)
```

The blank line and the `##refcode` header pass through untouched, and neither
counts as a row.

**Normalize Characters** replaces the en dashes and names what it did:

```
##refcode = 2026A+A...707A..13L

SDSS001009     |00:10:09.97    |-00:46:03.66   |0.2431
SDSS004054     |00:40:54.33    |15:34:09.66    |0.2832
SDSS005527     |00:55:27.46    |-00:21:48.71   |0.1674
```

and in the terminal:

```
normalize: A13L.mod.before:
  U+2013 EN DASH
```

An en dash and a minus sign are one column each, so the pipes have not moved.

**Trim Trailing Blanks** has nothing to do on this paste and leaves the buffer
alone. It is the one command here with no report at all, so a run that does
something and a run that does nothing look the same from the terminal.

The columns line up here because `expand` lined them up and nothing since has
changed a display width. No command measured them, so widen a value by hand and
its row stays out of true.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no substitute
it can pick on its own, and guessing at one would corrupt the data quietly,
which is worse than leaving a character that at least looks wrong.

That is not a problem for the pipe commands, which count columns as they are
displayed: `Balázs` is six columns wide to them, whatever it takes in bytes.
The count holds for anything XNEdit can decode, and a file it cannot decode is
locked against editing anyway.

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
becomes `Weiss` and `Æ` becomes `AE`; those move a boundary the same way a
ligature does, and nothing else in the command changes a width.

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
