# S-1 — toolkit feasibility

**Branch:** `r7/s-1-tk-feasibility`, cut from `main` at `4015c96`.
**Base:** `main`. Not stacked on anything.
**Adds:** `docs/findings/S-1-tk-headless.md` and `docs/progress/r7-s-1-tk-feasibility.md`.
No source, no tests — see *Deviation* below.

---

## The verdict, which is what the plan asked for

> **Yes. The Presentation layer can be tested headlessly on Tcl/Tk 8.5.**

**Assumption P8 holds in both halves**, so WI-5, WI-6, WI-7, WI-14 and WI-16 proceed
exactly as written, and **human item 5 of section 9 — consent to install a modern Tk —
does not open**. Nothing was installed.

## The three things S-1 was sent to find out

**1. Can a Tk root be built in a test without a window reaching the screen?** Yes, if
`withdraw()` is the statement immediately after `Tk()`. Tk defers mapping to idle time, so
a root withdrawn before the first `update()` is never shown at all. After pumping the event
loop as far as it will go: `state=withdrawn`, `winfo_ismapped()=False`,
`winfo_viewable()=False`, `winfo_exists()=True`. A child `Toplevel` behaves the same. It
also holds inside a venv built from `/usr/bin/python3`.

Confirmed from **outside** the process, so it does not rest on Tk's own word:
`/usr/bin/lsappinfo front` returned the same ASN before, during and after — the frontmost
application never changed and nothing stole focus.

**2. Cell metrics of a candidate font at a candidate size.**
**Menlo 16 → advance 10 px, linespace 19 px, so a 40 × 30 window is 400 × 570 px.**

**3. Do the double-line box and block glyphs share one cell width?** Yes — at *every*
Menlo size from 8 to 36, every glyph the game draws measures exactly `measure("M")`. The
box characters need no special case. Menlo is also the **only** font on this machine that
owns them all: Monaco, Courier New, Andale Mono and PT Mono all substitute part of the
range back to Menlo, and Monaco renders U+2592 one pixel narrow. SF Mono, Courier,
Consolas and DejaVu Sans Mono are absent.

## The finding nobody asked for, and it constrains WI-5

`Font.measure()` returns whole pixels, but Tk's own string layout uses a fractional
advance at some sizes. So a 40-character row drawn as one string is **not** always
40 × the per-character advance:

| Menlo size | `measure(c*40) == 40*measure(c)`? | worst drift over 40 cells |
|---|---|---|
| 8 – **16** | **yes** | 0 px |
| 17 | no | 9 px |
| 18 | no | 7 px |
| 19 | no | 18 px |
| 20 | no | 2 px |
| 24 | no | 18 px |
| 30 | no | 2 px |
| 36 | no | 13 px |

**Size 16 is the largest Menlo size with an exact integer cell grid**, and at that size a
row placed cell by cell at `x = column * 10` and the same row drawn as one string land on
identical pixels. That is why 16 is the recommendation: it leaves **WI-5's repaint strategy
free** — per cell, per row, or dirty-region only (contradiction C-5 leaves that to WI-5),
all give the same picture. Above 16, WI-5 would be forced into per-cell placement.

If a human later judges 16 too small (human item 3, assumption P4), **WI-19 must read the
table in the finding before picking the new constant** — every size above it breaks the
exact grid.

## Deviation needing a ruling

**No test is committed on this branch, although S-1's bar in section 5 says one should be
if the conclusions can be pinned headlessly — and they can.** WI-0 is creating the package
layout and the suite in parallel with this spike; a test committed here would have had to
guess at that layout and would race it. **The conductor ruled it be left to WI-5**, which
owns the cell-metrics responsibility and is the first item that needs it. The exact
assertions WI-5 should write, including the control that stops the substitution check
passing vacuously, are written out in **section 7 of the finding**.

Consequently there is **no suite to run on this branch** and no test counts to report. The
branch adds two documents and nothing executable.

## For a human (an addition to section 9)

**Constructing a Tk root — even a withdrawn one — puts a "Python" tile in the Dock** for
the life of the process. It is not a window (WI-5's and WI-16's bar is still met) and it
never takes focus, but it is visible and nobody agreed to it. A control process that holds
open the same length of time without importing `tkinter` has no Launch Services record at
all, so it is Tk's doing, not the interpreter's. I found no way to suppress it on Tk 8.5.
Section 5 of the finding has the steps and what a good answer looks like.

## What S-1 could not determine

**Whether Menlo's box-drawing ink actually spans the full cell**, so that a run of `═`
reads as one unbroken double line rather than a dashed one. Every measurement here is of
*advance*, not ink. Tk 8.5 has no canvas-to-image path and this interpreter has no PyObjC
and no PIL, so it cannot be rasterised without installing something. **The first chance to
see it is WI-7's window; WI-17 should put it in front of a person.** This is the specific
risk the technical lead named in section 1.2, and it is still open.

## Window hygiene

Every probe had a `SIGALRM` hard deadline, none contained a `mainloop`, and none could
block. No Terminal window was opened, so none needed reaping. No window was ever mapped,
no permission dialog was raised, and `lsappinfo` — which needs no permission — was the only
thing that touched the desktop.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
