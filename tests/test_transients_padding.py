"""Where the Python padder and the Pad Columns macro agree, and where they don't.

``ptable.render`` squares up a table in Python and ``macros/commands/pad-columns.nm``
does a similar job inside the editor. Two implementations of one rule drift, and
the drift is invisible until someone runs a generated file through the macro and
gets a diff.

They do not implement the same rule everywhere, and that is deliberate. The real
files use two conventions, and ``Layout.padded`` is which one a kind takes:

===========  =========================================  ==============
Convention   Looks like                                 Kinds
===========  =========================================  ==============
unpadded     ``189222|FRB 20250924A|203106.360|``       FRB, TNS
lead space   ``GRB 260204A | 134025.49 | +015550.7 |``  GRB
===========  =========================================  ==============

Pad Columns only knows the first one. It trims the spaces around every field and
pads to the widest value, which is the convention in ``samples/A13L.mod.after``
and in ``tests/fixtures/transients/FRB.2026.03.31.mod``. It cannot produce the
second, because nothing in a buffer says "this file is a GRB file".

So there are two tests. The first pins the agreement on an unpadded layout. The
second pins the disagreement on GRB, so it stays a recorded fact rather than
something the next person rediscovers by watching a test go red.

Both need a real XNEdit, and skip without one like the rest of the macro suite.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

from nedkit import XNEditRunner, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "macros" / "commands"

sys.path.insert(0, str(REPO_ROOT / "python"))

from nedtransients import ptable, sources  # noqa: E402

pytestmark = pytest.mark.xnedit

#: FRB rows shaped like the real load. Every value in a column is the same width,
#: because that is what the source produces: a TNS id is six digits and an FRB
#: designation is always ``FRB `` plus eight date digits and a letter. The
#: headings are all narrower than their columns, so ``render`` has real padding
#: to do on the heading row, which is the part the macro has to agree with.
FRB_RECORDS = [
    sources.Transient(
        "FRB",
        "FRB 20250924A",
        "20:31:06.360",
        "+53:50:56.40",
        dt.date(2025, 9, 24),
        tns_id="189222",
    ),
    sources.Transient(
        "FRB",
        "FRB 20250824A",
        "07:29:22.017",
        "+59:53:36.43",
        dt.date(2025, 8, 24),
        tns_id="188490",
    ),
    sources.Transient(
        "FRB",
        "FRB 20250822A",
        "04:19:39.422",
        "+20:20:29.78",
        dt.date(2025, 8, 22),
        tns_id="188486",
    ),
]

#: GRB rows whose uncertainties are deliberately uneven, so the lead-space
#: convention has something visible to line up.
GRB_RECORDS = [
    sources.Transient(
        "GRB",
        "GRB 260204A",
        "13:40:25.49",
        "+01:55:50.7",
        dt.date(2026, 2, 4),
        uncertainty="4.4",
    ),
    sources.Transient(
        "GRB",
        "GRB 251230A",
        "11:59:35.37",
        "+11:26:17.9",
        dt.date(2025, 12, 30),
        uncertainty="12.25",
    ),
    sources.Transient(
        "GRB",
        "GRB 250805A",
        "01:36:51.16",
        "-81:24:06.8",
        dt.date(2025, 8, 5),
        uncertainty="2.1",
    ),
]


def _pad_columns(runner: XNEditRunner, table: str, tmp_path: Path) -> str:
    """Run Pad Columns over ``table`` and return what came back."""
    run = runner.run_on_bytes(
        parse(COMMANDS / "pad-columns.nm").body,
        table.encode("utf-8"),
        tmp_path,
        name="table.mod",
    )
    assert run.ok, run.describe()
    assert run.output is not None, "Pad Columns left no file behind"
    return run.output.decode("utf-8")


def _diff(before: str, after: str) -> str:
    """Render the lines that moved, for a failure message."""
    moved = [
        (index, was, now)
        for index, (was, now) in enumerate(zip(before.splitlines(), after.splitlines()))
        if was != now
    ]
    return "\n".join(
        "  line {}\n    python: {!r}\n    macro : {!r}".format(*item)
        for item in moved[:5]
    )


def test_pad_columns_leaves_a_generated_frb_ptable_alone(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Pad Columns on an already-padded unpadded-convention table is a no-op.

    If the two disagree about a width, the macro rewrites the table and this
    fails with the exact rows that moved.
    """
    generated = ptable.render("FRB", "2026FRB03.C...0000.", FRB_RECORDS)
    after = _pad_columns(runner, generated, tmp_path)

    assert after == generated, (
        "Pad Columns disagrees with ptable.render on the FRB layout:\n"
        + _diff(generated, after)
    )


def test_the_frb_headings_actually_needed_padding() -> None:
    """Guard against the check above passing because nothing happened.

    A comparison on a table that was already uniform would pass whatever either
    implementation did. Every FRB heading is narrower than its column, so
    ``render`` pads the heading row and the macro has to arrive at the same
    widths to leave it alone.
    """
    generated = ptable.render("FRB", "2026FRB03.C...0000.", FRB_RECORDS)
    heading, first_row = generated.splitlines()[-4:-2]

    padded = [field for field in heading.split("|")[:-1] if field != field.rstrip(" ")]
    assert padded, "no heading was padded; the comparison would prove nothing"

    assert len(heading) == len(first_row), (
        "the heading row and the data rows are different lengths, so the table "
        "was never square to begin with"
    )


def test_pad_columns_does_not_implement_the_grb_lead_space(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """GRB is the one layout where the two cannot agree, and that is recorded.

    The real GRB file puts a space either side of every delimiter. Pad Columns
    trims those and pads to the widest value instead, because nothing in the
    buffer tells it the file is a GRB file. So it rewrites a GRB ptable, and
    this test says so out loud.

    If someone teaches the macro that convention, this fails and should be
    deleted deliberately rather than adjusted until it passes.
    """
    generated = ptable.render("GRB", "2026GRB03.C...0000.", GRB_RECORDS)
    after = _pad_columns(runner, generated, tmp_path)

    assert after != generated, (
        "Pad Columns left a GRB ptable alone. If it learned the lead-space "
        "convention, delete this test and fold GRB into the agreement test above."
    )

    # Say what the disagreement is, not merely that there is one. A test that
    # only asserts "these differ" would keep passing if the macro started
    # mangling the table some entirely different way.
    assert " | " in generated, "the GRB layout stopped using the lead space"
    assert " | " not in after, "Pad Columns left a lead space behind:\n" + _diff(
        generated, after
    )
