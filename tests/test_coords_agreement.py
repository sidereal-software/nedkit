"""The coordinate macros and ``nedtransients.coords`` have to agree.

``coords.ra_to_ned`` and ``coords.dec_to_ned`` convert a sexagesimal position to
the compact form a ptable wants, and ``macros/commands/ra-to-ned-form.nm`` and
``dec-to-ned-form.nm`` do the same job inside the editor. Two implementations of
one rule drift, and the drift is invisible until a file built by hand disagrees
with one built by ``ned-transients`` and nobody can say which is right.

So this feeds both the same values and compares. The values are the real ones:
``tests/fixtures/transients/`` came off a published load, so these are positions
as TNS and Swift actually print them, at the two different precisions those two
sources use.

Needs a real XNEdit, and skips without one like the rest of the macro suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "transients"

sys.path.insert(0, str(REPO_ROOT / "python"))

from nedtransients import coords, sources  # noqa: E402

pytestmark = pytest.mark.xnedit

#: How many of the corpus rows to run. Every row is one editor start, so the
#: whole corpus would cost minutes for no more coverage than its distinct
#: shapes give. Taken at a fixed stride through the sorted values rather than
#: at random, so the set is the same on every run and still spans the range.
#: The first N would not: sorted declinations put every ``+`` before every
#: ``-``, so a head slice never sees a southern one.
SAMPLE = 12


def _corpus() -> "list[sources.Transient]":
    """Real positions from the published FRB and GRB loads."""
    records = sources.parse_tns(
        (FIXTURES / "tns-frb.csv").read_text(encoding="utf-8"), "FRB"
    )
    records += sources.parse_swift(
        (FIXTURES / "swift-xrt.txt").read_text(encoding="utf-8")
    )
    return records


def _values(attribute: str) -> "list[str]":
    seen = sorted({getattr(record, attribute) for record in _corpus()})
    assert len(seen) >= SAMPLE, f"corpus has only {len(seen)} distinct {attribute}"
    return seen[:: max(1, len(seen) // SAMPLE)][:SAMPLE]


def _convert(runner: XNEditRunner, command: str, values: "list[str]", tmp_path: Path):
    """Run one coordinate command over a column of values, and return the lines."""
    buffer = ("\n".join(values) + "\n").encode("utf-8")
    run = runner.run_on_bytes(
        "select(0, $text_length)\n" + parse(COMMANDS / f"{command}.nm").body,
        buffer,
        tmp_path,
        name="column.txt",
    )
    assert run.ok, run.describe()
    assert not run.reports, f"{command} refused the column: {run.reports}"
    assert run.output is not None, f"{command} left no file behind"
    return run.output.decode("utf-8").splitlines()


def test_ra_macro_agrees_with_ra_to_ned(runner: XNEditRunner, tmp_path: Path) -> None:
    values = _values("ra")
    expected = [coords.ra_to_ned(value) for value in values]
    got = _convert(runner, "ra-to-ned-form", values, tmp_path)

    assert got == expected, "\n".join(
        f"  {value!r}\n    python: {want!r}\n    macro : {have!r}"
        for value, want, have in zip(values, expected, got)
        if want != have
    )


def test_dec_macro_agrees_with_dec_to_ned(runner: XNEditRunner, tmp_path: Path) -> None:
    values = _values("dec")
    expected = [coords.dec_to_ned(value) for value in values]
    got = _convert(runner, "dec-to-ned-form", values, tmp_path)

    assert got == expected, "\n".join(
        f"  {value!r}\n    python: {want!r}\n    macro : {have!r}"
        for value, want, have in zip(values, expected, got)
        if want != have
    )


def test_the_corpus_actually_exercises_the_conversion() -> None:
    """Guard against the comparisons above passing because nothing happened.

    Two implementations that both do nothing agree perfectly. So the sample has
    to contain values that really change, and declinations of both signs, since
    the sign is the only thing the two commands do differently.
    """
    ras = _values("ra")
    assert all(":" in value for value in ras), "no right ascension needs converting"
    assert [coords.ra_to_ned(value) for value in ras] != ras

    decs = _values("dec")
    converted = [coords.dec_to_ned(value) for value in decs]
    assert converted != decs, "no declination needs converting"

    signs = {value[0] for value in converted}
    assert signs == {"+", "-"}, (
        f"the sample declinations are all {signs}, so the sign handling that "
        "separates the two commands is never exercised"
    )
