"""WI-4 — the 40 x 30 field of glyph-and-colour, rows 0 to 28.

The centrepiece is :func:`test_the_composer_reproduces_the_specimen_picture`.
Assumption P5 makes the picture in ``docs/FUNCTIONAL_REQUIREMENTS.md``
normative, so taking that picture apart into a maze, a dot field and two
actors, composing it back with this module and comparing character for
character is the one test that can catch a frame composed *correctly but
differently* from what the specification shows. It is the only place WI-3's
glyph table is exercised from here; everything else below is about placement,
colour and order, which are WI-4's and nobody else's.

What is deliberately **not** here: the sixteen wall-glyph cases (WI-3 owns
them and pins them against the same picture), the maze's own structure (WI-1),
and the content of row 29 (WI-12 — this module places it and reads nothing of
it).
"""

from __future__ import annotations

from typing import Callable, List, Set, Tuple

import pytest

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.presentation.frame import (
    BLANK,
    COLUMNS,
    CONNECTOR_GLYPH,
    DOT_GLYPH,
    GHOST_GLYPHS,
    MAZE_COLUMNS,
    MAZE_ROWS,
    PLAYER_GLYPHS,
    RIGHT_MARGIN,
    ROWS,
    STATUS_ROW,
    Cell,
    Colour,
    compose_frame,
    compose_maze_rows,
)
from terminal_game.presentation.wall_glyphs import LONE_BLOCK

#: A row 29 that is obviously not WI-4's: this module must place it and read
#: nothing of it, so the tests hand it something no composer would produce.
SENTINEL_STATUS_ROW = tuple(
    Cell("~", Colour.CYAN) for _ in range(COLUMNS)
)  # type: Tuple[Cell, ...]

#: Somewhere out of the way to park an actor when a test is about the other
#: one. Corridor squares are carved explicitly by the tests that use it.
FAR_CORNER = Position(17, 27)


def _text(rows: Tuple[Tuple[Cell, ...], ...]) -> List[str]:
    """The glyphs of a composed field, one string per row."""
    return ["".join(cell.glyph for cell in row) for row in rows]


# --------------------------------------------------------------------------
# The shape of the field: WIN-2 and SCRN-1
# --------------------------------------------------------------------------


def test_the_whole_frame_is_forty_columns_by_thirty_rows(sound_maze: Maze) -> None:
    """WIN-2: the window is 40 characters wide and 30 rows deep."""
    frame = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert len(frame) == ROWS == 30
    assert {len(row) for row in frame} == {COLUMNS} == {40}


def test_the_maze_occupies_rows_nought_to_twentyeight(sound_maze: Maze) -> None:
    """SCRN-1: *"the top 29 rows show the maze"*, and there are 29 of them."""
    rows = compose_maze_rows(sound_maze, [], Position(5, 5), Position(6, 5))
    assert len(rows) == MAZE_ROWS == HEIGHT == 29
    assert {len(row) for row in rows} == {COLUMNS}


def test_row_twentynine_is_exactly_what_was_handed_in(sound_maze: Maze) -> None:
    """SCRN-1's other half, and the WI-4 / WI-12 seam.

    WI-4 places row 29 and owns nothing of its content, so the test hands in a
    row no composer would ever produce and requires it back untouched.
    """
    frame = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert frame[STATUS_ROW] == SENTINEL_STATUS_ROW
    assert frame[:STATUS_ROW] == compose_maze_rows(
        sound_maze, [], Position(5, 5), Position(6, 5)
    )


def test_a_status_row_of_the_wrong_width_is_refused(sound_maze: Maze) -> None:
    """A short row would silently ragged the field rather than fail."""
    with pytest.raises(ValueError):
        compose_frame(
            sound_maze,
            [],
            Position(5, 5),
            Position(6, 5),
            SENTINEL_STATUS_ROW[:-1],
        )


# --------------------------------------------------------------------------
# The grid mapping: MAZE-1 and ruling C-2
# --------------------------------------------------------------------------


def test_a_maze_square_is_drawn_at_twice_its_column(draw: Callable[..., Maze]) -> None:
    """Ruling C-2: square ``x`` lands on screen column ``2x``, not ``x``.

    A single wall square marooned inside a carved band draws as the lone
    block, which is the only glyph in the alphabet that cannot be part of a
    line — so where it lands says what the mapping is and nothing else could
    have put it there.
    """
    room = "\n".join(["." * 17] * 3)
    maze = draw(room, at=(1, 13)).with_walls_at([Position(9, 14)])
    row = _text(compose_maze_rows(maze, [], Position(1, 14), FAR_CORNER))[14]

    assert row.count(LONE_BLOCK) == 1
    assert row[2 * 9] == LONE_BLOCK
    assert row.index(LONE_BLOCK) == 18


def test_the_maze_spans_thirtyseven_columns_and_leaves_three_blank() -> None:
    """MAZE-1's *"narrow blank margin down the right-hand edge"*, as arithmetic."""
    assert MAZE_COLUMNS == 2 * WIDTH - 1 == 37
    assert RIGHT_MARGIN == COLUMNS - MAZE_COLUMNS == 3


def test_nothing_is_ever_drawn_in_the_right_hand_margin(specimen) -> None:
    """The three margin columns stay black ground on every maze row."""
    rows = compose_maze_rows(
        specimen.maze, specimen.dots, specimen.player, specimen.ghost
    )
    for y, row in enumerate(rows):
        assert row[MAZE_COLUMNS:] == (BLANK,) * RIGHT_MARGIN, "row {}".format(y)


# --------------------------------------------------------------------------
# The picture itself
# --------------------------------------------------------------------------


def test_the_composer_reproduces_the_specimen_picture(specimen) -> None:
    """The whole of rows 0-28, character for character, against the normative picture.

    Taken apart and put back together: the maze, the 262 dots, the player at
    (10, 13) and the ghost at (1, 27) are read out of the picture, and this
    module is asked to draw them. Anything wrong with the column mapping, a
    connector, an actor's width or the order the layers go down shows up here
    as a differing row, and nothing else in the suite would catch it.
    """
    composed = _text(
        compose_maze_rows(
            specimen.maze, specimen.dots, specimen.player, specimen.ghost
        )
    )
    expected = [row.ljust(COLUMNS) for row in specimen.maze_rows]
    assert composed == expected


def test_the_specimen_really_does_exercise_the_picture(specimen) -> None:
    """The guard on the test above: it must be comparing something substantial.

    A parse that quietly produced an empty maze would make the reproduction
    test pass by drawing nothing and comparing it with nothing.
    """
    assert len(specimen.maze_rows) == HEIGHT
    assert len(specimen.maze.corridors()) == 264
    assert len(specimen.maze.walls()) == 287
    assert len(specimen.dots) == 262
    assert specimen.player == Position(10, 13)
    assert specimen.ghost == Position(1, 27)


# --------------------------------------------------------------------------
# SCRN-3's colour, which the technical lead ruled is WI-4's
# --------------------------------------------------------------------------


def test_every_wall_cell_of_the_specimen_is_blue(specimen) -> None:
    """SCRN-3: *"the walls are drawn as blue double lines"*.

    Checked over the whole picture rather than one square, because the walls
    are drawn by two separate pieces of code — the squares and the connectors
    between them — and a connector left uncoloured would look right in a
    single-cell test.
    """
    rows = compose_maze_rows(
        specimen.maze, specimen.dots, specimen.player, specimen.ghost
    )
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if specimen.maze.is_wall(Position(x, y)):
                assert rows[y][2 * x].colour is Colour.BLUE, "square ({}, {})".format(
                    x, y
                )
    connectors = [
        cell
        for row in rows
        for cell in row
        if cell.glyph == CONNECTOR_GLYPH
    ]
    assert connectors
    assert {cell.colour for cell in connectors} == {Colour.BLUE}


def test_a_lone_block_is_the_same_blue_as_a_line(draw: Callable[..., Maze]) -> None:
    """The ruling's specific point: SCRN-3 names one colour for both.

    *"The walls are drawn as blue double lines … a wall square with no wall
    next to it is drawn as a single blue block."*  One blue, two shapes.
    """
    # A carved room with a single wall square marooned in the middle of it.
    maze = draw(
        """
        .....
        .....
        .....
        .....
        .....
        """,
        at=(6, 10),
    ).with_walls_at([Position(8, 12)])
    rows = compose_maze_rows(maze, [], Position(6, 10), FAR_CORNER)

    lone = rows[12][2 * 8]
    assert lone.glyph == LONE_BLOCK

    border = rows[0][0]  # the top-left corner of MAZE-3's solid ring
    assert border.glyph != LONE_BLOCK
    assert lone.colour is border.colour is Colour.BLUE


# --------------------------------------------------------------------------
# SCRN-4 and SCORE-4: the dots
# --------------------------------------------------------------------------


def test_a_dim_gold_dot_sits_on_every_corridor_square_that_has_one(
    draw: Callable[..., Maze]
) -> None:
    """SCRN-4: *"each dot is a small dim gold square, one to a corridor square"*."""
    maze = draw(".....", at=(6, 10))
    dots = {Position(x, 10) for x in range(6, 11)}
    rows = compose_maze_rows(maze, dots, FAR_CORNER, Position(1, 1))

    for x in range(6, 11):
        cell = rows[10][2 * x]
        assert cell == Cell(DOT_GLYPH, Colour.GOLD), "square ({}, 10)".format(x)


def test_a_corridor_square_whose_dot_was_eaten_shows_nothing(
    draw: Callable[..., Maze]
) -> None:
    """SCRN-4's other half — and SCORE-1's consequence, seen from the screen.

    The dot field is the whole truth about where dots are: a square left out
    of it is blank, not blank-looking.
    """
    maze = draw(".....", at=(6, 10))
    dots = {Position(x, 10) for x in range(6, 11)} - {Position(8, 10)}
    rows = compose_maze_rows(maze, dots, FAR_CORNER, Position(1, 1))

    assert rows[10][2 * 8] == BLANK
    assert rows[10][2 * 7].glyph == DOT_GLYPH


def test_an_actor_standing_on_a_dot_hides_it_without_removing_it(
    draw: Callable[..., Maze]
) -> None:
    """SCORE-4. Three consequences, because "hides without removing" is three claims.

    The square shows the actor and not the dot; the dot field handed in is not
    changed; and stepping off reveals the dot again, which is what proves it
    was still there all along rather than merely not yet redrawn.
    """
    maze = draw(".....", at=(6, 10))
    dots = {Position(x, 10) for x in range(6, 11)}
    dots_as_given = set(dots)  # type: Set[Position]
    standing_on = Position(8, 10)

    rows = compose_maze_rows(maze, dots, standing_on, Position(1, 1))
    assert rows[10][2 * 8] == Cell(PLAYER_GLYPHS[1], Colour.YELLOW)

    assert dots == dots_as_given, "the composer changed the caller's dot field"

    after = compose_maze_rows(maze, dots, Position(6, 10), Position(1, 1))
    assert after[10][2 * 8] == Cell(DOT_GLYPH, Colour.GOLD)


# --------------------------------------------------------------------------
# SCRN-5 and END-4: the actors
# --------------------------------------------------------------------------


def test_the_player_and_the_ghost_differ_in_both_glyph_and_colour(
    draw: Callable[..., Maze]
) -> None:
    """SCRN-5: *"told apart by colour and by outline"* — so both must differ.

    Their centre cells are the same solid block, which is why the comparison
    is over all three cells: the *outline* is what the flanking half-blocks
    and quadrants make, and a test that looked only at the square's own column
    would pass on two actors that were identical in shape.
    """
    maze = draw(".....", at=(6, 10))
    maze = maze.with_corridors_at([Position(x, 20) for x in range(6, 11)])
    rows = compose_maze_rows(maze, [], Position(8, 10), Position(8, 20))

    player = tuple(rows[10][2 * 8 - 1 : 2 * 8 + 2])
    ghost = tuple(rows[20][2 * 8 - 1 : 2 * 8 + 2])

    assert tuple(cell.glyph for cell in player) != tuple(cell.glyph for cell in ghost)
    assert {cell.colour for cell in player} == {Colour.YELLOW}
    assert {cell.colour for cell in ghost} == {Colour.PINK}


def test_each_actor_is_three_cells_wide(draw: Callable[..., Maze]) -> None:
    """The measured fact from the specimen, as a property of the composer.

    The player's block sits at columns 19, 20, 21 in the picture and the
    ghost's at 1, 2, 3 — the square's own column plus the connector either
    side.
    """
    maze = draw(".....", at=(6, 10))
    rows = compose_maze_rows(maze, [], Position(8, 10), Position(1, 1))

    assert tuple(cell.glyph for cell in rows[10][15:18]) == PLAYER_GLYPHS
    assert rows[10][14] == BLANK
    assert rows[10][18] == BLANK


def test_when_both_actors_are_on_one_square_the_ghost_is_what_you_see(
    draw: Callable[..., Maze]
) -> None:
    """END-4, on all three cells.

    The ghost goes down last so that the final picture of a loss shows what
    happened. Asserting only the centre cell would pass on a composer that
    drew the ghost's block over the player's but left the player's yellow
    half-blocks showing either side of it.
    """
    maze = draw(".....", at=(6, 10))
    together = Position(8, 10)
    rows = compose_maze_rows(maze, [], together, together)

    cells = tuple(rows[10][2 * 8 - 1 : 2 * 8 + 2])
    assert tuple(cell.glyph for cell in cells) == GHOST_GLYPHS
    assert {cell.colour for cell in cells} == {Colour.PINK}


def test_a_three_cell_actor_never_overwrites_a_wall_glyph(specimen) -> None:
    """The measured fact the three-cell actor rests on, checked everywhere.

    A connector beside a corridor square is always blank, because a horizontal
    wall join needs walls on *both* sides — so an actor, which always stands
    on a corridor, cannot reach a wall cell. Checked by standing the player on
    every one of the specimen's 264 corridor squares in turn and requiring the
    set of blue cells to come out identical each time.
    """
    reference = compose_maze_rows(
        specimen.maze, [], specimen.player, specimen.ghost
    )
    blue = {
        (y, x)
        for y, row in enumerate(reference)
        for x, cell in enumerate(row)
        if cell.colour is Colour.BLUE
    }
    assert len(blue) > 400, "the reference picture has almost no walls in it"

    for square in specimen.maze.corridors():
        rows = compose_maze_rows(specimen.maze, [], square, specimen.ghost)
        here = {
            (y, x)
            for y, row in enumerate(rows)
            for x, cell in enumerate(row)
            if cell.colour is Colour.BLUE
        }
        assert here == blue, "the player at {} covered a wall cell".format(square)
