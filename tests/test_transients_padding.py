"""The Python padder and the Pad Columns macro have to agree.

``ptable.render`` squares up a GRB table in Python, and
``macros/commands/pad-columns.nm`` does the same job inside the editor. Two
implementations of one rule drift, and the drift is invisible until someone
runs a generated file through the macro and gets a diff.

So this feeds the same table to both and compares. It needs a real XNEdit, and
skips without one like the rest of the macro suite.
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

#: Rows whose columns are deliberately uneven, so padding has work to do.
RECORDS = [
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


def test_pad_columns_leaves_a_generated_ptable_alone(
    runner: XNEditRunner, tmp_path: Path
) -> None:
    """Pad Columns on an already-padded table must be a no-op.

    If the two disagree about a width, the macro rewrites the table and this
    fails with the exact rows that moved.
    """
    generated = ptable.render("GRB", "2026GRB03.C...0000.", RECORDS)

    run = runner.run_on_bytes(
        parse(COMMANDS / "pad-columns.nm").body,
        generated.encode("utf-8"),
        tmp_path,
        name="table.mod",
    )
    assert run.ok, run.describe()
    assert run.output is not None, "Pad Columns left no file behind"

    after = run.output.decode("utf-8")
    if after == generated:
        return

    before_lines = generated.splitlines()
    after_lines = after.splitlines()
    moved = [
        (index, before, now)
        for index, (before, now) in enumerate(zip(before_lines, after_lines))
        if before != now
    ]
    pytest.fail(
        "Pad Columns disagrees with ptable.render on {} line(s):\n".format(len(moved))
        + "\n".join(
            "  line {}\n    python: {!r}\n    macro : {!r}".format(*item)
            for item in moved[:5]
        )
    )


def test_the_table_actually_needed_padding() -> None:
    """Guard against the check above passing because nothing happened.

    A no-op comparison on a table that was already uniform would pass whatever
    either implementation did.
    """
    widths = {len(record.uncertainty) for record in RECORDS}
    assert len(widths) > 1, "every uncertainty is the same width; nothing to pad"
