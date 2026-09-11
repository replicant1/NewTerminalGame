"""Stand-ins so that the M0 demo actually moves. **WI-9 deletes this file.**

PURE, and deliberately thin. Nothing in here carries a requirement code, and
nothing in here is meant to be right — it exists so the loop in
:mod:`termgame.loop` has something to call through the three seams it owns:

===============  =========================================================
``new_game``     a starting position — **WI-5** lands the real one
``move_player``  a player transition — **WI-6** lands the real one
``move_ghost``   a ghost transition — **WI-7** lands the real one
``render``       a picture — **WI-3** lands the real one, and the loop
                 prefers it the moment ``termgame.view`` exists
===============  =========================================================

The point of shipping stand-ins rather than waiting is that the *seam* is
what WI-4 has to prove, and a seam with nothing on the far side of it proves
nothing. Delete this file in WI-9 and the loop should not notice.

One thing here is **not** arbitrary, because the loop relies on it and so will
the real transitions: a transition is a **no-op once the outcome is not
PLAYING** (END-5). The loop holds no ``if`` about whether the game is over —
it calls the transition either way, and the transition declines. That is what
keeps game logic out of the shell, and WI-6 and WI-7 must honour it.
"""

import random
from typing import FrozenSet

from termgame import maze as mazelib
from termgame.model import (
    MAZE_COLS,
    MAZE_ROWS,
    SCREEN_COLS,
    SCREEN_ROWS,
    Direction,
    Frame,
    FrameBuilder,
    GameState,
    Outcome,
    Position,
)

# --------------------------------------------------------------------------
# Style identifiers
#
# WI-3 owns the real vocabulary; these are the plain names the adapter's
# palette is keyed on. An identifier the palette does not know falls back to
# the default attribute, so a disagreement costs colour and never the picture.
# --------------------------------------------------------------------------

STYLE_WALL = "wall"
STYLE_DOT = "dot"
STYLE_PLAYER = "player"
STYLE_GHOST = "ghost"
STYLE_STATUS = "status"

#: Every style identifier this stand-in can emit.
STYLE_IDS = (STYLE_WALL, STYLE_DOT, STYLE_PLAYER, STYLE_GHOST, STYLE_STATUS)


# --------------------------------------------------------------------------
# A starting position — WI-5 lands the real one
# --------------------------------------------------------------------------


def new_game(rng: random.Random) -> GameState:
    """A playable starting state: a random maze, dots everywhere but underfoot.

    Crude on purpose. WI-5 decides where the player and the ghost really
    start; all this has to do is put them somewhere legal and far enough
    apart to be visible.
    """
    maze = mazelib.generate(rng)
    corridors = sorted(maze.corridors())
    middle = Position(MAZE_ROWS // 2, MAZE_COLS // 2)
    player = min(corridors, key=lambda p: (_squared_distance(p, middle), p))
    ghost = max(corridors, key=lambda p: (_squared_distance(p, player), (-p.row, -p.col)))
    headings = maze.open_directions(ghost)
    heading = headings[rng.randrange(len(headings))]
    dots: FrozenSet[Position] = frozenset(p for p in corridors if p != player)
    return GameState(
        maze=maze,
        player=player,
        ghost=ghost,
        ghost_dir=heading,
        dots=dots,
        score=0,
        outcome=Outcome.PLAYING,
    )


def _squared_distance(a: Position, b: Position) -> int:
    return (a.row - b.row) ** 2 + (a.col - b.col) ** 2


# --------------------------------------------------------------------------
# Transitions — WI-6 and WI-7 land the real ones
# --------------------------------------------------------------------------


def move_player(state: GameState, direction: Direction) -> GameState:
    """Step the player one square if the way is open, eating a dot if there is
    one. Knows nothing about meeting the ghost or clearing the board.

    Returns the state **unchanged** when the game is over (END-5) or when the
    press is towards a wall (CTRL-3).
    """
    if state.outcome is not Outcome.PLAYING:
        return state
    target = state.player.shifted(direction)
    if not state.maze.is_corridor(target):
        return state
    dots = state.dots
    score = state.score
    if target in dots:
        dots = dots - {target}
        score += 1
    return GameState(
        maze=state.maze,
        player=target,
        ghost=state.ghost,
        ghost_dir=state.ghost_dir,
        dots=dots,
        score=score,
        outcome=state.outcome,
    )


def move_ghost(state: GameState, rng: random.Random) -> GameState:
    """Do nothing at all. WI-7 lands the ghost's policy.

    It still takes the ``rng`` it will need, so that WI-9 replaces a function
    with a function and not a call site with a call site.
    """
    return state


# --------------------------------------------------------------------------
# A picture — WI-3 lands the real one
# --------------------------------------------------------------------------

#: The three status strings, indented by one column (assumption A3).
STATUS_TEXT = {
    Outcome.PLAYING: " score %d    arrows, q quits",
    Outcome.CAUGHT: " CAUGHT  score %d   q quits",
    Outcome.CLEARED: " CLEARED  score %d  q quits",
}


def render(state: GameState) -> Frame:
    """A crude 30 x 40 picture of ``state``.

    Not the picture the specification describes — no double-line wall glyphs,
    no three-character entities, no joiner rule. Those are SCRN-3 and SCRN-5
    and they are WI-3's, and drawing a rough version here rather than a
    half-right one keeps the two from being confused. What this does carry is
    the geometry every later picture also has: maze column *c* at screen
    column *2c*, maze row *r* at screen row *r*, the status line on row 29,
    and columns 37-39 blank.
    """
    builder = FrameBuilder(SCREEN_ROWS, SCREEN_COLS)
    maze = state.maze
    for row in range(min(MAZE_ROWS, maze.height)):
        for col in range(min(MAZE_COLS, maze.width)):
            if maze.is_wall((row, col)):
                builder.put(row, 2 * col, "#", STYLE_WALL)
                if col + 1 < maze.width and maze.is_wall((row, col + 1)):
                    builder.put(row, 2 * col + 1, "#", STYLE_WALL)
    for dot in state.dots:
        builder.put(dot.row, 2 * dot.col, ".", STYLE_DOT)
    builder.put(state.player.row, 2 * state.player.col, "@", STYLE_PLAYER)
    builder.put(state.ghost.row, 2 * state.ghost.col, "G", STYLE_GHOST)
    builder.put_text(
        SCREEN_ROWS - 1, 0, status_line(state), STYLE_STATUS
    )
    return builder.build()


def status_line(state: GameState, width: int = SCREEN_COLS) -> str:
    """The bottom row's text, padded to ``width`` and never longer."""
    text = STATUS_TEXT[state.outcome] % state.score
    return text[:width].ljust(width)
