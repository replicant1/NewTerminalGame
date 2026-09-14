# M0 — DEV-B — completion

**Iteration:** M0, "Walking skeleton: a window, a screen, and a pure maze"
**Lane:** DEV-B
**Mode:** local — no remote, no `gh`, no pull requests. The technical lead merged.
**Written:** 04:59Z after WI-2; **revised 05:16Z after WI-4 was merged**, because the earlier version
said WI-4 had never been dispatched and that is no longer true.

---

## The short version

**Both of this lane's M0 work items are delivered and on `main`.**

| Item | Planned | What happened |
| --- | --- | --- |
| **WI-2** — the screen port and its terminal adapter, plus a game process that draws one frame and quits | 2 d | **Delivered and merged.** Merge commit `021db44`. |
| **WI-4** — the maze model and its generator | 2 d | **Delivered and merged.** Merge commit `dae4a24`. |

The earlier version of this document was written while the run was paused between the two, and said
of WI-4: *"Not dispatched. The user paused the run before it was handed out."* **That was true when
written and is false now.** The run resumed, WI-4 was dispatched to this lane, and it landed. The
pause cost the lane nothing that had to be redone — nothing had been half-built, so there was nothing
to reconcile.

`main` is green at **256 passed, 0 failed, 0 skipped**, which is 107 from WI-1 plus 84 from WI-2 plus
65 from WI-4, reconciling exactly. Three lanes' worth of work, no test lost, none double-counted.

---

## WI-2 — what landed

**Branch:** `wi-2-screen-port`, cut from `main` at `d4c1a7f`, merged `--no-ff` as `021db44`.
**PR summary:** `docs/prs/PR-WI-2-screen-port.md`
**Progress log:** `docs/progress/wi-2-screen-port.md`
**Finding:** `docs/findings/WI-2-pty-terminal-restore.md`

A character-cell port — put a cell, present a whole frame in one pass, read a key with a timeout —
with a curses adapter behind it in raw, non-echoing mode with the cursor hidden, and a game process
that drives the port end to end.

| File | What it is |
| --- | --- |
| `terminalgame/screen/port.py` | The port. `Frame`, `Cell`, `Colour`, `Key`, the `Screen` interface, `ScreenTooSmall`. Imports no curses, no subprocess, no sys. |
| `terminalgame/screen/curses_adapter.py` | `CursesScreen` and `TerminalSession`. The only module in the system that imports `curses`. |
| `terminalgame/game_main.py` | The walking-skeleton game process. `python3 -m terminalgame.game_main` — the command WI-3's launcher opens a window on. |
| `tests/fake_terminal.py` | A terminal that lives in memory: real state, and a virtual clock. |
| `tests/test_screen_port.py`, `test_curses_adapter.py`, `test_game_main.py`, `test_real_terminal.py`, `test_layering.py` | The suite. |

## WI-4 — what landed

**Branch:** `wi-4-maze-generator`, cut from `main` at `5269b67`, merged as `dae4a24`.
**PR summary:** `docs/prs/PR-WI-4-maze-generator.md`
**Progress log:** `docs/progress/wi-4-maze-generator.md`
**Finding:** `docs/findings/WI-4-maze-invariants-over-seeds.md`

A 19-across by 29-deep grid of corridor and wall, laid out at random every game, with no dead ends
and no unreachable square — MAZE-1 to MAZE-6. Pure: no `curses`, no `subprocess`, no `os`, no `sys`,
no `time`, and no screen geometry anywhere in it.

| File | What it is |
| --- | --- |
| `terminalgame/domain/__init__.py` | The Domain package, and the purity rule stated where a reader meets it. |
| `terminalgame/domain/maze.py` | `Maze` (immutable, hashable), `Direction`, `WIDTH`/`HEIGHT`, `WALL`/`CORRIDOR`, `solid`. Four-sided neighbour queries and a walk along corridors. |
| `terminalgame/domain/maze_generator.py` | `generate_maze`, `generate_maze_with`, `MazeTooSmall`. A spanning-tree carve then a braid, both on the odd lattice. |
| `tests/test_maze.py`, `tests/test_maze_generator.py` | 29 and 30 tests. |
| `tests/test_layering.py` | **Extended**, not created — `DomainPurityTest`, 6 tests. |

**The one idea in it.** Number squares from `(0, 0)`; call a square a *cell* when both coordinates are
odd and a *connector* when exactly one is. Neither pass ever opens a square with both coordinates
even. Every 2 x 2 block of squares contains exactly one both-even square, so every 2 x 2 block
contains a wall — **MAZE-2 holds by construction, at any size, under any random source.** That is
caution C8 seen properly, and the technical lead checked it independently rather than taking it on
report before writing it into the plan as **§11.7**, where it is now marked *not relaxable*.

## Suite state

| Where | Command | Result |
| --- | --- | --- |
| `wi-2-screen-port` at `ebbd510`, before its merge | `python3 -m unittest discover` | **84 passed, 0 failed, 0 skipped** |
| `main` after `021db44` | `python3 -m unittest discover` | **84 passed, 0 failed, 0 skipped** — technical lead, then conductor |
| `wi-4-maze-generator` at `ad81ae4`, before its merge | `python3 -m unittest discover` | **256 passed, 0 failed, 0 skipped** |
| `main` at `7b4b5a0`, after `dae4a24` | `python3 -m unittest discover` | **256 passed, 0 failed, 0 skipped** — technical lead, conductor, and again by me at 05:16Z for this document |

A longer sweep exists and is deliberately **not** in the default run:
`MAZE_SWEEP_SEEDS=20000 python3 -m unittest tests.test_maze_generator` — 30 passed, 0 failed, 58.8 s,
over 20 000 mazes with 0 border breaches, 0 squares off the lattice, 0 open 2 x 2 blocks, 0 dead ends,
0 unreachable squares and 20 000 distinct layouts. The default sweeps 400 seeds and costs about a
second.

**Nothing skipped, and that matters twice over.** The real-curses pseudo-terminal tests are guarded by
`skipUnless(PTYS_AVAILABLE)`, so a zero skip count is the evidence they genuinely ran against real
ncurses rather than quietly excusing themselves.

Plan §2 asked the two developers to confirm the whole-suite command before the first merge. Confirmed
and unchanged across both items: **`python3 -m unittest discover` from the repository root**, no
arguments and no installation. `tests/` is a package, so 3.9 discovery finds it without relying on
namespace-package behaviour.

---

## The rulings, and what they bind

Six deviations were raised across the two items and all six were accepted. Most carry an obligation
for a **later** work item, so they are restated here where the person picking that item up will find
them.

### From WI-2

#### 1. `--hold` is M0 scaffolding and is not a precedent — binds WI-11 and WI-12

`terminalgame/game_main.py` holds its frame for `--hold` seconds (default 3) and then exits by
itself. Accepted for M0, on the explicit constraint that **the real game process exits on `q` and
never on a timer.**

**WI-12 must not inherit a hold.** `game_main.py` is a walking skeleton that exists to prove the port
works end to end and to give WI-3's launcher something to join to; when WI-11's loop and WI-12's
wiring arrive, the timer goes. If anything in the finished game ends a session other than `q`, that
is END-6 broken and A1 flipped by accident.

#### 2. `tests/test_layering.py` is a standing obligation, not a one-off — **WI-4 done, WI-7 outstanding**

The layer-rule test was accepted **and promoted**, with WI-4 and WI-7 to extend it with the
domain-purity cases.

**WI-4 has done its half.** The file now contains, alongside the three original `LayerRuleTest` cases
which are untouched: `THE_DOMAIN`, `FORBIDDEN_IN_DOMAIN = ("curses", "subprocess", "os", "sys",
"time")`, the helpers `domain_files()` and `imported_game_modules()`, and `DomainPurityTest` with six
tests — the Domain is where it is said to be; it imports nothing forbidden; the scan can see the
imports it looks for and does not fire on prose; the dependency scan tells the Domain from the rest;
the Domain depends on nothing above it; the Domain carries no screen vocabulary. `sys` is on the list
because `sys.stdout` is what plan §3 names.

**WI-7 still owes its half** — the ghost's own domain modules fall under the same walk automatically,
so in practice WI-7's obligation is to add nothing and make sure nothing goes red.

**Still unguarded, and not WI-4's to close: nothing walks `launcher/`.** The launcher half of the
layer rule — that the launcher shares no code with the game — has no test. That gap is **WI-12's**,
and it is now recorded in the module's own docstring so it is not rediscovered a third time.

#### 3. `Frame.put` raises on an out-of-range cell — keep raising, and **do not** add clipping — binds WI-5b

I had flagged a worry that a three-column actor glyph centred on column 0 would need clipping. **The
worry was wrong and the case cannot occur.** MAZE-3's border ring means an actor only ever stands on
squares 1 to 17 of 0 to 18, so a glyph centred on column 2s spans columns 1 to 35 of 0 to 36 and can
never run off either edge. The technical lead measured the same thing independently from the
specification's picture.

**WI-5b must not add clipping, and must not add a `put_clipped`.** If WI-5b finds a genuine case, it
goes back to the technical lead rather than being softened locally.

This has since been generalised — see ruling 6 below.

#### 4. Dim yellow for gold, bold magenta for pink — accepted, stays a human check

An eight-colour terminal has no gold and no pink. The substitution lives in one dict, `_palette()` in
`terminalgame/screen/curses_adapter.py`. The tests establish that the five named colours reach the
terminal as five **distinct** attributes; whether dim yellow reads as *gold* and bold magenta as
*pink* to a person (SCRN-4, SCRN-5) is not something any agent can settle. It is on WI-14b's
human-check list and is **not** recorded anywhere as verified.

### From WI-4

#### 5. `generate_maze` keeps its `width` and `height` parameters — and the reason is better than the one I gave

I offered to drop them, having added them only so the tests could use small grids. **The technical
lead ruled the opposite: keep them.** Its reason is the stronger one — exercising the generator at
nine sizes is what turns C8 from a claim about 19 x 29 into a claim about the algorithm. MAZE-1 is
preserved by the default and asserted by the sweep.

It comes with a consequence for later domain items, now **§11.9** of the plan: the nine-size tests
are, without having been framed as one, **the real guard on caution C5**. A screen dimension
hard-coded anywhere in the Domain would fail them outright — worth more than the text scan in
`DomainPurityTest`, which cannot catch a bare `40` typed by hand. **Later domain items should keep
testing at sizes other than 19 x 29 for that reason, not merely for generality.**

To keep the record straight in both directions: **the observation is the technical lead's and the
tests are mine.** I built `OtherGridSizesTest` to show the invariants were the algorithm's rather
than 19 x 29's, and did not see that it was also the answer to the C5 problem I had just flagged as
unsolved two tests away. The lead saw that and I did not. Neither half of that is worth blurring — a
guard nobody knows they have is only half a guard, and it took someone else to finish it.

The text scan itself stays exactly as it is. I flagged it as weak rather than defending it; the ruling
is that flagging was the right response and that extending the word list would not fix it. **No work
is owed against it.**

#### 6. `MazeTooSmall` accepted, and promoted to policy for every later item — **§11.8**

`generate_maze` raises on an even dimension or a lattice under 2 x 2 cells rather than returning a
grid that cannot satisfy MAZE-5. Accepted — and the technical lead noticed that WI-2 had reached the
same conclusion independently in ruling 3 above, in a different lane, without either of us knowing.

**The rule, now binding on every later item: where an argument makes a requirement impossible, refuse
and say which requirement.** A quietly degraded result turns an obvious break into a picture or a maze
that is subtly wrong, which is far more expensive to find.

---

## The measurements worth carrying forward

### From WI-2 — the one termios bit that does not come back

From `docs/findings/WI-2-pty-terminal-restore.md`:

> After a complete curses session on a real terminal, `tcgetattr` before and after differ in
> **exactly one bit**: `0x20000000`, `termios.PENDIN`. `ECHO` and `ICANON` are both back on and every
> other field is identical, on all four exit paths — a normal exit, a `q`, a `SIGTERM`, and the
> refusal of a too-small terminal.

`PENDIN` is transient kernel state ("input pending redisplay"), not a mode the player chose.

**Why this matters more than it looks.** A restore test that compares `c_lflag` unmasked **fails on
correct code**, and the natural reaction to a failing test is to weaken the assertion until it
passes — which throws away the only check that the player's shell comes back at all (caution C10).
The right move is to mask `0x20000000` and leave the rest of the comparison strict.
`PseudoTerminal.modes()` in `tests/test_real_terminal.py` does that and says why in place. **Whoever
writes WI-12's real-run test needs this**, because they will hit it.

The finding also records the two pseudo-terminal traps that cost time: `LINES` and `COLUMNS` must be
removed from the child's environment or ncurses believes them over the real window size, and the
child's stderr must be a pipe or the "too small" message lands in the middle of the captured picture.

### From WI-4 — what the generator actually produces

From `docs/findings/WI-4-maze-invariants-over-seeds.md`, over 2 000 seeds with the two passes run
separately:

| | Minimum | Maximum | Mean |
| --- | --- | --- | --- |
| Dead ends the carve leaves behind | 8 | 22 | 14.5 |
| Connectors the braid then opens | 8 | 21 | 14.3 |
| Corridor squares in the finished maze | 259 | 272 | 265.3 |
| Most ways on from any one square | 3 | 4 | 3.5 |

Corridor occupies 47.0 % to 49.4 % of the 551 squares.

**Why the carve's number is the one to keep.** A grid of solid wall satisfies MAZE-2, MAZE-3, MAZE-5
and MAZE-6 *vacuously* — no square, no dead end, nothing unreachable. "Zero dead ends after the
braid" would therefore read identically whether the braid were doing the work or whether the carve had
happened never to make one. It makes 8 to 22 of them, every time, on every seed tried. **That, plus
asserting the corridor count, is what makes the green mean something.** Anyone tuning the braid later
should keep both assertions rather than the pretty one.

---

## Machine safety

**No window was opened on the user's screen at any point during this lane's work in M0, across either
item.** No `osascript` was run. No macOS permission was requested, and none is recorded as granted or
verified.

- **WI-2's** real-terminal proof is a pseudo-terminal created with `os.openpty()` inside the test
  process. A pseudo-terminal is a real terminal in every way curses cares about — size, termios,
  echo — and it exists entirely inside the process, so none of the window-safety hazards arise: no
  window id to capture, no modal sheet to raise, nothing to reap. The recipe is in the finding for
  WI-12 to reuse rather than rediscover.
- **WI-4** is pure domain and had nothing to open. `DomainPurityTest` now makes that a property of the
  code rather than a claim about the developer's behaviour: the Domain cannot import `subprocess` or
  `os`, so it cannot drive the desktop even by accident.

The five stale root executables — `verify`, `launch-smoke`, `check-window-placement`, `play`,
`Terminal Game` — were **not read, not repaired, not called from a test and not deleted**, on either
item.

---

## What still needs a human

Five things, none recorded as verified. The first four are on WI-14b's list where the plan puts them
and are repeated here because WI-14b has not been written and this document may be read before it is.

1. **The colours as a person sees them (SCRN-3 to SCRN-6).** Run `python3 -m terminalgame.game_main`
   in a Terminal window of at least 40 x 30 on black. Look for: the border in **blue**; the row of
   small squares in **dim gold, not bright yellow**; `▐█▌` in **bright yellow**; `▐▓▌` in **pink, not
   purple**; the bottom line in **cyan**.
2. **Flicker, and the cursor (SCRN-7).** During those three seconds — does the picture appear in one
   go, and is the text cursor invisible anywhere?
3. **Glyph coverage in the launcher's font (WIN-2).** The box-drawing characters survive a
   pseudo-terminal. Whether the font WI-1 sets on its window has them, at the same advance width,
   needs an eye on the real window. That join is WI-3's.
4. **The shell afterwards (caution C10, from the player's side).** When it exits, type at the prompt
   in that same window. It should appear.
5. **Are the mazes any good to play? (new, from WI-4.)** Every property MAZE-1 to MAZE-6 names is a
   *floor* — no dead end, no isolated pocket, one-square corridors. None of them asks whether a layout
   is interesting, and no agent can judge it. To look:

   ```
   python3 -c "from terminalgame.domain.maze_generator import generate_maze; print(generate_maze().as_text())"
   ```

   Run it a few times; `#` is wall, a space is corridor. Look at whether the corridors feel open
   enough to be chased through, whether the braid has left it too loopy or not loopy enough, and
   whether 47–49 % corridor is the density you want. **If it wants tuning, the braid is the knob** —
   opening more than one extra connector per dead end makes it more open, and every invariant survives
   that, because opening a connector on the lattice can only add ways on.

---

## Where this lane stands

- **Delivered and on `main`:** WI-2 and WI-4. **M0 is complete for lane B.**
- **Not started, and all downstream of WI-4 in this lane:** WI-5a, WI-9, WI-5b, WI-13, WI-14a, WI-14b.
  Nothing is half-done and no branch is left dangling.
- **The critical path is now open.** WI-4 was the head of the longest chain in the plan
  (WI-4 → WI-7 → WI-8 → WI-10 → WI-11 → WI-12 → WI-14b, 9 developer-days) and it is merged, so the
  chain is unblocked at its head for the first time this run.
- **What WI-7 inherits**, and the reason the maze's surface is written out in full in
  `docs/prs/PR-WI-4-maze-generator.md`: `maze.open_neighbours(x, y)` is the query the ghost wants;
  coordinates are `(x, y)` with x the column from the left and y the row from the top, **so north is
  `y - 1`**; `Maze` is immutable and hashable; and `generate_maze` carries no state between calls, so
  a seed names a maze however many were made before it.
- **M0 as a whole is not complete until DEV-A's WI-3 lands.** That is the other lane's, and nothing in
  this lane blocks it: WI-3 joins the launcher to `terminalgame.game_main`, which has been on `main`
  since `021db44`.
