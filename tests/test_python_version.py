"""Keep the NED team's Python on 3.9.

3.9 is the newest interpreter on their machines, so anything they are expected
to run has to parse there. This harness does not: it is developer tooling and
is free to use whatever ``pyproject.toml`` asks for.

The split is by location. Everything under ``src/nedkit/`` and ``tests/`` is
harness. Every other ``.py`` in the repo is theirs, wherever it ends up living,
and gets compiled by a real 3.9 that uv fetches.

Compiling catches syntax: ``match`` statements, walrus in the wrong place,
parenthesised context managers. It does not catch calls into a stdlib API that
3.9 lacks, or a PEP 604 ``int | str`` annotation that only fails when the
function is defined. Those need a 3.9 run of the actual script.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TEAM_CEILING = "3.9"

#: Directories that hold harness code, not deliverables.
HARNESS = (REPO_ROOT / "src" / "nedkit", REPO_ROOT / "tests")

#: Never worth walking into.
IGNORED = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist"}


def team_scripts() -> list[Path]:
    """Every .py in the repo that the NED team might be asked to run."""
    scripts = []
    for path in REPO_ROOT.rglob("*.py"):
        if IGNORED & set(path.relative_to(REPO_ROOT).parts):
            continue
        if any(path.is_relative_to(directory) for directory in HARNESS):
            continue
        scripts.append(path)
    return sorted(scripts)


def test_harness_layout_is_intact() -> None:
    """If src/nedkit moves, the rule above starts checking the wrong files."""
    assert (REPO_ROOT / "src" / "nedkit" / "runner.py").is_file(), (
        "the harness moved; update HARNESS in this file or every harness module "
        "will be held to Python 3.9"
    )


def test_team_scripts_parse_under_python_39() -> None:
    scripts = team_scripts()
    if not scripts:
        pytest.skip(
            "no team-facing Python yet. Anything added outside src/nedkit and "
            f"tests/ will be held to Python {TEAM_CEILING} from here on."
        )

    if shutil.which("uv") is None:
        pytest.skip(f"uv is needed to fetch a real Python {TEAM_CEILING}")

    # compile() rather than py_compile so no __pycache__ appears next to the
    # sources being checked.
    program = (
        "import sys\n"
        "for name in sys.argv[1:]:\n"
        "    with open(name, encoding='utf-8') as fh:\n"
        "        compile(fh.read(), name, 'exec')\n"
    )
    result = subprocess.run(
        [
            "uv",
            "run",
            "--python",
            TEAM_CEILING,
            "--no-project",
            "python",
            "-c",
            program,
            *[str(path) for path in scripts],
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, (
        f"these do not parse under Python {TEAM_CEILING}, which is all the NED "
        f"team has:\n{result.stderr.strip()}"
    )
