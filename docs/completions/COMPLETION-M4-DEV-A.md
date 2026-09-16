# COMPLETION — M4, DEV-A

**Run:** 6 · **Iteration:** M4, *the game itself*
**Lane:** DEV-A · **Work item finished:** **WI-18 — the wiring**
**Mode:** non-local — real pull request, merged by DEV-A

---

## What was finished

Branch `r6/wi-18-the-wiring`, cut from `main` at `a9af24a`. Pull request **#61**.

| File | What it is |
| --- | --- |
| `terminal_game/shell/game.py` | the composition root — `Game`, `GameCollaborator`, `build_game`, `compose_picture`, `main` |
| `terminal_game/__main__.py` | the single command, and nothing but the call |
| `tests/test_game.py` | 29 tests, no window anywhere, the joins only |
| `tools/play_the_game.py` | four bounded exercises against the assembled game |
| `docs/findings/WI-18-the-game-on-screen.md` | what four real windows said |
| `docs/prs/PR-WI-18-the-wiring.md` | the pull request's body |
| `docs/progress/r6-wi-18-the-wiring.md` | the progress log |

Also, and both flagged in the PR: `tools/window_manners.py` and
`tests/test_window_manners.py` lost a duplication (mine, both directions), and
`docs/TRACEABILITY.md` had one citation's path corrected (DEV-C's, and the only line of
another lane's I have touched on this run).

**The game exists**:

```
/usr/bin/python3 -m terminal_game
```

## The suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

**740 passed, 0 failed, 0 skipped** after merging `origin/main` at `7a76772`, which brought
WI-19, WI-20a and amendment 9 in beside this item.

## The screen

**Four windows opened, four reaped, no modal sheet, no orphan.** 0.550 s to 1.488 s, each
ended on its own Tk scheduler well inside its backstop, each reaped in a `finally`, each
acting only on the handle captured at creation. `pgrep` empty afterwards under every tool
name; System Events counted 0 GUI Python processes.

**The real game ran on a real desktop for the first time, and it played**: six real key
presses moved the real player and took the score to 2, `Left` into a wall cost nothing,
`z` did nothing, `q` ended it.

## The two traps, both closed on real Tk

They were WI-17's findings and they became this item's assertions. Then they became
observations.

**A crashed game no longer exits clean.** Every one of WI-17's measurements reproduced —
window reaped, phase Ended, stderr empty, the exception not coming out of `run()`, `error`
null — **and the process exited 1**. Nothing about the failure became visible; the exit
code changed anyway, because `Game.exit_code` reads `session.failure`.

**The close button reaches the session.** Phase `ended`, where WI-17 measured `playing` on
the same route. `Game.start()` rebinds the close request after opening, and
`terminal_game/shell/window_owner.py` — DEV-C's file — is untouched, because the binding is
last-writer-wins.

## What this lane inherits next

**WI-21 (the three questions for a human)** is the last item in this lane and it needs no
new mechanism. `main` already takes `--seconds`, which is what a bounded demo wants, and
`tools/play_the_game.py` is the shape to copy. What it must do that nothing here did:

- **put the finished game in front of a person** and ask A1 (does the titlebar read exactly
  *Terminal Game*), A4 (is the type comfortable) and A2 (did the window land somewhere
  visible) — noting that under **C-7** the answer to A2 on this machine will be the fixed
  fallback, which is expected and should be said before they look;
- **not answer any of them itself.** Five developers have declined to convert
  `title_read_back` into A1 and the advance-width measurement into A10. Do not be the
  sixth who does.

## What is still with the user, and unchanged

- **A1 — the titlebar.** Tk read `Terminal Game` back on all four windows. Not an answer.
- **A10 / SCRN-3 — do the strokes meet.** Untouched, not rounded up.
- **A3 — WIN-5 against END-5 and END-6.** One line in `Session._advance`, unchanged here.
- **A11 — modified arrows.** `KeyPress` carries no modifier state, so control-Up moves the
  player. Ruled a known gap in amendment 9 and deliberately not fixed; `GameCollaborator`
  passes the key through unchanged, so widening the seam later costs nothing here.
- **C-7 — the window opens at its fixed fallback.** Confirmed, and confirmed in the useful
  way: the anchor query **ran and saw nothing** rather than failing or prompting.
