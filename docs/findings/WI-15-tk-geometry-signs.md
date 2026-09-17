# Tk's geometry string, and the sign that means two different things

**Measured by developer B on 17 September 2026 at 02:12Z**, on the machine
this project is being built on, from `main` = `2599b1a`. Python 3.9.6,
Tcl/Tk 8.5, macOS 26.6.2.

S-2 left this open and said it was cheap for WI-15 to settle
(`docs/findings/S-2-anchor-window.md`, "what WI-15 should do", item 6):

> **Whether Tk's `wm geometry +x+y` uses the same space is NOT established** —
> the probe that would have settled it is one of the three that crashed. It is
> cheap for WI-15 to settle, and note that Tk's geometry string has no natural
> spelling for a negative x: `+-877+-1348` is what falls out of naive
> formatting and it needs checking before it is relied on.

It is settled, in the good direction, with one trap that is worth more than
the answer.

## What was measured

On a withdrawn Tk root — never mapped, no `update()`, no event loop, one root
in the process, no window on anybody's screen.

| set | read back |
|---|---|
| `400x570+100+200` | `1x1+100+200` |
| `400x570+0+0` | `1x1+0+0` |
| `400x570+-877+-1348` | `1x1+-877+-1348` |
| `400x570+-3509+-1440` | `1x1+-3509+-1440` |
| `400x570+1512+0` | `1x1+1512+0` |
| `400x570-877-1348` | `1x1-877-1348` |

Also: `winfo_screenwidth()` × `winfo_screenheight()` = **1512 × 982**, and
`winfo_vrootx()` / `winfo_vrooty()` = **0, 0**.

The `1x1` is an artefact of reading geometry from a window that has never
been realised; the position half is what was being measured and it round-trips
exactly.

## Answer 1 — Tk accepts a negative absolute origin

`+-877+-1348` is legal and round-trips unchanged. A window can be placed on a
display whose origin is negative, which on this desk means the displays at
`(-3509, -1440)` and `(-949, -1440)`. The worry S-2 raised does not bite.

## Answer 2 — but the sign is part of the grammar, not part of the number

This is the part worth keeping.

```
"+{}+{}".format(-877, -1348)     ->  "+-877+-1348"
"{:+d}{:+d}".format(-877, -1348) ->  "-877-1348"
```

**Both are legal Tk geometry strings. They mean different places.**

| string | meaning |
|---|---|
| `+-877+-1348` | x = −877, y = −1348. An absolute position. |
| `-877-1348` | 877 from the **right** edge, 1348 from the **bottom** edge. |

Tk's grammar is `WxH±X±Y`, where the leading `+` or `-` says *which edge the
number is measured from*. A second sign inside the field is part of the
number.

`"{:+d}{:+d}"` is the tidier-looking way to format a signed pair and it is
what a reasonable person writes. It is **correct on the main display**, where
x and y are positive, and wrong by roughly the width of a display everywhere
else — so it fails exactly where it is least likely to be tested and most
likely to be blamed on something else.

This is the same shape as the defect S-2 found in Terminal's own AppleScript
`position`, which disagrees with its own `bounds` by exactly the display
height off the main screen. Two unrelated systems, one class of mistake.

`terminal_game/shell/placement.py` writes that format string **once**, in
`geometry_string`, and `tests/test_placement.py` pins the difference so
nobody tidies it.

### Reading it back has the same trap

`position_in_geometry` is the inverse, and it **refuses** the from-the-edge
form rather than guessing:

```
"1x1+-877+-1348"  ->  Point(-877, -1348)
"1x1-877-1348"    ->  None
```

Silently reading `-877` as `x = -877` would be wrong by a display width.
There is no way to convert it without knowing which display, so it answers
`None`.

## Answer 3 — do not clamp to "the screen"

`winfo_screenwidth()` and `winfo_screenheight()` report **1512 × 982** — the
main display only — and `vrootx`/`vrooty` are both 0. Tk, through these calls,
has no knowledge of the two displays at negative origins.

So a bounds check of the form "is this position on the screen?" written
against those numbers would **reject every valid position on two of the three
displays** and push the window back onto the first. Nothing in
`placement.py` clamps, and there is a test per display that fails if anybody
adds a clamp, an `abs`, or a `max(0, ...)`.

## Answer 4 — position can be set without disturbing the size

A geometry string with no `WxH` changes only the position. WI-6 owns the
window's size (400 × 570, from P4's Menlo 16 and a 10 × 19 cell), and WI-15
must not overrule it, so `geometry_string` emits the position alone.

Measured only as far as a withdrawn window allows: the position round-trips,
and the string carries no size to overrule anything with. **Not** measured:
that the requested size survives on a *mapped* window, because reading size
back from an unrealised window returns `1x1` regardless. If that ever needs
proving it belongs with WI-17's human checks, not in the default suite.

## Reproducing it

`GameWindow.move_to` and `position()` exercise all of this, and
`tests/test_window_placement.py` runs it through a real Tk on the shared
withdrawn root. **No window reaches the screen**; the crash-report count in
`~/Library/Logs/DiagnosticReports/Python-*.ips` was 14 before and 14 after,
with nothing new since 02:00:51Z.
