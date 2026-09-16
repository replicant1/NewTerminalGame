# -*- coding: utf-8 -*-
"""WI-7 — the ghost's movement policy.

Hand-built mazes throughout: the point of this item is that it is a pure
function of a maze, a square and a heading, so nothing here needs the
generator, a clock, a window, or a player.
"""

from __future__ import annotations

import inspect
import random
import unittest

from terminal_game.domain.ghost import (
    GhostIsWalledIn,
    GhostStep,
    next_step,
    onward_choices,
)
from terminal_game.domain.maze import Direction, Maze, Square

# A straight east-west corridor.  (1,1) (2,1) (3,1).
STRAIGHT = Maze.from_text(
    """
#####
#...#
#####
"""
)

# A crossroads at (2,2), open all four ways.
CROSSROADS = Maze.from_text(
    """
#####
##.##
#...#
##.##
#####
"""
)

# A T at (2,2): north, south and west are open, east is wall.
TEE = Maze.from_text(
    """
#####
##.##
#..##
##.##
#####
"""
)

# A corner at (1,2): the only way on other than back is east.
CORNER = Maze.from_text(
    """
#####
#.###
#..##
#####
"""
)

# A dead end at (2,1): the only way off it is back west.
DEAD_END = Maze.from_text(
    """
#####
#..##
#####
"""
)

# A lattice with pillars — plenty of junctions, and no dead ends.
LATTICE = Maze.from_text(
    """
#######
#.....#
#.#.#.#
#.....#
#.#.#.#
#.....#
#######
"""
)

# One square of corridor with no way off it.  The generator cannot produce
# this (MAZE-5, MAZE-6); the function still has to say something sensible.
WALLED_IN = Maze.from_text(
    """
###
#.#
###
"""
)


def walk(maze, square, heading, random_source, steps):
    """Where the ghost goes over *steps* ticks, as a list of squares."""
    path = []
    for _ in range(steps):
        step = next_step(maze, square, heading, random_source)
        square, heading = step.square, step.direction
        path.append(step.square)
    return path


def branch_points(maze, square, heading, random_source, steps):
    """How many of those ticks the ghost actually had a choice on.

    Far fewer than you would guess: the ghost only chooses where it cannot
    carry straight on *and* more than one other way is open.  Measured on 30
    real generated mazes this is about 4.8 ticks in 100; on the regular
    lattice fixture below it is fewer still, which is why the tests that
    depend on a choice happening say how many they got.
    """
    count = 0
    for _ in range(steps):
        if heading is not None and heading not in maze.ways_on(square):
            if len(onward_choices(maze, square, heading)) > 1:
                count += 1
        step = next_step(maze, square, heading, random_source)
        square, heading = step.square, step.direction
    return count


class CarryingStraightOn(unittest.TestCase):
    """GHOST-2 — in a straight line for as long as the corridor lets it."""

    def test_in_a_straight_corridor_it_carries_on(self):
        step = next_step(
            STRAIGHT, Square(2, 1), Direction.EAST, random.Random(1)
        )

        self.assertEqual(GhostStep(Direction.EAST, Square(3, 1)), step)

    def test_it_carries_on_every_time_over_many_draws(self):
        source = random.Random(7)

        results = {
            next_step(STRAIGHT, Square(2, 1), Direction.EAST, source)
            for _ in range(200)
        }

        self.assertEqual({GhostStep(Direction.EAST, Square(3, 1))}, results)

    def test_carrying_on_does_not_depend_on_the_random_source_at_all(self):
        # Different seeds, same answer: there is no choice being made here.
        results = {
            next_step(
                STRAIGHT, Square(2, 1), Direction.EAST, random.Random(seed)
            )
            for seed in range(50)
        }

        self.assertEqual({GhostStep(Direction.EAST, Square(3, 1))}, results)

    def test_at_a_crossroads_it_still_goes_straight_rather_than_choosing(self):
        # Three ways onward and it takes none of them: a junction is not a
        # reason to turn.
        source = random.Random(3)

        results = {
            next_step(CROSSROADS, Square(2, 2), Direction.EAST, source)
            for _ in range(200)
        }

        self.assertEqual({GhostStep(Direction.EAST, Square(3, 2))}, results)

    def test_it_carries_on_in_whichever_direction_it_was_going(self):
        for heading, expected in (
            (Direction.NORTH, Square(2, 1)),
            (Direction.SOUTH, Square(2, 3)),
            (Direction.EAST, Square(3, 2)),
            (Direction.WEST, Square(1, 2)),
        ):
            step = next_step(
                CROSSROADS, Square(2, 2), heading, random.Random(11)
            )

            self.assertEqual(GhostStep(heading, expected), step)


class ChoosingWhereItCannotCarryOn(unittest.TestCase):
    """GHOST-3 — one of the *other* ways on, at random."""

    def test_at_a_tee_it_never_goes_back_the_way_it_came(self):
        source = random.Random(5)

        for _ in range(500):
            step = next_step(TEE, Square(2, 2), Direction.EAST, source)

            self.assertNotEqual(Direction.WEST, step.direction)
            self.assertNotEqual(Square(1, 2), step.square)

    def test_at_a_tee_it_takes_one_of_the_two_arms(self):
        source = random.Random(5)

        taken = {
            next_step(TEE, Square(2, 2), Direction.EAST, source)
            for _ in range(500)
        }

        self.assertEqual(
            {
                GhostStep(Direction.NORTH, Square(2, 1)),
                GhostStep(Direction.SOUTH, Square(2, 3)),
            },
            taken,
        )

    def test_over_many_draws_the_two_arms_come_up_about_equally(self):
        source = random.Random(20260916)
        draws = 2000

        north = sum(
            1
            for _ in range(draws)
            if next_step(TEE, Square(2, 2), Direction.EAST, source).direction
            is Direction.NORTH
        )

        self.assertGreater(north, draws * 0.45)
        self.assertLess(north, draws * 0.55)

    def test_at_a_corner_it_always_turns_the_one_way_there_is(self):
        source = random.Random(2)

        results = {
            next_step(CORNER, Square(1, 2), Direction.SOUTH, source)
            for _ in range(200)
        }

        self.assertEqual({GhostStep(Direction.EAST, Square(2, 2))}, results)

    def test_the_choices_offered_exclude_the_way_it_came(self):
        self.assertEqual(
            [Direction.NORTH, Direction.SOUTH],
            onward_choices(TEE, Square(2, 2), Direction.EAST),
        )

    def test_with_no_heading_yet_every_way_on_is_a_choice(self):
        # The first tick of a game: the ghost has been placed but has not
        # moved, so it has not come from anywhere.
        self.assertEqual(
            [
                Direction.NORTH,
                Direction.EAST,
                Direction.SOUTH,
                Direction.WEST,
            ],
            onward_choices(CROSSROADS, Square(2, 2), None),
        )

    def test_with_no_heading_yet_it_can_set_off_in_any_direction(self):
        source = random.Random(99)

        taken = {
            next_step(CROSSROADS, Square(2, 2), None, source).direction
            for _ in range(500)
        }

        self.assertEqual(
            {
                Direction.NORTH,
                Direction.EAST,
                Direction.SOUTH,
                Direction.WEST,
            },
            taken,
        )


class TurningBackOnlyAsALastResort(unittest.TestCase):
    """GHOST-3 — and the function is total even where the maze will not be."""

    def test_in_a_dead_end_it_reverses(self):
        step = next_step(
            DEAD_END, Square(2, 1), Direction.EAST, random.Random(4)
        )

        self.assertEqual(GhostStep(Direction.WEST, Square(1, 1)), step)

    def test_in_a_dead_end_it_reverses_every_time(self):
        source = random.Random(4)

        results = {
            next_step(DEAD_END, Square(2, 1), Direction.EAST, source)
            for _ in range(200)
        }

        self.assertEqual({GhostStep(Direction.WEST, Square(1, 1))}, results)

    def test_a_dead_end_offers_no_choice_but_going_back(self):
        self.assertEqual([], onward_choices(DEAD_END, Square(2, 1), Direction.EAST))

    def test_a_square_with_no_way_off_it_at_all_says_so(self):
        with self.assertRaises(GhostIsWalledIn):
            next_step(
                WALLED_IN, Square(1, 1), Direction.EAST, random.Random(1)
            )


class TheGhostTakesNoNoticeOfThePlayer(unittest.TestCase):
    """GHOST-4 — the player is not a parameter, so it cannot hunt by mistake."""

    def test_the_signature_carries_no_player(self):
        names = list(inspect.signature(next_step).parameters)

        self.assertEqual(
            ["maze", "square", "heading", "random_source"], names
        )

    def test_nothing_in_the_policy_names_a_player_a_dot_or_a_score(self):
        import terminal_game.domain.ghost as policy

        source = inspect.getsource(policy).lower()

        for forbidden in ("player", "dot", "score"):
            # The docstring says out loud *why* these are absent, so look at
            # the code rather than the prose it is wrapped in.
            code = "\n".join(
                line
                for line in source.splitlines()
                if not line.strip().startswith("#")
            )
            body = code.split('"""')
            executable = "".join(body[::2])
            self.assertNotIn(forbidden, executable)


class TheWalkIsReproducible(unittest.TestCase):
    """MAZE-4's discipline applied to the ghost: randomness is handed in."""

    START = Square(3, 3)
    HEADING = Direction.WEST
    STEPS = 200

    def setUp(self):
        # A walk with no branch point in it would make the two tests below
        # assert nothing, because every seed would give the same answer for
        # reasons that have nothing to do with the seed.  Say what the
        # fixture is worth rather than assuming it.
        self.assertGreater(
            branch_points(
                LATTICE,
                self.START,
                self.HEADING,
                random.Random(0),
                self.STEPS,
            ),
            0,
        )

    def a_walk(self, seed):
        return tuple(
            walk(
                LATTICE,
                self.START,
                self.HEADING,
                random.Random(seed),
                self.STEPS,
            )
        )

    def test_the_same_seed_gives_the_same_walk(self):
        self.assertEqual(self.a_walk(12345), self.a_walk(12345))

    def test_the_walk_depends_on_the_random_source(self):
        # Not "seed 1 differs from seed 2": with branch points this sparse,
        # two particular seeds can easily make the same choice at the one
        # place it matters and produce identical walks. What has to be true
        # is that the seed makes *a* difference.
        walks = {self.a_walk(seed) for seed in range(8)}

        self.assertGreater(len(walks), 1)

    def test_the_ghost_never_leaves_the_corridors(self):
        path = walk(
            LATTICE, self.START, self.HEADING, random.Random(777), 400
        )

        self.assertEqual(400, len(path))
        for square in path:
            self.assertTrue(
                LATTICE.is_corridor(square),
                "the ghost stood on {0!r}, which is not corridor".format(
                    tuple(square)
                ),
            )

    def test_the_ghost_moves_one_square_at_a_time_and_never_diagonally(self):
        start = self.START
        path = walk(LATTICE, start, self.HEADING, random.Random(31), 400)

        previous = start
        for square in path:
            gap = abs(square.column - previous.column) + abs(
                square.row - previous.row
            )
            self.assertEqual(
                1,
                gap,
                "{0!r} to {1!r} is not one orthogonal step".format(
                    tuple(previous), tuple(square)
                ),
            )
            previous = square

    def test_the_heading_returned_is_the_way_it_actually_went(self):
        square, heading = self.START, self.HEADING
        source = random.Random(64)

        for _ in range(300):
            step = next_step(LATTICE, square, heading, source)

            self.assertEqual(square.neighbour(step.direction), step.square)
            square, heading = step.square, step.direction


if __name__ == "__main__":
    unittest.main()
