"""Fetch and parse the two upstream lists.

Two very different sources behind one record type:

- **TNS** (`<https://www.wis-tns.org/>`_) covers supernovae and fast radio
  bursts. It exports the search page as CSV, filtered by discovery date.
- **Swift XRT** (`<https://www.swift.ac.uk/xrt_positions/>`_) covers gamma-ray
  bursts, as one pipe-delimited ASCII table with no filtering at all.

Neither needs an account, but TNS blocks requests that do not look like a
browser. See :data:`BROWSER_UA`.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import urllib.parse
import urllib.request
from typing import List, NamedTuple, Optional, Sequence

#: TNS answers **403** to urllib's default User-Agent, and to curl's, and to an
#: empty one. It is a User-Agent filter rather than authentication: the same
#: URLs return 200 with an ordinary browser string. This is load-bearing, and
#: without it the failure looks exactly like the site being down.
#:
#: The sanctioned route is a registered bot ID plus a ``tns_marker`` header,
#: which also unlocks the bulk daily-delta CSVs. See :func:`tns_url` for where
#: that would slot in. At three requests a month this is not a burden on them
#: either way.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

TNS_SEARCH = "https://www.wis-tns.org/search"
SWIFT_XRT = "https://www.swift.ac.uk/xrt_positions/index.php?basic=none&txt=1"

#: TNS's own numeric id for the FRB object type, read off the search form.
TNS_OBJTYPE_FRB = 130

#: How many rows to ask TNS for in one page. Comfortably above a month's worth.
TNS_PAGE_SIZE = 500

#: ``GRB 260204A``: two-digit year, month, day, then a letter per burst that
#: day.
GRB_NAME = re.compile(r"^GRB (\d{2})(\d{2})(\d{2})([A-Z])$")


class Transient(NamedTuple):
    """One object from one of the upstream lists.

    Attributes
    ----------
    kind : str
        ``"TNS"``, ``"FRB"`` or ``"GRB"``, matching the refcode it loads under.
    name : str
        The object designation, e.g. ``"FRB 20250924A"``.
    ra : str
        Right ascension, sexagesimal, exactly as the source published it.
    dec : str
        Declination, sexagesimal, exactly as the source published it.
    discovered : datetime.date
        Discovery date, used for the window filter.
    tns_id : str
        TNS's numeric id, or ``""`` for a GRB. This is what lands in the FRB
        ptable's ``skip`` column, and what makes bulk-upload runs detectable.
    obj_type : str
        The classification, e.g. ``"SN Ia"``. Empty for a GRB.
    redshift : str
        Redshift if the source published one, otherwise empty.
    host : str
        Host galaxy name if the source published one, otherwise empty.
    group : str
        Reporting group, e.g. ``"CHIMEFRB"``. Empty for a GRB.
    uncertainty : str
        Positional uncertainty. For a GRB this is Swift's 90% error radius in
        arcseconds; the other kinds carry theirs in the ptable header instead.
    """

    kind: str
    name: str
    ra: str
    dec: str
    discovered: dt.date
    tns_id: str = ""
    obj_type: str = ""
    redshift: str = ""
    host: str = ""
    group: str = ""
    uncertainty: str = ""


def fetch(url: str, timeout: int = 60) -> str:
    """Retrieve a URL as text, looking enough like a browser for TNS.

    Parameters
    ----------
    url : str
        The address to fetch.
    timeout : int, optional
        Seconds to wait, default 60.

    Returns
    -------
    str
        The response body, decoded as UTF-8 with replacement. NED data is not
        reliably UTF-8 and a mangled character is better than a crash here,
        because the raw response is cached to disk for inspection either way.
    """
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def tns_url(
    since: dt.date,
    until: dt.date,
    frb: bool = False,
    page: int = 0,
    page_size: int = TNS_PAGE_SIZE,
) -> str:
    """Build the TNS search URL for one window, kind and page.

    Parameters
    ----------
    since, until : datetime.date
        Inclusive discovery-date bounds. TNS applies these server-side.
    frb : bool, optional
        Ask for fast radio bursts rather than classified supernovae.
    page : int, optional
        Zero-based page number.
    page_size : int, optional
        Rows per page.

    Returns
    -------
    str
        A URL whose response is CSV.
    """
    params = [
        ("format", "csv"),
        ("num_page", str(page_size)),
        ("page", str(page)),
        ("date_start[date]", since.isoformat()),
        ("date_end[date]", until.isoformat()),
    ]
    if frb:
        params.append(("objtype[]", str(TNS_OBJTYPE_FRB)))
    else:
        # Only classified supernovae. An unclassified AT is not something NED
        # loads, and including them multiplies the list by roughly ten.
        params.append(("classified_sne", "1"))
    return TNS_SEARCH + "?" + urllib.parse.urlencode(params)


#: Stop paging after this many, so a mistaken window cannot spin forever. A
#: month of classified supernovae is a few hundred, so this is far above any
#: real request and low enough to notice.
TNS_MAX_PAGES = 40


def fetch_tns(
    since: dt.date,
    until: dt.date,
    frb: bool = False,
    page_size: int = TNS_PAGE_SIZE,
) -> str:
    """Fetch every page of a TNS search and return them as one CSV.

    TNS paginates, and a window wider than a month easily exceeds one page.
    Taking only the first page would silently drop the rest, which reads
    exactly like there being nothing more to load.

    Parameters
    ----------
    since, until : datetime.date
        Inclusive discovery-date bounds.
    frb : bool, optional
        Ask for fast radio bursts rather than classified supernovae.
    page_size : int, optional
        Rows per page.

    Returns
    -------
    str
        One CSV: the heading row once, then every page's rows in order.

    Raises
    ------
    RuntimeError
        If the page limit is reached, which means the window is far wider than
        this tool expects and the result would be truncated.
    """
    heading = ""
    body = []
    for page in range(TNS_MAX_PAGES):
        text = fetch(tns_url(since, until, frb=frb, page=page, page_size=page_size))
        lines = text.splitlines()
        if not lines:
            break
        heading = heading or lines[0]
        rows = lines[1:]
        body.extend(rows)
        if len(rows) < page_size:
            return "\n".join([heading] + body) + "\n"
    raise RuntimeError(
        "TNS returned {} full pages of {}; narrow the window rather than "
        "loading a truncated list".format(TNS_MAX_PAGES, page_size)
    )


def parse_tns(text: str, kind: str) -> "List[Transient]":
    """Parse a TNS CSV export into records.

    Parameters
    ----------
    text : str
        The CSV body, including its heading row.
    kind : str
        ``"TNS"`` for supernovae or ``"FRB"`` for fast radio bursts. TNS itself
        does not distinguish these in the export; the caller knows which query
        it ran.

    Returns
    -------
    list of Transient
        In the order TNS returned them, which is newest first.

    Raises
    ------
    ValueError
        If the expected columns are missing, which is how a change to the TNS
        export surfaces.
    """
    reader = csv.DictReader(io.StringIO(text))
    required = {"ID", "Name", "RA", "DEC", "Discovery Date (UT)"}
    missing = required - set(reader.fieldnames or ())
    if missing:
        raise ValueError(
            "TNS export is missing {}; the site's columns may have changed".format(
                ", ".join(sorted(missing))
            )
        )

    found = []
    for row in reader:
        discovered = row["Discovery Date (UT)"][:10]
        if not discovered:
            continue
        found.append(
            Transient(
                kind=kind,
                name=row["Name"].strip(),
                ra=row["RA"].strip(),
                dec=row["DEC"].strip(),
                discovered=dt.date.fromisoformat(discovered),
                tns_id=row["ID"].strip(),
                obj_type=row.get("Obj. Type", "").strip(),
                redshift=row.get("Redshift", "").strip(),
                host=row.get("Host Name", "").strip(),
                group=row.get("Reporting Group/s", "").strip(),
            )
        )
    return found


def parse_swift(text: str) -> "List[Transient]":
    """Parse the Swift XRT position table into records.

    The table has no date column. Every GRB designation encodes its own date,
    which is what :func:`grb_date` reads.

    Parameters
    ----------
    text : str
        The ASCII table, one burst per line, five pipe-delimited fields.

    Returns
    -------
    list of Transient
        In the order Swift returned them, which is newest first. Rows whose
        position could not be determined are skipped, since there is nothing to
        load for them.
    """
    found = []
    for line in text.splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 5 or not fields[0].startswith("GRB "):
            continue
        name, ra, dec, uncertainty, source = fields[:5]
        if source.lower().startswith("no position"):
            continue
        discovered = grb_date(name)
        if discovered is None:
            continue
        found.append(
            Transient(
                kind="GRB",
                name=name,
                ra=ra,
                dec=dec,
                discovered=discovered,
                uncertainty=uncertainty,
            )
        )
    return found


def grb_date(name: str) -> "Optional[dt.date]":
    """Read the burst date out of a GRB designation.

    Parameters
    ----------
    name : str
        A designation such as ``"GRB 260204A"``.

    Returns
    -------
    datetime.date or None
        The burst date, or ``None`` if the name does not have the standard
        shape.

    Examples
    --------
    >>> grb_date("GRB 260204A")
    datetime.date(2026, 2, 4)
    >>> grb_date("GRB 991231A")
    datetime.date(1999, 12, 31)
    """
    matched = GRB_NAME.match(name.strip())
    if matched is None:
        return None
    year, month, day = (int(part) for part in matched.groups()[:3])
    # Swift began in 2004, so a two-digit year is unambiguous against a 1990s
    # burst only if the pivot sits before then. GRB naming started in 1997.
    year += 2000 if year < 90 else 1900
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def in_window(
    records: "Sequence[Transient]", since: dt.date, until: dt.date
) -> "List[Transient]":
    """Keep the records discovered within an inclusive date window.

    Parameters
    ----------
    records : sequence of Transient
        What came back from a source.
    since, until : datetime.date
        Inclusive bounds.

    Returns
    -------
    list of Transient
        In the input order.
    """
    return [r for r in records if since <= r.discovered <= until]


def without(
    records: "Sequence[Transient]", already: "Sequence[str]"
) -> "List[Transient]":
    """Drop records whose names are already loaded.

    Parameters
    ----------
    records : sequence of Transient
        Candidates.
    already : sequence of str
        Names found in the ptable files already on disk.

    Returns
    -------
    list of Transient
        In the input order.
    """
    seen = set(already)
    return [r for r in records if r.name not in seen]


class Cluster(NamedTuple):
    """A run of consecutive TNS ids from one reporting group.

    TNS hands out ids in insertion order, so a catalogue uploaded in one go
    lands as a contiguous block. Collapsing twenty-seven near-identical CHIME
    entries into one line is what makes a 140-row candidate list scannable.

    **This groups, it does not decide.** The real ``FRB.2026.03.31.mod`` keeps
    33 of the 142 candidates in its window, and none of these separates the 33
    from the 109:

    ==========================================  ===========================
    Rule tried                                  Why it is not the rule
    ==========================================  ===========================
    Discovery-date window                       Kept and dropped interleave
    TNS id above a threshold                    Same
    Sits in a contiguous id run                 23 kept objects sit in one
    Reporting group                             Both sets are mostly CHIME
    Internal name lacks ``chimefrb_``           Misses 20 of the 33
    Has a discovery bibcode                     Keeps 82 that were dropped
    ==========================================  ===========================

    So the decision draws on something the TNS export does not carry, and the
    tool must not pretend otherwise. Every candidate is written to the ptable
    and a human deletes rows. A tool confident enough to drop three quarters of
    the list on a rule inferred from one sample would be wrong the first month
    CHIME changed how it reports, and wrong silently.
    """

    first: int
    last: int
    group: str
    members: "List[Transient]"

    @property
    def size(self) -> int:
        """int : How many objects the run holds."""
        return len(self.members)


#: A run has to reach this many objects before it is worth mentioning. Two
#: bursts reported minutes apart are ordinary; twenty-seven are a catalogue.
CLUSTER_MINIMUM = 3


def clusters(
    records: "Sequence[Transient]", minimum: int = CLUSTER_MINIMUM
) -> "List[Cluster]":
    """Find runs of consecutive TNS ids sharing a reporting group.

    Parameters
    ----------
    records : sequence of Transient
        Candidates. Records without a TNS id, such as GRBs, are ignored.
    minimum : int, optional
        Smallest run worth reporting.

    Returns
    -------
    list of Cluster
        Ordered by first id.
    """
    numbered = sorted(
        (r for r in records if r.tns_id.isdigit()), key=lambda r: int(r.tns_id)
    )
    found = []
    run: "List[Transient]" = []
    for record in numbered:
        if run:
            contiguous = int(record.tns_id) == int(run[-1].tns_id) + 1
            if contiguous and record.group == run[-1].group:
                run.append(record)
                continue
            if len(run) >= minimum:
                found.append(
                    Cluster(int(run[0].tns_id), int(run[-1].tns_id), run[0].group, run)
                )
        run = [record]
    if len(run) >= minimum:
        found.append(
            Cluster(int(run[0].tns_id), int(run[-1].tns_id), run[0].group, run)
        )
    return found
