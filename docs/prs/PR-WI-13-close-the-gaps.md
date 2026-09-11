# WI-13 — close the gaps the final gate found

**Branch** `wi-13-close-the-gaps`, cut from `origin/main` at `d49f046`
(the merge of PR #15, WI-12).

**Nothing in `termgame/` changes.** Every commit adds or repairs an
*assertion*, plus one wrong line in `docs/ARCHITECTURE.md`. `git diff
origin/main -- termgame/` is empty.

WI-12 audited all 49 requirement codes and deliberately fixed nothing, on the
grounds that a gate that edits what it gates is not a gate. This is the repair
pass. **Every one of its eight findings was re-checked against the code before
it was acted on** — none was taken on trust — and **every new assertion was
broken on purpose and observed to go red for the right reason**, with the
failure message recorded.

## The suite

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 774 tests in 13.246s

OK (skipped=2)
```

749 on `main`, 774 here: **25 added**, none removed, none weakened. The two
skips are the unchanged `tests/test_launch_smoke.py::LaunchSmokeTest`, which
skips with *"no controlling tty: nobody is watching this screen"* in every
agent session by design.

---

## The five gaps

### 1. SCRN-7's hidden cursor had nothing behind it

`tests/test_curses_pty.py:312` asserted `assertIsInstance(RESULT["curs_set"],
int)` — a value the probe script set itself with its own `curses.curs_set(0)`.
Confirmed: the only `curs_set` references in `tests/` were that one and a
literal in a fake result dictionary in `test_verify.py`.

The scripted game now reads back, from inside the real `session()`, the
visibility **the game** left behind — `curs_set` returns the previous
setting, so asking for "hidden" changes nothing and hands back the answer. The
old test is kept and renamed
`test_this_terminal_can_hide_its_cursor_at_all`, with a docstring saying it is
a guard on the terminal and **not** SCRN-7, so that a terminal which cannot
hide a cursor is told apart from a game that does not.

> Deleting `_hide_cursor()` from `session()`:
> `AssertionError: 0 != 1 : the game left the text cursor visible in the maze (SCRN-7)`

### 2. The WIN-2 size test could not fail

Confirmed: it asserted the pty size the test itself had set via `TIOCSWINSZ`,
and imported neither `window.COLUMNS/ROWS` nor `model.SCREEN_COLS/ROWS`.

The pty is now sized from `termgame.model` — the shape the renderer draws for
— and asserted against `termgame.window` — the shape the AppleScript asks
Terminal for. Those are two independent copies of WIN-2's numbers, so it
breaks from **either** side, and the literal 40 x 30 is pinned as well in case
both drift together. The probe's paint and read-back loops follow the same
constants rather than two more literals.

> `window.COLUMNS` 40 → 41: `AssertionError: Lists differ: [30, 41] != [30, 40]`
> `model.SCREEN_ROWS` 30 → 29: `AssertionError: Lists differ: [30, 40] != [29, 40]`

### 3. No test asserted any colour — SCRN-6 had nothing at all

Confirmed: `33`, `178` and `51` appeared nowhere in `tests/`. Acting on the
ruling that a colour the code *chooses* is assertable and must be, while
whether it *looks* cyan stays with the user under H6 — **both, not either**.

Three levels, each of which fails for a different reason:

| where | what it asserts |
| --- | --- |
| `test_theme.py::TestTheColoursTheSpecificationNames` | the exact index each style asks for, **and** the hue that index actually is, decoded from the xterm 6 x 6 x 6 cube in the test |
| `test_screen_adapter.py::BuildAttributesTest` | the colour number handed to `curses.init_pair` — `build_attributes` is the last place a colour exists as a number, so this is the only seam where "the status line is cyan" is checkable without a terminal |
| `test_curses_pty.py` | the escape sequence a **real terminal** receives: `ESC [ 38;5;51 m` in the byte stream of a real scripted game |

Plus `TheFallbackPaletteTest`, because `FALLBACK_PALETTE` is a copy of the
theme that is almost never read, which is exactly how a colour changed in one
place and not the other sits unnoticed until the day it matters.

The hue assertions are the ones worth having. Changing the status line from
51 to **39** — a blue that is very nearly cyan, and which passes every "is it
an int, is it distinct" test in the old suite — produces:

> `AssertionError: 5 != 3 : the status line is not full green, so not cyan`
> `AssertionError: 51 != 39 : the status style no longer asks for colour 51, cyan (SCRN-6)`
> `AssertionError: 39 != 51 : the fallback's status has drifted from theme.py`
> `AssertionError: b'\x1b[38;5;51m' not found in b'...' : the terminal was never asked for colour 51, the cyan status line (SCRN-6)`

And making `build_attributes` ask for colour 7 for every style reddens the
adapter half on its own:
`AssertionError: 33 != 7 : the wall style reaches curses as 7, not as the theme's 33`

### 4. CTRL-5's echo clause — **and the first test I wrote for it could not fail**

Confirmed: `grep -rni "echo" tests/` matched nothing, and there is no
`Screen.__enter__` anywhere in `termgame/screen.py`.

This one took three attempts and the detour is the most useful thing in this
PR. It is written up in **`docs/findings/WI-13-curses-echo.md`**; the short
version:

1. **The tty's ECHO bit is the wrong thing to read.** `curses.initscr()`
   clears it unasked, and `curses.echo()` never sets it back — ncurses echoes
   in *software*, from inside `wgetch`. An assertion on that bit passes
   whatever the game does. I only found this because I broke `noecho()` on
   purpose and the test stayed green.
2. **A painted screen hides the answer.** `wechochar` writes at the cursor,
   and after a full repaint the cursor is parked on the bottom-right cell —
   where this project's own C1 hazard swallows it. Measured: three `z`s typed
   with `curses.echo()` forced on come back **3** times with no paint in
   front, **1** with a paint, **3** with a paint and a `move(5, 5)`; and **0**
   in the real scripted game. So the scripted game cannot see this clause in
   either direction.
3. **What works** is the game's own `session()` with nothing painted in front
   of it: `NothingTypedIsEchoedTest` reads three keys through the real
   `Screen.read_key` and asserts no `z` reaches the terminal, with the pty's
   own line-discipline echo cleared first so anything that comes back is the
   game's doing. Three guard tests sit beside it: the keys really were read,
   the pty really was not echoing, and the output really was captured.

> Deleting `curses.noecho()` from `session()`:
> `AssertionError: b'z' unexpectedly found in b'\x1b[?1049h ... \x1b[H\x1b[2Jzzz\x1b[?1l ...' : the keystrokes the player typed were echoed back into the window: `z` appears 3 times in what the game wrote to the terminal (CTRL-5)`

**`docs/ARCHITECTURE.md:642` is corrected**, in place, with a note saying what
it used to say. A false record of verification is worse than a missing one, so
it is corrected rather than quietly dropped.

### 5. START-2's metric was not pinned — and it blocked WI-11

Confirmed by my own computation, not taken on trust: over seeds 0..199,
squared Euclidean, Manhattan and Chebyshev choose the **identical** corridor
square on all 200. The suite was green whichever metric the code used, so
WI-11 could apply the user's answer to question A2 and nobody could tell.

`GhostMetricDiscriminationTests` in `tests/test_rules_start.py` — named so its
purpose is unmissable, and with the whole situation in its class docstring —
carries two hand-built boards. Each separates squared Euclidean from one
rival, and a third test says in one place why neither board alone is enough.
Every test asserts the metrics genuinely **disagree** on its board before
asserting which square the code picks, so an edit that destroyed the
discrimination would say so rather than quietly proving nothing.

> `starting_ghost` → Manhattan:
> `AssertionError: Position(row=1, col=6) != Position(row=4, col=4) : START-2 is not being measured by squared Euclidean distance. If this is WI-11 applying the user's answer to question A2, this is the test that was built to notice, and the expected square above changes with the metric.`
>
> `starting_ghost` → Chebyshev:
> `AssertionError: Position(row=5, col=5) != Position(row=1, col=6) : ...` (plus the pre-existing hand-written-board test WI-12 predicted)

---

## The three smaller ones — all three were as described

- **`test_maze.py:152`** was named `test_a_thousand_seeds...` and looped
  `range(200)`. The sweep was brought **up** to the name rather than the name
  down to the sweep: 1000 seeds cost 0.74 s and all 1000 mazes are distinct,
  so the test is stronger as well as honest.
- **`test_window_supervisor.py:112`**, `assertEqual("open",
  kinds[kinds.index("open")])`, cannot fail and *raises* rather than reports
  if the open is missing. Replaced with a once-each count over open,
  configure, move and close — a supervisor that opened two windows would leave
  one on the user's screen and the ordering assertions would not notice.
  Making `supervise()` open twice: `AssertionError: 1 != 2 : expected exactly
  one 'open', got [... 'open', 'open', ...]`.
- **The pty unmapped-key test.** The `z` was second-to-last, so a `z` that
  quit left every recorded field byte-identical. **Measured**: with `z` added
  to `QUIT_KEYS` and the old keystroke order, all 21 tests in the file passed.
  With the `z` moved second, the same mutation reddens five, the unmapped-key
  test among them.

---

## No defect in `termgame/` was found

Every gap was a missing or hollow assertion. Nothing required a change to the
product, and none was made.

One thing about the product is worth the lead knowing, and it is **not** a
defect: CTRL-5's echo clause currently holds for two independent reasons —
`noecho()`, and the bottom-right cell swallowing whatever `noecho()` might
have missed. Nothing needs changing; it is why the clause looks untestable
from the game and is not. `docs/findings/WI-13-curses-echo.md` has it.

## For the lead

- **A trap that cost me five spurious failures.** This `python3` uses
  `sys.pycache_prefix` under `~/Library/Caches/com.apple.python`, and a
  same-size edit made within the same second as the cached `.pyc` is **not**
  invalidated. A `51` → `39` restore silently did not take. Every break and
  restore in this PR was re-verified after purging that cache, and the working
  tree is clean of product changes.
- **`./verify` was not run.** Its smoke stage opens a real window on the
  user's screen and nobody asked for one. The pinned suite is the gate these
  changes touch. Terminal window census before and after this work:
  all `[367, 2486, 2420, 2440]`, visible `[367, 2486]` — the established
  values, unchanged. **I opened no window and closed none.**
- **`IMPLEMENTATION_PLAN.md:1151`** carries the same CTRL-5 claim
  (*"echo is off"*) that ARCHITECTURE.md did. It is now **true**, so it is
  left alone — but it is the lead's document and worth a glance.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
