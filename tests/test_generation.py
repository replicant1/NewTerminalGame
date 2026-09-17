"""Maze generation — MAZE-2 through MAZE-6, over many seeds and by parity.

The plan asks that the four maze properties be established **over many seeds,
not one**, by driving WI-1's checker across a large range.  That sweep is
here, and it is the test that would actually catch a generator that mostly
works.

But a sweep only ever samples.  Two of the four properties do not need
sampling, because the lattice makes them impossible to break:

* **MAZE-2** — every 2 x 2 block of squares contains one whose column and row
  are both even, and no carveable square has both coordinates even.
* **MAZE-3** — no cell and no connector can land on the border ring.

Both are asserted **exhaustively over the whole lattice**, not over a sample
of mazes, so they hold for every maze the generator could ever produce rather
than for the two hundred it happened to produce here.
"""

from __future__ import annotations

import random
from typing import Dict, List, Sequence, Set

import pytest

from terminal_game.domain.generation import (
    CELL_COLUMNS,
    CELL_ROWS,
    Cell,
    GenerationFailed,
    all_cells,
    cell_neighbours,
    cell_position,
    connector_position,
    degrees,
    edge_between,
    generate,
    maze_from_edges,
    spanning_tree,
    verified,
    without_dead_ends,
)
from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.domain.structure import (
    MINIMUM_WAYS_ON,
    border_breaches,
    check,
    dead_ends,
    unreachable_corridors,
)

#: How many seeds the sweep drives the checker across.  Large enough to be a
#: real sample of the generator's behaviour, small enough that the suite stays
#: quick: each maze costs about three milliseconds to build and check.
SEEDS = 200

#: How many seeds the variety check compares.  Smaller, because it is a
#: statement about difference rather than about correctness.
VARIETY_SEEDS = 50


@pytest.fixture(scope="module")
def many_mazes() -> Dict[int, Maze]:
    """One maze per seed, built once and shared by every sweep below.

    Module-scoped deliberately: each requirement gets its own test so that a
    failure names the requirement it broke, but they all read the same two
    hundred mazes rather than each paying to build them again.
    """
    return {seed: generate(random.Random(seed)) for seed in range(SEEDS)}


def all_possible_connectors() -> List[Position]:
    """The square opened by every join the lattice could ever have."""
    positions = []  # type: List[Position]
    for cell in all_cells():
        for neighbour in cell_neighbours(cell):
            positions.append(connector_position(edge_between(cell, neighbour)))
    return positions


def corridor_blocks_of_two_by_two(maze: Maze) -> List[Position]:
    """The top-left square of every 2 x 2 block that is corridor throughout.

    MAZE-2 says corridors are one square wide; a 2 x 2 block of corridor is
    what being two squares wide looks like on a grid.
    """
    corridors = set(maze.corridors())
    return [
        Position(x, y)
        for y in range(HEIGHT - 1)
        for x in range(WIDTH - 1)
        if {
            Position(x, y),
            Position(x + 1, y),
            Position(x, y + 1),
            Position(x + 1, y + 1),
        }
        <= corridors
    ]


class Numbers:
    """A random source that is exactly the :class:`RandomSource` protocol.

    It has ``randrange`` and nothing else — no ``shuffle``, no ``choice``, no
    ``seed``.  A generator that reached for any of those would fail with an
    ``AttributeError`` here, which is how the claim that one method is the
    whole surface gets tested rather than merely asserted in a docstring.
    """

    def __init__(self, numbers: Sequence[int]) -> None:
        self.numbers = list(numbers)
        self.index = 0
        self.asked = []  # type: List[int]

    def randrange(self, stop: int) -> int:
        self.asked.append(stop)
        value = self.numbers[self.index % len(self.numbers)]
        self.index += 1
        return value % stop


# --------------------------------------------------------------------------
# The lattice: what can be carved at all
# --------------------------------------------------------------------------


def test_the_lattice_is_nine_cells_across_and_fourteen_deep() -> None:
    """19 = 2 x 9 + 1 and 29 = 2 x 14 + 1, which is why the grid is that size."""
    assert (CELL_COLUMNS, CELL_ROWS) == (9, 14)
    assert WIDTH == 2 * CELL_COLUMNS + 1
    assert HEIGHT == 2 * CELL_ROWS + 1


def test_there_are_one_hundred_and_twenty_six_cells_in_reading_order() -> None:
    cells = all_cells()
    assert len(cells) == 126
    assert cells[0] == Cell(0, 0)
    assert cells[1] == Cell(1, 0)
    assert cells[CELL_COLUMNS] == Cell(0, 1)
    assert cells[-1] == Cell(CELL_COLUMNS - 1, CELL_ROWS - 1)


def test_a_cell_sits_on_an_odd_column_and_an_odd_row() -> None:
    for cell in all_cells():
        position = cell_position(cell)
        assert position.x % 2 == 1
        assert position.y % 2 == 1


def test_the_cells_span_the_whole_interior() -> None:
    assert cell_position(Cell(0, 0)) == Position(1, 1)
    assert cell_position(Cell(CELL_COLUMNS - 1, CELL_ROWS - 1)) == Position(
        WIDTH - 2, HEIGHT - 2
    )


@pytest.mark.parametrize(
    "cell,expected",
    [
        (Cell(0, 0), 2),
        (Cell(CELL_COLUMNS - 1, 0), 2),
        (Cell(0, CELL_ROWS - 1), 2),
        (Cell(CELL_COLUMNS - 1, CELL_ROWS - 1), 2),
        (Cell(4, 0), 3),
        (Cell(0, 7), 3),
        (Cell(4, 7), 4),
    ],
)
def test_a_cell_has_two_three_or_four_lattice_neighbours(cell, expected) -> None:
    """Two at worst — which is why every cell can be given the two ways on
    that MAZE-5 asks for, with never a cell that has run out of neighbours."""
    assert len(cell_neighbours(cell)) == expected


def test_no_cell_has_fewer_neighbours_than_the_minimum_ways_on() -> None:
    """The repair pass rests on this being true of every cell without exception."""
    for cell in all_cells():
        assert len(cell_neighbours(cell)) >= MINIMUM_WAYS_ON


def test_being_a_neighbour_is_mutual() -> None:
    for cell in all_cells():
        for neighbour in cell_neighbours(cell):
            assert cell in cell_neighbours(neighbour)


def test_an_edge_is_the_same_value_whichever_way_it_was_found() -> None:
    assert edge_between(Cell(3, 4), Cell(3, 5)) == edge_between(Cell(3, 5), Cell(3, 4))


def test_a_connector_is_the_single_square_between_two_cells() -> None:
    assert connector_position(edge_between(Cell(0, 0), Cell(1, 0))) == Position(2, 1)
    assert connector_position(edge_between(Cell(0, 0), Cell(0, 1))) == Position(1, 2)


# --------------------------------------------------------------------------
# MAZE-2 and MAZE-3, by parity, over the whole lattice rather than a sample
# --------------------------------------------------------------------------


def test_no_carveable_square_has_both_coordinates_even() -> None:
    """MAZE-2, exhaustively.

    Every 2 x 2 block of squares contains one whose column and row are both
    even. If no square the generator can carve is like that, then no 2 x 2
    block can be corridor throughout, and a corridor two squares wide is not
    unlikely but unrepresentable.
    """
    carveable = [cell_position(cell) for cell in all_cells()]
    carveable.extend(all_possible_connectors())

    both_even = [p for p in carveable if p.x % 2 == 0 and p.y % 2 == 0]
    assert both_even == []


def test_every_two_by_two_block_contains_a_both_even_square() -> None:
    """The other half of that argument, which is about the grid, not the lattice."""
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            block = [
                Position(x, y),
                Position(x + 1, y),
                Position(x, y + 1),
                Position(x + 1, y + 1),
            ]
            assert any(p.x % 2 == 0 and p.y % 2 == 0 for p in block)


def test_no_carveable_square_is_on_the_border_ring() -> None:
    """MAZE-3, exhaustively. The border is never carved because it cannot be."""
    border = set(Maze.all_walls().border())
    carveable = [cell_position(cell) for cell in all_cells()]
    carveable.extend(all_possible_connectors())

    assert [p for p in carveable if p in border] == []


def test_a_connector_has_exactly_one_even_coordinate() -> None:
    for position in all_possible_connectors():
        assert (position.x % 2 == 0) != (position.y % 2 == 0)


# --------------------------------------------------------------------------
# Carving, and the repair that follows it
# --------------------------------------------------------------------------


def test_the_carve_reaches_every_cell() -> None:
    """MAZE-6 begins here: a cell the carve never reached could not be walked to."""
    edges = spanning_tree(random.Random(7))
    reached = set(degrees(edges))
    assert reached == set(all_cells())


def test_the_carve_produces_a_tree_with_no_loops() -> None:
    """126 cells joined by 125 edges is a tree, which is the most dead ends
    possible — and exactly what the repair pass then has to fix."""
    edges = spanning_tree(random.Random(7))
    assert len(edges) == len(all_cells()) - 1


def test_the_carve_is_nothing_but_dead_ends_before_the_repair() -> None:
    """Stated so that the repair pass is visibly doing something, not decoration."""
    maze = maze_from_edges(spanning_tree(random.Random(7)))
    assert len(dead_ends(maze)) > 0


def test_the_repair_gives_every_cell_at_least_two_ways_on() -> None:
    repaired = without_dead_ends(spanning_tree(random.Random(11)), random.Random(11))
    degree = degrees(repaired)
    assert min(degree[cell] for cell in all_cells()) >= MINIMUM_WAYS_ON


def test_the_repair_only_ever_adds_edges() -> None:
    """Which is why it cannot disconnect what the carve joined, and why it
    cannot create the dead ends it is removing."""
    carved = spanning_tree(random.Random(11))
    repaired = without_dead_ends(carved, random.Random(11))
    assert carved <= repaired


def test_the_repair_leaves_an_already_sound_lattice_alone() -> None:
    """Running it twice changes nothing the second time: it converges in one pass."""
    once = without_dead_ends(spanning_tree(random.Random(3)), random.Random(3))
    twice = without_dead_ends(once, random.Random(99))
    assert twice == once


def test_the_repair_gives_a_wholly_isolated_cell_two_ways_on() -> None:
    """A shortfall of two, not one.

    The carve cannot leave a cell with no edges at all, so this is the repair
    asked a question the generator never asks it. It is worth asking anyway:
    a repair that assumed every cell already had one way on would quietly
    leave this cell a dead end, and the checker would be the only thing that
    noticed.
    """
    corner = Cell(0, 0)
    everything_else = frozenset(
        edge_between(cell, neighbour)
        for cell in all_cells()
        for neighbour in cell_neighbours(cell)
        if corner not in (cell, neighbour)
    )
    repaired = without_dead_ends(everything_else, random.Random(5))

    assert degrees(repaired)[corner] == MINIMUM_WAYS_ON


def test_a_maze_is_built_from_every_cell_and_every_opened_edge() -> None:
    edges = frozenset([edge_between(Cell(0, 0), Cell(1, 0))])
    maze = maze_from_edges(edges)

    assert maze.is_corridor(Position(1, 1))
    assert maze.is_corridor(Position(3, 1))
    assert maze.is_corridor(Position(2, 1))
    assert maze.is_wall(Position(2, 2))


def test_a_cell_is_carved_even_when_no_edge_reaches_it() -> None:
    """So that a cell can never be silently dropped from the grid."""
    maze = maze_from_edges(frozenset())
    assert len(maze.corridors()) == len(all_cells())


# --------------------------------------------------------------------------
# The gate before a maze is handed out
# --------------------------------------------------------------------------


def test_a_sound_maze_passes_the_gate(sound_maze) -> None:
    assert verified(sound_maze) is sound_maze


def test_an_unsound_maze_is_refused_rather_than_handed_out(draw) -> None:
    """An unreachable dot makes the game unwinnable and a pocket traps the player."""
    with pytest.raises(GenerationFailed) as raised:
        verified(draw(".", at=(9, 9)))
    assert "MAZE-5" in str(raised.value)


def test_the_refusal_says_which_requirement_failed(draw) -> None:
    with pytest.raises(GenerationFailed) as raised:
        verified(draw(".", at=(0, 9)))
    message = str(raised.value)
    assert "MAZE-3" in message
    assert "(0, 9)" in message


# --------------------------------------------------------------------------
# MAZE-4 — a new maze every game, and the same maze from the same numbers
# --------------------------------------------------------------------------


def test_the_same_seed_gives_the_same_maze() -> None:
    assert generate(random.Random(42)) == generate(random.Random(42))


def test_different_seeds_give_different_mazes() -> None:
    """*"No two games are the same."*"""
    mazes = {generate(random.Random(seed)) for seed in range(VARIETY_SEEDS)}
    assert len(mazes) == VARIETY_SEEDS


def test_the_generator_asks_its_random_source_for_numbers() -> None:
    """A generator that ignored the source would be the same maze every game."""
    numbers = Numbers([3, 1, 4, 1, 5, 9, 2, 6])
    generate(numbers)
    assert len(numbers.asked) > 100


def test_the_generator_needs_nothing_but_randrange() -> None:
    """``Numbers`` has no ``shuffle`` and no ``choice``; reaching for either
    would raise ``AttributeError`` rather than quietly widening the protocol."""
    one = generate(Numbers([3, 1, 4, 1, 5, 9, 2, 6]))
    other = generate(Numbers([3, 1, 4, 1, 5, 9, 2, 6]))
    assert one == other


def test_the_same_numbers_in_a_different_order_give_a_different_maze() -> None:
    assert generate(Numbers([3, 1, 4, 1, 5])) != generate(Numbers([5, 1, 4, 1, 3]))


# --------------------------------------------------------------------------
# The sweep: every requirement, over many seeds
# --------------------------------------------------------------------------


def test_the_border_is_solid_in_every_maze(many_mazes) -> None:
    """MAZE-3 over every seed: nothing can leave the maze."""
    broken = {
        seed: border_breaches(maze)
        for seed, maze in many_mazes.items()
        if border_breaches(maze)
    }
    assert broken == {}


def test_no_maze_has_a_dead_end(many_mazes) -> None:
    """MAZE-5 over every seed: the player is never trapped in a pocket."""
    broken = {
        seed: dead_ends(maze) for seed, maze in many_mazes.items() if dead_ends(maze)
    }
    assert broken == {}


def test_every_corridor_square_is_reachable_in_every_maze(many_mazes) -> None:
    """MAZE-6 over every seed: no dot is unreachable."""
    broken = {
        seed: unreachable_corridors(maze)
        for seed, maze in many_mazes.items()
        if unreachable_corridors(maze)
    }
    assert broken == {}


def test_no_corridor_is_wider_than_one_square_in_any_maze(many_mazes) -> None:
    """MAZE-2 over every seed, as a check on the parity argument above."""
    broken = {
        seed: corridor_blocks_of_two_by_two(maze)
        for seed, maze in many_mazes.items()
        if corridor_blocks_of_two_by_two(maze)
    }
    assert broken == {}


def test_every_maze_is_sound_by_all_three_questions_at_once(many_mazes) -> None:
    """The oracle's own verdict, which is what the generator gates on."""
    unsound = {
        seed: check(maze).describe()
        for seed, maze in many_mazes.items()
        if not check(maze).is_sound
    }
    assert unsound == {}


def test_every_maze_has_a_substantial_amount_of_corridor(many_mazes) -> None:
    """A maze of almost no corridor would pass all three questions and be no
    maze at all — the 126 cells are always carved, so this is really a check
    that the connectors are being carved too."""
    for seed, maze in many_mazes.items():
        assert len(maze.corridors()) > 200, "seed {} carved too little".format(seed)


def test_no_two_of_the_swept_mazes_are_the_same(many_mazes) -> None:
    """MAZE-4 at the scale of the sweep rather than the sample."""
    assert len(set(many_mazes.values())) == SEEDS
