# Getting started

One download and one command installs all nine commands. Ten minutes if you
also have to build XNEdit.

## 1. Install XNEdit

There are no prebuilt macOS binaries, so XNEdit is built from source. Its
makefile has a `macos` build configuration and the dependencies are in
Homebrew:

```sh
brew install --cask xquartz
brew install openmotif
git clone https://github.com/unixwork/xnedit.git
cd xnedit
make macos
```

That leaves the binary at `source/xnedit`, and nothing puts it on your
`$PATH`. Everything below calls it as `xnedit`, so add it for this shell:

```sh
export PATH="$PWD/source:$PATH"
```

Put that line in `~/.zshrc` to keep it past this terminal, or spell out the
full path to `source/xnedit` each time. macOS is the only platform nedkit
targets.

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
[installing macros](installing-macros.md#install-several-commands-at-once) says
why that matters and why re-importing later is safe.

Prefer to install one command at a time, or want to see what the dialog is
doing? [Installing macros](installing-macros.md) walks through it with
screenshots, and each command's page in the [command
reference](commands.md) carries the values the dialog asks for.

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

## Subroutine libraries are separate

Files in `macros/lib/` define subroutines that other macros call. Nothing on
this page depends on them: they are not in the import file, and no command
shipped here calls one. Installing one means appending the file to
`autoload.nm`, which needs a clone of the repo rather than a download.
[Installing macros](installing-macros.md#install-a-subroutine-library) has the
steps.

`XNEDIT_HOME` overrides the configuration directory those files live in. Note
the leading `X`: XNEdit ignores NEdit's `NEDIT_HOME`.
