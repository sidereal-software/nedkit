# Preparing a SNe, FRB and GRB load

`ned-transients` does the copying part of the monthly transient load: it
fetches the lists from the Transient Name Server and Swift XRT, converts the
coordinates, and writes the loadstatus file, the ptables, the directory tree
and the Jira ticket body.

It loads nothing, and it decides nothing. `loadstatus`, `ptbl.py`, `lbl.py` and
the second-pass checks stay where they are and stay yours.

## One command per step

The procedure has five steps and each is its own command, so you can run the
parts that help and do the rest your way.

| Command | What it does |
| --- | --- |
| `scaffold` | Makes the SIP3 directory tree |
| `fetch` | Downloads the lists into `_raw/` |
| `ptable` | Builds the `.mod` files from what `fetch` cached |
| `loadstatus` | Writes the `.ls` file registering the refcodes |
| `jira` | Prints the author-information ticket |
| `prepare` | Runs all five in order |

There is also `refcodes`, which only prints the strings.

Run them one at a time:

```sh
cd /nedefs/Project/Production/dev/data.tables
B="--root . --batch a"

ned-transients scaffold $B
ned-transients fetch $B --since 2025-08-01 --until 2026-02-05
ned-transients ptable $B
ned-transients loadstatus $B
ned-transients jira $B
```

Or all at once, which is the same five functions in the same order:

```sh
ned-transients prepare $B --since 2025-08-01 --until 2026-02-05
```

Nothing needs installing. The tool is standard-library Python 3.9, so copying
the `python/` directory onto a machine is the whole setup. Run it as
`python3 python/ned-transients` if it is not on your `PATH`.

### They chain through the directory, not through each other

Each step reads what the last one left on disk, which is why any of them can be
re-run alone and any of them can be skipped and done by hand:

- `ptable` reads the responses `fetch` cached, and the window it recorded.
- `loadstatus` reads which `.mod` files exist to decide which refcodes to
  register. A source with no ptable gets no refcode, because that would point
  the reference database at a load that never happened.
- `ptable` skips objects already named in any `.mod` under the year, so a
  re-run finds nothing new rather than duplicating work.

A step that has not got what it needs says so and stops:

```
$ ned-transients ptable --root . --batch a
no window recorded for this batch. Run 'fetch' first, or pass --since / --month.
```

## Dates

`fetch` takes the range, and every other step picks it up from there.

| Flag | |
| --- | --- |
| `--since` | Window start, `YYYY-MM-DD` |
| `--until` | Window end, `YYYY-MM-DD`. Defaults to today |
| `--month` | Shorthand for a whole calendar month, `YYYY-MM` |
| `--obtained` | The download date. Defaults to today |

```sh
ned-transients fetch $B --since 2025-08-01 --until 2026-02-05
ned-transients fetch $B --month 2026-01
```

`fetch` writes the range to `_raw/window.txt`, and `ptable` uses it without
being told. Passing `--since` to `ptable` overrides that, which is how you cut
a narrower ptable out of a wider fetch:

```sh
ned-transients fetch  $B --since 2025-08-01 --until 2026-02-05
ned-transients ptable $B --since 2026-01-01   # only the last month of it
```

**`--obtained` is a different date from the window** and it is the one that
sets the refcode month. See [below](#the-window-is-not-a-month).

## The other flags

| Flag | |
| --- | --- |
| `--root` | The `data.tables` directory |
| `--batch` | Batch letter, `a` for the year's first load. Load sequence, not month |
| `--only` | A subset: `--only frb,grb`. `sne` also works for the TNS list |
| `--dry-run` | Print everything, write nothing. The right first move |
| `--force` | Overwrite files that already exist |
| `--tns-csv` | Use a CSV you downloaded by hand instead of fetching (`fetch` only) |

## What it writes

```
2026/SNe+FRB+GRB/SNe+FRB+GRB-a-SIP3/
    2026a.TNS.FRB.GRB.ls        the NED-only refcodes
    TNS/TNS.2026.03.31.mod      classified supernovae
    FRB/FRB.2026.03.31.mod      fast radio bursts
    GRB/GRB.2026.03.31.mod      gamma-ray bursts
    flt/  lbl/                  for the second-pass checks
    _raw/                       each response exactly as it arrived
```

`_raw/` is not part of the procedure. It holds the unparsed responses so
`ptable` never needs the network, a re-run costs nothing, and anything
surprising in a ptable can be traced back to what the server actually said.
`_raw/window.txt` is the range `fetch` covered.

## The window is not a month

The real files show loads covering much more than the month they were prepared
in: `GRB.2026.03.31.mod` spans August 2025 to February 2026, and
`FRB.2026.03.31.mod` spans December 2024 to September 2025. That is why
`--since` is the primary flag.

The **refcode** month is separate, and comes from the day you prepared the
batch rather than from the window. `FRB.2026.03.31.mod` loads under
`2026FRB...C...0000.`, where `C` is March, the month it was built. Use
`--obtained` to rebuild an old batch with its original refcodes.

## The three sources need different amounts of judgement

This is the thing to understand before trusting any output.

| Source | Selection needed |
| --- | --- |
| **GRB** | None. Load everything |
| **FRB** | A lot. Roughly a quarter of the candidates are kept |
| **TNS** | Unknown; no sample to check against |

**GRBs are automatic.** Checking the real `GRB.2026.03.31.mod` against the
Swift table, it holds every burst between its oldest and newest, in the same
order, with no gaps. All 66 rows reproduce byte for byte. Take what the tool
gives you.

**FRBs are not.** The real `FRB.2026.03.31.mod` keeps 33 of the 142 candidates
in its window, and nothing in the TNS export explains which 33. These were all
tried and none of them is the rule:

| Rule | Why it is not the rule |
| --- | --- |
| Discovery-date window | Kept and dropped objects interleave |
| TNS id above a threshold | Same |
| Sits in a contiguous id run | 23 kept objects sit in one |
| Reporting group | Both sets are mostly CHIME |
| Internal name lacks `chimefrb_` | Misses 20 of the 33 |
| Has a discovery bibcode | Would keep 82 that were dropped |

So the decision draws on something the export does not carry, and the tool does
not guess. Every candidate goes into the ptable and you delete rows.

What it does do is group them. TNS hands out ids in insertion order, so a
catalogue uploaded in one go lands as a contiguous block, and the report
collapses those into one line each:

```
FRB: 146 candidates

  130 of these arrived in 9 consecutive-id runs, which is what a bulk
  catalogue upload looks like. All of them are in the ptable; delete the
  rows you do not want.

    ids 172456-172469   14 objects  CHIMEFRB   2025-01-04 .. 2025-02-02
    ids 177067-177093   27 objects  CHIMEFRB   2025-02-07 .. 2025-04-05
```

That turns scanning 146 rows into scanning nine. It is a reading aid, not a
filter.

**The TNS supernova layout is unverified.** There is no real `TNS.*.mod` to
check against, so its metadata block is inferred from the FRB and GRB files.
The tool prints a warning every time it writes one. Check it against a real
file before loading, and if you find one, it belongs in
`tests/fixtures/transients/`.

## Coordinates are not rounded

Both sources publish sexagesimal positions, and the conversion only strips the
colons and makes the declination's sign explicit:

| | From the source | In the ptable |
| --- | --- | --- |
| TNS | `20:31:06.360` | `203106.360` |
| TNS | `+53:50:56.40` | `+535056.40` |
| Swift | `13:40:25.49` | `134025.49` |
| Swift | `+01:55:50.7` | `+015550.7` |

Precision is whatever the source published, which is why the FRB file carries
three decimals of right ascension and the GRB file two. Rounding to any fixed
number of places would be wrong for one of them.

## Getting the lists

Neither source needs an account.

Swift's position table is available as plain text and needs nothing special.

TNS answers **403** to a request that does not look like a browser, which is a
User-Agent filter rather than a login wall: the tool sends an ordinary browser
string and the same URLs return 200. The failure mode is worth knowing, because
a 403 reads exactly like the site being down.

That is not the sanctioned route. TNS's supported path is a registered bot
account, which also unlocks the bulk daily-delta files and would be worth
setting up. At three requests a month the current approach is not a burden on
them, but it can break without warning, which is what `--tns-csv` is for:
export the CSV from the search page yourself and point the tool at the file.

TNS also paginates. `fetch` follows every page, because stopping at the first
one silently truncates the list, and a truncated list looks exactly like a
quiet month.

Only `fetch` goes to the network. Every other step works from `_raw/`, so once
a batch is fetched you can rebuild it offline as many times as you like.

## After it runs

Nothing has been loaded. From here the procedure is unchanged:

1. `loadstatus` on the `.ls` file, check the `.msg`, then `loadstatus -load_ok`.
2. File the Jira ticket the tool printed.
3. Edit the ptables: delete the FRB rows you do not want.
4. `ptbl.py` and `lbl.py`.
5. Copy the `.flt` files into `flt/` and run the SecondPassOfChecking steps.

Step 3 is the one worth budgeting time for, and it is why the steps are
separate: run `ptable`, edit the file, then carry on with `loadstatus`.
