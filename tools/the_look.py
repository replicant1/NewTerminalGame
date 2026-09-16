# -*- coding: utf-8 -*-
"""WI-16 — the look, seen: the real colours and glyphs, in front of a person.

    /usr/bin/python3 tools/the_look.py                  # all three views, 8s each
    /usr/bin/python3 tools/the_look.py --view joinery   # just one
    /usr/bin/python3 tools/the_look.py --sizes 14,16,18,20
    /usr/bin/python3 tools/the_look.py --seconds 3 --json

**This is not a test and it cannot be collected as one.** Its name does not
match ``test_*``. What the suite imports is the pure half of this module —
the three frame builders and the option parsing — which name no toolkit and
open nothing.

Why it exists
-------------
Three questions on this project cannot be closed by measurement, and WI-16 is
where they get asked properly:

* **SCRN-3** — do the blue double lines *join up*?  I measured in WI-2 that
  all 113 glyphs share one advance in Menlo, so they are in the right
  *places*; whether the strokes meet is about the shapes and only an eye can
  settle it.  **Do not infer it from the advance measurement.**
* **A4** — is the type large enough to read comfortably?
* **A1** — does the titlebar read exactly *Terminal Game*?

The three views
---------------
``game``
    A real generated maze, composed by the real composer with the real
    status line.  What the player will actually see.
``joinery``
    Every wall junction at once — corners, tees, crossings and straights in
    a lattice — so the eye can check the joins in one place instead of
    hunting round a maze.  **Derived from WI-8's ``wall_layer``**, not
    hand-drawn: this module declares no wall glyph.
``colours``
    The five colours side by side with the thing each belongs to, so
    "can you tell the player from the ghost" is answerable at a glance.

Window hygiene — section 4 of the plan, in full
------------------------------------------------
* The quit is scheduled on the toolkit's own scheduler **before** the event
  loop is entered, so it never depends on anybody pressing anything.  There
  is no ``mainloop`` here without a way out.
* Each window is reaped in a ``finally``, so a failure anywhere still takes
  it away, and the next view does not open until the last one is confirmed
  gone.
* Only ever the handle captured at the moment of creation.  Never "the front
  window", never by title.
* The window belongs to this process, so there is no second application left
  holding one and no modal sheet for anybody to dismiss.
"""

from __future__ import annotations

import functools
import json
import os
import random
import sys

if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.domain.game_state import Outcome
from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.domain.opening_position import opening_position
from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    MAZE_ROWS,
    Colour,
    FrameBuilder,
)
from terminal_game.presentation.frame_composer import (
    DOT_GLYPH,
    GHOST_MOTIF,
    PLAYER_MOTIF,
    compose_frame,
)
from terminal_game.presentation.status_line import status_row
from terminal_game.presentation.wall_glyphs import wall_layer

#: How long each view stays up if nobody presses anything.  Long enough to
#: look properly at a maze; short enough that a forgotten run goes away.
DEFAULT_SECONDS = 8

#: The views, in the order a person should see them.
VIEWS = ("game", "joinery", "colours")

#: The seed whose maze is shown by the ``game`` view.  Fixed so that two
#: people looking at "the picture" are looking at the same picture.
GAME_SEED = 4


def lattice_maze(width: int = 19, height: int = 29) -> Maze:
    """A maze of nothing but wall lines, one corridor square in each pocket.

    Wall wherever the row or the column is even, which puts a junction at
    every crossing of the lattice.  Its wall layer therefore contains every
    glyph WI-8 can produce, including the crossing the specimen picture
    happens not to contain.
    """
    rows = [
        "".join(
            "#" if (column % 2 == 0 or row % 2 == 0) else "."
            for column in range(width)
        )
        for row in range(height)
    ]
    return Maze.from_text("\n".join(rows))


@functools.lru_cache(maxsize=8)
def game_frame(seed: int = GAME_SEED):
    """A real game, composed exactly as the player will see it.

    Cached because generating a maze that satisfies MAZE-4, MAZE-5 and
    MAZE-6 is the expensive thing in this module and the picture for a given
    seed never changes.  A frame is immutable, so sharing one is safe.
    """
    state = opening_position(generate_maze(random.Random(seed)))
    return compose_frame(
        state, status_row(state.score.points, state.outcome)
    )


@functools.lru_cache(maxsize=1)
def joinery_frame():
    """Every wall junction at once, for SCRN-3.

    The glyphs come from WI-8's ``wall_layer`` and are never named here.
    """
    builder = FrameBuilder()
    for row, cells in enumerate(wall_layer(lattice_maze())):
        for column, cell in enumerate(cells):
            if cell.glyph != " ":
                builder.set_cell(row, column, cell.glyph, cell.colour)
    builder.place_row(
        MAZE_ROWS, status_row(0, Outcome.UNDECIDED)
    )
    return builder.build()


@functools.lru_cache(maxsize=1)
def colour_frame():
    """The five colours, each beside the thing it belongs to.

    Row 29 is the *real* status line, so the cyan on show is the cyan the
    game uses rather than a sample of it.
    """
    builder = FrameBuilder()
    samples = (
        ("wall", "═════", Colour.WALL_BLUE),
        ("dot", DOT_GLYPH * 5, Colour.DOT_GOLD),
        ("you", PLAYER_MOTIF, Colour.PLAYER_YELLOW),
        ("ghost", GHOST_MOTIF, Colour.GHOST_PINK),
    )
    row = 2
    for label, sample, colour in samples:
        # The label is in the thing's own colour too, so the eye compares
        # letters as well as blocks — a hue that reads well as a solid block
        # can still be unreadable as text.
        builder.write(row, 2, label.ljust(7), colour)
        builder.write(row, 11, sample, colour)
        row += 3
    builder.write(
        row + 1, 2, "the two actors differ in shape", Colour.GHOST_PINK
    )
    builder.write(
        row + 3, 2, "as well as colour - SCRN-5", Colour.PLAYER_YELLOW
    )
    builder.place_row(MAZE_ROWS, status_row(0, Outcome.UNDECIDED))
    return builder.build()


#: The three views, by name.
FRAME_FOR_VIEW = {
    "game": game_frame,
    "joinery": joinery_frame,
    "colours": colour_frame,
}


class Options:
    """What a run was asked to do.  A value, so it can be asserted."""

    def __init__(self, views, sizes, seconds, quiet):
        self.views = tuple(views)
        self.sizes = tuple(sizes)
        self.seconds = seconds
        self.quiet = quiet

    def __eq__(self, other):
        if not isinstance(other, Options):
            return NotImplemented
        return (
            self.views == other.views
            and self.sizes == other.sizes
            and self.seconds == other.seconds
            and self.quiet == other.quiet
        )

    def __repr__(self):
        return "Options(views={0}, sizes={1}, seconds={2}, quiet={3})".format(
            self.views, self.sizes, self.seconds, self.quiet
        )

    @property
    def windows(self) -> int:
        """How many windows this run will open, one per view per size."""
        return len(self.views) * len(self.sizes)


def parse_options(argv) -> Options:
    """Read the command line, refusing anything unbounded.

    A run with no deadline is the one thing this tool must never do, so a
    non-positive ``--seconds`` is refused here rather than discovered when a
    window will not go away.
    """
    from terminal_game.shell.grid_surface import FONT_POINT_SIZE

    argv = list(argv)
    views = list(VIEWS)
    sizes = [FONT_POINT_SIZE]
    seconds = DEFAULT_SECONDS
    quiet = "--json" in argv

    if "--view" in argv:
        asked = argv[argv.index("--view") + 1]
        views = [v for v in asked.split(",") if v]
        unknown = [v for v in views if v not in FRAME_FOR_VIEW]
        if unknown:
            raise ValueError(
                "no such view: {0}. Known views: {1}".format(
                    ", ".join(unknown), ", ".join(VIEWS)
                )
            )
    if "--sizes" in argv:
        sizes = [int(s) for s in argv[argv.index("--sizes") + 1].split(",") if s]
        if not sizes:
            raise ValueError("--sizes needs at least one point size")
        if any(size <= 0 for size in sizes):
            raise ValueError("a font size must be positive")
    if "--seconds" in argv:
        seconds = int(argv[argv.index("--seconds") + 1])
    if seconds <= 0:
        raise ValueError(
            "--seconds must be positive: this tool never opens a window "
            "without a deadline"
        )
    if not views:
        raise ValueError("--view needs at least one view")
    return Options(views, sizes, seconds, quiet)


THE_THREE_QUESTIONS = (
    "1. SCRN-3 - do the blue double lines JOIN UP cleanly into corners, tees "
    "and crossings, or is there a hairline gap between cells?",
    "2. A4 - is the type large enough to read comfortably?",
    "3. A1 - does the titlebar read exactly 'Terminal Game'?",
)


# ---------------------------------------------------------------------------
# Everything below here touches the real toolkit and the real screen.
# ---------------------------------------------------------------------------


def _still_there(target) -> bool:  # pragma: no cover - needs a real widget
    """Is the window we created still in existence?

    Asked of the handle captured at creation and no other.  A destroyed Tk
    widget raises rather than answering, which is itself the answer.
    """
    if target is None:
        return False
    try:
        return bool(target.winfo_exists())
    except Exception:
        return False


def show(view, point_size, seconds, findings):  # pragma: no cover - opens a window
    """Open one window, paint one view, and reap it.

    Returns only once the window is gone.  Everything about this function is
    arranged so that it cannot leave one behind: the deadline is scheduled
    before the loop is entered, and the reap is in a ``finally``.
    """
    from terminal_game.shell import tk_grid
    from terminal_game.shell.grid_surface import pixel_size_for
    from terminal_game.shell.tk_toolkit import TkToolkit
    from terminal_game.shell.window_owner import WindowOwner

    class Nobody:
        """The window owner needs a collaborator; nothing here plays."""

        def on_tick(self):
            pass

        def on_key(self, key):
            if key.keysym in ("q", "Q"):
                owner.end_session()

    metrics = tk_grid.measure_metrics(point_size=point_size)
    toolkit = TkToolkit()
    owner = WindowOwner(toolkit, pixel_size_for(metrics), Nobody())

    target = None
    record = {
        "view": view,
        "point_size": point_size,
        "cell_width_px": metrics.width,
        "cell_height_px": metrics.height,
        "window_px": list(pixel_size_for(metrics)),
        "error": None,
    }
    try:
        target = owner.open()
        surface = tk_grid.surface_on(target, metrics, point_size=point_size)
        surface.paint(FRAME_FOR_VIEW[view]())
        root = target.winfo_toplevel()

        def measure():
            record.update({
                "title_read_back": root.title(),
                "canvas_items": len(target.find_all()),
                "canvas_item_kinds": sorted(
                    {target.type(item) for item in target.find_all()}
                ),
            })

        toolkit.schedule_once(400, measure)
        toolkit.schedule_once(seconds * 1000, owner.end_session)
        owner.run()
    except BaseException as exc:
        record["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        owner.end_session()
        record["window_reaped"] = not _still_there(target)

    findings["views"].append(record)
    return record


def main(argv) -> int:  # pragma: no cover - measured by running it
    try:
        options = parse_options(argv)
    except ValueError as error:
        print("the_look: {0}".format(error), file=sys.stderr)
        return 2

    findings = {
        "asked_for": {
            "views": list(options.views),
            "sizes": list(options.sizes),
            "seconds_each": options.seconds,
            "windows": options.windows,
        },
        "views": [],
    }

    if not options.quiet:
        print(
            "Opening {0} window(s), up to {1}s each. Press q to move on "
            "sooner; each closes itself either way.\n".format(
                options.windows, options.seconds
            )
        )
        for question in THE_THREE_QUESTIONS:
            print("  " + question)
        print()

    for point_size in options.sizes:
        for view in options.views:
            if not options.quiet:
                print("  showing {0} at {1}pt...".format(view, point_size))
            record = show(view, point_size, options.seconds, findings)
            if not record["window_reaped"]:
                print(
                    "the_look: a window was NOT reaped; stopping rather than "
                    "opening another.",
                    file=sys.stderr,
                )
                break

    findings["all_windows_reaped"] = all(
        v.get("window_reaped") for v in findings["views"]
    )
    findings["errors"] = [v["error"] for v in findings["views"] if v["error"]]
    print(json.dumps(findings, indent=2, sort_keys=True))
    return 1 if findings["errors"] or not findings["all_windows_reaped"] else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
