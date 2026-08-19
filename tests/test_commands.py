"""Run every menu command against its fixtures.

A command in ``macros/commands/<name>.nm`` is tested by the directories under
``tests/fixtures/<name>/``. Each of those is one case:

    tests/fixtures/trim-trailing-blanks/basic/
        input.txt       the buffer before
        expected.txt    the buffer after, byte for byte
        setup.nm        optional macro run first, e.g. select(0, 12)
        xnedit-only     optional; skip this case on classic NEdit, and say why

Fixtures are compared as bytes, because NED's data files are not reliably
UTF-8 and the difference between a stripped tab and a stripped space is the
entire point of some of these commands.

``xnedit-only`` exists because CI runs the same suite through NEdit 5.7 to see
how far the macros carry. Almost all of them do. The exceptions are the cases
about encoding, which XNEdit added and 5.7 predates, and marking those is what
keeps a real regression on NEdit visible instead of lost among expected noise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse
from nedkit.macro import command_files

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"
FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _case_dirs(command: Path) -> list[Path]:
    """Every fixture case for one command, in name order.

    A case is a directory holding an ``input.txt``. One definition, used by
    everything below: counting a directory without one as a case would let a
    half-written fixture satisfy ``test_every_command_has_fixtures`` while
    being invisible to every test that actually runs the editor.
    """
    case_root = FIXTURE_ROOT / command.stem
    if not case_root.is_dir():
        return []
    return [
        case for case in sorted(case_root.iterdir()) if (case / "input.txt").is_file()
    ]


def _cases() -> list[tuple[Path, Path]]:
    return [
        (command, case)
        for command in command_files(REPO_ROOT)
        for case in _case_dirs(command)
    ]


def _readable(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace").replace(" ", "·").replace("\t", "→")


def _fork_specific(case: Path) -> str | None:
    """Why this case only applies to XNEdit, if it is marked that way."""
    marker = case / "xnedit-only"
    return marker.read_text(encoding="utf-8").strip() if marker.is_file() else None


def _skip_unless_xnedit(case: Path, runner: XNEditRunner) -> None:
    reason = _fork_specific(case)
    if reason and not runner.is_xnedit:
        pytest.skip(f"{case.name} is XNEdit-only: {reason} (running {runner.version})")


@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_every_command_has_fixtures(command: Path) -> None:
    """A command with no fixtures is untested, which should be loud."""
    assert _case_dirs(command), (
        f"{command.name} has no fixtures. Add at least one case under "
        f"tests/fixtures/{command.stem}/<case>/ with input.txt and expected.txt."
    )


@pytest.mark.xnedit
@pytest.mark.parametrize(
    ("command", "case"), _cases(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_command_against_fixture(
    command: Path, case: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    _skip_unless_xnedit(case, runner)

    macro = parse(command)
    setup = case / "setup.nm"
    body = macro.body
    if setup.is_file():
        body = setup.read_text(encoding="utf-8").rstrip() + "\n" + body

    run = runner.run_on_bytes(
        body, (case / "input.txt").read_bytes(), tmp_path, name="input.txt"
    )
    assert run.ok, f"{command.name} on {case.name}: {run.describe()}"

    expected = (case / "expected.txt").read_bytes()
    assert run.output == expected, (
        f"{command.name} on {case.name} produced the wrong buffer "
        "(· is a space, → a tab)\n"
        f"expected: {_readable(expected)!r}\n"
        f"     got: {_readable(run.output or b'')!r}"
    )


#: Commands this test cannot say anything about, and where their second run is
#: covered instead. It runs a body with no ``setup.nm``, which leaves both
#: piping commands unable to pipe anything at all: one gets the harness's empty
#: answer to its prompt and stops at the ``ncols == 0`` guard, the other reads
#: ``$column`` as 0 on a freshly opened buffer and refuses column 0. Comparing
#: either no-op against itself passes whatever the column arithmetic does.
RERUN_COVERED_ELSEWHERE = {
    "pipe-at-columns": "tests/test_pipe_columns.py",
    "pipe-at-cursor-column": "tests/test_pipe_columns.py",
}


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_command_is_idempotent(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """Running a command twice does the same as running it once.

    Not a law of nature, but it holds for every cleanup command written so far,
    and a command that fails it is worth a second look before it ships.
    """
    if command.stem in RERUN_COVERED_ELSEWHERE:
        pytest.skip(
            f"{command.name} does nothing at all without a setup.nm to aim it, "
            f"so a second run here would prove nothing. Its re-run behaviour is "
            f"covered by {RERUN_COVERED_ELSEWHERE[command.stem]}."
        )

    cases = [
        case
        for case in _case_dirs(command)
        if (case / "expected.txt").is_file()
        and (runner.is_xnedit or not _fork_specific(case))
    ]
    if not cases:
        pytest.skip("no fixtures that apply to this editor")

    macro = parse(command)
    for case in cases:
        settled = (case / "expected.txt").read_bytes()
        run = runner.run_on_bytes(
            macro.body, settled, tmp_path, name=f"{case.name}.txt"
        )
        assert run.ok, f"{command.name} on settled input: {run.describe()}"
        assert run.output == settled, (
            f"{command.name} changed {case.name} on a second run, "
            "so it is not idempotent"
        )


#: UTF-8 for U+00B0 DEGREE SIGN, which every one of the buffers below carries
#: through the edit under test. It is the right character for the job because
#: no command maps it: ``test_the_degree_sign_is_in_neither_table`` in
#: tests/test_character_table.py is what keeps that true. It is also two bytes,
#: so a buffer re-encoded to latin-1 on the way out comes back one byte short
#: and a dropped character comes back two short.
DEGREE = "°".encode()

#: Per command, a prologue and a buffer that command genuinely rewrites, each
#: holding a degree sign somewhere the rewrite has to carry through. The
#: prologue is what a fixture would put in its ``setup.nm``; the two piping
#: commands do nothing at all without one.
#:
#: An input a command leaves alone is no good here. The whole failure being
#: guarded against happens on the way back out of the macro, so a command that
#: never writes keeps every byte it was given no matter how broken it is.
REWRITES: dict[str, tuple[str, bytes]] = {
    "trim-trailing-blanks": ("", "NGC 4151   25° C   \nsecond   \n".encode()),
    "pad-columns": ("", "NGC 4151|25° C\nsecond|x\n".encode()),
    "normalize-characters": ("", "NGC 4151 – 25° C\n".encode()),
    "fold-letters-to-ascii": ("", "Balázs 25° C\n".encode()),
    "expand-tabs": ("", "NGC 4151\t25° C\n".encode()),
    # The selection stops before the degree sign, because a degree sign inside
    # it is not a coordinate and would stop the command instead of rewriting.
    "ra-to-ned-form": ("select(0, 11)", "03:28:45.99 25° C\n".encode()),
    "dec-to-ned-form": ("select(0, 12)", "-00:46:03.66 25° C\n".encode()),
    "pipe-at-cursor-column": (
        "set_cursor_pos(10)",
        "NGC 4472   25° C\nIC 3583    25° C\n".encode(),
    ),
    "pipe-at-columns": (
        '$ned_string_dialog_answer = "10"\n$ned_string_dialog_button = 1',
        "NGC 4472   25° C\nIC 3583    25° C\n".encode(),
    ),
}


def _rewrite_case(command: Path) -> tuple[str, bytes]:
    setup, source = REWRITES.get(command.stem, ("", b""))
    assert source, (
        f"{command.name} is not in REWRITES, so nothing checks that it carries "
        f"a non-ASCII character through an edit. Add an entry: a buffer this "
        f"command rewrites, holding a degree sign, and whatever setup it needs "
        f"to do the rewrite."
    )
    return setup, source


def _with_setup(command: Path, setup: str) -> str:
    body = parse(command).body
    return setup.rstrip() + "\n" + body if setup else body


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_command_keeps_a_non_ascii_character_when_it_rewrites_the_buffer(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """The characters NED's files carry have to survive the rewrite.

    Half the point of Normalize Characters is that it keeps a degree sign, a
    Greek letter or an accented name rather than mangling it, and a command
    that rewrites the whole buffer is one bad round trip away from doing that
    silently. So each command is handed a buffer it really does edit, and the
    degree sign in it has to come back as the same two bytes.

    Both halves of that matter. The rewrite is checked as well as the bytes,
    because a command that wrote nothing keeps every byte it was given, which
    is a green tick and no information.

    The sample assumes the UTF-8 locale the workflows pin. Under a latin-1 one
    the editor would read the degree sign as two characters, one of them an
    accented capital A that Fold Letters to ASCII has an answer for.
    """
    setup, source = _rewrite_case(command)
    run = runner.run_on_bytes(
        _with_setup(command, setup), source, tmp_path, name="degree.txt"
    )

    assert run.ok, f"{command.name}: {run.describe()}"
    assert run.output is not None
    assert run.output != source, (
        f"{command.name} did not write, so this proves nothing. Give it an "
        f"input it edits: {source!r}"
    )
    assert run.output.count(DEGREE) == source.count(DEGREE), (
        f"{command.name} went in with {source.count(DEGREE)} degree sign(s) and "
        f"came out with {run.output.count(DEGREE)}, so one was re-encoded or "
        f"dropped: {run.output!r}"
    )


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_a_command_does_not_hang_on_a_buffer_xnedit_locked(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """A buffer the editor could not decode is read-only, and that is silent.

    XNEdit locks a file holding a byte it cannot read as part of a character,
    so ``replace_range()`` does nothing and raises nothing. Every command has
    to come back from that rather than put up an error dialog, which with
    nobody to click OK is a hang.

    Each command gets the buffer it was going to edit in the test above, with
    the degree sign left as the bare latin-1 byte a NED file would carry. So
    the command is aimed at an edit it genuinely wants to make and the lock is
    the only reason it does not land.

    Nothing here reads the command's own report, and that is deliberate: only
    the bytes settle whether anything was written. That is the same gap that
    made the byte-survival check this test was split out of pass against every
    mutant, since nothing had been written and so nothing could be lost. What
    the commands say about it is the test below.
    """
    if not runner.is_xnedit:
        pytest.skip(
            "the lock is XNEdit's encoding handling, which NEdit 5.7 predates: "
            f"it reads the file as bytes and edits it happily (running "
            f"{runner.version})"
        )

    setup, decodable = _rewrite_case(command)
    source = decodable.replace(DEGREE, b"\xb0")
    assert source != decodable, f"{command.name}: no degree sign to break"

    probe = 't_print("locked=" $locked "\\n")'
    run = runner.run_on_bytes(
        _with_setup(command, setup) + "\n" + probe,
        source,
        tmp_path,
        name="undecodable.txt",
    )

    assert run.ok, f"{command.name}: {run.describe()}"
    assert "locked=1" in run.messages, (
        f"XNEdit did not lock a buffer holding an undecodable byte, so this "
        f"test is no longer about the lock: {run.messages!r}"
    )
    assert run.output == source, (
        f"{command.name} wrote to a locked buffer: {run.output!r}"
    )


#: What a command prints in the terminal when it refuses to touch the buffer.
#: The same words the tab refusal uses, because it is the same kind of answer:
#: the command ran, found it could do nothing, and did nothing.
REFUSED = "nothing changed"


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_a_command_refuses_a_buffer_xnedit_locked_and_says_so(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """The other half of the test above: what the person running it is told.

    Nothing a command computes can reach a locked buffer, so its report is the
    only output it has, and for a while every one of them reported what it had
    computed instead. Trim Trailing Blanks announced two trimmed lines that
    were still there. Fold Letters to ASCII listed Greek letters by line and
    column and said the cursor was parked on the first, having moved nothing
    and folded nothing. That sends someone off to inspect replacements that
    were never made.

    So the refusal is what gets asserted here rather than a count: the terminal
    line says nothing changed, and the dialog names the file, says nothing was
    changed, and gives the encoding lock as the usual reason.

    The same buffer as the test above, and the byte check is repeated, because
    a command that reported a refusal and wrote anyway would be worse than
    either failure on its own.
    """
    if not runner.is_xnedit:
        pytest.skip(
            "the lock is XNEdit's encoding handling, which NEdit 5.7 predates: "
            f"it reads the file as bytes and edits it happily (running "
            f"{runner.version})"
        )

    setup, decodable = _rewrite_case(command)
    source = decodable.replace(DEGREE, b"\xb0")
    assert source != decodable, f"{command.name}: no degree sign to break"

    run = runner.run_on_bytes(
        _with_setup(command, setup), source, tmp_path, name="undecodable.txt"
    )

    assert run.ok, f"{command.name}: {run.describe()}"
    assert run.output == source, (
        f"{command.name} wrote to a locked buffer: {run.output!r}"
    )
    assert REFUSED in run.messages, (
        f"{command.name} did not say it had left the buffer alone. Its summary "
        f"has to report the refusal rather than the work it would have done: "
        f"{run.messages!r}"
    )

    assert len(run.dialogs) == 1, (
        f"{command.name} should put the reason in front of whoever ran it, "
        f"once: {run.dialogs}"
    )
    message = run.dialogs[0]
    assert message.startswith("undecodable.txt is locked, so nothing was changed"), (
        f"{command.name} does not name the file and say nothing changed: {message!r}"
    )
    assert "UTF-8" in message, (
        f"{command.name} does not say why the file is likely to be locked, "
        f"which is the one thing the person reading this cannot work out from "
        f"the buffer: {message!r}"
    )

    # Only Pipe at Columns asks anything, and the guard sits in front of its
    # prompt on purpose. A question whose answer cannot be acted on is worse
    # than no question.
    assert run.prompts == [], (
        f"{command.name} put a question to the user before finding out it "
        f"could not write: {run.prompts}"
    )


#: The commands whose header promises that a run finding nothing leaves the
#: buffer, the undo history and the modified flag untouched, each with a buffer
#: it has nothing to do with. Add a command here when it makes that promise.
#:
#: Nothing derives this from the macros, because the three of them word the
#: promise differently and matching on the prose would be worse than a list.
FINDS_NOTHING: dict[str, bytes] = {
    "normalize-characters": b"NGC 4472 z=0.003326\n",
    "fold-letters-to-ascii": b"NGC 4472 z=0.003326\n",
    "trim-trailing-blanks": b"NGC 4472 z=0.003326\n",
}


@pytest.mark.xnedit
@pytest.mark.parametrize("command", sorted(FINDS_NOTHING))
def test_command_that_finds_nothing_leaves_the_modified_flag_alone(
    command: str, runner: XNEditRunner, tmp_path: Path
) -> None:
    """The header's promise, which no byte comparison can reach.

    Each of these guards its write with ``if (cleaned != original)``, and the
    point of the guard is that the bytes are identical either way. Take it out
    and every fixture still passes; what changes is that the editor marks the
    file dirty, puts a rewrite of the whole buffer on the undo stack, and asks
    the user to save a file nothing happened to.

    Run without saving, so the flag read back is the one the macro left rather
    than the one ``save()`` cleared.
    """
    source = FINDS_NOTHING[command]
    body = parse(COMMANDS / f"{command}.nm").body
    probe = 't_print("modified=" $modified "\\n")'
    run = runner.run_on_bytes(
        body + "\n" + probe, source, tmp_path, name="quiet.txt", save=False
    )

    assert run.ok, f"{command}: {run.describe()}"
    assert "modified=0" in run.messages, (
        f"{command} marked the buffer modified with nothing to change, so it "
        f"put a no-op rewrite on the undo stack: {run.messages!r}"
    )


#: Assignments a command must still have room for. Twenty table pairs, which is
#: a group of accented letters or a run of Greek, so the check fails while there
#: is still somewhere to put the next one.
HEADROOM = 40


@pytest.mark.xnedit
@pytest.mark.parametrize("command", command_files(REPO_ROOT), ids=lambda p: p.stem)
def test_command_has_room_to_grow(
    command: Path, runner: XNEditRunner, tmp_path: Path
) -> None:
    """Every command compiles with room to spare in XNEdit's program array.

    XNEdit parses a macro into ``static Inst Prog[4096]`` and refuses anything
    longer, whatever route it was installed by. Ordinary macro code never comes
    close; a lookup table is nothing but assignments, at nine instructions each,
    and ``fold-letters-to-ascii`` already uses about two thirds of the budget.

    Growing a table past the limit is caught today only as a thirty second
    timeout on every fixture the command has, because the parse error arrives as
    a modal dialog that waits for a human who is not there. That is a wretched
    way to learn about a fixed-size array, so this pads each command out and
    asks the editor directly, while there is still room to act on the answer.
    """
    filler = "\n".join(f'headroom_probe["{i}"] = "{i}"' for i in range(HEADROOM))
    body = parse(command).body + "\n" + filler + "\n"

    run = runner.run_on_bytes(body, b"", tmp_path, name="headroom.txt", save=False)

    assert run.ok, (
        f"{command.name} has less than {HEADROOM} assignments of headroom left "
        f"in XNEdit's 4096 instruction program array, so the next table group "
        f"added to it will not compile. Splitting the command in two is what "
        f"fold-letters-to-ascii exists for; see the macro size note in "
        f"CLAUDE.md.\n{run.describe()}"
    )
