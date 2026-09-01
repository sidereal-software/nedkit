"""The worked example in ``docs/cleaning-pdf-tables.md``, run.

That page walks seven commands over ``samples/A13L.mod.before`` and prints what
each one reports and what the file looks like afterwards. Nothing else in the
repo checks a word of it, and a page can be wrong about the macros in a way that
reads perfectly: offering ``samples/A13L.mod.after`` as the thing to check your
run against is a sentence nothing here contradicts, and it is false, because
that file is the hand-finished NED file the sequence gets nowhere near. This is
the class of mistake the file exists to catch.

**The expectations are read out of the page rather than written down here.** A
test holding its own copy of the numbers is a test of the macros, and the macros
are not what goes wrong: it would pass against a page saying anything at all.
Reading the page makes an edit to the page an edit to the assertions, so the two
fail together in either direction. A command whose report changes stops matching
what the page quotes, and a page edited to claim something no command does stops
matching what the run said.

What that costs is coupling to the page's markdown. The steps are its bolded
command names in document order, the expected reports and listings are its
fenced blocks and inline code, and the counts come out of its prose through the
patterns below. Every one of those raises rather than quietly matching nothing,
so a rewrite of the page fails this file loudly instead of silently checking
less. That is the trade: the page is the specification, so the specification has
a shape.

One editor for the whole sequence, driven through ``docs/nedkit-macros.rc`` and
``macro_menu_command()``, which is the install the page tells a reader to do.
Running each command in its own editor would cost seven startups to prove the
same thing, and would not be the sequence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from nedkit import MacroRun, XNEditRunner, command_files, parse

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs" / "cleaning-pdf-tables.md"
SHIPPED = REPO_ROOT / "docs" / "nedkit-macros.rc"
PASTE = REPO_ROOT / "samples" / "A13L.mod.before"
FINISHED = REPO_ROOT / "samples" / "A13L.mod.after"

#: Every command, by the title its header gives it, which is what the page
#: bolds when it names one.
COMMANDS = {parse(path).title: parse(path) for path in command_files(REPO_ROOT)}

FENCE = re.compile(r"^```\n(.*?)^```$", re.S | re.M)
SPAN = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")


def worked_example() -> str:
    """The section of the page this file is about, and nothing else.

    Bounded by the next heading at the same level, so the ``###`` subsection
    holding the buffer's final line count comes along with it.
    """
    text = PAGE.read_text(encoding="utf-8")
    start = text.index("\n## A worked example")
    return text[start : text.index("\n## ", start + 1)]


SECTION = worked_example()


def stated(pattern: str) -> tuple[str, ...]:
    """What the page's prose says, or an error naming what stopped saying it."""
    match = re.search(pattern, SECTION)
    assert match, (
        f"the worked example holds nothing matching {pattern!r}, so the claim "
        "this test reads off the page is not there to read. The pattern and the "
        "sentence have to describe each other."
    )
    return match.groups()


#: Number words the page writes out, since it counts fields and columns in
#: prose rather than in figures.
WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight")


def number(word: str) -> int:
    assert word in WORDS, f"the page counts in {word!r}, which is not a number word"
    return WORDS.index(word)


@dataclass(frozen=True)
class Item:
    """One piece of code on the page: a fenced block or an inline span."""

    position: int
    text: str
    fenced: bool


def code_items() -> list[Item]:
    """Everything the page sets in code, in the order a reader meets it.

    Inline code has its whitespace flattened because markdown wraps it: the
    right ascension report is quoted across a line break and is one string to
    anybody reading the rendered page. A fenced block is left alone, since the
    listings are only worth anything line by line.
    """
    items = [
        Item(match.start(), match.group(1).rstrip("\n"), True)
        for match in FENCE.finditer(SECTION)
    ]
    outside_fences = FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), SECTION)
    items += [
        Item(match.start(), re.sub(r"\s+", " ", match.group(1)), False)
        for match in SPAN.finditer(outside_fences)
    ]
    return sorted(items, key=lambda item: item.position)


def steps() -> list[str]:
    """The commands the worked example runs, in the order it runs them.

    Taken from the page rather than fixed here, so the order is under test too.
    Declination before right ascension is the page's own point, and a test that
    hardcoded the sequence could not notice the page changing its mind about it.
    """
    named = [name for name in BOLD.findall(SECTION) if name in COMMANDS]
    assert named, "the worked example bolds none of the commands it runs"
    return named


STEPS = steps()

#: Where the page says to put the pipes, and which button it says to press. Both
#: are inputs to the run rather than expectations of it, which is exactly why
#: they have to come off the page: the listings further down are what a wrong
#: answer would contradict, and the test would supply the right answer to a page
#: asking for a different one.
COLUMNS = [
    int(column) for column in re.split(r"[ ,]+", stated(r"Answering `([^`]+)`")[0])
]
BUTTON_LABEL = stated(r"choosing (\w+)")[0]


def buttons() -> list[str]:
    """The buttons Pipe at Columns puts on its prompt, in the order it lists them.

    Read off the macro so the label the page names can be turned into the number
    the harness answers with, rather than the two being written down separately
    and left to drift apart.
    """
    call = re.search(
        r"string_dialog\(\s*\w+\s*,(.*)\)", COMMANDS["Pipe at Columns"].body
    )
    assert call, "Pipe at Columns asks its question some other way now"
    return re.findall(r'"([^"]+)"', call.group(1))


BUTTONS = buttons()

#: The field of the piped table each coordinate command is aimed at, counting
#: from the left. The page describes the rectangle in words rather than in
#: numbers, so this is the one thing about the sample the test knows on its own.
#: A wrong entry does not pass quietly: both commands refuse a column that is
#: not coordinates and convert nothing at all.
FIELD = {"RA to NED Form": 1, "Dec to NED Form": 2}

#: The start of the first line with a pipe in it, which once the boundaries are
#: in is the first data row. The page says to start the rectangle there so the
#: ``##refcode`` line stays out of it.
FIRST_DATA_ROW = 'search("^[^\\n]*\\\\|", 0, "regex")'

STEP_MARK = "__NEDKIT_STEP__"
BUFFER_MARK = "__NEDKIT_BUFFER__"
END_MARK = "__NEDKIT_ENDBUFFER__"


def aim(title: str) -> str:
    """Whatever a command needs pointing at it before it will do anything.

    Two of the seven take a rectangular selection and one asks a question. The
    other four take the whole buffer and need nothing. See
    ``nedkit.runner.PROMPT_STUB`` for the globals the answer feeds.
    """
    if title == "Pipe at Columns":
        assert BUTTON_LABEL in BUTTONS, (
            f"the page says to choose {BUTTON_LABEL!r}, which is not one of the "
            f"buttons Pipe at Columns offers: {BUTTONS}"
        )
        answer = ", ".join(str(column) for column in COLUMNS)
        return (
            f'$ned_string_dialog_answer = "{answer}"\n'
            f"$ned_string_dialog_button = {BUTTONS.index(BUTTON_LABEL) + 1}"
        )
    if title in FIELD:
        field = FIELD[title]
        return (
            f"select_rectangle({FIRST_DATA_ROW}, $text_length, "
            f"{COLUMNS[field - 1] + 1}, {COLUMNS[field]})"
        )
    return ""


def sequence_macro() -> str:
    """The seven commands in order, each fenced by markers naming its step.

    The buffer is printed after every one of them, not only where the page
    shows a listing, so which step a listing belongs to stays the page's
    business rather than this function's.
    """
    lines = []
    for index, title in enumerate(STEPS):
        lines += [
            aim(title),
            f't_print("{STEP_MARK}{index}\\n")',
            f'macro_menu_command("{COMMANDS[title].menu_entry}")',
            f't_print("{BUFFER_MARK}{index}\\n" get_range(0, $text_length)'
            f' "{END_MARK}{index}\\n")',
        ]
    return "\n".join(line for line in lines if line)


def between(lines: list[str], opening: str, closing: str) -> str:
    for mark in (opening, closing):
        assert mark in lines, (
            f"{mark} never reached stdout, so the run stopped part way through "
            f"the sequence:\n" + "\n".join(lines)
        )
    return "\n".join(lines[lines.index(opening) + 1 : lines.index(closing)])


@dataclass(frozen=True)
class Sequence:
    """What the seven commands said and what each one left in the buffer."""

    run: MacroRun
    reports: list[str]
    buffers: list[str]

    @property
    def result(self) -> str:
        return (self.run.output or b"").decode("utf-8")


@pytest.fixture(scope="module")
def sequence(
    runner: XNEditRunner, tmp_path_factory: pytest.TempPathFactory
) -> Sequence:
    """The whole worked example, in one editor, from the shipped resource file.

    The file keeps the sample's name, because the reports quote it and the page
    quotes the reports.

    Two things are settled here rather than in a test of their own, because
    neither can go wrong without every test below going wrong with it. A dialog
    is a command stopping to say something the worked example never mentions,
    and it is the shape a refusal takes: aiming a rectangle at the wrong column
    raises one and converts nothing. And a step that says nothing at all was
    never installed under the menu path the page names, since XNEdit discards an
    unknown one rather than complaining about it.
    """
    run = runner.run_on_bytes(
        sequence_macro(),
        PASTE.read_bytes(),
        tmp_path_factory.mktemp("worked-example"),
        name=PASTE.name,
        extra_args=["-import", str(SHIPPED)],
    )
    assert run.ok, run.describe()
    assert run.dialogs == [], (
        "a command stopped to tell the reader something the worked example does "
        f"not mention: {run.dialogs}"
    )

    lines = run.messages.split("\n")
    parsed = Sequence(
        run=run,
        reports=[
            between(lines, f"{STEP_MARK}{i}", f"{BUFFER_MARK}{i}")
            for i in range(len(STEPS))
        ],
        buffers=[
            between(lines, f"{BUFFER_MARK}{i}", f"{END_MARK}{i}") + "\n"
            for i in range(len(STEPS))
        ],
    )
    for index, title in enumerate(STEPS):
        assert parsed.reports[index].strip(), (
            f"{COMMANDS[title].menu_entry} said nothing, so nothing answers to "
            "that menu path. Either the shipped resource file installs the "
            "command under another name, or the page bolds a name it never had."
        )
    return parsed


REPORT_CALL = re.compile(r't_print\("(\w+): "')


def prefixes() -> tuple[str, ...]:
    """The word each command opens every one of its reports with.

    Read off the macros so the page is measured against what the commands
    print, rather than against a second list kept here that could drift from it.
    """
    found = []
    for title, macro in COMMANDS.items():
        match = REPORT_CALL.search(macro.body)
        assert match, f"{title} prints no report under a prefix"
        found.append(match.group(1) + ": ")
    return tuple(found)


#: The two shapes a report takes in this repo: a ``prefix:`` naming the command,
#: and a ``(s)`` on a noun the count in front of it might make plural. Anything
#: on the page written in either shape is a claim about a command's output, and
#: this is what separates those from the code spans that are only file names and
#: column headings.
PREFIXES = prefixes()


def report_shaped(item: Item) -> bool:
    return "(s)" in item.text or item.text.startswith(PREFIXES)


#: The one quote in the section that is not about this run. The trim paragraph
#: says what a run that did something would have said, with a placeholder where
#: the count goes, and no run of this file produces it.
HYPOTHETICAL = stated(r"would say\s+`([^`]+)`")[0]


@pytest.mark.xnedit
def test_the_page_quotes_the_report_every_command_made(sequence: Sequence) -> None:
    """Both directions at once, which is the whole point of this file.

    Every report the page sets in code has to be something one of the commands
    said, so a page edited to claim a count no command produces fails here. And
    every command has to be quoted somewhere, so a report string that changes
    leaves its step unquoted and fails here too. The quotes also have to arrive
    in the order the commands ran, or the page has hung one command's output on
    another.

    The page quotes some reports whole and some as the fragment after the
    ``prefix: file:`` header, so a quote is checked by containment rather than
    equality. Containment still pins every count and every word around it.
    """
    quoted = []
    for item in code_items():
        if not report_shaped(item) or item.text == HYPOTHETICAL:
            continue
        said_it = [
            index
            for index, report in enumerate(sequence.reports)
            if item.text in report
        ]
        assert len(said_it) == 1, (
            f"the page quotes {item.text!r}, and "
            + (
                "no command said it. Either the page is claiming something the "
                "commands do not do, or a command's report has changed under it."
                if not said_it
                else f"more than one command said it: {[STEPS[i] for i in said_it]}"
            )
            + "\nWhat they said:\n"
            + "\n".join(f"  {STEPS[i]}: {r!r}" for i, r in enumerate(sequence.reports))
        )
        quoted.append(said_it[0])

    assert quoted == sorted(quoted), (
        "the page quotes the reports out of sequence, so at least one is "
        f"attributed to the wrong command: {[STEPS[i] for i in quoted]}"
    )
    assert set(quoted) == set(range(len(STEPS))), (
        "the page runs a command whose report it never quotes: "
        f"{[title for index, title in enumerate(STEPS) if index not in quoted]}"
    )


def listings() -> list[Item]:
    """The fenced blocks showing the file, which all open on its header line."""
    header = PASTE.read_text(encoding="utf-8").split("\n")[0]
    found = [
        item for item in code_items() if item.fenced and item.text.startswith(header)
    ]
    assert len(found) > 1, (
        f"the worked example shows {len(found)} listings of the file, so there is "
        "nothing here to compare a buffer against"
    )
    return found


def data_rows(listing: str) -> list[str]:
    """The rows a listing shows, which are what follows its blank line."""
    lines = listing.split("\n")
    assert "" in lines, (
        f"no blank line separates the header from the rows in {listing!r}, so "
        "there is no telling where the rows start"
    )
    return lines[lines.index("") + 1 :]


def test_the_first_listing_is_the_file_the_page_says_to_download() -> None:
    """The page shows the paste before quoting anything a command says about it.

    Tabs and all: the warning above the block is about the rendered page, not
    about the markdown, so the source really does hold the file's own bytes.
    """
    shown = listings()[0]
    expected_rows = number(stated(r"show the first (\w+) of")[0])

    assert len(data_rows(shown.text)) == expected_rows, (
        f"the page says it shows the first {expected_rows} rows and shows "
        f"{len(data_rows(shown.text))}"
    )
    head = PASTE.read_text(encoding="utf-8").split("\n")[: len(shown.text.split("\n"))]
    assert shown.text == "\n".join(head), (
        "the listing of the paste is not the head of samples/A13L.mod.before"
    )


@pytest.mark.xnedit
def test_every_listing_is_the_buffer_the_command_above_it_left(
    sequence: Sequence,
) -> None:
    """Each listing belongs to the last command the page named before it.

    That is the only thing tying a block to a step, and it is what makes the
    order the page runs the commands in a testable claim: putting the right
    ascension before the declination changes what the middle listing shows.
    """
    marks = [
        (SECTION.index(f"**{title}**"), index) for index, title in enumerate(STEPS)
    ]
    expected_rows = number(stated(r"show the first (\w+) of")[0])

    for shown in listings()[1:]:
        step = max(index for position, index in marks if position < shown.position)
        rows = data_rows(shown.text)
        assert len(rows) == expected_rows, (
            f"the listing after {STEPS[step]} shows {len(rows)} rows, not the "
            f"{expected_rows} the page says it shows"
        )
        head = sequence.buffers[step].split("\n")[: len(shown.text.split("\n"))]
        assert shown.text == "\n".join(head), (
            f"the listing the page shows after {STEPS[step]} is not what the "
            f"buffer held then. The buffer held:\n{sequence.buffers[step]}"
        )


@pytest.mark.xnedit
def test_the_page_counts_the_file_the_sequence_leaves(sequence: Sequence) -> None:
    """The rows the page never shows, which only its prose says anything about.

    Every row after the third one is out of shot in every listing, so the counts
    under them are the whole of the page's claim about the other eleven.
    """
    rows_long = int(stated(r"It is (\d+) rows long")[0])
    lines_held = int(stated(r"buffer now holds (\d+) lines")[0])
    rows, fields, width = stated(r"(\d+) data rows of (\w+) fields, each (\d+) char")

    result = sequence.result.split("\n")
    assert result[-1] == "", "the saved file should end in a newline"
    body = result[:-1]

    assert len(body) == lines_held, (
        f"the page says the buffer holds {lines_held} lines and it holds {len(body)}"
    )
    assert int(rows) == rows_long, "the page counts the rows two different ways"
    assert len(data_rows("\n".join(body))) == rows_long, (
        f"the page says {rows_long} data rows and the file has "
        f"{len(data_rows(chr(10).join(body)))}"
    )
    for row in data_rows("\n".join(body)):
        assert len(row.split("|")) == number(fields), f"wrong field count: {row!r}"
        assert len(row) == int(width), f"{len(row)} characters, not {width}: {row!r}"


@pytest.mark.xnedit
def test_the_finished_file_is_not_what_the_sequence_produces(
    sequence: Sequence,
) -> None:
    """The gap the page puts between its own output and the finished NED file.

    ``samples/A13L.mod.after`` is the same data by hand, with a column no
    command can invent and seven header lines nothing in the paste says how to
    fill. Offering it as the thing to check a run against tells a reader their
    correct run failed, which is why the difference is asserted rather than
    assumed.
    """
    line_count, column_count, our_columns = stated(
        r"the same data, (\d+) lines with (\w+) columns where this has (\w+)"
    )
    finished_text = FINISHED.read_text(encoding="utf-8")
    finished = finished_text.split("\n")[:-1]

    assert sequence.result != finished_text, (
        "the sequence produces samples/A13L.mod.after outright, so the gap the "
        "page describes has closed and the page is now the thing that is wrong"
    )
    assert len(finished) == int(line_count), (
        f"the page says the finished file is {line_count} lines and it is "
        f"{len(finished)}"
    )
    assert max(len(line.split("|")) for line in finished) == number(column_count), (
        f"the page says the finished file has {column_count} columns"
    )
    assert max(len(line.split("|")) for line in sequence.result.split("\n")) == number(
        our_columns
    ), f"the page says the sequence leaves {our_columns} columns"
