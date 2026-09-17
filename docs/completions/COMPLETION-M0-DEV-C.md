# M0 — developer C — completion record

**Iteration:** M0, *Ground to stand on*.
**Lane:** C. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-a319e57ac3a444133`.
**Recorded** 17 Sep 2026, 01:44Z. **Extended** 01:56Z, when WI-5 landed and lane C's M0
was complete.

## What was finished

**Both of lane C's M0 items: S-2 — the anchor question, and WI-5 — the character grid
surface.**

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#76](https://github.com/replicant1/NewTerminalGame/pull/76) | S-2: the anchor question | `main` | `77c422e` |
| [#79](https://github.com/replicant1/NewTerminalGame/pull/79) | S-2: completion record and progress-log tail | `main` | `a33a4c6` |
| [#83](https://github.com/replicant1/NewTerminalGame/pull/83) | WI-5: the character grid surface | `main` | `9863a95` |

All merged by me. `r7/s-2-anchor-window` was cut from `main` at `4015c96` and merged with
`origin/main` at `c76bc37`; **no conflicts**, since S-2 touches only `docs/`.
`r7/wi-5-grid-surface` was cut from `main` at `a33a4c6` and merged with `origin/main`
twice, at `ddc250e` and `589902d`; **both merges conflicted in `tests/conftest.py`** — see
below.

**Files added by S-2:**

- `docs/findings/S-2-anchor-window.md` — the verdict, six measurement sections, seven
  instructions for WI-15, and plan section 9 item 4 posed as a three-option choice.
- `docs/prs/PR-S-2-anchor-window.md`, `docs/prs/PR-S-2-completion-record.md`.
- `docs/progress/r7-s-2-anchor-window.md`.

No code and no test, by the plan's own bar for S-2: *"nothing in the default suite may query
the desktop; the spike's conclusions live in the finding."*

**Files added by WI-5:**

| File | |
|---|---|
| `terminal_game/presentation/metrics.py` | WIN-2 as arithmetic: a 40 × 30 grid of a measured cell is a pixel rectangle, plus where each cell sits |
| `terminal_game/presentation/palette.py` | The six colours the specification names, as `#rrggbb` |
| `terminal_game/presentation/field.py` | The 40 × 30 field of glyph-and-colour — the data WI-4 and WI-12 produce |
| `terminal_game/presentation/surface.py` | The painter. **The only module in Presentation that names the toolkit** |
| `tests/test_metrics.py`, `tests/test_palette.py`, `tests/test_field.py`, `tests/test_surface.py` | 183 tests |
| `tests/conftest.py` | The withdrawn-root fixtures, added beside WI-1's and WI-4's |
| `docs/prs/PR-WI-5-grid-surface.md`, `docs/progress/r7-wi-5-grid-surface.md` | |

**No constant in WI-0 had to change**: `tools.layer_rule.PAINTING_MODULE` was already
`terminal_game.presentation.surface`, and that is what the painter is called.

## WI-5, and the four things section 5 asked it to establish

**WIN-2's pixel size is derived, never asserted.** The surface measures the real font at
construction. `Menlo 16 → advance 10, linespace 19 → 400 × 570`, which I measured myself on
a withdrawn root before writing anything, independently confirming S-1.
`metrics_match_measurement()` means a substitution shows up as a disagreement rather than
as a window that is quietly the wrong size.

**SCRN-7, flicker.** 2400 canvas items created once and only ever reconfigured, so the
picture is never torn down — which is what flicker is. One flush per frame. The tests
compare item **identity** across repaints, including across a full-to-blank transition,
because that is what catches a delete-and-recreate painter; a count does not, since such a
painter puts the same number back.

**SCRN-7, the caret.** `takefocus=0`, no focused item, `insertwidth=0`, and the surface
creates exactly one widget and it is a `Canvas`.

**SCRN-2.** No method here draws anything. The only route to the picture takes a `Field`,
and a `Cell` is exactly one character and two colours, so there is nothing for an image to
travel in. `item_types()` reads back what is on the canvas: only `text` and `rectangle`.

**The default suite puts no window on the screen**, asserted rather than assumed —
`state() == "withdrawn"`, not mapped, not viewable, re-checked after building a surface and
again after painting a frame.

## Two conflicts, both mine, both resolved without escalating

`tests/conftest.py` — pytest gives a directory exactly one — conflicted twice while WI-5 was
in flight: **add/add with developer B's WI-1** (maze `draw` and `sound_maze` fixtures), then
**content with developer A's WI-4** (the specimen-picture parse). Neither was a disagreement
about anything real; three unrelated fixture sets now share the file under three headings,
and **not a line of either developer's was changed** beyond two wording corrections my own
section made necessary ("two unrelated sets" → "three", and their "the second half of this
file" → "the middle"). The whole suite was run after each resolution, not just my half.

## Things I corrected in my own work

**Two tests were weaker than their names claimed** and I fixed them rather than leaving
them: both counted canvas items where only item identity catches a delete-and-recreate
painter.

**`repaint()` had a real flaw** — it went through `present()`'s diff, so a cell the painter
believed was blank but which was wrong on the canvas would be skipped, which is exactly the
case the method exists for. Rewritten to write every cell unconditionally, and pinned by a
test that disturbs one canvas item from outside and checks the repaint puts it back.

**A doubt recorded rather than papered over:** whether the painter touches *only* the
changed cells is not observable from outside, because the picture is identical either way.
Everything that matters is pinned; the diffing itself is a performance property, and I did
not add spy machinery for it.

**A missing test, now written.** S-1 measured that every glyph the game draws shares one
cell width and recorded it in a finding; nothing re-ran it. That belongs to the
cell-metrics responsibility, so it is now three tests — every wall glyph, every actor and
dot glyph, and a guard that the cell width is not zero so the first two cannot pass
vacuously.

## The verdict

> **The anchor can be read with no permission of any kind, for any application, in about
> 3 ms** — `CGWindowListCopyWindowInfo` returns every on-screen window front-to-back with
> owner and bounds. **The architect's assumption A2 is wrong on its premise.**

Proven on both sides of the permission gate. The same probe run detached through
`launchctl submit`, so its responsible process is launchd rather than Terminal — the case
caution C3 turns on — returned **no window titles** (`name=None`, 3 of 31) and **identical
geometry to the pixel**. `kCGWindowName` is gated behind Screen Recording; `kCGWindowBounds`
is not, and WIN-4 needs only the bounds.

## The caveat that decides what happens next

**The crash was not `ctypes` into CoreGraphics. It was `ctypes` into CoreGraphics inside a
process with a live Tk root.**

| Context | Runs | Outcome |
|---|---|---|
| plain Python process, no Tk | 8 | clean every time |
| process with a live `tkinter.Tk()` root | 3 | crashed every time |

Three crash reports were written. The conductor has ruled `ctypes` into
Objective-C/AppKit/Quartz/CoreGraphics off limits for agents, and — pending the user's
answer — for shipped code too. So **WI-15 implements nothing until the user chooses**, and
the finding poses the choice as three options: **A** CoreGraphics in a short-lived child
process before Tk exists (meets WIN-4 in general, grants nothing — my recommendation),
**B** AppleScript (a dialog per application, and defeated anyway by the defect below),
**C** no anchor (WIN-4 not met).

## Two defects found in routes the project was about to rely on

1. **Terminal's AppleScript `position` is out by the height of the display** on any window
   not on the main one — five Terminal windows measured, all three off-main out by exactly
   1440 px, both on-main correct. Its `bounds` is right. The architect's V3 placed a window
   at "position + (40, 40)"; on this desktop that lands 1440 px away. This kills option B on
   its own merits, independently of the consent dialog.
2. **The CoreGraphics route crashed 3 of 3 inside a live Tk process**, 0 of 8 outside one.
   One real signature error was found and corrected along the way
   (`CFPropertyListCreateData`'s `format` is `CFIndex`, not `uint32`), so the fault may be
   mine rather than the platform's; I did not establish which, on the conductor's ruling.

## One measurement that belongs to nobody yet

**`root.update()` blocks forever on Tcl/Tk 8.5 under macOS 26 once the window is mapped.**
`Tk()`, `withdraw()`, `geometry()`, `deiconify()` and `update_idletasks()` all return;
`update()` never does, pinned by a `faulthandler` traceback at `tkinter/__init__.py:1314`.

This does not contradict S-1. S-1's headless verdict measured `update_idletasks()` and
`update()` on a **withdrawn** root, which never maps and never reaches this. Mine is the
untested half: a root that has been `deiconify()`'d. It lands on **WI-5 and WI-6**, the two
items that have to drive a *visible* window.

## Suite state

```
.venv/bin/python -m pytest -q          →  418 passed, 0 failed, 0 skipped
```

Run from the repository root, in a `.venv` built from `/usr/bin/python3` 3.9.6 with pytest
8.4.2. Every run this lane made, with the head it was run on:

| When | Head | Result |
|---|---|---|
| 01:43:11Z, before marking #76 ready | branch merged with `origin/main` `c76bc37` | 56 passed, 0 failed, 0 skipped |
| 01:43:51Z, before merging #76 | same | 56 passed, 0 failed, 0 skipped |
| 01:44:20Z, after #76 landed | `77c422e`, `main` with S-2 in it | 56 passed, 0 failed, 0 skipped |
| 01:45:21Z, before merging #79 | branch | 56 passed, 0 failed, 0 skipped |
| 01:45:53Z, after #79 landed | `a33a4c6` | 56 passed, 0 failed, 0 skipped |
| 01:46:34Z, WI-5 baseline before touching anything | `a33a4c6` | **81** passed, 0 failed, 0 skipped |
| 01:52:29Z, WI-5 written | branch | 264 passed, 0 failed, 0 skipped |
| 01:53:22Z, after resolving the WI-1 conflict | branch merged with `ddc250e` | 357 passed, 0 failed, 0 skipped |
| 01:54:45Z, after resolving the WI-4 conflict | branch merged with `589902d` | 418 passed, 0 failed, 0 skipped |
| 01:55:09Z, before merging #83 | same | 418 passed, 0 failed, 0 skipped |
| **01:55:35Z, after #83 landed** | **`9863a95`, `main` with WI-5 in it** | **418 passed, 0 failed, 0 skipped** |

**S-2 adds no test**, by the plan's own bar for it, so 56 is the count `main` already
carried. **WI-5 adds 183**, against a baseline of 81 when its branch was cut; the rest of
the 418 arrived from lanes A and B while WI-5 was in flight.

`lsappinfo visibleApplicationCount` was 7 before and after every run: **the default suite
puts no window on the screen**, and it now says so in four of its own assertions rather
than only in this document.

## Window hygiene

No Terminal window was created and **no window was closed** — not one `close` command was
issued, all run. The only windows that reached the screen were this spike's own Tk root, in
four attempts, each identified by the process's own object reference and each now dead with
its process. Every probe carried a hard deadline (`signal.alarm`,
`faulthandler.dump_traceback_later(exit=True)`, or a `subprocess` timeout). The desktop was
re-checked after every crash rather than only at the end: layer-0 window count back to its
pre-spike 7 each time, no surviving process each time. The launchd job `s2anchorprobe` was
submitted at 01:40:06Z and removed at 01:40:10Z. Three crash reports sit in
`~/Library/Logs/DiagnosticReports/`; no crash dialog is on screen, and they are not mine to
dismiss.

**WI-5 opened no window at all.** Its measurements and its whole test suite run on a
withdrawn root, which S-1 measured never maps. That is asserted, not assumed —
`tests/test_surface.py` checks `state() == "withdrawn"`, `winfo_ismapped()` false and
`winfo_viewable()` false, after building a surface and again after painting a frame.

## What still needs a human, from this lane

1. **WIN-4: pick a route.** S-2 proved the anchor is readable with **no permission of any
   kind**, for any application, so plan section 9 item 4 is no longer "grant or decline".
   It is: **A** CoreGraphics in a short-lived child process before Tk exists (meets WIN-4
   in general, grants nothing — my recommendation), **B** AppleScript (a dialog per
   application, and defeated anyway by the `position` defect S-2 measured), **C** no
   anchor (WIN-4 not met). One sentence settles it. If A, WI-15 also needs to know whether
   the `ctypes` prohibition covers shipped product code.
2. **The Dock tile, now that the default suite constructs a Tk root.** S-1 raised it; WI-5
   is the item that makes it real, because the surface tests are in the default suite. A
   "Python" tile appears for the second the suite runs. *Steps:* run
   `.venv/bin/python -m pytest -q` and watch the Dock. *A good answer:* "fine" — nothing
   changes — or "no", in which case the surface tests need the `needs_window` marker and
   the default suite loses its coverage of the painter.
3. **Whether the box-drawing glyphs *look* joined.** Every measurement in S-1 and WI-5 is
   about *advance*, the space a glyph claims, never about ink. Whether a run of `═` reads
   as one unbroken double line is first visible at WI-7 and belongs in WI-17's pack.
