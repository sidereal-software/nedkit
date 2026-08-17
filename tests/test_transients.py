"""Tests for the ned-transients tool.

The strongest ones here compare against real files: ``2026a.TNS.FRB.GRB.ls``,
``FRB.2026.03.31.mod`` and ``GRB.2026.03.31.mod`` all came off a real load, and
their sources are still reachable, so the tool has to reproduce them byte for
byte from saved responses. That is a much better check than a golden file this
repo generated for itself, which would only ever prove the code still agrees
with itself.

Everything except the ``network`` test runs offline from
``tests/fixtures/transients/``.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "transients"

# The tool ships as a directory the team copies, not as an installed package,
# so it is not importable until its parent is on the path.
sys.path.insert(0, str(REPO_ROOT / "python"))

from nedtransients import coords, layout, ptable, refcodes, sources  # noqa: E402


def read(name: str) -> str:
    """Read a fixture as text."""
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def frb_records():
    """Every FRB in the saved TNS export."""
    return sources.parse_tns(read("tns-frb.csv"), "FRB")


@pytest.fixture(scope="module")
def grb_records():
    """Every GRB in the saved Swift table."""
    return sources.parse_swift(read("swift-xrt.txt"))


def chosen(records, golden: str):
    """Pick out the records a real .mod file kept, in its order.

    The tool cannot know which rows a human kept, so reproducing a real file
    means feeding it that selection. What is under test is the formatting and
    the coordinate conversion, not the choice.
    """
    order = [
        match.group(1)
        for match in (
            re.match(r"^(?:\d+\|)?([A-Z]{3} [^|]+?) *\|", line)
            for line in read(golden).splitlines()
        )
        if match
    ]
    by_name = {record.name: record for record in records}
    missing = [name for name in order if name not in by_name]
    assert not missing, f"fixture no longer covers {missing[:3]}"
    return [by_name[name] for name in order]


# --------------------------------------------------------------------------
# Coordinates
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("20:31:06.360", "203106.360"),
        ("13:40:25.49", "134025.49"),
        ("00:10:09.97", "001009.97"),
    ],
)
def test_right_ascension_only_loses_its_colons(value, expected):
    assert coords.ra_to_ned(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("+53:50:56.40", "+535056.40"),
        ("-44:31:58.60", "-443158.60"),
        ("+01:55:50.7", "+015550.7"),
        # No sign in the source. NED wants one, and assuming north is the only
        # sane default, but it has to be added rather than left off.
        ("15:34:09.66", "+153409.66"),
    ],
)
def test_declination_always_comes_back_signed(value, expected):
    assert coords.dec_to_ned(value) == expected


def test_declination_between_zero_and_minus_one_keeps_its_sign():
    """The case where the sign is the only thing distinguishing the hemisphere.

    ``-00:21:48.71`` and ``+00:21:48.71`` differ by one character and by 43
    arcminutes of sky. Dropping the sign here is silent.
    """
    assert coords.dec_to_ned("-00:21:48.71") == "-002148.71"
    assert coords.dec_to_ned("+00:21:48.71") == "+002148.71"


def test_a_signed_right_ascension_is_refused():
    """A signed value in the RA column means the two got swapped."""
    with pytest.raises(ValueError):
        coords.ra_to_ned("-00:21:48.71")


def test_precision_is_never_rounded(frb_records, grb_records):
    """The two sources publish different precision and both must survive.

    Rounding to any fixed number of decimals would be wrong for one of them,
    which is the mistake this pins.
    """
    frb = coords.ra_to_ned(frb_records[0].ra)
    grb = coords.ra_to_ned(grb_records[0].ra)
    assert len(frb.split(".")[1]) == 3, frb
    assert len(grb.split(".")[1]) == 2, grb


# --------------------------------------------------------------------------
# Refcodes
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("TNS", "2025TNS...C......0."),
        ("FRB", "2025FRB...C...0000."),
        ("GRB", "2025GRB03.C...0000."),
    ],
)
def test_refcode_matches_the_procedure(kind, expected):
    assert refcodes.refcode(kind, 2025, 3) == expected


@pytest.mark.parametrize("kind", refcodes.KINDS)
@pytest.mark.parametrize("month", range(1, 13))
def test_every_refcode_is_nineteen_characters(kind, month):
    """A wrong-length refcode reaches loadstatus before anything complains."""
    assert len(refcodes.refcode(kind, 2026, month)) == refcodes.REFCODE_LENGTH


def test_the_grb_c_is_not_a_month():
    """GRB's ``C`` stands for Catalog, so it does not move with the month.

    TNS and FRB spell the month as a letter, GRB as a number. Confusing the
    two produces a refcode that looks right and points at the wrong month.
    """
    assert refcodes.refcode("GRB", 2025, 7) == "2025GRB07.C...0000."
    assert refcodes.refcode("TNS", 2025, 7) == "2025TNS...G......0."


def test_month_letter_starts_at_a():
    assert refcodes.month_letter(1) == "A"
    assert refcodes.month_letter(12) == "L"
    with pytest.raises(ValueError):
        refcodes.month_letter(13)


def test_loadstatus_file_reproduces_the_real_one():
    """Byte-for-byte against ``2026a.TNS.FRB.GRB.ls``."""
    assert refcodes.loadstatus_file(2026, 3) == read("2026a.TNS.FRB.GRB.ls")


def test_loadstatus_rows_are_the_expected_width():
    """The fixed-width layout is the whole format; a drifted width breaks it."""
    lines = refcodes.loadstatus_file(2026, 3).splitlines()
    assert all(len(line) == 92 for line in lines[1:]), [len(x) for x in lines]
    # The heading is deliberately not padded, and reads shorter.
    assert len(lines[0]) == 77


def test_loadstatus_name_uses_the_batch_letter():
    assert refcodes.loadstatus_name(2026, "a") == "2026a.TNS.FRB.GRB.ls"
    assert refcodes.loadstatus_name(2026, "b", ("GRB",)) == "2026b.GRB.ls"


def test_jira_body_agrees_with_itself_about_number():
    """It reads as a sentence at one refcode as well as at three."""
    assert "1 refcode needs author info" in refcodes.jira_body(2025, 3, "x", ("GRB",))
    assert "3 refcodes need author info" in refcodes.jira_body(2025, 3, "x")


def test_jira_body_names_every_refcode_and_author():
    body = refcodes.jira_body(2025, 3, "2025.03.04")
    for kind in refcodes.KINDS:
        assert refcodes.refcode(kind, 2025, 3) in body
        assert refcodes.KIND_AUTHORS[kind] in body
    assert "2025.03.04" in body


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def test_tns_export_parses(frb_records):
    assert frb_records, "fixture is empty"
    first = frb_records[0]
    assert first.kind == "FRB"
    assert first.name.startswith("FRB ")
    assert first.tns_id.isdigit()
    assert first.discovered.year >= 2024


def test_a_missing_tns_column_is_an_error_not_a_silent_empty_list():
    """This is how a change to the TNS export surfaces.

    Without the check it would parse to zero records, which is
    indistinguishable from a month with nothing in it.
    """
    with pytest.raises(ValueError, match="missing"):
        sources.parse_tns('"Name","RA"\n"SN 2026a","00:00:00"\n', "TNS")


# --------------------------------------------------------------------------
# The second route into TNS
# --------------------------------------------------------------------------


def test_the_results_page_parses_too():
    """There is no API key, so the guard against TNS changing is two routes.

    The CSV export is one. The ordinary results page is the other, and its
    cells carry the same fields under ``class="cell-*"``.
    """
    records = sources.parse_tns(read("tns-frb-page.html"), "FRB")
    assert len(records) == 17
    first = records[0]
    assert first.name.startswith("FRB ")
    assert first.tns_id.isdigit()
    assert ":" in first.ra and ":" in first.dec


def test_both_routes_agree_record_for_record(frb_records):
    """The whole point of the fallback: same objects, same values.

    The HTML fixture's window sits inside the CSV fixture's, so every record
    it produces has a counterpart to check against. A fallback that quietly
    produced slightly different values would be worse than no fallback.
    """
    by_name = {record.name: record for record in frb_records}
    from_page = sources.parse_tns(read("tns-frb-page.html"), "FRB")
    assert from_page, "fixture is empty"

    checked = 0
    for record in from_page:
        assert record.name in by_name, "{} is not in the CSV fixture".format(
            record.name
        )
        assert record == by_name[record.name]
        checked += 1
    assert checked == 17


def test_the_format_is_sniffed_not_assumed():
    """A cached response is self-describing, so either can be handed back in."""
    assert sources.parse_tns(read("tns-frb.csv"), "FRB")
    assert sources.parse_tns(read("tns-frb-page.html"), "FRB")


def test_nested_detail_rows_do_not_become_objects():
    """TNS puts sub-rows under each result, and they are not results.

    This is what a regex over ``<tr>`` gets wrong: it cannot tell an object's
    row from the reporting detail nested inside it.
    """
    page = """
    <table><tbody>
      <tr class="row-odd">
        <td class="cell-id">1</td><td class="cell-name">SN 2026aaa</td>
        <td class="cell-ra">01:02:03.45</td><td class="cell-decl">+10:20:30.4</td>
        <td class="cell-discoverydate">2026-07-01 00:00:00</td>
        <td class="cell-notes">
          <table><tbody>
            <tr class="row-even"><td class="cell-name">not an object</td></tr>
          </tbody></table>
        </td>
      </tr>
    </tbody></table>
    """
    records = sources.parse_tns(page, "TNS")
    assert [r.name for r in records] == ["SN 2026aaa"]


def test_an_unrecognisable_response_raises(monkeypatch):
    """Neither format means something changed, and that is not an empty month."""
    with pytest.raises(ValueError, match="neither"):
        sources.parse_tns("<html><body>maintenance</body></html>", "TNS")


def test_the_fallback_fires_and_says_so(monkeypatch):
    """A fallback is not silent: the run works, the primary route is broken."""
    calls = []
    said = []

    def fake(since, until, frb=False, page_size=500, as_csv=True):
        calls.append(as_csv)
        if as_csv:
            raise ValueError("TNS export is missing Name")
        return read("tns-frb-page.html")

    monkeypatch.setattr(sources, "fetch_tns", fake)
    text = sources.fetch_tns_resilient(
        dt.date(2025, 7, 1), dt.date(2025, 9, 30), frb=True, on_fallback=said.append
    )
    assert calls == [True, False], "should try the CSV route first"
    assert len(sources.parse_tns(text, "FRB")) == 17
    assert said and "results page" in said[0]


def test_a_rate_limit_does_not_trigger_the_fallback(monkeypatch):
    """The quota covers both routes, so retrying the other way just wastes it."""
    calls = []

    def fake(since, until, frb=False, page_size=500, as_csv=True):
        calls.append(as_csv)
        raise RuntimeError("TNS rate limit hit (429)")

    monkeypatch.setattr(sources, "fetch_tns", fake)
    with pytest.raises(RuntimeError, match="rate limit"):
        sources.fetch_tns_resilient(dt.date(2025, 7, 1), dt.date(2025, 9, 30))
    assert calls == [True], "should not have tried the second route"


def test_the_csv_route_is_preferred_when_it_works(monkeypatch):
    calls = []

    def fake(since, until, frb=False, page_size=500, as_csv=True):
        calls.append(as_csv)
        return read("tns-frb.csv")

    monkeypatch.setattr(sources, "fetch_tns", fake)
    sources.fetch_tns_resilient(dt.date(2025, 1, 1), dt.date(2025, 10, 1), frb=True)
    assert calls == [True], "fell back when the CSV route was fine"


def test_the_two_routes_ask_the_same_question():
    """Same URL bar the format, so they cannot drift onto different queries."""
    since, until = dt.date(2026, 7, 1), dt.date(2026, 7, 31)
    as_csv = sources.tns_url(since, until, frb=True)
    as_html = sources.tns_url(since, until, frb=True, as_csv=False)
    assert as_csv.replace("format=csv&", "") == as_html
    assert "format=csv" not in as_html


def test_swift_table_parses(grb_records):
    assert grb_records
    first = grb_records[0]
    assert first.kind == "GRB"
    assert first.uncertainty
    assert first.tns_id == ""


def test_swift_rows_without_a_position_are_skipped():
    table = (
        "GRB 260208A | 13:38:55.58 | +33:48:04.5 | 2.5 | Enhanced\n"
        "GRB 260207A |  |  |  | No position found\n"
    )
    assert [record.name for record in sources.parse_swift(table)] == ["GRB 260208A"]


@pytest.mark.parametrize(
    "name,expected",
    [
        ("GRB 260204A", dt.date(2026, 2, 4)),
        ("GRB 991231A", dt.date(1999, 12, 31)),
        ("GRB 050805A", dt.date(2005, 8, 5)),
    ],
)
def test_grb_names_carry_their_own_date(name, expected):
    """Swift's table has no date column, so the name is the only source."""
    assert sources.grb_date(name) == expected


def test_an_unparseable_grb_name_is_none_not_a_crash():
    assert sources.grb_date("GRB unnumbered") is None
    assert sources.grb_date("GRB 261332A") is None  # month 13


def test_window_filter_is_inclusive_at_both_ends(grb_records):
    day = grb_records[0].discovered
    kept = sources.in_window(grb_records, day, day)
    assert kept and all(record.discovered == day for record in kept)


def test_already_loaded_names_are_dropped(grb_records):
    first = grb_records[0].name
    kept = sources.without(grb_records, [first])
    assert first not in {record.name for record in kept}
    assert len(kept) == len(grb_records) - 1


# --------------------------------------------------------------------------
# Reproducing the real output files
# --------------------------------------------------------------------------


def test_grb_ptable_is_reproduced_byte_for_byte(grb_records):
    """The strongest check in this file.

    ``GRB.2026.03.31.mod`` is a real loaded file, and every one of its 66 rows
    comes back identical from the live Swift table.
    """
    golden = read("GRB.2026.03.31.mod")
    records = chosen(grb_records, "GRB.2026.03.31.mod")
    assert len(records) == 66
    assert ptable.render("GRB", "2026GRB03.C...0000.", records) == golden


def test_frb_ptable_matches_except_for_the_heading_row(frb_records):
    """Same, but the real FRB heading row is malformed and we fix it.

    The original reads ``skip  |name1\\t    |coordx1   |coordy1   |``: it holds
    a tab and is three characters shorter than its data rows, so the labels do
    not sit over their columns. Every data row still has to match exactly.
    """
    golden = read("FRB.2026.03.31.mod").splitlines()
    records = chosen(frb_records, "FRB.2026.03.31.mod")
    assert len(records) == 33
    got = ptable.render("FRB", "2026FRB...C...0000.", records).splitlines()

    assert len(got) == len(golden)
    differing = [i for i, (a, b) in enumerate(zip(got, golden)) if a != b]
    assert len(differing) == 1, [golden[i] for i in differing]

    only = differing[0]
    assert "\t" in golden[only] and "\t" not in got[only]
    assert golden[only].split("|") != got[only].split("|")
    # Same labels, only the padding changed.
    assert [f.strip() for f in golden[only].split("|")] == [
        f.strip() for f in got[only].split("|")
    ]
    # And now the heading lines up with the data, which it did not before.
    assert len(got[only]) == len(got[only + 1])


def test_the_generated_frb_heading_would_survive_the_xnedit_macros():
    """CLAUDE.md notes the pipe and pad macros refuse a buffer holding a tab.

    The real file could not be re-padded by Pad Columns without the tab being
    removed first, which is a second reason not to reproduce it.
    """
    records = [
        sources.Transient(
            "FRB",
            "FRB 20250924A",
            "20:31:06.360",
            "+53:50:56.40",
            dt.date(2025, 9, 24),
            tns_id="189222",
        )
    ]
    assert "\t" not in ptable.render("FRB", "2026FRB...C...0000.", records)


def test_every_ptable_row_is_the_same_width_as_its_heading():
    """Alignment is the format; a row out of step means a misparsed column."""
    records = [
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
            uncertainty="2.0",
        ),
    ]
    lines = ptable.render("GRB", "2026GRB03.C...0000.", records).splitlines()
    table = [line for line in lines if not line.startswith("##")]
    assert len({len(line) for line in table}) == 1, table


def test_an_empty_ptable_is_refused():
    """Writing an empty file would look like a completed load of nothing."""
    with pytest.raises(ValueError, match="empty"):
        ptable.render("FRB", "2026FRB...C...0000.", [])


def test_ptable_name_follows_the_real_files():
    assert ptable.name_for("FRB", dt.date(2026, 3, 31)) == "FRB.2026.03.31.mod"


def test_only_the_sampled_layouts_are_marked_confirmed():
    """TNS has no real sample, and the tool has to keep saying so."""
    assert ptable.CONFIRMED == {"FRB", "GRB"}
    assert "TNS" in ptable.LAYOUTS


# --------------------------------------------------------------------------
# Reading back what is already loaded
# --------------------------------------------------------------------------


def test_loaded_names_reads_both_real_layouts():
    """One has a skip column in front of name1 and the other does not."""
    frb = ptable.loaded_names(read("FRB.2026.03.31.mod"))
    grb = ptable.loaded_names(read("GRB.2026.03.31.mod"))
    assert len(frb) == 33 and frb[0] == "FRB 20250924A"
    assert len(grb) == 66 and grb[0] == "GRB 260204A"


def test_a_rerun_finds_nothing_new(tmp_path, grb_records):
    """The tree on disk is the record of what has been loaded."""
    root = tmp_path / "data.tables"
    target = root / "2026" / "SNe+FRB+GRB" / "SNe+FRB+GRB-a-SIP3" / "GRB"
    target.mkdir(parents=True)
    records = chosen(grb_records, "GRB.2026.03.31.mod")
    (target / "GRB.2026.03.31.mod").write_text(
        ptable.render("GRB", "2026GRB03.C...0000.", records), encoding="utf-8"
    )

    already = layout.existing_names(str(root), 2026)
    assert len(sources.without(records, already)) == 0
    # And a genuinely new object still gets through, so this is not just
    # dropping everything.
    fresh = [record for record in grb_records if record.name not in set(already)]
    assert fresh, "the fixture has no object outside the loaded file"


# --------------------------------------------------------------------------
# Cluster reporting
# --------------------------------------------------------------------------


def test_clusters_find_the_known_chime_runs(frb_records):
    """The seven-plus contiguous CHIME runs in the real candidate window."""
    found = sources.clusters(frb_records)
    assert found, "no runs detected at all"
    biggest = max(found, key=lambda cluster: cluster.size)
    assert biggest.size == 27
    assert biggest.group == "CHIMEFRB"
    assert (biggest.first, biggest.last) == (177067, 177093)


def test_clustering_never_drops_a_candidate(frb_records):
    """It groups for reading. It is not a filter, and must not become one."""
    found = sources.clusters(frb_records)
    grouped = {record.name for cluster in found for record in cluster.members}
    assert grouped <= {record.name for record in frb_records}
    for cluster in found:
        assert cluster.last - cluster.first == cluster.size - 1
        assert len({record.group for record in cluster.members}) == 1


def test_clusters_are_not_the_selection_rule(frb_records):
    """Pinning the finding that stopped this becoming an automatic filter.

    The real file keeps objects that sit inside contiguous runs, so a tool that
    dropped every clustered object would throw away rows a human kept. If this
    ever starts passing as an equality, the rule was found and the tool can be
    revisited.
    """
    kept = set(ptable.loaded_names(read("FRB.2026.03.31.mod")))
    clustered = {
        record.name
        for cluster in sources.clusters(frb_records)
        for record in cluster.members
    }
    assert kept & clustered, "expected some kept objects to sit inside runs"
    assert kept - clustered, "expected some kept objects to sit outside runs"


def test_ungrouped_records_produce_no_clusters(grb_records):
    """GRBs have no TNS id, so there is nothing to cluster on."""
    assert sources.clusters(grb_records) == []


# --------------------------------------------------------------------------
# The Swift table needs no human selection
# --------------------------------------------------------------------------


def test_the_grb_file_is_a_contiguous_slice_of_the_swift_table(grb_records):
    """Unlike FRBs, GRBs are loaded wholesale.

    The real GRB file holds every burst between its oldest and newest, in the
    same order, with no gaps. That is what makes the GRB side fully automatic
    and is worth pinning, because a gap appearing would mean selection had
    started happening there too.
    """
    names = [record.name for record in grb_records]
    kept = ptable.loaded_names(read("GRB.2026.03.31.mod"))
    window = names[names.index(kept[0]) : names.index(kept[-1]) + 1]
    assert window == kept


# --------------------------------------------------------------------------
# Directory layout
# --------------------------------------------------------------------------


def test_batch_directory_matches_the_procedure():
    assert layout.batch_dir("/data.tables", 2026, "a").endswith(
        "/2026/SNe+FRB+GRB/SNe+FRB+GRB-a-SIP3"
    )


def test_planned_tree_holds_flt_lbl_and_a_directory_per_source():
    paths = layout.planned("/data.tables", 2026, "a", ["FRB", "GRB"])
    tails = [path.rsplit("/", 1)[-1] for path in paths]
    assert "flt" in tails and "lbl" in tails
    assert "FRB" in tails and "GRB" in tails
    assert "TNS" not in tails


def test_create_is_repeatable(tmp_path):
    paths = layout.planned(str(tmp_path), 2026, "a", ["GRB"])
    assert layout.create(paths) == paths
    assert layout.create(paths) == []


# --------------------------------------------------------------------------
# Carrying the window between steps
# --------------------------------------------------------------------------


def test_the_window_survives_between_commands(tmp_path):
    """``fetch`` records the window so ``ptable`` does not need it typed again.

    Swift publishes one undated table, so the window is applied locally and a
    ``ptable`` run that guessed differently from ``fetch`` would silently build
    the wrong file.
    """
    root = str(tmp_path)
    layout.create(layout.planned(root, 2026, "a", ["GRB"]))
    since, until = dt.date(2025, 6, 1), dt.date(2026, 2, 5)
    layout.write_window(root, 2026, "a", since, until)
    assert layout.read_window(root, 2026, "a") == (since, until)


def test_no_recorded_window_reads_as_missing(tmp_path):
    assert layout.read_window(str(tmp_path), 2026, "a") is None


def test_the_cache_extension_records_which_route_answered():
    """``_raw`` is read by people, so a .csv holding a web page is a lie."""
    assert layout.raw_name("FRB", read("tns-frb.csv")) == "tns-frb.csv"
    assert layout.raw_name("FRB", read("tns-frb-page.html")) == "tns-frb.html"
    assert layout.raw_name("GRB", read("swift-xrt.txt")) == "swift-xrt.txt"


def test_a_cached_response_is_found_under_either_extension(tmp_path):
    root = str(tmp_path)
    layout.create(layout.planned(root, 2026, "a", ["FRB"]))
    assert layout.cached(root, 2026, "a", "FRB") is None

    page = os.path.join(layout.raw_dir(root, 2026, "a"), "tns-frb.html")
    with open(page, "w", encoding="utf-8") as handle:
        handle.write(read("tns-frb-page.html"))
    assert layout.cached(root, 2026, "a", "FRB") == page


def test_ptables_reports_only_sources_that_have_one(tmp_path, grb_records):
    root = str(tmp_path)
    layout.create(layout.planned(root, 2026, "a", ["FRB", "GRB"]))
    assert layout.ptables(root, 2026, "a") == []

    target = tmp_path / "2026/SNe+FRB+GRB/SNe+FRB+GRB-a-SIP3/GRB/GRB.2026.03.31.mod"
    target.write_text(
        ptable.render("GRB", "2026GRB03.C...0000.", grb_records[:2]), encoding="utf-8"
    )
    assert layout.ptables(root, 2026, "a") == ["GRB"]


# --------------------------------------------------------------------------
# The commands
# --------------------------------------------------------------------------


def run_cli(argv):
    """Run the CLI in-process and return its status and captured output."""
    import contextlib
    import io as _io

    from nedtransients import __main__ as cli

    buffer = _io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = cli.main(argv)
    return status, buffer.getvalue()


@pytest.fixture
def offline(monkeypatch):
    """Serve the saved fixtures instead of going to the network."""

    def fake(kind, since, until, tns_csv, out=None):
        return read("tns-frb.csv") if kind == "FRB" else read("swift-xrt.txt")

    monkeypatch.setattr("nedtransients.__main__.download", fake)


BATCH = "2026/SNe+FRB+GRB/SNe+FRB+GRB-a-SIP3"


def base_args(root, *extra):
    return ["--root", str(root), "--batch", "a", "--obtained", "2026-03-31", *extra]


def test_each_step_runs_on_its_own_and_they_chain(tmp_path, offline):
    """The point of splitting them up: run one at a time, in order."""
    root = tmp_path
    common = base_args(root, "--only", "grb")

    status, _ = run_cli(["scaffold"] + common)
    assert status == 0
    assert (root / BATCH / "flt").is_dir()
    assert (root / BATCH / "GRB").is_dir()

    status, output = run_cli(
        ["fetch"] + common + ["--since", "2025-08-05", "--until", "2026-02-04"]
    )
    assert status == 0
    assert (root / BATCH / "_raw" / "swift-xrt.txt").is_file()
    assert "fetched" in output

    # No dates given: it uses the window fetch recorded.
    status, output = run_cli(["ptable"] + common)
    assert status == 0
    assert "2025-08-05 .. 2026-02-04" in output
    built = root / BATCH / "GRB" / "GRB.2026.03.31.mod"
    assert built.is_file()
    # The same 66 rows as the real file, from the same window.
    assert built.read_text(encoding="utf-8") == read("GRB.2026.03.31.mod")

    status, _ = run_cli(["loadstatus"] + common)
    assert status == 0
    assert (root / BATCH / "2026a.GRB.ls").is_file()

    status, output = run_cli(["jira"] + common)
    assert status == 0
    assert refcodes.refcode("GRB", 2026, 3) in output


def test_prepare_produces_the_same_thing_as_the_steps(tmp_path, offline):
    """The chain must not drift from the pieces it is made of."""
    stepwise, chained = tmp_path / "stepwise", tmp_path / "chained"
    window = ["--since", "2025-08-05", "--until", "2026-02-04"]

    for step in ("scaffold", "fetch", "ptable", "loadstatus"):
        argv = [step] + base_args(stepwise, "--only", "grb")
        run_cli(argv + window if step == "fetch" else argv)
    run_cli(["prepare"] + base_args(chained, "--only", "grb") + window)

    def tree(root):
        return sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        )

    assert tree(stepwise) == tree(chained)
    for name in tree(stepwise):
        assert (stepwise / name).read_bytes() == (chained / name).read_bytes(), name


def test_ptable_without_a_fetch_says_so(tmp_path):
    """The steps are independent, so each has to explain what it is missing."""
    status, output = run_cli(
        ["ptable"] + base_args(tmp_path, "--only", "grb") + ["--since", "2025-08-05"]
    )
    assert status == 0
    assert "nothing fetched yet" in output
    assert "fetch --only grb" in output


def test_ptable_with_no_window_anywhere_refuses(tmp_path):
    with pytest.raises(SystemExit, match="fetch"):
        run_cli(["ptable"] + base_args(tmp_path, "--only", "grb"))


def test_an_explicit_window_overrides_the_recorded_one(tmp_path, offline):
    """A narrower ptable can be built out of a wider fetch."""
    common = base_args(tmp_path, "--only", "grb")
    run_cli(["scaffold"] + common)
    run_cli(["fetch"] + common + ["--since", "2025-08-05", "--until", "2026-02-04"])

    run_cli(["ptable"] + common + ["--since", "2026-01-01", "--until", "2026-02-04"])
    rows = ptable.loaded_names(
        (tmp_path / BATCH / "GRB" / "GRB.2026.03.31.mod").read_text(encoding="utf-8")
    )
    assert 0 < len(rows) < 66
    assert all(name >= "GRB 260101" for name in rows)


def test_loadstatus_registers_only_sources_that_built_a_ptable(tmp_path, offline):
    """A refcode for an empty load would point the database at nothing.

    Two sources are asked for and only one has anything in the window, which is
    the ordinary FRB case the procedure warns about.
    """
    common = base_args(tmp_path, "--only", "frb,grb")
    run_cli(["scaffold"] + common)
    run_cli(["fetch"] + common + ["--since", "2026-01-01", "--until", "2026-02-04"])
    run_cli(["ptable"] + common)

    assert layout.ptables(str(tmp_path), 2026, "a") == ["GRB"]
    status, output = run_cli(["loadstatus"] + common)
    assert status == 0
    written = [path.name for path in tmp_path.rglob("*.ls")]
    assert written == ["2026a.GRB.ls"], written
    assert (
        refcodes.refcode("FRB", 2026, 3)
        not in (tmp_path / BATCH / written[0]).read_text()
    )


def test_loadstatus_before_any_ptable_writes_nothing(tmp_path):
    status, output = run_cli(["loadstatus"] + base_args(tmp_path))
    assert status == 0
    assert "Nothing to register" in output
    assert not list(tmp_path.rglob("*.ls"))


def test_dry_run_writes_nothing(tmp_path, offline):
    """Every writing step has to be inspectable before it touches the disk."""
    window = ["--since", "2025-08-05", "--until", "2026-02-04"]
    dry = base_args(tmp_path, "--only", "grb", "--dry-run")

    for step in ("scaffold", "fetch", "prepare"):
        argv = [step] + dry + (window if step != "scaffold" else [])
        status, output = run_cli(argv)
        assert status == 0, step
        assert list(tmp_path.rglob("*")) == [], "{} touched the disk".format(step)
        assert "would" in output, step

    # ptable needs something fetched before it has anything to show, so it gets
    # a real fetch first and then has to leave that alone.
    wet = base_args(tmp_path, "--only", "grb")
    run_cli(["scaffold"] + wet)
    run_cli(["fetch"] + wet + window)
    before = sorted(path.name for path in tmp_path.rglob("*") if path.is_file())

    status, output = run_cli(["ptable"] + dry)
    assert status == 0
    assert "would write" in output
    assert "##refcode" in output
    after = sorted(path.name for path in tmp_path.rglob("*") if path.is_file())
    assert after == before, "ptable --dry-run wrote something"


def test_an_existing_file_is_left_alone_without_force(tmp_path, offline):
    common = base_args(tmp_path, "--only", "grb")
    run_cli(["scaffold"] + common)
    run_cli(["fetch"] + common + ["--since", "2025-08-05", "--until", "2026-02-04"])
    run_cli(["ptable"] + common)

    target = tmp_path / BATCH / "GRB" / "GRB.2026.03.31.mod"
    target.write_text("sentinel", encoding="utf-8")

    _, output = run_cli(["ptable"] + common)
    assert "exists, left alone" in output
    assert target.read_text(encoding="utf-8") == "sentinel"

    run_cli(["ptable"] + common + ["--force"])
    assert target.read_text(encoding="utf-8") != "sentinel"


def test_refcodes_command_prints_just_the_strings():
    status, output = run_cli(["refcodes", "--obtained", "2025-03-04"])
    assert status == 0
    assert output.split() == [
        "TNS",
        "2025TNS...C......0.",
        "FRB",
        "2025FRB...C...0000.",
        "GRB",
        "2025GRB03.C...0000.",
    ]


def test_a_backwards_window_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        run_cli(
            ["fetch"]
            + base_args(tmp_path)
            + ["--since", "2026-07-01", "--until", "2026-06-01"]
        )


def test_unknown_source_names_are_refused(tmp_path):
    with pytest.raises(SystemExit):
        run_cli(["scaffold"] + base_args(tmp_path, "--only", "quasars"))


def test_sne_is_accepted_as_a_name_for_the_tns_list():
    from nedtransients.__main__ import kind_list

    assert kind_list("sne,grb") == ["TNS", "GRB"]


def test_every_step_is_reachable_as_its_own_command():
    """The chain and the command list must not drift apart."""
    from nedtransients.__main__ import STEPS, build_parser

    actions = build_parser()._subparsers._group_actions[0].choices
    for name, _ in STEPS:
        assert name in actions, name
    assert "prepare" in actions


def test_the_user_agent_identifies_the_tool_rather_than_faking_a_browser():
    """TNS blocks a few tool names, not everything that is not a browser.

    Measured: ``curl/*`` and ``python-requests/*`` get 403, while urllib's own
    default, an honest ``nedkit/...`` and a Chrome string all get 200. The
    first version of this spoofed Chrome on the strength of a ``curl`` 403
    generalised into "it wants a browser", which was never measured and was
    wrong.

    So this pins the honest identifier. It works, it says who we are, and it
    gives TNS something to contact if the traffic is ever a problem.
    """
    agent = sources.USER_AGENT
    assert agent.startswith("nedkit/")
    assert "https://" in agent, "no contact URL for TNS to follow"
    for faked in ("Mozilla", "AppleWebKit", "Chrome", "Safari", "Gecko"):
        assert faked not in agent, "do not impersonate a browser: {}".format(agent)
    # And not a name TNS is known to refuse.
    for blocked in ("curl/", "python-requests/"):
        assert blocked not in agent


def test_a_rate_limit_is_reported_as_a_quota_not_an_outage(monkeypatch):
    """429 means wait a minute, and saying so beats a bare HTTPError."""
    import urllib.error

    def limited(*args, **kwargs):
        raise urllib.error.HTTPError("u", sources.TOO_MANY, "Too Many", None, None)

    monkeypatch.setattr("urllib.request.urlopen", limited)
    with pytest.raises(RuntimeError, match="rate limit"):
        sources.fetch("https://example.invalid/")


def test_other_http_errors_are_not_swallowed(monkeypatch):
    """Only the quota gets reinterpreted; a 500 stays a 500."""
    import urllib.error

    def broken(*args, **kwargs):
        raise urllib.error.HTTPError("u", 500, "Server Error", None, None)

    monkeypatch.setattr("urllib.request.urlopen", broken)
    with pytest.raises(urllib.error.HTTPError):
        sources.fetch("https://example.invalid/")
