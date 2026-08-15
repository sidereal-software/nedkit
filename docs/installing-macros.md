# Installing macros

This repo holds two kinds of macro, and they install differently. Picking the
wrong one is the usual reason a new macro never shows up.

| Kind | Where it comes from | Where it ends up |
| --- | --- | --- |
| **Menu command** | `macros/commands/` | The **Macro** menu, and the right-click menu when the header asks for it |
| **Subroutine library** | `macros/lib/` | `~/.xnedit/autoload.nm`, callable from other macros, invisible in every menu |

Menu commands are the common case. Start there.

## Install a menu command

About five minutes, no Terminal needed. The example below installs
`macros/commands/trim-trailing-blanks.nm`.

### 1. Copy the macro body

Open the `.nm` file in any editor. The header comment tells you what to type
into each field of the dialog. Everything below the header is the macro body:
select it and copy it.

### 2. Open the Macro Commands dialog

**Preferences > Default Settings > Customize Menus > Macro Menu...**

![The Preferences menu, with Default Settings, Customize Menus, and Macro Menu opened in turn](images/macro-menu-path.png)

### 3. Fill in the form

`New` sits at the top of the list on the left and is already selected when the
dialog opens, which is what you want for a new command. Fill in the right-hand
side from the file's header comment, and paste the body into **Macro Command to
Execute**.

![The Macro Commands dialog with the Trim Trailing Blanks command filled in](images/macro-commands-dialog.png)

*The dialog once the command has been filled in. Until you add it, the list on
the left ends at `New` and the fields on the right are empty.*

| Field | What goes in it |
| --- | --- |
| **Menu Entry** | The menu path. `NED>Trim Trailing Blanks` puts the command in a `NED` submenu; each `>` adds a level. |
| **Accelerator** | Optional keyboard shortcut. Click the field and press the keys themselves, don't type their names. |
| **Mnemonic** | Optional single letter, which must appear in the item's name. Underlines that letter for keyboard navigation. |
| **Requires Selection** | Tick only if the header comment says a selection is required. The command is then greyed out when nothing is selected. |
| **Macro Command to Execute** | The body you copied. |

The header carries one field this dialog has no box for: **Install In**, the
list of menus the command belongs in. Anything naming `Window Background Menu`
needs a second trip through Customize Menus, described below.

**Check** compiles the macro and reports any syntax error without installing
anything. Click it before you commit to the command. Then **OK**, which applies
the command and closes the dialog.

### 4. Save the defaults

**Preferences > Save Defaults**, then **OK**.

![The Save Defaults confirmation, naming ~/.xnedit/nedit.rc](images/save-defaults.png)

The new command works immediately, but it lives only in the running program
until you do this. Save Defaults is what writes it to `~/.xnedit/nedit.rc`.

### 5. Check the menu

![The Macro menu, showing Trim Trailing Blanks in the NED submenu](images/macro-menu-result.png)

Test it on a copy of a real file before you trust it on anything you care
about. Macros write straight to the buffer with no confirmation step.

## Install a background menu command

Right-clicking in the text opens the window background menu, the short one
holding Undo, Redo, Cut, Copy and Paste. A command whose header names
`Window Background Menu` under **Install In** belongs there as well, which puts
it one click from the text it acts on.

It is a different dialog from the one above, which is the step people miss:

**Preferences > Default Settings > Customize Menus > Window Background
Menu...**

The form is the one you have already filled in, minus the Requires Selection
box. Paste the same body, click **Check**, then **OK**, then **Preferences > Save Defaults**. A command that belongs in both menus gets installed twice,
once through each dialog, and the two copies are independent: editing one does
not touch the other.

Undo, Redo, Cut, Copy and Paste survive that. They are the default value of the
`nedit.bgMenuCommands` resource, and both the dialog and `-import` add to the
list rather than replacing it. Writing `nedit.bgMenuCommands` into
`~/.xnedit/nedit.rc` by hand is what loses them, since the menu is then exactly
the entries on that line.

### Right-clicking does not move the cursor

Worth knowing before running Pipe at Cursor Column that way. Posting the
background menu leaves the insert cursor wherever it already was, so left-click
the column you mean first, then right-click.

## Install a subroutine library

Files in `macros/lib/` define subroutines that other macros call. They add
nothing to any menu, and they install by being appended to `autoload.nm`, which
XNEdit runs at startup:

```sh
cat macros/lib/text.nm >> ~/.xnedit/autoload.nm
```

XNEdit does not create `autoload.nm` for you, but `>>` will. Restart XNEdit
afterwards, then check it loaded by running one of its subroutines from
**Macro > Execute Macro**.

Appending the same file twice defines the same subroutines twice. When you
reinstall after an edit, delete the old block first.

## Install several commands at once

Rather than paste a dozen commands through the dialog, XNEdit can read them
from a file:

```sh
xnedit -import ned-macros.rc
```

Then **Preferences > Save Defaults** in the window that opens. The imported
commands are *merged* into whatever you already have, so this will not clobber
your own macros.

The file holds a single `nedit.macroCommands` resource listing every command:

```
nedit.macroCommands: \
	NED>Trim Trailing Blanks:::: {\n\
		original = get_range(0, $text_length)\n\
		trimmed = replace_in_string(original, "[ \\t]+$", "", "regex", "copy")\n\
		if (trimmed != original) {\n\
			replace_range(0, $text_length, trimmed)\n\
		}\n\
	}\n
```

The format is unforgiving:

- Each entry starts with four colon-separated fields: menu path, accelerator,
  mnemonic, flags. `R` in the flags field means the command requires a
  selection. Empty fields still need their colons, hence `::::`.
- Every line of the body ends with a literal `\n\`, an escaped newline followed
  by the resource-file line continuation.
- The last line of the resource ends with `\n` and no trailing backslash.
- Indentation is tabs, not spaces.
- **Backslashes double.** A macro that contains `"[ \t]+$"` is written
  `"[ \\t]+$"` here, and `"\\w"` becomes `"\\\\w"`.

Background menu commands sit in a second resource, `nedit.bgMenuCommands`, in
the identical format. One `-import` reads both, so a file carrying both
resources installs a command into both menus in one go.

Because of that backslash rule especially, don't hand-write these. Install the
command through the dialog, run Save Defaults, then copy the entry XNEdit
generated out of `~/.xnedit/nedit.rc`.

## Where XNEdit keeps things

`~/.xnedit/`, created on first run:

| File | Holds |
| --- | --- |
| `nedit.rc` | All preferences, including every Macro menu command, in X resource format |
| `autoload.nm` | Macro code run at startup. Not created for you |
| `nedit.history` | Recently opened files |

Setting `XNEDIT_HOME` moves the whole directory:

```sh
echo "${XNEDIT_HOME:-$HOME/.xnedit}"
```

Note the leading `X`. Classic NEdit used `NEDIT_HOME`; XNEdit does not read it.

XNEdit runs locally on XQuartz on the team's Macs, so this is your own machine.
Nothing here involves a remote host.

## Coming from classic NEdit

XNEdit uses NEdit 5.7's preferences format and the same `nedit` X resource
app-name, so existing settings transfer as they are:

```sh
cp -r ~/.nedit/. ~/.xnedit/
```

Fonts are the exception and will need setting again, since XNEdit renders
antialiased text.

## Troubleshooting

**The command is not in the menu.** It went into `autoload.nm` instead of the
Macro menu. `autoload.nm` defines subroutines; it does not create menu entries.

**It's in the Macro menu but not on right-click.** Those are two dialogs, not
one. Customize Menus > Macro Menu... fills the Macro menu; Customize Menus > Window Background Menu... fills the right-click menu. A command that belongs in
both is pasted into both.

**It was there yesterday and now it's gone.** Save Defaults was skipped.

**It works for you and not for anyone else.** It calls a subroutine from
`autoload.nm` that only you have installed.

**Nothing happens and there's no error.** Start XNEdit from a terminal and add
`t_print()` calls to the macro. That output goes to the terminal, not to any
window.

**It says the file is locked, so nothing was changed.** A locked buffer takes
no writes, so the command stopped before doing anything. XNEdit locks a file it
cannot read as UTF-8, which on NED data is the usual reason;
[when the file is locked](cleaning-pdf-tables.md#when-the-file-is-locked) goes
through the rest of what the window is telling you.

**The command is greyed out.** Requires Selection is ticked and nothing is
selected.
