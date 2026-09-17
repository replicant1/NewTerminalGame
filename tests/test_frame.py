"""WI-4 — what the picture is, for rows 0 to 28.

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
what a :class:`Field` and a :class:`Cell` are and refuse to be (WI-5 owns
those and ``tests/test_field.py`` pins them), the colours themselves (WI-5's
``tests/test_palette.py``), and the content of row 29 (WI-12 — this module
places it and reads nothing of it).

**WI-4b changed the data type under every test in this file** — from a tuple
of tuples with a colour enum to WI-5's ``Field`` with ``#rrggbb`` — and the
two that matter most survived it unchanged in intent: the specimen
reproduction and the 264-square actor check. They are what prove the composer
still draws the right picture after the migration.
"""

from __future__ import annotations

from typing import Callable, List, Set

import pytest

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.presentation import palette
from terminal_game.presentation.field import EMPTY_CELL, Cell, Field
from terminal_game.presentation.frame import (
    CONNECTOR_GLYPH,
    DOT_GLYPH,
    GHOST_GLYPHS,
    MAZE_COLUMNS,
    MAZE_ROWS,
    PLAYER_GLYPHS,
    RIGHT_MARGIN,
    STATUS_ROW,
    compose_frame,
    compose_maze_rows,
)
from terminal_game.presentation.metrics import COLUMNS, ROWS
from terminal_game.presentation.wall_glyphs import LONE_BLOCK

#: A row 29 that is obviously not WI-4's: this module must place it and read
#: nothing of it, so the tests hand it something no composer would produce.
SENTINEL_STATUS_ROW = [Cell("~", palette.STATUS) for _ in range(COLUMNS)]

#: Somewhere out of the way to park an actor when a test is about the other
#: one. Corridor squares are carved explicitly by the tests that use it.
FAR_CORNER = Position(17, 27)


def _maze_text(field: Field) -> List[str]:
    """Rows 0 to 28 of a composed field, one string per row."""
    return [field.row_text(row) for row in range(MAZE_ROWS)]


# --------------------------------------------------------------------------
# The shape of the field: WIN-2 and SCRN-1
# --------------------------------------------------------------------------


def test_the_composer_returns_the_field_the_surface_paints(sound_maze: Maze) -> None:
    """WI-4b's whole point: one data type across the Presentation seam.

    ``surface.present`` takes a :class:`Field`, so that is what the composer
    has to produce. Before WI-4b it produced a tuple of tuples of its own
    ``Cell``, and the two could not be joined at all.
    """
    field = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert isinstance(field, Field)
    assert isinstance(field[0, 0], Cell)


def test_what_the_composer_returns_is_what_the_painter_imports(
    sound_maze: Maze,
) -> None:
    """An architecture guard on the seam WI-4b exists to create.

    Comparing against the class ``surface`` itself imported, rather than
    against the one this test imported, is the point: if either module is
    ever pointed at a different ``Field``, the two halves of Presentation
    drift apart again silently and everything else here still passes. That is
    exactly how WI-4 and WI-5 came to have two of everything.

    It does not build a surface — no window is involved, and the join proper
    is WI-7's to assert.
    """
    from terminal_game.presentation import surface

    field = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert isinstance(field, surface.Field)
    assert surface.Field is Field
    assert surface.Cell is Cell


def test_the_maze_occupies_rows_nought_to_twentyeight(sound_maze: Maze) -> None:
    """SCRN-1: *"the top 29 rows show the maze"*, and there are 29 of them."""
    assert MAZE_ROWS == HEIGHT == 29
    assert STATUS_ROW == ROWS - 1 == 29


def test_composing_the_maze_leaves_row_twentynine_alone(sound_maze: Maze) -> None:
    """SCRN-1's other half. WI-4 does not write the status row; WI-12 owns it.

    A field is always 40 x 30, so the row exists — it must come back blank
    rather than half-drawn.
    """
    field = compose_maze_rows(sound_maze, [], Position(5, 5), Position(6, 5))
    assert field.row_text(STATUS_ROW) == " " * COLUMNS
    assert all(field[column, STATUS_ROW] == EMPTY_CELL for column in range(COLUMNS))


def test_row_twentynine_is_exactly_what_was_handed_in(sound_maze: Maze) -> None:
    """The WI-4 / WI-12 seam.

    WI-4 places row 29 and owns nothing of its content, so the test hands in a
    row no composer would ever produce and requires it back cell for cell.
    """
    field = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert [field[column, STATUS_ROW] for column in range(COLUMNS)] == (
        SENTINEL_STATUS_ROW
    )
    assert field.row_text(STATUS_ROW) == "~" * COLUMNS


def test_placing_the_status_row_disturbs_nothing_above_it(sound_maze: Maze) -> None:
    """The maze rows are the same whether or not a status row is placed."""
    without = compose_maze_rows(sound_maze, [], Position(5, 5), Position(6, 5))
    with_status = compose_frame(
        sound_maze, [], Position(5, 5), Position(6, 5), SENTINEL_STATUS_ROW
    )
    assert _maze_text(with_status) == _maze_text(without)


def test_a_status_row_of_the_wrong_width_is_refused(sound_maze: Maze) -> None:
    """A short row would leave the tail of row 29 showing whatever was under it."""
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
    row = compose_maze_rows(maze, [], Position(1, 14), FAR_CORNER).row_text(14)

    assert row.count(LONE_BLOCK) == 1
    assert row[2 * 9] == LONE_BLOCK
    assert row.index(LONE_BLOCK) == 18


def test_the_maze_spans_thirtyseven_columns_and_leaves_three_blank() -> None:
    """MAZE-1's *"narrow blank margin down the right-hand edge"*, as arithmetic."""
    assert MAZE_COLUMNS == 2 * WIDTH - 1 == 37
    assert RIGHT_MARGIN == COLUMNS - MAZE_COLUMNS == 3


def test_nothing_is_ever_drawn_in_the_right_hand_margin(specimen) -> None:
    """The three margin columns stay black ground on every maze row."""
    field = compose_maze_rows(
        specimen.maze, specimen.dots, specimen.player, specimen.ghost
    )
    for row in range(MAZE_ROWS):
        for column in range(MAZE_COLUMNS, COLUMNS):
            assert field[column, row] == EMPTY_CELL, "({}, {})".format(column, row)


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
    composed = _maze_text(
        compose_maze_rows(
            specimen.maze, specimen.dots, specimen.player, specimen.ghost
        )
    )
    assert composed == [row.ljust(COLUMNS) for row in specimen.maze_rows]


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


def test_every_wall_cell_of_the_specimen_is_the_wall_colour(specimen) -> None:
    """SCRN-3: *"the walls are drawn as blue double lines"*.

    Checked over the whole picture rather than one square, because the walls
    are drawn by two separate pieces of code — the squares and the connectors
    between them — and a connector left uncoloured would look right in a
    single-cell test.
    """
    field = compose_maze_rows(
        specimen.maze, specimen.dots, specimen.player, specimen.ghost
    )
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if specimen.maze.is_wall(Position(x, y)):
                assert field[2 * x, y].colour == palette.WALL, "({}, {})".format(x, y)

    connectors = [
        cell for _, _, cell in field.cells() if cell.glyph == CONNECTOR_GLYPH
    ]
    assert connectors
    assert {cell.colour for cell in connectors} == {palette.WALL}


def test_a_lone_block_is_the_same_colour_as_a_line(draw: Callable[..., Maze]) -> None:
    """The ruling's specific point: SCRN-3 names one colour for both.

    *"The walls are drawn as blue double lines … a wall square with no wall
    next to it is drawn as a single blue block."*  One blue, two shapes.
    """
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
    field = compose_maze_rows(maze, [], Position(6, 10), FAR_CORNER)

    lone = field[2 * 8, 12]
    border = field[0, 0]  # the top-left corner of MAZE-3's solid ring

    assert lone.glyph == LONE_BLOCK
    assert border.glyph != LONE_BLOCK
    assert lone.colour == border.colour == palette.WALL


# --------------------------------------------------------------------------
# SCRN-4 and SCORE-4: the dots
# --------------------------------------------------------------------------


def test_a_dim_gold_dot_sits_on_every_corridor_square_that_has_one(
    draw: Callable[..., Maze]
) -> None:
    """SCRN-4: *"each dot is a small dim gold square, one to a corridor square"*."""
    maze = draw(".....", at=(6, 10))
    dots = {Position(x, 10) for x in range(6, 11)}
    field = compose_maze_rows(maze, dots, FAR_CORNER, Position(1, 1))

    for x in range(6, 11):
        assert field[2 * x, 10] == Cell(DOT_GLYPH, palette.DOT), "({}, 10)".format(x)


def test_a_corridor_square_whose_dot_was_eaten_shows_nothing(
    draw: Callable[..., Maze]
) -> None:
    """SCRN-4's other half — and SCORE-1's consequence, seen from the screen.

    The dot field is the whole truth about where dots are: a square left out
    of it is blank, not blank-looking.
    """
    maze = draw(".....", at=(6, 10))
    dots = {Position(x, 10) for x in range(6, 11)} - {Position(8, 10)}
    field = compose_maze_rows(maze, dots, FAR_CORNER, Position(1, 1))

    assert field[2 * 8, 10] == EMPTY_CELL
    assert field[2 * 7, 10].glyph == DOT_GLYPH


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

    field = compose_maze_rows(maze, dots, standing_on, Position(1, 1))
    assert field[2 * 8, 10] == Cell(PLAYER_GLYPHS[1], palette.PLAYER)

    assert dots == dots_as_given, "the composer changed the caller's dot field"

    after = compose_maze_rows(maze, dots, Position(6, 10), Position(1, 1))
    assert after[2 * 8, 10] == Cell(DOT_GLYPH, palette.DOT)


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
    maze = draw(".....", at=(6, 10)).with_corridors_at(
        [Position(x, 20) for x in range(6, 11)]
    )
    field = compose_maze_rows(maze, [], Position(8, 10), Position(8, 20))

    player = [field[column, 10] for column in range(15, 18)]
    ghost = [field[column, 20] for column in range(15, 18)]

    assert [cell.glyph for cell in player] != [cell.glyph for cell in ghost]
    assert {cell.colour for cell in player} == {palette.PLAYER}
    assert {cell.colour for cell in ghost} == {palette.GHOST}


def test_each_actor_is_three_cells_wide(draw: Callable[..., Maze]) -> None:
    """The measured fact from the specimen, as a property of the composer.

    The player's block sits at columns 19, 20, 21 in the picture and the
    ghost's at 1, 2, 3 — the square's own column plus the connector either
    side.
    """
    maze = draw(".....", at=(6, 10))
    field = compose_maze_rows(maze, [], Position(8, 10), Position(1, 1))

    assert [field[column, 10].glyph for column in range(15, 18)] == list(
        PLAYER_GLYPHS
    )
    assert field[14, 10] == EMPTY_CELL
    assert field[18, 10] == EMPTY_CELL


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
    field = compose_maze_rows(maze, [], together, together)

    cells = [field[column, 10] for column in range(15, 18)]
    assert [cell.glyph for cell in cells] == list(GHOST_GLYPHS)
    assert {cell.colour for cell in cells} == {palette.GHOST}


def test_a_three_cell_actor_never_overwrites_a_wall_glyph(specimen) -> None:
    """The measured fact the three-cell actor rests on, checked everywhere.

    A connector beside a corridor square is always blank, because a horizontal
    wall join needs walls on *both* sides — so an actor, which always stands
    on a corridor, cannot reach a wall cell. Checked by standing the player on
    every one of the specimen's 264 corridor squares in turn and requiring the
    set of wall-coloured cells to come out identical each time.
    """
    reference = compose_maze_rows(
        specimen.maze, [], specimen.player, specimen.ghost
    )
    walls = {
        (column, row)
        for column, row, cell in reference.cells()
        if cell.colour == palette.WALL
    }
    assert len(walls) > 400, "the reference picture has almost no walls in it"

    for square in specimen.maze.corridors():
        field = compose_maze_rows(specimen.maze, [], square, specimen.ghost)
        here = {
            (column, row)
            for column, row, cell in field.cells()
            if cell.colour == palette.WALL
        }
        assert here == walls, "the player at {} covered a wall cell".format(square)
