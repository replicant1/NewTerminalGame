# Completion: M3, Dev B (lane B)

## WI-12: Session control (MEDIUM)

- **PR:** #133, branch `r8/wi-12-session-control`. It was merged by Dev B with `gh pr merge --merge` as `4fcc99b` on 2026-09-23 at about 04:34Z.
- **Verification:** Copilot left one thread and one note in its overview, both fixed in `f960472`. The thread: an unhashable intent raised `TypeError` instead of `ValueError`. The note: the C9 harness had no check with a different script. The verifier `APPROVED` it in round 1 at head `f960472`, with all 13 claims reproduced and no human gate.
- **Claims:** the plan's C1 to C10, plus:
  - A1: the session's intents are WI-6's own.
  - A2: an intent WI-6 could not have produced is refused with `ValueError`.
  - A3: `Session.new(rng)` equals `new_game(generate_maze(rng))`.
- **Built:** `terminal_game/application/session.py` (`Session`, with the phases `PLAYING`, `DECIDED` and `ENDED`), `tests/test_session.py` and `evidence/WI-12/session_transcript.py`.
- **Suite as left**, on landed `main` `4fcc99b`: `.venv/bin/python -m pytest -q` gave 494 passed, 0 failed, 1 skipped.

## The session's interface, for WI-13 (lane C)

`session = Session.new(random.Random())`.

- `on_key(name)` calls `session.handle(translate(name))`.
- `on_tick()` calls `session.tick()`.
- After each event, if `session.ended` the shell calls `window.close()`; otherwise it calls `window.paint(compose(session.state))`.

`docs/prs/PR-WI-12-session-control.md` has the full wiring.
