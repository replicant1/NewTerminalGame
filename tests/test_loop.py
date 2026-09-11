"""The loop, driven by a fake screen and a fake clock.

This file is the whole of the implementation plan's §10.1 ruling. The
architecture says the loop is "not unit-tested" and then traces CTRL-1,
CTRL-2, CTRL-4, CTRL-5, START-5 and END-6 to it; the plan rules that the loop
must be **drivable**, and here it is driven. Nothing in this file touches a
terminal, a clock or a window.

The two fakes are deliberately tiny, and neither of them is a stub that
records calls: the screen keeps the pictures it was given, and the clock is a
number that the *screen* moves on, because in the real thing it is the wait
for a key that makes time pass. Asserting on the pictures and on the state
that comes back is asserting the consequence, not the call.
"""

import random
import unittest

from termgame import controls, loop, standins, ticker
from termgame.model import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Frame,
    GameState,
    Outcome,
    Position,
    frame_from_rows,
)
from termgame import maze as mazelib

# A board small enough to reason about. The player starts in the middle of
# the cross; every corridor cell has at least two ways on.
BOARD = "\n".join(
    [
        "#####",
        "#...#",
        "#.#.#",
        "#...#",
        "#####",
    ]
)


def a_state(player=(1, 1), ghost=(3, 3), dots=(), outcome=Outcome.PLAYING, score=0):
    maze = mazelib.from_text(BOARD)
    return GameState(
        maze=maze,
        player=Position(*player),
        ghost=Position(*ghost),
        ghost_dir=UP,
        dots=frozenset(Position(*d) for d in dots),
        score=score,
        outcome=outcome,
    )


class FakeClock(object):
    """Seconds, as a number somebody else moves on."""

    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeScreen(object):
    """A screen that hands out scripted keys and keeps every picture.

    Reading a key advances the clock by the whole of the timeout it was
    given, which is what a real ``getch`` that times out does. A scripted key
    may instead be a ``(key, seconds)`` pair, for a key that arrives *early* —
    that is the case GHOST-1 and CTRL-2 both turn on.
    """

    def __init__(self, keys, clock):
        self.script = list(keys)
        self.clock = clock
        self.pictures = []
        self.timeouts = []
        self.reads = 0

    def paint(self, frame):
        self.pictures.append(frame)

    def read_key(self, timeout_ms):
        self.timeouts.append(timeout_ms)
        self.reads += 1
        if not self.script:
            raise AssertionError(
                "the loop read past the end of the script after %d reads; "
                "it should have returned" % self.reads
            )
        item = self.script.pop(0)
        if isinstance(item, tuple):
            key, elapsed = item
        else:
            key, elapsed = item, timeout_ms / 1000.0
        self.clock.advance(elapsed)
        return key


def constant_render(state):
    """A picture that says only where the player and the ghost are.

    Small on purpose: a test that compared whole 30 x 40 pictures would be
    asserting WI-3's work, not this loop's.
    """
    return frame_from_rows(["p%d%d g%d%d" % (
        state.player.row, state.player.col, state.ghost.row, state.ghost.col)])


def positions(pictures):
    return [picture.rows()[0] for picture in pictures]


def a_recording_player_move():
    """A player transition that records what it was asked to do."""
    calls = []

    def move(state, direction):
        calls.append(direction)
        return standins.move_player(state, direction)

    return move, calls


def a_recording_ghost_move():
    calls = []

    def move(state, rng):
        calls.append(state.ghost)
        return state

    return move, calls


def a_walking_ghost():
    """A ghost that shuffles one square right each tick, so ticks are visible."""

    def move(state, rng):
        if state.outcome is not Outcome.PLAYING:
            return state
        target = state.ghost.shifted(RIGHT)
        if not state.maze.is_corridor(target):
            target = Position(state.ghost.row, 1)
        return GameState(
            maze=state.maze,
            player=state.player,
            ghost=target,
            ghost_dir=RIGHT,
            dots=state.dots,
            score=state.score,
            outcome=state.outcome,
        )

    return move


def run(keys, state=None, render=constant_render, move_player=None,
        move_ghost=None, tick=1.0, start=0.0):
    """Drive the loop with a script, and hand back everything it did."""
    clock = FakeClock(start)
    screen = FakeScreen(keys, clock)
    if move_player is None:
        move_player = standins.move_player
    if move_ghost is None:
        move_ghost = standins.move_ghost
    final = loop.run_loop(
        screen,
        a_state() if state is None else state,
        render,
        move_player,
        move_ghost,
        random.Random(0),
        clock=clock,
        tick=tick,
    )
    return final, screen, clock


QUIT = ord("q")


class QuittingTest(unittest.TestCase):
    """CTRL-4 and END-6 — `q` quits at once, and is the only way out."""

    def test_a_quit_key_returns_from_the_loop(self):
        final, screen, _ = run([QUIT])
        self.assertEqual(a_state(), final)
        self.assertEqual(1, screen.reads)

    def test_an_upper_case_q_quits_too(self):
        _, screen, _ = run([ord("Q")])
        self.assertEqual(1, screen.reads)

    def test_quitting_does_not_apply_a_transition_first(self):
        move, calls = a_recording_player_move()
        ghost, ghost_calls = a_recording_ghost_move()
        run([QUIT], move_player=move, move_ghost=ghost)
        self.assertEqual([], calls)
        self.assertEqual([], ghost_calls)

    def test_quitting_does_not_paint_again_on_the_way_out(self):
        # The last picture the player saw is the one that stays on the screen
        # while the window closes.
        _, screen, _ = run([QUIT])
        self.assertEqual(1, len(screen.pictures))

    def test_a_finished_game_does_not_return_on_its_own(self):
        # END-6: an ending is not a way out. Ten ticks and ten arrow presses
        # against a game that is already lost, and the loop is still running.
        lost = a_state(outcome=Outcome.CAUGHT)
        keys = [None, controls.KEY_UP] * 10 + [QUIT]
        final, screen, _ = run(keys, state=lost)
        self.assertEqual(lost, final)
        self.assertEqual(21, screen.reads)

    def test_the_loop_returns_the_state_it_ended_on(self):
        state = a_state(player=(1, 1), dots=[(1, 2)])
        final, _, _ = run([controls.KEY_RIGHT, QUIT], state=state)
        self.assertEqual(Position(1, 2), final.player)
        self.assertEqual(1, final.score)


class PaintBeforeTheFirstReadTest(unittest.TestCase):
    """START-5 — the game is under way the moment the window opens."""

    def test_a_picture_is_painted_before_the_first_key_is_read(self):
        order = []
        clock = FakeClock(0.0)

        class Watching(FakeScreen):
            def paint(self, frame):
                order.append("paint")
                FakeScreen.paint(self, frame)

            def read_key(self, timeout_ms):
                order.append("read")
                return FakeScreen.read_key(self, timeout_ms)

        screen = Watching([QUIT], clock)
        loop.run_loop(
            screen,
            a_state(),
            constant_render,
            standins.move_player,
            standins.move_ghost,
            random.Random(0),
            clock=clock,
            tick=1.0,
        )
        self.assertEqual(["paint", "read"], order)

    def test_the_first_picture_is_of_the_starting_position(self):
        state = a_state(player=(1, 1), ghost=(3, 3))
        _, screen, _ = run([QUIT], state=state)
        self.assertEqual("p11 g33", screen.pictures[0].rows()[0])

    def test_the_ghost_is_not_due_until_a_whole_tick_after_that(self):
        _, screen, _ = run([QUIT], tick=1.0)
        self.assertEqual([1000], screen.timeouts)


class ArrowKeyTest(unittest.TestCase):
    """CTRL-1 and CTRL-2 — one square per press, and then it stops."""

    def test_an_arrow_key_produces_exactly_one_player_transition(self):
        move, calls = a_recording_player_move()
        run([controls.KEY_RIGHT, QUIT], move_player=move)
        self.assertEqual([RIGHT], calls)

    def test_each_arrow_maps_through_to_its_own_direction(self):
        move, calls = a_recording_player_move()
        run(
            [
                controls.KEY_UP,
                controls.KEY_DOWN,
                controls.KEY_LEFT,
                controls.KEY_RIGHT,
                QUIT,
            ],
            move_player=move,
        )
        self.assertEqual([UP, DOWN, LEFT, RIGHT], calls)

    def test_the_player_moves_one_square_and_then_stops(self):
        # CTRL-2's "the player never drifts on their own": a press, then a
        # hundred turns of the loop with no key at all.
        state = a_state(player=(1, 1))
        keys = [controls.KEY_RIGHT] + [None] * 100 + [QUIT]
        final, _, _ = run(keys, state=state)
        self.assertEqual(Position(1, 2), final.player)

    def test_holding_a_direction_is_not_required_and_is_not_remembered(self):
        # There is no "currently heading" anywhere for a key to set, so the
        # only way to move twice is to press twice.
        move, calls = a_recording_player_move()
        run([controls.KEY_RIGHT] + [None] * 5 + [QUIT], move_player=move)
        self.assertEqual(1, len(calls))

    def test_two_presses_are_two_transitions(self):
        move, calls = a_recording_player_move()
        run([controls.KEY_RIGHT, controls.KEY_RIGHT, QUIT], move_player=move)
        self.assertEqual([RIGHT, RIGHT], calls)

    def test_a_press_towards_a_wall_moves_nothing(self):
        # CTRL-3 belongs to the transition, not to the loop; what is asserted
        # here is that the loop does not paper over it.
        state = a_state(player=(1, 1))
        final, _, _ = run([controls.KEY_UP, QUIT], state=state)
        self.assertEqual(Position(1, 1), final.player)


class OtherKeysTest(unittest.TestCase):
    """CTRL-5 — no other key does anything."""

    def test_an_unmapped_key_produces_no_transition_at_all(self):
        move, calls = a_recording_player_move()
        ghost, ghost_calls = a_recording_ghost_move()
        run(
            [(ord("x"), 0.0), (ord("7"), 0.0), (27, 0.0), (410, 0.0), QUIT],
            move_player=move,
            move_ghost=ghost,
        )
        self.assertEqual([], calls)
        self.assertEqual([], ghost_calls)

    def test_an_unmapped_key_leaves_the_state_untouched(self):
        state = a_state(player=(1, 1), dots=[(1, 2), (1, 3)], score=4)
        final, _, _ = run([(ord("x"), 0.0), QUIT], state=state)
        self.assertEqual(state, final)

    def test_an_unmapped_key_does_not_quit(self):
        _, screen, _ = run([(ord("x"), 0.0), (ord("Z"), 0.0), QUIT])
        self.assertEqual(3, screen.reads)


class GhostClockTest(unittest.TestCase):
    """GHOST-1 — the ghost moves whether or not the player is moving."""

    def test_a_run_with_no_key_presses_still_ticks_once_per_tick(self):
        _, ghost_calls = None, None
        ghost, ghost_calls = a_recording_ghost_move()
        run([None] * 10 + [QUIT], move_ghost=ghost, tick=1.0)
        self.assertEqual(10, len(ghost_calls))

    def test_the_ghost_moves_while_the_player_stands_still(self):
        state = a_state(player=(1, 1), ghost=(1, 1))
        final, _, _ = run(
            [None] * 2 + [QUIT], state=state, move_ghost=a_walking_ghost(), tick=1.0
        )
        self.assertEqual(Position(1, 1), final.player)
        self.assertEqual(Position(1, 3), final.ghost)

    def test_a_key_arriving_early_does_not_bring_the_tick_forward(self):
        # Three keys arrive a quarter of the way into the tick each. The
        # deadline they did not reach is still the same deadline, so three
        # key presses have produced no tick at all.
        ghost, ghost_calls = a_recording_ghost_move()
        keys = [(ord("x"), 0.25)] * 3 + [QUIT]
        run(keys, move_ghost=ghost, tick=1.0)
        self.assertEqual([], ghost_calls)

    def test_a_key_arriving_early_does_not_hold_the_tick_up_either(self):
        # Ten early keys over ten seconds: ten ticks, no more and no fewer.
        ghost, ghost_calls = a_recording_ghost_move()
        keys = [(ord("x"), 1.0)] * 10 + [QUIT]
        run(keys, move_ghost=ghost, tick=1.0)
        self.assertEqual(10, len(ghost_calls))

    def test_the_wait_is_only_ever_the_time_left_until_the_deadline(self):
        # Half a tick passes on each read, so the waits alternate between a
        # whole tick and half of one.
        keys = [(None, 0.5)] * 4 + [QUIT]
        _, screen, _ = run(keys, tick=1.0)
        self.assertEqual([1000, 500, 1000, 500, 1000], screen.timeouts)

    def test_the_loop_never_asks_for_a_negative_wait(self):
        # A negative timeout makes ncurses block for ever.
        keys = [(None, 3.7)] * 20 + [QUIT]
        _, screen, _ = run(keys, tick=1.0)
        for timeout in screen.timeouts:
            self.assertGreaterEqual(timeout, 0)

    def test_a_clock_that_falls_a_long_way_behind_catches_its_ticks_up(self):
        # One read that eats ten whole ticks. The deadline is additive, so the
        # ten ticks are still owed and are worked off one turn at a time
        # rather than being silently dropped.
        ghost, ghost_calls = a_recording_ghost_move()
        keys = [(None, 10.0)] + [(None, 0.0)] * 20 + [QUIT]
        run(keys, move_ghost=ghost, tick=1.0)
        self.assertEqual(10, len(ghost_calls))

    def test_the_deadline_does_not_drift_over_a_hundred_ticks(self):
        # Each read is five milliseconds late, a hundred times over. If the
        # loop reset the deadline to `now + tick` the hundredth tick would
        # land half a second late; it must land on time.
        late = ticker.GHOST_TICK_SECONDS + 0.005
        keys = [(None, late)] * 100 + [QUIT]
        _, screen, clock = run(keys, tick=ticker.GHOST_TICK_SECONDS)
        # 100 reads, each overshooting by 5 ms, so the clock reads 0.5 s past
        # where the deadlines are. The waits prove the deadlines did not
        # follow the clock: every one of them is zero because the loop is
        # permanently 5 ms behind and never further.
        self.assertEqual(0, screen.timeouts[-1])
        self.assertAlmostEqual(
            100 * late, clock.now, places=9
        )


class PaintingTest(unittest.TestCase):
    """SCRN-7 — the picture is redrawn as things move."""

    def test_a_picture_is_painted_after_a_player_move(self):
        state = a_state(player=(1, 1))
        _, screen, _ = run([controls.KEY_RIGHT, QUIT], state=state)
        self.assertEqual(["p11 g33", "p12 g33"], positions(screen.pictures))

    def test_a_picture_is_painted_after_a_ghost_move(self):
        state = a_state(player=(1, 1), ghost=(1, 1))
        _, screen, _ = run(
            [None, None, QUIT], state=state, move_ghost=a_walking_ghost(), tick=1.0
        )
        self.assertEqual(
            ["p11 g11", "p11 g12", "p11 g13"], positions(screen.pictures)
        )

    def test_a_picture_is_still_painted_when_nothing_changed(self):
        # END-5's "the last picture stays on screen" is true by painting it,
        # not by declining to.
        _, screen, _ = run([(ord("x"), 0.0), (ord("x"), 0.0), QUIT])
        self.assertEqual(3, len(screen.pictures))

    def test_every_turn_of_the_loop_paints_exactly_once(self):
        _, screen, _ = run([None] * 7 + [QUIT], tick=1.0)
        # Eight reads; the first seven each paint, the quit does not, and one
        # picture was painted before the first read.
        self.assertEqual(8, len(screen.pictures))

    def test_the_picture_painted_is_of_the_state_as_it_now_stands(self):
        state = a_state(player=(1, 1), ghost=(1, 1))
        _, screen, _ = run(
            [controls.KEY_RIGHT, QUIT],
            state=state,
            move_ghost=a_walking_ghost(),
            tick=0.0,  # every read is already past the deadline
        )
        # Both the player's move and the ghost's tick are in the one picture.
        self.assertEqual("p12 g12", screen.pictures[-1].rows()[0])


class EndedGameTest(unittest.TestCase):
    """END-5 — once a game has ended, everything stops.

    The loop holds no test of the outcome: it calls the transitions as usual
    and they decline. These tests pin that arrangement, because it is the
    thing that keeps game logic out of the shell — and it is a requirement on
    whatever WI-6 and WI-7 land.
    """

    def test_the_loop_asks_the_transition_rather_than_deciding_itself(self):
        move, calls = a_recording_player_move()
        ghost, ghost_calls = a_recording_ghost_move()
        run(
            [(controls.KEY_RIGHT, 0.0), None, QUIT],
            state=a_state(outcome=Outcome.CLEARED),
            move_player=move,
            move_ghost=ghost,
            tick=1.0,
        )
        self.assertEqual([RIGHT], calls)
        self.assertEqual(1, len(ghost_calls))

    def test_an_arrow_key_after_the_ending_changes_nothing(self):
        lost = a_state(player=(1, 1), dots=[(1, 2)], outcome=Outcome.CAUGHT)
        final, _, _ = run([controls.KEY_RIGHT, QUIT], state=lost)
        self.assertEqual(lost, final)

    def test_the_last_picture_is_painted_over_and_over_unchanged(self):
        won = a_state(player=(1, 1), outcome=Outcome.CLEARED)
        _, screen, _ = run([None] * 5 + [QUIT], state=won, tick=1.0)
        self.assertEqual(["p11 g33"] * 6, positions(screen.pictures))


class ResolveRenderTest(unittest.TestCase):
    """Which renderer the loop draws with.

    WI-3 and WI-4 were built in parallel, so the loop looks its renderer up
    rather than importing it. Both halves of that are tested here with a fake
    lookup, because on this branch only one of them can be tested for real.
    """

    def test_without_wi_3_it_falls_back_to_the_stand_in(self):
        def missing(name):
            raise ImportError(name)

        self.assertIs(standins.render, loop.resolve_render(missing))

    def test_with_wi_3_present_it_uses_the_real_renderer(self):
        sentinel = lambda state: None

        class View(object):
            render = staticmethod(sentinel)

        def found(name):
            self.assertEqual("termgame.view", name)
            return View

        self.assertIs(sentinel, loop.resolve_render(found))

    def test_a_view_module_without_a_render_falls_back_rather_than_crashing(self):
        class Empty(object):
            pass

        self.assertIs(standins.render, loop.resolve_render(lambda name: Empty))

    def test_the_default_lookup_produces_something_callable(self):
        self.assertTrue(callable(loop.resolve_render()))


class PlainTextPathTest(unittest.TestCase):
    """With no terminal there is no key to press, so the game must not block.

    Plan §2.6 rule 4: never launch anything in a window that blocks for ever.
    This path is also how an agent, which has no tty at all, can see the
    picture the game would have drawn.
    """

    class NotATerminal(object):
        def fileno(self):
            raise ValueError("I/O operation on closed file")

    def test_a_stream_that_is_not_a_terminal_is_recognised(self):
        self.assertFalse(loop._has_a_terminal(self.NotATerminal()))

    def test_the_frame_is_written_whole_with_nothing_after_the_last_row(self):
        import io

        stream = io.StringIO()
        loop._write_plainly(frame_from_rows(["ab", "cd"]), stream=stream)
        self.assertEqual("ab\ncd\n", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
