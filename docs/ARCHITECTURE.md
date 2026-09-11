# Terminal Game — Architecture

Source of truth for requirements: `docs/FUNCTIONAL_REQUIREMENTS.md` (49 codes).
This document names the architecture, shows the structure, traces every code to a
home, and lists what was measured, what was assumed, and what needs a human.

---

## 1. Chosen architecture

**Functional core, imperative shell** — the core of the game is a set of pure
functions over immutable values, wrapped in a thin impure shell that owns the
terminal and the window. The shell is split across **two processes**.

Two sentences, because it is genuinely that small:

> A pure core computes *the next game state* and *the next screenful*; a thin
> curses adapter blits that screenful and reads keys; a separate launcher
> process creates, sizes, titles, positions and finally closes the Terminal
> window the game runs in.

Why this and nothing more elaborate:

- The spec is ~90% rules and ~10% platform. Maze generation, ghost policy,
  scoring, end conditions, glyph selection and the whole status line are
  deterministic functions of state. Making them pure means **44 of the 49
  requirements are testable with no terminal attached** (see §8).
- The remaining 5 (WIN-1..5) are *window management*, which on macOS is not a
  terminal concern at all — it is AppleScript against Terminal.app. That is a
  different process with a different lifetime, so it gets its own process.
- No MVC, no ECS, no event bus, no plugin points, no levels/lives abstraction.
  There is one maze, one ghost, one outcome. Anything generic here would be
  scaffolding for a sequel that the spec explicitly forbids (GAME-3).

There are **7 source modules and 2 executables**. Two developers can hold it in
their heads.

### 1.1 Language and runtime — and why

**Python 3.9+, standard library only** (`curses`, `random`, `time`, `unittest`,
`subprocess`). Shebang `#!/usr/bin/env python3`.

Measured on this machine before recommending it:

| Check | Result |
|---|---|
| `/usr/bin/python3` | 3.9.6, ships with macOS — **no install step for the player** |
| `/opt/homebrew/bin/python3` | 3.14.7, also present; both behave identically on every probe below |
| `curses` module | present on both, ncurses 6.0.20150808 |
| Wide-character curses | **yes** — the error text from a deliberate failure reads `addwstr()`, i.e. the ncurses**w** build, so Unicode box-drawing needs no `acs_map` fallback |
| Colours | `COLORS` = 256, `COLOR_PAIRS` = 32767, `use_default_colors()` ok, `can_change_color()` true |
| `pytest` | **absent on both interpreters** — hence `unittest`, which is present |

Python was chosen over C/Go/Rust because the entire performance budget is one
frame every 143 ms and the measured cost of the *naive* full repaint is 0.25 ms
(§7). There is no performance argument for a compiled language here, and there
is a strong argument against adding a toolchain to a 1000-line game.

---

## 2. Block diagram

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  PROCESS A — "play"            (runs in the player's own shell/window)   │
 │                                                                          │
 │   termgame/window.py     ── the only AppleScript in the system ──        │
 │     find_reference_window()   read position of the window the player     │
 │                               was last looking at            [WIN-4]     │
 │     open_game_window()        do script → capture window id  [WIN-1]     │
 │                               set 40 cols × 30 rows, font,   [WIN-2]     │
 │                               black bg, title components off [WIN-3]     │
 │                               set position = ref + (dx,dy)   [WIN-4]     │
 │     wait_until_idle()         poll `busy of tab 1` → false               │
 │     close_by_id()             close ONLY the captured id     [WIN-5]     │
 └───────────────────────────────┬──────────────────────────────────────────┘
                                 │ osascript (Terminal.app scripting)
                                 │ spawns:  exec "<repo>/Terminal Game"
                                 ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  PROCESS B — "Terminal Game"      (runs in the new 40×30 window)         │
 │                                                                          │
 │  ┌────────────────────────────  IMPURE SHELL  ────────────────────────┐  │
 │  │  termgame/loop.py      the one game loop; owns the 143 ms deadline │  │
 │  │                                                        [GHOST-1]   │  │
 │  │  termgame/screen.py    curses adapter:                             │  │
 │  │        paint(frame)      one addstr per cell, one refresh [SCRN-7] │  │
 │  │        read_key(ms)      timeout(ms) + getch          [CTRL-1..5]  │  │
 │  │        curs_set(0), noecho, cbreak, keypad(True)        [SCRN-7]   │  │
 │  └───────────┬──────────────────────────────────┬─────────────────────┘  │
 │              │ Frame (immutable)                │ Key (enum)             │
 │  ┌───────────▼──────────────────────────────────▼─────────────────────┐  │
 │  │                          PURE CORE                                 │  │
 │  │                                                                    │  │
 │  │   maze.py    generate(rng) -> Maze          [MAZE-1..6]            │  │
 │  │              19×29 cell grid derived from a 9×14 node lattice      │  │
 │  │                                                                    │  │
 │  │   model.py   Maze, GameState, Direction, Outcome  (frozen values)  │  │
 │  │                                                                    │  │
 │  │   rules.py   new_game(rng)      [START-1..5]                       │  │
 │  │              move_player(s,dir) [CTRL-1..3, SCORE-1..3, END-1..3]  │  │
 │  │              move_ghost(s,rng)  [GHOST-2..4, END-1]                │  │
 │  │                                                                    │  │
 │  │   view.py    render(state) -> Frame  [SCRN-1..6, STAT-1..3]        │  │
 │  │   theme.py   WALL_GLYPH[16] mask table, entity glyphs, colour ids  │  │
 │  │                                      [SCRN-3..6]                   │  │
 │  └────────────────────────────────────────────────────────────────────┘  │
 └──────────────────────────────────────────────────────────────────────────┘

   Dependency rule: arrows point inward only.
   The pure core imports nothing from `screen`, `loop` or `window`,
   and imports no module that touches a terminal, a clock or a window.
```

---

## 3. Directory structure

```
<repo root>/
  play                      # executable, shebang. PROCESS A entry point.
                            #   argv-free; this is what the player types.
  Terminal Game             # executable, shebang. PROCESS B entry point.
                            #   NAME IS LOAD-BEARING — see §6.3 (WIN-3).
  termgame/
    __init__.py
    model.py                # pure  — frozen value types, no logic
    maze.py                 # pure  — MAZE-1..6
    rules.py                # pure  — START-*, CTRL-*, GHOST-2..4, SCORE-*, END-*
    theme.py                # pure  — SCRN-3..6 glyph + colour tables
    view.py                 # pure  — SCRN-1..7 frame construction, STAT-1..3
    screen.py               # IMPURE — curses adapter (the ONLY curses import)
    loop.py                 # IMPURE — the game loop and the GHOST-1 clock
    window.py               # IMPURE — the ONLY osascript/AppleScript (WIN-1..5)
  tests/
    test_maze.py            # invariants over many seeds
    test_rules.py           # start, movement, ghost policy, scoring
    test_end.py             # END-1..6 including the END-3 precedence case
    test_view.py            # whole frames compared as text
    test_theme.py           # all 16 wall-mask cases
    fixtures/
      spec_maze.txt         # the mock-up from the spec, as a golden fixture
  docs/
    FUNCTIONAL_REQUIREMENTS.md
    ARCHITECTURE.md
```

Run the tests with `python3 -m unittest discover -s tests` from the repo root.
There is no `requirements.txt`, no virtualenv, no packaging. Do not add any.

---

## 4. The two processes and their lifecycle

`play` does not become the game. It is a supervisor that lives exactly as long
as the game window.

1. `play` asks Terminal.app for the **position of the window the player was last
   looking at**. It prefers the window whose `tab 1`'s `tty` equals the
   launcher's own `os.ttyname(0)` — that is precisely the window the player
   typed `./play` into. Falls back to Terminal's `front window`, then to a fixed
   position. *(No Accessibility permission is needed for any of this.)*
2. `play` issues `do script "exec '<repo>/Terminal Game'"`, captures the
   returned **tab**, resolves it to a **window** and records its **`id`**.
   Every subsequent AppleScript statement addresses `first window whose id is
   <that id>` — never `front window`, never a title, never an index.
3. `play` applies the window settings (§6) and returns to waiting.
4. `Terminal Game` runs the loop. The player plays. On `q` the process exits
   (END-6) — and only then.
5. `play` polls `busy of tab 1 of (window id N)` until it is `false`, i.e. the
   game process is gone, **then** closes that window by id (WIN-5).

The order in step 5 is not optional. Closing a window whose tab is still busy
raises a modal confirmation sheet that only a human can dismiss, and a modal
sheet blocks every subsequent AppleScript call in the system.

**Failure paths close the window too.** `play` wraps steps 3–5 in
`try/finally`; the `finally` runs the same wait-then-close-by-id. If the wait
times out, `play` reports the window id and leaves the window open rather than
forcing it.

---

## 5. The pure core

### 5.1 Value types (`model.py`)

```
Direction  = UP | DOWN | LEFT | RIGHT        (dr, dc)
Outcome    = PLAYING | CAUGHT | CLEARED
Maze       = frozen 29×19 grid of WALL/CORRIDOR  (+ derived neighbour lookup)
GameState  = maze, player: (r,c), ghost: (r,c), ghost_dir: Direction,
             dots: frozenset[(r,c)], score: int, outcome: Outcome
```

`GameState` is frozen and every transition returns a **new** state. There is no
mutation anywhere in the core. This is what makes the END-3 precedence case
(§5.4) a three-line test rather than a debugging session.

### 5.2 Maze generation (`maze.py`) — MAZE-1..6

The interesting constraint is MAZE-5: *no dead ends*. A plain maze algorithm
produces a spanning tree, which is nothing but dead ends. The structure that
makes this tractable was **derived by decoding the mock-up in the spec**, which
turns out to be exactly this:

```
19 columns × 29 rows of cells, where
    cell (odd, odd)   is a NODE        → 9 × 14 = 126 nodes
    cell (even, even) is a PILLAR      → always wall
    the cell between two adjacent nodes is a LINK → corridor iff the edge is open
```

Verified against the spec's own picture: every (odd,odd) cell in it is corridor,
every (even,even) cell is wall, and its 126 nodes + 64 horizontal links + 74
vertical links = its 264 corridor squares exactly.

With that model the requirements collapse into graph properties:

| Requirement | Becomes |
|---|---|
| MAZE-1 19×29 | 9×14 node lattice, fixed |
| MAZE-2 one-wide, orthogonal | true by construction — links are single cells |
| MAZE-3 solid border | true by construction — row 0/28 and col 0/18 are never nodes or links |
| MAZE-5 no dead ends | **every node has lattice degree ≥ 2** (a link cell always has exactly 2 corridor neighbours, so nodes are the only risk) |
| MAZE-6 all reachable | the lattice graph is connected |

**Algorithm — braided randomised-DFS:**

1. Randomised depth-first search over the 9×14 lattice → a spanning tree
   (connected, so MAZE-6 holds).
2. **Braid**: for every node of degree 1, add one edge to a uniformly-chosen
   grid-neighbour it is not already joined to. A tree leaf in a grid always has
   at least one spare neighbour (the poorest node, a corner, has 2 grid
   neighbours and uses 1), so this never fails and never needs a second pass.
   Adding edges cannot disconnect anything, so MAZE-6 survives.
3. Paint the lattice onto the 29×19 cell grid.

Measured: **5000 mazes, 0 failures** on border / dead-end / connectivity /
no-2×2-open-block; **max braid passes ever needed: 1**; mean 265.3 corridors
(the spec mock-up has 264); **0.642 ms per maze**.

`generate(rng)` takes a `random.Random` and is otherwise deterministic, so every
maze test is reproducible from a seed.

### 5.3 Starting a game (`rules.new_game`) — START-1..5

- START-1: player = the corridor cell minimising squared distance to the grid
  centre (14, 9); ties broken by lowest `(row, col)`.
- START-2: ghost = the corridor cell maximising **squared Euclidean** distance
  from the player over grid coordinates (see Assumption A2), ties broken the
  same way. Its initial direction is a random open direction.
- START-3: `dots = all corridor cells − {player}`.
- START-4: `score = 0`.
- START-5: there is no title screen and no "press any key". `play` spawns the
  game and the loop's first act is to paint frame 0; the ghost's first deadline
  is 143 ms later.

### 5.4 Transitions (`rules.py`)

Both transitions are total functions `(GameState, …) -> GameState` and both are
no-ops when `state.outcome != PLAYING` — that single guard is all of END-5.

```
move_player(state, direction) -> GameState
    if outcome != PLAYING: return state                  # END-5
    target = player + direction
    if maze[target] is WALL: return state                # CTRL-3 (nothing at all)
    score' = score + (1 if target in dots else 0)        # SCORE-1..3
    dots'  = dots - {target}
    if target == ghost:      outcome' = CAUGHT           # END-1
    elif not dots':          outcome' = CLEARED          # END-2
    else:                    outcome' = PLAYING
```

The `if CAUGHT … elif CLEARED` ordering **is** END-3: eating the last dot on the
ghost's square is a loss, because the collision test is evaluated first.

```
move_ghost(state, rng) -> GameState
    if outcome != PLAYING: return state                  # END-5
    if forward is open: dir' = forward                   # GHOST-2 (straight on)
    else:
        options = open directions except the reverse of dir
        dir' = rng.choice(options) if options else reverse(dir)   # GHOST-3
    ghost' = ghost + dir'
    outcome' = CAUGHT if ghost' == player else PLAYING   # END-1
    dots unchanged, score unchanged                      # SCORE-4, GHOST-4
```

The ghost never reads `state.player` other than for the collision test — GHOST-4
is enforced by inspection, and a test asserts that moving the player around does
not change a seeded ghost's trajectory.

### 5.5 Rendering (`view.py`, `theme.py`) — SCRN-1..6, STAT-1..3

`render(state) -> Frame`, where `Frame` is an immutable 30×40 grid of
`(character, style_id)`. **It contains no curses types and imports no curses.**
Tests read a `Frame` back as 30 plain strings and compare them to expected text.

The screen geometry was **derived from the spec's mock-up, not guessed**: the
mock-up is 37 columns wide over 29 maze rows plus 1 status row.

```
screen column = 2 × maze column        (maze col 0..18  →  screen col 0..36)
screen row    = maze row               (maze row 0..28  →  screen row 0..28)
screen row 29 = status line                                          [SCRN-1]
screen cols 37..39 = the "narrow blank margin"                       [MAZE-1]
```

The odd screen columns `2c+1` are *joiner* columns. Decoded from the mock-up,
exhaustively, with no exceptions:

- **Joiner column** holds `═` if and only if the cells on both sides are wall;
  otherwise it is blank.
- **Wall cell** glyph is a pure function of a 4-bit mask of which of its N/S/E/W
  cell-neighbours are wall — a 16-entry table (SCRN-3):

| N S E W | glyph | | N S E W | glyph |
|---|---|---|---|---|
| 0000 | `■` *(lone wall square)* | | 1000 / 0100 / 1100 | `║` |
| 0010 / 0001 / 0011 | `═` | | 0101 | `╗` |
| 0110 | `╔` | | 1001 | `╝` |
| 1010 | `╚` | | 0111 | `╦` |
| 1011 | `╩` | | 1101 | `╣` |
| 1110 | `╠` | | 1111 | `╬` |

  Fifteen of the sixteen appear in the spec's mock-up and were read off it
  directly; `1111 → ╬` is the only entry inferred, and it is the obvious one.

- **Dot** `▪`, one per corridor cell, at `2c` (SCRN-4).
- **Player** `▐█▌` and **ghost** `▗█▖`, **three characters wide**, centred on
  `2c` and spilling into the joiner columns either side (SCRN-5). This is safe
  and needs no special case: an entity always stands on a *corridor* cell, and a
  joiner beside a corridor cell is blank by the rule above. That invariant is
  worth a test of its own.
- **Draw order**: walls → dots → player → **ghost last**. That one ordering
  gives END-4 (on a loss the ghost is drawn over the player) for free.

Colours (SCRN-3..6) are 256-colour indices in `theme.py`, one curses colour pair
each — verified available. `A_BOLD` for the player's bright yellow, `A_DIM` for
the dots' dim gold.

Status line (SCRN-6, STAT-1..3), rendered in cyan at column 1 of row 29:

```
PLAYING  →  "score {score}    arrows, q quits"
CAUGHT   →  "CAUGHT  score {score}   q quits"
CLEARED  →  "CLEARED  score {score}  q quits"
```

These reproduce the spec's quoted strings verbatim. See Assumption A3 — the two
end-of-game strings do not align with each other and the mock-up adds a leading
blank column the quoted strings do not have.

---

## 6. The impure shell

### 6.1 `screen.py` — the curses adapter

Its whole surface is three functions, and it is the only module in the repo that
may `import curses`:

```
with Screen() as scr:        # curses.wrapper; curs_set(0), noecho, cbreak,
    scr.paint(frame)         #   keypad(True), set_escdelay(25)
    key = scr.read_key(ms)   # timeout(ms) + getch → Key enum or None
```

`paint` walks the `Frame` and issues one `addstr` per cell, then one `refresh()`.
ncurses diffs the virtual screen against the physical one, which is what makes
the redraw flicker-free (SCRN-7). No dirty-rectangle tracking: measured at
0.25 ms per full frame, 0.2% of a tick (§7).

`read_key` maps `KEY_UP/DOWN/LEFT/RIGHT` (259/258/260/261) to `Direction`, `q`
and `Q` to `QUIT`, and **everything else to `None`** (CTRL-5). `noecho()` is what
stops keystrokes appearing in the maze.

### 6.2 `loop.py` — the game loop and the GHOST-1 clock

One thread. No `threading`, no `asyncio`, no signal handlers.

```
GHOST_TICK = 1/7 s
next_tick  = monotonic() + GHOST_TICK
paint(render(state))
while True:
    remaining = next_tick - monotonic()
    key = screen.read_key(max(0, int(remaining * 1000)))   # returns EARLY on a keypress
    if key is QUIT:      return                            # CTRL-4, END-6
    if key is a Direction: state = move_player(state, key) # CTRL-1, CTRL-2
    if monotonic() >= next_tick:
        state = move_ghost(state, rng)                     # GHOST-1
        next_tick += GHOST_TICK
    paint(render(state))
```

`getch` with a timeout returns *as soon as a key arrives*, so player input is
handled at keypress latency while the ghost keeps to its own deadline — GHOST-1's
"whether or not the player is moving" and CTRL-2's "one square per key press"
fall out of the same loop with no second clock.

Measured: **70 ticks in 10.005 s = 6.997 ticks/s**, mean drift 4.15 ms, max
5.08 ms. `next_tick += GHOST_TICK` (rather than `= now + GHOST_TICK`) is what
keeps that from accumulating.

### 6.3 `window.py` — the AppleScript adapter (WIN-1..5)

Every claim below was executed against Terminal.app on this machine, in windows
created and closed by id.

**WIN-1** `do script` creates a new window. The returned value is a **tab**; the
window is `first window whose tabs contains t`, and its `id` is captured
immediately and used for everything after.

**WIN-2** `number of columns` and `number of rows` are read/write properties of
the *tab*. Setting them to 40 and 30 was confirmed from inside the child process:
`stty size` reported `30 40` and `tput colors` reported `256`. Font is
`font name = "Menlo-Regular"`, `font size = 18` on the tab; `background color =
{0,0,0}`. No global preference is touched.

**WIN-3** is the one that needed real work. Terminal composes its window title
from several components, and `custom title` is only one of them. With every
scriptable component turned off the title still read
`rodneybailey — Terminal Game — sleep ◂ osc.sh`: a working-directory prefix and
an *active process name* suffix, **neither of which has an AppleScript toggle**.
The working recipe, measured to produce a window whose `name` is exactly
`Terminal Game`:

1. The game executable is named **literally `Terminal Game`** — a shebang script
   invoked with **no arguments**, via `do script "exec '<repo>/Terminal Game'"`.
   Terminal's active-process component then *is* the required title.
2. The game emits `\033]7;\007` as its first write, which clears the
   working-directory prefix.
3. `title displays custom title` is set **false** (setting it true appends a
   second `Terminal Game`, giving `Terminal Game — Terminal Game`), along with
   `title displays device name / shell path / window size / file name`.

Renaming that file, or invoking it as `python3 "Terminal Game"`, or passing it an
argument, **breaks WIN-3.** Guard it with a human check, not a unit test.

**WIN-4** `position of front window` (read) and `position of <window id N>`
(write) share a coordinate space — an offset write of `(ref.x+30, ref.y+30)`
landed at exactly those coordinates. A 40×30 window in Menlo 18 measures
**477 × 707 px**, so a modest offset keeps it on screen. `play` prefers the
Terminal window whose `tab 1`'s `tty` matches its own `os.ttyname(0)`.

**WIN-5** The window does **not** close itself when the child shell exits on this
machine — the profile is not set to "close on exit", and relying on a per-profile
preference would be fragile in any case. `play` closes it explicitly, after
polling `busy of tab 1` to `false`. That poll went `true, true, true, false` and
the close then succeeded with no modal sheet.

**Safety rules for anyone touching this module — these are not style points.**
The player's own shells, and any agent session, are windows in the same
application:

- Capture the window `id` at creation. Address that id and nothing else.
- Never `close front window`, never close by title, never enumerate-and-guess.
- Never close a tab whose `busy` is `true`.
- Never launch anything in the game window that blocks forever.
- Clean up on the failure path with the same wait-then-close-by-id.

---

## 7. What was measured (and the numbers)

| Claim | Measurement |
|---|---|
| curses sees a 40×30 window | `LINES, COLS = (30, 40)` under a 40×30 pty; `stty size` = `30 40` in a real Terminal window |
| Unicode glyphs render | all of `╔ ═ ║ ▪ █ ▐ ▌ ▗ ▖ ■` written and read back verbatim from a live Terminal tab's `contents` |
| Glyphs are single-width | cursor advanced by exactly 1 column after each — the 2-column cell layout is safe |
| Wide curses build | failure text says `addwstr()`, i.e. ncursesw; no `acs_map` fallback needed |
| 256 colours | `COLORS` = 256, `COLOR_PAIRS` = 32767, `tput colors` = 256 in the real window |
| Cursor hides | `curs_set(0)` returned 1; `\e[?25l` present in the output byte stream |
| Ghost rate | 70 ticks in 10.005 s = **6.997 ticks/s**, mean drift 4.15 ms, max 5.08 ms — identical on Python 3.9.6 and 3.14.7 |
| Repaint cost | naive full repaint (1160 `addstr` + 1 `refresh`) = **0.25 ms/frame**, 0.2% of a 143 ms tick; per-row variant 0.04 ms |
| Maze generator | 5000 mazes, **0 failures**, max 1 braid pass, mean 265.3 corridors, **0.642 ms** each |
| The spec's mock-up is a legal maze | solid border, **0** corridor squares of degree < 2, 264 corridors all mutually reachable |
| Wall glyph rule | a pure 4-bit neighbour mask, 15/16 cases read directly off the mock-up, zero exceptions |
| Window geometry | 40×30 in Menlo 18 = 477 × 707 px; offset write landed exactly |
| WIN-3 recipe | window `name` read back as exactly `Terminal Game` |
| Safe close | `busy` polled to `false`, then close by id — no modal sheet |
| TCC permissions | Automation on Terminal already granted on this machine; **Accessibility is not required by this design** |
| `pytest` | absent on both interpreters → tests use `unittest` |

The probe that failed and why it matters: `addstr(LINES-1, COLS-1, ch)` raises
`addwstr() returned ERR`. `insstr` at the same cell succeeds. See Caution C1.

---

## 8. Testability — which layer is pure

**Pure, tested with no terminal and no window** — `model.py`, `maze.py`,
`rules.py`, `theme.py`, `view.py`. That is **44 of 49 requirements**. Every one
of them takes a seeded `random.Random` where randomness is involved, so every
test is deterministic and reproducible.

The three test shapes that carry the weight:

1. **Maze invariants over many seeds.** For seeds 0..999: solid border, every
   corridor cell has ≥ 2 corridor neighbours, all corridors mutually reachable,
   no 2×2 block of corridor. (The prototype ran 5000 and found nothing; 1000 in
   CI costs well under a second.)
2. **Whole frames compared as text.** `render(state)` returns a `Frame`;
   `frame.rows()` returns 30 strings. Build a state from a hand-written maze and
   assert the 30 strings. `tests/fixtures/spec_maze.txt` holds the picture from
   the spec itself, which pins SCRN-1..6 to the document.
3. **Exhaustive glyph table.** All 16 wall masks, asserted against the table
   decoded from the spec.

**Impure, not unit-tested** — `screen.py`, `loop.py`, `window.py`. Keep them
this thin on purpose: `screen.py` should contain no `if` that decides anything
about the game; `loop.py` should contain no arithmetic other than the deadline.
If a bug can only be reproduced by playing, something has leaked out of the core.

**Handed to a human, because an agent has no controlling tty.** These cannot be
asserted in a test run and must be on a checklist:

| # | Check | Why a human |
|---|---|---|
| H1 | **WIN-4** — the window lands a little below and right of the window `./play` was typed in, and is fully on screen | requires a real session with a real front window; the agent that wrote this has no tty at all |
| H2 | **WIN-5** — pressing `q` closes the game window and leaves every other window alone | the failure mode is destructive |
| H3 | **WIN-3** — the title bar reads exactly *Terminal Game* | depends on Terminal's per-profile title settings, which vary by machine |
| H4 | **WIN-2** — 18 pt Menlo is "large enough to read comfortably" | a judgement, not a measurement |
| H5 | **SCRN-7** — no visible flicker while the ghost moves | perceptual |
| H6 | **SCRN-3/5** — the walls look like the picture and the two characters are told apart at a glance | perceptual |

---

## 9. Sequence diagrams

### 9.1 Starting a game — WIN-1..4, START-1..5

```mermaid
sequenceDiagram
    actor P as Player
    participant PL as play (process A)
    participant W as window.py
    participant T as Terminal.app
    participant G as "Terminal Game" (process B)
    participant R as rules.py (pure)
    participant V as view.py (pure)

    P->>PL: ./play
    PL->>W: find_reference_window()
    W->>T: position of window whose tab tty = os.ttyname(0)
    T-->>W: (x, y)
    W->>T: do script "exec '<repo>/Terminal Game'"
    T-->>W: tab t
    W->>T: id of (first window whose tabs contains t)
    T-->>W: window id N
    Note over W,T: every later call addresses id N and nothing else
    W->>T: tab 1: 40 cols, 30 rows, Menlo 18, black bg,<br/>all title components off
    W->>T: position of window id N = (x+30, y+30)
    T->>G: spawn

    G->>G: write ESC]7;BEL  (clear directory prefix → WIN-3)
    G->>R: new_game(Random())
    R->>R: maze.generate  → braided 9×14 lattice
    R-->>G: GameState (player centre, ghost furthest, dots, score 0)
    G->>V: render(state)
    V-->>G: Frame
    G->>G: screen.paint(Frame)   ← first picture, nothing pressed
    Note over G: ghost's first deadline is now + 143 ms  (START-5, GHOST-1)
    PL->>T: poll busy of tab 1 of window id N  (blocks here until the game exits)
```

### 9.2 One loop iteration, and the END-3 precedence case

```mermaid
sequenceDiagram
    participant L as loop.py
    participant S as screen.py (curses)
    participant R as rules.py (pure)
    participant V as view.py (pure)

    loop until QUIT
        L->>S: read_key(remaining_ms)
        alt arrow key arrives before the deadline
            S-->>L: Direction
            L->>R: move_player(state, dir)
            Note right of R: wall? → unchanged state (CTRL-3)<br/>dot?  → score+1, dot removed (SCORE-1..3)<br/>ghost on target? → CAUGHT (END-1)<br/>else no dots left? → CLEARED (END-2)<br/>CAUGHT is tested FIRST → END-3
            R-->>L: state'
        else deadline reached first
            S-->>L: None
        end

        opt monotonic() >= next_tick
            L->>R: move_ghost(state, rng)
            Note right of R: straight on if open (GHOST-2)<br/>else random non-reverse turn (GHOST-3)<br/>reverse only if nothing else (GHOST-3)<br/>dots untouched (SCORE-4)<br/>lands on player → CAUGHT (END-1)
            R-->>L: state'
            L->>L: next_tick += 1/7 s
        end

        L->>V: render(state)
        Note right of V: walls → dots → player → ghost last,<br/>so the ghost covers the player on a loss (END-4)
        V-->>L: Frame
        L->>S: paint(Frame)  → one refresh, ncurses diffs (SCRN-7)
    end

    Note over L,R: once outcome != PLAYING both transitions are no-ops (END-5);<br/>only q returns from the loop (END-6), and the process exit is what<br/>lets play close the window (WIN-5)
```

---

## 10. Requirement traceability — all 49

| Code | Where it lives | How it is checked |
|---|---|---|
| GAME-1 | `model.GameState`, `rules` | unit |
| GAME-2 | `rules.move_player` outcome branches | unit (`test_end`) |
| GAME-3 | *absence* — no lives/levels/pause anywhere in `model` | review: `GameState` has no such fields |
| WIN-1 | `window.open_game_window` — `do script` | human H1 |
| WIN-2 | `window` — tab `number of columns`/`rows`, font, bg | **measured**: `stty size` = `30 40`; human H4 for font size |
| WIN-3 | executable named `Terminal Game` + `ESC]7;BEL` + title toggles off | **measured**: window `name` == `Terminal Game`; human H3 |
| WIN-4 | `window.find_reference_window` + `position` offset | **human H1 — cannot be asserted by an agent** |
| WIN-5 | `play` waits `busy → false`, closes by id | human H2 |
| SCRN-1 | `view.render` — rows 0..28 maze, row 29 status | unit (`test_view`) |
| SCRN-2 | `Frame` is characters only; no image code exists | review |
| SCRN-3 | `theme.WALL_GLYPH[16]` mask table + joiner-column rule | unit, all 16 masks; golden fixture |
| SCRN-4 | `theme.DOT` `▪`, dim gold | unit |
| SCRN-5 | `theme.PLAYER` `▐█▌` bright yellow, `theme.GHOST` `▗█▖` pink | unit; human H6 |
| SCRN-6 | `view.status_line` style = cyan | unit |
| SCRN-7 | `screen.paint` one `refresh` per frame; `curs_set(0)` | **measured**: 0.25 ms/frame, `\e[?25l` emitted; human H5 |
| MAZE-1 | `maze` — 19×29 from a 9×14 lattice; cols 37..39 blank | unit |
| MAZE-2 | link cells are single cells by construction | unit: no 2×2 open block, 1000 seeds |
| MAZE-3 | row 0/28, col 0/18 are never node or link | unit, 1000 seeds |
| MAZE-4 | `generate(rng)` called with an unseeded `Random()` in `rules.new_game` | unit: two seeds → two different mazes |
| MAZE-5 | braid pass: every node reaches degree ≥ 2 | **measured**: 0 failures in 5000; unit, 1000 seeds |
| MAZE-6 | spanning tree first; braiding only adds edges | unit flood-fill, 1000 seeds |
| START-1 | `rules.choose_player_start` — nearest corridor to (14, 9) | unit |
| START-2 | `rules.choose_ghost_start` — max squared Euclidean | unit (see Assumption A2) |
| START-3 | `dots = corridors − {player}` | unit |
| START-4 | `score = 0` | unit |
| START-5 | `loop` paints before its first `read_key`; ghost deadline already set | unit on the state; human H1 for the feel |
| CTRL-1 | `screen.read_key` maps 259/258/260/261 → `Direction` | unit on the mapping table |
| CTRL-2 | one `move_player` per key event; no auto-repeat state exists | unit |
| CTRL-3 | wall target → `return state` unchanged | unit |
| CTRL-4 | `q`/`Q` → `QUIT` → return from `loop`, checked before outcome | unit |
| CTRL-5 | every other key → `None`; `curses.noecho()` in `screen.session()` | unit on the mapping; **measured** (WI-13): a `z` typed into a real session never reaches the terminal, and does if `noecho` is removed — `tests/test_curses_pty.py::NothingTypedIsEchoedTest`, method in `docs/findings/WI-13-curses-echo.md` |
| GHOST-1 | `loop` deadline `next_tick += 1/7` | **measured**: 6.997 ticks/s, max drift 5.08 ms |
| GHOST-2 | `move_ghost` takes `forward` whenever open | unit: corridor run keeps direction |
| GHOST-3 | random non-reverse choice; reverse only when empty | unit with a seeded rng and a hand-built T-junction and a cul-de-sac |
| GHOST-4 | `move_ghost` reads `player` only for the collision test | unit: same seed, different player positions → identical ghost path |
| SCORE-1 | `dots' = dots − {target}` | unit |
| SCORE-2 | `score + 1` when the target held a dot | unit |
| SCORE-3 | no dot → no increment | unit |
| SCORE-4 | `move_ghost` returns `dots` and `score` untouched | unit |
| SCORE-5 | score only ever increases; `view.status_line` renders it | unit |
| END-1 | collision test in **both** transitions | unit, both directions |
| END-2 | `elif not dots'` | unit |
| END-3 | `CAUGHT` branch precedes `CLEARED` | **unit — the one test that must not be deleted** |
| END-4 | draw order: ghost painted last | unit on the `Frame` |
| END-5 | both transitions return `state` unchanged when `outcome != PLAYING` | unit |
| END-6 | `loop` returns only on `QUIT` | unit |
| STAT-1 | `view.status_line` is the only writer of row 29 | unit |
| STAT-2 | `"score {n}    arrows, q quits"` | unit (see Assumption A3) |
| STAT-3 | `"CAUGHT  score {n}   q quits"` / `"CLEARED  score {n}  q quits"` | unit (see Assumption A3) |

> **Correction, WI-13.** Until WI-13 the CTRL-5 row above read *"**measured**:
> `noecho` set in `Screen.__enter__`"*. That was wrong twice over: there is no
> `Screen.__enter__` anywhere in `termgame/screen.py` — the adapter uses a
> `session()` context manager — and nothing had been measured, since no test in
> the suite contained the string "echo". WI-12's audit found it; WI-13 supplied
> the measurement and rewrote the row to describe it. A false record of
> verification is worse than a missing one, so it is corrected here in place
> rather than quietly dropped.

---

## 11. Assumptions

**A1 — WIN-5 means "when the game process exits", not "on the final frame".**
WIN-5 says the window closes *as soon as the game ends*; END-5 says the last
picture stays on screen and END-6 says `q` is the only way to leave a finished
game. Taken literally together they are contradictory. Resolved in favour of
END-5/END-6: the final picture stays, `q` exits the process, the window closes
then. *Affects:* §4 step 5, the WIN-5 / END-5 / END-6 traceability rows, human
check H2. *Cost to flip:* delete one wait in `play` — minutes.

**A2 — START-2's "measured across the grid" is squared Euclidean distance,**
ties broken by lowest `(row, col)`. Manhattan and Chebyshev are equally
defensible readings of the phrase. *Affects:* `rules.choose_ghost_start` and one
test. *Cost to flip:* one expression.

**A3 — the three status strings are reproduced verbatim and start at column 1.**
The spec's two end-of-game examples do not align with one another (`q quits`
begins at offset 19 in `CAUGHT  score 37   q quits` and at 20 in
`CLEARED  score 274  q quits`), and the mock-up shows one blank column before the
status text that the quoted strings do not contain. Taking the quoted strings as
literal templates and indenting all three by one column reproduces both the
quotes and the picture. *Affects:* `view.status_line` and one test.

**A4 — the maze mock-up in the spec is illustrative, not a fixture to
reproduce.** MAZE-4 requires a new random maze each game, so the mock-up cannot
be the maze; it is used as a *golden rendering fixture* (given this grid, the
renderer must produce exactly this picture), which is a much stronger test than
anything hand-written.

**A5 — the game is launched from Terminal.app.** WIN-4's "whatever window the
player was last looking at" is read from Terminal. Launched from iTerm2, VS Code
or an SSH session, `play` falls back to Terminal's front window and then to a
fixed position; the game still runs.

**A6 — 18 pt Menlo satisfies "large enough to read comfortably" (WIN-2).** A
judgement, flagged as human check H4. The value is one constant in `window.py`.

**A7 — `python3` on the player's `PATH` is 3.9 or newer.** True for stock
macOS. The code should therefore avoid 3.10+ syntax (`match`, `X | Y` type
unions) so the system interpreter always works.

---

## 12. Cautions to implementers

**C1 — `addstr` at the bottom-right cell raises.** Measured:
`addstr(LINES-1, COLS-1, ch)` → `addwstr() returned ERR`; `insstr` at the same
cell succeeds. The status line is on the last row. Either keep `paint` off
column 39 of row 29, or use `insstr` for that one cell. Do not discover this
during a demo.

**C2 — the file name `Terminal Game` is load-bearing.** It *is* the window
title (§6.3). Renaming it, invoking it as `python3 "Terminal Game"`, or giving
it a command-line argument all break WIN-3. It is the one place in the repo
where a file name is a requirement.

**C3 — the AppleScript safety rules in §6.3 are not style points.** The
player's own shells and any agent session are windows in the same application.
Address the captured window `id` only; never `front window`, never a title,
never an index; never close a `busy` tab (it raises a modal sheet that blocks
*all* subsequent AppleScript, which reads as a mysterious timeout).

**C4 — do not put a second clock in.** One thread, one deadline. The measured
rate is 6.997 Hz with 5 ms of jitter from a single `getch` timeout. A ghost
thread would buy nothing and would cost you the purity of `rules.py`.

**C5 — do not optimise the renderer.** The naive full repaint is 0.2% of a
tick. Dirty-rectangle tracking would be the first thing to introduce a rendering
bug and the last thing to be needed.

**C6 — keep `curses` out of the core.** If `view.py` ever imports `curses`,
frame-comparison tests stop working without a tty and the main safeguard on
SCRN-1..6 is gone. `Frame` carries style *ids*; `screen.py` maps ids to colour
pairs.

**C7 — `rng` is a parameter, never a module-level `random.*` call.** Every
pure function that needs randomness takes a `random.Random`. This is the only
reason maze and ghost tests are reproducible.

**C8 — END-3 deserves a named test.** It is one `elif` away from being wrong,
the failure is invisible except in a rare board position, and it is the only
place in the spec where two end conditions race.

**C9 — the joiner-column invariant is worth asserting.** Three-character
entities rely on "a joiner column beside a corridor cell is blank". It holds by
construction; write the test anyway, because the whole entity-rendering scheme
collapses quietly if the joiner rule is ever changed.

**C10 — `curses.set_escdelay(25)`.** Present on both interpreters. ncurses
otherwise waits up to a second after a bare `ESC` deciding whether a sequence
follows, which would look like a freeze. Arrow keys are unaffected, but a
stray `ESC` press is not.

**C11 — this was written on macOS 26.6.2 (Darwin 25.6.0, arm64)**, not macOS 15.
Every measurement in §7 is from that machine. The Terminal title behaviour in
§6.3 in particular is version-sensitive; re-run human check H3 on any other
version.

---

## 13. What needs a human

1. **Confirm A1** — does WIN-5 mean the window vanishes on the final frame, or
   when the player presses `q`? This document assumes the latter.
2. **Confirm A2** — which distance metric START-2 means.
3. **Confirm A3** — the exact status-line spacing, given the spec's two examples
   disagree with each other.
4. **Run human checks H1–H6** (§8). H1 (WIN-4) in particular can only ever be
   verified by a person running the game: an agent has no controlling tty, which
   was confirmed directly — `tty` reports "not a tty" in this session.

Nothing in this design needs a macOS permission that is not already granted, and
nothing needs a Terminal preference changed. That was a deliberate goal and it
was reached: Automation on Terminal is already granted, Accessibility is not
required, and the WIN-3 recipe avoids the per-profile title settings entirely.
