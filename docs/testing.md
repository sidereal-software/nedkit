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
    flickers windows on and off the screen and takes focus for a couple of
    minutes. macOS has no hidden display to run them on. Nearly all of that
    time is the editor starting up once per test, so the wait grows with the
    suite rather than staying where this page last measured it.

You do not need to start XQuartz first. `$DISPLAY` points at a socket that
starts the server on demand the moment the first test connects.

## What CI runs

The two halves of the suite are also the two workflows.

| Workflow | Job | Runs | What it covers |
| --- | --- | --- | --- |
| `ci.yml` | `lint` | Every push and pull request | ruff, actionlint over the workflows, and `uv lock --check` |
| `ci.yml` | `test` | Every push and pull request | The half that needs no editor: the macro conventions, the generated pages, and a real 3.9 parse of anything the NED team is expected to run |
| `macros.yml` | XNEdit on Linux | Monday morning, 15:17 UTC | The whole suite against XNEdit v1.6.3, built on the runner and cached until either the version or the image changes |
| `macros.yml` | Classic NEdit 5.7 | Monday morning, 15:17 UTC | The same suite against Ubuntu's packaged NEdit, which is how far the macros carry outside the editor they were written for |
| `macros.yml` | The documented macOS build | Monday morning, 15:17 UTC | That the build recipe above still works on a current macOS. It stops at the binary and runs no tests |

`ci.yml` takes about twenty seconds. It deselects the macro tests rather than
letting them skip, so the count at the bottom of the log is the truth about
what ran.

Both editor jobs run under Xvfb with `NEDKIT_REQUIRE_XNEDIT=1`, so a build that
produced nothing comes back red instead of green. Start the workflow by hand
from the Actions tab, or:

```sh
gh workflow run macros.yml
```

Linux rather than macOS, for the one thing macOS cannot do. The macros do not
care which X server they are running on, and Xvfb gives Linux one that needs no
screen. The macOS job installs XQuartz too, because its headers are part of the
build and not only the X server the editor later runs on. That job is watching
Homebrew and the macOS toolchain rather than the macros.

The NEdit job is a gate like any other. Everything that diverges on 5.7 is
marked and skips there, either by an `xnedit-only` file beside the fixture or
by a skip in the test itself, so a red run means a real failure.

Weekly, because what it catches is rarely a bad commit. It is drift underneath
the macros: Ubuntu's Motif changing, a Homebrew formula moving, a runner image
turning over beneath a binary that used to build.

## Adding a test for a new command

A command with no tests fails the suite, by design. Each case is a directory
holding the file before and the file after:

```
tests/fixtures/<command-name>/<case-name>/
    input.txt       what is in the buffer to begin with
    expected.txt    what the command should leave behind
    setup.nm        optional, runs first, e.g. select(0, 12)
    xnedit-only     optional, skips the case on classic NEdit
```

`<command-name>` is the `.nm` filename without its extension, so
`macros/commands/pipe-at-columns.nm` reads its cases from
`tests/fixtures/pipe-at-columns/`.

`setup.nm` runs in the same interpreter as the command, so it is also where a
case puts the cursor with `set_cursor_pos()` and where it answers a prompt the
command is about to raise:

```
$ned_string_dialog_answer = "10, 23"
$ned_string_dialog_button = 2
```

Those two globals are what the harness's stand-in `string_dialog()` hands back.
They default to an empty answer and button 1, so a command that asks a question
and gets no fixture answer has to do nothing. That default is what stops the
blanket tests hanging on it.

Most cases need only the first two files. `xnedit-only` is for the handful that
turn on something XNEdit added and NEdit 5.7 does not have. There are two such
things, and the arithmetic one is the more common of the two:

- A column is a character on XNEdit and a byte on NEdit 5.7, in `$column` and
  in the regex engine alike, so any case putting a pipe or a pad on a line with
  an accented name in it lands somewhere else there.
- Encoding: a buffer locking on a byte it cannot convert, or a BOM that lives
  outside the buffer.

Put the reason in the file and it appears in the skip message. Reach for the
marker only when a case genuinely turns on the fork, because every expected
failure left unmarked is one more reason to stop reading the NEdit job.

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

| What it says | What happened |
| --- | --- |
| XNEdit did not exit | The macro raised an error. XNEdit puts errors in a dialog and waits for a click that never comes, so the harness times out and kills it. Look for a syntax error first |
| The macro exited without reaching its last line | The macro died part way through, so the file it was working on is half-rewritten |

A command that needs to tell the person running it something puts that in a
dialog, which would also wait forever. The harness defines its own `dialog()`
and `string_dialog()` that print instead, so tests can check what a command
would have said and choose what it hears back. Any other subroutine that stops
and waits needs the same treatment before a test can get past it, and a return
value some test can control before that treatment is worth anything.
