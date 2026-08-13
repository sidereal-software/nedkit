# nedkit

<p class="nedkit-strapline" markdown>
A first-aid kit for NED data. The name is <em>medkit</em> with the M swapped
out, because the NED team spends its days patching up text that arrived
injured, and doing it by hand hurts.
</p>

Most of nedkit is XNEdit macros. Reshaping a data file by hand is slow and
easy to get subtly wrong, and a macro does the same edit the same way every
time. Python utilities live here too, for the jobs too big to run inside the
editor.

## What is in the kit

<div class="nedkit-kit" markdown>

<div markdown>
:material-format-columns:

### [Align Columns](commands.md#align-columns)

**Treats:** columns that do not line up.

Joins fields with `|` and pads each column to its widest value. Run it first
to fix the field boundaries, then again once the file is finished.
</div>

<div markdown>
:material-bandage:

### [Normalize Characters](commands.md#normalize-characters)

**Treats:** characters that look like ASCII and are not.

Rewrites the dashes, quotes and ligatures a PDF brings with it, and reports
whatever it could not safely translate.
</div>

<div markdown>
:material-content-cut:

### [Trim Trailing Blanks](commands.md#trim-trailing-blanks)

**Treats:** invisible whitespace at the ends of lines.

Removes trailing spaces and tabs, and leaves the buffer alone when there is
nothing to remove.
</div>

</div>

Just pasted a table out of a paper and want to know what to run?
[Cleaning up a pasted table](cleaning-pdf-tables.md) walks through both
commands on a real file. To get them installed in the first place, start with
[getting started](getting-started.md).

## The editor is XNEdit, not NEdit

Three editors share the same macro language and get mistaken for each other
constantly. nedkit targets [XNEdit](https://github.com/unixwork/xnedit), the
Motif fork of NEdit 5.7, which keeps its configuration in `~/.xnedit/`.

| Editor | Configuration directory |
| --- | --- |
| XNEdit | `~/.xnedit/` |
| NEdit 5.7 | `~/.nedit/` |
| nedit-ng | a Qt configuration directory, `config.ini` |

NEdit settings are drop-in compatible with XNEdit apart from font
configuration. nedit-ng uses an unrelated file format, so its documentation is
misleading for anything about where files live. When a macro misbehaves, check
which editor is actually running before debugging the macro.

XNEdit runs locally on the Macs under XQuartz rather than being forwarded from
a Linux host, which explains some behavior that otherwise looks like a bug: the
menu bar sits inside the window, copy and paste go through the X selection
rather than the macOS clipboard, and `t_print()` output lands in the terminal
that launched `xnedit`.
