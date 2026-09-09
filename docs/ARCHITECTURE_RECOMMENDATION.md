# Architecture Recommendation — Terminal Game

Summary of the architect's proposal for `FUNCTIONAL_REQUIREMENTS.md`.
The full design document, with diagrams and the complete traceability table,
is in [ARCHITECTURE.md](ARCHITECTURE.md).

## What is proposed

**Python 3.9+, stdlib only** (`curses`, `random`, `unittest`) plus `osascript`.
Verified that `/usr/bin/python3` on this machine is 3.9.6 with working curses, so
there is zero install. Go/tcell and Rust/crossterm were rejected — they add a
toolchain without removing the AppleScript dependency.

**Layered functional core / imperative shell**, driven by a single-threaded
fixed-timestep game loop, with a separate launcher process owning the OS window.
Three off-the-shelf patterns: Game Loop, Functional Core/Imperative Shell, Humble
Object. No ECS, no event bus, no threads — one player, one ghost, one maze, one
outcome (GAME-3).

## Three things verified rather than assumed

1. **WIN-1..WIN-5 are achievable without mutating the player's Terminal profile.**
   `Terminal.sdef` was parsed: `number of rows`, `number of columns`,
   `background color`, `font size` and `custom title` are properties of the **tab**
   object; `position` and `close` are properties of the **window** object — all
   per-window. This drove the two-process design: the launcher reads the frontmost
   window position *before* `do script` (which steals focus), spawns and configures
   the window, then waits on a done-file and closes it (WIN-5), which avoids
   Terminal's "process still running" sheet.

2. **The maze algorithm** — randomised-DFS spanning tree on the odd lattice, then a
   braid pass. 19 and 29 are both odd, so lattice cells sit at odd coordinates
   (9×14 = 126 cells) and rows/cols 0 and 18/28 are never touched, making MAZE-3
   hold *by construction*. Braiding only adds edges (so MAZE-6 cannot be lost) and
   degrees only increase (so it terminates). Prototyped over **500 seeds with zero
   failures** on solid border, no dead ends (MAZE-5), and full BFS connectivity.

3. **The spec's own numbers corroborate the model.** The generator produces 0–8 lone
   wall squares per maze, mean **2.71** — the sample picture shows exactly two `■`.
   Every row of the sample picture measures exactly **37 columns** = 2×19−1,
   confirming the two-columns-per-cell render with `═` interstitials and a 3-column
   right margin (MAZE-1).

## Key structural decisions

- **The `ui`↔`core` seam is one type: `ScreenBuffer`**, a 30×40 array of
  `(char, Style)`. `core/view.render(state)` is *pure*, so SCRN-1..6, STAT-1..3 and
  END-4 are all assertable as plain strings with no terminal.
- **The loop reconciles CTRL-1..5 with GHOST-1** by computing ms-until-next-tick and
  using it as the `getch()` timeout — keys are serviced the instant they arrive, and
  `next_tick += PERIOD` (never `now + PERIOD`) prevents drift. After the game ends it
  blocks indefinitely (END-5) until `q` (END-6). A `dirty` flag means an idle game
  burns no CPU.
- **END-1/2/3 are enforced by statement order** in `rules.move_player` — collision
  checked before dot-eating. This is the requirement most likely to be destroyed by a
  well-meaning refactor.
- **GHOST-4 is enforced by the function signature**:
  `choose_direction(grid, pos, facing, rng)` never receives the player's position.
- **No `erase()`/`clear()` per frame** — all 1200 cells are written and committed with
  a single `doupdate()`; curses' damage tracking gives SCRN-7 for free.

## Risks worth attention before coding starts

- **SCRN-3 is the sharpest.** Every double-line box character is East-Asian
  **Ambiguous** width. Terminal's *"Treat ambiguous-width characters as double-width"*
  preference would tear the whole layout, and it is **not settable via AppleScript** —
  the launcher cannot defend against it. Spike on day one.
- **WIN-4 needs Accessibility (TCC) permission** to read another app's frontmost
  window. A three-step fallback chain plus screen-frame clamping is specified so
  "always lands somewhere visible" survives a denial.
- **STAT-2/STAT-3 spacing is not internally consistent** in the spec — `q` lands at
  column 19 in the CAUGHT example and column 20 in the CLEARED one. All three were
  treated as literal templates (reproducing the spec byte-for-byte), but if column
  alignment was the intent, that is a one-line decision now and fiddly later.
- **END-3 is under-specified on scoring:** the assumption taken is that the fatal last
  dot is *not* eaten or scored.
- **The sample's `CLEARED  score 274` exceeds what a 19×29 braided maze yields**
  (258–270 dots measured). Treated as illustrative, since no requirement states a dot
  count.
