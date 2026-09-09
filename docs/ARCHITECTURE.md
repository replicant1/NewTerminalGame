# Terminal Game — Architecture

Architecture proposal for the application specified in
[`FUNCTIONAL_REQUIREMENTS.md`](FUNCTIONAL_REQUIREMENTS.md).
Every design decision below is tagged with the requirement codes it exists to satisfy.

---

## 1. The chosen architecture

> **A layered *functional core / imperative shell*, driven by a single-threaded
> fixed-timestep *game loop*, hosted by a separate *launcher* process that owns the
> operating-system window.**

Three named, off-the-shelf patterns, nothing invented:

| Pattern | Where it is used | Why |
| --- | --- | --- |
| **Game Loop** (Nystrom, *Game Programming Patterns*) | `ui/loop.py` | One thread reconciles a ~7 Hz ghost tick (GHOST-1) with responsive key input (CTRL-1…5) by driving `getch()` with a computed timeout. No threads, no async, no locks. |
| **Functional Core / Imperative Shell** (Bernhardt) | `core/` vs `ui/` + `launcher/` | All rules, maze generation and *rendering* are pure functions over plain data. Everything untestable (curses, AppleScript, the clock) is pushed to a thin outer ring. |
| **Humble Object** (Meszaros, *xUnit Test Patterns*) | `ui/curses_app.py`, `launcher/mac_window.py` | The two modules that cannot be unit-tested are reduced to near-zero logic: one blits a pre-computed character buffer, the other shells out to `osascript`. |

### Why not something else

- **Not an ECS, not a scene graph, not an event bus.** One player, one ghost, one maze,
  no levels, no lives, no pause and no restart (GAME-3). Any of those would be pure ceremony.
- **Not multi-threaded.** A 7 Hz tick over a 551-cell grid is roughly six orders of
  magnitude inside the available budget. A second thread would buy nothing and cost
  a synchronisation model.
- **Not MVC/MVVM.** There is no user-editable model and no two-way binding. A pure
  `render(state) -> ScreenBuffer` function is the whole "view layer".

The single load-bearing rule for every developer who touches this codebase:

> **`core/` may not import `curses`, `os`, `time`, `subprocess`, or the `random` module's
> global functions.** Randomness arrives as an injected `random.Random`; time arrives as an
> injected clock. If a change wants to break that rule, the change is in the wrong package.

---

## 2. Language and runtime

**Python 3.9+, standard library only (`curses`, `random`, `unittest`), plus `osascript`
for the window.** No third-party packages, no build step, no virtualenv.

| Requirement | How the choice satisfies it |
| --- | --- |
| SCRN-7 (no flicker, no cursor) | `curses` is a double-buffered, damage-tracking screen library. Building the frame with `addstr` and committing it with a single `doupdate()` is atomic to the terminal — the defining reason curses exists. `curs_set(0)` hides the cursor. |
| CTRL-1…5 (non-blocking arrow keys, no echo) | `keypad(True)` decodes arrow escape sequences into `KEY_UP`/`KEY_DOWN`/…; `noecho()` + `cbreak()` guarantee nothing typed reaches the maze (CTRL-5); `timeout(ms)` gives the poll-with-deadline primitive the loop needs. |
| SCRN-3…6 (blue/gold/yellow/pink/cyan) | `start_color()` + 256-colour pairs. `TERM=xterm-256color` is Terminal.app's default and is forced explicitly at launch. |
| GHOST-1 (~7 Hz) | `time.monotonic()` plus a drift-corrected deadline. Trivial at this scale. |
| WIN-1…5 | Delegated to the launcher (§3) — curses deliberately does *not* attempt this. |

**Use `/usr/bin/python3` (system Python, 3.9.6 on this machine, `curses` present and
verified).** Zero installation for the player. The cost is a 3.9 language target:
no `match`, no PEP-604 `X | None` at runtime — put `from __future__ import annotations`
at the top of every module and the annotations are free.

*Alternative considered and rejected:* Go + `tcell`, or Rust + `crossterm`. Both are fine
terminal libraries, but they add a toolchain and a build step to a ~1000-line game, and
neither removes the need to shell out to AppleScript for WIN-1/WIN-2/WIN-4. No benefit.

---

## 3. The window problem (WIN-1, WIN-2, WIN-4, WIN-5) — a two-process design

This is the one requirement that a curses program genuinely cannot meet on its own:
curses draws *inside* a terminal, it does not *create* one. So the application runs as
**two processes**.

```
   player types ./play
          │
          ▼
┌───────────────────────┐   1. read frontmost window position      ┌──────────────┐
│   LAUNCHER PROCESS    │─────────── osascript ───────────────────▶│  System      │
│  launcher/mac_window  │   2. `do script` -> new Terminal window  │  Events /    │
│                       │   3. set tab rows/cols/colours/title     │  Terminal.app│
│  (stays alive,        │   4. set window position                 └──────┬───────┘
│   waits on done-file) │                                                 │ spawns
│                       │                                                 ▼
│                       │                                   ┌───────────────────────┐
│                       │                                   │  GAME PROCESS         │
│                       │                                   │  40x30 curses window  │
│  5. done-file appears │◀────────── writes done-file ───────│                       │
│  6. close window id N │─────────── osascript ─────────────▶│  (WIN-5)              │
└───────────────────────┘                                   └───────────────────────┘
```

The macOS `Terminal.sdef` scripting dictionary was inspected to confirm this is achievable
**without mutating the player's saved Terminal profile** — the relevant properties belong to
the `tab` and `window` objects, not only to the shared `settings set`:

- `tab`: `number of rows`, `number of columns` (WIN-2: 40 × 30), `background color`
  (WIN-2: black), `font name`, `font size` (WIN-2: legible), `custom title` +
  `title displays custom title` (WIN-3: *Terminal Game*).
- `window`: `position` (WIN-4), `close` (WIN-5).

**WIN-4 — "a little below and to the right of whatever window the player was last looking at."**
The position must be sampled *before* `do script`, because that call steals focus. Use a
fallback chain, because the first step needs macOS Accessibility permission that may not be granted:

1. `System Events` → `position of front window of (first application process whose frontmost is true)`.
2. Failing that, `position of front window` of Terminal itself (the launcher was almost
   certainly started from a Terminal window — a good proxy for "last looking at").
3. Failing that, a fixed offset from the main screen's origin.

Then offset by `(+40, +40)` points and **clamp to the visible screen frame**, so it
"always lands somewhere visible" (WIN-4).

**WIN-5 — the window closes itself when the game ends.** The launcher owns the window's
lifecycle. The command handed to `do script` is:

```sh
TERM=xterm-256color LANG=en_US.UTF-8 /usr/bin/python3 -m terminal_game --child; \
echo $? > "$DONE_FILE"; exit
```

The wrapper writes the done-file **even if the game crashes**, so the window is always
reaped; the launcher polls for it at 100 ms, closes `window id N`, and surfaces any traceback
in the player's original terminal. Closing *after* the child has exited avoids Terminal's
"a process is still running" confirmation sheet. The trailing `exit` is a belt-and-braces
second path if the launcher itself is killed.

---

## 4. Module decomposition

```
NewTerminalGame/
├── play                          # 2-line launcher script: exec python3 -m terminal_game
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_RECOMMENDATION.md
│   └── FUNCTIONAL_REQUIREMENTS.md
├── src/terminal_game/
│   ├── __main__.py               # role switch: no --child => launcher, --child => game
│   │
│   ├── core/                     ##### FUNCTIONAL CORE — pure, no I/O, no curses #####
│   │   ├── grid.py               # Pos, Direction, Grid (immutable 19x29 cell map)
│   │   ├── maze.py               # generate(rng) -> Grid; start placement   MAZE-*, START-1/2
│   │   ├── ghost.py              # choose_direction(grid, pos, facing, rng) GHOST-2/3/4
│   │   ├── state.py              # GameState, Phase                        START-3/4, SCORE-5
│   │   ├── rules.py              # move_player(), tick_ghost()             CTRL-3, SCORE-*, END-1..5
│   │   ├── glyphs.py             # wall bitmask -> box character, Style    SCRN-3/4/5/6
│   │   ├── view.py               # ScreenBuffer; render(state) -> buffer   SCRN-1/2, STAT-1/2/3, END-4
│   │   └── input.py              # key code -> Command                     CTRL-1/4/5
│   │
│   ├── ui/                       ##### IMPERATIVE SHELL — terminal I/O #####
│   │   ├── loop.py               # the game loop + Clock/KeySource seams   GHOST-1, CTRL-2, END-5/6
│   │   └── curses_app.py         # curses init/teardown, colour pairs, blit  SCRN-7
│   │
│   └── launcher/                 ##### IMPERATIVE SHELL — the OS window #####
│       └── mac_window.py         # osascript: spawn, size, colour, title, place, close  WIN-1..5
│
└── tests/                        # stdlib unittest; no live terminal required
    ├── test_maze.py  test_ghost.py  test_rules.py
    ├── test_glyphs.py  test_view.py  test_input.py  test_loop.py
    └── fakes.py                  # FakeClock, ScriptedKeys, StubRandom, grid-from-string
```

### Responsibilities and boundaries

| Module | Owns | Must not |
| --- | --- | --- |
| `core/grid.py` | Cell storage and neighbour queries. | Know anything about drawing or rules. |
| `core/maze.py` | Producing a legal maze and the two start squares from an injected RNG. | Touch `random` globals; know about dots or score. |
| `core/ghost.py` | *Only* the direction decision. Stateless, one function. | Move anything; know about the player (GHOST-4). |
| `core/state.py` | The mutable game state record. | Contain logic beyond trivial accessors. |
| `core/rules.py` | Every state transition, and **the ordering of end conditions**. | Know about characters, colours or keys. |
| `core/glyphs.py` | Character and colour vocabulary. | Know about game state. |
| `core/view.py` | `GameState -> 40×30 ScreenBuffer`. Pure. | Import curses or call the terminal. |
| `ui/loop.py` | Timing, dispatch, the redraw decision. | Contain any game rule. |
| `ui/curses_app.py` | curses lifecycle; blitting a buffer. | Contain any game rule or layout decision. |
| `launcher/mac_window.py` | AppleScript. | Know the game exists beyond a command line. |

The `ui`↔`core` boundary is one type: **`ScreenBuffer`**, a 30×40 array of
`(character, Style)`. `core` decides *what* every cell says; `ui` knows only how a `Style`
maps to a curses attribute. That single seam is what makes SCRN-* testable with no terminal.

---

## 5. Core data structures

### 5.1 Grid (MAZE-1, MAZE-2)

```python
Pos = tuple[int, int]                 # (x, y), x in 0..18, y in 0..28
WIDTH, HEIGHT = 19, 29

class Grid:                            # frozen after generation
    cells: bytes                       # flat, len 551, 0 = wall, 1 = corridor; index y*19 + x
    wall_glyphs: tuple[str, ...]       # 29 pre-rendered rows of 37 chars (see 5.2)
```

A flat `bytes` keeps it immutable, hashable and trivially cheap. 551 cells; nothing here
needs optimising.

### 5.2 Wall-glyph resolution (SCRN-3)

For every wall cell, build a 4-bit mask from its **grid** neighbours that are also walls
(`N=1, S=2, E=4, W=8`) and look up the double-line character. Corridor-only single-neighbour
cases collapse onto the line's orientation:

| Mask | Glyph | | Mask | Glyph | | Mask | Glyph | | Mask | Glyph |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `----` | `■` | | `N---` | `║` | | `-S--` | `║` | | `NS--` | `║` |
| `--E-` | `═` | | `---W` | `═` | | `--EW` | `═` | | `N-E-` | `╚` |
| `N--W` | `╝` | | `-SE-` | `╔` | | `-S-W` | `╗` | | `NSE-` | `╠` |
| `NS-W` | `╣` | | `-SEW` | `╦` | | `N-EW` | `╩` | | `NSEW` | `╬` |

The mask-0 case is the "lone blue block" of SCRN-3; `╬` is the "crossing". These arise
naturally — a 300-seed run of the §6 generator produced 0–8 lone blocks per maze, mean **2.71**,
against the **two** visible in the specification's own sample picture.

**Screen geometry.** Each grid cell occupies screen column `2x`; the odd column `2x+1` between
two cells is an *interstitial* filled with `═` when **both** flanking cells are walls, and blank
otherwise. Total width `2·19 − 1 = 37`, which is exactly the width of every row of the sample
picture, leaving `40 − 37 = 3` blank columns as MAZE-1's "narrow blank margin".

`wall_glyphs` is computed **once**, at maze construction. Walls never change, so per-frame
rendering is a copy plus a handful of overlays.

### 5.3 Game state (START-3/4, SCORE-*, END-*)

```python
class Phase(Enum): PLAYING; CAUGHT; CLEARED

@dataclass
class GameState:
    grid:    Grid
    dots:    set[Pos]        # every corridor square except the player's start (START-3)
    player:  Pos
    ghost:   Pos
    facing:  Direction       # the ghost's current heading (GHOST-2)
    score:   int = 0         # monotonic (SCORE-5)
    phase:   Phase = Phase.PLAYING
    rng:     random.Random   # injected (GHOST-3)
```

`dots` as a `set[Pos]` gives O(1) eat (SCORE-1) and makes END-2 the expression `not dots`.
`score` is stored rather than derived, so SCORE-2 and SCORE-5 are one line each.

State is **mutated in place** by `rules.py`; the *view* is the pure function. Immutable state
plus copy-on-write was considered and rejected: it buys nothing when there is exactly one
mutator, and it would copy a 260-element set 7 times a second for no reason.

---

## 6. Maze generation (MAZE-2 … MAZE-6)

**Randomised-DFS spanning tree on an odd lattice, followed by a braid pass.**
Both halves are textbook; the combination is the standard recipe for a "no dead ends" maze.

**Parity.** 19 and 29 are both odd, which is exactly what the lattice construction needs.
Lattice cells sit at odd coordinates: `x ∈ {1,3,…,17}` (9 columns) and `y ∈ {1,3,…,27}`
(14 rows) — **9 × 14 = 126 cells**. Row 0/28 and column 0/18 are therefore never touched,
which gives MAZE-3 (a solid outer wall, no tunnels) *by construction* rather than by a later fix-up.

**Phase 1 — carve a perfect maze.** Iterative randomised depth-first search over the 126
lattice cells, stepping two squares at a time and knocking out the wall square in between.
Yields a spanning tree: fully connected (MAZE-6) and one-square-wide, axis-aligned corridors
(MAZE-2). But a spanning tree is *all* dead ends, so:

**Phase 2 — braid away the dead ends (MAZE-5).** Repeatedly: collect every corridor square
with exactly one open neighbour, shuffle, and for each still-degree-1 square knock out one
more wall to an in-bounds lattice neighbour — **preferring a neighbour that is itself a dead
end**, which retires two dead ends per carve and keeps the maze from becoming too open.

Three properties make this safe and make the whole requirement group provable:

1. Braiding only ever *adds* edges, so **connectivity (MAZE-6) cannot be lost**.
2. Degrees only increase, so the count of dead ends strictly decreases — the loop
   **terminates** (measured: ≤ 2 passes).
3. Candidate neighbours are restricted to `0 < x < 18, 0 < y < 28`, so **the border is never
   breached (MAZE-3)**.

Note that a "between" square (odd/even coordinate) always has exactly the two lattice cells it
joins as neighbours, so it is *never* a dead end — only lattice cells need braiding.

**MAZE-4** is satisfied by seeding the injected `random.Random` from the system entropy pool
at startup; passing an explicit seed makes any maze reproducible for debugging and testing.

**This was prototyped and measured before being recommended.** Over 500 seeds: **zero
failures** on solid border, zero dead ends, and full connectivity. Corridor squares ranged
**259–271** (mean 265) → **258–270 dots**. See §12.5 on the sample picture's `score 274`.

### Start placement (START-1, START-2)

- **Player:** the corridor square minimising squared Euclidean distance to the grid centre
  `(9.0, 14.0)`, tie-broken by lowest `y` then lowest `x` so it is deterministic.
- **Ghost:** the corridor square *maximising* squared Euclidean distance from the player —
  "measured across the grid rather than along the corridors" (START-2), i.e. a straight-line
  metric, explicitly **not** a BFS/corridor distance. Same deterministic tie-break.
- **Dots:** every corridor square except the player's (START-3). **Score 0** (START-4).
- The loop starts ticking immediately; nothing is waited on (START-5).

---

## 7. The main loop and concurrency model

**One thread. No async. No timers.** The reconciliation of "input must feel instant"
(CTRL-1, CTRL-2) with "the ghost moves ~7 times a second regardless" (GHOST-1) is done by
computing, on each pass, how long until the next ghost tick and using *that* as the
`getch()` timeout.

```python
PERIOD = 1.0 / 7.0                                    # GHOST-1

def run(state, screen, keys, clock):
    next_tick = clock.now() + PERIOD
    dirty = True
    while True:
        if dirty:
            screen.blit(view.render(state))            # SCRN-7: one atomic doupdate
            dirty = False

        if state.phase is Phase.PLAYING:
            wait_ms = max(0, int((next_tick - clock.now()) * 1000))
        else:
            wait_ms = None                             # END-5: block; nothing else can happen

        key = keys.read(wait_ms)                       # None on timeout
        if key is not None:
            command = input.to_command(key)            # CTRL-5: unmapped keys -> None
            if command is Command.QUIT:
                return                                 # CTRL-4 / END-6, at any point
            if command is not None:
                dirty |= rules.move_player(state, command.direction)

        if state.phase is Phase.PLAYING and clock.now() >= next_tick:
            dirty |= rules.tick_ghost(state)
            next_tick += PERIOD                        # fixed rate, no drift
            if next_tick < clock.now():                # catch-up guard after a stall
                next_tick = clock.now() + PERIOD
```

Points worth understanding before changing this:

- **A keypress is serviced the moment it arrives**, not at the next tick. The ghost's cadence
  never gates the player's responsiveness.
- **`next_tick += PERIOD`, never `now + PERIOD`.** Accumulating the deadline prevents the
  ghost from slowly drifting slower than 7 Hz.
- **One move per press (CTRL-2)** falls out for free: there is no held-key state and no
  autorepeat handling, so the player cannot drift.
- **The `dirty` flag** means an idle game does nothing at all — no repaint, no CPU.
- **After the game ends (END-5)** the loop blocks indefinitely on input, and `rules.py`
  rejects everything except `q`. The final picture simply stays (END-5) until `q` (END-6),
  which returns, ends the process, and lets the launcher close the window (WIN-5).

### End-condition ordering (END-1 … END-5)

All of it lives in `rules.py`, in these two functions, and **the statement order is the
specification**:

```python
def move_player(state, direction) -> bool:            # returns "needs redraw"
    if state.phase is not Phase.PLAYING: return False          # END-5
    target = state.player + direction
    if state.grid.is_wall(target):     return False            # CTRL-3: nothing at all
    state.player = target
    if target == state.ghost:                                  # END-1 (player walks into ghost)
        state.phase = Phase.CAUGHT; return True                # END-3: checked BEFORE the dot
    if target in state.dots:
        state.dots.remove(target); state.score += 1            # SCORE-1, SCORE-2
        if not state.dots:
            state.phase = Phase.CLEARED                        # END-2
    return True                                                # SCORE-3: no dot, no points

def tick_ghost(state) -> bool:
    if state.phase is not Phase.PLAYING: return False           # END-5: the ghost stands still
    state.facing = ghost.choose_direction(state.grid, state.ghost, state.facing, state.rng)
    state.ghost += state.facing                                 # SCORE-4: dots untouched
    if state.ghost == state.player:                             # END-1 (ghost walks into player)
        state.phase = Phase.CAUGHT; return True
    return True
```

END-4 ("on a loss the ghost is drawn over the player") is not handled here at all — it is
purely a *painter's-algorithm* ordering in `view.render`: walls, then dots, then player,
then ghost last.

### Ghost movement (GHOST-2, GHOST-3, GHOST-4)

```python
def choose_direction(grid, pos, facing, rng):
    if grid.is_corridor(pos + facing):
        return facing                                  # GHOST-2: straight has absolute priority
    options = [d for d in DIRECTIONS
               if d is not facing.opposite and grid.is_corridor(pos + d)]
    if options:
        return rng.choice(options)                     # GHOST-3: random among the others
    return facing.opposite                             # GHOST-3: turn back only as a last resort
```

The function does not receive the player's position — GHOST-4 is enforced by the *signature*,
not by discipline. Note that MAZE-5 guarantees degree ≥ 2, so the final `return` is
unreachable in a generated maze; it is kept because GHOST-3 demands the behaviour, and it is
tested against a hand-built dead-ended grid.

---

## 8. Rendering (SCRN-1 … SCRN-7, STAT-1 … STAT-3)

### The pure half

`view.render(state) -> ScreenBuffer`, where `ScreenBuffer` is 30 rows × 40 columns of
`(char, Style)` and `Style ∈ {WALL, DOT, PLAYER, GHOST, STATUS, BLANK}`. In order:

1. **Rows 0–28, columns 0–36:** copy `grid.wall_glyphs` (SCRN-1, SCRN-3). Columns 37–39 blank (MAZE-1).
2. **Dots:** `▪` in `DOT` style at `(2x, y)` for every `Pos` in `state.dots` (SCRN-4).
3. **Player:** `▐█▌` in `PLAYER` style at columns `2x−1 … 2x+1` (SCRN-5).
4. **Ghost:** `▗█▖` in `GHOST` style, painted **last** so it covers the player on a loss (END-4, SCRN-5).
5. **Row 29:** the status line in `STATUS` style, space-padded to 40 (SCRN-1, STAT-1).

Three-column entity glyphs are taken from the specification's own picture. They are safe:
an entity always stands on a corridor square, so the interstitial columns either side are
blank — a three-wide glyph can never obscure a wall. And because the border is solid
(MAZE-3), no entity ever reaches column 0 or 18, so the glyph never runs off the edge.

**Status-line contract (STAT-1, STAT-2, STAT-3)** — three literal templates, reproducing the
specification's example strings byte-for-byte:

| Phase | Template | Spec example |
| --- | --- | --- |
| `PLAYING` | `" score {score}    arrows, q quits"` | `` score 0    arrows, q quits`` |
| `CAUGHT` | `"CAUGHT  score {score}   q quits"` | `CAUGHT  score 37   q quits` |
| `CLEARED` | `"CLEARED  score {score}  q quits"` | `CLEARED  score 274  q quits` |

Nothing else ever appears on row 29 (STAT-1). See §12.4 — the spacing in the spec is not
column-aligned, and this contract reproduces it exactly as written.

### The impure half

`curses_app.blit(buffer)`:

```
curs_set(0); noecho(); cbreak(); keypad(True)      # SCRN-7, CTRL-5, CTRL-1
for each row: group cells into runs of one Style, addstr(y, x, run, attr[style])
stdscr.noutrefresh(); curses.doupdate()            # SCRN-7: one atomic screen update
```

- **Never call `clear()` or `erase()`.** Every one of the 1200 cells is written each frame,
  so a wipe is pure flicker risk. curses' internal damage tracking then sends only the bytes
  that actually changed (SCRN-7).
- **Colour pairs (256-colour):** wall `12` bright blue (SCRN-3), dot `178` dim gold (SCRN-4),
  player `226` bright yellow, ghost `213` pink (SCRN-5), status `14` cyan (SCRN-6), all on
  black (WIN-2). Fall back to the 8 base colours with `A_BOLD`/`A_DIM` if `curses.COLORS < 256`.
- **Do not write the bottom-right cell** (row 29, column 39). Writing the last cell of the last
  line is the classic curses error; the layout leaves it blank so the situation never arises.
- `leaveok(True)` stops curses from repositioning a cursor that is already hidden.

---

## 9. Sequence diagrams

### 9.1 Starting a game (WIN-1…5, MAZE-4, START-1…5)

```mermaid
sequenceDiagram
    actor Player
    participant L as launcher/mac_window
    participant OS as osascript / Terminal.app
    participant M as __main__ (--child)
    participant G as core/maze
    participant Loop as ui/loop
    participant C as ui/curses_app

    Player->>L: ./play
    L->>OS: position of front window of frontmost process
    OS-->>L: (x, y)                                  %% WIN-4
    L->>OS: do script "python3 -m terminal_game --child; echo $? > done"
    OS-->>L: new tab, window id N
    L->>OS: set rows 30 / columns 40 / background black / font 16
    L->>OS: set custom title "Terminal Game"          %% WIN-2, WIN-3
    L->>OS: set position of window N to (x+40, y+40)  %% WIN-4
    OS->>M: starts the game process in the new window
    M->>G: generate(Random(entropy))                  %% MAZE-2..6
    G-->>M: Grid + wall_glyphs
    M->>G: place player (centre) and ghost (furthest)  %% START-1, START-2
    M->>M: dots = corridors - player square, score = 0 %% START-3, START-4
    M->>C: init curses, curs_set(0), colour pairs
    M->>Loop: run(state, screen, keys, clock)          %% START-5: already moving
    Loop->>C: blit(render(state))                      %% first frame
    L->>L: poll for done-file...
```

### 9.2 A move, a tick, and a loss (CTRL-1, GHOST-1, SCORE-*, END-1…5, WIN-5)

```mermaid
sequenceDiagram
    participant Loop as ui/loop
    participant K as ui/curses_app (getch)
    participant R as core/rules
    participant Gh as core/ghost
    participant V as core/view
    participant L as launcher

    Loop->>K: read(timeout = ms until next tick)
    K-->>Loop: KEY_LEFT
    Loop->>R: move_player(state, LEFT)
    R->>R: wall? -> no-op                        %% CTRL-3
    R->>R: player = target
    R->>R: target == ghost? no
    R->>R: eat dot, score += 1                   %% SCORE-1, SCORE-2
    R-->>Loop: dirty = True
    Loop->>V: render(state)
    V-->>Loop: ScreenBuffer
    Loop->>K: blit + doupdate                    %% SCRN-7

    Note over Loop: deadline reached (1/7 s)     %% GHOST-1
    Loop->>R: tick_ghost(state)
    R->>Gh: choose_direction(grid, pos, facing, rng)
    Gh-->>R: straight if open, else random turn  %% GHOST-2, GHOST-3
    R->>R: ghost = ghost + facing                %% SCORE-4: dots untouched
    R->>R: ghost == player -> phase = CAUGHT      %% END-1
    R-->>Loop: dirty = True
    Loop->>V: render(state)
    V-->>V: paint ghost after player              %% END-4
    V-->>V: status = "CAUGHT  score 37   q quits" %% STAT-3
    Loop->>K: blit + doupdate

    Note over Loop: phase != PLAYING -> no ticks, arrows ignored  %% END-5
    Loop->>K: read(blocking)
    K-->>Loop: 'q'
    Loop-->>L: process exits, done-file written    %% CTRL-4, END-6
    L->>L: close window id N                       %% WIN-5
```

---

## 10. Testability

The architecture exists largely to make this section short. **Everything except ~80 lines of
curses calls and ~60 lines of AppleScript is unit-testable with no terminal, no window, and
no timing.** Run with `python3 -m unittest discover tests` — stdlib only, no pytest needed.

| What | How | Requirements proven |
| --- | --- | --- |
| **Maze invariants** | Property-style test over 200+ seeds. For each: border is entirely wall; every corridor square has ≥ 2 corridor neighbours; a BFS from any corridor reaches all of them; corridors are one wide and axis-aligned; two seeds give different mazes. | MAZE-2, MAZE-3, MAZE-4, MAZE-5, MAZE-6 |
| **Wall glyphs** | Table-driven over all 16 masks, plus a golden test rendering a hand-written grid and comparing to expected text rows. | SCRN-3 |
| **Ghost rules** | Tiny grids written as string literals in the test. Straight corridor → keeps going. T-junction with a stubbed RNG → asserts the choice set excludes the reverse. Hand-built dead end → asserts it reverses. Any tick → asserts `dots` and `score` are unchanged, and that the function never sees the player. | GHOST-2, GHOST-3, GHOST-4, SCORE-4 |
| **End-condition ordering** | States constructed directly, no maze generation. The critical one: *ghost standing on the square holding the last dot; player steps in* → asserts `CAUGHT`, not `CLEARED`. Plus ghost-into-player → `CAUGHT`; arrows and ticks after the end → no state change. | END-1, END-2, **END-3**, END-5 |
| **Rendering** | `render()` is pure, so assert the buffer as 30 plain strings. Includes an END-4 test (ghost and player on one square → the ghost's glyph wins) and a spec-fidelity test that a hand-built state reproduces the sample picture's row shapes. | SCRN-1…6, END-4 |
| **Status line** | Three assertions against the specification's literal example strings. | STAT-1, STAT-2, STAT-3 |
| **Input mapping** | Key code → command table, including "every other key maps to None". | CTRL-1, CTRL-4, CTRL-5 |
| **The loop** | `run()` takes a `Clock` and a `KeySource` as parameters. A `FakeClock` advances on demand and a `ScriptedKeys` returns a canned sequence, so: exactly 7 ghost ticks per simulated second (GHOST-1); a keypress is serviced without waiting for the tick (CTRL-1); one press = one square (CTRL-2); `q` returns immediately at any phase (CTRL-4, END-6); no ticks after the end (END-5). | GHOST-1, CTRL-1/2/4, END-5/6 |

**Deliberately not unit-tested:** `ui/curses_app.py` and `launcher/mac_window.py`. That is the
Humble Object bargain — they are kept trivial *because* they are covered only by a short manual
smoke checklist (window is 40×30, titled *Terminal Game*, black, offset down-and-right from the
previously focused window, cursor invisible, no flicker while the ghost runs, window vanishes
on `q`) covering WIN-1…5 and SCRN-7.

---

## 11. Requirement → module traceability

| Req | Realised in |
| --- | --- |
| GAME-1, GAME-2, GAME-3 | `core/rules.py`, `core/state.py` (no lives/levels/pause anywhere in the design) |
| WIN-1, WIN-2, WIN-3, WIN-4, WIN-5 | `launcher/mac_window.py` (§3) |
| SCRN-1, SCRN-2 | `core/view.py` layout (29 maze rows + status row) |
| SCRN-3 | `core/glyphs.py` bitmask table + `Grid.wall_glyphs` (§5.2) |
| SCRN-4, SCRN-5 | `core/view.py` overlay steps 2–4 |
| SCRN-6 | `Style.STATUS` → cyan pair in `ui/curses_app.py` |
| SCRN-7 | `ui/curses_app.py`: `curs_set(0)`, full repaint, single `doupdate()` |
| MAZE-1 | `core/grid.py` dimensions; 37-column render + 3-column margin |
| MAZE-2, MAZE-6 | Randomised-DFS spanning tree (§6 phase 1) |
| MAZE-3 | Odd-lattice construction never touches row/col 0 or 18/28 |
| MAZE-4 | Injected `random.Random`, seeded from entropy at startup |
| MAZE-5 | Braid pass (§6 phase 2) |
| START-1, START-2 | `core/maze.py` placement functions |
| START-3, START-4 | `core/state.py` construction |
| START-5 | `__main__` enters `loop.run` immediately; first tick is scheduled at t+1/7 |
| CTRL-1, CTRL-5 | `core/input.py` + `keypad(True)`/`noecho()` |
| CTRL-2 | Loop design: one command per key event, no held-key state |
| CTRL-3 | `rules.move_player` wall guard |
| CTRL-4 | `loop.run` returns on `q`/`Q` before any phase check |
| GHOST-1 | `ui/loop.py` drift-corrected 1/7 s deadline |
| GHOST-2, GHOST-3, GHOST-4 | `core/ghost.choose_direction` |
| SCORE-1, SCORE-2, SCORE-3 | `rules.move_player` |
| SCORE-4 | `rules.tick_ghost` does not touch `dots` |
| SCORE-5 | `score` only ever `+= 1`; rendered by `core/view.py` |
| END-1, END-2, END-3, END-5 | Statement order in `core/rules.py` (§7) |
| END-4 | Paint order in `core/view.py` |
| END-6 | `loop.run` quit path + `launcher` close (WIN-5) |
| STAT-1, STAT-2, STAT-3 | `core/view.py` status templates (§8) |

---

## 12. Assumptions

1. **macOS with Terminal.app.** Confirmed present on this machine (`TERM_PROGRAM=Apple_Terminal`,
   no iTerm2 installed). WIN-1/2/4/5 are met with AppleScript against Terminal specifically.
   The spec states no portability requirement, so none is designed in — `core/` and `ui/` are
   portable anyway, and a second launcher could be added later if ever needed.
2. **`/usr/bin/python3` (3.9.6) is the target.** Code must stay 3.9-compatible.
3. **MAZE-1's "narrow blank margin"** is exactly the 3 columns left over after the 37-column
   maze, derived by measuring every row of the specification's sample picture.
4. **Entity glyphs are three columns wide** (`▐█▌`, `▗█▖`), taken from the sample picture,
   spilling into the interstitial columns either side. Justified in §8.
5. **START-2's "across the grid"** is read as straight-line (Euclidean) distance, explicitly
   *not* corridor/BFS distance, per the requirement's own wording.
6. **END-3 loss semantics:** stepping onto the ghost is fatal *before* the dot is eaten, so
   the final score does **not** include that last dot. The requirement fixes the outcome
   (a loss); it does not state whether the dot scores. See §12.3.
7. **GHOST-1's "about seven times a second"** is implemented as exactly 1/7 s = 142.9 ms.
8. **The ghost's initial heading** is a random open direction from its start square (spec is silent).
9. **`q` (CTRL-4) is a clean quit**, not a distinct outcome: the status line keeps whatever it
   said and the window closes (WIN-5).
10. **Font:** Menlo 16 pt — a fixed-width face with full double-line box-drawing coverage.

---

## 13. Cautions and open questions for the implementer

1. **WIN-4 needs macOS Accessibility permission.** Reading the frontmost *other* application's
   window position via System Events triggers a TCC prompt, and will silently fail if denied.
   **Implement the three-step fallback chain in §3 from the start**, and always clamp the final
   position to the visible screen frame — otherwise a window can land off-screen and WIN-4's
   "always lands somewhere visible" is violated. Automation permission for Terminal will also
   prompt on first run.

2. **Ambiguous-width characters could break the whole layout (SCRN-3).** Every double-line box
   character (`═ ║ ╔ ╬` …) and `■` is East-Asian **Ambiguous** width. Terminal.app renders them
   single-width by default, but the preference *Profiles → Advanced → "Treat ambiguous-width
   characters as double-width"* flips that — and it is **not** settable through AppleScript, so
   the launcher cannot defend against it. If a player has it enabled, every maze row will be
   37 cells wide in a 40-column window and the picture will tear. **Spike this on day one**;
   if it proves a real risk, consider detecting it by writing a probe character and reading the
   cursor column back, and showing a clear message rather than a broken maze.

3. **Prove the Unicode path early.** Set `locale.setlocale(locale.LC_ALL, "")` before
   `curses.initscr()` and force `LANG`/`LC_ALL` to a UTF-8 value in the launched command. A
   non-UTF-8 locale turns every box character into a `?`. This is a five-minute spike and it
   de-risks SCRN-2 and SCRN-3 entirely.

4. **The status-line spacing in STAT-2/STAT-3 is not internally consistent.** `CAUGHT  score 37   q quits`
   puts `q` at column 19 while `CLEARED  score 274  q quits` puts it at column 20 — the two are
   not column-aligned, and the in-play line has a leading space the others lack. §8 treats all
   three as literal templates, which reproduces the spec exactly but means the `q quits` column
   shifts as the score gains digits. **If column alignment was the real intent, say so now** —
   it is a one-line change before any code exists, and a fiddly one afterwards.

5. **The sample picture's `CLEARED  score 274` is above what this generator produces.**
   Measured over 500 seeds, a 19×29 braided maze yields 259–271 corridor squares, i.e.
   **258–270 dots**. The sample is treated as illustrative. If 274 was meant as a hard number,
   the braid rate would need tuning — but no requirement states a dot count, so nothing is
   built to hit it.

6. **END-3 is the requirement most likely to be broken by a well-meaning refactor.** It is
   satisfied *only* by the order of two statements in `rules.move_player`. Anyone who "tidies"
   the dot-eating above the collision check silently turns a loss into a win. The test named
   in §10 for exactly this case is the guard — do not delete it, and leave the `# END-3` comment
   in place.

7. **`GHOST-3`'s reverse branch is unreachable in a generated maze** (MAZE-5 guarantees degree
   ≥ 2). Do not delete it as dead code, and do not try to cover it with a generated maze — test
   it against a hand-built dead-ended grid.

8. **Do not add a thread for the ghost.** The timeout-driven loop in §7 is the entire
   concurrency model, and it is sufficient. A thread would introduce a data race on `GameState`
   and buy nothing at 7 Hz.

9. **Keep `core/` free of `curses`, `time`, `os` and `subprocess`.** Enforce it with a one-line
   test that greps the package's imports if you like. Once that boundary is breached, the
   test strategy in §10 collapses and the value of this architecture goes with it.

10. **Window teardown (WIN-5):** closing a Terminal window whose process is still running can
    raise a confirmation sheet. The launcher-waits-then-closes design in §3 avoids it — do not
    "simplify" it into having the game close its own window from inside itself.
