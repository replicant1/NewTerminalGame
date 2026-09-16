# -*- coding: utf-8 -*-
"""WI-18 — the wiring, asserted at the joins and nowhere else.

**No window is created anywhere in this file.**  The toolkit is WI-3's
:class:`RecordingToolkit` throughout, which is the whole reason the
composition root takes every collaborator as an argument.

What this module does **not** contain is the point of it.  The maze is
WI-5's, the opening position WI-6's, the rules WI-11's, the picture WI-12's
and WI-13's, the session's three states WI-15's, the window WI-3's, the
keys WI-9's — and a whole game played end to end is **WI-19's**, headless,
already landed.  One defect should turn one test red, so nothing below
re-asserts any of that.

The joins this item owns, and they are all it owns:

* the entry point **assembles the real components**;
* **a first frame exists before the event loop is entered** (START-5);
* a key reaches the session as a move, a quit, or as nothing at all;
* ending the session **closes the window**;
* **a recorded failure is noticed** — the first trap;
* **the close button reaches the session** — the second trap, which would
  otherwise defeat the first.

The last two are assertions rather than notes because they were measured on
a real window in WI-17; see ``docs/findings/WI-17-real-window-manners.md``.
"""

import random
import unittest

from terminal_game.application.session import Phase, Session
from terminal_game.domain.maze import Direction, Maze
from terminal_game.presentation.frame import Frame
from terminal_game.presentation.picture import frame_for
from terminal_game.shell.game import (
    Game,
    GameCollaborator,
    build_game,
    compose_picture,
)
from terminal_game.shell.toolkit import KeyPress, PixelSize, ScreenPosition
from terminal_game.shell.window_owner import WINDOW_TITLE, WindowOwner

from .generated_mazes import maze_for
from .recording_toolkit import RecordingToolkit

#: The size the window is told.  WI-2 works out the real one from the font;
#: the wiring only passes it along, so any number does here.
A_SIZE = PixelSize(width=400, height=570)

#: Somewhere to put the window.  WI-14 works out the real one.
A_POSITION = ScreenPosition(x=190, y=190)

#: One of the shared seeded mazes, laid out once and cached.
A_SEED = 7


class RecordingSurface:
    """Stands in for WI-2's character grid surface: keeps what it was shown."""

    def __init__(self, target=None):
        self.target = target
        self.painted = []

    def paint(self, frame):
        self.painted.append(frame)


class FakeSession:
    """Records what a key asked for.  What a session *does* is WI-15's."""

    def __init__(self):
        self.asked = []
        self.failure = None

    def tick(self):
        self.asked.append(("tick", None))

    def move(self, direction):
        self.asked.append(("move", direction))

    def quit(self):
        self.asked.append(("quit", None))

    def start(self):
        self.asked.append(("start", None))


def _game(toolkit, surfaces=None, **kwargs):
    """A real game over a real maze, with a recording toolkit and surface."""
    made = surfaces if surfaces is not None else []

    def make_surface(target):
        surface = RecordingSurface(target)
        made.append(surface)
        return surface

    arguments = {
        "position": A_POSITION,
        "random_source": random.Random(A_SEED),
        "maze": maze_for(A_SEED),
    }
    arguments.update(kwargs)
    return build_game(toolkit, A_SIZE, make_surface, **arguments)


class TheEntryPointAssemblesTheRealThingTest(unittest.TestCase):
    """That the parts joined are the real parts, not stand-ins."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.game = _game(self.toolkit)

    def test_it_joins_a_real_session_over_a_real_maze(self):
        self.assertIsInstance(self.game.session, Session)
        self.assertIsInstance(self.game.session.state.maze, Maze)

    def test_it_joins_a_real_window_owner_at_the_size_and_place_it_was_given(self):
        self.assertIsInstance(self.game.owner, WindowOwner)
        self.assertEqual(A_SIZE, self.game.owner.spec.size)
        self.assertEqual(A_POSITION, self.game.owner.spec.position)

    def test_the_window_it_will_ask_for_is_the_games_own(self):
        # WIN-1, WIN-3: what the window *is* belongs to WI-3, and this is
        # only that the wiring did not ask for some other window.
        self.assertEqual(WINDOW_TITLE, self.game.owner.spec.title)

    def test_the_collaborator_the_window_will_talk_to_holds_that_session(self):
        # The wiring's one genuinely fiddly moment: the session needs the
        # window owner's shutdown and the window owner needs the
        # collaborator, so the collaborator is attached second.
        self.assertIs(self.game.session, self.game.collaborator.session)

    def test_the_maze_is_laid_out_from_the_source_when_none_is_handed_over(self):
        game = build_game(
            RecordingToolkit(),
            A_SIZE,
            RecordingSurface,
            position=A_POSITION,
            random_source=random.Random(A_SEED),
        )

        self.assertIsInstance(game.session.state.maze, Maze)
        self.assertEqual(maze_for(A_SEED), game.session.state.maze)


class TheGameIsUnderWayBeforeTheLoopTest(unittest.TestCase):
    """START-5: nothing has to be pressed to begin."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.surfaces = []
        self.game = _game(self.toolkit, self.surfaces)

    def test_starting_paints_a_first_frame(self):
        self.game.start()

        self.assertEqual(1, self.game.frames_shown)
        self.assertEqual(1, len(self.surfaces[0].painted))
        self.assertIsInstance(self.surfaces[0].painted[0], Frame)

    def test_the_first_frame_is_painted_before_the_event_loop_is_entered(self):
        self.game.start()

        self.assertFalse(self.toolkit.event_loop_entered)

    def test_the_surface_is_built_on_the_drawing_target_the_window_gave_back(self):
        # The WI-2 / WI-3 join, and the only thing that crosses it.
        self.game.start()

        self.assertIs(self.toolkit.drawing_target, self.surfaces[0].target)

    def test_running_enters_the_loop_with_the_first_frame_already_up(self):
        self.game.run()

        self.assertTrue(self.toolkit.event_loop_entered)
        self.assertEqual(1, self.game.frames_shown)

    def test_the_ghost_is_ticking_by_the_time_the_loop_is_entered(self):
        # GHOST-1 at the wiring's level: that the timer was started, not
        # what its interval is -- that is WI-3's.
        self.game.run()

        self.assertIn(self.game.owner.tick_interval_ms, self.toolkit.scheduled_delays)


class AKeyReachingTheSessionTest(unittest.TestCase):
    """The three lines the layer rule forces to live on this side.

    ``Intent`` is Presentation vocabulary and the Application layer may not
    name Presentation, so the translation happens here.  What each keysym
    *means* is WI-9's and has its own tests; this is only that the meaning
    is acted on.
    """

    def setUp(self):
        self.session = FakeSession()
        self.collaborator = GameCollaborator(self.session)

    def press(self, keysym, char=""):
        self.collaborator.on_key(KeyPress(keysym=keysym, char=char))

    def test_each_arrow_reaches_the_session_as_a_move_in_its_direction(self):
        for keysym in ("Up", "Down", "Left", "Right"):
            self.press(keysym)

        self.assertEqual(
            [
                ("move", Direction.NORTH),
                ("move", Direction.SOUTH),
                ("move", Direction.WEST),
                ("move", Direction.EAST),
            ],
            self.session.asked,
        )

    def test_q_and_shifted_q_both_reach_the_session_as_a_quit(self):
        self.press("q", "q")
        self.press("Q", "Q")

        self.assertEqual([("quit", None), ("quit", None)], self.session.asked)

    def test_an_unmapped_key_asks_the_session_for_nothing_at_all(self):
        # CTRL-5 at the join: not "translates to None", which is WI-9's,
        # but "the session is never told", which is this.
        for keysym, char in (
            ("z", "z"),
            ("Escape", ""),
            ("F5", ""),
            ("space", " "),
            ("Return", "\r"),
        ):
            self.press(keysym, char)

        self.assertEqual([], self.session.asked)

    def test_a_tick_reaches_the_session_as_a_tick(self):
        self.collaborator.on_tick()

        self.assertEqual([("tick", None)], self.session.asked)

    def test_it_is_harmless_before_a_session_has_been_attached(self):
        # It exists for a moment without one, because the session needs the
        # window owner which needs it.
        loose = GameCollaborator()

        loose.on_tick()
        loose.on_key(KeyPress(keysym="q", char="q"))

        self.assertIsNone(loose.session)


class EndingTheGameClosesTheWindowTest(unittest.TestCase):
    """The route out, from the key to the window, asserted once."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.game = _game(self.toolkit)

    def test_q_ends_the_session_and_closes_the_window(self):
        self.game.start()

        self.toolkit.press("q", "q")

        self.assertIs(Phase.ENDED, self.game.session.phase)
        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_running_to_the_end_closes_the_window_exactly_once(self):
        # q from inside the loop, then the loop returning, then run()'s own
        # cleanup: three routes to a close, and one window.
        self.toolkit.event_loop_body = lambda: self.toolkit.press("q", "q")

        self.game.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))

    def test_nothing_is_painted_after_the_game_has_ended(self):
        # END-5 arrives here as the session composing nothing; that it
        # *does not compose* is WI-15's, and this is only that the wiring
        # does not paint anything of its own afterwards.
        self.game.start()
        shown = self.game.frames_shown

        self.toolkit.press("q", "q")

        self.assertEqual(shown, self.game.frames_shown)


class TheCloseButtonReachesTheSessionTest(unittest.TestCase):
    """The second trap, measured in WI-17 and asserted here.

    ``WindowOwner.open()`` binds the close request to its **own**
    ``end_session``.  Left alone, the close button takes the window and the
    process away without the session ever knowing — skipping its shutdown,
    and with it the failure check below.  Measured on a real window: the
    phase was still ``playing`` afterwards.

    The binding is last-writer-wins, so the wiring rebinds it after opening
    and :mod:`terminal_game.shell.window_owner` — another lane's landed
    file — is untouched.
    """

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.game = _game(self.toolkit)
        self.game.start()

    def test_the_close_button_takes_the_session_to_ended(self):
        self.toolkit.request_close()

        self.assertIs(Phase.ENDED, self.game.session.phase)

    def test_the_close_button_still_closes_the_window_exactly_once(self):
        # The window owner's end_session is what the session was given as
        # its shut_down, so rebinding did not lose the close.
        self.toolkit.request_close()

        self.assertEqual(1, self.toolkit.count("destroy_window"))
        self.assertTrue(self.game.owner.session_ended)

    def test_closing_twice_is_harmless(self):
        self.toolkit.request_close()
        self.toolkit.request_close()

        self.assertEqual(1, self.toolkit.count("destroy_window"))


class ACrashedGameDoesNotExitCleanTest(unittest.TestCase):
    """The first trap, and the reason this item has to do anything at all.

    Tk swallows an exception raised inside an ``after()`` callback, so the
    session cannot raise: it routes a failure into the same shutdown path
    ``q`` uses and records it.  Measured on a real window: the window was
    reaped, the phase reached Ended, **stderr was empty**, ``run()``
    returned **normally** and nothing anywhere said the game had fallen
    over.  ``exit_code`` is the only thing that does.
    """

    class DeliberateComposeFailure(Exception):
        """A collaborator handed in by the test, not a mutation of anything."""

    def setUp(self):
        self.toolkit = RecordingToolkit()
        self.composed = []

    def _failing_after(self, pictures):
        def compose(state):
            self.composed.append(state)
            if len(self.composed) > pictures:
                raise self.DeliberateComposeFailure("the composer fell over")
            return compose_picture(state)

        return compose

    def test_a_game_that_ends_normally_exits_clean(self):
        game = _game(self.toolkit)
        self.toolkit.event_loop_body = lambda: self.toolkit.press("q", "q")

        game.run()

        self.assertIsNone(game.failure)
        self.assertEqual(0, game.exit_code)

    def test_a_composer_that_falls_over_mid_game_is_noticed(self):
        game = _game(self.toolkit, compose=self._failing_after(1))
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        game.run()

        self.assertIsInstance(game.failure, self.DeliberateComposeFailure)
        self.assertEqual(1, game.exit_code)

    def test_the_failure_does_not_come_back_out_of_run(self):
        # This is the measurement, as a test: run() returning is not
        # evidence of anything, which is exactly why exit_code has to
        # exist.  If this ever starts raising, the check above is no longer
        # the only thing standing between a crash and a clean exit — and
        # somebody should find out why before relying on it.
        game = _game(self.toolkit, compose=self._failing_after(1))
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        game.run()  # deliberately not wrapped in assertRaises

        self.assertIsNotNone(game.failure)

    def test_a_game_that_fell_over_still_loses_its_window(self):
        game = _game(self.toolkit, compose=self._failing_after(1))
        self.toolkit.event_loop_body = self.toolkit.fire_due_timer

        game.run()

        self.assertEqual(1, self.toolkit.count("destroy_window"))
        self.assertEqual(0, self.toolkit.pending_count)

    def test_closing_the_window_after_a_crash_does_not_erase_the_crash(self):
        # The two traps meeting.  The close button now reaches the session,
        # which is what the rebinding is for — and a session that has
        # already failed must not have that failure quietly tidied away by
        # the ordinary shutdown path running a second time.
        game = _game(self.toolkit, compose=self._failing_after(1))

        def crash_then_close():
            self.toolkit.fire_due_timer()
            self.toolkit.request_close()

        self.toolkit.event_loop_body = crash_then_close

        game.run()

        self.assertEqual(1, game.exit_code)
        self.assertEqual(1, self.toolkit.count("destroy_window"))


class ThePictureTheSessionIsComposedWithTest(unittest.TestCase):
    """The join between the Shell and the picture, and only that."""

    def test_the_session_is_composed_with_presentations_picture_function(self):
        # WI-22a.  This used to rebuild the picture out of the composer and
        # the status line and compare against that — which was the wiring's
        # own job done a second time inside the test, so it would have gone
        # on passing if both copies drifted together.
        #
        # What the Shell owes is narrower and is all that is asserted here:
        # that the ``compose`` it hands the session is **Presentation's**
        # ``frame_for`` and not a picture of its own.  What that picture
        # contains is owned by ``tests/test_picture.py``, WI-12's tests and
        # WI-13's; this fails if and only if the Shell stops going through
        # the seam.
        state = _game(RecordingToolkit()).session.state

        self.assertEqual(frame_for(state), compose_picture(state))


class TheSingleCommandTest(unittest.TestCase):
    """``/usr/bin/python3 -m terminal_game`` is the one way in."""

    def test_the_package_is_runnable_and_runs_the_wiring(self):
        import terminal_game.__main__ as entry
        from terminal_game.shell.game import main

        self.assertIs(main, entry.main)


class TheSuiteStillOpensNothingTest(unittest.TestCase):
    def test_no_toolkit_interpreter_has_been_created(self):
        # The composition root imports the Tk modules only inside ``main``,
        # so importing it here is harmless -- and this is where that would
        # stop being true.
        import tkinter

        self.assertIsNone(tkinter._default_root)


if __name__ == "__main__":
    unittest.main()
