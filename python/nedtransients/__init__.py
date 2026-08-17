"""Prepare the monthly SNe, FRB and GRB load for NED.

Fetches the lists from TNS and Swift XRT, and writes the files the procedure
otherwise asks someone to build by copying last year's: the ``.ls`` loadstatus
file that registers the NED-only refcodes, a ``.mod`` ptable per source, the
SIP3 directory tree, and the Jira ticket body.

Each of those is its own command (``scaffold``, ``fetch``, ``ptable``,
``loadstatus``, ``jira``), with ``prepare`` running the five in order. They
chain through the batch directory rather than through each other, so any step
can be re-run alone and any step can be skipped and done by hand. See
:mod:`nedtransients.__main__`.

It stops there. Nothing here runs ``loadstatus``, ``ptbl.py``, ``lbl.py`` or the
second-pass checks, and nothing here decides which objects belong in NED. What
it removes is the copying, which is the part where a human adds nothing except
the chance of a typo.

Standard library only, and Python 3.9, because that is what the NED team's
machines have.
"""

__all__ = ["coords", "layout", "ptable", "refcodes", "sources"]

__version__ = "0.1.0"
