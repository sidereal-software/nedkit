# XNEdit macro language reference

A condensed reference for writing macros in this repo. It is not a replacement
for [the official docs](https://www.unixwork.de/xnedit/doc/html/xnedit.html),
which you should read for anything subtle. This page exists so you don't have to
go looking for the ninety percent of things you need every day.

XNEdit's macro language descends from NEdit 5.7, so NEdit macros found in the
wild generally work unchanged.

## Read this first

These five behaviors account for most of the time people lose.

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

Passing `"copy"` as the fifth argument makes it return the input unchanged
instead:

```
replace_in_string(text, "[ \t]+$", "", "regex", "copy")
```

**Backslashes are consumed twice.** The string literal is unescaped first, then
the result goes to the regex engine. A regex `\s` is written `"\\s"`. A regex
matching a literal `*` is `"\\*"`.

**`define` cannot nest,** and cannot appear inside a menu item definition.
Subroutines belong in `macros/lib/`, which is loaded through `autoload.nm` at
startup.

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
define ned_example {
    if ($n_args < 1) {
        return ""
    }
    return toupper($1)
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
toupper(string)
tolower(string)
valid_number(string)
max(n1, n2, ...)
min(n1, n2, ...)
```

`split()` returns an array indexed from 0.

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

That matters beyond letter case. XNEdit folds case over UTF-8, not over bytes,
and some characters change length when folded - uppercasing the `fi` ligature
U+FB01 gives the two characters `FI`. A `"literal"` search for a multi-byte
character can therefore match text you did not intend. Use `"case"` whenever
you are matching exact bytes.

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
`greedy()` path, which advances a byte at a time.

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

`$column` sits on the character side of this divide. It is the display column,
counting a multi-byte character as one and expanding a tab to the next tab
stop, and it is the same number the statistics line shows as `C:`. `length()`,
`substring()` and `get_character()` sit on the byte side, and `get_character()`
can hand you half of a character. Both sides are right about their own
question; mixing them produces the off-by-two.

Two more things about a bare `.`, both of which matter once you are stepping
with it: it never matches a newline, and on a byte that is not valid UTF-8 it
believes the lead byte anyway, so it can step clean past the end of a string
that is not valid text.

## Developing and testing

There is no test harness. What you have:

- `t_print()` for tracing, visible in the terminal that launched XNEdit.
- **Macro → Learn Keystrokes**, then **Macro → Replay**, to capture a sequence
  and see it as macro text.
- **Macro → Load Macro File** to run a `.nm` file without installing anything.
- `xnedit -do 'command' file` to run a macro from the shell, and
  `xnc -do 'command'` against a running `xnedit -server` session.

Always try a destructive macro on a copy first. Macros edit the buffer directly
and a wrong regex is quiet about it.
