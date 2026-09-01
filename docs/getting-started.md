# Getting started

Four steps, from a Mac with nothing on it to a macro that has just changed a
real file. Step 1 is a one-off. After that the nine commands are a download and
a command.

| Step | What it is | Skip it if |
| --- | --- | --- |
| 1. Build XNEdit | a from-source build, once ever | `xnedit -version` already prints a version |
| 2. Import the commands | a download and one command | never, redo it whenever the macros change |
| 3. Save Defaults | one click in the window that opened | never, skipping it discards the install with no error |
| 4. Run one on a real file | the check that any of it worked | never |

A block with a copy button is meant to leave this page: run it, or paste it
where the caption says. A block without one is something to look at.

## 1. Build XNEdit

macOS is the only platform nedkit targets, and there are no prebuilt macOS
binaries, so XNEdit gets compiled from source. That reads worse than it is. The
compile takes seconds, not minutes, and the long part of this step is XQuartz,
a large installer that comes down from xquartz.org.

Start with XQuartz on its own. Homebrew installs it from a pkg and stops to ask
for your password, and anything pasted underneath would be read as the answer:

```{ .sh .copy }
brew install --cask xquartz
```

The rest is one paste:

```{ .sh .copy }
brew install openmotif
git clone https://github.com/unixwork/xnedit.git ~/xnedit
cd ~/xnedit && git checkout v1.6.3 && make macos
echo 'export PATH="$HOME/xnedit/source:$PATH"' >> ~/.zshrc
export PATH="$HOME/xnedit/source:$PATH"
```

`v1.6.3` is the release the macros are tested against, here and in CI. The
build leaves the binary at `~/xnedit/source` and puts nothing on your `$PATH`,
which is what the last two lines are for: the same `export` written into
`~/.zshrc` for every terminal you open from now on, and run once for the one
you are in.

Check:

```{ .sh .copy }
xnedit -version
```

It answers `XNEdit 1.6.3` on the first line, then several lines of build and
display detail.

## 2. Import the commands

All nine commands are in one file, and XNEdit reads it in a single pass:

```{ .sh .copy }
cd ~
curl -O https://nedkit.sidereal.software/nedkit-macros.rc
xnedit -import nedkit-macros.rc
```

An editor window opens and the terminal stays busy until you close it. Leave
the window open. Step 3 happens in it.

## 3. Save Defaults

**Preferences > Save Defaults**, then **OK**.

After an import the confirmation is not the usual one. It ends
`SAVING WILL INCORPORATE SETTINGS FROM FILE`, in capitals, naming the file you
just handed it.

Skipping this looks fine. The commands are in the menu of the running program
whether you click it or not, and quitting then throws them away without asking
or warning. This click is what writes them to `~/.xnedit/nedit.rc`.

## 4. Run one on a real file

Looking at the menu now would prove nothing, since `-import` took effect the
moment you ran it in step 2. So quit XNEdit, and start it again on something to
work on:

```{ .sh .copy }
cd ~
curl -O https://nedkit.sidereal.software/samples/A13L.mod.before
xnedit A13L.mod.before
```

That is a real table pasted out of a paper, with tabs between the columns. Run
**Macro > NED > Expand Tabs**. The tabs become the spaces they were already
showing, and the terminal you launched from says
`42 tab(s) expanded at width 8`.

That checks two things at once. Finding the submenu after a restart is step 3
having stuck, and the report is the macro having actually run.

!!! warning "Before you point one at something you care about"

    A macro writes straight to the buffer with no confirmation step, so a
    pattern that matches more than you meant takes the file with it. Undo
    works, but try each command on a copy first.

## Next

The file you just downloaded is the one the next page works through.
[Cleaning up a pasted table](cleaning-pdf-tables.md) runs every command over it
in the order they are meant to go in, quotes what each one reports, and ends at
a squared-up `.mod` file.

The [command reference](commands.md) is one entry per command, for looking up
what a particular one does and what it refuses to do.

## If something went wrong

| What you see | Why |
| --- | --- |
| `You are in 'detached HEAD' state` | Normal. Git says it for any tag checkout |
| `fatal: destination path ... already exists` | You already cloned; skip to `cd ~/xnedit` |
| `command not found: xnedit` in a new Terminal | The `~/.zshrc` line did not get written, or your shell is not zsh |
| No `NED` submenu after restarting XNEdit | Save Defaults was skipped |
| Some commands present, others missing | One entry would not parse, costing it and everything after it. Download the file again |
| `XNEdit: Parse error in user defined menu item` | The reason for the row above, and the only place it is reported |
| A command is greyed out | It requires a selection and there isn't one |
| A command runs and the terminal says nothing | XNEdit was not launched from that terminal |

## Other ways in

[Installing macros](installing-macros.md) has the routes this page skipped:
installing one command at a time through the dialog, with screenshots of every
field; putting a command on the right-click menu as well; the subroutine
libraries in `macros/lib/`, which are not in the import file; and cloning the
repository, which is what the rest of this site assumes whenever it names a
path like `macros/lib/text.nm`.
