# Cleaning up a pasted table

Text copied out of a journal PDF arrives with two problems. The columns are
separated by whatever the PDF happened to emit, and many of the characters are
not the ASCII characters they look like. A declination that reads
`-00:46:03.66` on screen often starts with U+2013 EN DASH, and nothing
downstream that expects a minus sign will match it.

Two commands handle this, and **Align Columns** runs twice:

1. **Align Columns**, to fix the field boundaries
2. **Normalize Characters**, and any other tidying up
3. read the file through and fix what needs fixing by hand
4. **Align Columns** again, as the last thing that touches the file

## Why aligning comes first

Normalize Characters turns every tab into a single space. Once it has run,
`a<TAB><TAB>c` and `a<SPACE><SPACE>c` are the same text, so Align Columns has
no delimiter left to work with. It falls back to splitting on runs of
whitespace, which cuts every field containing a space into several and loses
any field that was empty:

| Order | `NGC 4472<TAB>12 29 46.76<TAB><TAB>0.0033` becomes |
| --- | --- |
| Align first | `NGC 4472\|12 29 46.76\| \|0.0033` |
| Normalize first | `NGC\|4472\|12\|29\|46.76\|0.0033` |

The second row is not a table any more. Aligning first turns the tabs into
pipes, and a pipe is the first delimiter Align Columns looks for, so the
boundaries hold through everything that follows.

## Why aligning comes last

The widths are only right until the next edit. Change a value and its column
no longer fits, and that includes the changes Normalize Characters makes: an
en dash measures three where it prints one, so rows containing one come out
two characters too wide until the dashes are gone and the file is aligned
again.

The same goes for anything you fix by hand. **Align last, after the file is
finished**, or the columns will be right for the version you had rather than
the version you are shipping.

## A worked example

Starting from a table pasted out of a paper, tab separated, with an en dash
standing in for the minus sign on the southern declinations:

```
##refcode = 2026A&A...707A..13L

SDSS001009	00:10:09.97	–00:46:03.66	0.2431
SDSS004054	00:40:54.33	15:34:09.66	0.2832
SDSS005527	00:55:27.46	–00:21:48.71	0.1674
```

**Align Columns** joins the fields with `|` and pads each column to its widest
value:

```
##refcode = 2026A&A...707A..13L

SDSS001009|00:10:09.97|–00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66   |0.2832
SDSS005527|00:55:27.46|–00:21:48.71|0.1674
```

The blank line and the `##refcode` header pass through untouched and take no
part in the column widths.

Column three has come out crooked, and that is expected at this stage. An en
dash is three bytes long where a minus sign is one, and the padding is measured
in bytes, so the middle row has been given two spaces more than it needs.

**Normalize Characters** replaces the en dashes:

```
SDSS001009|00:10:09.97|-00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66   |0.2832
SDSS005527|00:55:27.46|-00:21:48.71|0.1674
```

The characters are right now and the columns are still crooked, because
nothing has re-measured them. **Align Columns** a second time does that:

```
SDSS001009|00:10:09.97|-00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66 |0.2832
SDSS005527|00:55:27.46|-00:21:48.71|0.1674
```

## Fixing a value afterwards

Align Columns re-splits a line that already contains `|`, so it can be run as
often as you like. Widen a value by hand, run the command, and the whole column
re-pads around it. Narrow it again and the columns close back up. Every row
comes out the same length either way.

This is why the last step is the alignment and not the editing. Fix everything
first, then align once at the end, and the file you hand on is the file whose
columns were measured.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no safe
substitute, and guessing at one would corrupt the data quietly, which is worse
than leaving a character that at least looks wrong.

One consequence is worth watching for. A character that survives Normalize
Characters is still there for the final Align Columns, which measures it in
bytes, so a column containing `Balázs` or `α` comes out a space short for every
non-ASCII character in it. The file is correct; the columns are not quite
straight. If a column has to line up exactly, check that one by eye.

Rather than fail silently, the command counts what it left, puts the cursor on
the first one and lists them in a dialog with a count per character.
[Character replacements](character-replacements.md) has the full table of what
it does and does not touch.

One case worth knowing about: a `##refcode` of `2026A+A...707A..13L` should
read `2026A&A...707A..13L`. That is a plain ASCII `+` standing in for `&`,
not an encoding problem, and it is deliberately not automated. A blanket `+`
to `&` replacement would destroy every positive declination in the file.

## Trailing spaces

Align Columns pads the last column too, so each row ends with spaces when its
value is shorter than the column. Run **Trim Trailing Blanks** afterwards if
you would rather lines ended at the last real character. Doing so gives up the
property that every row is the same length, which matters if anything reads
the file by byte offset.

This is the one command that can follow the final alignment. It only removes
spaces from the end of a line, so no column boundary moves and nothing needs
re-aligning. Anything else that edits the file puts you back to step 4.
