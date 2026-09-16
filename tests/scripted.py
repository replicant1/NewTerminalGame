# -*- coding: utf-8 -*-
"""WI-19 — the apparatus for playing a whole game headless.

A game is a loop over three calls — ``tick()``, ``move()`` and ``quit()`` —
and this module is what collects the pictures as they go past.

**There is no clock here, and there must not be one** (amendment 5). Under
the adopted architecture control is inverted: the Shell's tick timer drives
the ticking, and a session-owned clock would be a second one that only tests
ever used. A headless game *is* the loop; ``tick()`` is the seam.

**No status-line string is authored here** (A7, as restated by amendment 5).
The prohibition is on *writing* one outside WI-13, not on a frame that
happens to contain one — so an expected picture's row 29 is composed from
WI-13's own function and joined onto the maze rows a test types. A derived
row follows WI-13 if the user ever rules on contradictions C-3 and C-4; a
typed one would not, which is the only property A7 ever had.

Deliberately not named ``test_*``: this is apparatus, not a test case.
"""

from __future__ import annotations

import collections
import random

from terminal_game.application.session import Phase, Session
from terminal_game.domain.dot_field import DotField
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import DIRECTIONS, Maze, Square
from terminal_game.presentation.frame import FRAME_COLUMNS, MAZE_ROWS
from terminal_game.presentation.frame_composer import compose_frame
from terminal_game.presentation.status_line import status_row, status_text


def compose(state):
    """The two lines that bind WI-13's row 29 into WI-12's picture.

    DEV-A specified this shape on PR #45 and WI-15 is written against it;
    it is repeated here rather than invented, so that the headless game and
    the real shell compose the same way.
    """
    return compose_frame(state, status_row(state.score.points, state.outcome))


def expected_picture(maze_rows, score, outcome):
    """An expected frame, as text: rows you typed plus WI-13's row 29.

    *maze_rows* are the maze lines as they should appear, short lines padded
    out.  Row 29 is **composed, never typed** — see the module docstring.
    """
    lines = [row.ljust(FRAME_COLUMNS) for row in maze_rows]
    lines += [" " * FRAME_COLUMNS] * (MAZE_ROWS - len(lines))
    lines.append(status_text(score, outcome).ljust(FRAME_COLUMNS))
    return "\n".join(lines)


def state_over(maze, player, ghost, ghost_heading=None, eaten=()):
    """A game state at a square of your choosing, dots everywhere else."""
    dots = DotField.over_corridors_except(maze, player)
    for square in eaten:
        dots = dots.without_dot_at(square)
    return GameState(
        maze=maze,
        dots=dots,
        player=player,
        ghost=ghost,
        score=Score(),
        outcome=Outcome.UNDECIDED,
        ghost_heading=ghost_heading,
    )


class ScriptedGame:
    """A session driven by a script, with every picture kept.

    It builds no clock and opens no window.  ``shown`` is every frame the
    session asked to be shown, in order, which is what makes a whole game
    assertable as a sequence of pictures.
    """

    def __init__(self, state, seed=0):
        self.shown = []
        self.shut_downs = 0
        #: How many times the session has been asked to take a turn — a
        #: tick or a move. One picture is shown per turn taken while the
        #: game is still playing.
        self.turns = 0
        self.session = Session(
            state,
            compose=compose,
            show=self.shown.append,
            random_source=random.Random(seed),
            shut_down=self._shut_down,
        )
        self.session.start()

    def _shut_down(self):
        self.shut_downs += 1

    # -- the three calls a game is made of --------------------------------

    def tick(self):
        self.turns += 1
        self.session.tick()
        return self

    def move(self, direction):
        self.turns += 1
        self.session.move(direction)
        return self

    def quit(self):
        self.session.quit()
        return self

    def play(self, script):
        """Run a script of ``("tick", None)`` / ``("move", direction)`` pairs."""
        for what, argument in script:
            if what == "tick":
                self.tick()
            elif what == "move":
                self.move(argument)
            elif what == "quit":
                self.quit()
            else:
                raise ValueError("no such move in a script: {0!r}".format(what))
        return self

    # -- what a test reads -------------------------------------------------

    @property
    def picture(self):
        """The last picture shown, as text."""
        return self.shown[-1].to_text()

    @property
    def maze_picture(self):
        """The last picture's maze rows only, as a list of lines."""
        return self.picture.split("\n")[:MAZE_ROWS]

    @property
    def score(self):
        return self.session.state.score.points

    @property
    def outcome(self):
        return self.session.outcome

    @property
    def phase(self):
        return self.session.phase

    @property
    def dots_left(self):
        return self.session.state.dots.remaining


def route_between(maze, start, goal, avoid=()):
    """The shortest corridor route from *start* to *goal*, as directions.

    Breadth-first over the maze's own ``ways_on``, so nothing here knows how
    a maze is built.  Squares in *avoid* are not walked through.  Returns
    ``None`` when there is no route, which is a real answer rather than an
    error: a planner asks about a goal it may not be able to reach.
    """
    if start == goal:
        return []
    avoid = set(avoid) - {goal}
    seen = {start}
    queue = collections.deque([(start, [])])
    while queue:
        square, path = queue.popleft()
        for direction in DIRECTIONS:
            neighbour = maze.ways_on(square).get(direction)
            if neighbour is None or neighbour in seen or neighbour in avoid:
                continue
            if neighbour == goal:
                return path + [direction]
            seen.add(neighbour)
            queue.append((neighbour, path + [direction]))
    return None


def eat_everything(game, tick_every=1, limit=20000):
    """Drive a game toward the nearest dot until it ends or runs out of moves.

    A deliberately simple planner: head for the closest remaining dot by the
    shortest route that does not walk through the ghost, and tick every
    *tick_every* moves.  It is not clever and does not need to be — the
    ghost does not hunt (GHOST-4), so a player that keeps away from the one
    square it occupies will generally clear the maze.

    Returns the number of moves made.  The caller asserts the outcome; this
    just plays.
    """
    moves = 0
    state = game.session.state
    while game.phase is Phase.PLAYING and moves < limit:
        state = game.session.state
        targets = sorted(state.dots.squares(), key=lambda s: (
            abs(s.column - state.player.column) + abs(s.row - state.player.row)
        ))
        route = None
        for target in targets[:8]:
            route = route_between(
                state.maze, state.player, target, avoid={state.ghost}
            )
            if route:
                break
        if not route:
            # Nowhere to go that avoids the ghost; let it move on instead.
            game.tick()
            moves += 1
            continue
        game.move(route[0])
        moves += 1
        # Only tick if that move did not end the game. A tick after the
        # outcome is decided is harmless — the session ignores it — but it
        # is a turn that shows no picture, and a real game loop would not
        # make it either.
        if (
            tick_every
            and moves % tick_every == 0
            and game.phase is Phase.PLAYING
        ):
            game.tick()
    return moves
