# WI-7 — do the box-drawing glyphs actually join up? Measured from the font.

**Measured** 17 Sep 2026 at 02:13Z, from the worktree
`.claude/worktrees/agent-ad9b18e196f2c349f`, against
`/System/Library/Fonts/Menlo.ttc` (2,156,036 bytes) on macOS 26.6.2.

This answers **human item 8** (assumption **P10**), which asked somebody to look at the
first real window and say whether a run of `═` reads as one unbroken double line or a
dashed one.

---

## Why this is a measurement and not the impression that was asked for

**I cannot see the screen.** WI-7 put a real 400 × 570 window on the user's desktop and it
painted the specification's own picture, but an agent has no eyes on it, and the window was
up for well under a second under a watchdog. *"It looked continuous to me"* is not something
I am in a position to say, and saying it would be worse than saying nothing.

So I measured the thing the impression was a proxy for. **The font knows.** A TrueType
`glyf` record begins with the glyph's bounding box and `hmtx` gives its advance width, so
*does the ink reach the edge of the cell* is arithmetic on a file the system already ships.
Pure `struct` parsing — no install, no `ctypes`, no permission, nothing on the screen. It
is what S-1 and WI-5 could not do, because both asked **Tk** for advances and Tk will not
talk about ink.

---

## The verdict

> **Menlo's box-drawing glyphs are designed to tile, and they overlap slightly at every
> joining edge rather than merely meeting.** A run of `═` will read as one unbroken double
> line, and a column of `║` likewise. There is no gap for a seam to show through.

---

## The numbers

Menlo Regular, taken from the 4-font collection. `unitsPerEm` 2048, 3157 glyphs,
`hhea` ascender 1901, descender −483, lineGap 0.

At the configuration WI-5 actually uses — **Menlo 16, cell 10 × 19 px** — one cell is
**1233 font units wide** (9.63 px, which Tk rounds to 10) and spans **+1920 to −512 font
units** vertically, from Tk's own ascent 15 and descent 4.

### Horizontal

Every glyph with an east or west arm has ink from **xMin = −20 to xMax = 1253** — that is,
**past both edges of its own advance**:

| | |
|---|---|
| overshoot to the left of the cell | **0.156 px** |
| overshoot to the right of the cell | **0.156 px** |

`═`, `╦`, `╩`, `╬` and the four corners all share those bounds. That overshoot is not an
accident of rounding: it is the same on both sides and it is exactly what a font designer
does to stop a hairline appearing between tiles.

### Vertical

Every glyph with a north or south arm has ink from **yMin = −618 to yMax = 1992**, against
a cell running +1920 to −512:

| | |
|---|---|
| overshoot above the top of the cell | **0.562 px** |
| overshoot below the bottom of the cell | **0.828 px** |

So `║`, `╠`, `╣` and the crossings overlap their neighbours vertically too.

### Every glyph the game draws

| glyph | advance | xMin | xMax | yMin | yMax | reaches the cell edge where it has an arm? |
|---|---|---|---|---|---|---|
| `═` U+2550 | 1233 | −20 | 1253 | 324 | 840 | **yes**, east and west |
| `║` U+2551 | 1233 | 376 | 856 | −618 | 1992 | **yes**, north and south |
| `╔` U+2554 | 1233 | 376 | 1253 | −618 | 840 | **yes**, south and east |
| `╗` U+2557 | 1233 | −20 | 856 | −618 | 840 | **yes**, south and west |
| `╚` U+255A | 1233 | 376 | 1253 | 324 | 1992 | **yes**, north and east |
| `╝` U+255D | 1233 | −20 | 856 | 324 | 1992 | **yes**, north and west |
| `╠` U+2560 | 1233 | 376 | 1253 | −618 | 1992 | **yes**, three arms |
| `╣` U+2563 | 1233 | −20 | 856 | −618 | 1992 | **yes**, three arms |
| `╦` U+2566 | 1233 | −20 | 1253 | −618 | 840 | **yes**, three arms |
| `╩` U+2569 | 1233 | −20 | 1253 | 324 | 1992 | **yes**, three arms |
| `╬` U+256C | 1233 | −20 | 1253 | −618 | 1992 | **yes**, all four |
| `█` U+2588 | 1233 | −20 | 1253 | −512 | 1576 | spans horizontally; see below |
| `■` U+25A0 | 1233 | 6 | 1227 | −78 | 1142 | n/a — a lone square, nothing to join |
| `▪` U+25AA | 1233 | 219 | 1013 | 135 | 929 | n/a — the dot, deliberately small |
| `M` *(control)* | 1233 | 36 | 1095 | 0 | 1488 | an ordinary letter sits inside its cell |

**The control is the last two rows.** An ordinary `M` stops well inside its advance, and the
dot `▪` stops a long way inside it — so "ink reaches the edge" is a real property of the
box-drawing glyphs and not something true of every glyph in the font. The corners are the
sharper control still: each one reaches the edge on **exactly the two sides where it has an
arm** and stops at the centre stub on the other two. A font that merely drew fat glyphs
would not do that.

---

## What this does not settle

**The font's geometry is not the renderer's output.** These are outlines; what reaches the
screen has been hinted, scaled and antialiased at 16 pt, and at 0.156 px the horizontal
overlap is a fraction of a pixel. The design intent is unambiguous — **overlap, not
abutment, and certainly not a gap** — but whether the rasteriser preserves it is a
different question and this measurement cannot answer it.

**What it does do is change the question the user is asked.** Human item 8 was *"is this
font unusable for the maze?"*, which is a decision about whether to go and ask for a
different toolkit. That worry is answered: the glyphs are built to tile. What is left is
*"does it look right to you?"* — an ordinary cosmetic check of the same kind as
human item 3, and WI-17 should put it that way rather than as a risk.

**I did not look at the window.** WI-7 mapped one and closed it, and I observed only that it
mapped, that it carried the composed frame, that it was 400 × 570, and that it closed by
itself. Nobody has yet seen this game.

---

## Reproducing it

The parser was a throwaway and lives outside the repository. What it does, in order:
read `Menlo.ttc`, walk the `ttcf` header to the four fonts and pick *Menlo Regular* by its
`name` table entry 4; read `head` for `unitsPerEm` and `indexToLocFormat`, `maxp` for the
glyph count, `hhea` for `numberOfHMetrics`; resolve each character through the best
available `cmap` subtable (format 12 preferred over format 4); index `loca` to find the
glyph's `glyf` record and read the four `int16` at offsets 2, 4, 6, 8 — that is the
bounding box; and read the advance from `hmtx`. Then compare the box against the cell,
where the cell is `advance` wide and runs from `+ascent` to `−descent` in font units, using
**Tk's own rounded ascent and descent** rather than `hhea`'s, because Tk's are what lay the
text out.

No part of it touches the toolkit, the screen, or any permission-gated interface.
