"""The player's move — CTRL-1..3, SCORE-1..3, SCORE-5, END-1..3, END-5, GAME-2.

The work of :func:`termgame.rules.move_player`.

**Every board in this file is hand-written and small enough to check by eye**,
as the implementation plan requires. They are written as pictures:

======  ===================================================================
``#``   wall
(space) corridor with no dot
``.``   corridor with a dot
``P``   the player, on a square with no dot
``G``   the ghost, on a square with no dot
``*``   the ghost, standing on a dot — the square END-3 is about
======  ===================================================================

So this board

::

    ####
    #P*#
    ####

is four squares wide and three deep, the player is at ``(1, 1)``, the ghost at
``(1, 2)``, and the only dot in the game is the one under the ghost.

:func:`board` turns a picture into a :class:`~termgame.model.GameState` and
nothing more; it does no arithmetic the tests then lean on. Where a board
matters — the END-3 one especially — the test also asserts the player, the
ghost, the dots and the score in literal coordinates *before* it moves
anything, so a mistake in the helper cannot quietly make a test pass.

Nothing here re-derives the answer with the expression the code uses: the
expected square, the expected score and the expected outcome are written out
as literals a reader can check against the picture.
"""

import unittest

from termgame import maze as mazelib
from termgame import rules
from termgame.model import (
    DIRECTIONS,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    GAME_STATE_FIELDS,
    GameState,
    Outcome,
    Position,
)


# --------------------------------------------------------------------------
# Boards
# --------------------------------------------------------------------------

WALL_CHAR = "#"
EMPTY_CHAR = " "
DOT_CHAR = "."
PLAYER_CHAR = "P"
GHOST_CHAR = "G"
GHOST_ON_DOT_CHAR = "*"


def board(picture, score=0, outcome=Outcome.PLAYING, ghost_dir=None):
    """A :class:`GameState` from a picture. See this module's docstring.

    Deliberately dumb: it walks the picture character by character and places
    what it finds. It computes no distances, chooses no squares and knows
    nothing about the rules of the game.
    """
    lines = [line for line in picture.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    player = None
    ghost = None
    dots = []
    grid_rows = []
    for row, line in enumerate(lines):
        grid = []
        for col, char in enumerate(line):
            here = Position(row, col)
            if char == WALL_CHAR:
                grid.append("#")
                continue
            grid.append(".")
            if char == PLAYER_CHAR:
                player = here
            elif char == GHOST_CHAR:
                ghost = here
            elif char == GHOST_ON_DOT_CHAR:
                ghost = here
                dots.append(here)
            elif char == DOT_CHAR:
                dots.append(here)
            elif char != EMPTY_CHAR:
                raise ValueError("%r is not a board character" % (char,))
        grid_rows.append("".join(grid))

    if player is None:
        raise ValueError("the board has no player")
    if ghost is None:
        raise ValueError("the board has no ghost")

    maze = mazelib.from_text("\n".join(grid_rows))
    if ghost_dir is None:
        open_ways = maze.open_directions(ghost)
        ghost_dir = open_ways[0] if open_ways else UP
    return GameState(
        maze=maze,
        player=player,
        ghost=ghost,
        ghost_dir=ghost_dir,
        dots=frozenset(dots),
        score=score,
        outcome=outcome,
    )


#: A plus with a tail. The player stands in the middle with all four ways
#: open; the ghost is off in the tail, out of reach of a single move.
#:
#: ::
#:
#:     ######
#:     ##.###
#:     #.P..#
#:     ##.#G#
#:     ######
#:
#: Player ``(2, 2)``; ghost ``(3, 4)``; dots ``(1, 2) (2, 1) (2, 3) (2, 4)
#: (3, 2)`` — five of them, so no single move can clear the board.
PLUS = """
######
##.###
#.P..#
##.#G#
######
"""

#: A ring with an alcove, for walking a lap and then walking it again.
#:
#: ::
#:
#:     ######
#:     #P..##
#:     #.#..#
#:     #...G#
#:     ######
#:
#: Player ``(1, 1)``; ghost ``(3, 4)``; eight dots. The lap
#: right-right-down-down-left-left-up-up eats seven of them and comes home;
#: the dot at ``(2, 4)`` is never reached, so the board never clears.
RING = """
######
#P..##
#.#..#
#...G#
######
"""


# --------------------------------------------------------------------------
# The board helper itself
# --------------------------------------------------------------------------


class TheBoardHelper(unittest.TestCase):
    """The pictures really do say what the docstring claims they say."""

    def test_the_plus_board_is_the_board_the_comment_describes(self):
        state = board(PLUS)
        self.assertEqual(Position(2, 2), state.player)
        self.assertEqual(Position(3, 4), state.ghost)
        self.assertEqual(
            {
                Position(1, 2),
                Position(2, 1),
                Position(2, 3),
                Position(2, 4),
                Position(3, 2),
            },
            set(state.dots),
        )
        self.assertEqual(0, state.score)
        self.assertIs(Outcome.PLAYING, state.outcome)
        self.assertTrue(state.maze.is_corridor((2, 2)))
        self.assertTrue(state.maze.is_wall((0, 0)))
        self.assertTrue(state.maze.is_wall((3, 3)))

    def test_a_ghost_standing_on_a_dot_keeps_the_dot(self):
        state = board(
            """
            ####
            #P*#
            ####
            """.replace("            ", "")
        )
        self.assertEqual(Position(1, 2), state.ghost)
        self.assertEqual(frozenset([Position(1, 2)]), state.dots)

    def test_a_board_with_no_player_is_rejected(self):
        with self.assertRaises(ValueError):
            board("####\n#.G#\n####")

    def test_a_board_with_no_ghost_is_rejected(self):
        with self.assertRaises(ValueError):
            board("####\n#.P#\n####")


# --------------------------------------------------------------------------
# The move itself — CTRL-1, CTRL-2
# --------------------------------------------------------------------------


class TheMoveItself(unittest.TestCase):
    """One press, one square, in the direction pressed."""

    def test_each_of_the_four_directions_moves_the_player_that_one_square(self):
        """CTRL-1: up, down, left and right each move one square that way."""
        expected = {
            UP: Position(1, 2),
            DOWN: Position(3, 2),
            LEFT: Position(2, 1),
            RIGHT: Position(2, 3),
        }
        for direction in DIRECTIONS:
            state = board(PLUS)
            moved = rules.move_player(state, direction)
            self.assertEqual(
                expected[direction],
                moved.player,
                "%s from (2, 2) should land on %s"
                % (direction.name, expected[direction]),
            )

    def test_a_press_moves_exactly_one_square_and_no_further(self):
        """CTRL-2: one square per press, and then it stops."""
        state = board("#######\n#P....#\n#####G#")
        self.assertEqual(Position(1, 1), state.player)

        first = rules.move_player(state, RIGHT)
        self.assertEqual(Position(1, 2), first.player)

        second = rules.move_player(first, RIGHT)
        self.assertEqual(Position(1, 3), second.player)

        third = rules.move_player(second, RIGHT)
        self.assertEqual(Position(1, 4), third.player)

    def test_five_presses_along_a_five_square_corridor_land_on_the_fifth(self):
        """Nothing accumulates across presses: five presses, five squares."""
        state = board("#######\n#P....#\n#####G#")
        for _ in range(4):
            state = rules.move_player(state, RIGHT)
        self.assertEqual(Position(1, 5), state.player)

        # The sixth press is into the end wall and changes nothing.
        self.assertIs(state, rules.move_player(state, RIGHT))

    def test_a_move_does_not_disturb_the_ghost_or_its_heading(self):
        state = board(PLUS)
        moved = rules.move_player(state, UP)
        self.assertEqual(Position(3, 4), moved.ghost)
        self.assertIs(state.ghost_dir, moved.ghost_dir)
        self.assertIs(state.maze, moved.maze)

    def test_the_state_moved_from_is_not_changed_by_the_move(self):
        """The transition is pure: the state handed in comes out untouched."""
        state = board(PLUS)
        before = {name: getattr(state, name) for name in GAME_STATE_FIELDS}

        rules.move_player(state, UP)

        for name in GAME_STATE_FIELDS:
            self.assertEqual(
                before[name], getattr(state, name), "%s was mutated" % name
            )

    def test_the_same_state_and_direction_always_give_the_same_answer(self):
        state = board(PLUS)
        self.assertEqual(
            rules.move_player(state, RIGHT), rules.move_player(state, RIGHT)
        )

    def test_from_every_square_of_a_board_a_press_stays_or_steps_one_square(self):
        """Totality: every square, every direction, always a legal answer."""
        picture = board(RING)
        for square in sorted(picture.maze.corridors()):
            if square == picture.ghost:
                continue
            here = GameState(
                maze=picture.maze,
                player=square,
                ghost=picture.ghost,
                ghost_dir=picture.ghost_dir,
                dots=picture.dots,
                score=0,
                outcome=Outcome.PLAYING,
            )
            for direction in DIRECTIONS:
                moved = rules.move_player(here, direction)
                self.assertIsInstance(moved, GameState)
                steps = abs(moved.player.row - square.row) + abs(
                    moved.player.col - square.col
                )
                self.assertIn(
                    steps,
                    (0, 1),
                    "%s from %s moved %d squares" % (direction.name, square, steps),
                )
                if steps == 1:
                    self.assertTrue(picture.maze.is_corridor(moved.player))


# --------------------------------------------------------------------------
# A press towards a wall — CTRL-3
# --------------------------------------------------------------------------


class APressTowardsAWall(unittest.TestCase):
    """CTRL-3: a press towards a wall does nothing at all."""

    def test_a_press_towards_a_wall_gives_back_the_very_same_state(self):
        """Not an equal copy — the identical object. "Nothing at all"."""
        state = board(PLUS)
        # The player's own square has all four ways open, so step down into
        # the stub at (3, 2), where both LEFT and RIGHT are wall.
        at_the_bottom = rules.move_player(state, DOWN)
        self.assertEqual(Position(3, 2), at_the_bottom.player)
        self.assertTrue(at_the_bottom.maze.is_wall((3, 1)))
        self.assertTrue(at_the_bottom.maze.is_wall((3, 3)))

        self.assertIs(at_the_bottom, rules.move_player(at_the_bottom, LEFT))
        self.assertIs(at_the_bottom, rules.move_player(at_the_bottom, RIGHT))

    def test_a_press_towards_a_wall_changes_no_field_of_the_state(self):
        state = board(RING)
        self.assertTrue(state.maze.is_wall((0, 1)))  # straight up from (1, 1)

        after = rules.move_player(state, UP)

        for name in GAME_STATE_FIELDS:
            self.assertEqual(
                getattr(state, name),
                getattr(after, name),
                "%s changed on a press towards a wall" % name,
            )

    def test_a_press_towards_a_wall_does_not_touch_the_score(self):
        """Explicitly, because a scoring wall press is the plausible bug."""
        state = board(RING, score=4)
        after = rules.move_player(state, UP)
        self.assertEqual(4, after.score)
        self.assertEqual(state.dots, after.dots)

    def test_a_press_off_the_edge_of_the_grid_does_nothing_either(self):
        """The corridor runs to the border; up and left leave the grid."""
        state = board("P.\n.G")
        self.assertEqual(Position(0, 0), state.player)
        self.assertFalse(state.maze.contains((-1, 0)))

        self.assertIs(state, rules.move_player(state, UP))
        self.assertIs(state, rules.move_player(state, LEFT))
        # And the two directions that stay on the grid still work, so the
        # board is not simply inert.
        self.assertEqual(Position(0, 1), rules.move_player(state, RIGHT).player)
        self.assertEqual(Position(1, 0), rules.move_player(state, DOWN).player)

    def test_a_wall_press_between_two_real_moves_loses_nothing(self):
        state = board(RING)
        state = rules.move_player(state, RIGHT)     # (1, 2), eats a dot
        blocked = rules.move_player(state, UP)      # wall
        self.assertIs(state, blocked)
        state = rules.move_player(blocked, RIGHT)   # (1, 3), eats a dot
        self.assertEqual(Position(1, 3), state.player)
        self.assertEqual(2, state.score)


# --------------------------------------------------------------------------
# Dots and the score — SCORE-1, SCORE-2, SCORE-3, SCORE-5
# --------------------------------------------------------------------------


class DotsAndTheScore(unittest.TestCase):

    def test_moving_onto_a_dot_eats_it_and_scores_exactly_one(self):
        """SCORE-1 and SCORE-2."""
        state = board(PLUS)
        self.assertIn(Position(2, 3), state.dots)
        self.assertEqual(0, state.score)

        moved = rules.move_player(state, RIGHT)

        self.assertEqual(Position(2, 3), moved.player)
        self.assertNotIn(Position(2, 3), moved.dots)
        self.assertEqual(1, moved.score)
        self.assertEqual(len(state.dots) - 1, len(moved.dots))

    def test_the_other_dots_are_left_exactly_where_they_were(self):
        state = board(PLUS)
        moved = rules.move_player(state, RIGHT)
        self.assertEqual(
            {
                Position(1, 2),
                Position(2, 1),
                Position(2, 4),
                Position(3, 2),
            },
            set(moved.dots),
        )

    def test_the_eaten_dot_is_gone_for_the_rest_of_the_game(self):
        """SCORE-1: the dot disappears from the maze, not just from view."""
        state = board(PLUS)
        eaten = rules.move_player(state, RIGHT)     # onto (2, 3)
        away = rules.move_player(eaten, RIGHT)      # onto (2, 4), another dot
        self.assertEqual(2, away.score)

        back = rules.move_player(away, LEFT)        # back onto (2, 3)

        self.assertEqual(Position(2, 3), back.player)
        self.assertNotIn(Position(2, 3), back.dots)

    def test_moving_back_onto_an_eaten_square_adds_nothing(self):
        """SCORE-3."""
        state = board(PLUS)
        eaten = rules.move_player(state, RIGHT)     # (2, 3), score 1
        away = rules.move_player(eaten, LEFT)       # back to (2, 2), empty
        self.assertEqual(1, away.score)

        back = rules.move_player(away, RIGHT)       # (2, 3) again, no dot now

        self.assertEqual(Position(2, 3), back.player)
        self.assertEqual(1, back.score)

    def test_moving_onto_a_square_that_never_had_a_dot_scores_nothing(self):
        state = board("######\n#P G.#\n######")
        self.assertNotIn(Position(1, 2), state.dots)

        moved = rules.move_player(state, RIGHT)

        self.assertEqual(Position(1, 2), moved.player)
        self.assertEqual(0, moved.score)
        self.assertEqual(state.dots, moved.dots)

    def test_the_score_is_the_count_of_dots_eaten_over_a_whole_lap(self):
        """Seven dots on the lap, seven points, and the eighth left behind."""
        lap = (RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, UP, UP)
        state = board(RING)
        self.assertEqual(8, len(state.dots))

        for direction in lap:
            state = rules.move_player(state, direction)

        self.assertEqual(Position(1, 1), state.player)
        self.assertEqual(7, state.score)
        self.assertEqual(frozenset([Position(2, 4)]), state.dots)
        self.assertIs(Outcome.PLAYING, state.outcome)

    def test_the_score_never_goes_down_at_any_step_of_a_scripted_run(self):
        """SCORE-5, over a lap, a wall press, and a second lap that scores
        nothing at all because every dot on it has already gone."""
        lap = (RIGHT, RIGHT, DOWN, DOWN, LEFT, LEFT, UP, UP)
        script = lap + (UP, LEFT) + lap
        state = board(RING)

        scores = [state.score]
        for direction in script:
            state = rules.move_player(state, direction)
            scores.append(state.score)

        for step in range(1, len(scores)):
            self.assertGreaterEqual(
                scores[step],
                scores[step - 1],
                "the score fell at step %d of the run: %r" % (step, scores),
            )
        self.assertEqual(0, scores[0])
        self.assertEqual(7, scores[8], "the first lap should eat seven dots")
        self.assertEqual(7, scores[-1], "the second lap should score nothing")
        self.assertEqual(Position(1, 1), state.player)


# --------------------------------------------------------------------------
# How a game ends — END-1, END-2, GAME-2
# --------------------------------------------------------------------------


class HowAGameEnds(unittest.TestCase):

    def test_a_move_that_ends_nothing_leaves_the_game_playing(self):
        state = board(PLUS)
        moved = rules.move_player(state, UP)
        self.assertIs(Outcome.PLAYING, moved.outcome)

    def test_walking_onto_the_ghosts_square_loses_the_game(self):
        """END-1, the player's half: the player walked into the ghost.

        ::

            ######
            #P G.#
            ######

        There is still a dot at ``(1, 4)``, so nothing here could be mistaken
        for the board having been cleared.
        """
        state = board("######\n#P G.#\n######")
        self.assertEqual(Position(1, 3), state.ghost)
        self.assertEqual(frozenset([Position(1, 4)]), state.dots)

        step = rules.move_player(state, RIGHT)       # (1, 2), still playing
        self.assertIs(Outcome.PLAYING, step.outcome)

        caught = rules.move_player(step, RIGHT)      # (1, 3) — the ghost

        self.assertIs(Outcome.CAUGHT, caught.outcome)
        self.assertEqual(Position(1, 3), caught.player)
        self.assertEqual(Position(1, 3), caught.ghost)
        self.assertEqual(0, caught.score)
        self.assertEqual(frozenset([Position(1, 4)]), caught.dots)

    def test_eating_the_last_dot_on_an_empty_square_wins_the_game(self):
        """END-2.

        ::

            #####
            #P.G#
            #####

        One dot left, at ``(1, 2)``, and the ghost is at ``(1, 3)`` — next to
        the dot but not on it.
        """
        state = board("#####\n#P.G#\n#####")
        self.assertEqual(frozenset([Position(1, 2)]), state.dots)
        self.assertEqual(Position(1, 3), state.ghost)

        won = rules.move_player(state, RIGHT)

        self.assertIs(Outcome.CLEARED, won.outcome)
        self.assertEqual(Position(1, 2), won.player)
        self.assertEqual(1, won.score)
        self.assertEqual(frozenset(), won.dots)

    def test_the_last_dot_is_only_the_last_when_the_board_is_really_empty(self):
        """Two dots left: eating one of them wins nothing."""
        state = board("######\n#P..G#\n######")
        self.assertEqual(2, len(state.dots))

        moved = rules.move_player(state, RIGHT)

        self.assertIs(Outcome.PLAYING, moved.outcome)
        self.assertEqual(1, moved.score)
        self.assertEqual(frozenset([Position(1, 3)]), moved.dots)

    def test_the_game_is_won_by_eating_every_dot_and_lost_by_meeting_the_ghost(self):
        """GAME-2: both outcomes, off the one board, by two different routes.

        ::

            ######
            #.P.G#
            ######

        Going left eats the last-but-one dot and then the last one, and wins.
        Going right eats a dot and then walks into the ghost, and loses.
        """
        start = board("######\n#.P.G#\n######")
        self.assertEqual(
            {Position(1, 1), Position(1, 3)}, set(start.dots)
        )

        winning = rules.move_player(start, LEFT)         # (1, 1), one dot left
        self.assertIs(Outcome.PLAYING, winning.outcome)
        winning = rules.move_player(winning, RIGHT)      # (1, 2), empty square
        self.assertIs(Outcome.PLAYING, winning.outcome)
        winning = rules.move_player(winning, RIGHT)      # (1, 3), the last dot
        self.assertIs(Outcome.CLEARED, winning.outcome)
        self.assertEqual(2, winning.score)

        losing = rules.move_player(start, RIGHT)         # (1, 3), eats a dot
        self.assertIs(Outcome.PLAYING, losing.outcome)
        losing = rules.move_player(losing, RIGHT)        # (1, 4), the ghost
        self.assertIs(Outcome.CAUGHT, losing.outcome)
        self.assertEqual(1, losing.score)


# --------------------------------------------------------------------------
# END-3 — the order of two branches
# --------------------------------------------------------------------------


class EndThreeTheOrderOfTwoBranches(unittest.TestCase):
    """END-3, the requirement flagged in the implementation plan (§2.7) as
    the fragile one.

        *"Eating the last dot on the square the ghost is standing on is a
        loss, not a win: meeting the ghost is decided first."*

    The whole of END-3 lives in the order of two branches in
    :func:`termgame.rules.move_player`: the ghost test is an ``if`` and the
    cleared-board test is the ``elif`` after it. Swap them and this one board
    starts reporting a win, every other test in this file still passes, and
    the position is rare enough that nobody would find it by playing.

    **Do not delete or rename the test below.** It is the only thing in the
    suite that puts both conditions true at once.
    """

    #: One dot left in the whole game, and the ghost is standing on it. The
    #: player is one square to its left.
    #:
    #: ::
    #:
    #:     ####
    #:     #P*#
    #:     ####
    BOARD = "####\n#P*#\n####"

    def test_END_3_eating_the_last_dot_on_the_ghosts_square_is_a_loss_not_a_win(self):
        state = board(self.BOARD)

        # The board is the one END-3 describes, asserted in literal
        # coordinates rather than taken on the helper's word.
        self.assertEqual(Position(1, 1), state.player)
        self.assertEqual(Position(1, 2), state.ghost)
        self.assertEqual(frozenset([Position(1, 2)]), state.dots)
        self.assertEqual(1, len(state.dots), "exactly one dot must be left")
        self.assertEqual(0, state.score)
        self.assertIs(Outcome.PLAYING, state.outcome)

        after = rules.move_player(state, RIGHT)

        # The dot was eaten and the board is now empty, so the winning
        # condition genuinely holds: this is not a board where END-2 simply
        # had nothing to say.
        self.assertEqual(frozenset(), after.dots, "the last dot was eaten")
        self.assertEqual(1, after.score)
        self.assertEqual(Position(1, 2), after.player)
        self.assertEqual(Position(1, 2), after.ghost)

        # And the game is LOST. Meeting the ghost is decided first.
        self.assertIs(
            Outcome.CAUGHT,
            after.outcome,
            "END-3: the last dot was on the ghost's square, so this is a "
            "loss. Outcome.CLEARED here means the collision test and the "
            "cleared-board test have been swapped in rules.move_player.",
        )

    def test_the_same_last_dot_one_square_away_from_the_ghost_is_a_win(self):
        """The companion. Identical but for where the ghost stands.

        ::

            #####
            #P.G#
            #####

        One dot left, the player one step from it, the ghost one step beyond.
        This wins — which is what makes the test above a statement about the
        ghost's square and not about last dots in general.
        """
        state = board("#####\n#P.G#\n#####")
        self.assertEqual(frozenset([Position(1, 2)]), state.dots)
        self.assertEqual(Position(1, 3), state.ghost)

        after = rules.move_player(state, RIGHT)

        self.assertEqual(frozenset(), after.dots)
        self.assertEqual(1, after.score)
        self.assertIs(Outcome.CLEARED, after.outcome)

    def test_END_3_holds_from_whichever_side_the_player_arrives(self):
        """The same position approached from above rather than from the side.

        ::

            ###
            #P#
            #*#
            ###

        The ghost is below the player, on the last dot.
        """
        state = board("###\n#P#\n#*#\n###")
        self.assertEqual(Position(1, 1), state.player)
        self.assertEqual(Position(2, 1), state.ghost)
        self.assertEqual(frozenset([Position(2, 1)]), state.dots)

        after = rules.move_player(state, DOWN)

        self.assertEqual(frozenset(), after.dots)
        self.assertIs(Outcome.CAUGHT, after.outcome)

    def test_the_ghost_on_a_dot_that_is_not_the_last_one_is_still_a_loss(self):
        """END-1 and END-3 agree when there are dots to spare.

        ::

            ######
            #P*..#
            ######
        """
        state = board("######\n#P*..#\n######")
        self.assertEqual(3, len(state.dots))

        after = rules.move_player(state, RIGHT)

        self.assertIs(Outcome.CAUGHT, after.outcome)
        self.assertEqual(1, after.score, "the dot under the ghost was eaten")
        self.assertEqual(
            {Position(1, 3), Position(1, 4)}, set(after.dots)
        )


# --------------------------------------------------------------------------
# After the game has ended — END-5
# --------------------------------------------------------------------------


class AfterTheGameHasEnded(unittest.TestCase):
    """END-5, the player's half: once it is over the arrow keys do nothing."""

    def _assert_every_direction_is_a_no_op(self, state):
        # The guard must be what stops the move, not a board with nowhere to
        # go: at least one direction out of the player's square is open.
        self.assertTrue(
            state.maze.open_directions(state.player),
            "this board has no open way out, so the test would pass vacuously",
        )
        for direction in DIRECTIONS:
            after = rules.move_player(state, direction)
            self.assertIs(
                state,
                after,
                "%s changed the state after the game ended" % direction.name,
            )

    def test_after_a_loss_every_direction_leaves_the_state_identical(self):
        lost = rules.move_player(board("####\n#P*#\n####"), RIGHT)
        self.assertIs(Outcome.CAUGHT, lost.outcome)
        self._assert_every_direction_is_a_no_op(lost)

    def test_after_a_win_every_direction_leaves_the_state_identical(self):
        won = rules.move_player(board("#####\n#P.G#\n#####"), RIGHT)
        self.assertIs(Outcome.CLEARED, won.outcome)
        self._assert_every_direction_is_a_no_op(won)

    def test_an_ended_game_is_not_disturbed_by_a_press_towards_a_dot(self):
        """The dots and the score of a finished game stay exactly as they were.

        ::

            ######
            #.P*.#
            ######
        """
        state = board("######\n#.P*.#\n######")
        lost = rules.move_player(state, RIGHT)
        self.assertIs(Outcome.CAUGHT, lost.outcome)
        self.assertEqual({Position(1, 1), Position(1, 4)}, set(lost.dots))
        self.assertEqual(1, lost.score)

        for direction in DIRECTIONS:
            after = rules.move_player(lost, direction)
            self.assertEqual(1, after.score)
            self.assertEqual(lost.dots, after.dots)
            self.assertEqual(lost.player, after.player)

    def test_a_game_already_over_before_any_move_stays_over(self):
        """A state that arrives finished is left alone, whatever it looks
        like — the guard is on the outcome and nothing else."""
        for outcome in (Outcome.CAUGHT, Outcome.CLEARED):
            state = board(PLUS, score=3, outcome=outcome)
            for direction in DIRECTIONS:
                self.assertIs(state, rules.move_player(state, direction))


if __name__ == "__main__":
    unittest.main()
