"""Re-derive the character tables rather than take them on trust.

Two commands carry one. ``normalize-characters.nm`` maps 73 punctuation
characters and ``fold-letters-to-ascii.nm`` maps 240 letters, which is more data
than anyone re-reads by eye when one line of it changes. So the rules the tables
were built from are written out here and checked against :mod:`unicodedata`: a
mistyped key byte, a letter left out of a range, a fold that drops a capital to
lower case, each one fails here rather than ships.

Nothing below reads a replacement out of a macro and then agrees with it. The
Greek readings, the nineteen letters Unicode cannot decompose and the ten with
no one-letter answer are the only hand-written answers in the whole table, and
each is listed once, here, as the thing the macro is measured against.

``tests/fixtures/fold-letters-to-ascii/`` is the other half of the job: this
settles what the table says, those settle that the editor applies it.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

from nedkit.chartable import (
    TABLE_ARRAYS,
    character_tables,
    label_for,
    parse_character_table,
    unescape,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FOLD = REPO_ROOT / "macros" / "commands" / "fold-letters-to-ascii.nm"

#: One ``array["key"] = "value"`` line, with the array's name kept.
#: :mod:`nedkit.chartable` throws that name away, because the generated docs
#: render both arrays the same way. These tests cannot: ``grk[]`` carries a rule
#: ``fix[]`` does not, so the two have to be told apart. The first test below
#: ties this pattern back to chartable's so they cannot drift.
ENTRY_RE = re.compile(
    r'^(%s)\["([^"]*)"\]\s*=\s*"(.*)"\s*$' % "|".join(TABLE_ARRAYS), re.MULTILINE
)

#: The Latin ranges Fold Letters to ASCII claims, end inclusive: Latin-1
#: Supplement and Latin Extended-A.
LATIN_RANGES = ((0x00C0, 0x00FF), (0x0100, 0x017F))

#: Every Greek letter, plus the micro sign. U+03A2 is unassigned, so the
#: capitals are not one unbroken run.
GREEK_CODE_POINTS = frozenset(
    [cp for cp in range(0x0391, 0x03AA) if cp != 0x03A2]
    + list(range(0x03B1, 0x03CA))
    + [0x00B5]
)

#: The letters with no canonical decomposition, so NFD has no answer for them
#: and a human had to pick one. Which letters belong on this list is not a
#: matter of taste, and it is re-derived below; only the answers are written
#: down.
UNDECOMPOSABLE = {
    "Ð": "D",  # LATIN CAPITAL LETTER ETH
    "ð": "d",  # LATIN SMALL LETTER ETH
    "Ø": "O",  # LATIN CAPITAL LETTER O WITH STROKE
    "ø": "o",  # LATIN SMALL LETTER O WITH STROKE
    "Đ": "D",  # LATIN CAPITAL LETTER D WITH STROKE
    "đ": "d",  # LATIN SMALL LETTER D WITH STROKE
    "Ħ": "H",  # LATIN CAPITAL LETTER H WITH STROKE
    "ħ": "h",  # LATIN SMALL LETTER H WITH STROKE
    "ı": "i",  # LATIN SMALL LETTER DOTLESS I
    "ĸ": "k",  # LATIN SMALL LETTER KRA
    "Ł": "L",  # LATIN CAPITAL LETTER L WITH STROKE
    "ł": "l",  # LATIN SMALL LETTER L WITH STROKE
    "Ŀ": "L",  # LATIN CAPITAL LETTER L WITH MIDDLE DOT
    "ŀ": "l",  # LATIN SMALL LETTER L WITH MIDDLE DOT
    "Ŋ": "N",  # LATIN CAPITAL LETTER ENG
    "ŋ": "n",  # LATIN SMALL LETTER ENG
    "Ŧ": "T",  # LATIN CAPITAL LETTER T WITH STROKE
    "ŧ": "t",  # LATIN SMALL LETTER T WITH STROKE
    "ſ": "s",  # LATIN SMALL LETTER LONG S
}

#: The ten letters with no one-letter answer at all. The only entries in either
#: table that make a line longer, which is why they are named and not counted.
EXPANSIONS = {
    "Æ": "AE",  # LATIN CAPITAL LETTER AE
    "æ": "ae",  # LATIN SMALL LETTER AE
    "ß": "ss",  # LATIN SMALL LETTER SHARP S
    "Þ": "TH",  # LATIN CAPITAL LETTER THORN
    "þ": "th",  # LATIN SMALL LETTER THORN
    "Œ": "OE",  # LATIN CAPITAL LIGATURE OE
    "œ": "oe",  # LATIN SMALL LIGATURE OE
    "Ĳ": "IJ",  # LATIN CAPITAL LIGATURE IJ
    "ĳ": "ij",  # LATIN SMALL LIGATURE IJ
    "ŉ": "'n",  # LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
}

#: The Greek readings, written out once. First letter of the letter's English
#: name, except where that letter is already taken: phi takes f and psi takes y
#: because pi holds p, chi takes c, and mu takes u rather than m so that
#: ``24 µm`` does not become ``24 mm``.
GREEK = {
    "Α": "A",
    "α": "a",  # alpha
    "Β": "B",
    "β": "b",  # beta
    "Γ": "G",
    "γ": "g",  # gamma
    "Δ": "D",
    "δ": "d",  # delta
    "Ε": "E",
    "ε": "e",  # epsilon
    "Ζ": "Z",
    "ζ": "z",  # zeta
    "Η": "E",
    "η": "e",  # eta
    "Θ": "T",
    "θ": "t",  # theta
    "Ι": "I",
    "ι": "i",  # iota
    "Κ": "K",
    "κ": "k",  # kappa
    "Λ": "L",
    "λ": "l",  # lambda
    "Μ": "U",
    "μ": "u",  # mu
    "Ν": "N",
    "ν": "n",  # nu
    "Ξ": "X",
    "ξ": "x",  # xi
    "Ο": "O",
    "ο": "o",  # omicron
    "Π": "P",
    "π": "p",  # pi
    "Ρ": "R",
    "ρ": "r",  # rho
    "Σ": "S",
    "σ": "s",  # sigma
    "ς": "s",  # final sigma
    "Τ": "T",
    "τ": "t",  # tau
    "Υ": "U",
    "υ": "u",  # upsilon
    "Φ": "F",
    "φ": "f",  # phi
    "Χ": "C",
    "χ": "c",  # chi
    "Ψ": "Y",
    "ψ": "y",  # psi
    "Ω": "O",
    "ω": "o",  # omega
    "µ": "u",  # micro sign, the same answer as mu
}

#: Every ASCII letter two or more Greek letters both fold to. Once a file has
#: been folded nothing can tell such a pair apart, which is the whole reason
#: the command raises a dialog.
COLLIDING_READINGS = {
    "E": ["U+0395 GREEK CAPITAL LETTER EPSILON", "U+0397 GREEK CAPITAL LETTER ETA"],
    "e": ["U+03B5 GREEK SMALL LETTER EPSILON", "U+03B7 GREEK SMALL LETTER ETA"],
    "T": ["U+0398 GREEK CAPITAL LETTER THETA", "U+03A4 GREEK CAPITAL LETTER TAU"],
    "t": ["U+03B8 GREEK SMALL LETTER THETA", "U+03C4 GREEK SMALL LETTER TAU"],
    "U": ["U+039C GREEK CAPITAL LETTER MU", "U+03A5 GREEK CAPITAL LETTER UPSILON"],
    "u": [
        "U+00B5 MICRO SIGN",
        "U+03BC GREEK SMALL LETTER MU",
        "U+03C5 GREEK SMALL LETTER UPSILON",
    ],
    "O": ["U+039F GREEK CAPITAL LETTER OMICRON", "U+03A9 GREEK CAPITAL LETTER OMEGA"],
    "o": ["U+03BF GREEK SMALL LETTER OMICRON", "U+03C9 GREEK SMALL LETTER OMEGA"],
    "s": [
        "U+03C2 GREEK SMALL LETTER FINAL SIGMA",
        "U+03C3 GREEK SMALL LETTER SIGMA",
    ],
}

#: Greek letters that carry an accent. They never appear in this data, and
#: folding one would drop the accent with nothing to record that it was there,
#: so they are meant to fall through to Normalize Characters' leftover report.
ACCENTED_GREEK = "άέήίόύώΪΫ"


def arrays(path: Path) -> dict[str, dict[str, str]]:
    """One macro's tables, keyed by the array each entry was written into."""
    found: dict[str, dict[str, str]] = {name: {} for name in TABLE_ARRAYS}
    for array, key, value in ENTRY_RE.findall(path.read_text(encoding="utf-8")):
        found[array][unescape(key)] = unescape(value)
    return found


FOLD_ARRAYS = arrays(FOLD)
FIX = FOLD_ARRAYS["fix"]
GRK = FOLD_ARRAYS["grk"]


def latin_letters() -> list[str]:
    """Every letter in the two ranges Fold Letters to ASCII claims to cover."""
    return [
        chr(cp)
        for low, high in LATIN_RANGES
        for cp in range(low, high + 1)
        if unicodedata.category(chr(cp)).startswith("L")
    ]


def named(char: str) -> str:
    """``U+03BC GREEK SMALL LETTER MU``. Failure messages full of Greek letters
    that look like Latin ones are what this exists to avoid."""
    return "U+%04X %s" % (ord(char), unicodedata.name(char, "(unnamed)"))


# --------------------------------------------------------------------------
# the tables as a whole


def test_both_commands_that_carry_a_table_are_found() -> None:
    """Guard against every test below quietly checking nothing."""
    found = {path.name for path, _, _ in character_tables(REPO_ROOT)}
    assert {"fold-letters-to-ascii.nm", "normalize-characters.nm"} <= found, (
        f"a command that carries a character table stopped being read: {found}"
    )


def test_the_line_syntax_read_here_is_the_one_the_docs_read() -> None:
    """``ENTRY_RE`` above and chartable's ``TABLE_RE`` have to see one table.

    Everything else in this module reads the table through ``ENTRY_RE`` and the
    generated docs read it through chartable. A line that one matches and the
    other does not would leave a character tested but undocumented, or
    documented but never checked.
    """
    for path, groups, _ in character_tables(REPO_ROOT):
        documented = sorted(entry for _, entries in groups for entry in entries)
        here = sorted(
            (char, replacement)
            for table in arrays(path).values()
            for char, replacement in table.items()
        )
        assert here == documented, f"{path.name}: the two readings disagree"


def test_every_key_is_exactly_one_character() -> None:
    """A longer key would rewrite a sequence, which no table means to do."""
    wrong = [
        (path.name, key)
        for path, _, _ in character_tables(REPO_ROOT)
        for table in arrays(path).values()
        for key in table
        if len(key) != 1
    ]
    assert wrong == [], f"keys that are not a single character: {wrong}"


def test_no_key_is_an_ascii_character() -> None:
    """An ASCII key would rewrite ordinary text on every run."""
    wrong = [
        (path.name, key)
        for path, _, _ in character_tables(REPO_ROOT)
        for table in arrays(path).values()
        for key in table
        if ord(key) < 0x80
    ]
    assert wrong == [], f"ASCII keys: {wrong}"


def test_no_character_is_claimed_by_two_tables() -> None:
    """Within a command and across the two, one character has one answer.

    A character listed twice is not a conflict any macro would report: the
    second assignment silently wins, and which that is depends on the order
    ``for (ch in fix)`` happens to walk the array.
    """
    owners: dict[str, list[str]] = {}
    for path, _, _ in character_tables(REPO_ROOT):
        for array, table in arrays(path).items():
            for key in table:
                owners.setdefault(key, []).append(f"{path.name} {array}[]")

    duplicated = {
        named(key): places for key, places in owners.items() if len(places) > 1
    }
    assert duplicated == {}, f"characters with more than one answer: {duplicated}"


def test_every_replacement_is_pure_ascii() -> None:
    """Ending up with ASCII is the entire point of both tables."""
    wrong = [
        (path.name, named(key), replacement)
        for path, _, _ in character_tables(REPO_ROOT)
        for table in arrays(path).values()
        for key, replacement in table.items()
        if not replacement.isascii()
    ]
    assert wrong == [], f"replacements that are not ASCII: {wrong}"


def test_the_degree_sign_is_in_neither_table() -> None:
    """``test_command_does_not_corrupt_a_non_utf8_file`` rests on this.

    That test hands every command a latin-1 file and asserts the byte comes
    back. It only means anything while no command maps the byte: an accented
    letter would survive a UTF-8 locale because the buffer locks rather than
    because the command left it alone, and would be folded away under a latin-1
    one. The degree sign is left alone on purpose by both commands, which is
    what makes it a safe sample.
    """
    claimed = [
        path.name
        for path, _, _ in character_tables(REPO_ROOT)
        for table in arrays(path).values()
        if "°" in table
    ]
    assert claimed == [], (
        "the degree sign now has a replacement, so it is no longer a safe "
        "sample for the latin-1 test in tests/test_commands.py. Pick a byte no "
        f"table maps and change it there too. Claimed by: {claimed}"
    )


# --------------------------------------------------------------------------
# the Greek table, and the position arithmetic resting on it


def test_every_greek_replacement_is_exactly_one_character() -> None:
    """The line and column in the Greek warning depend on this.

    ``fold-letters-to-ascii.nm`` records each Greek letter's byte offset while
    the buffer still holds it, then subtracts the bytes the folds ahead of it
    removed to get the offset in the finished text. That subtraction assumes
    every ``grk[]`` replacement is one character wide. An entry replacing with
    two would leave every position after it short by one and the dialog would
    point at the wrong column, with nothing in the output to show it was wrong.

    An entry needing more than one character belongs in ``fix[]``, which runs
    first and which nothing measures.
    """
    wrong = {named(key): value for key, value in GRK.items() if len(value) != 1}
    assert wrong == {}, (
        "grk[] entries that are not one character wide, which breaks the offset "
        f"arithmetic behind the Greek warning: {wrong}. Move them to fix[]."
    )


def test_every_greek_letter_is_in_the_greek_table() -> None:
    """Including the ones with a Latin twin, which are the dangerous ones.

    U+039F GREEK CAPITAL LETTER OMICRON is pixel-identical to ``O`` and matches
    nothing downstream, so leaving it out would leave an invisible fault.
    """
    missing = [named(chr(cp)) for cp in sorted(GREEK_CODE_POINTS) if chr(cp) not in GRK]
    assert missing == [], f"Greek letters with no entry: {missing}"


def test_the_greek_table_holds_nothing_but_greek_and_the_micro_sign() -> None:
    extra = [named(key) for key in GRK if ord(key) not in GREEK_CODE_POINTS]
    assert extra == [], f"unexpected entries in grk[]: {extra}"


def test_every_greek_letter_folds_to_the_agreed_letter() -> None:
    """The readings are a judgement call, so they are written out once above."""
    assert GRK == GREEK


def test_mu_folds_to_u_so_micrometres_do_not_become_millimetres() -> None:
    """Both code points for mu, and the capital, give ``u`` rather than ``m``.

    ``24 µm`` folded to ``24 mm`` is a factor of a thousand in a database of
    wavelengths, and still a valid unit, so nothing downstream would catch it.
    ``um`` is the usual ASCII spelling in this field. Which of U+00B5 and
    U+03BC a PDF emits is not the author's choice, so both answer the same way.
    """
    assert GRK["µ"] == "u", "U+00B5 MICRO SIGN"
    assert GRK["μ"] == "u", "U+03BC GREEK SMALL LETTER MU"
    assert GRK["Μ"] == "U", "U+039C GREEK CAPITAL LETTER MU"


def test_the_readings_two_greek_letters_share_are_the_known_ones() -> None:
    """A table change that creates a tenth collision changes what is destroyed.

    The macro's dialog exists because of this list, so the list is pinned
    rather than counted: after a fold, nothing in the file says which of the
    pair was there.
    """
    shared = Counter(GRK.values())
    collisions = {
        letter: sorted(named(key) for key, value in GRK.items() if value == letter)
        for letter, count in shared.items()
        if count > 1
    }
    assert collisions == COLLIDING_READINGS


def test_accented_greek_is_left_out_of_the_table() -> None:
    """The macro's prefilter matches these, so they reach the ``ch in grk``
    test and fall through to being left alone. An entry here would change that
    silently and drop the accent."""
    present = [named(char) for char in ACCENTED_GREEK if char in GRK]
    assert present == [], f"accented Greek should be left alone: {present}"


# --------------------------------------------------------------------------
# the accented Latin table


def test_every_accented_latin_letter_is_in_the_fold_table() -> None:
    missing = [named(char) for char in latin_letters() if char not in FIX]
    assert missing == [], f"letters with no entry: {missing}"


def test_the_fold_table_holds_nothing_but_those_two_ranges() -> None:
    covered = set(latin_letters())
    extra = [named(key) for key in FIX if key not in covered]
    assert extra == [], f"unexpected entries in fix[]: {extra}"


def test_no_letter_folds_to_nothing() -> None:
    """Normalize Characters deletes invisible characters on purpose. A letter
    that vanished would be data loss with no trace of it left in the file."""
    empty = [named(key) for key, value in FIX.items() if value == ""]
    assert empty == [], f"letters replaced with nothing: {empty}"


def test_the_hand_written_folds_are_exactly_the_letters_nfd_cannot_answer() -> None:
    """Re-derives which letters needed a human rather than trusting the list.

    Everything with a canonical decomposition gets its base letter from
    :func:`unicodedata.normalize`. What is left is the eth, the strokes, the
    dotless i and the rest, plus the ten with no one-letter answer, and those
    are the only entries in 190 where somebody chose.
    """
    undecomposable = {
        char for char in FIX if unicodedata.normalize("NFD", char) == char
    }
    assert undecomposable == set(UNDECOMPOSABLE) | set(EXPANSIONS)


def test_every_decomposable_letter_folds_to_its_own_base_letter() -> None:
    """161 of the 190 entries, checked against Unicode instead of by eye."""
    wrong = {}
    for char, replacement in FIX.items():
        if char in UNDECOMPOSABLE or char in EXPANSIONS:
            continue
        base = unicodedata.normalize("NFD", char)[0]
        if replacement != base:
            wrong[named(char)] = (replacement, base)
    assert wrong == {}, f"folded to something other than the NFD base letter: {wrong}"


def test_the_letters_unicode_cannot_decompose_fold_to_the_agreed_letter() -> None:
    assert {key: FIX[key] for key in UNDECOMPOSABLE} == UNDECOMPOSABLE


def test_the_ten_expansions_are_the_agreed_spellings() -> None:
    assert {key: FIX[key] for key in EXPANSIONS} == EXPANSIONS


def test_nothing_but_those_ten_makes_a_line_longer() -> None:
    """A one-letter fold leaves every column where it was, which is what lets
    the piping commands run either side of this one. Ten letters break that,
    and they break it in names, where ``Weiß`` to ``Weis`` is a misspelling and
    ``Weiss`` is not."""
    longer = sorted(
        named(key)
        for table in (FIX, GRK)
        for key, value in table.items()
        if len(value) > 1
    )
    assert longer == sorted(named(key) for key in EXPANSIONS)


# --------------------------------------------------------------------------
# case


@pytest.mark.parametrize("array", ["fix", "grk"])
def test_a_one_letter_fold_keeps_the_case_of_the_letter(array: str) -> None:
    wrong = {
        named(key): value
        for key, value in FOLD_ARRAYS[array].items()
        if len(value) == 1 and value.isupper() != key.isupper()
    }
    assert wrong == {}, f"{array}[] entries that changed case: {wrong}"


def test_an_expansion_carries_the_case_of_the_letter_it_replaces() -> None:
    """``Ærø`` becomes ``AEro``, not ``Aero``.

    Title-casing would mean looking at the character after the key, a second
    rule the table has no way to carry. It is named as a wart in the docs
    instead.
    """
    wrong = {
        named(key): FIX[key]
        for key in EXPANSIONS
        if FIX[key].isupper() != key.isupper() or FIX[key].islower() != key.islower()
    }
    assert wrong == {}, f"expansions whose case does not match the key: {wrong}"


# --------------------------------------------------------------------------
# labels


def test_every_character_in_a_table_gets_a_label() -> None:
    for path, groups, names in character_tables(REPO_ROOT):
        for _, entries in groups:
            for char, _ in entries:
                assert char in names, f"{path.name}: {named(char)} has no label"


def test_a_label_written_by_hand_agrees_with_the_derived_one() -> None:
    """``label_for()`` stands in for the ``nam[]`` lines the fold table has no
    instructions to spare for, so the two have to say the same thing about the
    same character.

    ``startswith`` rather than equality, because a hand-written label may add
    something the code point and the Unicode name do not carry. The one that
    does is U+FEFF, labelled ``... (BOM)``.
    """
    for path, groups, names in character_tables(REPO_ROOT):
        for _, entries in groups:
            for char, _ in entries:
                assert names[char].startswith(label_for(char)), (
                    f"{path.name}: the macro labels {char!r} {names[char]!r}, "
                    f"which is not {label_for(char)!r}"
                )


def test_label_for_says_what_to_do_when_a_character_has_no_name() -> None:
    """Unicode leaves control characters unnamed, so a derived label is
    impossible for them and the macro has to carry a ``nam[]`` line. The error
    message is the only place that is written down."""
    with pytest.raises(ValueError, match=r"nam\[\] label"):
        label_for("\x01")


# --------------------------------------------------------------------------
# the parser the tests and the docs share


def test_unescape_reads_the_escapes_the_tables_use() -> None:
    assert unescape(r"\xc3\xa9") == "é"
    assert unescape(r"a\nb") == "a\nb"
    assert unescape(r"a\\b") == "a\\b"
    assert unescape(r"a\"b") == 'a"b'


def test_unescape_stops_a_hex_escape_after_two_digits() -> None:
    r"""parse.y's lexer takes at most two digits, so ``\x41BC`` is ``A`` and
    then the letters ``BC``, not one impossible code point."""
    assert unescape(r"\x41BC") == "ABC"
    assert unescape(r"\xc3\xa9a") == "éa"


def test_a_group_starts_at_the_comment_directly_above_it() -> None:
    groups, _ = parse_character_table('# dashes\nfix["\\xe2\\x80\\x93"] = "-"\n')
    assert groups == [("dashes", [("–", "-")])]


def test_a_blank_line_below_a_comment_stops_it_being_a_heading() -> None:
    """The only thing separating a group heading from the prose earlier in the
    file is that a heading has no blank line under it."""
    groups, _ = parse_character_table('# prose\n\nfix["\\xe2\\x80\\x93"] = "-"\n')
    assert groups == [("", [("–", "-")])]


def test_a_label_written_in_the_macro_wins_over_the_derived_one() -> None:
    _, names = parse_character_table(
        'fix["\\xef\\xbb\\xbf"] = ""\nnam["\\xef\\xbb\\xbf"] = "the BOM"\n'
    )
    assert names["﻿"] == "the BOM"


def test_a_character_with_no_label_of_its_own_gets_the_derived_one() -> None:
    _, names = parse_character_table('grk["\\xce\\xb1"] = "a"\n')
    assert names["α"] == "U+03B1 GREEK SMALL LETTER ALPHA"
