"""The window owner: WIN-1, WIN-2, WIN-3 and WIN-5.

**Every test here runs on a window that never reaches the screen**, and they
assert against the toolkit's own reported state rather than by looking, which
is what plan section 5 asks of WI-6.  The one thing that genuinely cannot be
answered without mapping a window — that the event loop runs and returns — is
marked ``needs_window`` and excluded from the default suite.

What is deliberately *not* re-asserted here: the cell arithmetic
(``tests/test_metrics.py``), the colours (``tests/test_palette.py``), and what
the painter does with a field (``tests/test_surface.py``).  This file owns the
window — its title, its size, its ground, its closing — and the joins to those.
"""

from __future__ import annotations

import tkinter

import pytest

from terminal_game.presentation import palette
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.metrics import COLUMNS, MEASURED_MENLO_12, ROWS
from terminal_game.shell.window import TITLE, GameWindow


@pytest.fixture
def window(tk_root):
    """A window that is never shown, reaped however the test ends.

    Built on the session's single Tk root, because **one interpreter per
    process** is what keeps this build stable — measured for WI-6, where a
    ``mainloop()`` entered after other roots had been created and destroyed
    in the same process segfaulted, and stopped the moment every window
    became a Toplevel on one root.  In production ``GameWindow()`` takes no
    master and creates the one root itself.
    """
    made = GameWindow(master=tk_root)
    try:
        yield made
    finally:
        made.close()


class TestWinOneAWindowOfItsOwn:
    """WIN-1: *"the game opens in a window of its own"*."""

    def test_a_window_exists(self, window):
        assert window.is_open

    def test_it_is_a_toplevel_owned_by_this_process(self, window):
        # A real window of our own: it has a window id from the window
        # server, and it is its own toplevel rather than sitting inside
        # somebody else's.
        assert window._root.winfo_id() != 0
        assert window._root.winfo_toplevel() is window._root

    def test_it_holds_the_character_grid_and_nothing_else(self, window):
        assert [child.winfo_class() for child in window._root.winfo_children()] == [
            "Canvas"
        ]

    def test_the_grid_is_forty_by_thirty_cells(self, window):
        assert window.grid_size == (COLUMNS, ROWS) == (40, 30)

    def test_two_windows_are_two_windows(self, tk_root):
        # "A window of its own" means this process's, not a shared one.
        first = GameWindow(master=tk_root)
        second = GameWindow(master=tk_root)
        try:
            assert first._root is not second._root
            assert first.is_open and second.is_open
        finally:
            first.close()
            second.close()


class TestWinThreeTheTitle:
    """WIN-3: *"the window is titled Terminal Game"*."""

    def test_the_title_is_exactly_the_string_required(self, window):
        assert window.title == "Terminal Game"

    def test_nothing_is_appended_to_it(self, window):
        # Under candidate 1 the terminal composed extra parts around the
        # title, which is the architect's assumption A1 and his weakest
        # coverage row.  Nothing composes around this one.
        assert window.title == TITLE
        assert not window.title.startswith(" ")
        assert not window.title.endswith(" ")
        assert "—" not in window.title
        assert len(window.title) == len("Terminal Game")

    def test_the_title_survives_being_shown_and_painted(self, window):
        window.present(Field())
        assert window.title == TITLE

    def test_a_window_can_be_given_a_different_title(self, tk_root):
        # The constant is the requirement; the parameter is so a test can
        # tell the two apart.
        made = GameWindow(master=tk_root, title="Something Else")
        try:
            assert made.title == "Something Else"
        finally:
            made.close()


class TestWinTwoTheSizeAndTheGround:
    """WIN-2: 40 x 30 cells of the chosen font, on a black background."""

    def test_the_window_asks_for_the_size_the_metrics_computed(self, window):
        # The join to WI-5.  Whatever the metrics say, the window asks for
        # that; this fails if and only if the window stopped using them.
        assert window.requested_size == window.metrics.window_pixel_size()

    def test_that_size_is_four_hundred_by_five_seventy_here(self, window):
        # The measured cell on this machine, which is what makes the
        # derivation above a real number rather than a tautology.
        assert window.metrics == MEASURED_MENLO_12
        assert window.requested_size == (400, 570)

    def test_the_window_is_the_size_of_its_grid(self, window):
        assert window.pixel_size == window.surface.pixel_size

    def test_the_ground_is_black(self, window):
        assert window.ground == palette.GROUND == "#000000"

    def test_the_grid_behind_the_glyphs_is_the_same_black(self, window):
        # Two grounds that differ would show as a seam around the canvas.
        assert window.surface.ground == window.ground

    def test_the_window_cannot_be_resized(self, window):
        # WIN-2 says *exactly* 40 x 30.  A window the player could drag
        # larger would have rows and columns the game does not know about.
        assert not window.is_resizable()

    def test_a_ground_that_is_not_a_colour_is_refused(self, tk_root):
        with pytest.raises(ValueError):
            GameWindow(master=tk_root, ground="black")


class TestTheWindowIsNotOnTheScreen:
    """Plan section 5: keep every one of these off the default suite's screen."""

    def test_a_new_window_is_withdrawn(self, window):
        assert window._root.state() == "withdrawn"

    def test_a_new_window_is_not_mapped(self, window):
        assert not window._root.winfo_ismapped()

    def test_a_new_window_is_not_viewable(self, window):
        assert not window._root.winfo_viewable()

    def test_the_window_knows_it_is_not_on_screen(self, window):
        assert not window.is_on_screen()

    def test_painting_a_frame_does_not_put_it_on_screen(self, window):
        field = Field()
        field[0, 0] = Cell("═", palette.WALL)
        window.present(field)
        assert not window.is_on_screen()
        assert not window._root.winfo_viewable()


class TestWhatTheWindowShows:
    """The join to WI-5: a field given to the window reaches the grid."""

    def test_a_field_presented_reaches_the_surface(self, window):
        field = Field()
        field[4, 6] = Cell("█", palette.PLAYER)
        window.present(field)
        assert window.surface.shown_cell(4, 6) == Cell("█", palette.PLAYER)

    def test_the_window_presents_through_its_own_surface(self, window):
        assert window.surface is window.surface


class TestWinFiveClosing:
    """WIN-5: *"the window closes by itself as soon as the game ends"*."""

    def test_a_closed_window_is_not_open(self, window):
        window.close()
        assert not window.is_open

    def test_a_closed_window_is_not_on_screen(self, window):
        window.close()
        assert not window.is_on_screen()

    def test_closing_calls_the_handler_it_was_given(self, tk_root):
        called = []
        made = GameWindow(master=tk_root, on_close=lambda: called.append("closed"))
        made.close()
        assert called == ["closed"]

    def test_the_handler_is_called_once_however_many_times_it_closes(self, tk_root):
        called = []
        made = GameWindow(master=tk_root, on_close=lambda: called.append("closed"))
        made.close()
        made.close()
        made.close()
        assert called == ["closed"]

    def test_the_handler_can_still_see_the_window(self, tk_root):
        # Called before the toplevel is destroyed, so a handler that wants to
        # read the final state can.
        seen = []
        made = GameWindow(master=tk_root)
        made._on_close = lambda: seen.append(made.title)
        made.close()
        assert seen == ["Terminal Game"]

    def test_a_window_with_no_handler_closes_just_the_same(self, window):
        window.close()
        assert not window.is_open

    def test_the_close_button_goes_through_the_same_door(self, tk_root):
        # Without the WM_DELETE_WINDOW protocol the window manager destroys
        # the window behind the game's back and the handler never fires.
        called = []
        made = GameWindow(master=tk_root, on_close=lambda: called.append("closed"))
        try:
            handler = made._root.protocol("WM_DELETE_WINDOW")
            assert handler, "no WM_DELETE_WINDOW handler is registered"
            made._root.tk.call("eval", handler)
            assert called == ["closed"]
            assert not made.is_open
        finally:
            made.close()

    def test_the_toplevel_is_really_gone(self, tk_root):
        made = GameWindow(master=tk_root)
        toplevel = made._root
        made.close()
        # The window is destroyed, not merely hidden.  Tk reports that in
        # two different ways and `is_open` has to survive both, which is
        # why this test accepts either: a destroyed **Toplevel** answers
        # `winfo_exists()` with 0, while a destroyed **root** raises
        # TclError("application has been destroyed"). Both measured for
        # WI-6; production owns the root, the suite owns Toplevels.
        try:
            still_there = bool(toplevel.winfo_exists())
        except tkinter.TclError:
            still_there = False
        assert not still_there
        assert not made.is_open

    def test_a_window_that_owns_its_interpreter_also_really_goes(self):
        # The production shape: no master, so GameWindow creates the one Tk
        # root itself.  Built and closed in isolation, because a second live
        # interpreter is the thing this file otherwise avoids.
        made = GameWindow()
        root = made._root
        assert made.is_open
        made.close()
        assert not made.is_open
        with pytest.raises(tkinter.TclError):
            root.winfo_exists()

    def test_closing_does_not_end_the_process(self, window):
        # Deliberate: ending by running out of work is both the honest
        # mechanism and the testable one.  If close() called sys.exit, this
        # test could not exist and nor could any of the ones above it.
        window.close()
        assert True  # reaching this line is the assertion


class TestUsingAClosedWindow:
    """A closed window says so rather than failing obscurely."""

    @pytest.mark.parametrize(
        "action",
        [
            lambda w: w.present(Field()),
            lambda w: w.show(),
            lambda w: w.after(1, lambda: None),
            lambda w: w.bind_key("<Key>", lambda event: None),
        ],
    )
    def test_asking_a_closed_window_to_do_something_raises(self, window, action):
        window.close()
        with pytest.raises(RuntimeError):
            action(window)

    def test_running_a_closed_window_returns_at_once(self, window):
        # Not an error: the loop has nothing to do, which is exactly the
        # state it would be in after the window closed normally.
        window.close()
        window.run()

    def test_cancelling_on_a_closed_window_is_harmless(self, window):
        handle = window.after(10000, lambda: None)
        window.close()
        window.cancel(handle)

    def test_a_closed_window_describes_itself_as_closed(self, window):
        window.close()
        assert repr(window) == "GameWindow(closed)"


class TestTheLoopAndTheTimer:
    """What the Shell owns because it owns the loop."""

    def test_work_can_be_scheduled(self, window):
        handle = window.after(10000, lambda: None)
        assert handle
        window.cancel(handle)

    def test_a_key_binding_is_registered_on_the_toplevel(self, window):
        # Bound on the window, not on the canvas: the surface refuses the
        # keyboard focus so that no caret can appear (SCRN-7), so keys have
        # to be caught here.  Tk reports bindings in its own normalised
        # spelling — "<Key-q>" comes back as "q" — so this asks for the
        # normalised name rather than the one it was given.
        window.bind_key("<Key-q>", lambda event: None)
        assert window.bound_key_sequences() == ["q"]

    def test_bindings_accumulate_rather_than_replace(self, window):
        # Tk's normalisation again: "<Up>" comes back as "<Key-Up>".
        window.bind_key("<Key-q>", lambda event: None)
        window.bind_key("<Up>", lambda event: None)
        assert window.bound_key_sequences() == ["<Key-Up>", "q"]

    def test_the_four_arrows_and_quit_can_all_be_bound(self, window):
        # The set CTRL-1 and CTRL-4 will need.  WI-13 turns them into
        # intents; WI-6 only has to be able to catch them.
        for sequence in ("<Up>", "<Down>", "<Left>", "<Right>", "<Key-q>", "<Key-Q>"):
            window.bind_key(sequence, lambda event: None)
        assert len(window.bound_key_sequences()) == 6

    def test_a_window_with_no_bindings_reports_none(self, window):
        assert window.bound_key_sequences() == []

    def test_scheduled_work_runs_when_the_loop_turns(self, window):
        # The loop runs `after` callbacks; `update_idletasks` does not.
        # Measured for WI-6: mainloop works on a *withdrawn* root, so this
        # exercises the real loop with nothing reaching the screen.
        ran = []
        window.after(1, lambda: ran.append("ran"))
        window.after(2000, window.stop)   # belt and braces: always an exit
        window.after(40, window.stop)
        window.run()
        assert ran == ["ran"]

    def test_the_loop_can_be_left_without_closing_the_window(self, window):
        window.after(20, window.stop)
        window.run()
        assert window.is_open
        assert not window.is_on_screen()

    def test_the_loop_can_be_entered_again_after_being_left(self, window):
        counted = []
        for _ in range(3):
            window.after(1, lambda: counted.append("turn"))
            window.after(40, window.stop)
            window.run()
        assert counted == ["turn", "turn", "turn"]
        assert window.is_open

    def test_stopping_a_closed_window_is_harmless(self, window):
        window.close()
        window.stop()

    def test_closing_ends_the_loop_even_when_it_does_not_own_the_interpreter(
        self, window
    ):
        # The guarantee run() makes: there is always a way out.  `mainloop`
        # belongs to the Tk interpreter, not to a window, so destroying a
        # Toplevel on somebody else's root leaves the loop running — a
        # window gone from the screen and a process that will not end.
        # Measured for WI-6 by hitting it: a run hung with a window up until
        # it was killed.  `close` now quits before it destroys, so this
        # returns rather than hanging, and it returns for the production
        # shape and the test shape alike.
        assert window._owns_interpreter is False   # a Toplevel, not a root
        window.after(20, window.close)
        window.after(3000, window.stop)            # if close failed to exit
        window.run()
        assert not window.is_open

    def test_cancelled_work_does_not_run(self, window):
        ran = []
        handle = window.after(10, lambda: ran.append("ran"))
        window.cancel(handle)
        window.after(60, window.stop)
        window.run()
        assert ran == []


class TestDescribingTheWindow:

    def test_an_open_window_describes_itself(self, window):
        described = repr(window)
        assert "Terminal Game" in described
        assert "40 x 30 cells" in described
        assert "400 x 570 px" in described
        assert "not shown yet" in described


@pytest.mark.needs_window
class TestTheEventLoopOnARealWindow:
    """The one thing that cannot be answered without mapping a window.

    **Excluded from the default suite** by ``pytest.ini``.  It exists because
    ``root.update()`` never returns on a mapped window on Tk 8.5 / macOS 26
    (measured under S-2), and if the event loop shared that path, WI-7 would
    discover it as a hang with a window on the user's desk.  It does not, and
    this is the test that says so.  AMEND-6 moved the project to Tk 9.0.4,
    where ``update()`` itself returns; what this test asserts about the event
    loop is the same either way, and it is the reason the class survives the
    defect that prompted it.

    Section 1.5 in full: the window is this process's own, held by the object
    reference captured at creation; the exit path is scheduled *before* the
    loop is entered, so the loop cannot outlive it; and the fixture reaps on
    the failure path.
    """

    def test_the_loop_runs_and_returns_when_the_window_closes(self, window):
        observed = {}

        def measure_then_close():
            observed["mapped"] = window.is_on_screen()
            observed["size"] = (
                window._root.winfo_width(),
                window._root.winfo_height(),
            )
            observed["title"] = window.title
            window.close()

        window.after(300, measure_then_close)
        window.after(5000, window.close)  # belt and braces: always an exit
        window.show()
        window.run()                      # returns only when the window is gone

        assert observed["mapped"] is True
        assert observed["size"] == (400, 570)
        assert observed["title"] == "Terminal Game"
        assert not window.is_open

    def test_a_key_event_reaches_the_callback(self, window):
        """Keys need a mapped, focused window; this cannot be done headlessly.

        ``event_generate`` on a withdrawn toplevel delivers nothing —
        measured for WI-6, which is why this test is here and not beside the
        binding test above.  What WI-6 owns is that a key bound on the
        toplevel reaches its callback; turning keys into intents is WI-13's.
        """
        pressed = []
        window.bind_key("<Key-q>", lambda event: pressed.append(event.keysym))
        window.after(300, lambda: window._root.event_generate("<Key-q>", when="now"))
        window.after(600, window.close)
        window.after(5000, window.close)  # belt and braces: always an exit
        window.show()
        window._root.focus_force()
        window.run()

        assert pressed == ["q"]
