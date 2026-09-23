# Completion: M1, lane C (Dev C)

**Work item:** WI-3, Window and character grid. Risk HIGH, human-gated (HIGH; needs eyes on C15 and C16).
**Pull request:** #123, branch `r8/wi-3-window-grid`. **The user merges it. Nobody else does.**
**State when this was written (2026-09-23, 05:02Z):**

- Round 1: `CHANGES_REQUESTED` at `a724d8a`. Both findings were in the brief (a `-k` selector that selected nothing, and a stale base sha). Both fixed in `aae1ea7`.
- Round 2: `APPROVED` at `92d7f5d`, carrying `HUMAN-GATE: WI-3 — HIGH, needs eyes: WI-3/C15, WI-3/C16`.
- AMEND-1 (#128) then reworded WI-3/C7. `origin/main` `b1adc97` is merged in. C7 is copied word for word, and its evidence is extended to the space (257 characters). **Round 3 was requested at `526448b` at 03:54:56Z. No verdict had arrived by 05:01Z.**

## What was built

`terminal_game/shell/` holds the following.

- `window.py`: `GameWindow`. One Tk window titled "Terminal Game", 40 × 30 cells of Menlo at 16 px (400 × 570 points). It paints frames one text item per cell, delivers named keys and a 7 Hz tick scheduled against deadlines, and closes itself however the session ends.
- Pure helpers: `frame.py`, `palette.py`, `typeface.py`, `ticker.py`, `geometry.py`.
- Desktop tests (`tests/test_shell_window_desktop.py`, 17 of them) drive `tests/shell_driver.py` under a pseudo-terminal. They judge screen captures of the real window cell by cell.
- The test card for the human checks is `evidence/WI-3/card.py`.

## Suite as left, at `526448b`

- `.venv/bin/python -m pytest -q` → **416 passed, 1 skipped, 17 deselected**
- `.venv/bin/python -m pytest -q -s -m desktop` → **17 passed, 417 deselected** (about 90 s, about 12 short windows)

## Still open

- Round 3 verdict on #123. After that, the user's C15/C16 look and the merge.
- The *Problem Reporter* crash dialog, and the "reopen windows?" alert that every Python+Tk start shows since one crash of a test driver (brief, F2). Only the user can dismiss them.
- WI-9 (#132, M2) is in verification round 1 at `c7d0884`. It will be recorded in its own M2 completion.
