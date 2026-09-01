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

There is also `refcodes`, which only prints the strings and writes nothing,
which is why it is the one command taking no `--root` or `--batch`:

```{ .sh .copy }
python3 $NT refcodes --obtained 2026-03-31
```

`--obtained` is what sets the refcode month, so pass it to see what an older
batch was registered under.

Nothing needs installing. The tool is standard-library Python 3.9, so copying
the `python/` directory out of a
[clone of the repository](installing-macros.md#getting-the-repository) onto a
machine is the whole setup. There is no `ned-transients` on your `PATH` to run,
though: you hand the file to `python3` where it sits, so the examples here keep
its path in `$NT` and set that first.

Run the steps one at a time:

```{ .sh .copy }
NT=~/nedkit/python/ned-transients      # wherever you copied python/ to
cd /nedefs/Project/Production/dev/data.tables

python3 $NT scaffold   --root . --batch a
python3 $NT fetch      --root . --batch a --since 2025-08-01 --until 2026-02-05
python3 $NT ptable     --root . --batch a
python3 $NT loadstatus --root . --batch a
python3 $NT jira       --root . --batch a
```

Or all at once, which is the same five functions in the same order:

```{ .sh .copy }
python3 $NT prepare --root . --batch a --since 2025-08-01 --until 2026-02-05
```

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
$ python3 $NT ptable --root . --batch a
no window recorded for this batch. Run 'fetch' first, or pass --since / --month.
```

## Dates

`fetch` takes the range, and every other step picks it up from there.

| Flag | What it means |
| --- | --- |
| `--since` | Window start, `YYYY-MM-DD` |
| `--until` | Window end, `YYYY-MM-DD`. Defaults to today |
| `--month` | Shorthand for a whole calendar month, `YYYY-MM` |
| `--obtained` | The download date. Defaults to today |

```{ .sh .copy }
python3 $NT fetch --root . --batch a --since 2025-08-01 --until 2026-02-05
python3 $NT fetch --root . --batch a --month 2026-01
```

`fetch` writes the range to `_raw/window.txt`, and `ptable` uses it without
being told. Passing `--since` to `ptable` overrides that, which is how you cut
a narrower ptable out of a wider fetch:

```{ .sh .copy }
python3 $NT fetch  --root . --batch a --since 2025-08-01 --until 2026-02-05
python3 $NT ptable --root . --batch a --since 2026-01-01   # last month only
```

**`--obtained` is a different date from the window** and it is the one that
sets the refcode month. See [below](#the-window-is-not-a-month).

## The other flags

| Flag | What it means |
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

| Source | From the source | In the ptable |
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

TNS answers **403** to some clients, and it is worth being precise about which,
because the obvious conclusion is wrong. Measured against the live search
endpoint:

| `User-Agent` | What TNS answers |
| --- | --- |
| `curl/8.7.1` | 403 |
| `python-requests/2.32` | 403 |
| `Python-urllib/3.x`, the default | 200 |
| `nedkit/0.1 (+…)`, what the tool sends | 200 |
| a Chrome string | 200 |

So it is a blocklist of a few well-known tool names rather than a demand to
look like a browser, and an honest identifier passes. The tool says who it is
and gives TNS something to contact if the traffic ever becomes a problem. A
plain `curl` command against the same URL will 403, which is worth knowing
before concluding the site is down.

TNS also applies a request quota over a 60-second window and answers **429**
past it. Three requests a month is nowhere near that; a loop under development
is. The tool names the quota rather than reporting a bare HTTP error.

The sanctioned route for heavier use is a registered bot account, which also
unlocks the bulk daily-delta files and would be worth setting up. If the
current approach ever stops working, `--tns-csv` is the fallback: export the
CSV from the search page yourself and point `fetch` at the file.

## Other ways of getting the data

Checked, and none of them replaces the two sources in use:

| Alternative | Verdict |
| --- | --- |
| TNS bulk `tns_public_objects` files | **403 without credentials.** Genuinely needs a bot account, unlike the search export |
| TNS results page | **Adopted**, as the fallback route. See above |
| TNS per-object pages, as GOATS scrapes | One object per request, so no way to ask "what is new" |
| HEASARC `swiftgrb` via TAP | **Stops at December 2012.** 872 rows against swift.ac.uk's 1765 |
| Other HEASARC GRB tables | All historical or mission-specific. No live XRT position feed |
| FRBSTATS | **Gone.** The domain is parked and for sale |
| Alert brokers (ALeRCE, Lasair, Fink) | Not evaluated in depth, because of provenance. See below |

**Provenance is the reason this list is short.** The refcodes record where the
data came from: `2026TNS...C......0.` is credited to the "Transient Name Server
Collaboration" and its Jira ticket says *obtained from wis-tns.weizmann.ac.il*,
and the GRB refcode credits the "Neil Gehrels Swift Observatory Science Data
Centre". Pulling the same objects from a broker would make what NED records
about their origin untrue. So the question is not really which site to read,
it is how best to read the two that the refcodes already name.

For Swift there is nothing better: `swift.ac.uk/xrt_positions` is the UK Swift
Science Data Centre's own live table of enhanced positions, it needs no
account, and it is the thing the refcode cites.

For TNS, scraping is the route, and it is made as sturdy as scraping gets by
having two independent ways in rather than one.

### Would a bot account remove the need to scrape?

Only through one of its two doors, and not the one you would expect.

The TNS **API** is built for "tell me about this object": `/api/get/search`
takes a name or a position and hands back identifiers, and `/api/get/object`
returns the detail for one object at a time. There is no "every object
discovered between these dates, with coordinates". Getting a month that way
would be one request per object against a quota, where the search export is one
request for the lot. **The API is the wrong shape for this job**, which is why
`tns-api` on PyPI does single-object lookups and why GOATS does too.

What *would* replace scraping is the **bulk daily-delta files**, which do carry
full rows and answer "what changed since yesterday" directly. Those need the
bot account. If one ever appears, that is the route to take, and it is a
smaller change than it sounds: a different `fetch`, the same parser.

### Libraries that already do this

| Library | Why it does not fit |
| --- | --- |
| [`transientNamer`](https://github.com/thespacedoctor/transientNamer) | Scrapes the same `/search` endpoint. Maintained, last release February 2025 |
| [`tns-api`](https://github.com/temuller/Tns_api) | Wraps the official API. Needs bot credentials, single-object lookups |
| [`tom_tns`](https://github.com/TOMToolkit/tom_tns) | Report submission, which is the opposite direction |

`transientNamer` is the closest match and independently validates the approach:
it reads the same page, sends its own honest User-Agent, and asks for columns
with `display[...]=1` rather than trusting the default view, which is a trick
worth copying and now is. Its changelog carries a *"fix TNS search after TNS API
update"* entry, which is a fair warning about how durable any of this is.

It still would not do this job, for reasons that have nothing to do with
whether packages can be installed:

- **No object-type filter.** Its search sends `ra`, `decl`, `radius`, `name`,
  `internal_name` and a period, and that is all. It cannot ask for FRBs
  (`objtype[]=130`) or restrict to classified supernovae, which are exactly
  the two queries `fetch` makes.
- **Relative windows only.** It takes `discInLastDays`, so "the last 90 days",
  not "1 December 2024 to 30 September 2025". A load window that moves with
  the calendar cannot rebuild an old batch, and `--obtained` exists precisely
  so an old batch can be rebuilt.
- **It parses with one large regex** over the row, which fixes the column
  order. The parser here keys on each cell's class, so a reordered table still
  reads correctly; there is a test for that.

For the record, its TNS search does not use BeautifulSoup at all: `requests`
and `re`. BeautifulSoup appears elsewhere in the package, for a different
feature.

So the hand-rolled eighty lines are not a workaround for a missing dependency.
They do something the library does not.

TNS also paginates. `fetch` follows every page, because stopping at the first
one silently truncates the list, and a truncated list looks exactly like a
quiet month.

Only `fetch` goes to the network. Every other step works from `_raw/`, so once
a batch is fetched you can rebuild it offline as many times as you like.

### Two routes in, because there is no API key

Without a bot account the only way to get the list is to read the site, so the
guard against TNS changing is knowing two ways in rather than one. `fetch`
tries them in order:

| Order | Route | What it costs |
| --- | --- | --- |
| 1 | The CSV export, `&format=csv` | Structured, and about 50 KB for a month |
| 2 | The ordinary results page | Same query, same rows, about 3.9 MB |

The results page marks every cell with `class="cell-name"`, `cell-ra`,
`cell-decl` and so on, and those carry the same values as the CSV columns.
Checked against each other over a live month: **132 records each, identical
record for record.** The fixture test keeps them honest offline.

The CSV route is tried first because it is a tenth of a percent of the size.
If it fails, `fetch` says so and carries on:

```
  ! TNS CSV export failed (ValueError: ...). Falling back to the results
    page. The run is fine; the CSV route needs looking at.
fetched   FRB     17 objects -> .../_raw/tns-frb.html
```

The fallback is never silent. The run succeeding does not mean nothing is
wrong, and the cached file's extension records which route answered, so
`_raw/tns-frb.html` is itself the sign that route 1 needs attention.

A rate limit does **not** trigger the fallback, since the quota covers both
routes and asking the same server the same question a different way would only
spend more of it.

`--tns-csv` accepts either format too, so a page saved out of a browser works
as well as a CSV export.

This is roughly what the [GOATS project](https://github.com/gemini-hlsw/goats)
does for TNS, and its client is worth knowing about: it scrapes
`wis-tns.org/object/<name>` for one object at a time and identifies itself as
`GOATS.TNSClient/1.0`, which is independent confirmation that a plain honest
User-Agent is all TNS wants. Its per-object route does not answer "everything
in this date range", which is why it is not what `fetch` uses.

## After it runs

Nothing has been loaded. From here the procedure is unchanged:

1. `loadstatus` on the `.ls` file, check the `.msg`, then `loadstatus -load_ok`.
2. File the Jira ticket the tool printed.
3. Edit the ptables: delete the FRB rows you do not want.
4. `ptbl.py` and `lbl.py`.
5. Copy the `.flt` files into `flt/` and run the SecondPassOfChecking steps.

Step 3 is the one worth budgeting time for, and it is why the steps are
separate: run `ptable`, edit the file, then carry on with `loadstatus`.
