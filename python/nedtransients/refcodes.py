"""NED-only refcodes, the loadstatus file that registers them, and the Jira text.

Before any transient can be loaded, the three sources it came from need
refcodes, and those refcodes do not exist at ADS: NED makes them up. The shape
is documented in ``SNeFRBGRBProcedures.pdf`` and confirmed by the real
``2026a.TNS.FRB.GRB.ls``.

The month is encoded twice over, differently:

============  ==================================  =======================
Source        Pattern                             March 2025
============  ==================================  =======================
TNS           ``YYYYTNS...M......0.``             ``2025TNS...C......0.``
FRB           ``YYYYFRB...M...0000.``             ``2025FRB...C...0000.``
GRB           ``YYYYGRBmm.C...0000.``             ``2025GRB03.C...0000.``
============  ==================================  =======================

``M`` is the month as a letter with A for January, so March is ``C``. GRB uses
the two-digit month instead, and the ``C`` sitting in its refcode is a literal
standing for "Catalog" rather than a month. Getting those two confused produces
a refcode that looks right and points at the wrong month.
"""

from __future__ import annotations

#: Every refcode is this long. A wrong-length one parses far enough to reach
#: loadstatus before anything complains, so it is checked here instead.
REFCODE_LENGTH = 19

#: The three sources, in the order they appear in a .ls file.
KINDS = ("TNS", "FRB", "GRB")

#: What each source is called in prose, for reports and error messages.
KIND_LABELS = {
    "TNS": "IAU-named SNe",
    "FRB": "FRBs",
    "GRB": "GRBs",
}

#: Where each source's list comes from. Quoted in the Jira ticket.
KIND_URLS = {
    "TNS": "https://wis-tns.weizmann.ac.il/",
    "FRB": "https://wis-tns.weizmann.ac.il/",
    "GRB": "http://www.swift.ac.uk/xrt_positions/",
}

#: Who gets credited as the author of each NED-made refcode.
KIND_AUTHORS = {
    "TNS": "Transient Name Server Collaboration",
    "FRB": "Transient Name Server Collaboration",
    "GRB": "Neil Gehrels Swift Observatory Science Data Centre",
}


def month_letter(month: int) -> str:
    """Return the letter TNS and FRB refcodes use for a month.

    Parameters
    ----------
    month : int
        Month number, 1 through 12.

    Returns
    -------
    str
        A single upper-case letter, ``A`` for January through ``L`` for
        December.

    Raises
    ------
    ValueError
        If ``month`` is outside 1 to 12.

    Examples
    --------
    >>> month_letter(3)
    'C'
    >>> month_letter(7)
    'G'
    """
    if not 1 <= month <= 12:
        raise ValueError("month out of range: {!r}".format(month))
    return chr(ord("A") + month - 1)


def refcode(kind: str, year: int, month: int) -> str:
    """Build the NED-only refcode for one source and month.

    Parameters
    ----------
    kind : str
        One of ``"TNS"``, ``"FRB"`` or ``"GRB"``.
    year : int
        Four-digit year.
    month : int
        Month number, 1 through 12.

    Returns
    -------
    str
        A 19-character refcode. The trailing character is ``.`` rather than the
        ``:`` a bibcode would carry, which is what marks it NED-made.

    Raises
    ------
    ValueError
        If ``kind`` is not one of the three, or the month is out of range, or
        the result somehow came out the wrong length.

    Examples
    --------
    >>> refcode("TNS", 2025, 3)
    '2025TNS...C......0.'
    >>> refcode("FRB", 2025, 3)
    '2025FRB...C...0000.'
    >>> refcode("GRB", 2025, 3)
    '2025GRB03.C...0000.'
    """
    if kind not in KINDS:
        raise ValueError("unknown source: {!r}".format(kind))
    if not 1 <= month <= 12:
        raise ValueError("month out of range: {!r}".format(month))

    if kind == "GRB":
        # The C here is "Catalog", not the month. The month is the "03".
        built = "{:04d}GRB{:02d}.C...0000.".format(year, month)
    elif kind == "FRB":
        built = "{:04d}FRB...{}...0000.".format(year, month_letter(month))
    else:
        built = "{:04d}TNS...{}......0.".format(year, month_letter(month))

    if len(built) != REFCODE_LENGTH:
        raise ValueError(
            "built a {}-character refcode {!r}, expected {}".format(
                len(built), built, REFCODE_LENGTH
            )
        )
    return built


# --------------------------------------------------------------------------
# The .ls loadstatus file
# --------------------------------------------------------------------------

#: The loadstatus fields, in order, with the width each one occupies.
#:
#: Eleven of the fourteen widths happen to equal the length of the field's own
#: name, which is a coincidence of how the file was first laid out rather than a
#: rule: ``bibcode`` holds a 19-character refcode, ``Date`` a ``YYYY.MM.DD``,
#: and ``msg`` is empty and sits after the final delimiter. Deriving the widths
#: from the names would be right eleven times and wrong three times, so they are
#: written out.
LS_FIELDS = (
    ("bibcode", 19),
    ("atype", 5),
    ("ack", 3),
    ("Date", 10),
    ("basic", 5),
    ("phot", 4),
    ("diam", 4),
    ("class", 5),
    ("astro", 5),
    ("kinem", 5),
    ("image", 5),
    ("spec", 4),
    ("otype", 5),
    ("msg", 0),
)

#: What loadstatus accepts in the ``atype`` column. Anything else is reported in
#: the .msg file, which the procedure calls out as the usual typo.
LS_ATYPES = frozenset({"T", "O", "E"})

#: The values every transient row carries. Blank fields are filled on load.
LS_DEFAULTS = {"atype": "O", "basic": "Y", "astro": "Y"}


def loadstatus_file(year: int, month: int, kinds: "tuple[str, ...]" = KINDS) -> str:
    """Build the contents of a ``.ls`` loadstatus file.

    Parameters
    ----------
    year : int
        Four-digit year the refcodes belong to.
    month : int
        Month number the refcodes belong to.
    kinds : tuple of str, optional
        Which sources to register, defaulting to all three.

    Returns
    -------
    str
        The whole file, ending in a newline. The heading line is not padded;
        every data row is, and comes to exactly 92 characters.

    Examples
    --------
    >>> print(loadstatus_file(2026, 3, ("GRB",)))  # doctest: +ELLIPSIS
    bibcode|atype|ack|Date|basic|phot|diam|class|astro|kinem|image|spec|otype|msg
    2026GRB03.C...0000.|O    |   |          |Y    |...
    <BLANKLINE>
    """
    atype = LS_DEFAULTS["atype"]
    if atype not in LS_ATYPES:
        raise ValueError("atype {!r} is not one of {}".format(atype, sorted(LS_ATYPES)))

    lines = ["|".join(name for name, _ in LS_FIELDS)]
    for kind in kinds:
        values = dict(LS_DEFAULTS, bibcode=refcode(kind, year, month))
        lines.append(
            "|".join(values.get(name, "").ljust(width) for name, width in LS_FIELDS)
        )
    return "\n".join(lines) + "\n"


def loadstatus_name(year: int, batch: str, kinds: "tuple[str, ...]" = KINDS) -> str:
    """Return the filename a ``.ls`` file goes under.

    The batch letter is load sequence rather than month: the real ``2026a``
    file carries March refcodes.

    Parameters
    ----------
    year : int
        Four-digit year.
    batch : str
        The batch letter, ``a`` for the year's first load.
    kinds : tuple of str, optional
        Which sources the file covers. They appear in the name in order.

    Returns
    -------
    str
        For example ``"2026a.TNS.FRB.GRB.ls"``.

    Examples
    --------
    >>> loadstatus_name(2026, "a")
    '2026a.TNS.FRB.GRB.ls'
    """
    return "{:04d}{}.{}.ls".format(year, batch, ".".join(kinds))


# --------------------------------------------------------------------------
# The Jira ticket
# --------------------------------------------------------------------------

JIRA_SUMMARY = "Add Author Information to the Refcode"


def jira_body(
    year: int, month: int, obtained: str, kinds: "tuple[str, ...]" = KINDS
) -> str:
    """Build the description for the author-information Jira ticket.

    These refcodes are NED-made and have no match at ADS, so the author field
    has to be filled in by hand afterwards. The ticket is the same every month
    apart from the refcodes and the date.

    Parameters
    ----------
    year : int
        Four-digit year the refcodes belong to.
    month : int
        Month number the refcodes belong to.
    obtained : str
        The date the lists were downloaded, as ``YYYY.MM.DD``.
    kinds : tuple of str, optional
        Which sources are covered.

    Returns
    -------
    str
        The ticket body, ready to paste.
    """
    if not isinstance(kinds, tuple):
        kinds = KINDS
    codes = [refcode(kind, year, month) for kind in kinds]

    lines = [
        "The following {} refcode{} author info.".format(
            len(codes), " needs" if len(codes) == 1 else "s need"
        ),
        "",
    ]
    lines.extend(codes)
    lines.extend(
        [
            "",
            "They are NED made and do not have a corresponding bibcode match "
            "at ADS. The following information should be added manually to "
            "them.",
            "",
        ]
    )
    for kind, code in zip(kinds, codes):
        if kind == "TNS":
            what = "IAU-named SNe. Downloaded on {} from {}".format(
                obtained, KIND_URLS[kind]
            )
        else:
            what = "{} list as obtained {} from {}".format(
                KIND_LABELS[kind].rstrip("s"), obtained, KIND_URLS[kind]
            )
        lines.append(code)
        lines.append(what)
        lines.append('author | {{"{}"}}'.format(KIND_AUTHORS[kind]))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"
