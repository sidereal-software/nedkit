# XNEdit macro language reference

A condensed reference for writing macros in this repo, covering the things you
need every day. Read [the official
docs](https://www.unixwork.de/xnedit/doc/html/xnedit.html) for anything subtle.

XNEdit's macro language descends from NEdit 5.7, so NEdit macros found in the
wild generally work unchanged.

## Read this first

These behaviors account for most of the time people lose.

**There is no floating point.** Integers are 32-bit signed, from -2147483647 to
2147483647, and that is the only numeric type. Redshifts, coordinates, and flux
values cannot be computed in a macro. Shell out with `shell_command()` or move
the work to Python.

**`replace_in_string()` returns the empty string when nothing matched.** Not the
original. So this deletes the buffer whenever there is nothing to trim:

```
# WRONG. Wipes the file if there are no trailing blanks.
replace_range(0, $text_length, replace_in_string(get_range(0, $text_length), "[ \t]+$", "", "regex"))
```

Passing `"copy"` makes it return the input unchanged instead. It can go in the
fourth argument or the fifth, because the call scans every trailing argument for
it:

```
replace_in_string(text, "[ \t]+$", "", "regex", "copy")   # with a search type
replace_in_string(text, "\xc3\xa9", "e", "copy")          # without one
```

**With no search type, matching is case-insensitive.**
`replace_in_string("HELLO", "l", "-")` gives `HE--O`. The default type is
`"literal"`, which is the plain search with the Case Sensitive box unticked, so
a table keyed on one case of a letter fires on both until you pass `"case"`.
That bites hardest in a replacement table: `fold-letters-to-ascii.nm` carries
both cases of every Greek letter, and without `"case"` the entry for `α` would
answer for `Α` as well. An unrecognised type is a hard error rather than a
silent fallback, so the trap is only ever a type you left out, never one you
misspelled.

**Backslashes are consumed twice.** The string literal is unescaped first, then
the result goes to the regex engine. A regex `\s` is written `"\\s"`. A regex
matching a literal `*` is `"\\*"`.

**`define` cannot nest,** cannot appear inside a menu item definition, and is
not accepted in a `-do` string either: `xnedit -do 'define f { ... }' file`
stops on an error dialog whatever the body is. A definition has to arrive
through `autoload.nm` or Load Macro File. Subroutines belong in `macros/lib/`,
which is loaded through `autoload.nm` at startup.

**Positions are character offsets from 0,** not line and column. `$text_length`
is the offset one past the last character.

## Syntax

Statements end at a newline. Braces group them. `#` starts a comment that runs
to end of line. A trailing backslash continues a long statement.

```
# A comment.
x = 1
if (x > 0) {
    t_print("positive\n")
}
```

## Types

Three of them: integers, dynamic strings, and associative arrays. Integers and
strings convert into each other freely in most contexts. Concatenation is
juxtaposition, with no operator:

```
message = "found " count " matches"
```

String literals take C escapes: `\\ \t \n \r \b \f \v \a \" \e`, plus octal
(`\33`) and hex (`\x1B`).

### Arrays

Keys are always strings. Values can be integers, strings, or arrays.

```
a["key"] = "value"
n = a[]                    # element count, no index
for (k in a) t_print(k "\n")
delete a["key"]
delete a[]                 # clear
if ("key" in a) { }
```

Multi-dimensional keys are sugar over a single string joined by `$sub_sep`
(ASCII 0x1C):

```
x[1, 2] = "v"              # really x["1" $sub_sep "2"]
```

That detail leaks: `if ((1,2) in myArray)` does not work, but
`if (("1" $sub_sep "2") in myArray)` does.

Arrays support set operations on their keys: `+` merge, `-` difference, `&`
intersection, `|` symmetric difference. Both operands must be arrays.

## Variables

A leading letter makes a variable local to its subroutine or menu item. A
leading `$` makes it global and persistent across calls. No declarations;
assignment brings a variable into existence.

## Control flow

C syntax throughout, including `break` and `continue`.

```
for (i = 0; i < 100; i++)
    j = i * 2

for (i = 0, j = 20; i < 20; i++, j--) {
    t_print(i, j, "\n")
}

while (k > 0) {
    k--
}

if (a) {
    x = 1
} else {
    x = 2
}
```

**A brace and the statement after it cannot share a line.** Statements end at a
newline, so `while (k > 0) { k-- }` is a syntax error, and under `xnedit -do`
that arrives as a modal dialog rather than a message. Every `{` gets a newline
after it.

`&&` and `||` short-circuit left to right. Evaluation order for other operators
is undefined, so don't lean on side effects inside an expression.

## Operators

Precedence and meaning follow C with one exception: **`^` raises to a power**
rather than doing bitwise XOR. `y ^ x` is y to the x. There is no XOR operator.

In decreasing precedence: `()` `^` / unary `-` `!` `++` `--` / `*` `/` `%` /
`+` `-` / `>` `>=` `<` `<=` `==` `!=` / `&` / `|` / `&&` / `||` /
concatenation / assignment.

`&` and `|` are bitwise on integers and set operations on arrays. `==` and `!=`
compare strings as well as integers, which is what makes the
"did anything change" check in `trim-trailing-blanks.nm` work. Concatenation
has no operator at all, and binds loosest of anything but assignment:

```
message = "found " count " matches"
```

## Subroutines

```
define ned_trim_end {
    if ($n_args < 1) {
        return ""
    }
    return replace_in_string($1, "[ \t]+$", "", "regex", "copy")
}
```

Arguments arrive as `$1` through `$9`, or `$args[n]` for arbitrary counts, with
`$n_args` holding the count. `return` takes an optional value.

## Built-in variables

**Buffer and file**

`$file_name` `$file_path` `$text_length` `$modified` `$read_only` `$locked`
`$file_format` `$language_mode`

**Cursor and selection**

`$cursor` `$line` `$column` `$selection_start` `$selection_end`
`$selection_left` `$selection_right` `$search_end`

`$selection_start` is -1 when nothing is selected. `$selection_left` and
`$selection_right` apply to rectangular selections.

**Window and display**

`$top_line` `$n_display_lines` `$display_width` `$active_pane` `$n_panes`
`$empty_array` `$server_name`

**Settings**

`$auto_indent` `$em_tab_dist` `$tab_dist` `$use_tabs` `$wrap_text`
`$wrap_margin` `$overtype_mode` `$highlight_syntax` `$show_line_numbers`
`$show_matching` `$match_syntax_based` `$statistics_line`
`$incremental_search_line` `$incremental_backup` `$make_backup_copy`
`$font_name` `$font_name_bold` `$font_name_italic` `$font_name_bold_italic`
`$max_font_width` `$min_font_width`

**Status from the last call**

`$read_status` (from `read_file`), `$shell_cmd_status` (from `shell_command`),
`$string_dialog_button`, `$list_dialog_button`, `$sub_sep`

## Built-in subroutines

**Reading the buffer**

```
get_range(start, end)
get_character(position)
get_selection()
```

**Changing the buffer**

```
replace_range(start, end, string)
replace_selection(string)
set_cursor_pos(position)
select(start, end)
select_rectangle(start, end, left, right)
select_to_matching()
revert_to_saved()
focus_window(window_name)
```

**Strings**

```
length(string)
substring(string, start [, end])
replace_substring(string, start, end, replace_with)
replace_in_string(string, search_for, replace_with [, type, "copy"])
split(string, separation_string [, search_type])
string_compare(string1, string2 [, consider-case])
toupper(string)      # ASCII only. See the warning below
tolower(string)      # ASCII only. See the warning below
valid_number(string)
max(n1, n2, ...)
min(n1, n2, ...)
```

`split()` returns an array indexed from 0.

!!! danger "`toupper()` and `tolower()` destroy non-ASCII text"

    On XNEdit 1.6.3 the 8 bytes of `αβ Éx` come back from `toupper()` as the 5
    bytes `\xce\xce \xc3X`. Every multi-byte character has lost its
    continuation byte and what is left is not valid UTF-8. `tolower()` on the
    same string returns a single byte. Put that in the buffer and the save
    stops on a modal dialog that never closes, with the file on disk already
    truncated to nothing.

    The `uppercase()` and `lowercase()` action routines get the same string
    right, because the code behind them sets `LC_CTYPE` and measures each
    character before converting it, which `toupper()` and `tolower()` do not.
    So change case with the action routine, or leave the case alone.

    Measured on 1.6.3. Upstream changed that code after the v1.6.3 tag, in
    commit `c5b1120`, so a later release will not necessarily fail the same
    way. Check before trusting it on anything but ASCII.

**Searching**

```
search(search_for, start [, search_type, wrap, direction])
search_string(string, search_for, start [, search_type, direction])
```

`search_type` is one of `"literal"`, `"case"`, `"word"`, `"caseWord"`,
`"regex"`, `"regexNoCase"`, defaulting to `"literal"`. Both return the match
start or -1, and set `$search_end`.

**`"literal"` is case-insensitive.** The case-sensitive plain search is
`"case"`; `"literal"` is the one with the Case Sensitive box unticked, and it
is also the default when you leave `search_type` off. The same names mean the
same things in `replace_in_string()` and `replace_all()`.

That matters beyond letter case. XNEdit folds `"literal"` case over UTF-8
rather than over bytes, and some characters change length when folded:
uppercasing the `fi` ligature U+FB01 gives the two characters `FI`. So a
`"literal"` search for a multi-byte character can match text you did not
intend. Use `"case"` whenever you are matching exact bytes.

The other insensitive types do not reach that far. Searching `É` for `é` on
XNEdit 1.6.3:

| Type | Folds ASCII case | Folds non-ASCII case |
| --- | --- | --- |
| `"literal"` | yes | yes |
| `"case"` | no | no |
| `"word"` | yes | no |
| `"caseWord"` | no | no |
| `"regex"` | no | no |
| `"regexNoCase"` | yes | no |

`"regexNoCase"` folds one byte at a time, through `tolower()` guarded by
`isalpha()`, so a multi-byte character is not something it can see at all.
`"word"` is version-specific: a change to whole-word searching for strings
whose length differs between cases landed upstream after the v1.6.3 tag, in
commit `8c6cebc`, so check that row again on the next release.

**Files and shell**

```
read_file(filename)          # sets $read_status
write_file(string, filename)
append_file(string, filename)
shell_command(command, input_string)   # sets $shell_cmd_status
getenv(name)
```

`shell_command()` is the escape hatch for anything the macro language can't do,
floating point arithmetic very much included.

**Dialogs and output**

```
dialog(message, btn_1_label, btn_2_label, ...)
string_dialog(message, btn_1_label, ...)      # sets $string_dialog_button
list_dialog(message, text, btn_1_label, ...)  # sets $list_dialog_button
filename_dialog([title[, mode[, defaultPath[, filter[, defaultName]]]]])
calltip("text_or_key" [, pos [, mode ...]])
kill_calltip([calltip_ID])
beep()
t_print(string1, string2, ...)
```

`t_print()` writes to the terminal XNEdit was started from and buffers by line,
so include an explicit `"\n"`. It is the closest thing to a debugger here.

**Clipboard**

```
string_to_clipboard(string)
clipboard_to_string()
```

**Rangesets** let you tag and track regions of the buffer as it changes, which
is useful for multi-pass parsing work. See
[the rangeset docs](https://www.unixwork.de/xnedit/doc/html/rangeset.html).

## Action routines

Anything bound to a key or menu item is callable from a macro. The common ones:

`new()` `open()` `open_dialog()` `open_selected()` `close()` `save()`
`save_as()` `save_as_dialog()` `revert_to_saved_dialog()` `print()`
`print_selection()` `exit()` `include_file()` `include_file_dialog()`

`cut_clipboard()` `copy_clipboard()` `paste_clipboard()` `delete()`
`delete_selection()` `select_all()` `deselect_all()` `undo()` `redo()`

`beginning_of_selection()` `end_of_selection()` `forward_character()`
`newline()` `newline_and_indent()` `newline_no_indent()` `self_insert()`
`process_tab()` `process_return()` `process_cancel()`

`uppercase()` `lowercase()` `fill_paragraph()` `shift_left()` `shift_right()`
`shift_left_by_tab()` `shift_right_by_tab()`

`load_macro_file()` `load_macro_file_dialog()` `load_tags_file()`
`load_tips_file()` `unload_tags_file()` `unload_tips_file()`

Full list in [the action routines
docs](https://www.unixwork.de/xnedit/doc/html/actions.html).

### Multi-cursor

XNEdit adds multi-cursor editing, which classic NEdit does not have. Ctrl and
left-click adds a cursor; Escape returns to one. These actions apply at every
cursor:

`delete_next_character()` `delete_previous_character()` `delete_next_word()`
`delete_previous_word()` `forward_character()` `backward_character()`
`forward_word()` `backward_word()` `forward_paragraph()` `backward_paragraph()`
`insert_string()` `self_insert()` `newline()` `process_tab()` `process_up()`
`process_down()` `beginning_of_line()` `end_of_line()`

Selection and column paste do not support multiple cursors.

## Regular expressions

Mostly Perl-flavored. Anchors are `^` beginning of line, `$` end of line, `<`
and `>` word boundaries, `\B` not a word boundary. Because `^` and `$` are line
anchors rather than string anchors, a pattern like `"[ \t]+$"` applied to the
whole buffer trims every line in one pass.

Remember the double-escaping rule when writing these as macro strings. Details
in [the regex
docs](https://www.unixwork.de/xnedit/doc/html/basicSyntax.html).

### A bare `.` counts characters, repeating it counts bytes

`.` matches one whole UTF-8 character, however many bytes that takes. Repeat it
and that stops being true: `.{n}`, `.*` and `.+` all go through the engine's
`greedy()` path, which advances a byte at a time. It is not only `greedy()`.
The quantifier machinery around it backtracks with `Reg_Input = save +
num_matched` (`regularExp.c:3429`), which is the same assumption of one byte
per repetition.

`.{1}` is the exception, and only because it is not a repetition by the time it
runs: `regularExp.c:1063` optimises `x{1,1}` away entirely, leaving a bare `x`.
So `^.{1}$` matches a three-byte character and `^.{2}$` does not, while
`^.{3}$` does.

So this looks like it puts a pipe at column 24, and does not:

```
# WRONG on any line holding a non-ASCII character.
replace_in_string(line, "^(.{24})", "\\1|", "regex", "copy")
```

On an ASCII line the two counts agree and it is correct. On a line carrying an
en dash, three bytes for one character, the pipe lands two places early and
possibly inside the dash, so the bug shows up on real data and not on the file
you tested with. Count the characters yourself instead: match runs of `[ -~]`,
where a byte is a character, and step over everything else with a single bare
`.`. `pipe-at-cursor-column.nm` does that.

A character class counts bytes whether it is repeated or not, and a multi-byte
character written inside one is taken apart into its bytes: `^[é]$` does not
match `é`, and `^[é]{2}$` does. That does not break the `[ -~]+` walk above,
because every member of that class is one byte, so leave that pattern alone.

`$column` sits on the character side of this divide. It is the display column,
counting a multi-byte character as one and expanding a tab to the next tab
stop, and it is the same number the statistics line shows as `C:`. `length()`,
`substring()` and `get_character()` sit on the byte side, and `get_character()`
can hand you half of a character. Both sides are right about their own
question; mixing them produces the off-by-two.

The one place `$column` and the statistics line part company is when the
position is not in the displayed text, which in practice means continuous wrap
with the cursor scrolled off screen. The stats line goes to `C: ---` there,
because the call behind it fails rather than returning a column. `$column`
answers from the buffer and returns a number regardless, so a macro reading it
is on the safer side of the two.

Two more things about a bare `.`, both of which matter once you are stepping
with it: it never matches a newline, and on a byte that is not valid UTF-8 it
believes the lead byte anyway, so it can step clean past the end of a string
that is not valid text.

None of this is XNEdit adding a hazard. NEdit 5.7 counts bytes in a bare `.`
too, and the character-aware `.` is the one Unicode change XNEdit has made to
the 4178-line regex engine, in commit `732c8ab`. That single difference is why
the macros here put a pipe in a different place on the two editors whenever a
line holds a non-ASCII character, and why the column fixtures carry an
`xnedit-only` marker.

## Fixed-size limits

Six compile-time constants that a macro can reach. None of them are in the
official docs, and they are the same in XNEdit 1.6.3 and NEdit 5.7, since 5.7
is where all six come from.

| Constant | Value | What hits it |
| --- | --- | --- |
| `PROGRAM_SIZE` | 4096 instructions | A single compiled macro |
| `SEARCHMAX` | 5119 bytes | The pattern of a literal or case search |
| `MAX_ITEMS_PER_MENU` | 400 items | Each of the Macro, Shell and background menus |
| `STACK_SIZE` | 1024 | The interpreter's value stack |
| `MAX_SYM_LEN` | 100 characters | A variable or subroutine name |
| `LOOP_STACK_SIZE` | 200 | `break` and `continue` statements per program |

The first two are the ones that turn up in practice.

**4096 instructions** is per compiled macro, and every way of getting a macro
into the editor goes through the same parser: `-do`, a menu command out of
`nedit.rc`, `autoload.nm`, Load Macro File. Over the limit it is refused at
parse time with `macro too large`, naming the line it stopped on. Each `define`
compiles separately and gets its own 4096. A table assignment such as
`fix["\xe2\x80\x93"] = "-"` costs 9 instructions, so 455 of them fill a `-do`
body and 456 are refused; inside a `define` it is 454, because `return` takes
the last slot. That is what a big replacement table has to be budgeted against.

**5119 bytes** is the more dangerous one, because nothing tells you. A
`"literal"` or `"case"` search whose pattern is 5119 bytes or longer returns
-1, the same answer as a pattern that genuinely is not there. 5118 bytes
matches; 5119 does not. Regex searches do not go through that path and are not
affected. The source comment is blunt about it: the limit "should be done away
with now that searching can be done from macros without limits. Returning
search failure here is cheating users. This limit is not documented."

## Developing and testing

XNEdit ships no test harness, so out of the box you have:

- `t_print()` for tracing, visible in the terminal that launched XNEdit.
- **Macro > Learn Keystrokes**, then **Macro > Replay**, to capture a sequence
  and see it as macro text.
- **Macro > Load Macro File** to run a `.nm` file without installing anything.
- `xnedit -do 'command' file` to run a macro from the shell, and
  `xnc -do 'command'` against a running `xnedit -server` session.

This repo builds on that last one: every command is run through a real XNEdit
and the buffer compared byte for byte against a fixture. See
[running the tests](testing.md) for how to build an editor to test against and
how to add a case.

Always try a destructive macro on a copy first. Macros edit the buffer directly
and a wrong regex is quiet about it.
