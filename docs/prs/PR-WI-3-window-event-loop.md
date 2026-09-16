# WI-3 — The window and its event loop

**Developer:** DEV-C · **Branch:** `r6/wi-3-window-event-loop` · **Base:** `main`
**Milestone:** M0 · **Effort budgeted:** 3 developer-days

## What this is

The process's own native window, under the adopted architecture (candidate 2). The
application creates the window, titles it, sizes it, places it, and closes it itself.
On top of that: a repeating timer at the ghost's cadence, raw key delivery, and a way
to end the session that reaps the window exactly once — on the failure path as well
as the success path.

Nothing here draws, and nothing here knows what a maze is.

## The boundary with WI-2

The plan fixes it and this branch stays on its side of it:

> **WI-3 owns the window, the timer and key delivery. WI-2 owns everything inside the
> pixels.**

Concretely, one thing crosses in each direction and no more:

- **WI-2 → WI-3:** the window owner is *told* a `PixelSize`. It never asks how that
  number was arrived at, and it contains no font, no cell metric and no character
  count. `WindowOwner(toolkit, size, collaborator)`.
- **WI-3 → WI-2:** `WindowOwner.open()` returns an opaque **drawing target** — the
  thing the character grid surface paints into. The Shell never paints on it and
  never inspects it.

## What is in it

| File | What it is |
| --- | --- |
| `terminal_game/shell/toolkit.py` | The seam. `Toolkit` (abstract), and the plain values `PixelSize`, `ScreenPosition`, `KeyPress`, `WindowSpec`. Imports no toolkit. |
| `terminal_game/shell/tk_toolkit.py` | **The only module in the application that names the windowing toolkit.** The thinnest translation from that seam to Tk. |
| `terminal_game/shell/cadence.py` | GHOST-1 as two constants: 7 ticks a second, 143 ms. |
| `terminal_game/shell/tick_timer.py` | The repeating tick, built from the toolkit's one-shot scheduler. |
| `terminal_game/shell/window_owner.py` | The window owner: creates the window, delivers ticks and keys to a collaborator it is given, ends the session once. |
| `tests/shell/recording_toolkit.py` | A `Toolkit` that records calls in order and opens nothing. This is what keeps the suite window-free. |
| `tools/probe_tk_window.py` | **Not part of the suite.** A bounded, self-quitting probe that opens one real window for about a second, measures what Tk actually did, reaps it, and prints JSON. Run deliberately. |

## Decisions worth knowing about

**The repeating tick is built, not bought.** Tk offers a one-shot `after`. `TickTimer`
delivers the tick and *then* arms the next one, so that a tick whose collaborator
raised leaves nothing scheduled to fire into a half-dead session, and a tick that ends
the session does not arm another.

**A key becomes a plain value at the seam.** The Tk adapter turns Tk's event object
into `KeyPress(keysym, char)` and the owner hands that on untouched. WI-9's input
translator lives in Presentation, which may not name the toolkit, so the value has to
be toolkit-neutral before it leaves the Shell.

**A collaborator that raises loses its window, and the exception is re-raised.**
Swallowing it would make a defect look exactly like a clean exit. `run()` reaps in a
`finally`, so an event loop that falls over reaps too.

**The order of shutdown is asserted, not assumed.** Stop the timer, leave the event
loop, then destroy the window — and a test pins that ordering, because a tick firing
into a window that has already gone is the failure this item exists to prevent.

## Tests

`/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"` — **50 passed, 0
failed, 0 skipped.**

**No test in this branch constructs a toolkit window.** The toolkit is stood in for by
a recording double throughout. The Tk adapter's own tests check that it answers the
whole seam and that its key translation loses nothing, neither of which needs a window.

What the tests own, by file:

- `test_cadence.py` — that the interval really is 1000/7 rounded, and gives about
  seven ticks a second.
- `test_tick_timer.py` — arming, one tick per expiry, re-arming, stopping, stopping
  twice, stopping from inside a tick, and that a tick which raises leaves nothing
  scheduled.
- `test_window_owner.py` — the window that is asked for (title, size it was told,
  black, non-resizable, placement); the tick reaching the collaborator; the key
  reaching the collaborator unchanged and un-echoed; the shutdown order, its
  idempotency, and reaping on three separate failure paths.
- `test_tk_toolkit.py` — that the adapter answers every part of the seam, that its key
  translation preserves name and character, and that a freshly constructed adapter has
  no window behind it.

## Requirements this item is responsible for

| Req | How |
| --- | --- |
| WIN-1 | The process creates its own native window. |
| WIN-2 | Black ground, non-resizable, at the pixel size WI-2's metrics give. The 40 × 30 part is WI-2's; the window part is here. |
| WIN-3 | The title is set directly on our own window — **assumption A1, and still unlooked-at by a human.** See below. |
| WIN-5 | The window owner closes its own window, once, by whatever route the session ended. The *timing* question (A3) lands in WI-15, not here. |
| GHOST-1 | The repeating timer at 143 ms. |

## What still needs a human

**WIN-3 / assumption A1 — has anybody looked at the titlebar?** No. Under candidate 2
the process sets the title on its own window, so it should be exact, and the probe
measures that Tk reports the title back unchanged — but *reading a string back from
the toolkit that set it* is not the same as a person seeing the titlebar. The plan asks
for the human look at WI-4 and again at WI-21. This branch does not close A1.

## Notes for whoever reads this next

- `DEFAULT_WINDOW_POSITION` is the fixed screen offset the plan asks for "for now".
  WI-14 replaces it with a real anchor and keeps it as the fallback. The constructor
  already takes a `position`, so WI-14 is an argument, not a change here.
- The window's own close button is wired to end the session. Without it the window
  would go and the process would stay, which is the orphan WIN-5 exists to prevent.
  This is slightly ahead of WI-17 and is flagged as an additive deviation.
