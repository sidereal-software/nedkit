"""The generated documentation pages, and the header parsing they rely on.

``tools/gen_docs.py`` rewrites three pages and one downloadable file from the
macros. CI runs it with ``--check``, but that is late: catching a stale page
here means a developer finds out from ``uv run pytest`` instead of from a red
build.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from nedkit.macro import command_files, parse

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_gen_docs():
    """Import ``tools/gen_docs.py``, which is a script rather than a module."""
    spec = importlib.util.spec_from_file_location(
        "gen_docs", REPO_ROOT / "tools" / "gen_docs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_docs = _load_gen_docs()


@pytest.mark.parametrize("path", sorted({**gen_docs.REGIONS, **gen_docs.FILES}))
def test_generated_files_are_current(path: str) -> None:
    current, updated = gen_docs.regenerate(path)
    assert updated == current, (
        f"{path} is out of date with the macros. Run: uv run python tools/gen_docs.py"
    )


@pytest.mark.parametrize("path", command_files(REPO_ROOT), ids=lambda p: p.name)
def test_every_command_has_prose_for_the_docs(path: Path) -> None:
    """The header description becomes the command's page, so it has to exist."""
    macro = parse(path)
    assert macro.prose.strip(), f"{path.name} has no description under its title"


def test_prose_excludes_the_title_and_the_install_boilerplate() -> None:
    macro = parse(REPO_ROOT / "macros" / "commands" / "pipe-at-cursor-column.nm")
    assert not macro.prose.startswith(macro.title)
    assert "Install the body below" not in macro.prose
    assert "Menu Entry" not in macro.prose


def test_prose_keeps_indentation_so_examples_stay_code_blocks() -> None:
    macro = parse(REPO_ROOT / "macros" / "commands" / "pipe-at-cursor-column.nm")
    indented = [line for line in macro.prose.split("\n") if line.startswith("    ")]
    assert indented, "the worked example in the header lost its indentation"


def test_a_hash_in_prose_does_not_become_a_heading() -> None:
    """``# ##refcode ...`` in a header loses its marker and reads as a heading."""
    assert gen_docs.as_prose("##refcode is kept") == "\\##refcode is kept"
    assert gen_docs.as_prose("    # inside a code block") == "    # inside a code block"


def test_generated_headings_are_only_the_ones_the_generator_writes() -> None:
    """Any other heading came from prose and is a rendering accident."""
    page = gen_docs.read("docs/commands.md")
    body = page.split(gen_docs.BEGIN % "commands")[1].split(gen_docs.END % "commands")[
        0
    ]
    expected = {"## %s" % parse(p).title for p in command_files(REPO_ROOT)}
    headings = {
        line
        for line in body.split("\n")
        if line.startswith("#") and not line.startswith("<!--")
    }
    assert headings == expected, "unexpected heading in the generated command reference"


# --------------------------------------------------------------------------
# What a copy button means
#
# ``content.code.copy`` is off in mkdocs.yml, so Material hangs a copy button
# only on a block that carries ``.copy`` itself. That turns the button into a
# claim: this block is meant to leave the page. Most blocks on this site are
# output listings, and a button on one of those tells a reader to paste their
# own expected output somewhere.

DOCS = REPO_ROOT / "docs"

#: The info string of every fenced block that has one. A closing fence carries
#: nothing after the backticks, so anything matching here opened a block.
FENCE_INFO = re.compile(r"^[ \t]*```(\S[^\n]*)$", re.M)

#: ``sh`` as a language, written either bare or as a class in the brace form.
SHELL = re.compile(r"(?:^|[.\s{])sh\b")


@pytest.mark.parametrize("page", sorted(DOCS.glob("*.md")), ids=lambda p: p.name)
def test_every_shell_block_offers_a_copy_button(page: Path) -> None:
    """A block of commands is the one kind that always wants copying."""
    for info in FENCE_INFO.findall(page.read_text(encoding="utf-8")):
        if not SHELL.search(info):
            continue
        assert ".copy" in info, (
            f"{page.name} has a shell block written ```{info}, which renders "
            "without a copy button. Write it ```{ .sh .copy } instead."
        )


def theme_features() -> list[str]:
    """``theme.features`` from mkdocs.yml, read as text rather than as YAML.

    The file carries ``!!python/name:`` tags that ``yaml.safe_load`` refuses,
    and pyyaml is in the docs dependency group, which the ``not xnedit`` run in
    CI does not install. This is one list of scalars; a regex reads it.
    """
    text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    block = re.search(r"^(\s*)features:\n((?:\1[ \t]+.*\n|[ \t]*\n)+)", text, re.M)
    assert block, "mkdocs.yml has no theme.features block"
    return re.findall(r"^\s*-\s*(\S+)\s*$", block.group(2), re.M)


def test_the_copy_button_is_not_on_by_default() -> None:
    """With the feature on, every block gets a button and ``.copy`` says nothing."""
    features = theme_features()
    assert "navigation.tabs" in features, (
        f"theme.features parsed as {features}, which is not the list in mkdocs.yml"
    )
    assert "content.code.copy" not in features, (
        "content.code.copy puts a copy button on every fenced block, including "
        "the output listings, which is what the per-block .copy class replaces"
    )


# --------------------------------------------------------------------------
# The quickstart's success check

#: A report a command prints: a count, then a noun the count might pluralise.
REPORT = re.compile(r"`(\d+ [^`]*\(s\)[^`]*)`")


def reports(page: Path) -> set[str]:
    """The report strings a page quotes inline, unwrapped.

    Markdown wraps a long span across a line break, and the two halves are one
    string to anyone reading the rendered page.
    """
    return {
        re.sub(r"\s+", " ", found)
        for found in REPORT.findall(page.read_text(encoding="utf-8"))
    }


def test_the_quickstart_checks_against_a_report_the_suite_runs() -> None:
    """Step 4 tells a first-time reader what the terminal will say.

    Nothing here drives an editor, so this file cannot check that claim. What it
    can check is that the string is one ``docs/cleaning-pdf-tables.md`` also
    quotes, because ``tests/test_worked_example.py`` runs that page against a
    live XNEdit and fails on a report no command made. Quoting a string from
    there borrows the proof; inventing a new one has nothing behind it.
    """
    quickstart = reports(DOCS / "getting-started.md")
    assert quickstart, (
        "getting-started.md quotes no command report, so its final step no "
        "longer gives the reader anything to check their run against"
    )
    worked = reports(DOCS / "cleaning-pdf-tables.md")
    for report in sorted(quickstart):
        assert report in worked, (
            f"getting-started.md promises {report!r}, which the worked example "
            "never quotes, so no test watches an editor say it"
        )
