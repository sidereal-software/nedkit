# nedkit

XNEdit macros for the NED team at IPAC. Reshaping a data file by hand is slow
and easy to get subtly wrong, and a macro does the same edit the same way every
time. Python utilities live here too, for the jobs too big to run inside the
editor.

## The commands

<div class="nedkit-kit" markdown>

<div markdown>
:material-format-columns:

### [Align Columns](commands.md#align-columns)

For columns that do not line up.

Joins fields with `|` and pads each column to its widest value. Run it first
to fix the field boundaries, then again once the file is finished.
</div>

<div markdown>
:material-bandage:

### [Normalize Characters](commands.md#normalize-characters)

For characters that look like ASCII and are not.

Rewrites the dashes, quotes and ligatures a PDF brings with it, and reports
whatever it could not safely translate.
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
[Cleaning up a pasted table](cleaning-pdf-tables.md) walks through both
commands on a real file. To get them installed in the first place, start with
[getting started](getting-started.md).

## Which editor

These are written for [XNEdit](https://github.com/unixwork/xnedit) and tested
against it on every release. They are ordinary NEdit macros, though, and CI
also runs the suite through classic NEdit 5.7 to see how far they carry. The
answer is: nearly all the way. The one command that depends on the fork is
Normalize Characters, which works in UTF-8, and NEdit 5.7 predates it.

The two editors keep their settings in different places, `~/.xnedit/` against
`~/.nedit/`, so instructions written for one will send you to the wrong
directory. That is the difference worth remembering.

XNEdit runs under XQuartz on the Macs, which explains some behavior that
otherwise looks like a bug: the menu bar sits inside the window, copy and paste
go through the X selection rather than the macOS clipboard, and `t_print()`
output lands in the terminal that launched `xnedit`.
