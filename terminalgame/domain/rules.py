"""How a game ends: one ordered function, and the steps that call it.

END-1, END-2, END-3 and GAME-2. END-4 — the ghost drawn over the player on a
loss — is a drawing order and belongs to Presentation (WI-5b), not here.

## The order is the requirement

:func:`outcome_of` asks two questions in a fixed order, and **the order is not
an implementation detail, it is END-3**:

1. are the player and the ghost on the same square? Then the game is lost.
2. otherwise, are there no dots left? Then it is won.

Reverse those two lines and every end-condition test still passes except one:
the state where the player has just eaten the last dot **on the square the
ghost is standing on**. Correctly ordered that is a loss; reversed it is a win.
That single state is the whole of the difference between a correct
implementation and a wrong one, which is why it lives in one named function
rather than being spread across whoever calls it, and why the tests hit it both
directly and through a real move.

It is reachable at all only because of a decision made in WI-7: **START-3
excepts the player's starting square and no other, so the ghost begins on a
square that holds a dot.** If the ghost's square were cleared at the start, the
last dot could never be underneath it and END-3 would be unreachable.

## Once a game has ended, it has ended

END-5: *"Once a game has ended everything stops: the ghost stands still, the
arrow keys do nothing, and the last picture stays on screen."*

That is a statement about the game rather than about key handling, so it is
enforced here and in :func:`~terminalgame.domain.player.move_player` rather
than being left to the loop. Two consequences worth stating:

* :func:`advance_player` and :func:`advance_ghost` both refuse to move anything
  once the outcome is decided, and return the state they were given.
* :func:`settle` does **not** recompute a finished outcome. It cannot be
  allowed to: `outcome_of` is a pure function of where the actors are and how
  many dots are left, so re-running it on a won game whose ghost had since
  been placed on the player would read that game as lost. A game that has
  ended keeps the ending it got.

END-6 — *"`q` still quits, and is the only way to leave a finished game"* — is
about which keys do what, and stays with the loop (WI-11) alongside CTRL-4 and
CTRL-5.
"""

from __future__ import annotations

from terminalgame.domain.game_state import Outcome
from terminalgame.domain.player import move_player


def outcome_of(state):
    """How the game stands, decided in the one order END-3 requires.

    A pure reading of the state: it changes nothing and does not care how the
    state came to look like this — "whoever walked into whom" (END-1) is not a
    question it can ask and does not need to.
    """
    # END-1, and it is first. END-3 is the statement that this line comes
    # before the next one.
    if state.player == state.ghost:
        return Outcome.CAUGHT
    # END-2 / GAME-2.
    if not state.dots:
        return Outcome.CLEARED
    return Outcome.PLAYING


def settle(state):
    """The state with its outcome brought up to date.

    A finished game is returned untouched — see the module docstring: END-5
    means the ending a game got is the ending it keeps, and recomputing it
    could turn a win into a loss.
    """
    if state.is_over:
        return state
    outcome = outcome_of(state)
    if outcome == state.outcome:
        return state
    return state.with_changes(outcome=outcome)


def advance_player(state, direction):
    """One key press: move the player, then read the outcome.

    The unit the loop calls, so that "check after every move" is not something
    a caller has to remember. Returns the state it was given if the game is
    already over (END-5) or the way is wall (CTRL-3).
    """
    if state.is_over:
        return state
    return settle(move_player(state, direction))


def advance_ghost(state, square, heading):
    """One ghost step: put the ghost where its policy chose, then read the
    outcome.

    Takes the square and heading already decided rather than calling the
    policy, so that the ghost's rule (WI-9) and the game's rules stay separate
    — this function has no opinion about where the ghost should go, only about
    what it means once it is there.

    The ghost neither eats dots nor hides them (SCORE-4), so nothing about the
    dots or the score changes here. Returns the state it was given if the game
    is already over: END-5's "the ghost stands still".

    It also avoids building a new state when the ghost was told to stay where
    it is — which happens when it has nowhere to go. `with_changes` builds a
    new object whatever it is handed, so without this a ghost standing still
    would look like a change to everything downstream, and the loop, which
    detects change by identity, would redraw a picture identical to the one
    already on the screen.

    Note the exact claim, because it is one step weaker than "returns the same
    object". This returns `settle(state)`, and `settle` returns a NEW state
    when the outcome has moved on — a stationary ghost that the player has
    just walked into comes back as a fresh `CAUGHT` state, and must, or the
    ending would never be recorded. So the Domain's convention is *nothing
    changed means nothing new*, not *this call never allocates*. The loop's
    redraw is correct either way: a changed outcome is a change worth drawing.
    """
    if state.is_over:
        return state
    square = tuple(square)
    if square == state.ghost and heading == state.ghost_heading:
        return settle(state)
    return settle(state.with_changes(ghost=square, ghost_heading=heading))
