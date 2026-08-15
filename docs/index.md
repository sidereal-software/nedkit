# nedkit

XNEdit macros for the NED team at IPAC. Reshaping a data file by hand is slow
and easy to get subtly wrong, and a macro does the same edit the same way every
time. Python utilities live here too, for the jobs too big to run inside the
editor.

## The commands

<div class="nedkit-kit" markdown>

<div markdown>
:material-bandage:

### [Normalize Characters](commands.md#normalize-characters)

For characters that look like ASCII and are not.

Rewrites the dashes, quotes and ligatures a PDF brings with it, and reports
whatever it could not safely translate.
</div>

<div markdown>
:material-format-letter-case:

### [Fold Letters to ASCII](commands.md#fold-letters-to-ascii)

For accented names and Greek symbols.

Turns `Balázs` into `Balazs` and `α` into `a`, keeping case. Lists every Greek
letter it replaced, since those readings collide.
</div>

<div markdown>
:material-cursor-text:

### [Pipe at Cursor Column](commands.md#pipe-at-cursor-column)

For a fixed-width table with no delimiter in it.

Writes a `|` down the column the cursor is in, on every line at once. It is on
the right-click menu too, so you can do a boundary without leaving the text.
</div>

<div markdown>
:material-table-column-plus-after:

### [Pipe at Columns](commands.md#pipe-at-columns)

For several boundaries in one pass.

Asks which columns, and whether to write over the space there or push the rest
of the line right, then does the whole file.
</div>

<div markdown>
:material-format-align-justify:

### [Pad Columns](commands.md#pad-columns)

For a pipe-delimited table that has gone out of true.

Pads every field to the width of the widest value in its column, counting
characters rather than bytes, so the pipes line up again.
</div>

<div markdown>
:material-content-cut:

### [Trim Trailing Blanks](commands.md#trim-trailing-blanks)

For invisible whitespace at the ends of lines.

Removes trailing spaces and tabs, and leaves the buffer alone when there is
nothing to remove.
</div>

</div>

They are in the order they are meant to be run.
[Cleaning up a pasted table](cleaning-pdf-tables.md) walks the sequence through
on a real file, and [getting started](getting-started.md) covers installing
them in the first place.

## Which editor

These are written for [XNEdit](https://github.com/unixwork/xnedit) and tested
against it every week. They are ordinary NEdit macros and run on classic NEdit
5.7 too, give or take some column arithmetic on non-ASCII text. The two editors
keep their settings in different places, `~/.xnedit/` against `~/.nedit/`, so
instructions written for one send you to the wrong directory.

Only XNEdit locks a file it cannot read as UTF-8, and all six commands refuse a
locked buffer rather than write into one. [When the file is
locked](cleaning-pdf-tables.md#when-the-file-is-locked) is what that looks like
and what to do about it.

XNEdit runs under XQuartz on the Macs, which explains some behavior that
otherwise looks like a bug: the menu bar sits inside the window, copy and paste
go through the X selection rather than the macOS clipboard, and `t_print()`
output lands in the terminal that launched `xnedit`.
