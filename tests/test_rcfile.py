"""The importable resource file the docs site hands out.

``docs/nedkit-macros.rc`` is what a reader downloads, so what is worth asserting
is that a real XNEdit takes it and that the commands then answer to their menu
path, not that the generator is deterministic. The format has no forgiveness in
it and no error short of a parse failure, so a wrong file installs commands that
look right and do something else. Whether the committed copy is still in step
with the macros is ``tests/test_docs.py``'s business, along with every other
generated artifact.

The menu itself cannot be inspected, but it does not have to be. XNEdit's
``macro_menu_command`` action looks a name up in ``MacroMenuItems``, which is
the same list the Macro menu is built from and the same list ``-import``
appends to, so reaching a command by its menu path is the installed-ness the
reader cares about. ``bg_menu_command`` does it for the right-click menu.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import MacroFile, XNEditRunner, command_files, parse
from nedkit.rcfile import (
    BG_MENU_RESOURCE,
    MACRO_MENU_RESOURCE,
    entry,
    resource,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED = Path("docs/nedkit-macros.rc")

#: A buffer every command has something to say about, so that "said nothing" is
#: unambiguous. Each has a trailing blank to trim, a pipe to pad between, an em
#: dash to normalise, and no coordinates, so the two that need a selection
#: report that instead. What is asserted is the report, not the edit: only three
#: of the nine change these bytes, and which three is not this test's business.
PROBE = "name | value   \nBalazs — x  \n".encode()


def menu_paths(text: str) -> dict[str, list[str]]:
    """The menu path of every entry, per resource, read back out of the file.

    An entry opens on a single tab and every line of a body carries two, which
    is the only thing distinguishing the two in a file that is otherwise one
    long run of continuations. The closing brace inherits a single tab as well,
    hence the one exclusion.
    """
    blocks: dict[str, list[str]] = {}
    resource = None
    for line in text.split("\n"):
        if line.startswith("nedit."):
            resource = line.split(":", 1)[0]
            blocks[resource] = []
        elif (
            resource is not None
            and line.startswith("\t")
            and not line.startswith("\t\t")
            and not line.startswith("\t}")
        ):
            blocks[resource].append(line[1:].split(":", 1)[0])
    return blocks


def test_every_command_reaches_the_menu_its_header_names() -> None:
    blocks = menu_paths((REPO_ROOT / SHIPPED).read_text(encoding="utf-8"))
    macros = [parse(path) for path in command_files(REPO_ROOT)]

    assert blocks.keys() == {MACRO_MENU_RESOURCE, BG_MENU_RESOURCE}
    assert set(blocks[MACRO_MENU_RESOURCE]) == {
        m.menu_entry for m in macros if m.in_macro_menu
    }
    assert set(blocks[BG_MENU_RESOURCE]) == {
        m.menu_entry for m in macros if m.in_background_menu
    }


def test_no_command_is_written_twice_into_one_menu() -> None:
    """A duplicate would silently replace its twin, since the reader keys on
    the menu path. One entry would then be installed and the other lost."""
    for name, paths in menu_paths(
        (REPO_ROOT / SHIPPED).read_text(encoding="utf-8")
    ).items():
        assert len(paths) == len(set(paths)), name


def test_a_body_ending_in_a_comment_still_closes() -> None:
    """The brace has to land on its own line, not inside the last comment.

    Dropping the terminating newline puts ``}`` on the end of whatever the body
    ends with, and the pipe commands end on a divider comment. The macro would
    then never close, and one unparseable entry fails the whole resource.
    """
    ending_in_a_comment = [
        parse(path)
        for path in command_files(REPO_ROOT)
        if parse(path).body.split("\n")[-1].lstrip().startswith("#")
    ]
    assert ending_in_a_comment, (
        "no command ends on a comment any more; retire this test"
    )

    for macro in ending_in_a_comment:
        lines = entry(macro).split("\n")
        assert lines[-2] == "\t}\\n\\", macro.path.name
        assert lines[-3].lstrip().startswith("#"), macro.path.name


#: Everything XNEdit says when an imported file does not work out. A bad entry
#: is not fatal and does not hang: ``parseError()`` reports a malformed field
#: list, ``ParseError()`` reports a body that will not compile, and both write
#: to stderr because the import happens with no dialog parent to attach to. The
#: editor then carries on with that entry and every entry after it dropped, so
#: stderr is the only thing that distinguishes a good import from a half one.
IMPORT_FAILURES = (
    "Parse error in user defined menu item",
    "macro menu item",
    "Could not read additional preferences file",
)


def test_no_macro_quotes_the_words_the_import_test_watches_for() -> None:
    """The detector reads stdout, so a body saying one of these blinds it.

    This runs without an editor, which is the point: the test that would go
    quiet needs one, and would go quiet without saying so.
    """
    shipped = (REPO_ROOT / SHIPPED).read_text(encoding="utf-8")
    for failure in IMPORT_FAILURES:
        assert failure not in shipped, (
            f"a macro now contains {failure!r}, which "
            "test_a_real_xnedit_imports_the_shipped_file treats as an error"
        )


def import_run(runner: XNEditRunner, rc: Path, workdir: Path):
    return runner.run_on_bytes(
        't_print("")',
        b"",
        workdir,
        save=False,
        extra_args=["-import", str(rc)],
    )


@pytest.mark.xnedit
def test_a_real_xnedit_imports_the_shipped_file(
    runner: XNEditRunner, repo_root: Path, tmp_path: Path
) -> None:
    """The claim the download makes, checked against the editor it is for."""
    run = import_run(runner, repo_root / SHIPPED, tmp_path)

    assert run.ok, run.describe()
    for failure in IMPORT_FAILURES:
        assert failure not in run.stdout, run.stdout


@pytest.mark.xnedit
def test_a_broken_entry_would_be_noticed(runner: XNEditRunner, tmp_path: Path) -> None:
    """The negative control for the test above.

    Nothing about a bad import fails loudly: the editor starts, the macro runs,
    and the exit code is zero. Without this, the assertions above would pass
    just as happily against a file XNEdit had thrown away, and would be a claim
    of coverage rather than coverage.
    """
    broken = tmp_path / "broken.rc"
    broken.write_text(
        "nedit.macroCommands: \\\n\tNED>Broken:::: {\\n\\\n\t\tbeep(\\n\t}\\n",
        encoding="utf-8",
    )

    run = import_run(runner, broken, tmp_path / "work")

    assert run.ok, run.describe()
    assert any(failure in run.stdout for failure in IMPORT_FAILURES), run.stdout


def reported(run) -> str:
    """Everything the command said, whether printed or put in a dialog."""
    return (run.messages.strip() + " ".join(run.reports)).strip()


@pytest.mark.xnedit
@pytest.mark.parametrize("path", command_files(REPO_ROOT), ids=lambda p: p.name)
def test_an_imported_command_answers_to_its_menu_path(
    runner: XNEditRunner, repo_root: Path, tmp_path: Path, path: Path
) -> None:
    """The claim the download actually makes, for every command in it.

    Parsing clean is not installing. This asks XNEdit to run the command by the
    menu path its header declares, which only succeeds if ``-import`` put it in
    the list the Macro menu is built from.

    The signal is that the command reported something, because only three of
    the nine edit this buffer. That rests on every command reporting what it
    did, which ``tests/test_command_reporting.py`` is what keeps true.
    """
    macro = parse(path)
    run = runner.run_on_bytes(
        f'macro_menu_command("{macro.menu_entry}")',
        PROBE,
        tmp_path,
        extra_args=["-import", str(repo_root / SHIPPED)],
    )

    assert run.ok, run.describe()
    assert reported(run), (
        f"{macro.menu_entry} said nothing, so XNEdit did not find it under that "
        "name. Either the import did not install it or the header's Menu Entry "
        "and the shipped file disagree."
    )


@pytest.mark.xnedit
@pytest.mark.parametrize(
    "path",
    [p for p in command_files(REPO_ROOT) if parse(p).in_background_menu],
    ids=lambda p: p.name,
)
def test_an_imported_command_answers_on_the_right_click_menu(
    runner: XNEditRunner, repo_root: Path, tmp_path: Path, path: Path
) -> None:
    """The second resource in the file, which the Macro menu never touches."""
    macro = parse(path)
    run = runner.run_on_bytes(
        f'bg_menu_command("{macro.menu_entry}")',
        PROBE,
        tmp_path,
        extra_args=["-import", str(repo_root / SHIPPED)],
    )

    assert run.ok, run.describe()
    assert reported(run), (
        f"{macro.menu_entry} is not in nedit.bgMenuCommands, so a right-click "
        "would not offer it"
    )


@pytest.mark.xnedit
def test_without_the_import_no_command_answers(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The control for the two tests above.

    An unknown name is not an error: ``DoNamedMacroMenuCmd`` returns False and
    the action routine discards it, so nothing happens and nothing is said.
    Without this, both tests above would pass just as happily on a signal that
    had nothing to do with the import.
    """
    run = runner.run_on_bytes(
        'macro_menu_command("NED>Trim Trailing Blanks")', PROBE, tmp_path
    )

    assert run.ok, run.describe()
    assert not reported(run), "something answered without the file being imported"
    assert run.output == PROBE


#: The menu path the update tests install, rename and re-install under. Not one
#: of the shipped commands: this is about the mechanism, and a body that only
#: announces its version says which copy ran without editing anything.
DEMO = "NED>Version Demo"


def one_command_rc(path: Path, menu_entry: str, marker: str) -> Path:
    """A single-command resource whose body only says which version it is.

    Built through ``rcfile.resource()`` rather than by hand. A hand-written
    ``\\n`` inside the body is eaten by the resource reader and ends the string
    literal it sits in, which is the whole reason the writer exists, and it
    catches anyone writing one of these fixtures by eye.
    """
    macro = MacroFile(
        path=Path("version-demo.nm"),
        title="Version Demo",
        prose="",
        fields={"Menu Entry": menu_entry, "Accelerator": "", "Mnemonic": ""},
        body=f't_print("{marker}\\n")',
        body_offset=1,
    )
    path.write_text(resource(MACRO_MENU_RESOURCE, [macro]), encoding="utf-8")
    return path


def already_installed(runner: XNEditRunner, workdir: Path, rc: Path) -> XNEditRunner:
    """An editor whose preferences already hold ``rc``, as Save Defaults leaves it.

    Its own configuration directory, not the session runner's: writing a
    resource into the shared one would install these commands for every test
    that ran afterwards.
    """
    fresh = XNEditRunner(runner.binary, workdir / "cfg")
    prefs = workdir / "cfg" / "nedit.rc"
    prefs.write_text(
        prefs.read_text(encoding="utf-8") + "\n" + rc.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return fresh


@pytest.mark.xnedit
def test_reinstalling_after_a_macro_changed_updates_the_command(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The whole reason the docs tell people to re-import after every change.

    An entry whose menu path is already installed is replaced in place rather
    than appended, so the second install wins. If it were appended instead,
    ``DoNamedMacroMenuCmd`` would find the older copy first and the reader
    would keep running the macro they thought they had just updated, with
    nothing anywhere saying so.
    """
    v1 = one_command_rc(tmp_path / "v1.rc", DEMO, "VERSION-ONE")
    v2 = one_command_rc(tmp_path / "v2.rc", DEMO, "VERSION-TWO")
    editor = already_installed(runner, tmp_path, v1)

    run = editor.run_on_bytes(
        f'macro_menu_command("{DEMO}")',
        b"x\n",
        tmp_path / "work",
        save=False,
        extra_args=["-import", str(v2)],
    )

    assert run.ok, run.describe()
    assert "VERSION-TWO" in run.messages, run.messages
    assert "VERSION-ONE" not in run.messages, (
        "the old body ran, so the import appended a second copy instead of "
        "replacing the first"
    )


@pytest.mark.xnedit
def test_renaming_a_command_leaves_the_old_one_installed(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Renaming a Menu Entry adds a command rather than moving one.

    Replacement is keyed on the menu path, so the old path matches nothing in
    the new file and its entry survives untouched. The reader ends up with both
    names in the menu and the old one still running the old body, and Save
    Defaults then writes the ghost out permanently. Pinned rather than fixed:
    the fix is to delete the old entry through Customize Menus, and nothing
    here can do it for them.
    """
    old = one_command_rc(tmp_path / "old.rc", DEMO, "VERSION-ONE")
    renamed = one_command_rc(tmp_path / "new.rc", DEMO + " Renamed", "VERSION-TWO")
    editor = already_installed(runner, tmp_path, old)

    def invoke(entry: str, label: str) -> str:
        return editor.run_on_bytes(
            f'macro_menu_command("{entry}")',
            b"x\n",
            tmp_path / label,
            save=False,
            extra_args=["-import", str(renamed)],
        ).messages

    assert "VERSION-TWO" in invoke(DEMO + " Renamed", "new"), "the rename did not land"
    assert "VERSION-ONE" in invoke(DEMO, "ghost"), (
        "the old menu entry no longer answers, so XNEdit has started cleaning up "
        "after a rename. Good news, but the docs say otherwise"
    )
