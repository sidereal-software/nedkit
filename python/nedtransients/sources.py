"""Fetch and parse the two upstream lists.

Two very different sources behind one record type:

- **TNS** (`<https://www.wis-tns.org/>`_) covers supernovae and fast radio
  bursts. It exports the search page as CSV, filtered by discovery date.
- **Swift XRT** (`<https://www.swift.ac.uk/xrt_positions/>`_) covers gamma-ray
  bursts, as one pipe-delimited ASCII table with no filtering at all.

Neither needs an account. TNS blocks a short list of well-known tool names by
User-Agent, which an honest identifier is not on. See :data:`USER_AGENT`.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import List, NamedTuple, Optional, Sequence

#: What we tell TNS and Swift we are.
#:
#: TNS blocks some clients by User-Agent, and it is worth being precise about
#: which, because the obvious conclusion is the wrong one. Measured against the
#: live search endpoint:
#:
#: ==============================  ======  =======================
#: ``User-Agent``                  Result
#: ==============================  ======  =======================
#: ``curl/8.7.1``                  403     blocked
#: ``python-requests/2.32``        403     blocked
#: ``Python-urllib/3.x`` (default) 200     fine
#: ``nedkit/...`` (this one)       200     fine
#: a Chrome string                 200     fine
#: ==============================  ======  =======================
#:
#: So it is a blocklist of two or three well-known tool names, not a demand to
#: look like a browser. An honest identifier passes, which means there is no
#: reason to impersonate Chrome: this says who we are and gives them something
#: to contact if the traffic is ever a problem.
#:
#: The sanctioned route for heavier use is a registered bot ID plus a
#: ``tns_marker`` header, which also unlocks the bulk daily-delta CSVs. See
#: :func:`tns_url` for where that would slot in.
USER_AGENT = "nedkit/0.1 (+https://nedkit.sidereal.software)"

#: TNS applies a request quota over a 60-second window and answers **429** when
#: it is exceeded. Three requests a month is nowhere near it, but a loop under
#: development easily is, so the error says which it was.
TOO_MANY = 429

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

    Raises
    ------
    RuntimeError
        On 429, with what to do about it. Left as a plain ``HTTPError`` this
        reads as a site outage rather than as a quota, and the fix is to wait
        rather than to investigate.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        if error.code == TOO_MANY:
            raise RuntimeError(
                "TNS rate limit hit (429). It resets within a minute; wait and "
                "re-run. Nothing already fetched is lost."
            ) from error
        raise


def tns_url(
    since: dt.date,
    until: dt.date,
    frb: bool = False,
    page: int = 0,
    page_size: int = TNS_PAGE_SIZE,
    as_csv: bool = True,
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
    as_csv : bool, optional
        Ask for the CSV export. With ``False`` the same query returns the
        ordinary results page, which :func:`parse_tns` can also read. See
        :func:`fetch_tns`.

    Returns
    -------
    str
        A URL whose response is CSV, or HTML if ``as_csv`` is false.
    """
    params = [
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
    if as_csv:
        params.insert(0, ("format", "csv"))
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
    as_csv: bool = True,
) -> str:
    """Fetch every page of a TNS search and return them as one document.

    TNS paginates, and a window wider than a month easily exceeds one page.
    Taking only the first page would silently drop the rest, which reads
    exactly like there being nothing more to load.

    There is no API key here, so this reads the site the way a person would.
    That means two routes to the same query, and :func:`fetch_tns_resilient`
    uses the second when the first stops working.

    Parameters
    ----------
    since, until : datetime.date
        Inclusive discovery-date bounds.
    frb : bool, optional
        Ask for fast radio bursts rather than classified supernovae.
    page_size : int, optional
        Rows per page.
    as_csv : bool, optional
        Use the CSV export. With ``False``, collect the results pages instead.

    Returns
    -------
    str
        One CSV with the heading row once, or the concatenated results pages.
        Either is something :func:`parse_tns` can read.

    Raises
    ------
    RuntimeError
        If the page limit is reached, which means the window is far wider than
        this tool expects and the result would be truncated.
    """
    heading = ""
    body = []
    pages = []
    for page in range(TNS_MAX_PAGES):
        text = fetch(
            tns_url(
                since, until, frb=frb, page=page, page_size=page_size, as_csv=as_csv
            )
        )
        if not as_csv:
            pages.append(text)
            # The results page has no row count to read, so count the rows.
            if len(_parse_tns_html(text, "TNS")) < page_size:
                return "\n".join(pages)
            continue
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


def fetch_tns_resilient(
    since: dt.date,
    until: dt.date,
    frb: bool = False,
    page_size: int = TNS_PAGE_SIZE,
    on_fallback=None,
) -> str:
    """Fetch a TNS search, falling back to the results page if the CSV fails.

    Without an API key the only way in is to read the site, so the guard
    against it changing is to know two ways in rather than one. The CSV export
    is tried first because it is structured and cheap; the results page is the
    same query rendered for a person, and its cells carry the same fields.
    Both were checked against each other and agree row for row.

    A fallback is not silent. It means the primary route has broken and
    somebody should look, even though the run itself succeeded.

    Parameters
    ----------
    since, until : datetime.date
        Inclusive discovery-date bounds.
    frb : bool, optional
        Ask for fast radio bursts rather than classified supernovae.
    page_size : int, optional
        Rows per page.
    on_fallback : callable, optional
        Called with a message when the CSV route fails and the page route is
        used instead.

    Returns
    -------
    str
        Whichever document was obtained.

    Raises
    ------
    Exception
        If both routes fail, the second route's error is raised. A rate limit
        is not retried on the other route, since the quota covers both.
    """
    try:
        text = fetch_tns(since, until, frb=frb, page_size=page_size)
        parse_tns(text, "FRB" if frb else "TNS")
        return text
    except RuntimeError:
        # Either the page cap or the rate limit. Neither is fixed by asking
        # the same server the same question a different way.
        raise
    except Exception as error:
        if on_fallback is not None:
            on_fallback(
                "TNS CSV export failed ({}: {}). Falling back to the results "
                "page. The run is fine; the CSV route needs looking at.".format(
                    type(error).__name__, error
                )
            )
        return fetch_tns(since, until, frb=frb, page_size=page_size, as_csv=False)


class _ResultRows(HTMLParser):
    """Pull the result rows out of a TNS search page.

    The results table marks every cell with ``class="cell-<field>"``, and the
    field names match the CSV export's columns closely enough to map one to
    one. A row counts as a result when it has both a name and a position;
    that is what separates it from the nested detail rows TNS puts underneath
    each object, which a regex over ``<tr>`` cannot tell apart.

    ``html.parser`` rather than BeautifulSoup, because the NED team's machines
    have no way to install packages.
    """

    def __init__(self) -> None:
        HTMLParser.__init__(self, convert_charrefs=True)
        self.rows = []  # type: List[dict]
        self._open = []  # type: List[dict]
        self._field = None  # type: Optional[str]
        self._text = []  # type: List[str]

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._open.append({})
        elif tag == "td" and self._open:
            for name in (dict(attrs).get("class") or "").split():
                if name.startswith("cell-"):
                    self._field = name[len("cell-") :]
                    self._text = []

    def handle_data(self, data):
        if self._field is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self._field is not None and self._open:
            # setdefault: a nested table's cell must not overwrite the row's.
            self._open[-1].setdefault(self._field, "".join(self._text).strip())
            self._field = None
        elif tag == "tr" and self._open:
            row = self._open.pop()
            if row.get("name") and row.get("ra"):
                self.rows.append(row)


#: Maps the CSV export's column names onto the search page's cell classes, so
#: one parser can read either.
HTML_COLUMNS = {
    "ID": "id",
    "Name": "name",
    "RA": "ra",
    "DEC": "decl",
    "Obj. Type": "objtype_name",
    "Redshift": "redshift",
    "Host Name": "hostname",
    "Reporting Group/s": "reporting_group_name",
    "Discovery Date (UT)": "discoverydate",
}


def parse_tns(text: str, kind: str) -> "List[Transient]":
    """Parse a TNS response into records, in either format it comes in.

    TNS serves the same query two ways, and this reads both: the CSV export,
    and the ordinary results page. Which one arrived is sniffed from the
    content rather than tracked alongside it, so a cached response is
    self-describing and ``--tns-csv`` keeps working whichever a person saved.

    Parameters
    ----------
    text : str
        A CSV body including its heading row, or a search results page.
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
        If the text is neither format, or the expected columns are missing.
        That is how a change at TNS surfaces, rather than as an empty list
        that reads like a quiet month.
    """
    if "cell-name" in text:
        return _parse_tns_html(text, kind)
    heading = text.split("\n", 1)[0]
    # A quoted, comma-separated heading is the CSV export. Sniffing only that
    # far leaves a CSV with the wrong columns to the column check below, whose
    # message names what is missing.
    if not (heading.startswith('"') and '","' in heading):
        raise ValueError(
            "TNS response is neither the CSV export nor a results page; the "
            "site may have changed, or this may be an error page"
        )
    reader = csv.DictReader(io.StringIO(text))
    required = {"ID", "Name", "RA", "DEC", "Discovery Date (UT)"}
    missing = required - set(reader.fieldnames or ())
    if missing:
        raise ValueError(
            "TNS export is missing {}; the site's columns may have changed".format(
                ", ".join(sorted(missing))
            )
        )

    return [record for record in (_record(row, kind) for row in reader) if record]


def _parse_tns_html(text: str, kind: str) -> "List[Transient]":
    """Parse a TNS search results page into records.

    The fallback route. Its cells are renamed to the CSV export's column names
    so both formats build records the same way, which is the only thing
    keeping the two from drifting apart.

    Parameters
    ----------
    text : str
        A search results page.
    kind : str
        ``"TNS"`` or ``"FRB"``.

    Returns
    -------
    list of Transient
        In the order the page listed them.
    """
    parser = _ResultRows()
    parser.feed(text)
    found = []
    for row in parser.rows:
        renamed = {column: row.get(cell, "") for column, cell in HTML_COLUMNS.items()}
        record = _record(renamed, kind)
        if record:
            found.append(record)
    return found


def _record(row: dict, kind: str) -> "Optional[Transient]":
    """Build one record from a row keyed by the CSV export's column names.

    Parameters
    ----------
    row : dict
        One row, however it was parsed.
    kind : str
        ``"TNS"`` or ``"FRB"``.

    Returns
    -------
    Transient or None
        ``None`` for a row with no usable discovery date, which is not
        something to load and not something to complain about either.
    """
    discovered = (row.get("Discovery Date (UT)") or "")[:10]
    if not discovered:
        return None
    try:
        day = dt.date.fromisoformat(discovered)
    except ValueError:
        return None
    return Transient(
        kind=kind,
        name=row["Name"].strip(),
        ra=row["RA"].strip(),
        dec=row["DEC"].strip(),
        discovered=day,
        tns_id=(row.get("ID") or "").strip(),
        obj_type=(row.get("Obj. Type") or "").strip(),
        redshift=(row.get("Redshift") or "").strip(),
        host=(row.get("Host Name") or "").strip(),
        group=(row.get("Reporting Group/s") or "").strip(),
    )


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
