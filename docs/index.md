# nedkit

Tools for the NED team at IPAC. Most of the work here is reading and reshaping
text files by hand, so most of what nedkit contains is XNEdit macros, with
Python utilities for jobs too large to run inside the editor.

## What is here

Three macro commands, installed through XNEdit's Macro menu:

- [Align Columns](commands.md#align-columns) joins whitespace-separated fields
  with `|` and pads each column to its widest value.
- [Normalize Characters](commands.md#normalize-characters) rewrites the
  characters that come along with text pasted out of a PDF, the dashes and
  quotes and spaces that look like ASCII and are not.
- [Trim Trailing Blanks](commands.md#trim-trailing-blanks) removes trailing
  spaces and tabs.

If you have just pasted a table out of a paper and want to know what to run,
start with [cleaning up a pasted table](cleaning-pdf-tables.md).

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
