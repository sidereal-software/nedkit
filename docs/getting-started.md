# Getting started

One download and one command installs all nine commands. Building XNEdit comes
first, if you do not have it already.

## 1. Install XNEdit

There are no prebuilt macOS binaries, so XNEdit is built from source. Its
makefile has a `macos` build configuration and the dependencies are in
Homebrew:

```sh
brew install --cask xquartz
brew install openmotif

cd ~
git clone https://github.com/unixwork/xnedit.git
cd xnedit
git checkout v1.6.3
make macos
```

`v1.6.3` is the release the macros are tested against, here and in CI. The
checkout answers with a paragraph beginning `You are in 'detached HEAD' state`.
Git says that whenever you check out a tag rather than a branch, so it is
correct here and nothing has gone wrong. The `cd ~` puts the clone at
`~/xnedit`, which matters in a moment: the permanent `PATH` line has to name
that directory in full.

That leaves the binary at `source/xnedit`, and nothing puts it on your `$PATH`.
Everything below calls it as `xnedit`, so add it for this shell:

```sh
export PATH="$PWD/source:$PATH"
```

That one works because you are still in the directory you built in, and it
lasts until you close the terminal. To keep `xnedit` past that, write the path
out in full in `~/.zshrc`:

```sh
export PATH="$HOME/xnedit/source:$PATH"
```

The `$PWD` version cannot go in `~/.zshrc`. That file runs at the start of
every shell, and `$PWD` is then wherever that shell opened, which for a new
Terminal window is your home directory: the line quietly becomes
`$HOME/source`, and there is no such directory. Nothing reports it either.
`xnedit` is simply not found, in some later terminal rather than in the one
where the line was written.

macOS is the only platform nedkit targets.

## 2. Import the commands

Download [nedkit-macros.rc](nedkit-macros.rc){ download }, then hand it to
XNEdit:

```sh
xnedit -import ~/Downloads/nedkit-macros.rc
```

In the window that opens, run **Preferences > Save Defaults** and click **OK**.
After an import the confirmation is not the usual one: it ends
`SAVING WILL INCORPORATE SETTINGS FROM FILE`, in capitals, naming the file you
just handed it.

That is the whole install. The file carries all nine commands, and the two that
belong on the right-click menu as well are in it twice, once for each menu.
Importing merges into whatever you already have rather than replacing it, and
[installing macros](installing-macros.md#install-every-command-at-once) says
why that matters and why re-importing later is safe.

Prefer to install one command at a time, or want to see what the dialog is
doing? [Installing macros](installing-macros.md) walks through it with
screenshots, and each command's page in the [command
reference](commands.md) carries the values the dialog asks for.

### Subroutine libraries are not in that file

Files in `macros/lib/` define subroutines that other macros call. Nothing on
this page depends on them: they are not in the import file, and no command
shipped here calls one. Installing one means appending the file to
`autoload.nm`, which needs [a clone](#getting-the-repository) rather than a
download. [Installing macros](installing-macros.md#install-a-subroutine-library)
has the steps.

`XNEDIT_HOME` overrides the configuration directory those files live in. Note
the leading `X`: XNEdit ignores NEdit's `NEDIT_HOME`.

## 3. Check that it worked

Open a file and look under **Macro** in the menu bar. The commands are in a
`NED` submenu:

| What you see | Why |
| --- | --- |
| No `NED` submenu at all | **Save Defaults** was skipped, so the import lasted only until you quit, and quitting discarded it silently rather than asking |
| Some commands in the submenu, others missing | One entry would not parse, which costs that entry and the ones following it. The ones read before it were already installed, which is what makes the menu look half built |
| `XNEdit: Parse error in user defined menu item` in the terminal | The reason for the row above, and the only place XNEdit reports it. The file was edited or truncated on the way here. Download it again |
| The submenu, but a command is greyed out | It requires a selection and there isn't one |

!!! warning "Before you run one on something you care about"

    A macro writes straight to the buffer with no confirmation step, so a
    pattern that matches more than you meant takes the file with it. Undo
    works, but try each command on a copy first.

## Getting the repository

The import file is one way in, and it carries the menu commands and nothing
else. The other is a clone, which is what the rest of this site assumes
whenever it names a path like `macros/lib/text.nm`:

```sh
cd ~
git clone https://github.com/sidereal-software/nedkit.git
cd nedkit
```

| Route | What it gets you |
| --- | --- |
| The [nedkit-macros.rc](nedkit-macros.rc){ download } download | The nine menu commands, installed in one import |
| A clone | The same nine as `macros/commands/*.nm`, plus the subroutine libraries, the sample files the guides work through, and `ned-transients` |

There is nothing to build or install. The macros are text files XNEdit reads,
and `python/ned-transients` is standard-library Python 3.9 you hand to
`python3` where it sits. A command on these pages that names a path without
saying where to run it means from the top of the clone, `~/nedkit` above.

## Then clean up a table

That is what the commands are for, and they are meant to run in a particular
order. [Cleaning up a pasted table](cleaning-pdf-tables.md) takes a real paste
out of a paper, tab separated with en dashes for minus signs, and works it
through every command to a squared-up `.mod` file, with the report each one
prints along the way.

Two pages to keep beside it: the [command reference](commands.md), which is one
entry per command, and [character replacements](character-replacements.md),
which lists every character the two rewriting commands touch and every one they
deliberately leave alone.
