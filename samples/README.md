# samples

A real job, kept as a pair of files: what lands in the editor, and what has to
come out the other end.

| File | What it is |
| --- | --- |
| `A13L.mod.before` | An SDSS table pasted straight out of the paper, tab separated, with en dashes standing in for minus signs |
| `A13L.mod.after` | The finished NED file for the same data |

Neither file is wired into a test. `tests/test_pipeline.py` works from inline
bytes, so nothing fails if these two go stale. They are here to be read.

## What the commands already do

Not much of it, and none of it straight off the disk. `A13L.mod.before` is tab
separated, and the two pipe commands and **Pad Columns** refuse a buffer with a
tab in it, so it goes through `expand` first. After that, **Normalize
Characters** turns the en dashes into minus signs, piping the boundaries puts
the delimiters in, and **Pad Columns** squares the result up. That gets to a
padded pipe-delimited table, which is still a long way from `A13L.mod.after`.
[Cleaning up a pasted table](https://nedkit.sidereal.software/cleaning-pdf-tables/)
works that through step by step, on exactly this file.

## What is still done by hand

Everything that makes it a NED file, none of which any command here attempts:

- `##refcode = 2026A+A...` has to become `2026A&A...`. The `+` is an artifact
  of pasting, and no command knows about it.
- The seven `##` lines below the refcode: `##type1`, the two `##coord*_unit`
  lines, `##coord_equinox1`, `##coord_system1`, `##vz_flag1`, `##vz_unit1`.
- The column heading row, `ap_name1|name1|coordx1|coordy1|vz1`.
- Coordinates lose their colons and gain an explicit sign:
  `00:10:09.97` to `001009.97`, `15:34:09.66` to `+153409.66`.
- `ap_name1` and `name1` are the SDSS designations, and they have to be looked
  up. Row 2 shows why: the name reads `SDSS J004054.31+153409.8` where
  `coordx1` is `004054.33` and `coordy1` is `+153409.66`. Different digits, not
  a rounding of them, because the designation comes from SDSS's own astrometry
  and the paper's measured position is a separate quantity that lands nearby.
  Deriving a name from the coordinates would produce a plausible identifier for
  the wrong object.
- The column widths in `A13L.mod.after` are measured over the finished values,
  including the heading row and the explicit signs. Pad Columns will square the
  file up once those are in, but it cannot invent them.

That list is the gap between the two files, and the most concrete statement in
this repo of what a NED job involves. Anything added to `macros/commands/`
should be closing part of it.
