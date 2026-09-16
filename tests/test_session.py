# -*- coding: utf-8 -*-
"""WI-15 — the session controller.

Requirements: GAME-3, START-5, CTRL-4, GHOST-1 (in part), END-5, END-6,
WIN-5 under assumption A3.

**What these tests own, and what they deliberately do not.**  The session is
the caller of three things that already have their own tests, and the rule
in section 4 of the plan is that a wiring test owns the join and nothing
else:

* *the turn resolver* — what a turn does is WI-11's.  The join is asserted
  by computing the expected state with ``resolve_move`` / ``resolve_tick``
  in the test and checking the session kept exactly that.  One defect in the
  resolver turns WI-11's tests red, not these.
* *the frame composer* — amendment 3 dropped the WI-12 dependency: this item
  is written against a **one-call seam**, a game state goes in and a frame
  comes out, and tested with a fake.  **Nothing here asserts what is in a
  frame.**  That is WI-12's and WI-13's, and asserting it twice is what the
  rule exists to prevent.
* *the status line* — the ending shown is chosen by the outcome in the state
  the composer is handed, so the join is that the state carries the outcome.
  What the line then reads is WI-13's, in ``tests/test_status_line.py``.

No window is opened and no clock is read.  The session has no clock: the
test is the clock.
"""

from __future__ import annotations

import random
import unittest

from terminal_game.application.session import Phase, Session, new_session
from terminal_game.domain.dot_field import DotField
from terminal_game.domain.game_state import GameState, Outcome, Score
from terminal_game.domain.maze import Direction, Maze, Square
from terminal_game.domain.turn_resolver import resolve_move, resolve_tick

# A ring of eight corridor squares around one lone wall, so the ghost always
# has somewhere to go and the player always has somewhere to walk.
RING = Maze.from_text(
    """
#####
#...#
#.#.#
#...#
#####
"""
)

# A straight east-west corridor, five squares long.
CORRIDOR = Maze.from_text(
    """
#######
#.....#
#######
"""
)


class Picture:
    """What the composer hands back.

    Deliberately **not** a ``Frame``: nothing in this item may depend on what
    a frame contains, and a value with no content at all makes that
    impossible to do by accident.  Each one is a distinct object, so a test
    can ask whether the picture that was shown is the picture that was
    composed.
    """

    def __init__(self, number: int) -> None:
        self.number = number

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return "Picture({0})".format(self.number)


class Composer:
    """The one-call seam WI-12 implements: a state goes in, a frame comes out.

    Records every state it was asked about, so a test can assert *what the
    session asked to have drawn* without saying anything about the drawing.
    """

    def __init__(self, fails_after: int = None, error: Exception = None) -> None:
        self.states = []
        self.fails_after = fails_after
        self.error = error or ValueError("the composer fell over")

    def __call__(self, state: GameState) -> Picture:
        if self.fails_after is not None and len(self.states) >= self.fails_after:
            raise self.error
        self.states.append(state)
        return Picture(len(self.states))


class Screen:
    """Where frames go.  The real one is the character grid surface."""

    def __init__(self, fails_after: int = None, error: Exception = None) -> None:
        self.shown = []
        self.fails_after = fails_after
        self.error = error or RuntimeError("the surface fell over")

    def __call__(self, picture) -> None:
        if self.fails_after is not None and len(self.shown) >= self.fails_after:
            raise self.error
        self.shown.append(picture)


class Shutdown:
    """What the window owner's ``end_session`` stands in for."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


class Fixture:
    """A session and the four seams it was handed."""

    def __init__(
        self,
        state: GameState,
        seed: int = 0,
        compose: Composer = None,
        screen: Screen = None,
    ) -> None:
        self.compose = compose or Composer()
        self.screen = screen or Screen()
        self.shut_down = Shutdown()
        self.random_source = random.Random(seed)
        self.session = Session(
            state,
            compose=self.compose,
            show=self.screen,
            random_source=self.random_source,
            shut_down=self.shut_down,
        )


def a_game(
    maze: Maze = RING,
    player: Square = Square(1, 1),
    ghost: Square = Square(3, 3),
    dots: DotField = None,
    score: Score = None,
    outcome: Outcome = Outcome.UNDECIDED,
) -> GameState:
    """A hand-built game state, so every square in it can be read off."""
    return GameState(
        maze=maze,
        dots=DotField.over_corridors_except(maze, player) if dots is None else dots,
        player=player,
        ghost=ghost,
        score=Score.zero() if score is None else score,
        outcome=outcome,
    )


def a_lost_game() -> GameState:
    """A game already decided, so Decided can be entered without playing one."""
    return a_game(outcome=Outcome.CAUGHT)


class ThreeStatesAndNoMore(unittest.TestCase):
    """GAME-3: Playing, Decided, Ended, and there is nowhere for a fourth."""

    def test_there_are_exactly_three_phases(self):
        self.assertEqual(
            ["PLAYING", "DECIDED", "ENDED"], [phase.name for phase in Phase]
        )

    def test_a_fresh_session_is_playing(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        self.assertIs(Phase.PLAYING, fixture.session.phase)

    def test_a_session_whose_outcome_is_set_is_decided(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()

        self.assertIs(Phase.DECIDED, fixture.session.phase)

    def test_quitting_a_decided_game_leaves_it_ended_not_decided(self):
        """``q`` is honoured in every state, so Ended wins over Decided."""
        fixture = Fixture(a_lost_game())
        fixture.session.start()
        fixture.session.quit()

        self.assertIs(Phase.ENDED, fixture.session.phase)

    def test_there_is_no_restart_edge(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        fixture.session.quit()

        with self.assertRaises(RuntimeError):
            fixture.session.start()


class TheGameIsUnderWayWhenTheWindowOpens(unittest.TestCase):
    """START-5: nothing has to be pressed to begin."""

    def test_starting_composes_the_first_picture(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        self.assertEqual(1, len(fixture.compose.states))

    def test_starting_shows_the_picture_it_composed(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        self.assertEqual(1, len(fixture.screen.shown))
        self.assertIs(fixture.session.frame, fixture.screen.shown[0])

    def test_the_first_picture_is_composed_from_the_opening_state(self):
        state = a_game()
        fixture = Fixture(state)
        fixture.session.start()

        self.assertIs(state, fixture.compose.states[0])

    def test_nothing_is_composed_before_the_session_starts(self):
        fixture = Fixture(a_game())

        self.assertEqual([], fixture.compose.states)
        self.assertIsNone(fixture.session.frame)

    def test_the_ghost_moves_without_any_key_being_pressed(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        before = fixture.session.state

        fixture.session.tick()

        self.assertNotEqual(before.ghost, fixture.session.state.ghost)

    def test_starting_twice_composes_one_picture(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        fixture.session.start()

        self.assertEqual(1, len(fixture.compose.states))


class TheJoinToTheResolver(unittest.TestCase):
    """The session hands the turn to WI-11 and keeps what it gives back.

    Asserted once for a move and once for a tick.  What a turn *does* is
    WI-11's own 25 tests; these say only that this is where it happens.
    """

    def test_a_move_keeps_exactly_what_resolve_move_returned(self):
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(5, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertEqual(
            resolve_move(state, Direction.EAST), fixture.session.state
        )

    def test_a_tick_keeps_exactly_what_resolve_tick_returned(self):
        state = a_game()
        fixture = Fixture(state, seed=7)
        fixture.session.start()

        fixture.session.tick()

        self.assertEqual(
            resolve_tick(state, random.Random(7)), fixture.session.state
        )

    def test_the_outcome_is_the_one_the_resolver_set(self):
        """The session records an ending; it does not decide one.

        The player is one square from the ghost, so the resolver's collision
        test fires on this move.  That the collision *is* a loss is END-1's,
        owned by WI-11.
        """
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(2, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertIs(Outcome.CAUGHT, fixture.session.outcome)
        self.assertIs(Phase.DECIDED, fixture.session.phase)

    def test_a_press_towards_a_wall_composes_nothing_new(self):
        """CTRL-3 arrives here as the resolver handing back what it was given."""
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(5, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.NORTH)

        self.assertEqual(1, len(fixture.compose.states))
        self.assertIs(state, fixture.session.state)

    def test_something_that_is_not_a_direction_is_refused(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        for not_a_direction in (None, "north", 0):
            with self.assertRaises(ValueError):
                fixture.session.move(not_a_direction)


class TheJoinToTheComposer(unittest.TestCase):
    """A state goes in, a frame comes out — the seam WI-12 implements.

    Nothing here says anything about what is *in* a frame.  That is WI-12's
    and WI-13's, and amendment 3 keeps the two items in different files
    precisely so that it is asserted once.
    """

    def test_a_turn_that_changed_the_game_composes_from_the_new_state(self):
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(5, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertEqual(2, len(fixture.compose.states))
        self.assertIs(fixture.session.state, fixture.compose.states[1])

    def test_what_was_composed_is_what_was_shown(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        fixture.session.tick()

        self.assertEqual(2, len(fixture.screen.shown))
        self.assertIs(fixture.session.frame, fixture.screen.shown[-1])

    def test_the_final_picture_is_composed_from_the_state_carrying_the_outcome(self):
        """How the status line comes to say which ending happened.

        The session does not tell anyone which line to draw: it composes
        from a state whose outcome is set, and WI-13 selects by that outcome.
        The join is that the outcome reaches the composer.
        """
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(2, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertIs(Outcome.CAUGHT, fixture.compose.states[-1].outcome)


class OnceDecidedNothingMoves(unittest.TestCase):
    """END-5, and assumption A3: the last picture stands until ``q``."""

    def test_a_tick_in_decided_moves_nothing(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()
        before = fixture.session.state

        fixture.session.tick()

        self.assertIs(before, fixture.session.state)

    def test_a_tick_in_decided_composes_nothing_new(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()

        for _ in range(5):
            fixture.session.tick()

        self.assertEqual(1, len(fixture.compose.states))

    def test_an_arrow_in_decided_changes_nothing(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()
        before = fixture.session.state

        for direction in Direction:
            fixture.session.move(direction)

        self.assertIs(before, fixture.session.state)
        self.assertEqual(1, len(fixture.compose.states))

    def test_the_picture_the_player_is_looking_at_does_not_change(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()
        standing = fixture.session.frame

        fixture.session.tick()
        fixture.session.move(Direction.NORTH)

        self.assertIs(standing, fixture.session.frame)
        self.assertEqual(1, len(fixture.screen.shown))

    def test_the_outcome_is_not_replaced_by_a_later_turn(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()

        for _ in range(5):
            fixture.session.tick()

        self.assertIs(Outcome.CAUGHT, fixture.session.outcome)

    def test_deciding_does_not_shut_the_session_down(self):
        """Assumption A3, and the one place a ruling against it would land.

        WIN-5 read literally would close the window the instant the outcome
        is decided; END-5 and END-6 say the picture stands and ``q`` is the
        only way out.  We proceed on A3, so nothing is shut down here.
        """
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(2, 1))
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertIs(Phase.DECIDED, fixture.session.phase)
        self.assertEqual(0, fixture.shut_down.calls)


class QuittingIsTheOnlyWayOut(unittest.TestCase):
    """CTRL-4 and END-6: ``q`` is honoured in every state."""

    def test_quitting_while_playing_reaches_ended(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        fixture.session.quit()

        self.assertIs(Phase.ENDED, fixture.session.phase)

    def test_quitting_a_finished_game_reaches_ended(self):
        fixture = Fixture(a_lost_game())
        fixture.session.start()

        fixture.session.quit()

        self.assertIs(Phase.ENDED, fixture.session.phase)

    def test_quitting_before_the_first_picture_reaches_ended(self):
        fixture = Fixture(a_game())

        fixture.session.quit()

        self.assertIs(Phase.ENDED, fixture.session.phase)
        self.assertEqual(1, fixture.shut_down.calls)

    def test_reaching_ended_asks_to_be_shut_down_exactly_once(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        fixture.session.quit()

        self.assertEqual(1, fixture.shut_down.calls)

    def test_quitting_twice_asks_to_be_shut_down_once(self):
        fixture = Fixture(a_game())
        fixture.session.start()

        fixture.session.quit()
        fixture.session.quit()

        self.assertEqual(1, fixture.shut_down.calls)

    def test_nothing_happens_after_ended(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        fixture.session.quit()
        composed = len(fixture.compose.states)
        before = fixture.session.state

        fixture.session.tick()
        fixture.session.move(Direction.EAST)

        self.assertIs(before, fixture.session.state)
        self.assertEqual(composed, len(fixture.compose.states))


class AFailureEndsTheSessionRatherThanPropagating(unittest.TestCase):
    """Amendment 1, from a Tk 8.5 behaviour measured during WI-3.

    Tk swallows an exception raised inside an ``after()`` callback: it
    reaches ``report_callback_exception``, a traceback is printed, and the
    main loop carries on.  A session that let an error out of a tick would
    therefore not shut down — it would sit there with a broken game on an
    unquittable screen.  So a failure is routed into the same path ``q``
    takes, deliberately, and is recorded rather than absorbed.
    """

    def _session_whose_composer_fails(self):
        """Started successfully, and the *next* picture cannot be composed."""
        fixture = Fixture(a_game(), compose=Composer(fails_after=1))
        fixture.session.start()
        return fixture

    def test_a_tick_that_fails_ends_the_session(self):
        fixture = self._session_whose_composer_fails()

        fixture.session.tick()

        self.assertIs(Phase.ENDED, fixture.session.phase)

    def test_a_tick_that_fails_asks_to_be_shut_down_exactly_once(self):
        fixture = self._session_whose_composer_fails()

        fixture.session.tick()

        self.assertEqual(1, fixture.shut_down.calls)

    def test_a_tick_that_fails_does_not_raise(self):
        fixture = self._session_whose_composer_fails()

        fixture.session.tick()  # no assertRaises: the point is that it does not

        self.assertIsInstance(fixture.session.failure, ValueError)

    def test_the_failure_is_reported_rather_than_absorbed(self):
        fixture = self._session_whose_composer_fails()
        fixture.session.tick()

        self.assertEqual(
            "the composer fell over", str(fixture.session.failure)
        )

    def test_a_move_that_fails_ends_the_session_the_same_way(self):
        state = a_game(maze=CORRIDOR, player=Square(1, 1), ghost=Square(5, 1))
        fixture = Fixture(state, screen=Screen(fails_after=1))
        fixture.session.start()

        fixture.session.move(Direction.EAST)

        self.assertIs(Phase.ENDED, fixture.session.phase)
        self.assertEqual(1, fixture.shut_down.calls)
        self.assertIsInstance(fixture.session.failure, RuntimeError)

    def test_a_ghost_that_cannot_move_ends_the_session(self):
        """The one failure the game itself can produce, rather than a seam.

        A ghost with nowhere to go raises out of the policy.  The real
        generator never builds such a maze — WI-5 pins that — but a session
        that met one must shut down rather than hang.
        """
        walled_in = Maze.from_text(
            """
###
#.#
###
"""
        )
        state = a_game(
            maze=walled_in, player=Square(1, 1), ghost=Square(1, 1)
        )
        fixture = Fixture(state)
        fixture.session.start()

        fixture.session.tick()

        self.assertIs(Phase.ENDED, fixture.session.phase)
        self.assertIsNotNone(fixture.session.failure)

    def test_an_ordinary_game_records_no_failure(self):
        fixture = Fixture(a_game())
        fixture.session.start()
        fixture.session.tick()
        fixture.session.quit()

        self.assertIsNone(fixture.session.failure)

    def test_a_first_picture_that_cannot_be_composed_raises(self):
        """``start`` runs before the event loop, where raising still works.

        A game that cannot draw its opening position should fail loudly
        rather than open a window and shut itself down again.
        """
        fixture = Fixture(a_game(), compose=Composer(fails_after=0))

        with self.assertRaises(ValueError):
            fixture.session.start()


class AWholeSessionWithNoWindow(unittest.TestCase):
    """The headless session WI-19 consumes, and builds no second one.

    There is no clock: the session reads none and schedules nothing, so a
    game runs as fast as it can be driven.  This is the shape of it.
    """

    def test_a_session_can_be_built_from_a_maze_at_its_opening_position(self):
        fixture_compose = Composer()
        session = new_session(
            RING,
            compose=fixture_compose,
            show=Screen(),
            random_source=random.Random(3),
            shut_down=Shutdown(),
        )
        session.start()

        self.assertIs(Phase.PLAYING, session.phase)
        self.assertTrue(RING.is_corridor(session.state.player))
        self.assertTrue(RING.is_corridor(session.state.ghost))

    def test_a_hundred_ticks_and_moves_run_with_no_window_and_no_clock(self):
        screen = Screen()
        session = new_session(
            RING,
            compose=Composer(),
            show=screen,
            random_source=random.Random(5),
            shut_down=Shutdown(),
        )
        session.start()

        for _ in range(100):
            session.tick()
            if session.phase is not Phase.PLAYING:
                break

        self.assertGreater(len(screen.shown), 1)
        self.assertIn(session.phase, (Phase.PLAYING, Phase.DECIDED))

    def test_a_seeded_session_replays_identically(self):
        """What WI-19's asserted pictures rest on: nothing here is ambient."""
        walks = []
        for _ in range(2):
            session = new_session(
                RING,
                compose=Composer(),
                show=Screen(),
                random_source=random.Random(11),
                shut_down=Shutdown(),
            )
            session.start()
            walk = []
            for _ in range(20):
                session.tick()
                walk.append(session.state.ghost)
            walks.append(walk)

        self.assertEqual(walks[0], walks[1])


class WhatTheSessionRefuses(unittest.TestCase):
    """A seam that is missing is a defect that would show up much later."""

    def test_a_session_needs_a_game_state(self):
        with self.assertRaises(TypeError):
            Session(
                "not a game",
                compose=Composer(),
                show=Screen(),
                random_source=random.Random(0),
                shut_down=Shutdown(),
            )

    def test_every_seam_must_be_callable(self):
        seams = {
            "compose": Composer(),
            "show": Screen(),
            "shut_down": Shutdown(),
        }
        for name in seams:
            broken = dict(seams)
            broken[name] = None
            with self.assertRaises(TypeError):
                Session(
                    a_game(), random_source=random.Random(0), **broken
                )


if __name__ == "__main__":
    unittest.main()
