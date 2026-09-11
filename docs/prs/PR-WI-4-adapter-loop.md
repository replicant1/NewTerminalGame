# WI-4 — The curses adapter and the loop with its one deadline

**Branch** `wi-4-adapter-loop`, cut from `main` at `c75f052`, with `main`
merged in once WI-3 landed. **Lands** SCRN-7, CTRL-1, CTRL-2, CTRL-4, CTRL-5,
GHOST-1 (the deadline), START-5 (painted before the first read), END-6.

## What this is

The only module in the repository that imports `curses`, the single-threaded
loop that owns the game's one clock, and — the point of the item — the two
*decisions* in that layer pulled out into pure functions so that five
requirements get real tests instead of a footnote.

| | |
|---|---|
| `termgame/controls.py` | **pure.** What a key code means: arrows to directions, `q`/`Q` to quit, everything else to nothing. CTRL-1, CTRL-4, CTRL-5. |
| `termgame/ticker.py` | **pure.** When the tick is due, how long to wait for a key, and the **additive** advance that is the whole of GHOST-1. The time arrives as a parameter; the module imports no clock. |
| `termgame/screen.py` | **impure, sole `curses` importer.** Enter and leave curses safely, hide the cursor, `noecho`, `cbreak`, `keypad`, `set_escdelay(25)`, paint a `Frame`, read a key with a timeout. It holds no decision about the game. |
| `termgame/loop.py` | **impure.** The loop, taking its screen, clock, renderer and transitions as parameters so a fake can drive it. Plus `run_game`, the entry point `Terminal Game` calls. |
| `termgame/standins.py` | **pure. WI-9 deletes this file.** A starting state, a player step, a ghost that does nothing, and a crude picture — so the M0 demo moves, which is what proves the seam. |

The shape of the loop is the architecture's §6.2 sketch, unchanged:

```
paint(render(state))                       # before the first read: START-5
loop:
    key = screen.read_key(time until the deadline)
    quit  -> return                        # CTRL-4, END-6
    arrow -> one player transition         # CTRL-1, CTRL-2
    anything else -> nothing               # CTRL-5
    deadline passed -> one ghost transition, deadline += one tick  # GHOST-1
    paint(render(state))                   # SCRN-7
```

No second clock, no thread, no `asyncio`, no signal handler (C4). No
dirty-rectangle tracking (C5) — the full repaint is 0.25 ms against a 143 ms
tick, and the plan was explicit about not building it.

## §10.1, which is the reason this item looks like this

`ARCHITECTURE.md` §8 says the adapter and the loop are "not unit-tested", and
then §10 traces CTRL-1, CTRL-2, CTRL-4, CTRL-5 and END-6 to those two modules
with "unit" named as the check. Five requirements would have had no test. The
plan ruled: pull the key mapping and the deadline out as pure functions, and
make the loop drivable by a fake screen and a fake clock.

That is done, and it is where the weight of the test suite sits:

- **`tests/test_controls.py`** — CTRL-5 is a claim about *every* key there is,
  so it is checked by sweeping the whole key space from −1 to 1023 and
  asserting that exactly six codes in it mean anything at all. Letters,
  digits, punctuation, the function keys, a resize event, a `getkey()` string
  and a `bool` all mean nothing. It also asserts the four arrow integers
  really are the ones ncurses reports — `controls.py` copies them rather than
  importing curses, and nothing else in the suite would notice if they
  diverged and the arrows silently stopped working.
- **`tests/test_ticker.py`** — a hundred deliberately late ticks, at the 5 ms
  lateness the architect measured, land exactly where they should. The test
  runs the **mistake alongside it**: resetting the deadline to `now + tick`
  instead of adding a tick to it loses half a second over the same hundred
  ticks. The property is pinned by a comparison rather than by a tolerance
  somebody can widen later.
- **`tests/test_loop.py`** — the loop driven end to end by fakes. The fake
  clock is moved on by the fake *screen*, because in the real thing it is the
  wait for a key that makes time pass; a scripted key can therefore arrive
  *early*, which is the case both GHOST-1 and CTRL-2 turn on.

## The bottom-right cell, measured rather than assumed

`tests/test_curses_pty.py` runs the adapter against **real ncurses on a real
40 × 30 pseudo-terminal** — the plan asked for that "if you can make one". It
can be made: `pty.openpty()` with `TIOCSWINSZ`, a child process on the slave
end, and the result handed back through a file. It opens no window, touches
nothing on anyone's desktop, and needs no controlling tty.

It proves both halves of C1:

| | |
|---|---|
| `addstr(29, 39, ch)` | raises `addwstr() returned ERR` |
| `insstr(29, 39, ch)` | no error |
| `Screen.paint` of a full 30 × 40 picture | no error |
| the screen read back | identical to the picture, corner cell included |

The hazard being re-measured matters as much as the guard being tested: if
`addstr` there ever stopped raising, the guard would quietly become dead code
and nobody would find out.

## Two things the two halves of M0 had to agree on

**The style identifiers.** WI-3 owns the vocabulary and WI-4 paints it, and
the two were built in parallel. The adapter therefore reads
`termgame.theme.STYLES` when it is there and falls back to its own table when
it is not, and an identifier the table does not describe **falls back to the
default attribute** rather than raising — a disagreement between the two
halves should cost colour and never the picture. The colour numbers are not
copied into the adapter, so a change after human check H6 lands in the pure
module where a reviewer expects to find it.

`TheRealRendererTest` in `tests/test_screen_adapter.py` is self-arming: it
skips while `termgame.view` does not exist and turns itself on the moment WI-3
merges, asserting that every identifier the real renderer emits is one the
palette knows. That converts the lenient fallback — which is the right
behaviour and is also exactly how a colour bug hides — into a loud failure at
the seam.

**When the game is over.** The loop holds **no test of the outcome**. It calls
the transitions as usual and they decline. That is what keeps game logic out
of the shell, and it is a requirement on what WI-6 and WI-7 land: *a
transition applied to a finished game must return the same state.* It is
asserted here against the stand-ins and is named in `loop.py`'s docstring.

## Deviations that need a ruling

1. **WI-2's placeholder screen is gone, and its tests with it.** The item said
   the loop's body was mine to replace; `placeholder_screen`, `paint`,
   `size_label` and `wait_for_quit` went with it, and so did the nine tests in
   `tests/test_placeholder_screen.py`. **The suite therefore loses nine tests
   that main had.** Everything they protected is protected better elsewhere:
   C1 is now measured against real ncurses rather than asserted about an
   escape-sequence string, and the picture being exactly the size of the
   window is asserted against the real picture in `tests/test_executables.py`.
2. **`run_game` keeps a no-terminal path, and now paints on it.** With no
   controlling tty there is no key to press, so rather than block for ever in
   a window nobody could then close (plan §2.6 rule 4) it writes one frame as
   plain text and returns. WI-2 had the same guard; what is new is that it
   paints. That is how `tests/test_executables.py` can assert the real
   picture, and how an agent — which has no tty at all — can see what the game
   would draw. **Additive, so it needs a ruling.**
3. **The loop looks its renderer up rather than importing it**
   (`loop.resolve_render`). WI-3 and WI-4 were built in parallel against a
   picture type that was already merged, so the import could not be written
   when this module was. WI-9 should replace the whole of it with a plain
   `from termgame.view import render`. Both branches of the lookup are tested.

## Contradictions found

- **§10.1, already ruled on**, and this item is the ruling carried out.
- **`int(remaining * 1000)` loses up to a millisecond on a dirty float.**
  Measured: `int((10.1 - 10.0) * 1000)` is **99**, not 100. The architecture's
  §6.2 writes the truncating form and that is what is shipped, because it is
  what the 6.997 ticks/s measurement was taken with and because truncation
  can only ever wake *early*. The cost is one extra turn of the loop and one
  extra 0.25 ms repaint per tick, and never a missed tick. It is recorded here
  because it is also why nothing in `tests/test_ticker.py` asserts an exact
  millisecond against a value that is not exact in binary.

## What needs a human

- **H5 — no flicker while the ghost moves.** Perceptual; I cannot judge it and
  do not claim it. What I can say is what the design rests on: one `addstr`
  per cell and one `refresh`, with ncurses diffing its virtual screen against
  the physical one, and no `erase()` before the paint.
- **H6 — the picture looking right**, which is WI-3's to answer, but the
  colours are the adapter's to apply. If the colours want changing they should
  be changed in `termgame/theme.py`; the adapter reads them.

## Suite

```
/usr/bin/python3 -m unittest discover -s tests
Ran 368 tests in 6.980s
OK (skipped=2)
```

`main` stood at **258 / 2** after WI-3 merged. This branch merges `main` in —
no conflicts; WI-3 touched no file of mine — adds 119 tests, and removes WI-2's
nine placeholder ones. The same 368 / 2 on `/opt/homebrew/bin/python3` 3.14.7,
as the plan's cross-check.

The two skips are `tests/test_launch_smoke.py`, guarded on a controlling tty,
exactly as WI-2 left them. Nothing in this branch opens a window, and this work
item opened none while it was being built.

With WI-3 merged in, two self-arming tests armed and passed for the first time
against real data: every style identifier `view.py` emits is one the palette
knows, and `loop.resolve_render()` now resolves to `view.render`. The child
executable, run with no tty, paints the real maze with the real double-line
wall glyphs, the dots, the three-character player and ghost, and
`score 0    arrows, q quits` on the last row.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
