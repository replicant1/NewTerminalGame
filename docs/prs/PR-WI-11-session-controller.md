# WI-11 — the session controller

**Branch:** `r7/wi-11-session-controller`, cut from the tip of `main` at `a2373a9`. Not
stacked.

| File | |
|---|---|
| `terminal_game/application/session.py` | `Session`, `Phase`, `INITIAL_GHOST_HEADING`. |
| `tests/test_session.py` | 26 tests. |
| `docs/progress/r7-wi-11-session-controller.md` | |
| `docs/progress/r7-wi-4b-frame-field-seam.md` | *(modified)* WI-4b's tail, carried forward. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**560 passed, 0 failed, 0 skipped**, nothing deselected. 534 before; WI-11 adds 26.

---

## Decided is what keeps WI-10's outcome honest

Stating the coupling here as the lead asked, because it is now the most important thing
about this item.

WI-10 made END-3 **structural**: the outcome is one total function of the board, so *"eating
the last dot on the ghost's square is a loss, not a win"* is true by the shape of an
expression rather than by the order of two statements. **A derived outcome is only stable
while the state is.** Decided is what keeps the state still — so if anything ever makes the
board mutable after a decision, END-3 breaks again in a new way, and it breaks **here**
rather than in the resolver.

That is why the END-5 assertions in this file are that a decided board is **unchanged**,
not merely that the session declines to act on it. `test_a_decided_game_is_unchanged_not_merely_ignored`
throws ten ticks and thirty arrows at a decided game and requires the board, the score, the
dots and the outcome all to be identical afterwards.

## The design question the tests found, and how it was settled

A test failed, and **the code was wrong rather than the test.**

`GameState.outcome` is a **field the resolver stamps**; `turn.outcome_of` is the **derived
total function**. A board built by hand can have the player and the ghost on the same square
and still carry `UNDECIDED`. My first draft read the field — which would have let such a
board be **playable**, and since Decided is what holds END-3 up, that is precisely the crack
it exists to keep shut.

**Settled: the session asks `outcome_of` and never reads the field.** One source of truth,
which is what structural END-3 means. The consequence runs both ways and both are pinned:

- a board that is over **by the rules** but unstamped starts in **Decided**;
- a board **stamped** `CAUGHT` whose actors are a square apart starts in **Playing**,
  because the rules are authoritative and the stamp is a cache of them. Saying otherwise
  would put back the second source of truth that structural END-3 removed.

In production the two can never disagree — the resolver always stamps what `outcome_of`
returned. This only bites on hand-built boards, which is to say on fixtures, WI-16's
journeys, and any resumed state.

## Every "nothing happened" test has a control

Applying the generalisation the lead drew from lane B. A test that a tick moves nothing in
Decided is **worthless** unless the identical tick, on the identical board, visibly moves
the ghost in Playing — otherwise it might be passing because the tick is inert everywhere,
or because the ghost was boxed in. So:

| The assertion | Its control |
|---|---|
| in Decided a tick moves nothing | `test_a_tick_moves_the_ghost_while_playing` |
| in Decided an arrow changes nothing | `test_an_arrow_moves_the_player_while_playing` — west is a legal move on that very board |
| a finished board starts in Decided | `test_a_playable_board_is_not_mistaken_for_a_finished_one` |

The controls are not duplicates. They are what makes the assertions mean anything.

## The rest of the bar

- **START-5** — a session is Playing the moment it exists, and a tick works before anything
  is pressed. Plus an architecture guard: no method whose name contains *start*, *begin*,
  *restart*, *reset*, *pause*, *resume*, *life*, *level* or *timer*.
- **GAME-3** — exactly three phases, and `test_nothing_ever_returns_a_session_to_playing`
  drives every intent, a tick and a quit against a session in each of the three phases and
  requires Playing never to be re-entered. That is "no restart edge" as a fact about
  transitions rather than about naming.
- **END-6 / CTRL-4** — quit accepted in Playing and in Decided; in Decided nothing else is.
- **WIN-5 under P1** — **a decided session is still running.** Deciding an outcome does not
  end it; the last picture stays up until `q`. If that were false the window would vanish at
  the moment of the decision, which is the reading the plan proceeds *against*
  (contradiction C-1).

## Decisions taken (section 1.8 — reported, not asking)

**The session owns the ghost's heading.** Nobody claimed it — I flagged it as unclaimed in
WI-9's PR — and the session is the natural owner because it is the thing that persists
between ticks. `INITIAL_GHOST_HEADING = EAST` is **arbitrary** — nothing in the
specification chooses — but fixed, and pinned by a test, because WI-16's seeded playthroughs
must reproduce.

**A tick moves the ghost**, by calling WI-9's policy. It has to: if a tick did nothing,
END-5's *"a tick moves nothing"* would be untestable. The beat still *arrives as a call* —
this module names no clock and no timer, and the 143 ms is WI-14's.

**Additive: `on_end`.** WIN-5 has to reach the window, and Application may name neither
`sys` nor a toolkit. So reaching Ended sets `is_running` false and calls an optional
callback the Shell supplies. `quit()` is idempotent and the callback fires once — the Shell
may well hear about a quit twice, a key and a closing window, and neither should have to
know whether the other got there first.

**Identity guard**, per the section 7 rule: `session.Outcome is state.Outcome` and
`session.Intent is turn.Intent`. Two modules that must agree on a type is exactly where
things drift apart, and behaviour tests on both halves pass throughout.

## Window hygiene

Pure Application: no toolkit, no clock, no process, no `ctypes`, no window. The layer-rule
checker passes. No code was broken to watch a test go red — the one failure in this item was
a real defect in my own module, found by a test, and fixed in the module.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
