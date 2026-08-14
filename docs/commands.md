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
    # XNEdit has nothing that expands a tab to the spaces it stands for, so when the
    # columns have to survive, select the file and run expand through
    # Shell > Filter Selection instead of this.
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

Nothing here pads the fields afterwards, so the file comes out delimited
rather than squared up.

Type the columns separated by spaces or commas, in any order; repeats are
ignored. They count from 0, the numbering the C: field of the statistics line
uses, and the prompt names the column the cursor is in so you can read one
straight off the screen.

Two buttons, two ways of putting the pipe in:

  - Overwrite writes over the character at that column, and only where that
    character is a space. Use this on a table already laid out in fixed-width
    columns, since it leaves every row the width it was.
  - Insert puts the pipe in and pushes the rest of the line right. Nothing is
    lost, so it reaches rows with no blank column to spare, at the price of
    one character of width on every row it touches.

Insert works through the columns right to left, so every pipe lands at the
column you named rather than each one shifting the next along. It also means
a second run inserts a second set of pipes. Overwrite can be run again
safely; multi-column insert cannot.

Four things it refuses rather than guesses at:

  - Column 0. A pipe at the start of a line opens the table with an empty
    field, which is never what a fixed-width table wants.
  - Under Overwrite, a row holding anything but a space at one of those
    columns. Overwriting there would destroy a character, and a column that
    is blank on most rows can land inside a name like NGC 4472 on one. Those
    rows are counted and the first is named.
  - A row that ends before one of those columns. Padding it out would invent
    data.
  - A buffer with a tab anywhere in it, because a tab is one byte wide and
    any number of columns wide. Replace the tabs with the spaces they stand
    for first: select the whole file and run expand through
    Shell > Filter Selection.

So read the report before you go on. A skipped row usually means a column is
a place or two off.

Columns are counted as they are displayed, so an en dash counts as one column
though it takes three bytes. That holds for anything XNEdit can decode; on a
file it cannot, the count drifts, but XNEdit locks such a file against
editing anyway.

For one column with no dialog in the way, use Pipe at Cursor Column.

??? example "The macro body, ready to paste"

    ```
    mode = "overwrite"
    cols = $empty_array
    ncols = 0
    ok = 0
    msg = ""

    # string_dialog() takes no default text, so the message is the only place to
    # put the current column.
    prompt = "Which columns should get a pipe?\n\n"
    prompt = prompt "Type the numbers separated by spaces or commas. They count "
    prompt = prompt "from 0, the way the C: field of the statistics line counts, "
    prompt = prompt "and the cursor is in column " $column " right now.\n\n"
    prompt = prompt "Overwrite writes a pipe over the character at each column, "
    prompt = prompt "and only where that character is a space.\n\n"
    prompt = prompt "Insert puts the pipe in and pushes the rest of the line right, "
    prompt = prompt "which loses nothing but widens every row it touches."

    answer = string_dialog(prompt, "Overwrite", "Insert", "Cancel")

    # Button 3 is Cancel and button 0 is the window manager's close button. Both
    # leave ok at 0, and so does anything else the dialog might return.
    if ($string_dialog_button == 1) {
        mode = "overwrite"
        ok = 1
    } else if ($string_dialog_button == 2) {
        mode = "insert"
        ok = 1
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
            # length, but clamp rather than reason about which happened.
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

Run it once per boundary. Nothing here pads the fields afterwards, so the
file comes out delimited rather than squared up.

The column is the one the statistics line calls C:, counting from 0.
Preferences > Statistics Line puts that number on screen while you aim.
Right-clicking does not move the cursor, so left-click the column first when
you run this from the background menu.

Four things it refuses rather than guesses at:

  - Column 0. A pipe at the start of a line opens the table with an empty
    field, which is never what a fixed-width table wants.
  - A row holding anything but a space at that column. Overwriting there
    would destroy a character, and a column that is blank on most rows can
    land inside a name like NGC 4472 on one. Those rows are counted and the
    first is named.
  - A row that ends before that column. Padding it out would invent data.
  - A buffer with a tab anywhere in it, because a tab is one byte wide and
    any number of columns wide. Replace the tabs with the spaces they stand
    for first: select the whole file and run expand through
    Shell > Filter Selection.

So read the report before you go on. A skipped row usually means the column
is a place or two off.

Columns are counted as they are displayed, so an en dash counts as one column
though it takes three bytes. That holds for anything XNEdit can decode; on a
file it cannot, the count drifts, but XNEdit locks such a file against
editing anyway.

For several columns at once, or to push the line right instead of writing
over the space, use Pipe at Columns.

??? example "The macro body, ready to paste"

    ```
    mode = "overwrite"
    cols = $empty_array
    ncols = 0
    ok = 1
    msg = ""

    # $column is the display column counting from 0, the same number the C: field
    # of the statistics line shows.
    if ($column == 0) {
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
            # length, but clamp rather than reason about which happened.
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
