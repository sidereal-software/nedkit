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
separated, and **Pipe at Cursor Column** and **Pipe at Columns** both refuse a
buffer with a tab in it: a tab is one character and any number of columns, so
there is no saying what column anything is in. Select the whole file and run it
through `expand` first, using **Shell > Filter Selection**.

After that, piping the boundaries and then running **Normalize Characters**
turns the en dashes into minus signs and gets to a pipe delimited table, which
is still a long way from `A13L.mod.after`.
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
- `ap_name1` and `name1` are the SDSS designations, and they cannot be worked
  out from anything else in the file. Row 2 is the one to look at: the name
  reads `SDSS J004054.31+153409.8` where `coordx1` is `004054.33` and
  `coordy1` is `+153409.66`. Different digits, not a rounding of them. The
  designation comes from SDSS's own astrometry and the paper's measured
  position is a separate quantity that lands nearby, so the names have to be
  looked up. Deriving them from the coordinates would produce a plausible
  identifier for the wrong object.
- Every field in `A13L.mod.after` is padded out to the width of the widest
  value in its column, and every row ends up the same length. Nothing in
  `macros/commands/` pads anything.

That list is the gap between the two files, so it is also the most concrete
statement in this repo of what a NED job actually involves. Anything added to
`macros/commands/` should be closing part of it.
