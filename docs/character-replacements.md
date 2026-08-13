# Character replacements

Everything [Normalize Characters](commands.md#normalize-characters) rewrites,
and everything it deliberately does not.

Text pasted out of a PDF is full of characters that look like ASCII on screen
and are not. A declination that reads `-00:46:03.66` may actually start with
U+2013 EN DASH, and nothing downstream that expects a minus sign will match it.

The table below is generated from the macro itself by `tools/gen_docs.py`, so
the two cannot drift apart. Add a character to the macro, run the script, and
this page follows.

## Whitespace

Handled outside the character table.

| What | Becomes | Note |
| --- | --- | --- |
| Tab | One space | Not tab-stop aware. Use **Edit > Untabify** when the columns have to survive, or run [Align Columns](commands.md#align-columns) first. |
| CR LF | LF | A DOS-format file never shows these, because XNEdit strips carriage returns on open and restores them on save. A pasted block can still carry them into a Unix-format buffer. |
| Lone CR | LF | Same reason. |

## The character table

<!-- BEGIN GENERATED: character-table -->

73 characters, every one of them replaced by plain ASCII.

### Dashes and hyphens

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `‐` | U+2010 | HYPHEN | `-` |
| `‑` | U+2011 | NON-BREAKING HYPHEN | `-` |
| `‒` | U+2012 | FIGURE DASH | `-` |
| `–` | U+2013 | EN DASH | `-` |
| `—` | U+2014 | EM DASH | `-` |
| `―` | U+2015 | HORIZONTAL BAR | `-` |
| `⁃` | U+2043 | HYPHEN BULLET | `-` |
| `−` | U+2212 | MINUS SIGN | `-` |
| `﹘` | U+FE58 | SMALL EM DASH | `-` |
| `﹣` | U+FE63 | SMALL HYPHEN-MINUS | `-` |
| `－` | U+FF0D | FULLWIDTH HYPHEN-MINUS | `-` |

### Single quotes, apostrophes, primes

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `´` | U+00B4 | ACUTE ACCENT | `'` |
| `ʹ` | U+02B9 | MODIFIER LETTER PRIME | `'` |
| `ʼ` | U+02BC | MODIFIER LETTER APOSTROPHE | `'` |
| `‘` | U+2018 | LEFT SINGLE QUOTATION MARK | `'` |
| `’` | U+2019 | RIGHT SINGLE QUOTATION MARK | `'` |
| `‚` | U+201A | SINGLE LOW-9 QUOTATION MARK | `'` |
| `‛` | U+201B | SINGLE HIGH-REVERSED-9 QUOTATION MARK | `'` |
| `′` | U+2032 | PRIME | `'` |
| `‵` | U+2035 | REVERSED PRIME | `'` |
| `＇` | U+FF07 | FULLWIDTH APOSTROPHE | `'` |

### Double quotes and double primes

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `ʺ` | U+02BA | MODIFIER LETTER DOUBLE PRIME | `"` |
| `“` | U+201C | LEFT DOUBLE QUOTATION MARK | `"` |
| `”` | U+201D | RIGHT DOUBLE QUOTATION MARK | `"` |
| `„` | U+201E | DOUBLE LOW-9 QUOTATION MARK | `"` |
| `‟` | U+201F | DOUBLE HIGH-REVERSED-9 QUOTATION MARK | `"` |
| `″` | U+2033 | DOUBLE PRIME | `"` |
| `‶` | U+2036 | REVERSED DOUBLE PRIME | `"` |
| `＂` | U+FF02 | FULLWIDTH QUOTATION MARK | `"` |

### Spaces

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| (not printable) | U+00A0 | NO-BREAK SPACE | a space |
| (not printable) | U+1680 | OGHAM SPACE MARK | a space |
| (not printable) | U+2000 | EN QUAD | a space |
| (not printable) | U+2001 | EM QUAD | a space |
| (not printable) | U+2002 | EN SPACE | a space |
| (not printable) | U+2003 | EM SPACE | a space |
| (not printable) | U+2004 | THREE-PER-EM SPACE | a space |
| (not printable) | U+2005 | FOUR-PER-EM SPACE | a space |
| (not printable) | U+2006 | SIX-PER-EM SPACE | a space |
| (not printable) | U+2007 | FIGURE SPACE | a space |
| (not printable) | U+2008 | PUNCTUATION SPACE | a space |
| (not printable) | U+2009 | THIN SPACE | a space |
| (not printable) | U+200A | HAIR SPACE | a space |
| (not printable) | U+202F | NARROW NO-BREAK SPACE | a space |
| (not printable) | U+205F | MEDIUM MATHEMATICAL SPACE | a space |
| (not printable) | U+3000 | IDEOGRAPHIC SPACE | a space |

### Invisible characters, deleted outright

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| (not printable) | U+00AD | SOFT HYPHEN | removed |
| (not printable) | U+200B | ZERO WIDTH SPACE | removed |
| (not printable) | U+200C | ZERO WIDTH NON-JOINER | removed |
| (not printable) | U+200D | ZERO WIDTH JOINER | removed |
| (not printable) | U+2060 | WORD JOINER | removed |
| (not printable) | U+FEFF | ZERO WIDTH NO-BREAK SPACE (BOM) | removed |

### Line separators

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| (not printable) | U+2028 | LINE SEPARATOR | a newline |
| (not printable) | U+2029 | PARAGRAPH SEPARATOR | a newline |

### Ligatures

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `ﬀ` | U+FB00 | LATIN SMALL LIGATURE FF | `ff` |
| `ﬁ` | U+FB01 | LATIN SMALL LIGATURE FI | `fi` |
| `ﬂ` | U+FB02 | LATIN SMALL LIGATURE FL | `fl` |
| `ﬃ` | U+FB03 | LATIN SMALL LIGATURE FFI | `ffi` |
| `ﬄ` | U+FB04 | LATIN SMALL LIGATURE FFL | `ffl` |
| `ﬅ` | U+FB05 | LATIN SMALL LIGATURE LONG S T | `st` |
| `ﬆ` | U+FB06 | LATIN SMALL LIGATURE ST | `st` |

### Other punctuation

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `•` | U+2022 | BULLET | `*` |
| `…` | U+2026 | HORIZONTAL ELLIPSIS | `...` |
| `×` | U+00D7 | MULTIPLICATION SIGN | `x` |
| `÷` | U+00F7 | DIVISION SIGN | `/` |
| `⁄` | U+2044 | FRACTION SLASH | `/` |
| `∕` | U+2215 | DIVISION SLASH | `/` |

### Math relations

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `±` | U+00B1 | PLUS-MINUS SIGN | `+/-` |
| `∓` | U+2213 | MINUS-OR-PLUS SIGN | `-/+` |
| `≈` | U+2248 | ALMOST EQUAL TO | `~` |
| `∼` | U+223C | TILDE OPERATOR | `~` |
| `≠` | U+2260 | NOT EQUAL TO | `!=` |
| `≤` | U+2264 | LESS-THAN OR EQUAL TO | `<=` |
| `≥` | U+2265 | GREATER-THAN OR EQUAL TO | `>=` |

<!-- END GENERATED: character-table -->

## What is left alone

Anything with no safe ASCII spelling stays exactly as it is. Guessing would
quietly corrupt data, which is worse than leaving a character that at least
looks wrong.

| Character | Why it stays |
| --- | --- |
| `°` U+00B0 DEGREE SIGN | `deg`, `d` and `o` all appear in real files. Picking one would silently change what the number means. |
| `α` `β` `μ` Greek letters | Spelling them out as `alpha` changes field widths and is wrong inside a name. |
| `µ` U+00B5 MICRO SIGN | The same shape as Greek mu but a different character, and `u` is not always the right reading. |
| `é` `á` `ñ` accented letters | Author and observatory names. Stripping the accent corrupts the name. |
| `≪` `≫` `∝` `≃` and other relations not in the table | Add them if your files use them consistently. |
| Bytes that are not valid UTF-8 | A lone byte such as `0x96` may be a Windows-1252 en dash, or it may be the remains of a truncated character. Replacing it blind would corrupt any multi-byte character that happens to contain that byte. |

The macro does not stay quiet about these. After it runs it counts what is
left, puts the cursor on the first one, and lists them in a dialog with a count
per character, so each case can be decided by hand.

## What is deliberately not automated

A `##refcode` of `2026A+A...707A..13L` should read `2026A&A...707A..13L`. That
is a plain ASCII `+` standing in for `&`, not an encoding problem, and it is
not in the table on purpose: a blanket `+` to `&` replacement would destroy
every positive declination in the file. Fix refcodes by hand.

## Adding a character

Two lines in the table in `macros/commands/normalize-characters.nm`, keyed on
the UTF-8 bytes of the character:

```
fix["\xe2\x80\x93"] = "-"
nam["\xe2\x80\x93"] = "U+2013 EN DASH"
```

Get the bytes with:

```sh
python3 -c 'print("".join("\\x%02x" % b for b in chr(0x2013).encode()))'
```

Then regenerate this page:

```sh
python3 tools/gen_docs.py
```

Keys are written as escapes rather than as literal characters so the macro
survives being pasted through the Customize Menus dialog, and so the entries
you cannot see stay readable in the source. Order does not matter, because
every replacement is ASCII and no entry can feed another.

Keep the layout of the table as it is. The group heading is the comment line
directly above a `fix[...]` line with no blank line between them, and that is
how `tools/gen_docs.py` tells a heading apart from ordinary prose earlier in
the file.

Two things to watch if you edit the macro itself:

- The search type must stay `"case"`. NEdit's `"literal"` is case-insensitive,
  and XNEdit folds case over UTF-8, where uppercasing the `fi` ligature gives
  the two characters `FI`. A `"literal"` search for a multi-byte character can
  match text you never intended.
- `replace_in_string()` needs its `"copy"` argument. Without it the call
  returns an empty string whenever the pattern does not match, and the loop
  would erase the buffer on its first miss.
