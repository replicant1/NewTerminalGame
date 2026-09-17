# WI-15 — where the window lands

**Branch:** `r7/wi-15-window-placement`, cut from `main` at `2599b1a`
**Lane:** B (moved from C) · **Iteration:** M2 · **Depends on:** WI-6, S-2
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**763 passed, 0 failed, 0 skipped, 2 deselected** (705 inherited, 58 new)

**Crash reports:** `~/Library/Logs/DiagnosticReports/Python-*.ips` — **14
before, 14 after**, newest still `2026-09-17-120051`. Nothing new.

---

## WIN-4 is met under assumption P2 and not in general

The plan asks for that sentence and it is the honest one.

S-2 measured three routes to the anchor and **the choice between them is an
unanswered question with the user** (plan section 9, item 4). So this item
builds everything that does not depend on the answer, and **chooses no
route**:

* **Option A** — CoreGraphics via `ctypes`. Currently **prohibited**, product
  code included. Not implemented, not imported, not referenced in code.
* **Option B** — AppleScript. Prompts per application, and S-2 found it
  defective anyway. Not used.
* **Option C** — no anchor. **This is what ships**, as `NoAnchor`: it reads
  nothing, so it cannot prompt and cannot fail. With it the window is
  **centred on the main display**, which is a sane default and is **not
  WIN-4**.

Reading the anchor is a one-method seam. Whichever route the user permits
becomes a small, tested substitution rather than a rewrite — and the test
`test_the_seam_accepts_anything_with_a_read_method` exists to say so.

**Nothing in this item queried the desktop, ran AppleScript, used `ctypes`,
or caused a permission dialog.** No window reached the screen.

---

## What is here

`terminal_game/shell/placement.py` — the arithmetic, the fallback, the seam,
and the geometry formatting. Names no toolkit.

`terminal_game/shell/window.py` — gains `move_to(point)` and `position()`
**and nothing else**, which is the whole of what WI-15 is permitted to add to
the window owner. Everything else in that module stays lane C's.

---

## The two measurements this item exists to encode

Both were left open by S-2, which said settling them was cheap for WI-15.
Both are written up in `docs/findings/WI-15-tk-geometry-signs.md`.

### 1. Tk accepts a negative origin — but the sign is part of the grammar

`+-877+-1348` is legal and round-trips exactly, so a window *can* be placed
on a display whose origin is negative. S-2's worry does not bite.

The trap is the format string:

| written as | produces | Tk reads it as |
|---|---|---|
| `"+{}+{}".format(-877, -1348)` | `+-877+-1348` | x = −877, y = −1348 |
| `"{:+d}{:+d}".format(-877, -1348)` | `-877-1348` | 877 from the **right**, 1348 from the **bottom** |

**Both are legal. They mean different places.** The second is the tidier way
to format a signed pair, it is what a reasonable person writes, and it is
**correct on the main display** — where x and y are positive — and wrong by
about a display width everywhere else. It fails exactly where it is least
likely to be tested.

That is the same shape as the defect S-2 found in Terminal's own AppleScript
`position`, which disagrees with its own `bounds` by exactly the display
height off the main screen. Two unrelated systems, one class of mistake.

`geometry_string` writes that format **once**, and
`test_the_tidy_sign_format_would_mean_something_else_entirely` pins the
difference so nobody tidies it.

Reading it back has the same trap the other way round, so
`position_in_geometry` **refuses** the from-the-edge form rather than
guessing — `"1x1-877-1348"` gives `None`, not `Point(-877, -1348)`.

### 2. Do not clamp to "the screen"

`winfo_screenwidth()` × `winfo_screenheight()` report **1512 × 982** — the
main display only — and `vrootx`/`vrooty` are both 0. Tk has no knowledge
through those calls of the displays at `(-3509, -1440)` and `(-949, -1440)`.

So a bounds check written against them would **reject every valid position on
two of the three displays**. **Nothing clamps**, and there is a test per
display that fails if anybody adds a clamp, an `abs`, or a `max(0, ...)`.

---

## Graceful degradation, the other half of the bar

> *"a failure to read the anchor degrades to a sane default rather than
> crashing or prompting."*

`anchor_from` swallows any exception from a reader and answers `None`,
deliberately and broadly: there is no useful distinction between the ways
reading an anchor can fail and the response to all of them is the same one. A
missing permission is a reason to put the window somewhere sensible, never a
reason for the game not to start.

Tested with four different failures — `PermissionError`, `OSError`,
`ValueError`, `RuntimeError` — because a handler that caught only one kind
would be worse than none.

---

## A false claim my own test caught

I wrote in `position()`'s docstring that a freshly built window has no
position. **It has one**: Tk gives a fresh toplevel `(5, 38)` on this build.

That matters beyond the docstring. It means **`position()` answering
something is not evidence that anything placed the window** — a test checking
placement by asking whether a position exists would pass without the
placement code being called at all. The docstring is corrected and the test
now moves to distinctive coordinates and checks those.

## Where the tests sit

`tests/test_placement.py` (49) touches no toolkit at all — every case is a
supplied number, which is what the plan's bar asks for. `tests/test_window_placement.py`
(9) owns only **the join**: that `move_to` really moves the window and that a
negative coordinate survives the trip through a real Tk. What the arithmetic
computes is pinned next door and is not re-asserted through a bigger object.

Its fixture is **local**, not in `conftest.py`: WI-6's own `window` fixture
lives in `tests/test_window.py`, and the conftest is a named contention point.
This adds to neither.

## Deviations needing a ruling

1. **`position()` is additive.** WI-15 is meant to add "placement and nothing
   else". A setter with no getter cannot be tested through the real window at
   all, so I judged the reader part of the placement. Say if it should go on
   lane C's side of the line.
2. **`anchor_from` catches bare `Exception`.** Normally indefensible; here it
   is the requirement. Named because it will look wrong to a reviewer who has
   not read the bar.
3. **`Rect` and `Point` are new shell vocabulary.** WI-17 may want them.
4. **The `OFFSET` constant is a tuple, not two constants**, so P3 is one thing
   to change rather than two.

## Contradictions found

**None**, but one thing worth stating plainly: **the plan's WI-15 bar can be
fully met while WIN-4 is not.** The bar asks for the arithmetic against a
supplied anchor and for graceful degradation, and both are done and tested —
but with no permitted anchor reader, the shipped behaviour is option C and
the player's last window is not followed. That is not a contradiction in the
plan; it is the gap between what the bar tests and what the requirement
promises, and it should not be read off the green suite as WIN-4 being done.

## What needs a human

**One, and it is the item's blocker, not a detail.**

**Rule on how the anchor is read** (plan section 9, item 4). Until then WIN-4
is met under P2 only. The three options and their measured costs are in
`docs/findings/S-2-anchor-window.md`; the substitution point is
`placement.AnchorReader`, and swapping it is a small tested change.

*If option A is permitted*, S-2's own guidance applies: read the anchor
**before Tk is initialised** or in a short-lived child process (3 crashes out
of 3 reading it in-process), and exclude the game's own pid.

*If nothing is permitted*, the shipped behaviour above is already correct and
nothing more is needed — but WIN-4 should be recorded as not met rather than
quietly passing.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
