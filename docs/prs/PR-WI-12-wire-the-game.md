# WI-12 — wire the whole game

**Branch** `wi-12-wire-the-game`. **Lane** A (DEV-A), M3. **Local mode.**
**Suite** `python3 -m unittest discover` — **648 passed, 0 failed, 0 skipped**.
**Windows opened: 1. Closed: 1.** Census `['7104']` before and after.

Requirements touched: **STAT-1**, **END-4**, **END-6**, and every code the
assembled game now exercises end to end.

## Exactly what was integrated

| Step | What | Suite |
| --- | --- | --- |
| 1 | Cut from **`wi-11-game-loop` @ `41108ed`** | — |
| 2 | Merged **`main` @ `16b4dac`** — clean, no conflicts | **620** |
| 3 | WI-12's own work | **648** |

**`main` was at `16b4dac`, re-read at the moment of branching.** Nine branches
had landed, including my own `wi-10-rules-outcome` and `wi-6-status-line`, so
**`wi-11-game-loop` and this are all that remain unmerged of lane A.**

**Before touching anything in `launcher/`, I compared it with DEV-B's live
`wi-13-launcher-robustness` by blob id** rather than asking and waiting:
`launcher/game.py` `88870dd`, `tests/test_game_command.py` `fbd8747`,
`terminalgame/game_main.py` `e64b3f9`, `tests/test_layering.py` `707994b` —
**all four byte-identical on both branches.** DEV-B has touched none of them, so
the seam change here cannot collide with WI-13.

## What the game is now

`terminalgame/game_main.py` was the M0 skeleton — one frame, a `--hold` timer,
no game underneath. It is now the assembly point, and almost nothing else:

```python
def build_frame(state):
    return compose(state, status_line=status_row(state))

def play_a_game(screen, seed=None):
    random_source = random.Random(seed)
    return play(screen, new_game_with(random_source), random_source, build_frame)
```

**One seed names the whole game.** A single `random.Random` goes to
`new_game_with` for the maze and the opening positions **and** to the loop for
the ghost. With two sources a seed would reproduce the maze but not the game
played on it — which is exactly what the acceptance pack needs it for, and there
is a test that plays far enough for the ghost to have moved and asserts two runs
agree about where it ended up.

## The camouflage case, and the three places it is guarded

`compose(state, status_line=None)` leaves row 29 blank — and **a frame with a
blank row 29 is a perfectly well-formed frame.** It composes without complaint
and satisfies every test the frame builder has. So forgetting to pass the status
row would not break anything loudly; it would produce a game that quietly fails
STAT-1 while looking entirely correct to every automated check above it.

That is why `build_frame` is a named function with tests of its own rather than
an argument written inline. The assertions are that the row is **not blank** and
**carries the real score**, because *"a status row exists"* is exactly what a
blank row also satisfies. Guarded in three places:

1. `tests/test_game_main.py` — on `build_frame` directly, including that the row
   equals what the status module says it should be, that it is cyan across all
   40 columns, and that no row above it carries the status text;
2. `tests/test_wired_game.py` — on **every frame a played game presented**, not
   just one;
3. the real run — the picture in the finding has the row on it.

## `--hold` is gone, from both sides in one commit

It was M0 scaffolding. The real game ends when the player presses `q` (END-6)
and the launcher takes the window afterwards (WIN-5, under assumption A1).

**Both sides had to change together**: either alone leaves the launcher starting
a game with an argument it will reject. `launcher/game.py` no longer passes it
and no longer offers it; `game_main` no longer accepts it. Both now take
`--seed` instead.

**What that costs, said where the constant used to be**: the launched command is
no longer bounded by anything the launcher controls. That is correct for a game
— a player may stare at a maze for an hour — and it is safe because the launcher
never closes a window with something running in it and waits on the **process
list** rather than a clock. But **anything that starts a game without a person
at the keyboard must now arrange its own way out**, because nothing in the
launcher will end one. The real run below does exactly that.

## Both layering debts paid

**`LauncherTest` — the gap open since M0.** Nothing had ever walked `launcher/`;
that the launcher shares no code with the game had been checked by hand, which
is to say checked once. It now uses `ast` to **enumerate every import and judge
each**, rather than asking whether a name is mentioned — the other scans in that
file answer "does this mention X", where this one must miss nothing. Four
checks: the launcher imports nothing from `terminalgame`; every import is either
the standard library or `launcher` itself; the game never imports the launcher
either; and the scanner can see what it is looking for.

"Standard library" is decided **from the tree** — is this name a package this
repository defines? — rather than from a list of stdlib names, which 3.9 does
not offer and which would go stale.

**`ApplicationLayerTest` — the class I deferred from WI-11**, having said WI-12
was the natural place to settle what Application may import. It is: the loop may
reach the Domain, Presentation and the screen port, never the terminal adapter,
never `curses` or `subprocess` — and, the half that is easy to lose, **nothing
beneath it imports it**, which is what keeps the Domain and Presentation
testable by the thousand with no loop anywhere.

### The scanner had a bug and its own test found it

`top_level_imports` hardcoded relative imports as `launcher`, so the game's own
`from .screen import port` was reported as importing the launcher, and
`test_the_game_never_imports_the_launcher_either` failed on `game_main.py` and
`curses_adapter.py`. It now takes the package to resolve relative imports
within, and **refuses to guess one** — left out, it reports `"."`, which belongs
to nothing and so can never be mistaken for a real dependency.

Worth recording because the failure was in the guard, not in the code it guards,
and a guard that is wrong in that direction is the kind that gets "fixed" by
loosening it.

## The pty tests move from `--hold` to `q`

`tests/test_real_terminal.py` drove the real game process with a bounded
`--hold`. It now types `q`, which is what ends the real game — and
`PATIENCE_SECONDS` still kills a child that will not go, so **a game that
stopped listening fails the suite rather than hanging it**. Its failure message
says so now instead of talking about a hold that no longer exists.

**The `PENDIN` mask is untouched.** It is the one transient bit that differs
after a correct curses session, and weakening the comparison would throw away
the only check that the player's shell comes back.

Its content assertions moved from the skeleton's placeholder text to the real
picture: the status line, the wall glyphs and the dots.

## The real run

One window, in `docs/findings/WI-12-the-whole-game-in-a-real-window.md` with the
picture read off the live tab. In short: window **7891** opened at +0.93 s, the
game running at +0.95 s, the whole maze with joined-up walls, a dot on every
corridor square, the player `▐█▌` near the middle and the ghost `▗█▖` most of
the way across the maze after roughly twenty ticks **with nothing pressed** —
which is GHOST-1 and START-5 in one picture. `q` at +4.05 s, game gone at
+4.17 s, window closed by its captured identity, **nothing leaked**.

Also reproduced: **`set position` is a request, not an instruction.** Asked for
y = −1352, landed at y = 30 — WI-1's measurement exactly, visible only because
the launcher reads the position back instead of believing the move.

**Safety.** The window id was captured at creation and every later call named
it. `q` was delivered with `do script … in selected tab of window id 7891`,
which writes to that one tab, so nothing depended on focus and no keystroke went
anywhere near the user's own windows. Had `q` failed, the harness would have
killed **the child by pid, never the window** — a dead child lets the window
fall idle and close cleanly, where closing a busy window raises the modal sheet
that blocks every later automation call including the cleanup. The reap ran in a
`finally`. The census metric is `visible is true`, because `id of every window`
reports windows already closed.

## Deviations, for a ruling

1. **`--seed` is new on both the game and the launcher.** The plan asks for
   neither. It exists because one seed naming a whole game is what makes WI-14a
   able to assert anything about a *particular* game, and because reproducing a
   reported bug otherwise means reproducing a random maze.
2. **`play_a_game` is separate from `main`** so a test can play a whole game
   without an argument parser or an exit code in the way.
3. **I changed four files that are not mine alone** — `launcher/game.py` and
   `tests/test_game_command.py` (the seam), `tests/test_real_terminal.py`
   (DEV-B's WI-2 pty harness) and `tests/test_layering.py` (the shared guard).
   All four were byte-identical on DEV-B's live branch when I started, so none
   was being edited. **Flagged so DEV-B is told rather than surprised.**

## A deliberate omission, recorded so nobody "fixes" it

`terminalgame/game_main.py` is **not** added to `ApplicationLayerTest`'s
`application_files()`, because it is not under `terminalgame/application/`. It
is the process entry point and sits above the layers, which is why it is allowed
to import all of them. Moving it into the package would make
`test_nothing_beneath_it_depends_on_the_application_layer` narrower rather than
stronger. **This is a decision, not an oversight.**

## Assumptions

**Q1 is at its most load-bearing here and remains an assumption.** A1 — the
picture freezes at the ending and the window closes by itself when the player
quits — is the whole end-of-game behaviour of the wired application. The loop
stops moving anything, the frame stops being rebuilt, `q` is the only key still
acted on, and the launcher closes the window when the process goes. **If the
user rules otherwise, this is the item that changes.** Not recorded as a ruling.

Q2 (the Automation permission) was available throughout; Q3's `--seed`-free
default keeps MAZE-4.

## Contradictions found

**None.** Everything assembled as specified.

One observation: **nothing in the specification says what happens if the player
never quits.** END-6 makes `q` the only way out of a *finished* game, and GAME-3
rules out a timer, so a game left running holds its window indefinitely — which
is correct, and is why removing `--hold` needed the note about unattended
starts rather than being a silent tidy-up.

## What needs a human

1. **The colours.** `contents of selected tab` is text, so SCRN-3 to SCRN-6 —
   blue walls, dim gold dots, a bright yellow player, a pink ghost, a cyan
   status line — are unverified by any automated check. Run
   `python3 -m launcher.game`, look, press `q`.
2. **WIN-2's font**, whether Menlo 14 is comfortably readable.
3. **SCRN-7's flicker**, which a capture cannot see.
4. **Playing it.** Nobody pressed an arrow key in a real window; whether the
   ghost is too fast to escape or too slow to fear is a judgement about play.
5. **WIN-4**, that the window lands visibly below and right of the previous one
   — the numbers say it did, but "visibly" is a person's word.

## Commits

| | |
| --- | --- |
| `de576a2` | WI-12: wire the whole game |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
