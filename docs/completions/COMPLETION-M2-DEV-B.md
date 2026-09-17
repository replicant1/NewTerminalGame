# Lane B, iteration M2 — completion record

Lane B's M2 is **WI-8**, **WI-10** and **WI-13** — the game state, the only
thing that changes it, and the translation that feeds it. WI-8 arrived from
lane C so that one developer would own both sides of the WI-8/WI-10 seam;
WI-13 was lent to lane C while that pair was in flight and restored when it
landed.

---

## WI-8 — the opening position

| | |
|---|---|
| Branch | `r7/wi-8-opening-position`, cut from `main` at `9863a95` |
| Head of branch | `2543545` |
| Pull request | [#87](https://github.com/replicant1/NewTerminalGame/pull/87) — merged by developer B |
| Merged to `main` as | `3a89d84` |
| PR summary | `docs/prs/PR-WI-8-opening-position.md` |
| Progress log | `docs/progress/r7-wi-8-opening-position.md` |

`terminal_game/domain/state.py` — `Outcome`, `GameState`, `new_game`, and the
two placement functions. START-1 to START-4 and SCORE-5.

**Suite as left: 485 passed, 0 failed, 0 skipped** (49 new).

The two things worth carrying forward:

* **START-1 is swept, not sampled**, because the grid centre `(9, 14)` is a
  lattice connector and is corridor in only 109 of 200 seeds. The sweep also
  asserts that both halves of that coin toss actually occurred, so it cannot
  degrade into a single-seed test wearing a sweep.
* **SCORE-5 is structural.** Of four transitions exactly one touches the
  score, by adding one. No setter, no subtraction, negative scores
  unconstructable.

---

## WI-10 — the turn resolver

| | |
|---|---|
| Branch | `r7/wi-10-turn-resolver`, cut from `main` at `3a89d84` |
| Head of branch | `e163ad4` |
| Pull request | [#89](https://github.com/replicant1/NewTerminalGame/pull/89) — merged by developer B |
| Merged to `main` as | `a2373a9` |
| PR summary | `docs/prs/PR-WI-10-turn-resolver.md` |
| Progress log | `docs/progress/r7-wi-10-turn-resolver.md` |

`terminal_game/application/turn.py` — the first Application-layer module.
CTRL-1/2/3, SCORE-1/2/3, SCORE-4, END-1 on both arms, END-2, END-3, GAME-2,
MAZE-3, and the `Intent` vocabulary.

**Suite as left: 534 passed, 0 failed, 0 skipped** (46 new).

**END-3 is structural rather than sequential**, on the lead's ruling. The
outcome is one total function of the state whose branches are mutually
exclusive by construction; the win branch is *unreachable* while the player
and ghost share a square. Caution C6's failure — the collision test migrating
into the movement code — cannot happen because there is no collision test to
migrate. The plan's section 1.6 fragility note was struck on the strength of
it.

**The coupling that keeps it honest, and it is load-bearing.** A derived
outcome is only as stable as the state it derives from. **WI-11's Decided
state — stop ticking, ignore moves, leave the last picture standing — is what
stops anything re-deriving a different answer.** If the state is ever made
mutable after a decision, END-3 breaks again in a new way.

**One behaviour the ruling settled afterwards:** a player who eats the last
dot on the ghost's square does eat it and does score it, and is still caught.
END-3's own wording decides it — it says *eating*, and SCORE-1 and SCORE-2 are
not conditioned on surviving. `CAUGHT  score N` counts that dot.

---

## WI-13 — input translation

| | |
|---|---|
| Branch | `r7/wi-13-input-translation`, cut from `main` at `a2373a9` |
| PR summary | `docs/prs/PR-WI-13-input-translation.md` |
| Progress log | `docs/progress/r7-wi-13-input-translation.md` |

`terminal_game/presentation/keys.py` — CTRL-1, CTRL-4, CTRL-5. Keysym in,
`Intent` out; `None` for every key that means nothing.

**Suite as left: 627 passed, 0 failed, 0 skipped** (93 new, most of them rows
of the CTRL-5 spread).

`Intent.QUIT` was already in the vocabulary from WI-10, put there so WI-13
would not have to invent a word for quitting. It did not.

---

## What the three together hand to WI-14

* `new_game(maze)` for the opening position.
* `resolve_player_move(state, direction)` and `resolve_ghost_move(state, square)`
  as the only two ways a game changes — the ghost's square comes from WI-9's
  policy, which the resolver never calls.
* `intent_for(event.keysym)` for the keyboard, and the intended wiring is a
  single `<Key>` binding rather than six.
* `outcome_of(state)` if anything needs to ask; the resolvers have already
  applied it.
