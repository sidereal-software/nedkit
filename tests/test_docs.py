"""The generated documentation pages, and the header parsing they rely on.

``tools/gen_docs.py`` rewrites three pages from the macros. CI runs it with
``--check``, but that is late: catching a stale page here means a developer
finds out from ``uv run pytest`` instead of from a red build.
"""

from __future__ import annotations

import importlib.util
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


@pytest.mark.parametrize("page", sorted(gen_docs.REGIONS))
def test_generated_pages_are_current(page: str) -> None:
    current = gen_docs.read(page)
    updated = current
    for marker, generator in gen_docs.REGIONS[page]:
        updated = gen_docs.splice(updated, marker, generator())
    assert updated == current, (
        f"{page} is out of date with the macros. Run: uv run python tools/gen_docs.py"
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
