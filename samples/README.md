# samples

A real job, kept as a pair of files: what lands in the editor, and what has to
come out the other end.

| File | What it is |
| --- | --- |
| `A13L.mod.before` | An SDSS table pasted straight out of the paper, tab separated, with en dashes standing in for minus signs |
| `A13L.mod.after` | The finished NED file for the same data |

`A13L.mod.before` is the input for `tests/test_pipeline.py`, so it is a live
test fixture rather than a file sitting here going stale. What the commands
currently make of it is recorded in
`tests/fixtures/pipeline/A13L.expected.txt`.

## What the commands already do

**Align Columns**, then **Normalize Characters**, then **Align Columns** again
gets from `A13L.mod.before` to a padded, pipe delimited table: en dashes become
minus signs, the tabs go, and every column is as wide as its widest value.

Align Columns runs at both ends for two different reasons. First, because it
needs the tabs: once Normalize Characters has turned them into spaces there is
no delimiter left and fields get cut in the wrong places. Last, because the
widths are only right until the next edit, and that includes the edits
Normalize Characters makes.

## What is still done by hand

Everything that makes it a NED file, none of which any command here attempts:

- `##refcode = 2026A+A...` has to become `2026A&A...`. The `+` is an artifact
  of pasting, and no command knows about it.
- The seven `##` lines below the refcode: `##type1`, the two `##coord*_unit`
  lines, `##coord_equinox1`, `##coord_system1`, `##vz_flag1`, `##vz_unit1`.
- The column heading row, `ap_name1|name1|coordx1|coordy1|vz1`.
- Coordinates lose their colons and gain an explicit sign:
  `00:10:09.97` to `001009.97`, `15:34:09.66` to `+153409.66`.
- `ap_name1` and `name1` are built out of the coordinates:
  `SDSS J001009.97-004603.6`. Note that these are rounded to one decimal and
  are not simply `coordx1` and `coordy1` pasted together.

That list is the gap between the two files, so it is also the most concrete
statement in this repo of what a NED job actually involves. Anything added to
`macros/commands/` should be closing part of it.
