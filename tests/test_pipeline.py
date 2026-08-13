"""The commands run together, on a real file.

``tests/fixtures/`` exercises one command at a time on input written to isolate
a single behaviour. This runs the actual sequence over the actual paste in
``samples/``, which is where the two interact and where the order turns out to
matter a great deal.

The rule the tests below pin:

    Align Columns, then everything else, then Align Columns again.

Aligning first fixes the field boundaries while the tabs that mark them are
still there. Aligning last is what makes the widths right, and it has to be
last because every later edit changes them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"
SAMPLES = REPO_ROOT / "samples"
EXPECTED = Path(__file__).parent / "fixtures" / "pipeline" / "A13L.expected.txt"

#: Align, format, align. See the module docstring.
PIPELINE = ["align-columns", "normalize-characters", "align-columns"]

pytestmark = pytest.mark.xnedit


def apply(runner: XNEditRunner, names: list[str], data: bytes, workdir: Path) -> bytes:
    for name in names:
        run = runner.run_on_bytes(
            parse(COMMANDS / f"{name}.nm").body, data, workdir, name="table.txt"
        )
        assert run.ok, f"{name}: {run.describe()}"
        data = run.output or b""
    return data


def widths(data: bytes) -> set[int]:
    """Line lengths of the table rows. One value means the columns line up."""
    return {len(line) for line in data.split(b"\n") if b"|" in line}


def fields(data: bytes) -> list[int]:
    return [len(line.split(b"|")) for line in data.split(b"\n") if b"|" in line]


def test_pasted_table_becomes_a_ned_table(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """The full run over the real SDSS paste in samples/."""
    result = apply(
        runner, PIPELINE, (SAMPLES / "A13L.mod.before").read_bytes(), tmp_path
    )
    assert result == EXPECTED.read_bytes()
    assert len(widths(result)) == 1, "the columns should line up"


def test_running_the_pipeline_again_changes_nothing(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    settled = EXPECTED.read_bytes()
    assert apply(runner, PIPELINE, settled, tmp_path) == settled


def test_aligning_last_is_what_makes_the_widths_right(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Stopping before the final align leaves the columns ragged.

    Align Columns measures fields with ``length()``, which counts bytes. An en
    dash is three bytes and one column, so widths measured before Normalize
    Characters shrinks those dashes are two too wide afterwards. Any edit at
    all has the same effect, which is the general reason aligning goes last.
    """
    source = (SAMPLES / "A13L.mod.before").read_bytes()

    stopped_early = apply(runner, PIPELINE[:-1], source, tmp_path)
    assert len(widths(stopped_early)) > 1, "expected ragged columns"

    finished = apply(runner, PIPELINE, source, tmp_path)
    assert len(widths(finished)) == 1


def test_aligning_first_is_what_saves_the_field_boundaries(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Normalising before the first align destroys the table.

    Normalize Characters turns every tab into a single space. After that,
    Align Columns has no delimiter left and falls back to splitting on runs of
    whitespace, which cuts each field that contains a space into several and
    swallows any field that was empty. Aligning first turns the tabs into
    pipes, and a pipe is the delimiter Align Columns looks for first, so the
    boundaries survive everything that follows.
    """
    # A name with a space in it, and a row with no measured redshift.
    source = b"NGC 4472\t12 29 46.76\t0.003326\nNGC 4486\t\t0.004283\n"

    assert fields(apply(runner, PIPELINE, source, tmp_path)) == [3, 3]

    normalize_first = apply(
        runner, ["normalize-characters", "align-columns"], source, tmp_path
    )
    assert fields(normalize_first) != [3, 3], (
        "if this passes, Normalize Characters stopped eating tabs and the "
        "align-first half of the rule can be reconsidered"
    )


@pytest.mark.xfail(
    strict=True,
    reason="align-columns pads by bytes, so a non-ASCII value comes up short "
    "by one column per extra byte. Normalize Characters deliberately keeps "
    "accented names and Greek letters, so they reach the final align intact.",
)
def test_align_columns_measures_characters_not_bytes(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    result = apply(
        runner, ["align-columns"], "Balázs\tz=0.1\nSmith\tz=0.2\n".encode(), tmp_path
    )
    columns = {
        len(line.split("|")[0]) for line in result.decode().splitlines() if "|" in line
    }
    assert len(columns) == 1, f"first column came out at {columns} characters wide"
