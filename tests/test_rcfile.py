"""The importable resource file the docs site hands out.

``docs/nedkit-macros.rc`` is what a reader downloads, so the thing worth
asserting is that a real XNEdit takes it, not that the generator is
deterministic. The format has no forgiveness in it and no error short of a
parse failure, so a wrong file installs commands that look right and do
something else. Whether the committed copy is still in step with the macros is
``tests/test_docs.py``'s business, along with every other generated artifact.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, command_files, parse
from nedkit.rcfile import BG_MENU_RESOURCE, MACRO_MENU_RESOURCE, entry

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED = Path("docs/nedkit-macros.rc")


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
    for resource, paths in menu_paths(
        (REPO_ROOT / SHIPPED).read_text(encoding="utf-8")
    ).items():
        assert len(paths) == len(set(paths)), resource


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
