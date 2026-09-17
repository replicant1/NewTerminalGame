"""The structural checker — MAZE-3, MAZE-5 and MAZE-6, asked separately.

The plan asks that the checker *"correctly accepts and rejects hand-built
grids for each of its three questions independently"*, and independence is
the substance of it rather than a qualifier.  This is WI-2's oracle: a
carve-then-repair loop opens a wall to remove a dead end and thereby changes
connectivity, so an answer that bundled the three together would leave the
generator unable to tell whether its last repair helped.

So each question is exercised three ways: it accepts what it should, it
rejects what it should and names the squares, and — the part that matters —
**a maze that fails one question passes the other two.**
"""

from __future__ import annotations

import pytest

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.domain.structure import (
    MINIMUM_WAYS_ON,
    border_breaches,
    check,
    dead_ends,
    unreachable_corridors,
)

#: A loop touching the top-left corner of the grid.  A ring, so no square on
#: it is a dead end, and all of it is one piece — but five of its squares are
#: on the border ring, so MAZE-3 fails and only MAZE-3.
RING_ON_THE_BORDER = """
    ...
    .#.
    ...
"""

#: A ring with one square hanging off the middle of its bottom edge.  The stub
#: has exactly one way on, so MAZE-5 fails; the border is untouched and every
#: square is still reachable, so the other two questions hold.
#:
#: The stub hangs off the *middle* deliberately.  Hung off a corner it would
#: touch two squares of the ring and have two ways on, which is no dead end at
#: all — the first draft of this picture made exactly that mistake.
RING_WITH_A_STUB = """
    .....
    .###.
    .....
      .
"""

#: Two rings that never meet.  Neither has a dead end and neither touches the
#: border, so only MAZE-6 fails.
TWO_SEPARATE_RINGS = """
    ...#...
    .#.#.#.
    ...#...
"""


# --------------------------------------------------------------------------
# MAZE-3 — is the border ring solid?
# --------------------------------------------------------------------------


def test_a_solid_maze_has_no_border_breaches() -> None:
    assert border_breaches(Maze.all_walls()) == ()


def test_an_interior_maze_has_no_border_breaches(sound_maze) -> None:
    assert border_breaches(sound_maze) == ()


@pytest.mark.parametrize(
    "breach",
    [
        Position(0, 0),
        Position(WIDTH - 1, 0),
        Position(0, HEIGHT - 1),
        Position(WIDTH - 1, HEIGHT - 1),
        Position(9, 0),
        Position(0, 14),
    ],
)
def test_one_carved_border_square_is_reported_as_a_breach(sound_maze, breach) -> None:
    """Corners included — a tunnel out is a tunnel out wherever it is."""
    assert border_breaches(sound_maze.with_corridors_at([breach])) == (breach,)


def test_breaches_are_reported_in_reading_order(sound_maze) -> None:
    """So that a generator filling them back in works down the maze predictably."""
    breached = sound_maze.with_corridors_at(
        [Position(0, 7), Position(5, 0), Position(0, 2)]
    )
    assert border_breaches(breached) == (
        Position(5, 0),
        Position(0, 2),
        Position(0, 7),
    )


def test_a_corridor_just_inside_the_border_is_not_a_breach() -> None:
    """The ring is one square deep; row 1 is inside the maze, not part of it."""
    maze = Maze.all_walls().with_corridors_at([Position(1, 1)])
    assert border_breaches(maze) == ()


def test_a_breached_border_does_not_make_the_other_two_questions_fail(draw) -> None:
    """MAZE-3 alone: a ring on the corner has no dead end and is all one piece."""
    maze = draw(RING_ON_THE_BORDER, at=(0, 0))
    report = check(maze)

    assert not report.border_is_solid
    assert report.has_no_dead_ends
    assert report.is_fully_connected


# --------------------------------------------------------------------------
# MAZE-5 — has any corridor square fewer than two ways on?
# --------------------------------------------------------------------------


def test_a_solid_maze_has_no_dead_ends() -> None:
    """Vacuously: there are no corridor squares to be trapped in."""
    assert dead_ends(Maze.all_walls()) == ()


def test_a_ring_has_no_dead_ends(sound_maze) -> None:
    assert dead_ends(sound_maze) == ()


def test_every_square_of_a_ring_has_exactly_two_ways_on(sound_maze) -> None:
    """Which is what makes the ring the right baseline to break one thing in."""
    for position in sound_maze.corridors():
        assert len(sound_maze.corridor_neighbours(position)) == MINIMUM_WAYS_ON


def test_a_lone_corridor_square_is_a_dead_end(draw) -> None:
    """Zero ways on, not one. A checker looking for exactly one would miss it."""
    maze = draw(".", at=(9, 9))
    assert dead_ends(maze) == (Position(9, 9),)


def test_a_stub_hanging_off_a_ring_is_a_dead_end(draw) -> None:
    maze = draw(RING_WITH_A_STUB, at=(5, 5))
    assert dead_ends(maze) == (Position(7, 8),)


def test_a_square_touching_a_ring_at_two_points_is_not_a_dead_end(draw) -> None:
    """Two ways on is enough, even when both lead to the same loop.

    MAZE-5 counts ways on; it does not ask where they go. This is the shape
    the stub picture above accidentally had at first, and it is worth keeping
    as a test so that nobody 'fixes' the checker towards it.
    """
    maze = draw(
        """
        .....
        .###.
        .....
        ..
        """,
        at=(5, 5),
    )
    assert dead_ends(maze) == ()


def test_both_ends_of_a_straight_corridor_are_dead_ends_and_the_middle_is_not(draw) -> None:
    maze = draw("...", at=(4, 11))
    assert dead_ends(maze) == (Position(4, 11), Position(6, 11))


def test_dead_ends_are_reported_in_reading_order(draw) -> None:
    maze = draw(
        """
        .

        .
        """,
        at=(3, 3),
    )
    assert dead_ends(maze) == (Position(3, 3), Position(3, 5))


def test_a_dead_end_does_not_make_the_other_two_questions_fail(draw) -> None:
    """MAZE-5 alone: the stub is reachable and the border is untouched."""
    maze = draw(RING_WITH_A_STUB, at=(5, 5))
    report = check(maze)

    assert report.border_is_solid
    assert not report.has_no_dead_ends
    assert report.is_fully_connected


# --------------------------------------------------------------------------
# MAZE-6 — can every corridor square be walked to from every other?
# --------------------------------------------------------------------------


def test_a_maze_with_no_corridors_is_connected() -> None:
    """Vacuously, and truthfully. Whether it is a *good* maze is MAZE-5's business."""
    assert unreachable_corridors(Maze.all_walls()) == ()


def test_a_maze_with_one_corridor_square_is_connected(draw) -> None:
    assert unreachable_corridors(draw(".", at=(9, 9))) == ()


def test_a_single_ring_is_all_one_piece(sound_maze) -> None:
    assert unreachable_corridors(sound_maze) == ()


def test_the_second_of_two_separate_rings_is_unreachable(draw) -> None:
    maze = draw(TWO_SEPARATE_RINGS, at=(5, 5))
    cut_off = unreachable_corridors(maze)

    assert cut_off == (
        Position(9, 5),
        Position(10, 5),
        Position(11, 5),
        Position(9, 6),
        Position(11, 6),
        Position(9, 7),
        Position(10, 7),
        Position(11, 7),
    )


def test_the_component_holding_the_first_corridor_square_is_the_reachable_one(draw) -> None:
    """Which component counts as "the rest" has to be decided the same way twice."""
    maze = draw(TWO_SEPARATE_RINGS, at=(5, 5))
    reachable = set(maze.corridors()) - set(unreachable_corridors(maze))

    assert maze.corridors()[0] in reachable
    assert len(reachable) == 8


def test_three_separate_pieces_leave_two_of_them_unreachable(draw) -> None:
    maze = draw(
        """
        . . .
        """,
        at=(4, 12),
    )
    assert unreachable_corridors(maze) == (Position(6, 12), Position(8, 12))


def test_diagonally_touching_squares_are_not_connected(draw) -> None:
    """MAZE-2 says corridors run north-south and east-west; a corner is not a way on."""
    maze = draw(
        """
        .#
        #.
        """,
        at=(7, 7),
    )
    assert unreachable_corridors(maze) == (Position(8, 8),)


def test_a_long_winding_corridor_is_walked_all_the_way_to_the_end(draw) -> None:
    """A search that stopped early would report the far end as unreachable."""
    maze = draw(
        """
        .........
        ########.
        .........
        .########
        .........
        """,
        at=(5, 5),
    )
    assert unreachable_corridors(maze) == ()


def test_being_cut_off_does_not_make_the_other_two_questions_fail(draw) -> None:
    """MAZE-6 alone: both rings are clear of the border and neither has a dead end."""
    maze = draw(TWO_SEPARATE_RINGS, at=(5, 5))
    report = check(maze)

    assert report.border_is_solid
    assert report.has_no_dead_ends
    assert not report.is_fully_connected


# --------------------------------------------------------------------------
# The report the three answers arrive in
# --------------------------------------------------------------------------


def test_a_sound_maze_is_sound_by_all_three_questions(sound_maze) -> None:
    report = check(sound_maze)

    assert report.is_sound
    assert (report.breaches, report.pockets, report.islands) == ((), (), ())


def test_a_maze_failing_any_one_question_is_not_sound(draw) -> None:
    for picture, at in [
        (RING_ON_THE_BORDER, (0, 0)),
        (RING_WITH_A_STUB, (5, 5)),
        (TWO_SEPARATE_RINGS, (5, 5)),
    ]:
        assert not check(draw(picture, at=at)).is_sound


def test_the_report_carries_the_same_squares_the_three_questions_return(draw) -> None:
    """One call and three calls must not be able to disagree."""
    maze = draw(RING_WITH_A_STUB, at=(5, 5)).with_corridors_at([Position(0, 3)])
    report = check(maze)

    assert report.breaches == border_breaches(maze)
    assert report.pockets == dead_ends(maze)
    assert report.islands == unreachable_corridors(maze)


def test_a_maze_can_fail_all_three_questions_at_once(draw) -> None:
    """The three are independent, so nothing stops them all going wrong together."""
    maze = draw(".", at=(0, 5)).with_corridors_at([Position(9, 9), Position(10, 9)])
    report = check(maze)

    assert not report.border_is_solid
    assert not report.has_no_dead_ends
    assert not report.is_fully_connected


def test_a_sound_report_describes_itself_as_sound(sound_maze) -> None:
    assert check(sound_maze).describe() == (
        "sound: border solid, no dead ends, fully connected"
    )


def test_a_failing_report_names_the_requirement_and_the_squares(draw) -> None:
    """Somebody reads this string when a generator gives up; it has to say which."""
    described = check(draw(RING_WITH_A_STUB, at=(5, 5))).describe()

    assert "MAZE-5" in described
    assert "(7, 8)" in described
    assert "MAZE-3" not in described
    assert "MAZE-6" not in described


def test_a_long_list_of_failures_is_summarised_rather_than_dumped(draw) -> None:
    """Twenty-odd coordinates in a failure message is a failure nobody reads."""
    maze = Maze.all_walls().with_corridors_at(
        [Position(x, 0) for x in range(0, WIDTH, 2)]
    )
    described = check(maze).describe()

    assert "MAZE-3" in described
    assert "and 2 more" in described
