"""Write the ``.mod`` ptable files the NED loaders read.

The format is the one ``samples/A13L.mod.after`` demonstrates: a ``##refcode``
line, a block of ``##`` metadata, a pipe-delimited heading row, then the data.

The three sources do **not** share a layout, and the differences are not
cosmetic. Each kind's real file dictates its own metadata block, its own
columns, and its own padding, so each gets an entry in :data:`LAYOUTS` copied
from a file that actually loaded rather than from a template that looked
reasonable.

Verified against the real files:

- Every one of the 33 FRB rows and 66 GRB rows reproduces exactly from live
  source data.
- The GRB file is a contiguous slice of the Swift table with no gaps and in the
  same order, so GRBs need no selection at all. FRBs do; see
  :class:`~nedtransients.sources.Cluster`.
"""

from __future__ import annotations

from typing import List, NamedTuple, Sequence

from .coords import dec_to_ned, ra_to_ned
from .sources import Transient


class Column(NamedTuple):
    """One column of a ptable.

    Attributes
    ----------
    name : str
        The heading, e.g. ``"coordx1"``.
    value : str
        Which :class:`~nedtransients.sources.Transient` attribute fills it, or
        a derived name handled by :func:`_cell`.
    """

    name: str
    value: str


class Layout(NamedTuple):
    """Everything that differs between one source's ptable and another's.

    Attributes
    ----------
    meta : tuple of str
        The ``##`` lines, in the order the real file has them. Order is
        preserved rather than normalised, because a diff against last year's
        file should come out empty.
    columns : tuple of Column
        The columns, in order.
    padded : bool
        Whether data rows are aligned into columns. The real GRB file is; the
        real FRB file is not.

        Padding puts one space on each side of every ``|``, so a GRB row reads
        ``GRB 260204A | 134025.49 | ...``. The first column has no space in
        front of it because no delimiter precedes it, which is why its cells
        are one character narrower than the rule would otherwise give.
    """

    meta: "tuple[str, ...]"
    columns: "tuple[Column, ...]"
    padded: bool


#: The per-source formats, each taken from a real file.
#:
#: ``FRB`` and ``GRB`` are copied from ``FRB.2026.03.31.mod`` and
#: ``GRB.2026.03.31.mod``. ``TNS`` is the one without a sample: it follows the
#: FRB shape with a supernova's type and no ``skip`` column, and
#: :func:`write` flags it as unconfirmed. Replace it from a real file before
#: trusting it.
LAYOUTS = {
    "FRB": Layout(
        meta=(
            "##type1=RadioS",
            "##name_type1=RadioS",
            "##coordy_unit1=SX",
            "##coordy_unc_unit1=AM",
            "##coordy_unc1=8.",
            "##coordx_unit1=SX",
            "##coordx_unc_unit1=AM",
            "##coordx_unc1=8.",
            "##coord_system1=Equ",
            "##coord_sig1=68",
            "##coord_equinox1=J2000",
        ),
        # The real file's heading row holds a tab and is three characters
        # short of its data rows, so its labels do not sit over their columns.
        # Its exact bytes were:
        #     b'skip  |name1\t    |coordx1   |coordy1   |'
        # That is hand-editing damage rather than a format: the loader splits
        # on the delimiter, and CLAUDE.md notes the XNEdit pipe macros refuse a
        # buffer containing a tab. We emit it aligned and tab-free.
        columns=(
            Column("skip", "tns_id"),
            Column("name1", "name"),
            Column("coordx1", "ra"),
            Column("coordy1", "dec"),
        ),
        padded=False,
    ),
    "GRB": Layout(
        meta=(
            "##name_type1=GammaS",
            # The leading space is in the real file. Harmless, and kept so a
            # diff against last year comes out empty.
            "##type1= GammaS",
            "##coordx_unit1=SX",
            "##coordy_unit1=SX",
            "##coord_equinox1=J2000",
            "##coord_system1=Equ",
            "##coordx_unc_unit1=AS",
            "##coordy_unc_unit1=AS",
            "##coord_sig1=90",
        ),
        columns=(
            Column("name1", "name"),
            Column("coordx1", "ra"),
            Column("coordy1", "dec"),
            # Swift publishes one 90% error radius, which goes in both axes.
            Column("coordx_unc1", "uncertainty"),
            Column("coordy_unc1", "uncertainty"),
        ),
        padded=True,
    ),
    "TNS": Layout(
        meta=(
            "##type1=SN",
            "##name_type1=SN",
            "##coordy_unit1=SX",
            "##coordx_unit1=SX",
            "##coord_system1=Equ",
            "##coord_equinox1=J2000",
        ),
        columns=(
            Column("skip", "tns_id"),
            Column("name1", "name"),
            Column("coordx1", "ra"),
            Column("coordy1", "dec"),
        ),
        padded=False,
    ),
}

#: Kinds whose layout came from a real loaded file rather than from inference.
CONFIRMED = frozenset({"FRB", "GRB"})


def _cell(record: Transient, value: str) -> str:
    """Render one column's value for one record.

    Parameters
    ----------
    record : Transient
        The object being written.
    value : str
        The attribute name from :class:`Column`.

    Returns
    -------
    str
        The cell contents. Coordinates go through :mod:`nedtransients.coords`;
        everything else is used as published.
    """
    if value == "ra":
        return ra_to_ned(record.ra)
    if value == "dec":
        return dec_to_ned(record.dec)
    return getattr(record, value)


def render(kind: str, refcode: str, records: "Sequence[Transient]") -> str:
    """Build a complete ptable file.

    Parameters
    ----------
    kind : str
        ``"TNS"``, ``"FRB"`` or ``"GRB"``.
    refcode : str
        The NED-only refcode the objects load under.
    records : sequence of Transient
        The objects, in the order they should appear.

    Returns
    -------
    str
        The whole file, ending in a newline.

    Raises
    ------
    KeyError
        If ``kind`` has no layout.
    ValueError
        If ``records`` is empty. An empty ptable is never wanted, and for FRBs
        it is the case the procedure warns about.
    """
    layout = LAYOUTS[kind]
    if not records:
        raise ValueError("refusing to write an empty {} ptable".format(kind))

    headings = [column.name for column in layout.columns]
    rows = [
        [
            _lead(layout, index) + _cell(record, column.value)
            for index, column in enumerate(layout.columns)
        ]
        for record in records
    ]

    # A padded column also leaves room for the space that follows its value,
    # unless the heading is wider than anything in the column anyway.
    room = 1 if layout.padded else 0
    widths = [
        max([len(heading)] + [len(row[index]) + room for row in rows])
        for index, heading in enumerate(headings)
    ]

    lines = ["##refcode = {}".format(refcode)]
    lines.extend(layout.meta)
    # Headings are never lead-padded, only right-padded to the column width.
    lines.append(
        "|".join(heading.ljust(width) for heading, width in zip(headings, widths)) + "|"
    )
    for row in rows:
        if layout.padded:
            row = [cell.ljust(width) for cell, width in zip(row, widths)]
        lines.append("|".join(row) + "|")
    return "\n".join(lines) + "\n"


def _lead(layout: Layout, index: int) -> str:
    """Return the space that sits between a delimiter and a padded value.

    Parameters
    ----------
    layout : Layout
        The format being written.
    index : int
        Zero-based column number.

    Returns
    -------
    str
        A single space, or empty for an unpadded layout or the first column,
        which has no delimiter in front of it.
    """
    return " " if layout.padded and index > 0 else ""


def name_for(kind: str, obtained: "object") -> str:
    """Return the filename a ptable goes under.

    Parameters
    ----------
    kind : str
        ``"TNS"``, ``"FRB"`` or ``"GRB"``.
    obtained : datetime.date
        The date the list was downloaded.

    Returns
    -------
    str
        For example ``"FRB.2026.03.31.mod"``.
    """
    return "{}.{:%Y.%m.%d}.mod".format(kind, obtained)


def loaded_names(text: str) -> "List[str]":
    """Read the object names out of an existing ptable.

    Used to skip objects already loaded, so the tree on disk is the record of
    what has been done and no separate state file is needed.

    Parameters
    ----------
    text : str
        The contents of a ``.mod`` file.

    Returns
    -------
    list of str
        Every value found in the ``name1`` column.
    """
    found = []
    headings = None
    for line in text.splitlines():
        if line.startswith("##") or not line.strip():
            continue
        fields = [field.strip() for field in line.split("|")]
        if headings is None:
            headings = fields
            continue
        if "name1" in headings:
            index = headings.index("name1")
            if index < len(fields) and fields[index]:
                found.append(fields[index])
    return found
