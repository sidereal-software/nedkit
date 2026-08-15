# Getting started

## Installing XNEdit

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

macOS is the only platform nedkit targets.

## Installing the macros

Macro menu commands live in `~/.xnedit/nedit.rc`, under the
`nedit.macroCommands` X resource. Getting one there means pasting it through
**Preferences > Default Settings > Customize Menus > Macro Menu** and then
**Preferences > Save Defaults**. [Installing macros](installing-macros.md) walks
through the dialog with screenshots.

Each command's page in the [command reference](commands.md) carries the values
the dialog asks for and the macro body itself, folded away under a toggle so
you can copy it straight off this site.

Subroutine libraries work differently. They are appended to
`~/.xnedit/autoload.nm`, which XNEdit runs at startup, and they add nothing to
any menu:

```sh
cat macros/lib/text.nm >> "${XNEDIT_HOME:-$HOME/.xnedit}/autoload.nm"
```

Restart XNEdit afterwards. `autoload.nm` is not created for you.

`XNEDIT_HOME` overrides the configuration directory. Note the leading `X`:
XNEdit ignores NEdit's `NEDIT_HOME`.

## Checking that it worked

Open a file, then look under **Macro** in the menu bar. The commands appear in
a `NED` submenu. If the submenu is missing, the usual cause is that the macro
went into `autoload.nm` instead of the macro menu, or that **Save Defaults**
was never run.

!!! warning "Before you run one on something you care about"

    A macro writes straight to the buffer with no confirmation step, so a
    pattern that matches more than you meant takes the file with it. Undo
    works, but try each command on a copy first.
