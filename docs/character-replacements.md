# Character replacements

Everything the two rewriting commands replace, and everything they deliberately
do not.

Text pasted out of a PDF is full of characters that look like ASCII on screen
and are not. A declination that reads `-00:46:03.66` may actually start with
U+2013 EN DASH, and nothing downstream that expects a minus sign will match it.

The work is split across two commands, and which one you want depends on the
character:

| Command | Replaces | Run it |
| --- | --- | --- |
| [Normalize Characters](commands.md#normalize-characters) | Dashes, quotes, spaces, ligatures, math relations, invisible characters | First. It also takes out tabs and stray carriage returns. |
| [Fold Letters to ASCII](commands.md#fold-letters-to-ascii) | Accented Latin letters and Greek letters | After Normalize Characters, and only when you want the letters flattened. |

They are separate commands because flattening `Balázs` to `Balazs` is a
decision about your data rather than a typographic cleanup, and because one
table of 313 characters does not fit in the 4096 instructions a macro gets.

Run Normalize Characters on its own and it reports the accented and Greek
letters in its "no safe ASCII spelling" dialog, which is the nudge toward the
second command.

The tables below are generated from the macros themselves by
`tools/gen_docs.py`, so they cannot drift apart.

## Whitespace

Handled by Normalize Characters, outside the character table.

| What | Becomes | Note |
| --- | --- | --- |
| Tab | One space | Not tab-stop aware, so the columns close up. When the layout has to survive, run [Expand Tabs](commands.md#expand-tabs) instead: it writes the spaces each tab stands for. See [cleaning up a pasted table](cleaning-pdf-tables.md#tabs-have-to-go-first). |
| CR LF | LF | A DOS-format file never shows these, because XNEdit strips carriage returns on open and restores them on save. A pasted block can still carry them into a Unix-format buffer. |
| Lone CR | LF | Same reason. |

## The character tables

<!-- BEGIN GENERATED: character-table -->

### Fold Letters to ASCII

240 characters, every one of them replaced by plain ASCII. From [`macros/commands/fold-letters-to-ascii.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/fold-letters-to-ascii.nm).

#### Accented capitals, Latin-1 Supplement

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `À` | U+00C0 | LATIN CAPITAL LETTER A WITH GRAVE | `A` |
| `Á` | U+00C1 | LATIN CAPITAL LETTER A WITH ACUTE | `A` |
| `Â` | U+00C2 | LATIN CAPITAL LETTER A WITH CIRCUMFLEX | `A` |
| `Ã` | U+00C3 | LATIN CAPITAL LETTER A WITH TILDE | `A` |
| `Ä` | U+00C4 | LATIN CAPITAL LETTER A WITH DIAERESIS | `A` |
| `Å` | U+00C5 | LATIN CAPITAL LETTER A WITH RING ABOVE | `A` |
| `Ç` | U+00C7 | LATIN CAPITAL LETTER C WITH CEDILLA | `C` |
| `È` | U+00C8 | LATIN CAPITAL LETTER E WITH GRAVE | `E` |
| `É` | U+00C9 | LATIN CAPITAL LETTER E WITH ACUTE | `E` |
| `Ê` | U+00CA | LATIN CAPITAL LETTER E WITH CIRCUMFLEX | `E` |
| `Ë` | U+00CB | LATIN CAPITAL LETTER E WITH DIAERESIS | `E` |
| `Ì` | U+00CC | LATIN CAPITAL LETTER I WITH GRAVE | `I` |
| `Í` | U+00CD | LATIN CAPITAL LETTER I WITH ACUTE | `I` |
| `Î` | U+00CE | LATIN CAPITAL LETTER I WITH CIRCUMFLEX | `I` |
| `Ï` | U+00CF | LATIN CAPITAL LETTER I WITH DIAERESIS | `I` |
| `Ð` | U+00D0 | LATIN CAPITAL LETTER ETH | `D` |
| `Ñ` | U+00D1 | LATIN CAPITAL LETTER N WITH TILDE | `N` |
| `Ò` | U+00D2 | LATIN CAPITAL LETTER O WITH GRAVE | `O` |
| `Ó` | U+00D3 | LATIN CAPITAL LETTER O WITH ACUTE | `O` |
| `Ô` | U+00D4 | LATIN CAPITAL LETTER O WITH CIRCUMFLEX | `O` |
| `Õ` | U+00D5 | LATIN CAPITAL LETTER O WITH TILDE | `O` |
| `Ö` | U+00D6 | LATIN CAPITAL LETTER O WITH DIAERESIS | `O` |
| `Ø` | U+00D8 | LATIN CAPITAL LETTER O WITH STROKE | `O` |
| `Ù` | U+00D9 | LATIN CAPITAL LETTER U WITH GRAVE | `U` |
| `Ú` | U+00DA | LATIN CAPITAL LETTER U WITH ACUTE | `U` |
| `Û` | U+00DB | LATIN CAPITAL LETTER U WITH CIRCUMFLEX | `U` |
| `Ü` | U+00DC | LATIN CAPITAL LETTER U WITH DIAERESIS | `U` |
| `Ý` | U+00DD | LATIN CAPITAL LETTER Y WITH ACUTE | `Y` |

#### Accented small letters, Latin-1 Supplement

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `à` | U+00E0 | LATIN SMALL LETTER A WITH GRAVE | `a` |
| `á` | U+00E1 | LATIN SMALL LETTER A WITH ACUTE | `a` |
| `â` | U+00E2 | LATIN SMALL LETTER A WITH CIRCUMFLEX | `a` |
| `ã` | U+00E3 | LATIN SMALL LETTER A WITH TILDE | `a` |
| `ä` | U+00E4 | LATIN SMALL LETTER A WITH DIAERESIS | `a` |
| `å` | U+00E5 | LATIN SMALL LETTER A WITH RING ABOVE | `a` |
| `ç` | U+00E7 | LATIN SMALL LETTER C WITH CEDILLA | `c` |
| `è` | U+00E8 | LATIN SMALL LETTER E WITH GRAVE | `e` |
| `é` | U+00E9 | LATIN SMALL LETTER E WITH ACUTE | `e` |
| `ê` | U+00EA | LATIN SMALL LETTER E WITH CIRCUMFLEX | `e` |
| `ë` | U+00EB | LATIN SMALL LETTER E WITH DIAERESIS | `e` |
| `ì` | U+00EC | LATIN SMALL LETTER I WITH GRAVE | `i` |
| `í` | U+00ED | LATIN SMALL LETTER I WITH ACUTE | `i` |
| `î` | U+00EE | LATIN SMALL LETTER I WITH CIRCUMFLEX | `i` |
| `ï` | U+00EF | LATIN SMALL LETTER I WITH DIAERESIS | `i` |
| `ð` | U+00F0 | LATIN SMALL LETTER ETH | `d` |
| `ñ` | U+00F1 | LATIN SMALL LETTER N WITH TILDE | `n` |
| `ò` | U+00F2 | LATIN SMALL LETTER O WITH GRAVE | `o` |
| `ó` | U+00F3 | LATIN SMALL LETTER O WITH ACUTE | `o` |
| `ô` | U+00F4 | LATIN SMALL LETTER O WITH CIRCUMFLEX | `o` |
| `õ` | U+00F5 | LATIN SMALL LETTER O WITH TILDE | `o` |
| `ö` | U+00F6 | LATIN SMALL LETTER O WITH DIAERESIS | `o` |
| `ø` | U+00F8 | LATIN SMALL LETTER O WITH STROKE | `o` |
| `ù` | U+00F9 | LATIN SMALL LETTER U WITH GRAVE | `u` |
| `ú` | U+00FA | LATIN SMALL LETTER U WITH ACUTE | `u` |
| `û` | U+00FB | LATIN SMALL LETTER U WITH CIRCUMFLEX | `u` |
| `ü` | U+00FC | LATIN SMALL LETTER U WITH DIAERESIS | `u` |
| `ý` | U+00FD | LATIN SMALL LETTER Y WITH ACUTE | `y` |
| `ÿ` | U+00FF | LATIN SMALL LETTER Y WITH DIAERESIS | `y` |

#### Latin Extended-A

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `Ā` | U+0100 | LATIN CAPITAL LETTER A WITH MACRON | `A` |
| `ā` | U+0101 | LATIN SMALL LETTER A WITH MACRON | `a` |
| `Ă` | U+0102 | LATIN CAPITAL LETTER A WITH BREVE | `A` |
| `ă` | U+0103 | LATIN SMALL LETTER A WITH BREVE | `a` |
| `Ą` | U+0104 | LATIN CAPITAL LETTER A WITH OGONEK | `A` |
| `ą` | U+0105 | LATIN SMALL LETTER A WITH OGONEK | `a` |
| `Ć` | U+0106 | LATIN CAPITAL LETTER C WITH ACUTE | `C` |
| `ć` | U+0107 | LATIN SMALL LETTER C WITH ACUTE | `c` |
| `Ĉ` | U+0108 | LATIN CAPITAL LETTER C WITH CIRCUMFLEX | `C` |
| `ĉ` | U+0109 | LATIN SMALL LETTER C WITH CIRCUMFLEX | `c` |
| `Ċ` | U+010A | LATIN CAPITAL LETTER C WITH DOT ABOVE | `C` |
| `ċ` | U+010B | LATIN SMALL LETTER C WITH DOT ABOVE | `c` |
| `Č` | U+010C | LATIN CAPITAL LETTER C WITH CARON | `C` |
| `č` | U+010D | LATIN SMALL LETTER C WITH CARON | `c` |
| `Ď` | U+010E | LATIN CAPITAL LETTER D WITH CARON | `D` |
| `ď` | U+010F | LATIN SMALL LETTER D WITH CARON | `d` |
| `Đ` | U+0110 | LATIN CAPITAL LETTER D WITH STROKE | `D` |
| `đ` | U+0111 | LATIN SMALL LETTER D WITH STROKE | `d` |
| `Ē` | U+0112 | LATIN CAPITAL LETTER E WITH MACRON | `E` |
| `ē` | U+0113 | LATIN SMALL LETTER E WITH MACRON | `e` |
| `Ĕ` | U+0114 | LATIN CAPITAL LETTER E WITH BREVE | `E` |
| `ĕ` | U+0115 | LATIN SMALL LETTER E WITH BREVE | `e` |
| `Ė` | U+0116 | LATIN CAPITAL LETTER E WITH DOT ABOVE | `E` |
| `ė` | U+0117 | LATIN SMALL LETTER E WITH DOT ABOVE | `e` |
| `Ę` | U+0118 | LATIN CAPITAL LETTER E WITH OGONEK | `E` |
| `ę` | U+0119 | LATIN SMALL LETTER E WITH OGONEK | `e` |
| `Ě` | U+011A | LATIN CAPITAL LETTER E WITH CARON | `E` |
| `ě` | U+011B | LATIN SMALL LETTER E WITH CARON | `e` |
| `Ĝ` | U+011C | LATIN CAPITAL LETTER G WITH CIRCUMFLEX | `G` |
| `ĝ` | U+011D | LATIN SMALL LETTER G WITH CIRCUMFLEX | `g` |
| `Ğ` | U+011E | LATIN CAPITAL LETTER G WITH BREVE | `G` |
| `ğ` | U+011F | LATIN SMALL LETTER G WITH BREVE | `g` |
| `Ġ` | U+0120 | LATIN CAPITAL LETTER G WITH DOT ABOVE | `G` |
| `ġ` | U+0121 | LATIN SMALL LETTER G WITH DOT ABOVE | `g` |
| `Ģ` | U+0122 | LATIN CAPITAL LETTER G WITH CEDILLA | `G` |
| `ģ` | U+0123 | LATIN SMALL LETTER G WITH CEDILLA | `g` |
| `Ĥ` | U+0124 | LATIN CAPITAL LETTER H WITH CIRCUMFLEX | `H` |
| `ĥ` | U+0125 | LATIN SMALL LETTER H WITH CIRCUMFLEX | `h` |
| `Ħ` | U+0126 | LATIN CAPITAL LETTER H WITH STROKE | `H` |
| `ħ` | U+0127 | LATIN SMALL LETTER H WITH STROKE | `h` |
| `Ĩ` | U+0128 | LATIN CAPITAL LETTER I WITH TILDE | `I` |
| `ĩ` | U+0129 | LATIN SMALL LETTER I WITH TILDE | `i` |
| `Ī` | U+012A | LATIN CAPITAL LETTER I WITH MACRON | `I` |
| `ī` | U+012B | LATIN SMALL LETTER I WITH MACRON | `i` |
| `Ĭ` | U+012C | LATIN CAPITAL LETTER I WITH BREVE | `I` |
| `ĭ` | U+012D | LATIN SMALL LETTER I WITH BREVE | `i` |
| `Į` | U+012E | LATIN CAPITAL LETTER I WITH OGONEK | `I` |
| `į` | U+012F | LATIN SMALL LETTER I WITH OGONEK | `i` |
| `İ` | U+0130 | LATIN CAPITAL LETTER I WITH DOT ABOVE | `I` |
| `ı` | U+0131 | LATIN SMALL LETTER DOTLESS I | `i` |
| `Ĵ` | U+0134 | LATIN CAPITAL LETTER J WITH CIRCUMFLEX | `J` |
| `ĵ` | U+0135 | LATIN SMALL LETTER J WITH CIRCUMFLEX | `j` |
| `Ķ` | U+0136 | LATIN CAPITAL LETTER K WITH CEDILLA | `K` |
| `ķ` | U+0137 | LATIN SMALL LETTER K WITH CEDILLA | `k` |
| `ĸ` | U+0138 | LATIN SMALL LETTER KRA | `k` |
| `Ĺ` | U+0139 | LATIN CAPITAL LETTER L WITH ACUTE | `L` |
| `ĺ` | U+013A | LATIN SMALL LETTER L WITH ACUTE | `l` |
| `Ļ` | U+013B | LATIN CAPITAL LETTER L WITH CEDILLA | `L` |
| `ļ` | U+013C | LATIN SMALL LETTER L WITH CEDILLA | `l` |
| `Ľ` | U+013D | LATIN CAPITAL LETTER L WITH CARON | `L` |
| `ľ` | U+013E | LATIN SMALL LETTER L WITH CARON | `l` |
| `Ŀ` | U+013F | LATIN CAPITAL LETTER L WITH MIDDLE DOT | `L` |
| `ŀ` | U+0140 | LATIN SMALL LETTER L WITH MIDDLE DOT | `l` |
| `Ł` | U+0141 | LATIN CAPITAL LETTER L WITH STROKE | `L` |
| `ł` | U+0142 | LATIN SMALL LETTER L WITH STROKE | `l` |
| `Ń` | U+0143 | LATIN CAPITAL LETTER N WITH ACUTE | `N` |
| `ń` | U+0144 | LATIN SMALL LETTER N WITH ACUTE | `n` |
| `Ņ` | U+0145 | LATIN CAPITAL LETTER N WITH CEDILLA | `N` |
| `ņ` | U+0146 | LATIN SMALL LETTER N WITH CEDILLA | `n` |
| `Ň` | U+0147 | LATIN CAPITAL LETTER N WITH CARON | `N` |
| `ň` | U+0148 | LATIN SMALL LETTER N WITH CARON | `n` |
| `Ŋ` | U+014A | LATIN CAPITAL LETTER ENG | `N` |
| `ŋ` | U+014B | LATIN SMALL LETTER ENG | `n` |
| `Ō` | U+014C | LATIN CAPITAL LETTER O WITH MACRON | `O` |
| `ō` | U+014D | LATIN SMALL LETTER O WITH MACRON | `o` |
| `Ŏ` | U+014E | LATIN CAPITAL LETTER O WITH BREVE | `O` |
| `ŏ` | U+014F | LATIN SMALL LETTER O WITH BREVE | `o` |
| `Ő` | U+0150 | LATIN CAPITAL LETTER O WITH DOUBLE ACUTE | `O` |
| `ő` | U+0151 | LATIN SMALL LETTER O WITH DOUBLE ACUTE | `o` |
| `Ŕ` | U+0154 | LATIN CAPITAL LETTER R WITH ACUTE | `R` |
| `ŕ` | U+0155 | LATIN SMALL LETTER R WITH ACUTE | `r` |
| `Ŗ` | U+0156 | LATIN CAPITAL LETTER R WITH CEDILLA | `R` |
| `ŗ` | U+0157 | LATIN SMALL LETTER R WITH CEDILLA | `r` |
| `Ř` | U+0158 | LATIN CAPITAL LETTER R WITH CARON | `R` |
| `ř` | U+0159 | LATIN SMALL LETTER R WITH CARON | `r` |
| `Ś` | U+015A | LATIN CAPITAL LETTER S WITH ACUTE | `S` |
| `ś` | U+015B | LATIN SMALL LETTER S WITH ACUTE | `s` |
| `Ŝ` | U+015C | LATIN CAPITAL LETTER S WITH CIRCUMFLEX | `S` |
| `ŝ` | U+015D | LATIN SMALL LETTER S WITH CIRCUMFLEX | `s` |
| `Ş` | U+015E | LATIN CAPITAL LETTER S WITH CEDILLA | `S` |
| `ş` | U+015F | LATIN SMALL LETTER S WITH CEDILLA | `s` |
| `Š` | U+0160 | LATIN CAPITAL LETTER S WITH CARON | `S` |
| `š` | U+0161 | LATIN SMALL LETTER S WITH CARON | `s` |
| `Ţ` | U+0162 | LATIN CAPITAL LETTER T WITH CEDILLA | `T` |
| `ţ` | U+0163 | LATIN SMALL LETTER T WITH CEDILLA | `t` |
| `Ť` | U+0164 | LATIN CAPITAL LETTER T WITH CARON | `T` |
| `ť` | U+0165 | LATIN SMALL LETTER T WITH CARON | `t` |
| `Ŧ` | U+0166 | LATIN CAPITAL LETTER T WITH STROKE | `T` |
| `ŧ` | U+0167 | LATIN SMALL LETTER T WITH STROKE | `t` |
| `Ũ` | U+0168 | LATIN CAPITAL LETTER U WITH TILDE | `U` |
| `ũ` | U+0169 | LATIN SMALL LETTER U WITH TILDE | `u` |
| `Ū` | U+016A | LATIN CAPITAL LETTER U WITH MACRON | `U` |
| `ū` | U+016B | LATIN SMALL LETTER U WITH MACRON | `u` |
| `Ŭ` | U+016C | LATIN CAPITAL LETTER U WITH BREVE | `U` |
| `ŭ` | U+016D | LATIN SMALL LETTER U WITH BREVE | `u` |
| `Ů` | U+016E | LATIN CAPITAL LETTER U WITH RING ABOVE | `U` |
| `ů` | U+016F | LATIN SMALL LETTER U WITH RING ABOVE | `u` |
| `Ű` | U+0170 | LATIN CAPITAL LETTER U WITH DOUBLE ACUTE | `U` |
| `ű` | U+0171 | LATIN SMALL LETTER U WITH DOUBLE ACUTE | `u` |
| `Ų` | U+0172 | LATIN CAPITAL LETTER U WITH OGONEK | `U` |
| `ų` | U+0173 | LATIN SMALL LETTER U WITH OGONEK | `u` |
| `Ŵ` | U+0174 | LATIN CAPITAL LETTER W WITH CIRCUMFLEX | `W` |
| `ŵ` | U+0175 | LATIN SMALL LETTER W WITH CIRCUMFLEX | `w` |
| `Ŷ` | U+0176 | LATIN CAPITAL LETTER Y WITH CIRCUMFLEX | `Y` |
| `ŷ` | U+0177 | LATIN SMALL LETTER Y WITH CIRCUMFLEX | `y` |
| `Ÿ` | U+0178 | LATIN CAPITAL LETTER Y WITH DIAERESIS | `Y` |
| `Ź` | U+0179 | LATIN CAPITAL LETTER Z WITH ACUTE | `Z` |
| `ź` | U+017A | LATIN SMALL LETTER Z WITH ACUTE | `z` |
| `Ż` | U+017B | LATIN CAPITAL LETTER Z WITH DOT ABOVE | `Z` |
| `ż` | U+017C | LATIN SMALL LETTER Z WITH DOT ABOVE | `z` |
| `Ž` | U+017D | LATIN CAPITAL LETTER Z WITH CARON | `Z` |
| `ž` | U+017E | LATIN SMALL LETTER Z WITH CARON | `z` |
| `ſ` | U+017F | LATIN SMALL LETTER LONG S | `s` |

#### Letters with no one-letter answer

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `Æ` | U+00C6 | LATIN CAPITAL LETTER AE | `AE` |
| `Þ` | U+00DE | LATIN CAPITAL LETTER THORN | `TH` |
| `ß` | U+00DF | LATIN SMALL LETTER SHARP S | `ss` |
| `æ` | U+00E6 | LATIN SMALL LETTER AE | `ae` |
| `þ` | U+00FE | LATIN SMALL LETTER THORN | `th` |
| `Ĳ` | U+0132 | LATIN CAPITAL LIGATURE IJ | `IJ` |
| `ĳ` | U+0133 | LATIN SMALL LIGATURE IJ | `ij` |
| `ŉ` | U+0149 | LATIN SMALL LETTER N PRECEDED BY APOSTROPHE | `'n` |
| `Œ` | U+0152 | LATIN CAPITAL LIGATURE OE | `OE` |
| `œ` | U+0153 | LATIN SMALL LIGATURE OE | `oe` |

#### Greek capitals

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `Α` | U+0391 | GREEK CAPITAL LETTER ALPHA | `A` |
| `Β` | U+0392 | GREEK CAPITAL LETTER BETA | `B` |
| `Γ` | U+0393 | GREEK CAPITAL LETTER GAMMA | `G` |
| `Δ` | U+0394 | GREEK CAPITAL LETTER DELTA | `D` |
| `Ε` | U+0395 | GREEK CAPITAL LETTER EPSILON | `E` |
| `Ζ` | U+0396 | GREEK CAPITAL LETTER ZETA | `Z` |
| `Η` | U+0397 | GREEK CAPITAL LETTER ETA | `E` |
| `Θ` | U+0398 | GREEK CAPITAL LETTER THETA | `T` |
| `Ι` | U+0399 | GREEK CAPITAL LETTER IOTA | `I` |
| `Κ` | U+039A | GREEK CAPITAL LETTER KAPPA | `K` |
| `Λ` | U+039B | GREEK CAPITAL LETTER LAMDA | `L` |
| `Μ` | U+039C | GREEK CAPITAL LETTER MU | `U` |
| `Ν` | U+039D | GREEK CAPITAL LETTER NU | `N` |
| `Ξ` | U+039E | GREEK CAPITAL LETTER XI | `X` |
| `Ο` | U+039F | GREEK CAPITAL LETTER OMICRON | `O` |
| `Π` | U+03A0 | GREEK CAPITAL LETTER PI | `P` |
| `Ρ` | U+03A1 | GREEK CAPITAL LETTER RHO | `R` |
| `Σ` | U+03A3 | GREEK CAPITAL LETTER SIGMA | `S` |
| `Τ` | U+03A4 | GREEK CAPITAL LETTER TAU | `T` |
| `Υ` | U+03A5 | GREEK CAPITAL LETTER UPSILON | `U` |
| `Φ` | U+03A6 | GREEK CAPITAL LETTER PHI | `F` |
| `Χ` | U+03A7 | GREEK CAPITAL LETTER CHI | `C` |
| `Ψ` | U+03A8 | GREEK CAPITAL LETTER PSI | `Y` |
| `Ω` | U+03A9 | GREEK CAPITAL LETTER OMEGA | `O` |

#### Greek small letters

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `α` | U+03B1 | GREEK SMALL LETTER ALPHA | `a` |
| `β` | U+03B2 | GREEK SMALL LETTER BETA | `b` |
| `γ` | U+03B3 | GREEK SMALL LETTER GAMMA | `g` |
| `δ` | U+03B4 | GREEK SMALL LETTER DELTA | `d` |
| `ε` | U+03B5 | GREEK SMALL LETTER EPSILON | `e` |
| `ζ` | U+03B6 | GREEK SMALL LETTER ZETA | `z` |
| `η` | U+03B7 | GREEK SMALL LETTER ETA | `e` |
| `θ` | U+03B8 | GREEK SMALL LETTER THETA | `t` |
| `ι` | U+03B9 | GREEK SMALL LETTER IOTA | `i` |
| `κ` | U+03BA | GREEK SMALL LETTER KAPPA | `k` |
| `λ` | U+03BB | GREEK SMALL LETTER LAMDA | `l` |
| `μ` | U+03BC | GREEK SMALL LETTER MU | `u` |
| `ν` | U+03BD | GREEK SMALL LETTER NU | `n` |
| `ξ` | U+03BE | GREEK SMALL LETTER XI | `x` |
| `ο` | U+03BF | GREEK SMALL LETTER OMICRON | `o` |
| `π` | U+03C0 | GREEK SMALL LETTER PI | `p` |
| `ρ` | U+03C1 | GREEK SMALL LETTER RHO | `r` |
| `ς` | U+03C2 | GREEK SMALL LETTER FINAL SIGMA | `s` |
| `σ` | U+03C3 | GREEK SMALL LETTER SIGMA | `s` |
| `τ` | U+03C4 | GREEK SMALL LETTER TAU | `t` |
| `υ` | U+03C5 | GREEK SMALL LETTER UPSILON | `u` |
| `φ` | U+03C6 | GREEK SMALL LETTER PHI | `f` |
| `χ` | U+03C7 | GREEK SMALL LETTER CHI | `c` |
| `ψ` | U+03C8 | GREEK SMALL LETTER PSI | `y` |
| `ω` | U+03C9 | GREEK SMALL LETTER OMEGA | `o` |

#### A Greek letter with a second code point

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `µ` | U+00B5 | MICRO SIGN | `u` |

### Normalize Characters

73 characters, every one of them replaced by plain ASCII. From [`macros/commands/normalize-characters.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/commands/normalize-characters.nm).

#### Dashes and hyphens

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

#### Single quotes, apostrophes, primes

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

#### Double quotes and double primes

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

#### Spaces

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

#### Invisible characters, deleted outright

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| (not printable) | U+00AD | SOFT HYPHEN | removed |
| (not printable) | U+200B | ZERO WIDTH SPACE | removed |
| (not printable) | U+200C | ZERO WIDTH NON-JOINER | removed |
| (not printable) | U+200D | ZERO WIDTH JOINER | removed |
| (not printable) | U+2060 | WORD JOINER | removed |
| (not printable) | U+FEFF | ZERO WIDTH NO-BREAK SPACE (BOM) | removed |

#### Line separators

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| (not printable) | U+2028 | LINE SEPARATOR | a newline |
| (not printable) | U+2029 | PARAGRAPH SEPARATOR | a newline |

#### Ligatures

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `ﬀ` | U+FB00 | LATIN SMALL LIGATURE FF | `ff` |
| `ﬁ` | U+FB01 | LATIN SMALL LIGATURE FI | `fi` |
| `ﬂ` | U+FB02 | LATIN SMALL LIGATURE FL | `fl` |
| `ﬃ` | U+FB03 | LATIN SMALL LIGATURE FFI | `ffi` |
| `ﬄ` | U+FB04 | LATIN SMALL LIGATURE FFL | `ffl` |
| `ﬅ` | U+FB05 | LATIN SMALL LIGATURE LONG S T | `st` |
| `ﬆ` | U+FB06 | LATIN SMALL LIGATURE ST | `st` |

#### Other punctuation

| Character | Code point | Name | Becomes |
| --- | --- | --- | --- |
| `•` | U+2022 | BULLET | `*` |
| `…` | U+2026 | HORIZONTAL ELLIPSIS | `...` |
| `×` | U+00D7 | MULTIPLICATION SIGN | `x` |
| `÷` | U+00F7 | DIVISION SIGN | `/` |
| `⁄` | U+2044 | FRACTION SLASH | `/` |
| `∕` | U+2215 | DIVISION SLASH | `/` |

#### Math relations

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

## How the letters were chosen

Normalize Characters' table is a lookup: an en dash has one obvious ASCII
spelling and that is the end of it. Fold Letters to ASCII is a set of judgement
calls.

### Accented letters

An accented letter becomes its base letter and keeps its case: `Balázs` becomes
`Balazs`, `Ångström` becomes `Angstrom`. For the 161 letters that have a
Unicode decomposition, the replacement is the first character of it. The other
19 do not decompose and were set by hand, among them `Ø` to `O`, `ð` to `d`,
`ı` to `i` and `Ł` to `L`.

Ten letters have no one-letter answer and get longer instead:

| Character | Becomes |
| --- | --- |
| `Æ` `æ` | `AE` `ae` |
| `Œ` `œ` | `OE` `oe` |
| `Þ` `þ` | `TH` `th` |
| `ß` | `ss` |
| `Ĳ` `ĳ` | `IJ` `ij` |
| `ŉ` | `'n` |

These are the only rows that widen a line. A capital expands to two capitals,
so `Ærø` comes out `AEro` rather than `Æro`; title-casing it would mean looking
at the character after it, and that is a second rule the table cannot carry.
They lengthen rather than fold because they turn up in names, where `Weiß` to
`Weis` is a misspelling and `Weiss` is not.

!!! warning "An accent fold is silent"

    A Greek letter gets a dialog. An accented letter does not. `Balázs` becomes
    `Balazs`, the terminal names U+00E1, and nothing in the file itself records
    that the accent was ever there. Keep the original if the spelling of a name
    matters.

### Greek letters

A Greek letter becomes the first letter of its English name, keeping its case,
so `α` becomes `a` and `Δ` becomes `D`.

| | | | | | |
| --- | --- | --- | --- | --- | --- |
| `Α` `α` → `A` `a` | `Β` `β` → `B` `b` | `Γ` `γ` → `G` `g` | `Δ` `δ` → `D` `d` | `Ε` `ε` → `E` `e` | `Ζ` `ζ` → `Z` `z` |
| `Η` `η` → `E` `e` | `Θ` `θ` → `T` `t` | `Ι` `ι` → `I` `i` | `Κ` `κ` → `K` `k` | `Λ` `λ` → `L` `l` | `Μ` `μ` → `U` `u` |
| `Ν` `ν` → `N` `n` | `Ξ` `ξ` → `X` `x` | `Ο` `ο` → `O` `o` | `Π` `π` → `P` `p` | `Ρ` `ρ` → `R` `r` | `Σ` `σ` → `S` `s` |
| `Τ` `τ` → `T` `t` | `Υ` `υ` → `U` `u` | `Φ` `φ` → `F` `f` | `Χ` `χ` → `C` `c` | `Ψ` `ψ` → `Y` `y` | `Ω` `ω` → `O` `o` |

Three of those are not the first letter of the name:

`μ` and `Μ` give `u`, not `m`. `24 µm` turning into `24 mm` is a factor of a
thousand in a column of wavelengths, and `mm` is a real unit, so nothing
downstream would catch it. `um` is the usual ASCII spelling in this field.
U+00B5 MICRO SIGN gives the same answer as U+03BC GREEK SMALL LETTER MU, so the
reading does not depend on which of the two the PDF happened to emit.

`φ` gives `f` and `ψ` gives `y`, because `π` already has `p`. `y` is psi's
letter in Beta Code.

Five readings collide, and nothing can tell a pair apart afterwards:

| Reading | Comes from |
| --- | --- |
| `e` | epsilon, eta |
| `o` | omicron, omega |
| `s` | sigma, final sigma |
| `t` | tau, theta |
| `u` | upsilon, mu |

That is why every Greek letter the macro replaces is listed in a dialog with
the line and column it was on, and why the cursor lands on the first one. Read
that list before the file goes any further. `σ` and `ς` both giving `s` also
means word-final position is not recoverable, so do not reach for this macro on
Greek prose; it is built for a data column.

Two published schemes avoid the collisions and are not used here. Beta Code
(`ω` to `W`) is bijective, so the original is always recoverable, and ISO 843
(`β` to `v`) follows modern Greek pronunciation; both need a reader who knows
the standard before an astronomy file makes sense. Spelling the name out, `α`
to `alpha`, would widen the line, and the point of running this before the
pipes go in is that nothing moves.

Every Greek letter is in the table, including the fourteen that look like a
Latin letter already. `Ο` U+039F is pixel-identical to `O`, and nothing
downstream will match it, so leaving it alone would leave an invisible fault
rather than avoid one.

## What is left alone

Nothing here has a safe ASCII spelling, so both commands leave it exactly as it
is. Guessing would quietly corrupt data, which is worse than leaving a
character that at least looks wrong.

| Character | Why it stays |
| --- | --- |
| `°` U+00B0 DEGREE SIGN | `deg`, `d` and `o` all appear in real files. Picking one would silently change what the number means. |
| `Ω` U+2126 OHM SIGN | A unit symbol with its own code point, not a letter, and folding it to `O` would destroy it. Greek `Ω` U+03A9 is a different character and Fold Letters to ASCII does replace that one. |
| `ά` `έ` `ώ` accented Greek | Never seen in this data, so it is not in either table. |
| `≪` `≫` `∝` `≃` and other relations not in the table | Add them if your files use them consistently. |
| Bytes that are not valid UTF-8 | XNEdit replaces each byte it cannot decode with U+FFFD REPLACEMENT CHARACTER as it reads the file, and locks the buffer, so both commands refuse the file rather than reach the byte. See [when the file is locked](cleaning-pdf-tables.md#when-the-file-is-locked). |

Normalize Characters is the command that reports these. After it runs it counts
what is left, puts the cursor on the first one, and lists them in a dialog with
a count per character, so each case can be decided by hand. That count includes
the accented and Greek letters until you run Fold Letters to ASCII, which is
what makes the dialog a pointer to the second command rather than a dead end.

Fold Letters to ASCII says nothing about what it left. It only ever reports the
Greek it replaced, because that is the one thing it does that cannot be
reversed by reading the result.

## What is deliberately not automated

A `##refcode` of `2026A+A...707A..13L` should read `2026A&A...707A..13L`. That
is a plain ASCII `+` standing in for `&`, not an encoding problem, and it is
not in the table on purpose: a blanket `+` to `&` replacement would destroy
every positive declination in the file. Fix refcodes by hand.

## Adding a character

A punctuation character goes in `macros/commands/normalize-characters.nm`, as
two lines keyed on its UTF-8 bytes:

```
fix["\xe2\x80\x93"] = "-"
nam["\xe2\x80\x93"] = "U+2013 EN DASH"
```

A letter goes in `macros/commands/fold-letters-to-ascii.nm`, as one line. That
macro carries no `nam[]` labels, because 240 entries plus a label each will not
fit in the 4096 instructions a macro gets, and `tools/gen_docs.py` works the
Unicode name out from the key instead:

```
fix["\xc3\xa9"] = "e"
```

Either way `fix[]` is where a new character goes. `grk[]` is the second table
in the fold macro, and it exists because the macro records where each Greek
letter sits before it replaces it, which is what lets the dialog give a line
and column. That arithmetic assumes every `grk[]` replacement is exactly one
character, so a character that replaces to more or fewer belongs in `fix[]`
whatever it is. `fix[]` runs first and nothing measures it.

Both macros still have room, but a macro compiles into 4096 instructions and no
more, and past that the editor refuses it with `macro too large` at parse time.
Do not work from a headroom figure written on a page: every edit to either
macro moves it. `test_command_has_room_to_grow` asks the editor instead, padding
each command with 40 more assignments and failing while there is still room to
act. The answer then is a third command rather than a bigger table, the way Fold
Letters to ASCII was split off in the first place.

Get the bytes with:

```sh
python3 -c 'print("".join("\\x%02x" % b for b in chr(0x2013).encode()))'
```

Then regenerate this page:

```sh
uv run python tools/gen_docs.py
```

Keys are written as escapes rather than as literal characters so the macro
survives being pasted through the Customize Menus dialog, and so the entries
you cannot see stay readable in the source. Order does not matter, because
every replacement is ASCII and no entry can feed another.

Keep the layout of the tables as it is. The group heading is the comment line
directly above a `fix[...]` or `grk[...]` line with no blank line between them,
and that is how `tools/gen_docs.py` tells a heading apart from ordinary prose
earlier in the file.

Two things to watch if you edit either macro:

- The search type must stay `"case"`. NEdit's `"literal"` is case-insensitive,
  and XNEdit folds case over UTF-8, where uppercasing the `fi` ligature gives
  the two characters `FI`. A `"literal"` search for a multi-byte character can
  match text you never intended, and with both cases of every Greek letter in
  the table, a `"literal"` search for `α` matches `Α`. `nedkit.checks` fails
  the build over this rather than leaving it to review.
- `replace_in_string()` needs its `"copy"` argument. Without it the call
  returns an empty string whenever the pattern does not match, and the loop
  would erase the buffer on its first miss.
