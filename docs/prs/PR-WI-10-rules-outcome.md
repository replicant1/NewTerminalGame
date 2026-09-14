# WI-10 — the rules and the outcome, as one ordered function

**Branch** `wi-10-rules-outcome`.
**Stacked on `wi-8-player-move` at `62d2bb5`** — a three-deep stack:
`wi-7-game-state` → `wi-8-player-move` → this. WI-10 depends on WI-7 and WI-8
and neither can merge while `main` is frozen. **Read its diff against
`wi-8-player-move`**, not against `main`, or WI-7's and WI-8's changes appear as
its own.
**Lane** A (DEV-A), iteration M1, the last item of M1. **Local mode.**
**Suite** `python3 -m unittest discover` — **371 passed, 0 failed, 0 skipped**.
**Windows opened: none.** Pure domain.

Requirements: **END-1, END-2, END-3, GAME-2**, and **END-5**'s "everything
stops". END-4's draw order is WI-5b's.

## What is new

| File | What it is |
| --- | --- |
| `terminalgame/domain/rules.py` | `outcome_of`, `settle`, `advance_player`, `advance_ghost`. |
| `tests/test_rules.py` | 31 tests. |
| `terminalgame/domain/player.py` | **Changed** — one guard, four lines, plus docstring. |
| `tests/test_player.py` | **Changed** — WI-8's three pinning tests rewritten, one added. |

## The order is the requirement

```python
def outcome_of(state):
    if state.player == state.ghost:     # END-1 — and it is first
        return Outcome.CAUGHT
    if not state.dots:                  # END-2 / GAME-2
        return Outcome.CLEARED
    return Outcome.PLAYING
```

**Reverse those two lines and every end-condition test still passes except
one**: the state where the player and the ghost share a square *and* no dots
remain. Correctly ordered that is a loss; reversed it is a win. That single
state is the whole of the difference between a correct implementation and a
wrong one — which is why it lives in one named function rather than being
spread across whoever calls it.

So it is tested **three ways**, each asserting `CAUGHT` where a reversed
implementation would say `CLEARED`:

1. constructed directly — a state with both conditions true, with each
   condition asserted separately first so the test says out loud that it is the
   *overlap* being tested;
2. reached by a real move — the player eats the last dot **on the ghost's
   square**, which is END-3 in its own words;
3. reached from the other side — the ghost steps onto a player who has just
   cleared the board.

And there is a **control**: clearing the board *away* from the ghost, which must
still be `CLEARED`. Without it, an `outcome_of` that returned `CAUGHT` for
everything would pass the three above.

Every other test in the file passes under either order. That is exactly why
they are not enough on their own, and the file's docstring says so.

**END-3 is reachable only because of a WI-7 decision.** START-3 excepts the
player's starting square and no other, so the ghost begins on a dotted square.
If the ghost's square were cleared at the start, the last dot could never be
underneath it. Both `rules.py` and the END-3 test record that, so the next
person to touch either does not quietly remove the thing that makes the case
possible.

## A trap found while writing `settle`

`outcome_of` is a pure function of where the actors are and how many dots are
left. So **re-running it on a game that has already ended can change the
answer**: a won game whose ghost was afterwards found on the player would read
as a loss, and END-5 forbids that — the ending a game got is the ending it
keeps.

`settle` therefore does not recompute a finished outcome. The test reads such a
state *cold* — asserting `outcome_of` really does say `CAUGHT` — and then shows
`settle` keeps the `CLEARED`. Asserting only the second half would not
distinguish this from a `settle` that never changes anything.

## The outcome gap — I am arguing for the domain, and here is the case

The technical lead leans towards WI-11, and asked for the argument rather than
compliance. **I think it belongs in the domain, and I have implemented it
there.** The case, in the order I find it convincing:

**1. The specification splits exactly where I have split it.** END-5 is phrased
as a property of the game — *"Once a game has ended everything stops: the ghost
stands still, the arrow keys do nothing"*. END-6 is phrased as a property of key
handling — *"`q` still quits, and is the only way to leave a finished game"*. I
have put END-5 in the domain and left END-6 with the loop. The third clause of
END-5, *"the last picture stays on screen"*, is genuinely Presentation's and I
am not claiming it.

**2. The loop cannot simply stop, so "the loop owns it" is not the simpler
arrangement it sounds like.** After the game ends the loop *must* keep running
and keep reading keys, because `q` must still work (END-6). There is no moment
at which it stops calling into the domain. So the rule has to be expressed as a
condition either way — and the question is only where. With the guard in the
domain, the loop's rule is "`q` quits; an arrow calls `advance_player`", and
correctness falls out. With the guard in the loop, it is "`q` quits; an arrow
calls `advance_player` **unless the game is over**".

**3. That extra condition would live in the least testable component in the
system.** The loop needs a terminal; the domain has 371 tests that run in seven
seconds with no terminal at all. Pushing this rule outward moves it from
somewhere it can be tested exhaustively to somewhere it can barely be tested —
and END-5 is not a hard rule to get right, it is a rule that is easy to *forget*,
which is precisely the kind that should not live where testing is expensive.

**4. A guard that a caller can bypass is not a guard.** This is why it is on
`move_player` and not only on `advance_player`. WI-12's verification pack, a
future replay tool, or a test can call the primitive; if the rule lives only in
the loop, each of those can produce a state the requirements say cannot exist,
silently.

**5. It is not the camouflage problem.** The lead's framing of `NotADirection`
was that silence is wrong when it makes a bug byte-identical to correct
behaviour. This is the opposite case: the loop passing an arrow key to a
finished game is not a wiring bug being hidden — the loop is *supposed* to keep
reading keys — and "nothing happens" is the correct answer rather than a
symptom being swallowed.

**6. The ghost half is covered too.** The lead is right that END-5 covers the
ghost, and that is an argument for the domain rather than against it:
`advance_ghost` refuses as well, so both halves of "everything stops" are
enforced in one place. A loop-side guard would need to remember both.

**If overruled, the change is small and I will make it without further
argument**: delete two `if state.is_over` guards and rewrite about eight tests.
It is a cheap decision to reverse, which is part of why I was willing to take a
position rather than hedge.

## The composed steps, and why they exist

`advance_player(state, direction)` and `advance_ghost(state, square, heading)`
are additive — the plan asks for the ordered function, not for these. They exist
because the plan also says *"the order lives in that one function, not in
whoever calls it"*, and "check the outcome after **every** move" is exactly the
kind of thing a caller forgets once and then forgets everywhere.

`advance_ghost` takes the square and heading **already chosen** rather than
calling WI-9's policy. That keeps the ghost's rule and the game's rules apart,
and it means a policy bug shows up in WI-9's tests rather than being masked
here. There is a test asserting this function has no opinion about where the
ghost should go. It also leaves dots and score alone, which is SCORE-4.

## Deviations, for a ruling

1. **`advance_player` / `advance_ghost` are additive**, as above.
2. **The guard on `move_player`** — the disagreement stated in full above. This
   is the one that needs an answer rather than a nod.
3. **`settle` returns the same state object when nothing changed**, following
   the convention WI-8 set for CTRL-3.

## Changes to files this branch did not create

**`terminalgame/domain/player.py`** gained a four-line guard and a docstring
paragraph. **`tests/test_player.py`** had WI-8's `AFinishedGameStillMoves`
class rewritten as `AFinishedGameDoesNotMove`. Those three tests existed to pin
a gap and their own docstrings said to delete them when someone closed it; this
is that. A fourth test was added to the class — *the same press on the same
square while the game is still playing* — because without it the three would
pass against a `move_player` that never moves anything at all.

Both files are mine from WI-8 and neither is touched by DEV-B's WI-9, which is
stacked on `wi-7-game-state` and does not contain them.

## A deliberate omission, recorded so nobody "fixes" it

**`tests/test_layering.py` is not touched, and `rules.py` is deliberately not
added to its module list** — the same decision as WI-8's `player.py`, for the
same reason. `domain_files()` already sweeps every file under
`terminalgame/domain/`, so `rules.py` is covered by the purity, dependency,
screen-geometry and shared-random-generator scans automatically. Listing it as
well would be an adjacent-line edit to the one file DEV-B is also editing for
WI-9. The explicit "the scan really does look at this module" assertion lives in
my own test file instead.

**This absence is a decision, not an oversight. Do not add it.**

## Assumptions

None new. Q1 is adjacent — A1 says the picture freezes at the ending and the
window closes when the player quits — and this item implements the "freezes"
half as a domain fact: once the outcome is decided, nothing moves. Flipping A1
would change when the loop stops, not what `outcome_of` answers.

## Contradictions found

**None.** END-1, END-2, END-3, GAME-2 and END-5 are consistent with each other
and with WI-7's state and WI-8's move, and all are met.

One observation: **END-1's "whether the player walked into the ghost or the
ghost walked into the player" is not a distinction `outcome_of` can make, and
should not be.** It reads a state, and a state does not record how it came
about. The requirement is satisfied by the reading being the same either way,
which is what the two END-1 tests check — one arriving by a player move, one by
a ghost move. Any implementation that *could* tell the difference would be
carrying history it has no reason to have.

## What needs a human

1. **The outcome-gap decision above** — a ruling, and the only thing in this
   item that is not settled by measurement.
2. **Nothing else.** No window was opened; every requirement here is checkable
   without a person looking at a screen.

## Commits

| | |
| --- | --- |
| `b273425` | WI-10: the rules and the outcome, as one ordered function |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
