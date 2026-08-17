"""The SIP3 directory tree a batch gets prepared in.

Mirrors what the procedure says to build by hand::

    YYYY/SNe+FRB+GRB/SNe+FRB+GRB-<batch>-SIP3/
        flt/
        lbl/
        _raw/
        TNS/  FRB/  GRB/

``flt`` and ``lbl`` are what the second-pass checks read. ``_raw`` is ours: it
holds each upstream response exactly as it arrived, so a re-run costs nothing
and anything surprising in the output can be traced back to what the server
actually said.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence

#: Subdirectories every batch gets, whichever sources are being loaded.
FIXED = ("flt", "lbl", "_raw")

#: Base name of each source's cached response, without an extension.
#:
#: The extension records which of the two TNS routes answered, because ``_raw``
#: is there to be read by a person and a file called ``.csv`` holding a web
#: page is a small lie that costs someone ten minutes.
RAW_STEMS = {
    "TNS": "tns-sne",
    "FRB": "tns-frb",
    "GRB": "swift-xrt",
}

#: Extensions a cached response may carry, in the order they are looked for.
RAW_SUFFIXES = (".csv", ".html", ".txt")


def raw_name(kind: str, text: str) -> str:
    """Return the filename a freshly fetched response should be saved under.

    Parameters
    ----------
    kind : str
        ``"TNS"``, ``"FRB"`` or ``"GRB"``.
    text : str
        The response, so the extension can describe it.

    Returns
    -------
    str
        For example ``"tns-frb.csv"`` or, when the fallback route answered,
        ``"tns-frb.html"``.
    """
    if kind == "GRB":
        return RAW_STEMS[kind] + ".txt"
    return RAW_STEMS[kind] + (".html" if "cell-name" in text else ".csv")


#: Records the window ``fetch`` used, next to the responses it describes.
#:
#: The steps run as separate commands, and ``ptable`` needs the same window
#: ``fetch`` did. TNS applies the window server-side so its cached CSV is
#: already trimmed, but Swift publishes one undated table and the filter has to
#: happen locally. Without this, running ``ptable`` after ``fetch`` would need
#: the dates typed again and would silently use the wrong ones if they were
#: mistyped.
RAW_WINDOW = "window.txt"


def raw_dir(root: str, year: int, batch: str) -> str:
    """Return the directory holding a batch's cached responses."""
    return os.path.join(batch_dir(root, year, batch), "_raw")


def write_window(root: str, year: int, batch: str, since, until) -> str:
    """Record the window a fetch covered.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year.
    batch : str
        Batch letter.
    since, until : datetime.date
        Inclusive bounds.

    Returns
    -------
    str
        The path written.
    """
    path = os.path.join(raw_dir(root, year, batch), RAW_WINDOW)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{}\n{}\n".format(since.isoformat(), until.isoformat()))
    return path


def read_window(root: str, year: int, batch: str):
    """Read back the window a fetch covered.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year.
    batch : str
        Batch letter.

    Returns
    -------
    tuple of datetime.date, or None
        The bounds, or ``None`` if no fetch has run for this batch.
    """
    import datetime as dt

    path = os.path.join(raw_dir(root, year, batch), RAW_WINDOW)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]
    if len(lines) != 2:
        return None
    return dt.date.fromisoformat(lines[0]), dt.date.fromisoformat(lines[1])


def cached(root: str, year: int, batch: str, kind: str) -> "Optional[str]":
    """Return the path of a cached response, or ``None`` if it is not there.

    Looks under every extension, since which one is present records which
    route answered when the batch was fetched.
    """
    directory = raw_dir(root, year, batch)
    for suffix in RAW_SUFFIXES:
        path = os.path.join(directory, RAW_STEMS[kind] + suffix)
        if os.path.isfile(path):
            return path
    return None


def ptables(root: str, year: int, batch: str) -> "List[str]":
    """Return the sources a batch has already built a ptable for.

    This is how ``loadstatus`` knows which refcodes to register without being
    told: a source with no ptable has nothing to load, and registering a
    refcode for it would point the reference database at an empty load.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year.
    batch : str
        Batch letter.

    Returns
    -------
    list of str
        Source names, in ``KIND`` order.
    """
    base = batch_dir(root, year, batch)
    found = []
    for kind in ("TNS", "FRB", "GRB"):
        directory = os.path.join(base, kind)
        if os.path.isdir(directory) and any(
            name.endswith(".mod") for name in os.listdir(directory)
        ):
            found.append(kind)
    return found


def batch_dir(root: str, year: int, batch: str) -> str:
    """Return the path of a batch's SIP3 directory.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year.
    batch : str
        Batch letter, ``a`` for the year's first load.

    Returns
    -------
    str
        The full path. Nothing is created.

    Examples
    --------
    >>> batch_dir("/data.tables", 2026, "a")
    '/data.tables/2026/SNe+FRB+GRB/SNe+FRB+GRB-a-SIP3'
    """
    return os.path.join(
        root,
        "{:04d}".format(year),
        "SNe+FRB+GRB",
        "SNe+FRB+GRB-{}-SIP3".format(batch),
    )


def planned(root: str, year: int, batch: str, kinds: "Sequence[str]") -> "List[str]":
    """List every directory a batch needs, in creation order.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year.
    batch : str
        Batch letter.
    kinds : sequence of str
        Which sources are being loaded. Each gets its own subdirectory.

    Returns
    -------
    list of str
        Full paths, parents before children.
    """
    base = batch_dir(root, year, batch)
    return [base] + [os.path.join(base, name) for name in list(FIXED) + list(kinds)]


def create(paths: "Sequence[str]") -> "List[str]":
    """Create directories, skipping any that already exist.

    Parameters
    ----------
    paths : sequence of str
        Full paths, parents first.

    Returns
    -------
    list of str
        Only the paths that were actually created, so the caller can report
        the difference between a fresh batch and a resumed one.
    """
    made = []
    for path in paths:
        if not os.path.isdir(path):
            os.makedirs(path)
            made.append(path)
    return made


def existing_names(root: str, year: int) -> "List[str]":
    """Collect object names from every ptable already under a year.

    This is how a re-run avoids reloading what is already done. The tree is the
    record, so there is no separate state file to keep in step with it.

    Parameters
    ----------
    root : str
        The ``data.tables`` directory.
    year : int
        Four-digit year to search under.

    Returns
    -------
    list of str
        Every name found, with duplicates left in.
    """
    from .ptable import loaded_names

    found = []
    top = os.path.join(root, "{:04d}".format(year))
    for directory, _, files in os.walk(top):
        for name in files:
            if not name.endswith(".mod"):
                continue
            path = os.path.join(directory, name)
            with open(path, encoding="utf-8", errors="replace") as handle:
                found.extend(loaded_names(handle.read()))
    return found
