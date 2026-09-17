"""WI-14 — the seams of the assembled game, and nothing either side of them.

This module decides nothing, so these tests prove nothing about rules. That a
maze is sound is WI-2's; that a move is legal is WI-10's; that Decided
ignores a tick is WI-11's; that ``q`` means quit is WI-13's; that the picture
is right is WI-4b's; that a canvas shows what it was given is WI-5's. **What
is asserted here is that those things are connected to each other**, and the
temptation to re-prove them through a bigger object is exactly what the plan
warns WI-14 against.

So the joins, one test each: a key reaches the resolver; a completed turn
reaches the glass; the timer calls the tick at the named cadence; the random
source reaches both the generator and the ghost; quitting closes the window
and closing the window quits.

**Nothing here puts a window on the screen** except the one class marked
``needs_window``. A ``GameWindow`` is withdrawn until ``show()``, and
``tick()`` is public, so a whole game runs with no real time passing and
nothing to see.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pytest

from terminal_game.application.session import Phase
from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.domain.state import Outcome
from terminal_game.domain.structure import check
from terminal_game.presentation import frame as frame_module
from terminal_game.presentation import status as status_module
from terminal_game.presentation import surface as surface_module
from terminal_game.presentation.metrics import COLUMNS, ROWS
from terminal_game.shell import game as game_module
from terminal_game.shell.game import CADENCE_MS, Game, build_game

CENTRE_ROW = HEIGHT // 2


class RecordingScheduler:
    """A clock that never advances unless a test says so.

    The plan asks for the timer to be injectable *"so the game can be driven
    from a test without waiting"*. This is that: it records what was asked
    for and fires it on demand, so a test can assert **what interval was
    requested** as well as what happened when it elapsed.
    """

    def __init__(self) -> None:
        self.requested = []  # type: List[int]
        self.cancelled = []  # type: List[str]
        self._pending = None  # type: Optional[Tuple[str, Callable[[], None]]]
        self._issued = 0

    def after(self, milliseconds: int, callback: "Callable[[], None]") -> str:
        self._issued += 1
        handle = "handle-{}".format(self._issued)
        self.requested.append(milliseconds)
        self._pending = (handle, callback)
        return handle

    def cancel(self, handle: str) -> None:
        self.cancelled.append(handle)
        self._pending = None

    def fire(self) -> None:
        """Let the scheduled beat happen. Raises if nothing is scheduled.

        The pending entry is cleared **before** the callback runs, because
        Tk's ``after`` is one-shot: a callback that has fired is no longer
        scheduled, and it is the callback itself that asks for the next one.
        A double that kept it would report a timer as still pending after the
        game had deliberately stopped rescheduling — which is a false pass on
        exactly the test that matters most here.
        """
        if self._pending is None:
            raise AssertionError("nothing is scheduled; the timer has stopped")
        _, callback = self._pending
        self._pending = None
        callback()

    @property
    def has_pending(self) -> bool:
        return self._pending is not None


def open_corridor() -> Maze:
    """A maze with one long corridor straight through the centre row.

    Hand-built so a test knows where the player starts and which way it can
    go: WI-8 puts the player on the corridor square nearest the grid centre,
    and on this board that is exactly ``(9, 14)`` with clear ground east.
    """
    return Maze.all_walls().with_corridors_at(
        [Position(x, CENTRE_ROW) for x in range(1, WIDTH - 1)]
    )


def corridor_game(master, scheduler=None) -> Game:
    return build_game(master=master, seed=1, maze=open_corridor(), scheduler=scheduler)


# --------------------------------------------------------------------------
# The fixture is what this file thinks it is
# --------------------------------------------------------------------------


def test_the_hand_built_board_puts_the_player_where_the_tests_assume(tk_root) -> None:
    """A guard. Every join test below moves east from a known square.

    If WI-8 ever placed the player somewhere else on this board, the move
    tests would be asserting against a wall and would fail for a reason that
    had nothing to do with the join.
    """
    game = corridor_game(tk_root)
    try:
        assert game.state.player == Position(9, CENTRE_ROW)
        assert game.state.maze.is_corridor(Position(10, CENTRE_ROW))
        assert game.state.has_dot_at(Position(10, CENTRE_ROW))
    finally:
        game.window.close()


# --------------------------------------------------------------------------
# START-5 — under way before anything is pressed
# --------------------------------------------------------------------------


def test_the_first_frame_is_painted_and_the_timer_running_before_any_key(
    tk_root,
) -> None:
    """START-5: *"the ghost is already moving, and nothing has to be pressed"*.

    Both halves in one place, because the requirement is one sentence: there
    is a picture, and there is a beat pending, and neither waited for input.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        assert game.field is None
        assert not scheduler.has_pending

        game.start()

        assert game.field is not None
        assert game.timer_is_running
        assert scheduler.has_pending
        assert not game.window.is_on_screen()
    finally:
        game.window.close()


def test_starting_twice_does_not_double_the_ghosts_speed(tk_root) -> None:
    """An entry point and a test could each call ``start``; only one timer.

    Two pending beats would move the ghost twice per cadence, which is a
    GHOST-1 violation that would be very hard to see.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        game.start()
        assert scheduler.requested == [CADENCE_MS]
    finally:
        game.window.close()


# --------------------------------------------------------------------------
# GHOST-1 — the timer, and the named cadence
# --------------------------------------------------------------------------


def test_ghost_1_the_ghost_moves_on_the_timer_with_no_key_at_all(tk_root) -> None:
    """**GHOST-1**: *"whether or not the player is moving."*

    The join: the scheduler's callback reaches the session's tick. No key is
    sent in this test at all, and the ghost still moves.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        before = game.state.ghost

        scheduler.fire()

        assert game.state.ghost != before
    finally:
        game.window.close()


def test_ghost_1_the_interval_asked_for_is_the_named_cadence(tk_root) -> None:
    """**GHOST-1**: *"moving one square at a time about seven times a second."*

    Assumption P6 fixes "about" at 143 ms. The assertion is against
    :data:`CADENCE_MS` and not against a literal, so that WI-19 changing the
    constant changes this test's meaning rather than breaking it — with one
    separate line pinning the constant's current value, which is the thing
    P6 actually chose.

    Named after the requirement because lane B found GHOST-1 was the one code
    with no test naming it anywhere: a cadence inlined into an ``after()``
    call is a requirement nobody can audit.

    Asserted on every beat, not just the first, because a reschedule that
    used a different interval would drift after the first tick only.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        for _ in range(5):
            scheduler.fire()

        assert scheduler.requested == [CADENCE_MS] * 6
        assert CADENCE_MS == 143
    finally:
        game.window.close()


def test_the_timer_keeps_going_by_itself(tk_root) -> None:
    """Each beat asks for the next, so the ghost keeps moving.

    A timer that fired once would pass every single-tick test above.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        walk = []  # type: List[Position]
        for _ in range(4):
            scheduler.fire()
            walk.append(game.state.ghost)

        assert len(set(walk)) > 1, "the ghost went nowhere over four beats"
        assert scheduler.has_pending
    finally:
        game.window.close()


def test_the_timer_stops_once_the_game_is_decided(tk_root) -> None:
    """END-5's consequence up here: a beat into a decided game is a beat wasted.

    The session would ignore it — WI-11 pins that — but a timer that went on
    firing for the rest of the process would be a tick that moves nothing,
    forever.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        for _ in range(200):
            if not game.session.accepts_play:
                break
            scheduler.fire()

        assert game.session.phase is Phase.DECIDED, "the fixture never decided"
        assert not scheduler.has_pending
        assert not game.timer_is_running
    finally:
        game.window.close()


# --------------------------------------------------------------------------
# The joins
# --------------------------------------------------------------------------


def test_a_key_event_reaches_the_resolver(tk_root) -> None:
    """The seam WI-13 → WI-11 → WI-10, asserted by its consequence.

    One key in at the top, and the board has changed at the bottom: the
    player moved one square and the dot there was scored.
    """
    game = corridor_game(tk_root)
    try:
        game.start()
        assert game.state.player == Position(9, CENTRE_ROW)
        assert game.state.score == 0

        game.handle_key("Right")

        assert game.state.player == Position(10, CENTRE_ROW)
        assert game.state.score == 1
    finally:
        game.window.close()


def test_a_key_that_means_nothing_changes_nothing(tk_root) -> None:
    """CTRL-5, and the control that makes the test above mean something.

    If every key moved the player, "Right moved the player" would say nothing
    about translation being wired in at all.
    """
    game = corridor_game(tk_root)
    try:
        game.start()
        before = game.state

        for keysym in ("a", "Escape", "F1", "Shift_L", "7", "space"):
            game.handle_key(keysym)
            assert game.state == before, "{!r} changed the board".format(keysym)
    finally:
        game.window.close()


def test_a_completed_turn_reaches_the_glass(tk_root) -> None:
    """The seam WI-4b → WI-5, asserted after a turn rather than at start-up.

    A game that painted its first frame and never repainted would pass a
    start-up check. So the comparison is made *after* a move and *after* a
    tick, and against the whole field.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        first = [game.window.surface.shown_row(r) for r in range(ROWS)]

        game.handle_key("Right")
        scheduler.fire()

        assert game.field is not None
        for row in range(ROWS):
            assert game.window.surface.shown_row(row) == game.field.row_text(row), (
                "row {} on the glass is not the row that was composed".format(row)
            )
        assert [game.window.surface.shown_row(r) for r in range(ROWS)] != first, (
            "the picture never changed; a repaint may not be happening at all"
        )
    finally:
        game.window.close()


def test_row_twentynine_is_what_the_status_module_says_it_is(tk_root) -> None:
    """The seam WI-12 → WI-4b, asserted as the exact string and nothing more.

    WI-12 owns what row 29 says and pins all three forms itself; this asserts
    only that what it says is what is on the row. Nothing here knows the
    literal.
    """
    game = corridor_game(tk_root)
    try:
        game.start()
        expected = status_module.status_for(game.state)

        assert game.field is not None
        assert game.field.row_text(29) == expected.ljust(COLUMNS)

        game.handle_key("Right")
        assert game.field.row_text(29) == status_module.status_for(
            game.state
        ).ljust(COLUMNS)
    finally:
        game.window.close()


# --------------------------------------------------------------------------
# MAZE-4, and the random source reaching both things that need it
# --------------------------------------------------------------------------


def test_a_real_maze_is_generated_at_start_up(tk_root) -> None:
    """The seam WI-2 → WI-8. A guard, not a re-proof of WI-2's properties.

    WI-2's own 200-seed sweep is what establishes that generated mazes are
    sound; this asserts that the assembly actually calls it rather than
    playing something hand-made.
    """
    game = build_game(master=tk_root, seed=99)
    try:
        assert check(game.state.maze).is_sound
        assert game.state.maze != open_corridor()
    finally:
        game.window.close()


def test_the_same_seed_gives_the_same_game_and_a_different_seed_does_not(
    tk_root,
) -> None:
    """MAZE-4, and the join that makes WI-16's journeys possible.

    One random source has to reach **both** the generator and the ghost, or a
    seeded journey would reproduce its maze and then diverge on the first
    junction. So the comparison is over a maze *and* a walk.
    """

    def play(seed: int) -> "Tuple[Tuple[str, ...], List[Position]]":
        game = build_game(master=tk_root, seed=seed)
        try:
            game.start()
            walk = []  # type: List[Position]
            for _ in range(30):
                game.tick()
                walk.append(game.state.ghost)
            return game.state.maze.to_rows(), walk
        finally:
            game.window.close()

    assert play(4) == play(4)
    assert play(4) != play(5)


# --------------------------------------------------------------------------
# WIN-5 — quitting, from either side
# --------------------------------------------------------------------------


def test_quitting_closes_the_window(tk_root) -> None:
    """The seam WI-11 → WI-6: the session ending is what shuts the window."""
    game = corridor_game(tk_root)
    try:
        game.start()
        assert game.window.is_open

        game.handle_key("q")

        assert not game.is_running
        assert not game.window.is_open
    finally:
        game.window.close()


def test_closing_the_window_quits_the_session(tk_root) -> None:
    """The same seam the other way, which nothing else would catch.

    A player who clicks the close button has left the game. If that did not
    reach the session, the session would still be nominally playing when the
    window had gone — and WI-6 wires the close button straight to ``close``,
    so this is the only place that connection is made.
    """
    game = corridor_game(tk_root)
    try:
        game.start()
        assert game.is_running

        game.window.close()

        assert not game.is_running
        assert game.session.phase is Phase.ENDED
    finally:
        game.window.close()


# --------------------------------------------------------------------------
# One vocabulary
# --------------------------------------------------------------------------


def test_the_assembly_the_composer_and_the_painter_share_one_field() -> None:
    """An identity guard, per the section 7 rule.

    The assembly holds every layer at once, so it is the last place a type
    could be pointed somewhere different without a behaviour test noticing.
    """
    assert game_module.Field is frame_module.Field
    assert game_module.Field is surface_module.Field
    assert game_module.Outcome is status_module.Outcome


# --------------------------------------------------------------------------
# The one test on a real screen
# --------------------------------------------------------------------------


@pytest.mark.needs_window
class TestOnTheRealScreen:
    """Excluded from the default suite. Section 1.5 applies without exception.

    Run under a deadline **outside** pytest — an internal timeout does not
    help when a hang is inside ``mainloop``.
    """

    def test_the_real_game_runs_on_a_real_window_and_closes_itself(
        self, tk_root
    ) -> None:
        """The whole game, on the real timer, on a real window.

        This is the only test in the project where the 143 ms cadence is a
        real 143 milliseconds. The watchdog is the only thing that presses
        anything, because nobody is here to press ``q``.
        """
        from terminal_game.shell.game import run_game

        game = run_game(master=tk_root, seed=3, watchdog_ms=900)

        assert not game.window.is_open
        assert game.field is not None
        assert game.state.score >= 0


# --------------------------------------------------------------------------
# WI-14b — the placement WI-15 decided is actually carried out
# --------------------------------------------------------------------------


def test_the_assembled_game_places_its_window_where_wi15_says(tk_root) -> None:
    """WI-14b: the join WI-14 shipped without.

    ``placement.py`` and ``GameWindow.move_to`` were both complete and
    tested, and **nothing in the product called either** — so the running
    game left its window wherever Tk drops a fresh toplevel, measured at
    ``(5, 38)``. The unit tests either side of the gap were green throughout,
    which is why only driving the assembly found it.

    This asserts the wiring and not the decision: where the window goes is
    ``placement_for``'s answer, asked for here rather than recomputed.
    """
    from terminal_game.shell import placement

    game = corridor_game(tk_root)
    try:
        widget = game.window.surface.widget
        display = placement.Rect(
            0, 0, widget.winfo_screenwidth(), widget.winfo_screenheight()
        )
        expected = placement.placement_for(
            placement.no_anchor(), display, game.window.pixel_size
        )

        where = game.place()

        assert where == expected
        assert game.window.position() == expected
    finally:
        game.window.close()


def test_placing_the_window_actually_moves_it(tk_root) -> None:
    """The control. Without it the test above passes on a game that never moved.

    Tk gives a fresh toplevel a position of its own, so ``position()``
    answering something is not evidence that anything placed it — WI-15's
    own docstring says exactly that. The evidence is that the position
    **changed**, and changed to the computed one.
    """
    game = corridor_game(tk_root)
    try:
        before = game.window.position()
        after = game.place()

        assert before != after, (
            "the window was already where placement wanted it, so this test "
            "cannot tell a placed window from an unplaced one"
        )
        assert game.window.position() == after
    finally:
        game.window.close()


def test_placing_the_window_does_not_disturb_its_size(tk_root) -> None:
    """WIN-2 survives WIN-4's attempt.

    A geometry string carrying ``WxH`` would silently overrule the size WI-6
    computed from the cell metrics. WI-15 writes position only; this is the
    assembly checking that what it asked for did not cost it the size.
    """
    game = corridor_game(tk_root)
    try:
        before = game.window.pixel_size
        game.place()
        assert game.window.pixel_size == before == (400, 570)
    finally:
        game.window.close()


def test_the_game_asks_the_anchor_reader_it_was_given(tk_root) -> None:
    """WI-14c: the seam WI-16b needs, and the reason it is on ``build_game``.

    Ground rule 1.6 forbids the default suite from querying the desktop, so
    a placement test cannot use the shipped reader. Without this seam the
    only test of placement would be one marked ``needs_window`` — excluded by
    default, and so unable to catch the very defect WI-14b existed to fix.
    """
    from terminal_game.shell import placement

    class RecordingReader(object):
        def __init__(self, rect):
            self.rect = rect
            self.reads = 0

        def read(self):
            self.reads += 1
            return self.rect

    anchor = placement.Rect(300, 200, 640, 480)
    reader = RecordingReader(anchor)
    game = build_game(
        master=tk_root, seed=1, maze=open_corridor(), anchor_reader=reader
    )
    try:
        where = game.place()

        assert reader.reads >= 1, "the game never asked for an anchor"
        assert where == placement.below_and_right_of(anchor)
        assert game.window.position() == where
    finally:
        game.window.close()


def test_a_different_anchor_puts_the_window_somewhere_different(tk_root) -> None:
    """The control: the game uses the answer rather than merely asking for it.

    A game that asked and then ignored the reply would pass the test above if
    the fallback happened to agree. Two anchors, two positions.
    """
    from terminal_game.shell import placement

    class FixedReader(object):
        def __init__(self, rect):
            self.rect = rect

        def read(self):
            return self.rect

    def place_with(rect):
        game = build_game(
            master=tk_root,
            seed=1,
            maze=open_corridor(),
            anchor_reader=FixedReader(rect),
        )
        try:
            return game.place()
        finally:
            game.window.close()

    first = place_with(placement.Rect(100, 100, 640, 480))
    second = place_with(placement.Rect(500, 400, 640, 480))

    assert first != second


def test_ending_a_game_between_beats_leaves_no_timer_outstanding(tk_root) -> None:
    """The defect WI-20's full run found, pinned where it can run by default.

    A game can end between two beats — a ``q``, or the close button — and
    when it does there is a scheduled beat outstanding that nothing else
    clears: ``_schedule`` only declines to book the *next* one, and it runs
    after a beat rather than after a quit. Left alone, ``timer_is_running``
    goes on reporting ``True`` for a game that is over, and on a shared Tk
    interpreter the pending ``after`` is still live and still fires.

    Lane C found it on a real window in a ``needs_window`` test. This is the
    same fact in the default suite, where it costs nothing to keep.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        assert game.timer_is_running, "nothing was scheduled, so this proves nothing"

        game.handle_key("q")

        assert not game.is_running
        assert not game.timer_is_running
        assert not scheduler.has_pending
        assert scheduler.cancelled, "the scheduled beat was never cancelled"
    finally:
        game.window.close()


def test_closing_the_window_between_beats_also_clears_the_timer(tk_root) -> None:
    """The other way in, which is the one the real entry point takes.

    ``run_game``'s watchdog closes the window rather than sending a key, so a
    fix that only handled the quit intent would leave the real call site
    exactly as it was.
    """
    scheduler = RecordingScheduler()
    game = corridor_game(tk_root, scheduler)
    try:
        game.start()
        assert game.timer_is_running

        game.window.close()

        assert not game.is_running
        assert not game.timer_is_running
    finally:
        game.window.close()
