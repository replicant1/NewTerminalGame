# WI-11 — The turn resolver

**Developer:** DEV-A · **Branch:** `r6/wi-11-turn-resolver`
**Base:** `main` — opened stacked on `r6/wi-7-ghost-policy`, retargeted once WI-7 merged
**Depends on:** WI-6 (merged), WI-7 (DEV-B, PR #33, **merged**) · **Iteration:** M2
**Requirements:** GAME-2, CTRL-1, CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3, SCORE-4, END-1, END-2, END-3, END-5

---

## It was stacked, and then it was not

WI-11 depends on WI-7, which was **out of draft but not yet merged** when
this branch had to be cut. DEV-A holds the critical path
(WI-5 → WI-6 → **WI-11** → WI-15 → WI-18 → WI-21), so the conductor's
instruction was to stack rather than idle.

- Cut from `r6/wi-7-ghost-policy` at `c47f1c4`, whose own merge base is
  `edcb5a3` — my WI-6 merge — so the stack already had everything WI-11
  needed, and the PR was opened `--base r6/wi-7-ghost-policy`.
- **WI-7 then merged (PR #33).** This PR was retargeted with
  `gh pr edit 39 --base main` and `origin/main` merged onto the branch,
  cleanly and with no conflict. **There is no merge-order constraint left**;
  it stands on `main` like any other.
- **Nothing here touches DEV-B's files.** `terminal_game/domain/ghost.py`
  and `tests/test_ghost.py` are untouched; the only shared file is
  `terminal_game/domain/game_state.py`, which is mine.

## What this is

One module, `terminal_game/domain/turn_resolver.py`, holding the two things
that can happen in this game. Each is one function, and each **opens with
its own step order written out as a list**:

```python
def resolve_move(state, direction):
    # 1. a wall, or off the grid -> nothing happens at all   (CTRL-3)
    # 2. the player moves, exactly one square                (CTRL-1, CTRL-2)
    # 3. the collision is tested                             (END-1)
    # 4. the dot is eaten, if there is one           (SCORE-1, SCORE-2)
    # 5. the win is tested                                   (END-2)

def resolve_tick(state, random_source):
    # 1. the ghost moves, the way its policy says            (WI-7)
    # 2. the collision is tested            (END-1's second arm)
```

## END-3 is held up by two independent things, and neither is discipline

END-3 — *"eating the last dot on the square the ghost is standing on is a
loss, not a win"* — is correctness living in the order of two statements.
The technical lead flagged it as the one requirement fragile enough that an
ordinary test might not catch a plausible refactor breaking it, and
deliberately imposed no mutation obligation. **None was invented here:
breaking working code to watch a test go red is prohibited and was not
done.** Instead:

**First, the order is in one place and visible**, which is the architect's
caution C6. The collision test sits between the move and the win, in a
five-line function body you can read at a glance.

**Second, an outcome once decided cannot be replaced.** Every ending goes
through one small function:

```python
def _decided(state, outcome):
    if state.outcome.is_decided:
        return state
    return state.with_outcome(outcome)
```

So a win cannot overwrite a collision decided a moment earlier in the same
turn — **even if the two tests were reordered**. That is the part that does
not depend on anyone remembering the rule. The two guards are independent:
one is about sequence, the other about precedence, and END-3 needs only one
of them to survive.

**And the precedence case is asserted directly**, as the plan asks, with the
premise asserted alongside it:

```python
def test_eating_the_last_dot_on_the_ghosts_square_is_a_loss(self):
    self.assertEqual(Outcome.CAUGHT, resolve_move(self.before, EAST).outcome)

def test_the_winning_condition_really_did_hold_in_that_same_turn(self):
    after = resolve_move(self.before, EAST)
    self.assertTrue(after.dots.is_empty)
    self.assertTrue(after.actors_share_a_square)
```

The second test is there because without it the first could pass for the
wrong reason — a dot field that was never actually emptied would make it a
test about something else entirely.

## END-1's two arms

*"whether the player walked into the ghost or the ghost walked into the
player"*. The collision test is the step after the player's move **and** the
step after the ghost's move, and there is a test for each.

## `GameState` gains `ghost_heading`

DEV-B raised this on PR #32: `next_step` returns a heading precisely so it
can be carried to the next tick, and `GameState` had nowhere to carry it, so
GHOST-2's *"keeps going in a straight line"* had no line to remember. They
recommended putting it in `GameState` and, since it is my file, left it to
me.

**Done as they recommended.** `ghost_heading: Optional[Direction] = None`,
with a `with_ghost_heading` wither alongside `with_ghost_at`, keeping the
one-field-per-wither property the rest of `GameState` has. It sits last only
because every field before it has no default. `opening_position` leaves it
`None`, which is DEV-B's "placed but has not moved" case.

## The seam to WI-7, and how it is asserted without a coin flip

The only thing WI-11 owns at that seam is that the heading really is carried
between ticks. What the ghost's policy decides is WI-7's and is not
re-asserted here.

Asserting it needed care. A ghost in a straight corridor carries straight on
without consulting the random source at all; if the resolver *dropped* the
heading, the policy would have to choose, and in a straight corridor a blind
choice goes the right way half the time. So the test hands in a source that
**raises if it is consulted**:

```python
class NeverConsulted:
    def choice(self, sequence):
        raise AssertionError("... the resolver did not carry the heading")
```

The assertions are still on the resulting state — the square and the heading
after each tick. The raising double only turns a coin flip into a
deterministic failure with a message that explains itself. DEV-B's
measurement that the ghost's move is forced on about **95 ticks in 100**
(`docs/findings/WI-7-ghost-roaming.md`) is what makes that the normal case
rather than a contrived one.

## A judgement call needing a ruling

**On the losing turn, the dot is still eaten and still scores.** The plan's
step order is *move, collision, eat, win* — eat comes **after** the
collision rather than instead of it — so a player who walks onto the ghost's
square while it still holds a dot has, on the way, eaten that dot (SCORE-1
says moving onto a square that still has a dot eats it). Only the *ending*
is the collision's.

Measured: with a score of 6 and one dot left on the ghost's square, the
losing move gives **outcome `CAUGHT`, score 7, dots 0**. It is pinned in
`test_the_dot_is_still_eaten_and_still_scores_on_the_losing_turn` so that
changing it has to be deliberate.

The alternative reading — the turn stops dead at the collision, leaving the
last dot uneaten — also satisfies END-3, and the difference is one point on
the `CAUGHT` status line. **If the other reading is wanted, it is one line
in `resolve_move`.**

## What this deliberately does *not* do

- **It does not read a clock.** Whose turn it is and how often is WI-15's.
- **It does not know about keys or intents.** `resolve_move` takes a
  `Direction`, so the Domain never names anything in Presentation; mapping
  WI-9's Move intent to a direction is WI-15's one-line job.
- **It does not compose a picture** and never mentions a colour or a glyph.

## Tests

`tests/test_turn_resolver.py`, 25 tests. Every *"this changes nothing"*
requirement — CTRL-3, END-5 — is asserted as `assertEqual(before, after)` on
the **whole state**, which is what WI-6 made `GameState` a value for: the
square, the score, the dot field, the ghost and the outcome are all covered
at once, and none can be forgotten.

What is deliberately **not** re-asserted here: what the ghost's policy
chooses (WI-7's 40-odd tests own it), what a dot field does when a dot is
taken twice (WI-6's), and what a score refuses to do (WI-6's).

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 349 tests in 3.7s

OK
```

**349 passed, 0 failed, 0 skipped**, with `origin/main` merged in after
WI-7 landed — so WI-1, WI-2, WI-3, WI-4, WI-5, WI-6 and WI-7 are all
present, with WI-11 on top. **25 are WI-11's.**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
