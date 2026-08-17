"""Checks against the live TNS and Swift sites.

The offline suite proves the code still agrees with saved responses. It cannot
notice the responses changing shape, and since there is no API key here, the
shape is a web page's markup and a search page's CSV export. Both can change
without anyone announcing it, and the first sign would otherwise be a load
built from a short or empty list.

So this fetches for real and compares against a **corpus**: the objects in
``tests/fixtures/transients/`` came off a real load, their values are known,
and they are still on TNS and Swift today. Re-fetching them and getting
different values means something moved.

Off by default. ``NEDKIT_NETWORK=1`` turns it on, and ``.github/workflows/
sources.yml`` runs it nightly.

**"Cannot reach" is not "has changed".** A refusal or a timeout skips, because
the job exists to notice a format change and a red build for someone else's
outage teaches people to ignore it. Only a reachable site whose content is
wrong fails.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "transients"

sys.path.insert(0, str(REPO_ROOT / "python"))

from nedtransients import ptable, sources  # noqa: E402

pytestmark = pytest.mark.network


def read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(scope="module", autouse=True)
def opted_in():
    if not os.environ.get("NEDKIT_NETWORK"):
        pytest.skip("set NEDKIT_NETWORK=1 to check the live sources")


def reachable(what: str, call):
    """Run a fetch, turning "cannot reach" into a skip and leaving the rest.

    Parameters
    ----------
    what : str
        The site, for the skip message.
    call : callable
        The fetch to attempt.

    Returns
    -------
    object
        Whatever ``call`` returned.
    """
    try:
        return call()
    except urllib.error.HTTPError as error:
        if error.code in (403, 429, 503):
            pytest.skip(
                "{} answered {} from this network. That is a reachability "
                "problem, not a format change.".format(what, error.code)
            )
        raise
    except (urllib.error.URLError, TimeoutError) as error:
        pytest.skip("{} unreachable: {}".format(what, error))
    except RuntimeError as error:
        # fetch() turns the documented quota into this.
        if "rate limit" in str(error):
            pytest.skip(str(error))
        raise


@pytest.fixture(scope="module")
def live_swift():
    return sources.parse_swift(
        reachable("Swift", lambda: sources.fetch(sources.SWIFT_XRT))
    )


@pytest.fixture(scope="module")
def live_frb():
    """Every FRB over the window the saved CSV fixture covers."""
    window = (dt.date(2024, 12, 1), dt.date(2025, 10, 1))
    text = reachable("TNS", lambda: sources.fetch_tns(window[0], window[1], frb=True))
    return sources.parse_tns(text, "FRB")


# --------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------


def test_swift_still_publishes_the_position_table(live_swift):
    assert len(live_swift) > 1000, "the table got much shorter"
    for record in live_swift[:20]:
        assert record.name.startswith("GRB ")
        assert record.ra.count(":") == 2, record.ra
        assert record.dec.count(":") == 2, record.dec
        assert record.uncertainty


def test_tns_still_exports_the_columns_we_read(live_frb):
    assert live_frb, "TNS returned nothing for a window that has objects"
    for record in live_frb[:20]:
        assert record.name.startswith("FRB ")
        assert record.tns_id.isdigit()
        assert record.ra.count(":") == 2
        assert record.discovered.year >= 2024


# --------------------------------------------------------------------------
# The corpus: known objects must still read the same
# --------------------------------------------------------------------------


def test_the_saved_grbs_still_match_swift(live_swift):
    """The 66 GRBs of a real load, re-fetched and compared value by value."""
    by_name = {record.name: record for record in live_swift}
    saved = sources.parse_swift(read("swift-xrt.txt"))
    checked = 0
    for record in saved:
        live = by_name.get(record.name)
        if live is None:
            continue
        assert (live.ra, live.dec, live.uncertainty) == (
            record.ra,
            record.dec,
            record.uncertainty,
        ), "{} moved".format(record.name)
        checked += 1
    assert checked > 50, "only {} of the saved GRBs are still listed".format(checked)


def test_the_saved_frbs_still_match_tns(live_frb):
    """Same for the FRBs, which is where the ptable's precision comes from."""
    by_name = {record.name: record for record in live_frb}
    saved = sources.parse_tns(read("tns-frb.csv"), "FRB")
    checked = 0
    for record in saved:
        live = by_name.get(record.name)
        if live is None:
            continue
        assert live == record, "{} changed".format(record.name)
        checked += 1
    assert checked > 100, "only {} of the saved FRBs came back".format(checked)


def test_a_real_ptable_still_rebuilds_byte_for_byte(live_swift):
    """The strongest check available: a real loaded file, rebuilt from today.

    ``GRB.2026.03.31.mod`` came off a real load. If Swift's table and this
    code both still say what they said, it reproduces exactly.
    """
    golden = read("GRB.2026.03.31.mod")
    by_name = {record.name: record for record in live_swift}
    wanted = ptable.loaded_names(golden)
    missing = [name for name in wanted if name not in by_name]
    if missing:
        pytest.skip("Swift no longer lists {}".format(missing[:3]))
    rebuilt = ptable.render(
        "GRB", "2026GRB03.C...0000.", [by_name[name] for name in wanted]
    )
    assert rebuilt == golden


# --------------------------------------------------------------------------
# The two TNS routes
# --------------------------------------------------------------------------


def test_both_tns_routes_still_agree():
    """The fallback is only worth having while it returns the same answer.

    A narrow window, because the results page is roughly eighty times the size
    of the CSV export and this runs every night.
    """
    since, until = dt.date(2025, 7, 1), dt.date(2025, 9, 30)
    from_csv = sources.parse_tns(
        reachable("TNS", lambda: sources.fetch_tns(since, until, frb=True)), "FRB"
    )
    from_page = sources.parse_tns(
        reachable(
            "TNS", lambda: sources.fetch_tns(since, until, frb=True, as_csv=False)
        ),
        "FRB",
    )
    assert from_csv, "the CSV route returned nothing"
    assert from_csv == from_page, "the two routes have diverged"
