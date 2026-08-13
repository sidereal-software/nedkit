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

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: Printed by the macro epilogue. Absence means the macro aborted.
SENTINEL = "__NEDKIT_MACRO_OK__"

#: Prefixes a line of stdout standing in for a dialog the macro raised.
DIALOG_MARK = "__NEDKIT_DIALOG__"

#: A user-defined subroutine shadows the built-in of the same name, so a macro
#: that reports through dialog() can be run without a human to click OK. The
#: message is flattened onto one line and handed back through stdout instead.
#: Add string_dialog() or list_dialog() here if a macro ever needs them, but
#: give them a return value some test can control first.
DIALOG_STUB = f"""\
define dialog {{
    t_print("{DIALOG_MARK}" replace_in_string($1, "\\n", "\\\\n", "case", "copy") "\\n")
    return 1
}}
"""

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
    def messages(self) -> str:
        """Everything the macro printed, minus the harness's own bookkeeping."""
        return "\n".join(
            line
            for line in self.stdout.splitlines()
            if not line.startswith(DIALOG_MARK) and SENTINEL not in line
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
            DIALOG_STUB + ("\n" + autoload if autoload else ""), encoding="utf-8"
        )

    @property
    def env(self) -> dict[str, str]:
        return {**os.environ, "XNEDIT_HOME": str(self.home)}

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
        """
        run = self.run_on_bytes(
            macro, b"", workdir, name="evaluate.txt", save=False
        )
        if not run.ok:
            raise AssertionError(f"macro did not complete: {run.describe()}")
        return run.messages.strip("\n")

    def smoke_test(self, workdir: Path) -> None:
        """Prove XNEdit actually runs here, or explain why it doesn't."""
        try:
            run = self.run_on_bytes(
                't_print("")', b"", workdir, name="smoke.txt", save=False
            )
        except OSError as error:
            raise XNEditUnavailable(f"could not start {self.binary}: {error}") from error

        if run.timed_out:
            raise XNEditUnavailable(
                f"{self.binary} started but never exited. Is DISPLAY "
                f"({os.environ.get('DISPLAY', 'unset')}) a working X server?"
            )
        if not run.completed:
            raise XNEditUnavailable(
                f"{self.binary} exited without running the macro.\n{run.describe()}"
            )
