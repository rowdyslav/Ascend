# Flet 0.86 compatibility notes

Workarounds required by the pinned flet version (0.86.x). Keep this list in sync
whenever a workaround is added or removed.

## 1. SegmentedButton.selected must be a list (not a set)
`ft.SegmentedButton(selected={...})` (a Python set) is silently accepted by the
constructor, but msgpack cannot serialize a set → the whole session crashes.
Always pass a list: `selected=[str(period_days)]`.

## 2. RoundedRectangleBorder radius must be a keyword argument
`ft.RoundedRectangleBorder(12)` (positional radius) builds fine server-side, but
the web client fails to lay the button out and paints the whole page grey
(#b7b7b7) once it scrolls into view. Use `ft.RoundedRectangleBorder(radius=12)`.

## 3. `expand` child inside `Row(wrap=True)` greys out the whole page
A `Row` with `wrap=True` that contains an `expand=True` child (e.g. a full-width
`Dropdown`) renders as a full-viewport grey slab. Keep `expand` children in their
own non-wrap row and use fixed widths inside wrap rows.
