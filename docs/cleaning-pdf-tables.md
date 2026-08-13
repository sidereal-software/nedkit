# Cleaning up a pasted table

Text copied out of a journal PDF arrives with two problems. The columns are
separated by whatever the PDF happened to emit, and many of the characters are
not the ASCII characters they look like. A declination that reads
`-00:46:03.66` on screen often starts with U+2013 EN DASH, and nothing
downstream that expects a minus sign will match it.

Two commands handle this. Run **Align Columns** first, then **Normalize
Characters**.

## Why that order

Normalize Characters turns every tab into a single space. Once it has run,
`a<TAB><TAB>c` and `a<SPACE><SPACE>c` are the same text, and an empty field
between two tabs can no longer be told apart from ordinary spacing. Align
Columns splits on the tab while the tab is still there, so an empty column
survives:

| Order | `a<TAB>b<TAB><TAB>d` becomes |
| --- | --- |
| Align first | `a\|b\| \|d` |
| Normalize first | `a\|b\|d` |

The second row has lost a column. On a file with no empty fields either order
gives the same result, but aligning first costs nothing and is safe either way.

## A worked example

Starting from a table pasted out of a paper, tab separated, with an en dash
standing in for the minus sign on the southern declinations:

```
##refcode = 2026A&A...707A..13L

SDSS001009	00:10:09.97	–00:46:03.66	0.2431
SDSS004054	00:40:54.33	15:34:09.66	0.2832
SDSS005527	00:55:27.46	–00:21:48.71	0.1674
```

Align Columns gives every column the width of its widest value:

```
##refcode = 2026A&A...707A..13L

SDSS001009|00:10:09.97|–00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66 |0.2832
SDSS005527|00:55:27.46|–00:21:48.71|0.1674
```

The blank line and the `##refcode` header pass through untouched and take no
part in the column widths. Column three is padded to 12 because the negative
declinations are a character wider than the positive ones.

Normalize Characters then replaces the en dashes:

```
SDSS001009|00:10:09.97|-00:46:03.66|0.2431
SDSS004054|00:40:54.33|15:34:09.66 |0.2832
SDSS005527|00:55:27.46|-00:21:48.71|0.1674
```

## Fixing a value afterwards

Align Columns re-splits a line that already contains `|`, so it can be run
again. Widen a value by hand, run the command, and the whole column re-pads
around it. Narrow it again and the columns close back up. Every row comes out
the same length either way.

## What Normalize Characters will not do

It replaces characters that have an unambiguous ASCII spelling and leaves the
rest alone. Degree signs, Greek letters and accented names have no safe
substitute, and guessing at one would corrupt the data quietly, which is worse
than leaving a character that at least looks wrong.

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
