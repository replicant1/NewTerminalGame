"""Where the ghost goes next — GHOST-2, GHOST-3 and GHOST-4.

> **GHOST-2** The ghost keeps going in a straight line for as long as the
> corridor lets it.
>
> **GHOST-3** Where it cannot carry on, it picks one of the other ways on at
> random, and turns back the way it came only when there is no other choice.
>
> **GHOST-4** The ghost does not hunt the player and takes no notice of where
> they are.

## GHOST-4 is enforced by the signature, not by good behaviour

`choose_heading(maze, square, heading, random_source)` and
`ghost_move(maze, square, heading, random_source)` **do not take the player's
position**. Not "take it and ignore it" — do not take it. A function that
cannot see something cannot take notice of it, which turns GHOST-4 from a
promise into a property of the code that a reader can check in one line.

`move_ghost` is handed a whole `GameState`, which does contain the player, so
it is the one place the guarantee could be lost. It is three lines long and
pulls out exactly the maze, the square and the heading before calling the
policy. The test that matters puts the player on every corridor square of a
maze in turn and checks the ghost's move never changes.

## What "the other ways on" means

At a square, the **ways on** are the four sides that are corridor — MAZE-5
guarantees a corridor square has at least two. Given a heading:

* **ahead** is the way the ghost is already going;
* **back** is the way it came, `heading.opposite()`;
* **the others** are the ways on that are neither.

GHOST-2 says: if ahead is a way on, take it — even where there are side
openings, because the corridor still lets it carry straight on. GHOST-3 says:
otherwise pick at random among the others, and take back only when the others
are empty.

So back is never chosen while anything else is available, which is GHOST-3's
"only when there is no other choice" stated as code rather than as a hope.

## The ghost touches neither dots nor score

`move_ghost` changes `ghost` and `ghost_heading` and nothing else — SCORE-4, "a
dot under the ghost is still there to be taken". It goes through
`GameState.with_changes`, so the state it was handed is not modified at all and
the fields it did not name come across untouched.

It does not set `outcome` either. Whether the move ended the game is WI-10's
question, asked after every move by either actor, and deciding it here would
put the ordered rule of caution C6 in two places.

## The timing is not here

GHOST-1's "about seven times a second" is WI-11's game loop. This module says
*where*, never *when*, and has no clock in it — it could not have one, since
the Domain imports no `time`.
"""

from __future__ import annotations

#: How the ghost behaves when it is somewhere it cannot move from at all.
#: Not reachable through the generator: MAZE-5 gives every corridor square at
#: least two ways on, so a ghost the game placed always has somewhere to go.
#: A maze written out by hand in a test can produce it, and then the ghost
#: stays where it is, keeping its heading.
NOWHERE_TO_GO_MEANS_STAY_PUT = True


def ways_on(maze, square):
    """The directions from `square` that lead onto a corridor square.

    In the maze's own `DIRECTIONS` order — north, south, east, west — so that a
    seeded random source gives the same answer every time. That determinism is
    not cosmetic: it is what lets a failing ghost run be reproduced from a
    seed.
    """
    return [direction for direction, _, _ in maze.open_neighbours(*square)]


def choose_heading(maze, square, heading, random_source):
    """Which way the ghost goes next. **The player is not a parameter.**

    GHOST-2 first: carry straight on if the corridor allows. Then GHOST-3: pick
    at random among the other ways on, and turn back only if there is no other
    choice. If there is nowhere to go at all, keep the current heading — see
    `NOWHERE_TO_GO_MEANS_STAY_PUT`.

    `random_source` is anything with `choice`, normally a `random.Random`. It
    is a required argument rather than a default, so that no caller can get an
    unreproducible ghost by forgetting one.
    """
    available = ways_on(maze, square)
    if not available:
        return heading

    # GHOST-2 — "keeps going in a straight line for as long as the corridor
    # lets it". Note this wins even when there are side openings: a crossroads
    # the ghost can drive straight through is not a place it has to choose.
    if heading in available:
        return heading

    # GHOST-3 — "picks one of the other ways on at random".
    back = heading.opposite()
    others = [direction for direction in available if direction is not back]
    if others:
        return random_source.choice(others)

    # "...and turns back the way it came only when there is no other choice."
    return back


def ghost_move(maze, square, heading, random_source):
    """The ghost's next square and heading. **The player is not a parameter.**

    Returns `(square, heading)`. The square is one step along the new heading
    where that is a corridor square, and unchanged where the ghost had nowhere
    to go — which is the only case in which the ghost does not move.
    """
    new_heading = choose_heading(maze, square, heading, random_source)
    ahead = new_heading.from_square(*square)
    if maze.is_corridor(*ahead):
        return ahead, new_heading
    return tuple(square), new_heading


def move_ghost(state, random_source):
    """A new game state with the ghost moved one square.

    Changes `ghost` and `ghost_heading`. **Nothing else** — not the player, not
    the dots, not the score (SCORE-4), and not the outcome, which is WI-10's to
    decide after a move rather than this module's to guess during one.

    This is the only function here that is handed the player's position at all,
    because it is handed the whole state. It takes the three things the policy
    needs and passes those; see the module docstring on GHOST-4.
    """
    square, heading = ghost_move(state.maze, state.ghost, state.ghost_heading,
                                 random_source)
    return state.with_changes(ghost=square, ghost_heading=heading)
