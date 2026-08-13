# Commands

Every macro command in `macros/commands/`. [Installing
macros](installing-macros.md) covers how to get one into the Macro menu; the
table on each command below carries the values the dialog asks for, and the
body is folded away underneath ready to copy.

This page is generated from the macro files by `tools/gen_docs.py`, so it
cannot drift away from what the macros actually do.

<!-- BEGIN GENERATED: commands -->

## Align Columns

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Align Columns` |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/align-columns.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/align-columns.nm) |

Turns whitespace-separated columns into NED's pipe-delimited table format:
fields joined with "|", each one padded with spaces to the width of the
widest value in its column, so the columns line up when you read the file.

    SDSS001009<TAB>00:10:09.97<TAB>-00:46:03.66<TAB>0.2431
    SDSS004054<TAB>00:40:54.33<TAB>15:34:09.66<TAB>0.2832

becomes

    SDSS001009|00:10:09.97|-00:46:03.66|0.2431
    SDSS004054|00:40:54.33|15:34:09.66 |0.2832

Blank lines and lines starting with "#" are left exactly as they are, so the
\##refcode / ##type1 header block at the top of a NED file passes through
untouched and does not get counted when measuring column widths.

How a line gets split into fields, first match wins:

  1. contains "|"   split on "|", then trim each field
  2. contains a tab  split on the tab
  3. otherwise       split on runs of spaces and tabs

Run this first, and then again as the very last thing you do to the file.

First, because rule 2 needs the tabs. Normalize Characters turns every tab
into a single space, and once that has happened there is no delimiter left:
rule 3 takes over and cuts every field that contains a space into several,
while a field that was empty disappears into the gap. Running this first
turns the tabs into pipes, and rule 1 then holds those boundaries through
everything that comes after.

Last, because the widths are only right until the next edit. Anything that
changes a value changes the width of its column, and that includes Normalize
Characters: length() counts bytes, so an en dash measures three where it
prints one, and rows containing one come out two characters too wide until
the dashes are gone and this is run again.

So: align, clean up, read it through, align again.

Every column is padded, including the last, so each row comes out the same
length. Run Trim Trailing Blanks afterwards if you would rather the lines
ended at the last real character.

Rows whose field count differs from the first data row are still aligned as
far as they go, but they get reported rather than quietly padded out - a
short row usually means a value went missing upstream.

??? example "The macro body, ready to paste"

    ```
    original = get_range(0, $text_length)

    # split() on "\n" yields one element per line plus a trailing empty element
    # when the buffer ends in a newline, so joining the elements back with "\n"
    # reproduces the buffer exactly. That is what lets the no-change case below be
    # a plain string comparison.
    lines = split(original, "\n", "case")
    n_lines = lines[]

    # Arrays have to exist before "in" is used on them.
    keep = $empty_array
    cell = $empty_array
    count = $empty_array
    width = $empty_array

    n_rows = 0
    first_count = 0
    ragged = 0
    first_ragged = 0

    # --- pass 1: split every line into fields and measure each column -----------

    for (i = 0; i < n_lines; i++) {
        body = replace_in_string(lines[i], "^[ \t]+", "", "regex", "copy")
        body = replace_in_string(body, "[ \t]+$", "", "regex", "copy")

        # Blank lines and header lines are copied through verbatim, indentation
        # and all, and take no part in the column widths.
        if (body == "" || substring(body, 0, 1) == "#") {
            keep[i] = lines[i]
            continue
        }

        if (search_string(body, "|", 0, "case") != -1) {
            f = split(body, "|", "case")
        } else if (search_string(body, "\t", 0, "case") != -1) {
            f = split(body, "\t", "case")
        } else {
            f = split(body, "[ \t]+", "regex")
        }

        nf = f[]
        for (j = 0; j < nf; j++) {
            v = replace_in_string(f[j], "^[ \t]+", "", "regex", "copy")
            v = replace_in_string(v, "[ \t]+$", "", "regex", "copy")
            cell[i, j] = v
            if (j in width) {
                width[j] = max(width[j], length(v))
            } else {
                width[j] = length(v)
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

    # --- pass 2: rebuild the buffer --------------------------------------------

    # One run of spaces, long enough to pad the widest column with a single
    # substring() rather than a loop per field. Doubling gets there in a few steps.
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
                v = cell[i, j]
                chunk = chunk v substring(pad, 0, width[j] - length(v))
            }
        }
        if (i < n_lines - 1) {
            chunk = chunk "\n"
        }

        # Appending every line straight onto one growing string is quadratic:
        # each append copies everything written so far. Flushing a chunk every
        # 200 lines keeps a few thousand rows instant instead of a visible stall.
        if (i % 200 == 199) {
            out = out chunk
            chunk = ""
        }
    }
    out = out chunk

    if (out != original) {
        saved_cursor = $cursor
        replace_range(0, $text_length, out)

        # Padding makes the buffer longer, but a re-align can shorten it.
        if (saved_cursor > $text_length) {
            saved_cursor = $text_length
        }
        set_cursor_pos(saved_cursor)
    }

    # --- report ----------------------------------------------------------------

    if (n_rows == 0) {
        t_print("align: " $file_name ": no data rows, nothing to align\n")
    } else {
        t_print("align: " $file_name ": " n_rows " row(s), " width[] " column(s)\n")
    }

    if (ragged > 0) {
        msg = $file_name " has " ragged " row(s) whose field count differs from "
        msg = msg "the first data row, which has " first_count ". The first one is "
        msg = msg "on line " first_ragged ".\n\nThey were aligned as far as they "
        msg = msg "go and no empty columns were invented. A short row usually "
        msg = msg "means a value went missing upstream, so check those rows "
        msg = msg "before this file goes anywhere."
        dialog(msg, "OK")
    }
    ```

## Normalize Characters

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Normalize Characters` |
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
says so in a dialog. Nothing is changed silently and nothing hides.

A run that finds nothing leaves the buffer, the undo history and the
modified flag untouched.

??? example "The macro body, ready to paste"

    ```
    original = get_range(0, $text_length)
    cleaned = original
    fixed = ""

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

    # Stray carriage returns. A DOS-format file never shows these - XNEdit strips
    # them on open and puts them back on save - but a pasted block can carry them
    # into a Unix-format buffer.
    if (search_string(cleaned, "\r", 0, "case") != -1) {
        cleaned = replace_in_string(cleaned, "\r\n", "\n", "case", "copy")
        cleaned = replace_in_string(cleaned, "\r", "\n", "case", "copy")
        fixed = fixed "  carriage return -> newline\n"
    }

    # Tabs. One tab becomes one space, which does not preserve column alignment.
    # Use Edit > Untabify (Shift+Ctrl+Tab) instead when the columns matter.
    if (search_string(cleaned, "\t", 0, "case") != -1) {
        cleaned = replace_in_string(cleaned, "\t", " ", "case", "copy")
        fixed = fixed "  tab -> space\n"
    }

    # The table itself. Skipped outright on a buffer that is already pure ASCII,
    # which turns the common case into one scan instead of one per entry.
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

        # The buffer usually got shorter, so the old offset may be past the end.
        if (saved_cursor > $text_length) {
            saved_cursor = $text_length
        }
        set_cursor_pos(saved_cursor)
    }

    # What is still not ASCII. Counted per character, capped so that a buffer of
    # mostly non-Latin text cannot turn this into a long stall.
    left = $empty_array
    n_left = 0
    first_left = -1
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

    # Report. t_print() goes to the terminal that launched xnedit, so the routine
    # case stays quiet; the dialog is reserved for the case that wants a human.
    if (fixed == "") {
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
        dialog(msg, "OK")
    }
    ```

## Trim Trailing Blanks

| Setting | Value |
| --- | --- |
| Menu entry | `NED>Trim Trailing Blanks` |
| Accelerator | (none) |
| Requires a selection | no |
| Source | [`macros/commands/trim-trailing-blanks.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/trim-trailing-blanks.nm) |

Removes trailing spaces and tabs from every line in the buffer. Leaves the
file and the undo history alone when there is nothing to trim.

??? example "The macro body, ready to paste"

    ```
    original = get_range(0, $text_length)

    # The "copy" argument is doing real work here. Without it replace_in_string()
    # returns an empty string when the pattern matches nothing, and the
    # replace_range() below would then erase the entire file.
    trimmed = replace_in_string(original, "[ \t]+$", "", "regex", "copy")

    if (trimmed != original) {
        saved_cursor = $cursor
        replace_range(0, $text_length, trimmed)

        # The buffer just got shorter, so the old offset may now be past the end.
        if (saved_cursor > $text_length) {
            saved_cursor = $text_length
        }
        set_cursor_pos(saved_cursor)
    }
    ```

<!-- END GENERATED: commands -->
