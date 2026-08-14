"""Running XNEdit macros from Python.

XNEdit executes a macro against a real file when it is started with ``-do``:

    xnedit -do '<macro>' file.txt

That is the whole mechanism. The awkward parts are all about failure. A macro
with a syntax error, or one that trips over a read-only buffer, raises a modal
dialog and then waits forever, so every run needs a timeout and something to
kill. And because a macro that dies mid-way leaves the file half-written, the
runner appends a sentinel to the end of every macro: if the sentinel doesn't
come back on stdout, the macro did not reach its last line, whatever the file
on disk looks like.

XNEdit needs an X display even for this. On the team's Macs that means XQuartz,
which launchd starts on demand the first time something connects.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: Printed by the macro epilogue. Absence means the macro aborted.
SENTINEL = "__NEDKIT_MACRO_OK__"

#: Prefixes a line of stdout standing in for a dialog the macro raised.
DIALOG_MARK = "__NEDKIT_DIALOG__"

#: Prefixes a line of stdout standing in for a prompt the macro put up.
#: Deliberately not DIALOG_MARK: ``assert run.dialogs == []`` has to keep
#: meaning "nothing a human had to acknowledge", and a prompt the macro asked
#: for is not that.
PROMPT_MARK = "__NEDKIT_PROMPT__"

#: Separates whatever the editor printed on startup from the macro's output.
OUTPUT_MARK = "__NEDKIT_OUTPUT__"

#: A user-defined subroutine shadows the built-in of the same name, so a macro
#: that reports through dialog() can be run without a human to click OK. The
#: message is flattened onto one line and handed back through stdout instead.
DIALOG_STUB = f"""\
define dialog {{
    t_print("{DIALOG_MARK}" replace_in_string($1, "\\n", "\\\\n", "case", "copy") "\\n")
    return 1
}}
"""

#: The same trick for string_dialog(), which needs an answer as well as a
#: button. A fixture picks both by assigning these globals in its setup.nm,
#: which is prepended to the macro body and runs in the same interpreter.
#:
#: The globals are initialised here because referencing an unset global is a
#: runtime error, and a runtime error is a modal dialog and a hung run. The
#: default of an empty answer is doing real work: a command that reaches
#: string_dialog() with no fixture saying otherwise gets nothing back and must
#: no-op, which is what keeps the blanket tests in test_commands.py from
#: hanging on a command that asks a question.
PROMPT_STUB = f"""\
$ned_string_dialog_answer = ""
$ned_string_dialog_button = 1

define string_dialog {{
    t_print("{PROMPT_MARK}" replace_in_string($1, "\\n", "\\\\n", "case", "copy") "\\n")
    $string_dialog_button = $ned_string_dialog_button
    return $ned_string_dialog_answer
}}
"""

#: Everything the harness puts in autoload.nm before a macro runs. Add
#: list_dialog() here if a macro ever needs it, but give it a return value some
#: test can control first.
STUBS = DIALOG_STUB + "\n" + PROMPT_STUB

#: Written to the throwaway XNEDIT_HOME so a run never depends on, or disturbs,
#: whatever the developer has in ~/.xnedit.
PREFERENCES = """\
! Written by nedkit's test harness. Not for humans.
nedit.autoSave: False
nedit.saveOldVersion: False
nedit.warnFileMods: False
nedit.warnRealFileMods: False
nedit.openInTab: False
! True is the XNEdit default, and the safe setting: a file that isn't valid
! UTF-8 gets locked rather than silently re-encoded on save.
nedit.lockEncodingError: True
! Also the default. Pinned because it changes what lands on disk: saving adds a
! final newline to a file that lacks one, whatever the macro did.
nedit.appendLF: True
"""


class XNEditUnavailable(RuntimeError):
    """No usable XNEdit, so the execution tests cannot run."""


@dataclass(frozen=True)
class MacroRun:
    """What happened when a macro ran."""

    returncode: int
    stdout: str
    timed_out: bool
    completed: bool
    """The macro reached its final line."""
    output: bytes | None
    """The file's contents afterwards, or None if it was removed."""

    @property
    def ok(self) -> bool:
        return self.completed and not self.timed_out

    @property
    def dialogs(self) -> list[str]:
        """Messages the macro tried to put in front of a human.

        Newlines come back as a literal ``\\n``, since each dialog is flattened
        onto one line of stdout.
        """
        return [
            line[len(DIALOG_MARK) :]
            for line in self.stdout.splitlines()
            if line.startswith(DIALOG_MARK)
        ]

    @property
    def prompts(self) -> list[str]:
        """Questions the macro put to a human, in the order it asked them.

        Flattened the same way as :attr:`dialogs`. What came back is whatever
        ``$ned_string_dialog_answer`` was set to, which is the fixture's
        business rather than this one's.
        """
        return [
            line[len(PROMPT_MARK) :]
            for line in self.stdout.splitlines()
            if line.startswith(PROMPT_MARK)
        ]

    @property
    def messages(self) -> str:
        """Everything the macro printed, minus the harness's own bookkeeping."""
        return "\n".join(
            line
            for line in self.stdout.splitlines()
            if not line.startswith(DIALOG_MARK)
            and not line.startswith(PROMPT_MARK)
            and SENTINEL not in line
        )

    def describe(self) -> str:
        """A failure message worth reading."""
        if self.timed_out:
            return (
                "XNEdit did not exit. A macro that fails opens a modal dialog and "
                "waits, so this is almost always a syntax or runtime error in the "
                f"macro.\nstdout:\n{self.stdout or '(empty)'}"
            )
        if not self.completed:
            return (
                "the macro exited without reaching its last line, so it aborted "
                f"part way through.\nexit code: {self.returncode}\n"
                f"stdout:\n{self.stdout or '(empty)'}"
            )
        return f"exit code: {self.returncode}\nstdout:\n{self.stdout or '(empty)'}"


def find_binary() -> Path | None:
    """Locate XNEdit: ``NEDKIT_XNEDIT`` first, then ``$PATH``."""
    override = os.environ.get("NEDKIT_XNEDIT")
    if override:
        path = Path(override).expanduser()
        return path if path.is_file() else None

    found = shutil.which("xnedit")
    return Path(found) if found else None


class XNEditRunner:
    """Runs macros in an XNEdit configured from scratch for the test run."""

    def __init__(
        self,
        binary: Path,
        home: Path,
        *,
        autoload: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.binary = binary
        self.home = home
        self.timeout = timeout

        home.mkdir(parents=True, exist_ok=True)
        (home / "nedit.rc").write_text(PREFERENCES, encoding="utf-8")
        (home / "autoload.nm").write_text(
            STUBS + ("\n" + autoload if autoload else ""), encoding="utf-8"
        )

    @functools.cached_property
    def version(self) -> str:
        """What the editor calls itself: ``XNEdit 1.6.3``, ``NEdit 5.7``.

        ``-version`` prints and exits without opening a display, so this is
        cheap and works before any X server is involved.
        """
        try:
            result = subprocess.run(
                [str(self.binary), "-version"],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return (result.stdout or result.stderr).strip().split("\n")[0].strip()

    @property
    def is_xnedit(self) -> bool:
        """False for classic NEdit, which the suite also runs against.

        The two share a macro language, so nearly every test applies to both.
        The handful that depend on the fork are the ones about encoding: XNEdit
        added Unicode support and NEdit 5.7 predates it.
        """
        return self.version.lower().startswith("xnedit")

    @property
    def env(self) -> dict[str, str]:
        # NEDIT_HOME as well as XNEDIT_HOME. XNEdit renamed the variable and
        # ignores the old one, so setting both costs nothing there and is what
        # lets NEDKIT_XNEDIT point at a classic NEdit 5.7 instead: same macro
        # language, same ~/.nedit layout, different variable. CI runs the suite
        # through both.
        return {
            **os.environ,
            "XNEDIT_HOME": str(self.home),
            "NEDIT_HOME": str(self.home),
        }

    def run_on_file(self, macro: str, path: Path, *, save: bool = True) -> MacroRun:
        """Run ``macro`` against ``path``, saving afterwards unless told not to.

        The file is modified in place, so hand this a copy.
        """
        epilogue = ["save()"] if save else []
        epilogue.append(f't_print("{SENTINEL}\\n")')
        # close("nosave") rather than a bare exit(): exiting with a modified
        # buffer raises a "save before closing?" dialog and hangs, which a
        # macro that edits without saving would otherwise do every time.
        # Whether the save actually landed is settled by reading the file back,
        # not by trusting this.
        epilogue += ['close("nosave")', "exit()"]
        full = macro.rstrip() + "\n" + "\n".join(epilogue) + "\n"

        process = subprocess.Popen(
            [str(self.binary), "-do", full, str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=self.env,
            text=True,
            errors="replace",
        )

        timed_out = False
        try:
            stdout = process.communicate(timeout=self.timeout)[0]
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            stdout = process.communicate()[0]

        return MacroRun(
            returncode=process.returncode,
            stdout=stdout,
            timed_out=timed_out,
            completed=SENTINEL in stdout,
            output=path.read_bytes() if path.exists() else None,
        )

    def run_on_bytes(
        self,
        macro: str,
        content: bytes,
        workdir: Path,
        *,
        name: str = "buffer.txt",
        save: bool = True,
    ) -> MacroRun:
        """Run ``macro`` against a throwaway file holding ``content``."""
        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / name
        path.write_bytes(content)
        return self.run_on_file(macro, path, save=save)

    def evaluate(self, macro: str, workdir: Path) -> str:
        """Run ``macro`` for its ``t_print()`` output and return that output.

        Used for exercising subroutine libraries, where the assertion is about
        a return value rather than about a file. Nothing is saved.

        The editor gets to stdout first: classic NEdit announces that it is
        converting old preferences, and anything else it has to say arrives
        before the macro runs. Only what follows the marker below is the
        macro's own output.
        """
        run = self.run_on_bytes(
            f't_print("{OUTPUT_MARK}\\n")\n{macro}',
            b"",
            workdir,
            name="evaluate.txt",
            save=False,
        )
        if not run.ok:
            raise AssertionError(f"macro did not complete: {run.describe()}")

        lines = run.messages.split("\n")
        if OUTPUT_MARK in lines:
            lines = lines[lines.index(OUTPUT_MARK) + 1 :]
        return "\n".join(lines).strip("\n")

    def smoke_test(self, workdir: Path) -> None:
        """Prove XNEdit actually runs here, or explain why it doesn't."""
        try:
            run = self.run_on_bytes(
                't_print("")', b"", workdir, name="smoke.txt", save=False
            )
        except OSError as error:
            raise XNEditUnavailable(
                f"could not start {self.binary}: {error}"
            ) from error

        if run.timed_out:
            raise XNEditUnavailable(
                f"{self.binary} started but never exited. Is DISPLAY "
                f"({os.environ.get('DISPLAY', 'unset')}) a working X server?"
            )
        if not run.completed:
            raise XNEditUnavailable(
                f"{self.binary} exited without running the macro.\n{run.describe()}"
            )
