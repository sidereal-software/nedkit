"""Command line for preparing a transient load.

The procedure is five steps, and each one is its own command so you can run the
parts that help and do the rest your way:

============  ==========================================================
Command       What it does
============  ==========================================================
``scaffold``  Makes the SIP3 directory tree
``fetch``     Downloads the lists into ``_raw/``
``ptable``    Builds the ``.mod`` files from what ``fetch`` cached
``loadstatus``Writes the ``.ls`` file registering the refcodes
``jira``      Prints the author-information ticket
``prepare``   Runs all five in order
============  ==========================================================

They chain through the batch directory rather than through each other, so any
step can be re-run on its own, and the ones you skip can be done by hand
without the rest noticing. ``refcodes`` is a sixth command that only prints,
for when you want the strings and nothing else.

argparse rather than a nicer library: the team's machines have Python 3.9 and
no way to install packages, so the shipped tool imports nothing that is not in
the standard library.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import os
import sys
from typing import List, Optional, Sequence

from . import layout, ptable, refcodes, sources
from .sources import Transient

#: What ``--only`` accepts, and the order sources are processed in.
KINDS = refcodes.KINDS


# --------------------------------------------------------------------------
# Shared argument handling
# --------------------------------------------------------------------------


def parse_month(text: str) -> "tuple[dt.date, dt.date]":
    """Turn ``YYYY-MM`` into the first and last day of that month.

    Parameters
    ----------
    text : str
        A month, e.g. ``"2026-07"``.

    Returns
    -------
    tuple of datetime.date
        First and last day, both inclusive.

    Raises
    ------
    ValueError
        If the text is not a year and month.
    """
    parts = text.split("-")
    if len(parts) != 2:
        raise ValueError("expected YYYY-MM, got {!r}".format(text))
    year, month = int(parts[0]), int(parts[1])
    last = calendar.monthrange(year, month)[1]
    return dt.date(year, month, 1), dt.date(year, month, last)


def window(args: argparse.Namespace) -> "tuple[dt.date, dt.date]":
    """Work out the date window from the arguments.

    ``--month`` is shorthand for a whole calendar month. Otherwise ``--since``
    and ``--until`` apply, with ``--until`` defaulting to today. The real files
    show a load usually covers much more than a month, which is why ``--since``
    is the primary flag.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    tuple of datetime.date
        Inclusive bounds.

    Raises
    ------
    SystemExit
        If no window was given, or it runs backwards.
    """
    if getattr(args, "month", None):
        return parse_month(args.month)
    if not getattr(args, "since", None):
        raise SystemExit("give --since or --month; there is no sensible default")
    since = dt.date.fromisoformat(args.since)
    until = (
        dt.date.fromisoformat(args.until)
        if getattr(args, "until", None)
        else dt.date.today()
    )
    if until < since:
        raise SystemExit("--until {} is before --since {}".format(until, since))
    return since, until


def stored_window(args: argparse.Namespace, year: int) -> "tuple[dt.date, dt.date]":
    """Get the window, preferring what ``fetch`` recorded for this batch.

    ``ptable`` needs the same window ``fetch`` used. Reading it back means the
    dates are typed once, at the step that actually goes to the network, and a
    later step cannot quietly disagree. An explicit ``--since`` still wins, for
    building a narrower ptable out of a wider fetch.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.
    year : int
        The batch year.

    Returns
    -------
    tuple of datetime.date
        Inclusive bounds.

    Raises
    ------
    SystemExit
        If neither the arguments nor the batch directory supply one.
    """
    if getattr(args, "since", None) or getattr(args, "month", None):
        return window(args)
    found = layout.read_window(args.root, year, args.batch)
    if found is None:
        raise SystemExit(
            "no window recorded for this batch. Run 'fetch' first, or pass "
            "--since / --month."
        )
    return found


def obtained_date(args: argparse.Namespace) -> dt.date:
    """The date the lists were downloaded, which sets the refcode month.

    Not the window. The real ``FRB.2026.03.31.mod`` covers December 2024 to
    September 2025 and loads under ``2026FRB...C...0000.``, where ``C`` is
    March, the month it was prepared. Taking the month from the window would
    produce a refcode that looks right and points at the wrong month.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    datetime.date
        The download date, defaulting to today.
    """
    value = getattr(args, "obtained", None)
    return dt.date.fromisoformat(value) if value else dt.date.today()


def wanted(args: argparse.Namespace) -> "List[str]":
    """Which sources this invocation covers, in a stable order."""
    only = getattr(args, "only", None) or list(KINDS)
    return [kind for kind in KINDS if kind in only]


def kind_list(text: str) -> "List[str]":
    """Parse a comma-separated ``--only`` value.

    Parameters
    ----------
    text : str
        For example ``"frb,grb"``. Case does not matter.

    Returns
    -------
    list of str
        Upper-cased source names.

    Raises
    ------
    argparse.ArgumentTypeError
        If any name is not a known source.
    """
    chosen = [part.strip().upper() for part in text.split(",") if part.strip()]
    # "SNE" is what a person calls the TNS supernova list.
    chosen = ["TNS" if name == "SNE" else name for name in chosen]
    unknown = [name for name in chosen if name not in KINDS]
    if unknown:
        raise argparse.ArgumentTypeError(
            "unknown source {}; pick from sne, frb, grb".format(", ".join(unknown))
        )
    return chosen


def _write(target: str, text: str, force: bool, out) -> "Optional[str]":
    """Write a file unless it is already there.

    Parameters
    ----------
    target : str
        Full path.
    text : str
        Contents.
    force : bool
        Overwrite an existing file.
    out : file-like
        Where to report.

    Returns
    -------
    str or None
        The path if it was written, otherwise ``None``.
    """
    if os.path.exists(target) and not force:
        print("exists, left alone   {}".format(target), file=out)
        return None
    directory = os.path.dirname(target)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(text)
    print("wrote     {}".format(target), file=out)
    return target


# --------------------------------------------------------------------------
# scaffold
# --------------------------------------------------------------------------


def cmd_scaffold(args: argparse.Namespace) -> int:
    """Create the SIP3 directory tree for a batch.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    out = sys.stdout
    year = obtained_date(args).year
    kinds = wanted(args)
    paths = layout.planned(args.root, year, args.batch, kinds)

    if args.dry_run:
        for path in paths:
            print("would create   {}".format(path), file=out)
        return 0

    made = layout.create(paths)
    for path in made:
        print("created   {}".format(path), file=out)
    if not made:
        print("already there   {}".format(paths[0]), file=out)
    return 0


# --------------------------------------------------------------------------
# fetch
# --------------------------------------------------------------------------


def download(
    kind: str, since: dt.date, until: dt.date, tns_csv: "Optional[str]", out=None
) -> str:
    """Get one source's list as text, without parsing it.

    Parameters
    ----------
    kind : str
        ``"TNS"``, ``"FRB"`` or ``"GRB"``.
    since, until : datetime.date
        The window. TNS applies it server-side; Swift publishes one whole
        table and is filtered later.
    tns_csv : str or None
        A hand-downloaded file to read instead of fetching. Either the CSV
        export or a saved results page;
        :func:`~nedtransients.sources.parse_tns` reads both.
    out : file-like, optional
        Where to report a fallback to the second route.

    Returns
    -------
    str
        The response body, verbatim.
    """
    if tns_csv and kind in ("TNS", "FRB"):
        with open(tns_csv, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    if kind == "GRB":
        return sources.fetch(sources.SWIFT_XRT)

    def warn(message):
        print("  ! {}".format(message), file=out if out is not None else sys.stdout)

    return sources.fetch_tns_resilient(
        since, until, frb=(kind == "FRB"), on_fallback=warn
    )


def cmd_fetch(args: argparse.Namespace) -> int:
    """Download the source lists into the batch's ``_raw`` directory.

    The responses are stored exactly as they arrived, so a re-run costs
    nothing, ``ptable`` can work offline, and anything surprising downstream
    can be traced back to what the server actually said.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    out = sys.stdout
    since, until = window(args)
    obtained = obtained_date(args)
    year = obtained.year
    kinds = wanted(args)
    raw = layout.raw_dir(args.root, year, args.batch)

    print("window    {} .. {}".format(since, until), file=out)
    print("into      {}".format(raw), file=out)
    print("", file=out)

    if args.dry_run:
        for kind in kinds:
            where = (
                sources.SWIFT_XRT
                if kind == "GRB"
                else sources.tns_url(since, until, frb=(kind == "FRB"))
            )
            print("would fetch  {:<4s} {}".format(kind, where), file=out)
        return 0

    if not os.path.isdir(raw):
        os.makedirs(raw)

    for kind in kinds:
        existing = layout.cached(args.root, year, args.batch, kind)
        if existing and not args.force:
            print("exists, left alone   {}".format(existing), file=out)
            continue
        text = download(kind, since, until, args.tns_csv, out)
        target = os.path.join(raw, layout.raw_name(kind, text))
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
        # Count what parses, not what has a newline in it: the fallback route
        # returns a web page, whose line count means nothing.
        if kind == "GRB":
            found = len(sources.parse_swift(text))
        else:
            found = len(sources.parse_tns(text, kind))
        print(
            "fetched   {:<4s} {:5d} objects -> {}".format(kind, found, target),
            file=out,
        )

    layout.write_window(args.root, year, args.batch, since, until)
    print("", file=out)
    print("window recorded; 'ptable' will use it without being told.", file=out)
    return 0


# --------------------------------------------------------------------------
# ptable
# --------------------------------------------------------------------------


def load_cached(
    args: argparse.Namespace, year: int, kind: str, since: dt.date, until: dt.date
) -> "Optional[List[Transient]]":
    """Parse one source's cached response into records.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.
    year : int
        The batch year.
    kind : str
        Which source.
    since, until : datetime.date
        The window to filter to.

    Returns
    -------
    list of Transient, or None
        ``None`` if nothing has been fetched for this source yet.
    """
    path = layout.cached(args.root, year, args.batch, kind)
    if path is None:
        return None
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if kind == "GRB":
        records = sources.parse_swift(text)
    else:
        records = sources.parse_tns(text, kind)
    return sources.in_window(records, since, until)


def report_clusters(records: "Sequence[Transient]", out) -> None:
    """Print the id runs in a candidate list, if there are any.

    Grouping only. See :class:`nedtransients.sources.Cluster` for why this does
    not filter anything.

    Parameters
    ----------
    records : sequence of Transient
        The candidates.
    out : file-like
        Where to write.
    """
    found = sources.clusters(records)
    if not found:
        return
    covered = sum(cluster.size for cluster in found)
    print(
        "\n  {} of these arrived in {} consecutive-id runs, which is what a bulk\n"
        "  catalogue upload looks like. All of them are in the ptable; delete the\n"
        "  rows you do not want.\n".format(covered, len(found)),
        file=out,
    )
    for cluster in found:
        dates = [record.discovered for record in cluster.members]
        print(
            "    ids {}-{}  {:3d} objects  {:<10s} {} .. {}".format(
                cluster.first,
                cluster.last,
                cluster.size,
                cluster.group,
                min(dates),
                max(dates),
            ),
            file=out,
        )
    print("", file=out)


def cmd_ptable(args: argparse.Namespace) -> int:
    """Build the ``.mod`` ptable files from the cached responses.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    out = sys.stdout
    obtained = obtained_date(args)
    year, month = obtained.year, obtained.month
    since, until = stored_window(args, year)
    kinds = wanted(args)
    base = layout.batch_dir(args.root, year, args.batch)

    print("window    {} .. {}".format(since, until), file=out)
    print("prepared  {} (sets the refcode month)".format(obtained), file=out)
    print("", file=out)

    already = layout.existing_names(args.root, year) if os.path.isdir(args.root) else []

    for kind in kinds:
        records = load_cached(args, year, kind, since, until)
        if records is None:
            print(
                "{}: nothing fetched yet. Run 'fetch --only {}' first.".format(
                    kind, kind.lower()
                ),
                file=out,
            )
            continue

        fresh = sources.without(records, already)
        skipped = len(records) - len(fresh)
        note = " ({} already loaded)".format(skipped) if skipped else ""
        print("{}: {} candidates{}".format(kind, len(fresh), note), file=out)

        if not fresh:
            print(
                "  nothing in the window. For FRBs that is normal; the procedure\n"
                "  says to check the time frame before assuming a problem.\n",
                file=out,
            )
            continue

        report_clusters(fresh, out)

        if kind not in ptable.CONFIRMED:
            print(
                "  NOTE: the {} ptable layout is inferred, not copied from a real\n"
                "  loaded file. Check it against one before loading.".format(kind),
                file=out,
            )

        text = ptable.render(kind, refcodes.refcode(kind, year, month), fresh)
        target = os.path.join(base, kind, ptable.name_for(kind, obtained))
        if args.dry_run:
            print("  would write {}\n".format(target), file=out)
            print(text, file=out)
        else:
            _write(target, text, args.force, out)
    return 0


# --------------------------------------------------------------------------
# loadstatus
# --------------------------------------------------------------------------


def cmd_loadstatus(args: argparse.Namespace) -> int:
    """Write the ``.ls`` file registering this batch's NED-only refcodes.

    Which sources get a refcode is read off the batch directory: a source with
    no ptable has nothing to load, and registering a refcode for it would point
    the reference database at an empty load and then ask for a Jira ticket
    adding author information to it.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    out = sys.stdout
    obtained = obtained_date(args)
    year, month = obtained.year, obtained.month

    built = layout.ptables(args.root, year, args.batch)
    # --only narrows what gets registered; it does not add a source that has
    # no ptable. A refcode with nothing behind it points the reference database
    # at an empty load and then asks for a Jira ticket giving it an author.
    kinds = [kind for kind in wanted(args) if kind in built]

    absent = [kind for kind in wanted(args) if kind not in built]
    for kind in absent:
        print(
            "{}: no ptable in this batch, so no refcode. Run 'ptable' first.".format(
                kind
            ),
            file=out,
        )
    if not kinds:
        print("Nothing to register.", file=out)
        return 0

    text = refcodes.loadstatus_file(year, month, tuple(kinds))
    target = os.path.join(
        layout.batch_dir(args.root, year, args.batch),
        refcodes.loadstatus_name(year, args.batch, tuple(kinds)),
    )
    print("registering  {}".format(", ".join(kinds)), file=out)
    if args.dry_run:
        print("would write {}\n".format(target), file=out)
        print(text, file=out)
    else:
        _write(target, text, args.force, out)
    return 0


# --------------------------------------------------------------------------
# jira and refcodes
# --------------------------------------------------------------------------


def batch_kinds(args: argparse.Namespace, year: int) -> "List[str]":
    """Which sources to name, from ``--only`` or from what the batch built."""
    if getattr(args, "only", None):
        return wanted(args)
    if getattr(args, "root", None) and getattr(args, "batch", None):
        found = layout.ptables(args.root, year, args.batch)
        if found:
            return found
    return list(KINDS)


def cmd_jira(args: argparse.Namespace) -> int:
    """Print the author-information ticket.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    obtained = obtained_date(args)
    year, month = obtained.year, obtained.month
    kinds = tuple(batch_kinds(args, year))
    print(refcodes.JIRA_SUMMARY)
    print()
    print(refcodes.jira_body(year, month, "{:%Y.%m.%d}".format(obtained), kinds))
    return 0


def cmd_refcodes(args: argparse.Namespace) -> int:
    """Print the NED-only refcodes for a month and nothing else.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        Process exit status.
    """
    obtained = obtained_date(args)
    for kind in wanted(args):
        print(
            "{:<4s} {}".format(
                kind, refcodes.refcode(kind, obtained.year, obtained.month)
            )
        )
    return 0


# --------------------------------------------------------------------------
# prepare, which is the five steps in order
# --------------------------------------------------------------------------

#: The chain ``prepare`` runs, in order.
STEPS = (
    ("scaffold", cmd_scaffold),
    ("fetch", cmd_fetch),
    ("ptable", cmd_ptable),
    ("loadstatus", cmd_loadstatus),
    ("jira", cmd_jira),
)


def cmd_prepare(args: argparse.Namespace) -> int:
    """Run every step in order.

    Each step is the same function the standalone command calls, so there is
    one implementation of each and no chance of the chain drifting from the
    pieces.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments.

    Returns
    -------
    int
        The first non-zero status, or zero.
    """
    out = sys.stdout
    print(
        "batch     {}".format(
            layout.batch_dir(args.root, obtained_date(args).year, args.batch)
        ),
        file=out,
    )
    print("sources   {}".format(", ".join(wanted(args))), file=out)

    for name, handler in STEPS:
        print("", file=out)
        print("=== {} ===".format(name), file=out)
        status = handler(args)
        if status:
            return status

    print("", file=out)
    print("Next, by hand: loadstatus, then ptbl.py and lbl.py, then the", file=out)
    print("SecondPassOfChecking steps. Nothing here has loaded anything.", file=out)
    return 0


# --------------------------------------------------------------------------
# Wiring
# --------------------------------------------------------------------------


def add_batch(parser: argparse.ArgumentParser) -> None:
    """Add the arguments naming which batch to work on."""
    parser.add_argument("--root", required=True, help="the data.tables directory")
    parser.add_argument(
        "--batch", required=True, help="batch letter, 'a' for the year's first load"
    )


def add_window(parser: argparse.ArgumentParser, required: bool) -> None:
    """Add the date-range arguments.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The subcommand to add them to.
    required : bool
        Whether a window has to be given. ``ptable`` reads it back from what
        ``fetch`` recorded, so there it is optional.
    """
    note = "" if required else " (default: whatever 'fetch' used)"
    parser.add_argument("--since", help="window start, YYYY-MM-DD" + note)
    parser.add_argument("--until", help="window end, YYYY-MM-DD, default today")
    parser.add_argument("--month", help="shorthand for a whole month, YYYY-MM")


def add_common(parser: argparse.ArgumentParser) -> None:
    """Add the arguments every writing step shares."""
    parser.add_argument(
        "--only", type=kind_list, help="comma-separated subset of sne,frb,grb"
    )
    parser.add_argument(
        "--obtained",
        help="download date, YYYY-MM-DD, default today. Sets the refcode month.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print everything and write nothing"
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite files that already exist"
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser.

    Returns
    -------
    argparse.ArgumentParser
        With every subcommand attached.
    """
    parser = argparse.ArgumentParser(
        prog="ned-transients",
        description=(
            "Prepare a SNe/FRB/GRB load. Each step is its own command; "
            "'prepare' runs them all. Loads nothing and chooses nothing."
        ),
        epilog=(
            "The steps chain through the batch directory, so any one can be "
            "re-run on its own and any one can be skipped and done by hand."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    step = sub.add_parser("scaffold", help="create the SIP3 directory tree")
    add_batch(step)
    add_common(step)
    step.set_defaults(handler=cmd_scaffold)

    step = sub.add_parser("fetch", help="download the lists into _raw/")
    add_batch(step)
    add_window(step, required=True)
    add_common(step)
    step.add_argument("--tns-csv", help="use a hand-downloaded TNS CSV instead")
    step.set_defaults(handler=cmd_fetch)

    step = sub.add_parser("ptable", help="build the .mod files from _raw/")
    add_batch(step)
    add_window(step, required=False)
    add_common(step)
    step.set_defaults(handler=cmd_ptable)

    step = sub.add_parser("loadstatus", help="write the .ls file")
    add_batch(step)
    add_common(step)
    step.set_defaults(handler=cmd_loadstatus)

    step = sub.add_parser("jira", help="print the author-information ticket")
    step.add_argument("--root", help="the data.tables directory, to read the batch")
    step.add_argument("--batch", help="batch letter")
    add_common(step)
    step.set_defaults(handler=cmd_jira)

    step = sub.add_parser("refcodes", help="print the NED-only refcodes")
    add_common(step)
    step.set_defaults(handler=cmd_refcodes)

    step = sub.add_parser("prepare", help="run every step in order")
    add_batch(step)
    add_window(step, required=True)
    add_common(step)
    step.add_argument("--tns-csv", help="use a hand-downloaded TNS CSV instead")
    step.set_defaults(handler=cmd_prepare)

    return parser


def main(argv: "Optional[Sequence[str]]" = None) -> int:
    """Entry point.

    Parameters
    ----------
    argv : sequence of str, optional
        Arguments, defaulting to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit status.
    """
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
