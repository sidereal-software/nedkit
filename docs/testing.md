# Running the tests

Every command is run through a real XNEdit and the resulting buffer compared,
byte for byte, against a file saying what it should have been. A macro rewrites
the buffer with no confirmation step, so the only convincing test is one that
runs it on a file and checks what came back.

```sh
uv run pytest
```

## The two halves

The suite splits in two, and only one half needs an editor.

| | What it covers | Needs XNEdit |
| --- | --- | --- |
| Conventions | Header comments, filenames, the `replace_in_string()` trap, formatting | No |
| Macros | What each command actually does to a file | Yes |

Without XNEdit installed, the second half **skips** and the run still goes
green. That result says the macros are tidy, not that they work.

```sh
uv run pytest -m "not xnedit"   # just the conventions, deliberately
```

## Building an XNEdit to test against

There are no prebuilt macOS binaries, so this is a one-time build from source.
XQuartz is the X server it runs on, and openmotif is the widget toolkit.

```sh
brew install --cask xquartz
brew install openmotif

git clone https://github.com/unixwork/xnedit.git
cd xnedit
git checkout v1.6.3
make macos
```

The binary lands at `source/xnedit`. Point the suite at it and tell it to
insist:

```sh
export NEDKIT_XNEDIT=/path/to/xnedit/source/xnedit
export NEDKIT_REQUIRE_XNEDIT=1
uv run pytest
```

`NEDKIT_REQUIRE_XNEDIT=1` turns those skips into errors, so the run can no
longer pass by testing nothing. Set it whenever a green result has to mean
something. If `xnedit` is already on your `$PATH`, `NEDKIT_XNEDIT` is optional.

!!! warning "The tests are not headless"

    Each test opens a real XNEdit window for a second or two, so a full run
    flickers windows on and off the screen and takes focus for about 45
    seconds. macOS has no hidden display to run them on.

You do not need to start XQuartz first. `$DISPLAY` points at a socket that
starts the server on demand the moment the first test connects.

## Adding a test for a new command

A command with no tests fails the suite, by design. Each case is a directory
holding the file before and the file after:

```
tests/fixtures/<command-name>/<case-name>/
    input.txt       what is in the buffer to begin with
    expected.txt    what the command should leave behind
    setup.nm        optional, runs first, e.g. select(0, 12)
```

`<command-name>` is the `.nm` filename without its extension, so
`macros/commands/align-columns.nm` reads its cases from
`tests/fixtures/align-columns/`.

The two files are compared without being decoded, so trailing spaces, tabs and
a missing final newline all count. That is deliberate. Write them with a
script rather than an editor if the whitespace matters, since most editors will
quietly tidy it for you.

Worth a case each time: the ordinary input, an input the command should leave
completely alone, and an empty file. The middle one catches the most damaging
class of bug these macros have, where a pattern that matches nothing returns an
empty string and the command writes that over your file.

## When a test fails

A failure names the command and the case, and prints both buffers with spaces
as `·` and tabs as `→`, because otherwise the interesting failures are
invisible.

Two failures mean something other than a wrong answer:

- **"XNEdit did not exit"** is a macro that raised an error. XNEdit puts errors
  in a dialog and waits for a click that never comes, so the harness times out
  and kills it. Look for a syntax error first.
- **"the macro exited without reaching its last line"** is a macro that died
  part way through, which means the file it was working on is half-rewritten.

A command that needs to tell the person running it something puts that in a
dialog, which would also wait forever. The harness defines its own `dialog()`
that prints instead, so tests can check what a command would have said. Any
other subroutine that stops and waits needs the same treatment before a test
can get past it.
