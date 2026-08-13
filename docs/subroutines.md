# Subroutines

Reusable subroutines from `macros/lib/`. These are appended to
`~/.xnedit/autoload.nm` rather than installed as menu commands, so they are
available to every macro from startup onward and add nothing to any menu:

```sh
cat macros/lib/text.nm >> "${XNEDIT_HOME:-$HOME/.xnedit}/autoload.nm"
```

Restart XNEdit afterwards.

Every name is prefixed `ned_` so it cannot collide with a built-in or with
someone's personal macros.

This page is generated from the library files by `tools/gen_docs.py`.

<!-- BEGIN GENERATED: subroutines -->

## `text.nm`

From [`macros/lib/text.nm`](https://github.com/sidereal-software/nedkit/blob/main/macros/lib/text.nm).

### `ned_trim()`

Strip leading and trailing spaces and tabs.

Note that ^ and $ anchor to line boundaries rather than string boundaries,
so passing a multi-line string trims every line in it. That is usually what
you want; if it isn't, split first.

### `ned_field()`

Return the Nth whitespace-separated field of a string, counting from 1.
Returns "" when the field doesn't exist.

    ned_field("NGC  4151   Sy1.5", 2)   ->  "4151"

### `ned_current_line()`

Return the text of the line the cursor is on, without its newline.

<!-- END GENERATED: subroutines -->
