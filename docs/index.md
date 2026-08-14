# nedkit

XNEdit macros for the NED team at IPAC. Reshaping a data file by hand is slow
and easy to get subtly wrong, and a macro does the same edit the same way every
time. Python utilities live here too, for the jobs too big to run inside the
editor.

## The commands

<div class="nedkit-kit" markdown>

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
:material-content-cut:

### [Trim Trailing Blanks](commands.md#trim-trailing-blanks)

For invisible whitespace at the ends of lines.

Removes trailing spaces and tabs, and leaves the buffer alone when there is
nothing to remove.
</div>

</div>

Just pasted a table out of a paper and want to know what to run?
[Cleaning up a pasted table](cleaning-pdf-tables.md) walks the whole sequence
through on a real file. To get the commands installed in the first place, start
with [getting started](getting-started.md).

## Which editor

These are written for [XNEdit](https://github.com/unixwork/xnedit) and tested
against it on every release. They are ordinary NEdit macros, though, and CI
also runs the suite through classic NEdit 5.7 to see how far they carry. The
answer is: nearly all the way. The commands that depend on the fork are
Normalize Characters and Fold Letters to ASCII, both of which work in UTF-8,
and NEdit 5.7 predates it. Fold Letters also reports a Greek letter's column,
which XNEdit counts as it is displayed and NEdit 5.7 counts in bytes.

The two editors keep their settings in different places, `~/.xnedit/` against
`~/.nedit/`, so instructions written for one will send you to the wrong
directory. That is the difference worth remembering.

XNEdit runs under XQuartz on the Macs, which explains some behavior that
otherwise looks like a bug: the menu bar sits inside the window, copy and paste
go through the X selection rather than the macOS clipboard, and `t_print()`
output lands in the terminal that launched `xnedit`.
