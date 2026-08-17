"""Sexagesimal coordinates in the form NED's ptable files want.

The conversion is smaller than it looks. Both upstream sources already publish
positions in sexagesimal, so there is no arithmetic to do: strip the colons,
make the declination's sign explicit, and leave every digit alone.

That last part matters. Checking the real ``FRB.2026.03.31.mod`` and
``GRB.2026.03.31.mod`` against their sources, all 97 rows carry exactly the
precision the source published, which is three decimals of right ascension from
TNS and two from Swift. Rounding to a fixed number of places would have been the
obvious guess and would have been wrong for one of the two files whichever
number was picked.
"""

from __future__ import annotations

#: What a sexagesimal field may contain once the colons are gone.
_DIGITS = "0123456789."


def _strip(value: str) -> str:
    """Remove the colons and surrounding blanks from a sexagesimal field.

    Parameters
    ----------
    value : str
        A field such as ``"20:31:06.360"``.

    Returns
    -------
    str
        The same field with colons and blanks removed.
    """
    return value.strip().replace(":", "")


def ra_to_ned(value: str) -> str:
    """Convert a right ascension to NED's compact form.

    Parameters
    ----------
    value : str
        Sexagesimal right ascension, ``HH:MM:SS.sss``. TNS and Swift both
        publish this, at different precisions.

    Returns
    -------
    str
        The same value without colons, e.g. ``"203106.360"``.

    Raises
    ------
    ValueError
        If the input holds anything other than digits, colons and a decimal
        point. A right ascension is never signed, so a leading ``+`` or ``-``
        means the declination and the right ascension have been swapped.

    Examples
    --------
    >>> ra_to_ned("20:31:06.360")
    '203106.360'
    >>> ra_to_ned("13:40:25.49")
    '134025.49'
    """
    stripped = _strip(value)
    if not stripped or any(character not in _DIGITS for character in stripped):
        raise ValueError("not a right ascension: {!r}".format(value))
    return stripped


def dec_to_ned(value: str) -> str:
    """Convert a declination to NED's compact form, with an explicit sign.

    A declination between 0 and -1 degrees is the case worth care: the degrees
    field is ``00`` and the sign is the only thing distinguishing north from
    south. Sources are not consistent about writing ``+`` on a positive value,
    so this adds one when it is missing rather than passing the input through.

    Parameters
    ----------
    value : str
        Sexagesimal declination, ``[+-]DD:MM:SS.ss``.

    Returns
    -------
    str
        The same value without colons and always signed, e.g. ``"+535056.40"``.

    Raises
    ------
    ValueError
        If the input is not a signed or unsigned run of digits and colons.

    Examples
    --------
    >>> dec_to_ned("+53:50:56.40")
    '+535056.40'
    >>> dec_to_ned("-00:21:48.71")
    '-002148.71'
    >>> dec_to_ned("01:55:50.7")
    '+015550.7'
    """
    stripped = _strip(value)
    sign = "+"
    if stripped[:1] in "+-":
        sign, stripped = stripped[0], stripped[1:]
    if not stripped or any(character not in _DIGITS for character in stripped):
        raise ValueError("not a declination: {!r}".format(value))
    return sign + stripped
