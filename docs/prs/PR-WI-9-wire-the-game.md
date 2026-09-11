# WI-9 — Wire the real game together

**Branch** `wi-9-wire-the-game` · **base** `main` at `c8defe7` · Dev A, round 5,
iteration M2.

This is the item where the game becomes a game. GAME-1, GAME-2, START-5,
CTRL-1..5, GHOST-1, END-4, END-5, END-6 and WIN-5 stop being true in pieces and
start being true of the running program.

## What it does

The three seams WI-4 built are filled with the things they were built for.

| Seam | Was | Is |
|---|---|---|
| starting state | `standins.new_game` | `rules.new_game` |
| picture | `loop.resolve_render()` — a run-time module lookup | `view.render`, plainly imported |
| player transition | `standins.move_player` | `rules.move_player` |
| ghost transition | `standins.move_ghost` (which did nothing) | `rules.move_ghost` |

`termgame/standins.py` is **deleted**, as WI-4 said it would be.
`loop.resolve_render` is **deleted**, as WI-4's own report asked.
`run_loop` itself is byte-for-byte unchanged, which was the whole point of its
taking those four things as parameters.

### The child executable did not change

**`Terminal Game` needed no edit.** It writes the title-clearing escape
sequence, puts the repo on `sys.path`, and calls
`sys.exit(run_game())` — and that is still exactly the entry point.
The seam WI-2 built was in the right place, and
`RunGameIsTheOnlyThingTheChildCallsTest` now says so in the suite so that a
later change cannot quietly move it.

### One addition to `run_game`'s signature

`run_game()` grew two optional keyword parameters, `open_screen` and `out`,
and one more, `stdin`. All three have defaults and **the child still calls it
with no arguments**.

`stdin` is the one that needs justifying. `run_game` decides between curses and
the plain-text path by asking whether stdin is a tty. A test of that decision
that could not *say* "there is no terminal here" would, on the day somebody
runs the suite from a real terminal, open curses and block the whole suite on a
keypress nobody is there to make. `stdin` is a parameter so the test can be
honest instead of lucky. `open_screen` is the same idea for the other branch:
it is a real capability (a caller supplying its own screen), and it is how the
scripted games drive the entry point end to end.

## Files

- `termgame/loop.py` — `run_game` builds a real game and drives the loop with
  the real renderer and the real transitions; `resolve_render` gone.
- `termgame/standins.py` — **deleted**.
- `tests/test_scripted_game.py` — **new, 41 tests.** The scripted full game.
- `tests/test_loop.py` — `ResolveRenderTest` replaced; a local `a_plain_step`
  transition replaces `standins.move_player` in the loop's own tests, on
  purpose (below).
- `tests/test_curses_pty.py` — the real-ncurses scripted run now drives the
  **real** rules and the **real** renderer, and asserts on the real outcome and
  the real status line.
- `tests/test_screen_adapter.py` — the fallback palette is now checked against
  what the real renderer emits for a real game.
- `docs/findings/WI-9-the-running-game.md` — what the wired game does in a real
  process: the measured tick rate, the measured cost of a frame, the ghost's
  reversals, and a game that ended by itself.

### Why the loop's own tests do *not* use `rules.move_player`

`tests/test_loop.py` drives the loop with a small local transition rather than
the real one, and that is deliberate rather than left over. Those tests are
about the *shape* of the loop, and most of their boards start with no dots at
all — under `rules.move_player` the very first arrow press would win the game
by END-2, and every one of them would then be asserting the rules instead of
the loop. The real transitions are driven through the real loop in
`tests/test_scripted_game.py`, which is where that belongs.

## What the new tests establish

**A scripted full game, to a win and to a loss**, through the real
`run_loop` + `rules` + `view`, with only the screen and the clock faked:

- **a win** — a board cleared, two dots eaten, `CLEARED`, status line
  ` CLEARED  score 2  q quits`, and the ghost really moving on the real ticks
  the whole time;
- **a loss the player caused** — walked into the ghost with a dot still on the
  board, so it is END-1 and not the END-3 ordering case;
- **END-3, played rather than reasoned about** — the last dot *is* the ghost's
  square, both conditions hold in the same move, and the answer is `CAUGHT`.
  The test also asserts the board really was cleared by that move, so it cannot
  pass on a game that simply never cleared;
- **a loss the ghost caused** — the player never presses a key at all; the
  ghost walks the corridor and arrives (END-1's second half, GHOST-1), and the
  dot it crossed on the way is still on the board (SCORE-4).

**After the ending** (END-5, END-6, STAT-3): eight more arrow keys in all four
directions and eight more ticks arrive, and every state painted after the
ending is **the very same object** — identity, not equality, which is what the
loop relies on when it declines to test the outcome itself. A picture is
painted every turn, every picture after the ending is identical, the status
line goes on saying which ending happened, and only the `q` returns.

**`run_game` itself**: it paints before it reads (START-5), the first picture is
a whole 30 × 40 window with a 19 × 29 maze and a blank right margin (MAZE-1),
the status line of a fresh game reads ` score 0    arrows, q quits`
(START-4, STAT-2), a dot sits on every corridor but the player's (START-3), and
**two games in a row are not the same game** (MAZE-4, end to end through the
entry point).

## Suite

```
/usr/bin/python3 -m unittest discover -s tests
Ran 606 tests in 12.013s
OK (skipped=2)
```

Cross-checked on `/opt/homebrew/bin/python3` 3.14.7: `Ran 606 tests`, `OK
(skipped=2)`. The gate is 3.9.6.

### The ledger — 567 on `main`, 606 here

**This is the one item whose count can go down, so it is observed rather than
reconstructed**: `c8defe7` extracted with `git archive` into a scratch
directory, the pinned command run with `-v` in both trees, the test ids listed,
sorted, and diffed.

**Removed — 7**

| Test | File | Why |
|---|---|---|
| `ResolveRenderTest` × 6 | `test_loop.py` | The run-time renderer lookup is gone, so its fake-lookup cases have nothing left to drive. One of the six, `test_the_picture_the_loop_paints_is_the_size_of_the_window`, **moved** to the replacing class rather than being deleted — it appears on both sides of the diff and nets to zero. |
| `test_the_fallback_knows_every_identifier_the_stand_in_emits` | `test_screen_adapter.py` | The stand-in had no vocabulary left to publish. **Renamed and rewritten in place** as `test_the_fallback_covers_every_style_a_real_picture_emits`, a stronger claim against what the real renderer actually emits — also a net zero. |

**Added — 46**

| File | Count |
|---|---|
| `test_scripted_game.py` (new) | 41 |
| `test_curses_pty.py` — real outcome, real status line | 2 |
| `test_loop.py` — `TheRendererTheLoopDrawsWithTest` | 2 |
| `test_screen_adapter.py` — the rewritten fallback test | 1 |

**567 − 7 + 46 = 606**, which is exactly what the runner prints.

Netting out the two pairs that are a move and a rename: 5 genuinely deleted,
44 genuinely new, 567 − 5 + 44 = 606. Both framings agree.

The two skips are unchanged from `main` — they are `test_launch_smoke`'s, and
they need a controlling tty.

No test file stopped being discovered: 20 flat `test_*.py` in `tests/`, plus a
`fixtures/` directory holding data only, and still no `tests/__init__.py`.

**The ledger found a defect of mine.** The diff showed
`test_loop.TheRendererTheLoopDrawsWithTest.test_the_stand_ins_are_gone` was
character-for-character `test_scripted_game.TheStandInsAreGoneTest.test_the_module_cannot_be_imported`.
I removed the `test_loop` one; 607 became 606. Reading the files would not have
caught it.

## Mutation checks

not applicable — not part of this workflow

## What I observed of the game actually running

Written up in full, with the numbers, in
`docs/findings/WI-9-the-running-game.md`. The short version, all from real
processes on a 40 × 30 pty with real ncurses and a real generated maze:

- **GHOST-1 holds with the real renderer drawing.** Three runs of ~11.7 s:
  **6.99990, 7.00078 and 6.99999 ticks/s**. Cumulative drift against an ideal
  ¹⁄₇ s grid: mean 0.7–1.2 ms, max 12.2 ms. The architect measured 6.997 ticks/s
  against a stand-in; the real picture costs the game nothing.
- **The ghost never reversed**: 0 reversals in 195 live ghost moves, 149 of them
  straight on. WI-7's finding, confirmed in games that were actually played.
- **A game ended by itself.** One run came back `CAUGHT`, score 0, all 267 dots
  still down: the player never moved from `(14, 9)` and the ghost arrived there
  from `(1, 1)` after 29 ticks — 4.14 s — taking no notice of where they were
  (GHOST-4). The remaining 54 ticks changed nothing and the `q` was what
  returned. That is END-1, END-5 and END-6 unprompted in a real process.
- **`/usr/bin/python3 "Terminal Game"` with no tty paints the specification's
  picture** — 29 maze rows and a status line, double-line walls joining into
  corners and tees, lone wall squares as `■`, the player at the centre, the
  ghost at the far corner, a dot on every other corridor square, blank margin
  in columns 37–39.

**No Terminal window was opened.** I have no controlling tty, so I could not
press `q`, and scripting keystrokes into another application needs
Accessibility, which this design deliberately does not require. WI-4 declined
for the same reason and got its coverage from a pty; so did I. Consequently the
window census is untouched — I opened nothing and closed nothing.

## Deviations needing a ruling

1. **`run_game` gained three optional keyword parameters** (`open_screen`,
   `out`, `stdin`). Additive; the child calls it with none of them. Reasoning
   above — `stdin` in particular is what keeps the suite from blocking on
   curses when it is run from a real terminal.
2. **`tests/test_loop.py` keeps a local `a_plain_step` transition** rather than
   switching to `rules.move_player`. Reasoning above.
3. **The win board in `test_scripted_game.py` is deliberately disconnected**
   (two corridors with a wall between). MAZE-6 is a promise about
   `maze.generate`, not about `maze.from_text`, and a scripted game whose every
   ghost step had to be predicted to avoid an accidental collision would be a
   test of arithmetic rather than of wiring. Said so in the module docstring.
4. **A findings document was written** — `docs/findings/WI-9-the-running-game.md`.
   §5 of the plan does not ask WI-9 for one. It is there because §2.5 says a
   measurement worth relying on later goes in `docs/findings/`, and the tick
   rate, the frame cost and the reversal count are all that.

## Contradictions found

**`loop.py`'s docstring — and `ARCHITECTURE.md` §7 behind it — understate the
cost of painting every turn by roughly fifty times.**

`loop.py` says the loop paints on every turn even when nothing changed and that
"it costs 0.25 ms of a 143 ms tick". That 0.25 ms is §7's *Repaint cost* row,
which measured **a naive `addstr` loop against a bare curses window** — not this
adapter, and not the renderer that feeds it. Measured in a real game:

| | mean | max |
|---|---|---|
| `view.render` — building the `Frame` | 3.4 – 11.8 ms *(load-dependent)* | 20.3 ms |
| `screen.paint` — the curses adapter | 0.5 – 1.4 ms | 3.1 ms |
| **together** | **3.9 – 13.2 ms = 2.7 % – 9.2 % of a tick** | 14 % of a tick |

Nearly all of it is the pure renderer, which nobody had measured at all.

**Nothing is broken by this** — even the worst single frame left 86 % of the
tick unused, and the measured tick rate is 6.9999–7.0008/s. But a reader who
takes "0.25 ms" as the per-turn cost is wrong by two orders of magnitude, which
matters the day somebody wants to add to the picture. I have not edited the
architecture; that is the conductor's to rule on.

## What needs a human

Nothing here is claimed as verified by me.

1. **The colours and the flicker — human checks H3, H4, H5.** SCRN-3's blue
   double lines, SCRN-4's dim gold dots, SCRN-5's bright yellow player and pink
   ghost, SCRN-6's cyan status line, and SCRN-7's redraw with no flicker and no
   visible cursor. A pty capture is bytes; none of these are judgeable from
   bytes. **Run `./play` and look.**
2. **WIN-5 and human check H2 — the window closing on `q`.** I cannot press
   `q`, so the whole of the *process exits → supervisor closes the window* path
   is unobserved by me. `./play`, play a little, press `q`, and the window
   should go away on its own and take nothing else with it.
3. **That a person can play it to a win and to a loss.** The plan's "done when"
   for this item. I have played it to a win and to a loss in scripted form and
   watched a real process lose on its own, but neither is a person with their
   hands on the arrow keys.

## Open question, still open

**A1 — does WIN-5 mean the window vanishes on the final frame, or when the
player presses `q`?** Unanswered. I proceeded on the architect's reading: the
last picture stays (END-5), `q` exits the process (END-6), the supervisor closes
the window then (WIN-5). **This is an assumption, not a ruling.** What rests on
it here: `run_loop` returning only on quit, `run_game` returning only after it,
and `NothingHappensAfterTheEndingTest`. If the answer differs, the change is
WI-11's and it lives in `window.py`, not in this branch — and the plan's §10
note applies, that the answer "on the final frame" makes WIN-5 and END-5/END-6
genuinely contradictory and needs a second answer before anyone implements it.

## Note on the user's own commits

Local `main` carries unpushed commits of the user's touching `orchestration/`
only. This branch was cut from `c8defe7` (`origin/main`), so those commits are
not underneath it and **`orchestration/static/index.html` does not appear in
this diff**. I did not touch anything under `orchestration/`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
