# Commands

Every macro command in `macros/commands/`. [Installing
macros](installing-macros.md) covers how to get one into the Macro menu; the
table on each command below carries the values the dialog asks for, and the
body is folded away underneath ready to copy.

**Installed in** names the menus a command belongs in. Most are Macro menu
only. The two that also say Window Background Menu answer a right-click in the
text as well, which takes [a second trip through Customize
Menus](installing-macros.md#install-a-background-menu-command).

This page is generated from the macro files by `tools/gen_docs.py`, so it
cannot drift away from what the macros actually do.

<!-- BEGIN GENERATED: commands -->

## Fold Letters to ASCII

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Fold Letters to ASCII` |
| Installed in | Macro Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/fold-letters-to-ascii.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/fold-letters-to-ascii.nm) |

Turns accented Latin letters and Greek letters into the plain ASCII letters
nearest to them, keeping upper and lower case as they were. Run it after
Normalize Characters, which handles the dashes, quotes and spaces and then
names the letters it left behind.

Accented letters lose the accent, so Balázs becomes Balazs and Ångström
becomes Angstrom. Ten letters have no one-letter answer and get longer
instead: Weiß becomes Weiss, Ærø becomes AEro. Those are the only ones that
change a line's width.

Greek letters become a single Latin letter, so α becomes a and Δ becomes D.
Five readings collide:

| Letters | Both give |
| --- | --- |
| ε η | e |
| ο ω | o |
| σ ς | s |
| τ θ | t |
| υ μ | u |

The capitals collide the same way, apart from the sigmas. Nothing can tell a
pair apart afterwards, so every Greek letter gets listed in a dialog with the
line and column it was on, and the cursor lands on the first one. Read that
list before the file goes any further.

μ, Μ and the micro sign µ give u rather than m, so that 24 µm stays a
wavelength instead of turning into 24 mm.

An accent fold gets no dialog, only the terminal summary, since there is
nothing ambiguous to decide. It is still data loss: nothing in the file
records that the accent was ever there, so keep the original if the spelling
of a name matters.

Anything else non-ASCII is left exactly as it was, accented Greek and the
degree sign included. Run Normalize Characters to get those counted.

A run that finds nothing leaves the buffer, the undo history and the modified
flag untouched.

It refuses a locked buffer, since nothing written to one lands. XNEdit locks
a file it cannot read as UTF-8; File > Read Only and a file you cannot write
lock one too.

A buffer with any accented letter in it gets scanned once per accented entry
in the table, so a file of several megabytes stalls. A job that size belongs
in Python rather than in the editor.

??? example "The macro body, ready to paste"

    ```
    fixed = ""
    ok = 1
    msg = ""

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    if ($read_only == 1) {
        ok = 0
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    }

    # Any byte with the high bit set, i.e. any part of any non-ASCII character.
    # The buffer holds UTF-8 and macro positions are byte offsets, so this is a
    # byte test, not a character test.
    high_byte = "[\\x80-\\xff]"

    # Every two-byte character whose lead byte could start a Greek one. A prefilter
    # and not the table: each hit is looked up in grk[] and anything that misses is
    # left alone, which is how accented Greek such as ά survives untouched. Only
    # genuine lead bytes are in the class, so it cannot match inside a three- or
    # four-byte character.
    greek_char = "[\\xc2\\xce\\xcf][\\x80-\\xbf]"

    # The fold table, keyed on the UTF-8 bytes of each letter. Keys are spelled as
    # \xNN escapes rather than as literal characters so the macro survives being
    # pasted through the Customize Menus dialog.
    #
    # There are no nam[] labels here, unlike normalize-characters.nm. Every entry
    # costs instructions and a macro compiles into 4096 of them, which a second
    # line per letter would blow through. tools/gen_docs.py derives each character's
    # Unicode name from the key bytes instead, so the documentation still names
    # them one by one.
    #
    # Greek sits in a table of its own because it is scanned for its positions
    # before it is replaced, and that scan is what the warning at the end reports.
    # The arithmetic behind it assumes every grk[] replacement is exactly one
    # character, so anything that replaces to more or fewer belongs in fix[] and
    # never in grk[]. fix[] carries no such rule, because it runs first and nothing
    # measures it.
    #
    # Order does not matter inside either table: every replacement is ASCII, so no
    # entry can feed another.

    # accented capitals, Latin-1 Supplement
    fix["\xc3\x80"] = "A"
    fix["\xc3\x81"] = "A"
    fix["\xc3\x82"] = "A"
    fix["\xc3\x83"] = "A"
    fix["\xc3\x84"] = "A"
    fix["\xc3\x85"] = "A"
    fix["\xc3\x87"] = "C"
    fix["\xc3\x88"] = "E"
    fix["\xc3\x89"] = "E"
    fix["\xc3\x8a"] = "E"
    fix["\xc3\x8b"] = "E"
    fix["\xc3\x8c"] = "I"
    fix["\xc3\x8d"] = "I"
    fix["\xc3\x8e"] = "I"
    fix["\xc3\x8f"] = "I"
    fix["\xc3\x90"] = "D"
    fix["\xc3\x91"] = "N"
    fix["\xc3\x92"] = "O"
    fix["\xc3\x93"] = "O"
    fix["\xc3\x94"] = "O"
    fix["\xc3\x95"] = "O"
    fix["\xc3\x96"] = "O"
    fix["\xc3\x98"] = "O"
    fix["\xc3\x99"] = "U"
    fix["\xc3\x9a"] = "U"
    fix["\xc3\x9b"] = "U"
    fix["\xc3\x9c"] = "U"
    fix["\xc3\x9d"] = "Y"

    # accented small letters, Latin-1 Supplement
    fix["\xc3\xa0"] = "a"
    fix["\xc3\xa1"] = "a"
    fix["\xc3\xa2"] = "a"
    fix["\xc3\xa3"] = "a"
    fix["\xc3\xa4"] = "a"
    fix["\xc3\xa5"] = "a"
    fix["\xc3\xa7"] = "c"
    fix["\xc3\xa8"] = "e"
    fix["\xc3\xa9"] = "e"
    fix["\xc3\xaa"] = "e"
    fix["\xc3\xab"] = "e"
    fix["\xc3\xac"] = "i"
    fix["\xc3\xad"] = "i"
    fix["\xc3\xae"] = "i"
    fix["\xc3\xaf"] = "i"
    fix["\xc3\xb0"] = "d"
    fix["\xc3\xb1"] = "n"
    fix["\xc3\xb2"] = "o"
    fix["\xc3\xb3"] = "o"
    fix["\xc3\xb4"] = "o"
    fix["\xc3\xb5"] = "o"
    fix["\xc3\xb6"] = "o"
    fix["\xc3\xb8"] = "o"
    fix["\xc3\xb9"] = "u"
    fix["\xc3\xba"] = "u"
    fix["\xc3\xbb"] = "u"
    fix["\xc3\xbc"] = "u"
    fix["\xc3\xbd"] = "y"
    fix["\xc3\xbf"] = "y"

    # Latin Extended-A
    fix["\xc4\x80"] = "A"
    fix["\xc4\x81"] = "a"
    fix["\xc4\x82"] = "A"
    fix["\xc4\x83"] = "a"
    fix["\xc4\x84"] = "A"
    fix["\xc4\x85"] = "a"
    fix["\xc4\x86"] = "C"
    fix["\xc4\x87"] = "c"
    fix["\xc4\x88"] = "C"
    fix["\xc4\x89"] = "c"
    fix["\xc4\x8a"] = "C"
    fix["\xc4\x8b"] = "c"
    fix["\xc4\x8c"] = "C"
    fix["\xc4\x8d"] = "c"
    fix["\xc4\x8e"] = "D"
    fix["\xc4\x8f"] = "d"
    fix["\xc4\x90"] = "D"
    fix["\xc4\x91"] = "d"
    fix["\xc4\x92"] = "E"
    fix["\xc4\x93"] = "e"
    fix["\xc4\x94"] = "E"
    fix["\xc4\x95"] = "e"
    fix["\xc4\x96"] = "E"
    fix["\xc4\x97"] = "e"
    fix["\xc4\x98"] = "E"
    fix["\xc4\x99"] = "e"
    fix["\xc4\x9a"] = "E"
    fix["\xc4\x9b"] = "e"
    fix["\xc4\x9c"] = "G"
    fix["\xc4\x9d"] = "g"
    fix["\xc4\x9e"] = "G"
    fix["\xc4\x9f"] = "g"
    fix["\xc4\xa0"] = "G"
    fix["\xc4\xa1"] = "g"
    fix["\xc4\xa2"] = "G"
    fix["\xc4\xa3"] = "g"
    fix["\xc4\xa4"] = "H"
    fix["\xc4\xa5"] = "h"
    fix["\xc4\xa6"] = "H"
    fix["\xc4\xa7"] = "h"
    fix["\xc4\xa8"] = "I"
    fix["\xc4\xa9"] = "i"
    fix["\xc4\xaa"] = "I"
    fix["\xc4\xab"] = "i"
    fix["\xc4\xac"] = "I"
    fix["\xc4\xad"] = "i"
    fix["\xc4\xae"] = "I"
    fix["\xc4\xaf"] = "i"
    fix["\xc4\xb0"] = "I"
    fix["\xc4\xb1"] = "i"
    fix["\xc4\xb4"] = "J"
    fix["\xc4\xb5"] = "j"
    fix["\xc4\xb6"] = "K"
    fix["\xc4\xb7"] = "k"
    fix["\xc4\xb8"] = "k"
    fix["\xc4\xb9"] = "L"
    fix["\xc4\xba"] = "l"
    fix["\xc4\xbb"] = "L"
    fix["\xc4\xbc"] = "l"
    fix["\xc4\xbd"] = "L"
    fix["\xc4\xbe"] = "l"
    fix["\xc4\xbf"] = "L"
    fix["\xc5\x80"] = "l"
    fix["\xc5\x81"] = "L"
    fix["\xc5\x82"] = "l"
    fix["\xc5\x83"] = "N"
    fix["\xc5\x84"] = "n"
    fix["\xc5\x85"] = "N"
    fix["\xc5\x86"] = "n"
    fix["\xc5\x87"] = "N"
    fix["\xc5\x88"] = "n"
    fix["\xc5\x8a"] = "N"
    fix["\xc5\x8b"] = "n"
    fix["\xc5\x8c"] = "O"
    fix["\xc5\x8d"] = "o"
    fix["\xc5\x8e"] = "O"
    fix["\xc5\x8f"] = "o"
    fix["\xc5\x90"] = "O"
    fix["\xc5\x91"] = "o"
    fix["\xc5\x94"] = "R"
    fix["\xc5\x95"] = "r"
    fix["\xc5\x96"] = "R"
    fix["\xc5\x97"] = "r"
    fix["\xc5\x98"] = "R"
    fix["\xc5\x99"] = "r"
    fix["\xc5\x9a"] = "S"
    fix["\xc5\x9b"] = "s"
    fix["\xc5\x9c"] = "S"
    fix["\xc5\x9d"] = "s"
    fix["\xc5\x9e"] = "S"
    fix["\xc5\x9f"] = "s"
    fix["\xc5\xa0"] = "S"
    fix["\xc5\xa1"] = "s"
    fix["\xc5\xa2"] = "T"
    fix["\xc5\xa3"] = "t"
    fix["\xc5\xa4"] = "T"
    fix["\xc5\xa5"] = "t"
    fix["\xc5\xa6"] = "T"
    fix["\xc5\xa7"] = "t"
    fix["\xc5\xa8"] = "U"
    fix["\xc5\xa9"] = "u"
    fix["\xc5\xaa"] = "U"
    fix["\xc5\xab"] = "u"
    fix["\xc5\xac"] = "U"
    fix["\xc5\xad"] = "u"
    fix["\xc5\xae"] = "U"
    fix["\xc5\xaf"] = "u"
    fix["\xc5\xb0"] = "U"
    fix["\xc5\xb1"] = "u"
    fix["\xc5\xb2"] = "U"
    fix["\xc5\xb3"] = "u"
    fix["\xc5\xb4"] = "W"
    fix["\xc5\xb5"] = "w"
    fix["\xc5\xb6"] = "Y"
    fix["\xc5\xb7"] = "y"
    fix["\xc5\xb8"] = "Y"
    fix["\xc5\xb9"] = "Z"
    fix["\xc5\xba"] = "z"
    fix["\xc5\xbb"] = "Z"
    fix["\xc5\xbc"] = "z"
    fix["\xc5\xbd"] = "Z"
    fix["\xc5\xbe"] = "z"
    fix["\xc5\xbf"] = "s"

    # letters with no one-letter answer
    fix["\xc3\x86"] = "AE"
    fix["\xc3\x9e"] = "TH"
    fix["\xc3\x9f"] = "ss"
    fix["\xc3\xa6"] = "ae"
    fix["\xc3\xbe"] = "th"
    fix["\xc4\xb2"] = "IJ"
    fix["\xc4\xb3"] = "ij"
    fix["\xc5\x89"] = "'n"
    fix["\xc5\x92"] = "OE"
    fix["\xc5\x93"] = "oe"

    # Greek capitals
    grk["\xce\x91"] = "A"
    grk["\xce\x92"] = "B"
    grk["\xce\x93"] = "G"
    grk["\xce\x94"] = "D"
    grk["\xce\x95"] = "E"
    grk["\xce\x96"] = "Z"
    grk["\xce\x97"] = "E"
    grk["\xce\x98"] = "T"
    grk["\xce\x99"] = "I"
    grk["\xce\x9a"] = "K"
    grk["\xce\x9b"] = "L"
    grk["\xce\x9c"] = "U"
    grk["\xce\x9d"] = "N"
    grk["\xce\x9e"] = "X"
    grk["\xce\x9f"] = "O"
    grk["\xce\xa0"] = "P"
    grk["\xce\xa1"] = "R"
    grk["\xce\xa3"] = "S"
    grk["\xce\xa4"] = "T"
    grk["\xce\xa5"] = "U"
    grk["\xce\xa6"] = "F"
    grk["\xce\xa7"] = "C"
    grk["\xce\xa8"] = "Y"
    grk["\xce\xa9"] = "O"

    # Greek small letters
    grk["\xce\xb1"] = "a"
    grk["\xce\xb2"] = "b"
    grk["\xce\xb3"] = "g"
    grk["\xce\xb4"] = "d"
    grk["\xce\xb5"] = "e"
    grk["\xce\xb6"] = "z"
    grk["\xce\xb7"] = "e"
    grk["\xce\xb8"] = "t"
    grk["\xce\xb9"] = "i"
    grk["\xce\xba"] = "k"
    grk["\xce\xbb"] = "l"
    grk["\xce\xbc"] = "u"
    grk["\xce\xbd"] = "n"
    grk["\xce\xbe"] = "x"
    grk["\xce\xbf"] = "o"
    grk["\xcf\x80"] = "p"
    grk["\xcf\x81"] = "r"
    grk["\xcf\x82"] = "s"
    grk["\xcf\x83"] = "s"
    grk["\xcf\x84"] = "t"
    grk["\xcf\x85"] = "u"
    grk["\xcf\x86"] = "f"
    grk["\xcf\x87"] = "c"
    grk["\xcf\x88"] = "y"
    grk["\xcf\x89"] = "o"

    # a Greek letter with a second code point
    grk["\xc2\xb5"] = "u"

    # What the report reads, whether or not the work below runs. found[], gpos[]
    # and gch[] are filled by the Greek scan; every grk[] key is two bytes and
    # every replacement is one, so an offset taken there, less the bytes the folds
    # ahead of it removed, is the offset in the finished buffer. shrink is written
    # out as the lengths rather than as a count of letters, so an entry that is not
    # two bytes to one would still be right.
    found = $empty_array
    gpos = $empty_array
    gch = $empty_array
    glist = ""
    n_greek = 0
    n_shown = 0
    shrink = 0

    if (ok == 1) {
        original = get_range(0, $text_length)
        cleaned = original

        # The accented letters. Skipped outright on a buffer that is already pure
        # ASCII, which turns the common case into one scan instead of one per
        # entry.
        if (search_string(cleaned, high_byte, 0, "regex") != -1) {
            # One scan per distinct lead byte, three of them here, answers for
            # every entry that starts with it, so a paste with no accents in it
            # never pays for the 190 accented entries. Memoising against a buffer
            # that changes under the loop is safe because every replacement is
            # ASCII and so cannot put a lead byte back in.
            seen = $empty_array

            for (ch in fix) {
                lead = substring(ch, 0, 1)
                if (lead in seen) {
                    here = seen[lead]
                } else {
                    here = 0
                    if (search_string(cleaned, lead, 0, "case") != -1) {
                        here = 1
                    }
                    seen[lead] = here
                }

                if (here == 1) {
                    if (search_string(cleaned, ch, 0, "case") != -1) {
                        # "copy" is not optional. Without it replace_in_string()
                        # returns an empty string whenever the pattern does not
                        # match, and this loop would erase the buffer on its first
                        # miss.
                        cleaned = replace_in_string(cleaned, ch, fix[ch], "case", "copy")
                        fixed = fixed "  " ch " -> " fix[ch] "\n"
                    }
                }
            }
        }

        # Greek, in two passes. The first records where every letter is while the
        # text still holds them, because those offsets are what the report turns
        # into line and column numbers; the second replaces them. Nothing caps the
        # scan: the index it builds is what drives the replacement, so a cap would
        # mean a silent partial conversion.
        pos = search_string(cleaned, greek_char, 0, "regex")
        while (pos != -1) {
            # $search_end is global and the next search overwrites it, so read it
            # before anything else touches the string.
            stop = $search_end
            ch = substring(cleaned, pos, stop)
            if (ch in grk) {
                # Positions are kept for the first 20 only, which is as much as a
                # dialog can usefully hold. The count below is of all of them.
                if (n_shown < 20) {
                    gpos[n_shown] = pos - shrink
                    gch[n_shown] = ch
                    n_shown++
                }
                shrink = shrink + (stop - pos) - length(grk[ch])
                found[ch] = 1
                n_greek++
            }
            pos = search_string(cleaned, greek_char, stop, "regex")
        }

        for (ch in found) {
            cleaned = replace_in_string(cleaned, ch, grk[ch], "case", "copy")
        }

        # Write back, once, only if there is a change to make.
        if (cleaned != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, cleaned)

            # An accented letter is longer than what replaces it, so the buffer
            # usually got shorter and the old offset may be past the end. Belt and
            # braces: set_cursor_pos() clamps to the end of the buffer itself, on
            # XNEdit and on NEdit 5.7 alike, so no test can reach the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }

        # Line and column for each Greek letter, now that the buffer holds the
        # finished text. set_cursor_pos() and then $line and $column are the
        # editor's own arithmetic, the same numbers the statistics line shows as L:
        # and C:, so nothing here counts a column by hand. A tab would make a
        # column ambiguous, so run this after Normalize Characters, which takes the
        # tabs out.
        for (i = 0; i < n_shown; i++) {
            # These are offsets into the finished text, and the guard at the top is
            # what says the write above landed, so they fit the buffer. Belt and
            # braces: set_cursor_pos() clamps to the end of the buffer itself, on
            # XNEdit and on NEdit 5.7 alike, so no test can reach the line below.
            if (gpos[i] > $text_length) {
                gpos[i] = $text_length
            }
            set_cursor_pos(gpos[i])
            glist = glist "    line " $line ", column " $column "    " gch[i] " -> " grk[gch[i]] "\n"
        }

        # The cursor ends on the first Greek letter, because that is the one thing
        # here that asks for a decision. With no Greek it stays where it was.
        if (n_greek > 0) {
            set_cursor_pos(gpos[0])
        }
    }

    # Report. t_print() goes to the terminal that launched xnedit, so the routine
    # case stays quiet; the dialog is reserved for the case that wants a human.
    if (ok == 0) {
        t_print("fold: " $file_name ": nothing changed\n")
    } else if (fixed == "" && n_greek == 0) {
        t_print("fold: " $file_name ": nothing to change\n")
    } else {
        t_print("fold: " $file_name ":\n" fixed glist)
    }

    # Built up a statement at a time, because line continuations would have to
    # survive the extra layer of escaping that nedit.rc puts on every macro line.
    if (n_greek > 0) {
        msg = $file_name " had " n_greek " Greek letter(s) in it, and each one is "
        msg = msg "now the nearest single Latin letter. Which letter it started as "
        msg = msg "is no longer recoverable from the file. Five of the readings are "
        msg = msg "shared, whether or not this file held the pair:\n\n"
        msg = msg "    e   epsilon, eta\n"
        msg = msg "    o   omicron, omega\n"
        msg = msg "    s   sigma, final sigma\n"
        msg = msg "    t   tau, theta\n"
        msg = msg "    u   upsilon, mu, micro sign\n\n"
        msg = msg glist
        if (n_greek > n_shown) {
            n_more = n_greek - n_shown
            msg = msg "    ...and " n_more " more\n"
        }
        msg = msg "\nLines count from 1 and columns from 0, the same as the "
        msg = msg "statistics line. The cursor is on the first one."
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    ```

## Normalize Characters

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Normalize Characters` |
| Installed in | Macro Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/normalize-characters.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/normalize-characters.nm) |

Rewrites the characters that ride along with text pasted out of a PDF: the
dashes that are not "-", the quotes that are not "'" or '"', the spaces that
are not " ", the ff/fi/fl ligatures PDFs store as single characters, and the
zero-width characters that stay invisible until something downstream chokes
on them. Tabs become single spaces and stray carriage returns become
newlines.

Non-ASCII characters with no safe ASCII spelling - degree signs, Greek
letters, accented names - are deliberately left alone. Rather than mangle
them, the macro counts what is left, parks the cursor on the first one, and
lists them in a dialog.

A run that finds nothing leaves the buffer, the undo history and the
modified flag untouched.

It refuses a locked buffer, since nothing written to one lands. XNEdit locks
a file it cannot read as UTF-8; File > Read Only and a file you cannot write
lock one too.

??? example "The macro body, ready to paste"

    ```
    fixed = ""
    ok = 1
    msg = ""

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    if ($read_only == 1) {
        ok = 0
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    }

    # Any byte with the high bit set, i.e. any part of any non-ASCII character.
    # The buffer holds UTF-8 and macro positions are byte offsets, so this is a
    # byte test, not a character test.
    high_byte = "[\\x80-\\xff]"

    # One whole non-ASCII character: a lead byte plus its continuation bytes, or
    # a stray continuation byte left behind by a file that was not valid UTF-8.
    # Used to report the leftovers a character at a time instead of a byte at a
    # time.
    high_char = "[\\xc0-\\xff][\\x80-\\xbf]*|[\\x80-\\xff]"

    # The rewrite table. fix[] maps the UTF-8 bytes of a character to its ASCII
    # stand-in, nam[] is the label the summary prints. Keys are spelled as \xNN
    # escapes rather than as literal characters for two reasons: the macro
    # survives being pasted through the Customize Menus dialog, and the entries
    # you cannot see - the zero-width ones - are still readable here.
    #
    # To add a character, look up its UTF-8 bytes and add a matching pair of
    # lines. Order does not matter: every replacement is ASCII, so no entry can
    # feed another.

    # dashes and hyphens
    fix["\xe2\x80\x90"] = "-"
    nam["\xe2\x80\x90"] = "U+2010 HYPHEN"
    fix["\xe2\x80\x91"] = "-"
    nam["\xe2\x80\x91"] = "U+2011 NON-BREAKING HYPHEN"
    fix["\xe2\x80\x92"] = "-"
    nam["\xe2\x80\x92"] = "U+2012 FIGURE DASH"
    fix["\xe2\x80\x93"] = "-"
    nam["\xe2\x80\x93"] = "U+2013 EN DASH"
    fix["\xe2\x80\x94"] = "-"
    nam["\xe2\x80\x94"] = "U+2014 EM DASH"
    fix["\xe2\x80\x95"] = "-"
    nam["\xe2\x80\x95"] = "U+2015 HORIZONTAL BAR"
    fix["\xe2\x81\x83"] = "-"
    nam["\xe2\x81\x83"] = "U+2043 HYPHEN BULLET"
    fix["\xe2\x88\x92"] = "-"
    nam["\xe2\x88\x92"] = "U+2212 MINUS SIGN"
    fix["\xef\xb9\x98"] = "-"
    nam["\xef\xb9\x98"] = "U+FE58 SMALL EM DASH"
    fix["\xef\xb9\xa3"] = "-"
    nam["\xef\xb9\xa3"] = "U+FE63 SMALL HYPHEN-MINUS"
    fix["\xef\xbc\x8d"] = "-"
    nam["\xef\xbc\x8d"] = "U+FF0D FULLWIDTH HYPHEN-MINUS"

    # single quotes, apostrophes, primes
    fix["\xc2\xb4"] = "'"
    nam["\xc2\xb4"] = "U+00B4 ACUTE ACCENT"
    fix["\xca\xb9"] = "'"
    nam["\xca\xb9"] = "U+02B9 MODIFIER LETTER PRIME"
    fix["\xca\xbc"] = "'"
    nam["\xca\xbc"] = "U+02BC MODIFIER LETTER APOSTROPHE"
    fix["\xe2\x80\x98"] = "'"
    nam["\xe2\x80\x98"] = "U+2018 LEFT SINGLE QUOTATION MARK"
    fix["\xe2\x80\x99"] = "'"
    nam["\xe2\x80\x99"] = "U+2019 RIGHT SINGLE QUOTATION MARK"
    fix["\xe2\x80\x9a"] = "'"
    nam["\xe2\x80\x9a"] = "U+201A SINGLE LOW-9 QUOTATION MARK"
    fix["\xe2\x80\x9b"] = "'"
    nam["\xe2\x80\x9b"] = "U+201B SINGLE HIGH-REVERSED-9 QUOTATION MARK"
    fix["\xe2\x80\xb2"] = "'"
    nam["\xe2\x80\xb2"] = "U+2032 PRIME"
    fix["\xe2\x80\xb5"] = "'"
    nam["\xe2\x80\xb5"] = "U+2035 REVERSED PRIME"
    fix["\xef\xbc\x87"] = "'"
    nam["\xef\xbc\x87"] = "U+FF07 FULLWIDTH APOSTROPHE"

    # double quotes and double primes
    fix["\xca\xba"] = "\""
    nam["\xca\xba"] = "U+02BA MODIFIER LETTER DOUBLE PRIME"
    fix["\xe2\x80\x9c"] = "\""
    nam["\xe2\x80\x9c"] = "U+201C LEFT DOUBLE QUOTATION MARK"
    fix["\xe2\x80\x9d"] = "\""
    nam["\xe2\x80\x9d"] = "U+201D RIGHT DOUBLE QUOTATION MARK"
    fix["\xe2\x80\x9e"] = "\""
    nam["\xe2\x80\x9e"] = "U+201E DOUBLE LOW-9 QUOTATION MARK"
    fix["\xe2\x80\x9f"] = "\""
    nam["\xe2\x80\x9f"] = "U+201F DOUBLE HIGH-REVERSED-9 QUOTATION MARK"
    fix["\xe2\x80\xb3"] = "\""
    nam["\xe2\x80\xb3"] = "U+2033 DOUBLE PRIME"
    fix["\xe2\x80\xb6"] = "\""
    nam["\xe2\x80\xb6"] = "U+2036 REVERSED DOUBLE PRIME"
    fix["\xef\xbc\x82"] = "\""
    nam["\xef\xbc\x82"] = "U+FF02 FULLWIDTH QUOTATION MARK"

    # spaces
    fix["\xc2\xa0"] = " "
    nam["\xc2\xa0"] = "U+00A0 NO-BREAK SPACE"
    fix["\xe1\x9a\x80"] = " "
    nam["\xe1\x9a\x80"] = "U+1680 OGHAM SPACE MARK"
    fix["\xe2\x80\x80"] = " "
    nam["\xe2\x80\x80"] = "U+2000 EN QUAD"
    fix["\xe2\x80\x81"] = " "
    nam["\xe2\x80\x81"] = "U+2001 EM QUAD"
    fix["\xe2\x80\x82"] = " "
    nam["\xe2\x80\x82"] = "U+2002 EN SPACE"
    fix["\xe2\x80\x83"] = " "
    nam["\xe2\x80\x83"] = "U+2003 EM SPACE"
    fix["\xe2\x80\x84"] = " "
    nam["\xe2\x80\x84"] = "U+2004 THREE-PER-EM SPACE"
    fix["\xe2\x80\x85"] = " "
    nam["\xe2\x80\x85"] = "U+2005 FOUR-PER-EM SPACE"
    fix["\xe2\x80\x86"] = " "
    nam["\xe2\x80\x86"] = "U+2006 SIX-PER-EM SPACE"
    fix["\xe2\x80\x87"] = " "
    nam["\xe2\x80\x87"] = "U+2007 FIGURE SPACE"
    fix["\xe2\x80\x88"] = " "
    nam["\xe2\x80\x88"] = "U+2008 PUNCTUATION SPACE"
    fix["\xe2\x80\x89"] = " "
    nam["\xe2\x80\x89"] = "U+2009 THIN SPACE"
    fix["\xe2\x80\x8a"] = " "
    nam["\xe2\x80\x8a"] = "U+200A HAIR SPACE"
    fix["\xe2\x80\xaf"] = " "
    nam["\xe2\x80\xaf"] = "U+202F NARROW NO-BREAK SPACE"
    fix["\xe2\x81\x9f"] = " "
    nam["\xe2\x81\x9f"] = "U+205F MEDIUM MATHEMATICAL SPACE"
    fix["\xe3\x80\x80"] = " "
    nam["\xe3\x80\x80"] = "U+3000 IDEOGRAPHIC SPACE"

    # invisible characters, deleted outright
    fix["\xc2\xad"] = ""
    nam["\xc2\xad"] = "U+00AD SOFT HYPHEN"
    fix["\xe2\x80\x8b"] = ""
    nam["\xe2\x80\x8b"] = "U+200B ZERO WIDTH SPACE"
    fix["\xe2\x80\x8c"] = ""
    nam["\xe2\x80\x8c"] = "U+200C ZERO WIDTH NON-JOINER"
    fix["\xe2\x80\x8d"] = ""
    nam["\xe2\x80\x8d"] = "U+200D ZERO WIDTH JOINER"
    fix["\xe2\x81\xa0"] = ""
    nam["\xe2\x81\xa0"] = "U+2060 WORD JOINER"
    fix["\xef\xbb\xbf"] = ""
    nam["\xef\xbb\xbf"] = "U+FEFF ZERO WIDTH NO-BREAK SPACE (BOM)"

    # line separators
    fix["\xe2\x80\xa8"] = "\n"
    nam["\xe2\x80\xa8"] = "U+2028 LINE SEPARATOR"
    fix["\xe2\x80\xa9"] = "\n"
    nam["\xe2\x80\xa9"] = "U+2029 PARAGRAPH SEPARATOR"

    # ligatures
    fix["\xef\xac\x80"] = "ff"
    nam["\xef\xac\x80"] = "U+FB00 LATIN SMALL LIGATURE FF"
    fix["\xef\xac\x81"] = "fi"
    nam["\xef\xac\x81"] = "U+FB01 LATIN SMALL LIGATURE FI"
    fix["\xef\xac\x82"] = "fl"
    nam["\xef\xac\x82"] = "U+FB02 LATIN SMALL LIGATURE FL"
    fix["\xef\xac\x83"] = "ffi"
    nam["\xef\xac\x83"] = "U+FB03 LATIN SMALL LIGATURE FFI"
    fix["\xef\xac\x84"] = "ffl"
    nam["\xef\xac\x84"] = "U+FB04 LATIN SMALL LIGATURE FFL"
    fix["\xef\xac\x85"] = "st"
    nam["\xef\xac\x85"] = "U+FB05 LATIN SMALL LIGATURE LONG S T"
    fix["\xef\xac\x86"] = "st"
    nam["\xef\xac\x86"] = "U+FB06 LATIN SMALL LIGATURE ST"

    # other punctuation
    fix["\xe2\x80\xa2"] = "*"
    nam["\xe2\x80\xa2"] = "U+2022 BULLET"
    fix["\xe2\x80\xa6"] = "..."
    nam["\xe2\x80\xa6"] = "U+2026 HORIZONTAL ELLIPSIS"
    fix["\xc3\x97"] = "x"
    nam["\xc3\x97"] = "U+00D7 MULTIPLICATION SIGN"
    fix["\xc3\xb7"] = "/"
    nam["\xc3\xb7"] = "U+00F7 DIVISION SIGN"
    fix["\xe2\x81\x84"] = "/"
    nam["\xe2\x81\x84"] = "U+2044 FRACTION SLASH"
    fix["\xe2\x88\x95"] = "/"
    nam["\xe2\x88\x95"] = "U+2215 DIVISION SLASH"

    # math relations
    fix["\xc2\xb1"] = "+/-"
    nam["\xc2\xb1"] = "U+00B1 PLUS-MINUS SIGN"
    fix["\xe2\x88\x93"] = "-/+"
    nam["\xe2\x88\x93"] = "U+2213 MINUS-OR-PLUS SIGN"
    fix["\xe2\x89\x88"] = "~"
    nam["\xe2\x89\x88"] = "U+2248 ALMOST EQUAL TO"
    fix["\xe2\x88\xbc"] = "~"
    nam["\xe2\x88\xbc"] = "U+223C TILDE OPERATOR"
    fix["\xe2\x89\xa0"] = "!="
    nam["\xe2\x89\xa0"] = "U+2260 NOT EQUAL TO"
    fix["\xe2\x89\xa4"] = "<="
    nam["\xe2\x89\xa4"] = "U+2264 LESS-THAN OR EQUAL TO"
    fix["\xe2\x89\xa5"] = ">="
    nam["\xe2\x89\xa5"] = "U+2265 GREATER-THAN OR EQUAL TO"

    # What the report reads, whether or not the work below runs.
    left = $empty_array
    n_left = 0
    first_left = -1

    if (ok == 1) {
        original = get_range(0, $text_length)
        cleaned = original

        # Stray carriage returns. A DOS-format file never shows these - XNEdit
        # strips them on open and puts them back on save - but a pasted block can
        # carry them into a Unix-format buffer.
        if (search_string(cleaned, "\r", 0, "case") != -1) {
            cleaned = replace_in_string(cleaned, "\r\n", "\n", "case", "copy")
            cleaned = replace_in_string(cleaned, "\r", "\n", "case", "copy")
            fixed = fixed "  carriage return -> newline\n"
        }

        # Tabs. One tab becomes one space, which does not preserve column
        # alignment. XNEdit has nothing that expands a tab to the spaces it stands
        # for, so when the columns have to survive, select the file and run expand
        # through Shell > Filter Selection instead of this.
        if (search_string(cleaned, "\t", 0, "case") != -1) {
            cleaned = replace_in_string(cleaned, "\t", " ", "case", "copy")
            fixed = fixed "  tab -> space\n"
        }

        # The table itself. Skipped outright on a buffer that is already pure
        # ASCII, which turns the common case into one scan instead of one per
        # entry.
        if (search_string(cleaned, high_byte, 0, "regex") != -1) {
            for (ch in fix) {
                before = cleaned
                # "copy" is not optional. Without it replace_in_string() returns an
                # empty string whenever the pattern does not match, and this loop
                # would erase the buffer on its first miss.
                cleaned = replace_in_string(cleaned, ch, fix[ch], "case", "copy")
                if (cleaned != before) {
                    fixed = fixed "  " nam[ch] "\n"
                }
            }
        }

        # Write back, once, only if there is a change to make.
        if (cleaned != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, cleaned)

            # The buffer usually got shorter, so the old offset may be past the
            # end. Belt and braces: set_cursor_pos() clamps to the end of the
            # buffer itself, on XNEdit and on NEdit 5.7 alike, so no test can reach
            # the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }

        # What is still not ASCII. Counted per character, capped so that a buffer
        # of mostly non-Latin text cannot turn this into a long stall.
        pos = search_string(cleaned, high_char, 0, "regex")
        while (pos != -1 && n_left < 2000) {
            if (first_left == -1) {
                first_left = pos
            }
            ch = substring(cleaned, pos, $search_end)
            if (ch in left) {
                left[ch] = left[ch] + 1
            } else {
                left[ch] = 1
            }
            n_left++
            pos = search_string(cleaned, high_char, $search_end, "regex")
        }
    }

    # Report. t_print() goes to the terminal that launched xnedit, so the routine
    # case stays quiet; the dialog is reserved for the case that wants a human.
    if (ok == 0) {
        t_print("normalize: " $file_name ": nothing changed\n")
    } else if (fixed == "") {
        t_print("normalize: " $file_name ": nothing to change\n")
    } else {
        t_print("normalize: " $file_name ":\n" fixed)
    }

    if (n_left > 0) {
        set_cursor_pos(first_left)

        # Built up a statement at a time. Line continuations would have to survive
        # the extra layer of escaping that nedit.rc puts on every macro line.
        summary = ""
        for (ch in left) {
            summary = summary "    " left[ch] "x  " ch "\n"
        }
        if (pos != -1) {
            summary = summary "    ...and more, counting stopped at 2000\n"
        }

        msg = $file_name " has " left[] " kind(s) of non-ASCII character left, "
        msg = msg n_left " in all. These have no safe ASCII spelling, so the "
        msg = msg "macro did not touch them:\n\n" summary
        msg = msg "\nThe cursor is on the first one, line " $line ". Fix those by "
        msg = msg "hand, or add them to the table in this macro if the answer is "
        msg = msg "always the same."
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    ```

## Pad Columns

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Pad Columns` |
| Installed in | Macro Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/pad-columns.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/pad-columns.nm) |

Squares up a pipe-delimited table. Trims the spaces around every field, then
pads it back out to the width of the widest value in its column, so each row
comes out the same length and the pipes line up down the file.

    Griffin        |12:29:46.7
    Smith         |12:36:44.0

becomes

    Griffin|12:29:46.7
    Smith  |12:36:44.0

Run it last, because every edit before it changes a width: a ligature becomes
the two letters it stands for, ß becomes ss, and a value fixed by hand is
whatever length you typed. So fix the characters, put the pipes in, read the
file through, and pad at the end.

It splits on "|" and nothing else. A line with no pipe in it is not a table
row: it passes through verbatim, along with blank lines and the ##refcode
header block, and none of them count towards a column width. Nothing here
reads a boundary out of a run of spaces, so a file nobody has piped yet comes
back untouched.

Widths are counted in characters rather than bytes, so a field measures what
it prints. Balázs is six wide, though it takes seven bytes.

Every column is padded, the last one included, so each row ends in the same
place. Run Trim Trailing Blanks afterwards if you would rather the lines
stopped at the last real character.

It refuses a buffer with a tab anywhere in it. A tab is one character and
however many columns it takes to reach the next tab stop, so every width
measured on a line holding one would be wrong. Replace the tabs with the
spaces they stand for first: select the whole file and run expand through
Shell > Filter Selection.

It refuses a locked buffer too, since nothing written to one lands. XNEdit
locks a file it cannot read as UTF-8; File > Read Only and a file you cannot
write lock one too.

Rows whose field count differs from the first data row are padded as far as
they go and then reported, by count and first line number. No empty field is
invented to make a row fit, because a short row usually means a value went
missing upstream.

A second run finds the file already square and leaves it alone.

??? example "The macro body, ready to paste"

    ```
    # Arrays have to exist before "in" is used on them.
    keep = $empty_array
    cell = $empty_array
    clen = $empty_array
    count = $empty_array
    width = $empty_array

    ok = 1
    msg = ""
    n_rows = 0
    first_count = 0
    ragged = 0
    first_ragged = 0

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    if ($read_only == 1) {
        ok = 0
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    }

    if (ok == 1) {
        original = get_range(0, $text_length)

        # split() on "\n" yields one element per line plus a trailing empty element
        # when the buffer ends in a newline, so joining the elements back with "\n"
        # reproduces the buffer exactly. That is what lets the no-change case below
        # be a plain string comparison.
        lines = split(original, "\n", "case")
        n_lines = lines[]

        # A tab is one character and any number of columns, so a width measured on
        # a line holding one is not a width. Refusing here keeps tab stops out of
        # every measurement below.
        if (search_string(original, "\t", 0, "case") != -1) {
            ok = 0
            msg = $file_name " has a tab in it, so there is no telling which column "
            msg = msg "anything is in: a tab is one character and however many "
            msg = msg "columns it takes to reach the next tab stop.\n\nReplace the "
            msg = msg "tabs with the spaces they stand for first: select the whole "
            msg = msg "file and run expand through Shell > Filter Selection, which "
            msg = msg "leaves the columns where they sit on screen. Normalize "
            msg = msg "Characters takes tabs out too, but it writes one space for "
            msg = msg "each, which usually closes the columns up."
        }
    }

    # --- pass 1: split every row on "|" and measure each column -----------------

    if (ok == 1) {
        for (i = 0; i < n_lines; i++) {
            body = replace_in_string(lines[i], "^[ \t]+", "", "regex", "copy")
            body = replace_in_string(body, "[ \t]+$", "", "regex", "copy")

            # Blank lines and header lines are copied through verbatim,
            # indentation and all, and take no part in the column widths.
            if (body == "" || substring(body, 0, 1) == "#") {
                keep[i] = lines[i]
                continue
            }

            # Anything with no pipe in it goes the same way. A line with no
            # delimiter is not a table row, and reading a boundary out of a run of
            # spaces is the one thing this must never do.
            if (search_string(body, "|", 0, "case") == -1) {
                keep[i] = lines[i]
                continue
            }

            f = split(body, "|", "case")
            nf = f[]

            for (j = 0; j < nf; j++) {
                v = replace_in_string(f[j], "^[ \t]+", "", "regex", "copy")
                v = replace_in_string(v, "[ \t]+$", "", "regex", "copy")
                cell[i, j] = v

                # Measure the field in characters. length() counts bytes, and a
                # column holding an en dash or an accented name would then come out
                # one place short for every extra byte.
                #
                # "[ -~]+" is every printable ASCII character, so a run of them is
                # as many characters as it is bytes and measures in a single step.
                # Anything else advances one character at a time through a bare
                # ".", which is UTF-8 aware. Repetition is not: ".{n}", ".*" and
                # ".+" all count bytes, so none of them can appear here.
                p = 0
                w = 0

                while (p < length(v)) {
                    s = search_string(v, "[ -~]+", p, "regex")
                    if (s == p) {
                        w = w + ($search_end - p)
                    } else {
                        # "." matches everything except a newline, and split() has
                        # already taken every newline out, so this always advances.
                        search_string(v, ".", p, "regex")
                        w++
                    }
                    p = $search_end
                }

                clen[i, j] = w
                if (j in width) {
                    width[j] = max(width[j], w)
                } else {
                    width[j] = w
                }
            }
            count[i] = nf

            if (n_rows == 0) {
                first_count = nf
            } else if (nf != first_count) {
                if (ragged == 0) {
                    first_ragged = i + 1
                }
                ragged++
            }
            n_rows++
        }
    }

    # --- pass 2: rebuild the buffer ---------------------------------------------

    if (ok == 1) {
        # One run of spaces, long enough to pad the widest column with a single
        # substring() rather than a loop per field. Doubling gets there in a few
        # steps.
        max_width = 0
        for (j in width) {
            max_width = max(max_width, width[j])
        }
        pad = " "
        while (length(pad) < max_width) {
            pad = pad pad
        }

        out = ""
        chunk = ""

        for (i = 0; i < n_lines; i++) {
            if (i in keep) {
                chunk = chunk keep[i]
            } else {
                nf = count[i]
                for (j = 0; j < nf; j++) {
                    if (j > 0) {
                        chunk = chunk "|"
                    }
                    chunk = chunk cell[i, j] substring(pad, 0, width[j] - clen[i, j])
                }
            }
            if (i < n_lines - 1) {
                chunk = chunk "\n"
            }

            # Appending every line straight onto one growing string is quadratic:
            # each append copies everything written so far. Flushing a chunk every
            # 200 lines keeps a few thousand rows instant instead of a visible
            # stall.
            if (i % 200 == 199) {
                out = out chunk
                chunk = ""
            }
        }
        out = out chunk

        if (out != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, out)

            # Padding lengthens the buffer, but trimming the spaces a field came in
            # with can shorten it. Belt and braces: set_cursor_pos() clamps to the
            # end of the buffer itself, on XNEdit and on NEdit 5.7 alike, so no
            # test can reach the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }
    }

    # --- report -----------------------------------------------------------------

    if (ok == 0) {
        t_print("pad: " $file_name ": nothing changed\n")
    } else if (n_rows == 0) {
        t_print("pad: " $file_name ": no rows with a | in them, nothing to pad\n")
    } else {
        t_print("pad: " $file_name ": " n_rows " row(s), " width[] " column(s)\n")
    }

    if (ragged > 0) {
        msg = $file_name " has " ragged " row(s) whose field count differs from "
        msg = msg "the first data row, which has " first_count ". The first one is "
        msg = msg "on line " first_ragged ".\n\nThey were padded as far as they go "
        msg = msg "and no empty columns were invented. A short row usually means a "
        msg = msg "value went missing upstream, so check those rows before this "
        msg = msg "file goes anywhere."
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    ```

## Pipe at Columns

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Pipe at Columns` |
| Installed in | Macro Menu, Window Background Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/pipe-at-columns.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/pipe-at-columns.nm) |

Puts a "|" at each of several columns on every line of the file. It asks
which columns and how, then does the lot in one pass.

    NGC 4472   12:29:46.7   0.003326
    IC 3583    12:36:44.0   0.001155

Answering "10, 23" and choosing Overwrite gives

    NGC 4472  |12:29:46.7  |0.003326
    IC 3583   |12:36:44.0  |0.001155

Get the characters right first: a replacement that changes how many
characters are on a line moves every column to its right, so Normalize
Characters and Fold Letters to ASCII belong before this. Nothing here pads
the fields either; Pad Columns does that, last.

Type the columns separated by spaces or commas, in any order; repeats are
ignored. They count from 0, the numbering the C: field of the statistics line
uses, and the prompt names the column the cursor is in so you can read one
straight off the screen.

Two buttons, two ways of putting the pipe in:

| | Overwrite | Insert |
| --- | --- | --- |
| Needs a space at the column | yes | no |
| Row width | unchanged | one character wider per pipe |
| A second run | leaves the pipe alone | puts in more pipes |

So overwrite is the one for a table already laid out in fixed-width columns,
since it cannot move anything, and it is the one that repeats safely. Insert
loses nothing, so it reaches rows with no blank column to spare. It works
through the columns right to left, so every pipe lands at the column you
named rather than each one shifting the next along.

A second insert run does not settle. The leftmost pipe is found and left
alone, but every column after it has slid along by then, so each of those
gets a fresh pipe beside the one already there.

Five things it refuses rather than guesses at:

| What it refuses | Why |
| --- | --- |
| A locked buffer | Nothing written to one lands |
| Column 0 | A pipe there opens the table with an empty field |
| A tab anywhere in the buffer | One byte wide, any number of columns wide |
| Overwriting anything but a space | It would destroy that character |
| A row that ends before a column | Padding it out invents data |

The first three stop the command before it writes anything, and the locked
check runs before the prompt, so it does not ask which columns to pipe first.
The last two are per row: the rest of the file is piped, and the rows that
were skipped are counted with the first of them named. So read the report
before you go on. A skipped row usually means a column is a place or two off,
and a column that is blank on most rows can land inside a name like NGC 4472
on the one row where it is not.

XNEdit locks a file it cannot read as UTF-8; File > Read Only and a file you
cannot write lock one too. For tabs, replace them with the spaces they
stand for first: select the whole file and run expand through
Shell > Filter Selection.

Columns are counted as they are displayed, so an en dash counts as one column
though it takes three bytes.

For one column with no dialog in the way, use Pipe at Cursor Column.

??? example "The macro body, ready to paste"

    ```
    # --- prologue: ask which columns, and how -----------------------------------

    mode = "overwrite"
    cols = $empty_array
    ncols = 0
    ok = 0
    msg = ""

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    #
    # It goes here rather than in the shared block below, because the prompt is in
    # between: asking which columns to pipe and then refusing to pipe any of them
    # is worse than not asking.
    if ($read_only == 1) {
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    } else {
        # string_dialog() takes no default text, so the message is the only place
        # to put the current column.
        prompt = "Which columns should get a pipe?\n\n"
        prompt = prompt "Type the numbers separated by spaces or commas. They "
        prompt = prompt "count from 0, the way the C: field of the statistics line "
        prompt = prompt "counts, and the cursor is in column " $column " right "
        prompt = prompt "now.\n\n"
        prompt = prompt "Overwrite writes a pipe over the character at each "
        prompt = prompt "column, and only where that character is a space.\n\n"
        prompt = prompt "Insert puts the pipe in and pushes the rest of the line "
        prompt = prompt "right, which loses nothing but widens every row it "
        prompt = prompt "touches."

        answer = string_dialog(prompt, "Overwrite", "Insert", "Cancel")

        # Button 3 is Cancel and button 0 is the window manager's close button.
        # Both leave ok at 0, and so does anything else the dialog might return.
        if ($string_dialog_button == 1) {
            mode = "overwrite"
            ok = 1
        } else if ($string_dialog_button == 2) {
            mode = "insert"
            ok = 1
        }
    }

    if (ok == 1) {
        # Dedupe through an associative array, then insertion-sort. for (k in arr)
        # walks the keys as strings, where "10" sorts before "9", so it cannot do
        # the sorting.
        tokens = split(answer, "[ ,\t]+", "regex")
        n_tokens = tokens[]
        seen = $empty_array

        for (t = 0; t < n_tokens; t++) {
            word = tokens[t]

            # split() yields an empty token wherever a separator sits at either end
            # of the answer, and "" passes valid_number(), so drop those first.
            if (word != "") {
                if (valid_number(word) == 0) {
                    ok = 0
                    msg = "\"" word "\" is not a column number.\n\nType the columns "
                    msg = msg "as plain numbers separated by spaces or commas, like "
                    msg = msg "this: 10 23"
                    break
                }

                v = word + 0
                if (v < 1) {
                    ok = 0
                    msg = "Column " v " is not a place a pipe can go.\n\nColumns "
                    msg = msg "count from 0, and a pipe in column 0 would open the "
                    msg = msg "table with an empty field, so the first column that "
                    msg = msg "can take one is 1."
                    break
                }

                if ((v in seen) == 0) {
                    seen[v] = 1
                    m = ncols
                    while (m > 0 && cols[m - 1] > v) {
                        cols[m] = cols[m - 1]
                        m--
                    }
                    cols[m] = v
                    ncols++
                }
            }
        }
    }

    # An answer with no numbers in it at all is a change of mind rather than a
    # mistake, so it does nothing and says nothing about it.
    if (ok == 1 && ncols == 0) {
        ok = 0
    }

    # --- shared: column arithmetic ---
    #
    # Everything down to the end marker is byte-identical in
    # pipe-at-cursor-column.nm and pipe-at-columns.nm, and tests/test_conventions.py
    # keeps it that way. Change something here and paste the whole block into the
    # other file.
    #
    # The prologue above settles five things:
    #
    #   cols[0..ncols-1]  display columns to pipe, ascending, deduped, all >= 1
    #   ncols             how many
    #   mode              "overwrite" or "insert"
    #   ok                1 to go ahead, 0 if the prologue already refused
    #   msg               "" or the reason it refused

    n_rows = 0
    piped = 0
    occupied = 0
    first_occupied = 0
    too_short = 0
    first_too_short = 0

    if (ok == 1) {
        original = get_range(0, $text_length)

        # split() on "\n" yields one element per line plus a trailing empty element
        # when the buffer ends in a newline, so joining the elements back with "\n"
        # reproduces the buffer exactly. That is what lets the no-change case below
        # be a plain string comparison.
        lines = split(original, "\n", "case")
        n_lines = lines[]

        # A tab is one byte wide and any number of columns wide, so a buffer with
        # one in it cannot be reasoned about a column at a time. Refusing here is
        # what keeps tab stops out of every calculation that follows.
        if (search_string(original, "\t", 0, "case") != -1) {
            ok = 0
            msg = $file_name " has a tab in it, so there is no telling which column "
            msg = msg "anything is in: a tab is one character and however many "
            msg = msg "columns it takes to reach the next tab stop.\n\nReplace the "
            msg = msg "tabs with the spaces they stand for first: select the whole "
            msg = msg "file and run expand through Shell > Filter Selection, which "
            msg = msg "leaves the columns where they sit on screen. Normalize "
            msg = msg "Characters takes tabs out too, but it writes one space for "
            msg = msg "each, which usually closes the columns up."
        }
    }

    if (ok == 1) {
        out = ""
        chunk = ""

        for (i = 0; i < n_lines; i++) {
            line = lines[i]

            stripped = replace_in_string(line, "^[ \t]+", "", "regex", "copy")
            stripped = replace_in_string(stripped, "[ \t]+$", "", "regex", "copy")

            # Blank lines and header lines are copied through verbatim, so the
            # ##refcode block at the top of a NED file goes through untouched.
            if (stripped != "" && substring(stripped, 0, 1) != "#") {
                n_rows++

                # Resolve every target column to a byte offset in one left-to-right
                # walk, because byte offsets and display columns only agree while
                # the line is ASCII. An en dash is three bytes and one column.
                #
                # "[ -~]+" is every printable ASCII character, so a run of them is
                # as many characters as it is bytes and resolves in a single step.
                # Anything else advances one character at a time through a bare
                # ".", which is UTF-8 aware. Repetition is not: ".{n}", ".*" and
                # ".+" all count bytes, so none of them can appear here.
                off = $empty_array
                p = 0
                col = 0
                j = 0

                while (j < ncols && p < length(line)) {
                    s = search_string(line, "[ -~]+", p, "regex")
                    if (s == p) {
                        run = $search_end - p
                        while (j < ncols && cols[j] < col + run) {
                            off[j] = p + (cols[j] - col)
                            j++
                        }
                        col = col + run
                        p = $search_end
                    } else {
                        # "." matches everything except a newline, and split() has
                        # already taken every newline out, so this always advances.
                        search_string(line, ".", p, "regex")
                        if (j < ncols && cols[j] == col) {
                            off[j] = p
                            j++
                        }
                        col++
                        p = $search_end
                    }
                }

                # A column the walk never reached is one past the end of this line.
                # Apply right to left, so inserting a pipe never shifts an offset
                # that has not been used yet.
                occupied_here = 0
                short_here = 0

                for (k = ncols - 1; k >= 0; k--) {
                    if (k in off) {
                        o = off[k]
                        here = substring(line, o, o + 1)

                        # A pipe already in place is left alone, which is what
                        # makes a second run over the same columns do nothing.
                        if (here != "|") {
                            if (mode == "insert") {
                                line = replace_substring(line, o, o, "|")
                                piped++
                            } else if (here == " ") {
                                # A space is one byte whatever else is on the line,
                                # so writing over one never has to ask how wide the
                                # character was.
                                line = replace_substring(line, o, o + 1, "|")
                                piped++
                            } else {
                                occupied_here = 1
                            }
                        }
                    } else {
                        short_here = 1
                    }
                }

                if (occupied_here == 1) {
                    if (occupied == 0) {
                        first_occupied = i + 1
                    }
                    occupied++
                }
                if (short_here == 1) {
                    if (too_short == 0) {
                        first_too_short = i + 1
                    }
                    too_short++
                }
            }

            chunk = chunk line
            if (i < n_lines - 1) {
                chunk = chunk "\n"
            }

            # Appending every line straight onto one growing string is quadratic:
            # each append copies everything written so far. Flushing a chunk every
            # 200 lines keeps a few thousand rows instant instead of a visible
            # stall.
            if (i % 200 == 199) {
                out = out chunk
                chunk = ""
            }
        }
        out = out chunk

        if (out != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, out)

            # Inserting lengthens the buffer and overwriting leaves it the same
            # length, but clamp rather than reason about which happened. Belt and
            # braces: set_cursor_pos() clamps to the end of the buffer itself, on
            # XNEdit and on NEdit 5.7 alike, so no test can reach the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }
    }

    # --- report ----------------------------------------------------------------

    if (ok == 0) {
        t_print("pipe: " $file_name ": nothing changed\n")
    } else if (n_rows == 0) {
        t_print("pipe: " $file_name ": no data rows, nothing to pipe\n")
    } else {
        t_print("pipe: " $file_name ": " piped " pipe(s) into " n_rows " row(s)\n")
    }

    if (occupied > 0) {
        if (msg != "") {
            msg = msg "\n\n"
        }
        msg = msg $file_name " has " occupied " row(s) holding something other than "
        msg = msg "a space at one of those columns, and they were left as they are. "
        msg = msg "The first is on line " first_occupied ".\n\nOverwriting there "
        msg = msg "would have destroyed a character. Either the column is a place "
        msg = msg "or two off, or those rows are wider than the rest, so read them "
        msg = msg "before this file goes any further."
    }

    if (too_short > 0) {
        if (msg != "") {
            msg = msg "\n\n"
        }
        msg = msg $file_name " has " too_short " row(s) that end before one of those "
        msg = msg "columns, so no pipe went in at that column. The first is on line "
        msg = msg first_too_short ".\n\nNothing was padded out to reach it, because a "
        msg = msg "padded row invents data. If those rows should have carried a "
        msg = msg "value there, it went missing upstream."
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    # --- end shared ---
    ```

## Pipe at Cursor Column

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Pipe at Cursor Column` |
| Installed in | Macro Menu, Window Background Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/pipe-at-cursor-column.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/pipe-at-cursor-column.nm) |

Puts a "|" at the cursor's column on every line of the file, over the space
that is already there. Point at a boundary in a fixed-width table, run this,
and every line gets a delimiter at that column.

    NGC 4472   12:29:46.7   0.003326
    IC 3583    12:36:44.0   0.001155

with the cursor on the blank column in front of 12:29 becomes

    NGC 4472  |12:29:46.7   0.003326
    IC 3583   |12:36:44.0   0.001155

Run it once per boundary, and get the characters right first: a replacement
that changes how many characters are on a line moves every column to its
right, so Normalize Characters and Fold Letters to ASCII belong before this.
Nothing here pads the fields either; Pad Columns does that, last.

The column is the one the statistics line calls C:, counting from 0.
Preferences > Statistics Line puts that number on screen while you aim.
Right-clicking does not move the cursor, so left-click the column first when
you run this from the background menu.

Five things it refuses rather than guesses at:

| What it refuses | Why |
| --- | --- |
| A locked buffer | Nothing written to one lands |
| Column 0 | A pipe there opens the table with an empty field |
| A tab anywhere in the buffer | One byte wide, any number of columns wide |
| A row with anything but a space there | Overwriting destroys a character |
| A row that ends before the column | Padding it out invents data |

The first three stop the command before it writes anything. The last two are
per row: the rest of the file is piped, and the rows that were skipped are
counted with the first of them named. So read the report before you go on. A
skipped row usually means the column is a place or two off, and a column that
is blank on most rows can land inside a name like NGC 4472 on the one row
where it is not.

XNEdit locks a file it cannot read as UTF-8; File > Read Only and a file you
cannot write lock one too. For tabs, replace them with the spaces they
stand for first: select the whole file and run expand through
Shell > Filter Selection.

Columns are counted as they are displayed, so an en dash counts as one column
though it takes three bytes.

For several columns at once, or to push the line right instead of writing
over the space, use Pipe at Columns.

??? example "The macro body, ready to paste"

    ```
    # --- prologue: the single column the cursor is sitting in -------------------

    mode = "overwrite"
    cols = $empty_array
    ncols = 0
    ok = 1
    msg = ""

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    #
    # $column is the display column counting from 0, the same number the C: field
    # of the statistics line shows.
    if ($read_only == 1) {
        ok = 0
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    } else if ($column == 0) {
        ok = 0
        msg = "The cursor is in column 0, at the very start of the line.\n\nA pipe "
        msg = msg "there would open the table with an empty field. Put the cursor "
        msg = msg "in the column you want the pipe to land in and run this again."
    } else {
        cols[0] = $column
        ncols = 1
    }

    # --- shared: column arithmetic ---
    #
    # Everything down to the end marker is byte-identical in
    # pipe-at-cursor-column.nm and pipe-at-columns.nm, and tests/test_conventions.py
    # keeps it that way. Change something here and paste the whole block into the
    # other file.
    #
    # The prologue above settles five things:
    #
    #   cols[0..ncols-1]  display columns to pipe, ascending, deduped, all >= 1
    #   ncols             how many
    #   mode              "overwrite" or "insert"
    #   ok                1 to go ahead, 0 if the prologue already refused
    #   msg               "" or the reason it refused

    n_rows = 0
    piped = 0
    occupied = 0
    first_occupied = 0
    too_short = 0
    first_too_short = 0

    if (ok == 1) {
        original = get_range(0, $text_length)

        # split() on "\n" yields one element per line plus a trailing empty element
        # when the buffer ends in a newline, so joining the elements back with "\n"
        # reproduces the buffer exactly. That is what lets the no-change case below
        # be a plain string comparison.
        lines = split(original, "\n", "case")
        n_lines = lines[]

        # A tab is one byte wide and any number of columns wide, so a buffer with
        # one in it cannot be reasoned about a column at a time. Refusing here is
        # what keeps tab stops out of every calculation that follows.
        if (search_string(original, "\t", 0, "case") != -1) {
            ok = 0
            msg = $file_name " has a tab in it, so there is no telling which column "
            msg = msg "anything is in: a tab is one character and however many "
            msg = msg "columns it takes to reach the next tab stop.\n\nReplace the "
            msg = msg "tabs with the spaces they stand for first: select the whole "
            msg = msg "file and run expand through Shell > Filter Selection, which "
            msg = msg "leaves the columns where they sit on screen. Normalize "
            msg = msg "Characters takes tabs out too, but it writes one space for "
            msg = msg "each, which usually closes the columns up."
        }
    }

    if (ok == 1) {
        out = ""
        chunk = ""

        for (i = 0; i < n_lines; i++) {
            line = lines[i]

            stripped = replace_in_string(line, "^[ \t]+", "", "regex", "copy")
            stripped = replace_in_string(stripped, "[ \t]+$", "", "regex", "copy")

            # Blank lines and header lines are copied through verbatim, so the
            # ##refcode block at the top of a NED file goes through untouched.
            if (stripped != "" && substring(stripped, 0, 1) != "#") {
                n_rows++

                # Resolve every target column to a byte offset in one left-to-right
                # walk, because byte offsets and display columns only agree while
                # the line is ASCII. An en dash is three bytes and one column.
                #
                # "[ -~]+" is every printable ASCII character, so a run of them is
                # as many characters as it is bytes and resolves in a single step.
                # Anything else advances one character at a time through a bare
                # ".", which is UTF-8 aware. Repetition is not: ".{n}", ".*" and
                # ".+" all count bytes, so none of them can appear here.
                off = $empty_array
                p = 0
                col = 0
                j = 0

                while (j < ncols && p < length(line)) {
                    s = search_string(line, "[ -~]+", p, "regex")
                    if (s == p) {
                        run = $search_end - p
                        while (j < ncols && cols[j] < col + run) {
                            off[j] = p + (cols[j] - col)
                            j++
                        }
                        col = col + run
                        p = $search_end
                    } else {
                        # "." matches everything except a newline, and split() has
                        # already taken every newline out, so this always advances.
                        search_string(line, ".", p, "regex")
                        if (j < ncols && cols[j] == col) {
                            off[j] = p
                            j++
                        }
                        col++
                        p = $search_end
                    }
                }

                # A column the walk never reached is one past the end of this line.
                # Apply right to left, so inserting a pipe never shifts an offset
                # that has not been used yet.
                occupied_here = 0
                short_here = 0

                for (k = ncols - 1; k >= 0; k--) {
                    if (k in off) {
                        o = off[k]
                        here = substring(line, o, o + 1)

                        # A pipe already in place is left alone, which is what
                        # makes a second run over the same columns do nothing.
                        if (here != "|") {
                            if (mode == "insert") {
                                line = replace_substring(line, o, o, "|")
                                piped++
                            } else if (here == " ") {
                                # A space is one byte whatever else is on the line,
                                # so writing over one never has to ask how wide the
                                # character was.
                                line = replace_substring(line, o, o + 1, "|")
                                piped++
                            } else {
                                occupied_here = 1
                            }
                        }
                    } else {
                        short_here = 1
                    }
                }

                if (occupied_here == 1) {
                    if (occupied == 0) {
                        first_occupied = i + 1
                    }
                    occupied++
                }
                if (short_here == 1) {
                    if (too_short == 0) {
                        first_too_short = i + 1
                    }
                    too_short++
                }
            }

            chunk = chunk line
            if (i < n_lines - 1) {
                chunk = chunk "\n"
            }

            # Appending every line straight onto one growing string is quadratic:
            # each append copies everything written so far. Flushing a chunk every
            # 200 lines keeps a few thousand rows instant instead of a visible
            # stall.
            if (i % 200 == 199) {
                out = out chunk
                chunk = ""
            }
        }
        out = out chunk

        if (out != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, out)

            # Inserting lengthens the buffer and overwriting leaves it the same
            # length, but clamp rather than reason about which happened. Belt and
            # braces: set_cursor_pos() clamps to the end of the buffer itself, on
            # XNEdit and on NEdit 5.7 alike, so no test can reach the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }
    }

    # --- report ----------------------------------------------------------------

    if (ok == 0) {
        t_print("pipe: " $file_name ": nothing changed\n")
    } else if (n_rows == 0) {
        t_print("pipe: " $file_name ": no data rows, nothing to pipe\n")
    } else {
        t_print("pipe: " $file_name ": " piped " pipe(s) into " n_rows " row(s)\n")
    }

    if (occupied > 0) {
        if (msg != "") {
            msg = msg "\n\n"
        }
        msg = msg $file_name " has " occupied " row(s) holding something other than "
        msg = msg "a space at one of those columns, and they were left as they are. "
        msg = msg "The first is on line " first_occupied ".\n\nOverwriting there "
        msg = msg "would have destroyed a character. Either the column is a place "
        msg = msg "or two off, or those rows are wider than the rest, so read them "
        msg = msg "before this file goes any further."
    }

    if (too_short > 0) {
        if (msg != "") {
            msg = msg "\n\n"
        }
        msg = msg $file_name " has " too_short " row(s) that end before one of those "
        msg = msg "columns, so no pipe went in at that column. The first is on line "
        msg = msg first_too_short ".\n\nNothing was padded out to reach it, because a "
        msg = msg "padded row invents data. If those rows should have carried a "
        msg = msg "value there, it went missing upstream."
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    # --- end shared ---
    ```

## Trim Trailing Blanks

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Trim Trailing Blanks` |
| Installed in | Macro Menu |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/trim-trailing-blanks.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/trim-trailing-blanks.nm) |

Removes trailing spaces and tabs from every line in the buffer. Leaves the
file and the undo history alone when there is nothing to trim. Either way it
says what it did in the terminal xnedit was launched from.

It refuses a locked buffer, since nothing written to one lands. XNEdit locks
a file it cannot read as UTF-8; File > Read Only and a file you cannot write
lock one too.

??? example "The macro body, ready to paste"

    ```
    ok = 1
    msg = ""
    n_trimmed = 0

    # A locked buffer takes no writes. replace_range() on one does nothing and says
    # nothing, so everything below would be computed and thrown away and the
    # summary would name an edit that never happened. $read_only is the test and
    # not $locked: $locked misses a file with no write permission, while $read_only
    # is the same condition replace_range() itself refuses on.
    if ($read_only == 1) {
        ok = 0
        msg = $file_name " is locked, so nothing was changed.\n\nXNEdit locks a "
        msg = msg "file it cannot read as UTF-8, which is the usual reason. "
        msg = msg "File > Read Only locks a buffer too, and so does a file with "
        msg = msg "no write permission."
    }

    if (ok == 1) {
        original = get_range(0, $text_length)

        # The "copy" argument is doing real work here. Without it
        # replace_in_string() returns an empty string when the pattern matches
        # nothing, and the replace_range() below would then erase the entire file.
        trimmed = replace_in_string(original, "[ \t]+$", "", "regex", "copy")

        if (trimmed != original) {
            saved_cursor = $cursor
            replace_range(0, $text_length, trimmed)

            # The buffer just got shorter, so the old offset may now be past the
            # end. Belt and braces: set_cursor_pos() clamps to the end of the
            # buffer itself, on XNEdit and on NEdit 5.7 alike, so no test can reach
            # the line below.
            if (saved_cursor > $text_length) {
                saved_cursor = $text_length
            }
            set_cursor_pos(saved_cursor)
        }

        # Count the lines that had blanks on the end of them, in the text as it
        # came in. "$" anchors to the end of a line rather than the end of the
        # string, so every match is one line, and $search_end is past the blanks it
        # matched, which is what makes the search walk forward.
        pos = search_string(original, "[ \t]+$", 0, "regex")
        while (pos != -1) {
            n_trimmed++
            pos = search_string(original, "[ \t]+$", $search_end, "regex")
        }
    }

    # --- report -----------------------------------------------------------------

    if (ok == 0) {
        t_print("trim: " $file_name ": nothing changed\n")
    } else if (n_trimmed == 0) {
        t_print("trim: " $file_name ": nothing to trim\n")
    } else {
        t_print("trim: " $file_name ": " n_trimmed " line(s) trimmed\n")
    }

    if (msg != "") {
        dialog(msg, "OK")
    }
    ```

<!-- END GENERATED: commands -->
