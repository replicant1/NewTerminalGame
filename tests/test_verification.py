"""WI-17 — checks that used to need a human, converted into checks that do not.

Converting a human check into an agent check is this item's purpose: every
one moved out of the pack is one the user does not have to do, and the pack
is only honest if what is left in it is genuinely irreducible.

**What is here is the keysym spelling of the four arrow keys.**  WI-6 proves
that a key event reaches a binding and that ``event.keysym`` comes back
``"q"`` — but only for ``q``. WI-13 keys its table on ``"Up"``, ``"Down"``,
``"Left"`` and ``"Right"``, and **nothing anywhere proves those are the names
Tk actually reports.** A bind-time check only proves the names are accepted
as *sequences*; a misspelling would bind happily and never fire, and CTRL-1
would then be a requirement that passes its unit tests and does not work.

That check needs a mapped, focused window — ``event_generate`` on a withdrawn
toplevel is accepted and delivers nothing — so it is marked ``needs_window``
and excluded from the default suite. **Only the physical keypress stays
human**, which is the honest irreducible.

The window pattern here is WI-7's, deliberately and unchanged: a watchdog
through ``after`` inside ``mainloop``, a belt-and-braces second close, and
the window reaped whatever happens. Section 1.5 says the hazard is a second
pattern, not a second author.
"""

from __future__ import annotations

from typing import Dict, List

import pytest

from terminal_game.application.turn import Intent
from terminal_game.presentation.keys import (
    ARROW_INTENTS,
    QUIT_KEYSYMS,
    TRANSLATED_KEYSYMS,
    intent_for,
)
from terminal_game.shell.window import GameWindow


def test_the_arrow_names_this_file_checks_are_the_ones_wi13_relies_on() -> None:
    """A guard, so the ``needs_window`` test below cannot drift out of step.

    If WI-13 ever re-keys its table, the excluded test would go on checking
    the old names and nobody would notice, because it does not run by
    default. This one does.
    """
    assert set(ARROW_INTENTS) == {"Up", "Down", "Left", "Right"}
    assert set(TRANSLATED_KEYSYMS) == set(ARROW_INTENTS) | set(QUIT_KEYSYMS)


@pytest.mark.needs_window
class TestKeysTkActuallyReports:
    """Excluded from the default suite. Section 1.5 applies without exception.

    Run under a deadline **outside** pytest — an internal timeout does not
    help when a hang is inside ``mainloop``:

        .venv/bin/python -m pytest -q -m needs_window
    """

    def test_every_arrow_key_arrives_under_the_name_wi13_expects(self, tk_root) -> None:
        """CTRL-1, closed properly: the names in WI-13's table are Tk's own.

        All four in one window, because opening four is four times the
        exposure on somebody's desktop for no more information.

        The assertion is on the **intent**, not just the keysym, so this
        fails whether Tk reports a different name or WI-13 maps it to the
        wrong direction.
        """
        window = GameWindow(master=tk_root)
        seen = {}  # type: Dict[str, str]
        try:
            window.bind_key("<Key>", lambda event: seen.setdefault(
                event.keysym, event.keysym))

            def press_all() -> None:
                for sequence in ("<Up>", "<Down>", "<Left>", "<Right>"):
                    window._root.event_generate(sequence, when="now")
                window.close()

            window.after(300, press_all)
            window.after(5000, window.close)  # belt and braces: always an exit
            window.show()
            window._root.focus_force()
            window.run()
        finally:
            window.close()

        assert sorted(seen) == ["Down", "Left", "Right", "Up"], (
            "Tk reported {} for the arrow keys; WI-13's table is keyed on "
            "{}".format(sorted(seen), sorted(ARROW_INTENTS))
        )
        assert {keysym: intent_for(keysym) for keysym in seen} == {
            "Up": Intent.MOVE_NORTH,
            "Down": Intent.MOVE_SOUTH,
            "Left": Intent.MOVE_WEST,
            "Right": Intent.MOVE_EAST,
        }

    def test_a_key_that_means_nothing_still_arrives_and_still_means_nothing(
        self, tk_root
    ) -> None:
        """CTRL-5's control, and the reason the test above is not vacuous.

        If *no* key event were being delivered at all, a test asserting that
        the arrows arrive would fail — but a test asserting that other keys
        do nothing would pass for the wrong reason. This shows delivery is
        working and translation is what discards the key, not the wiring.
        """
        window = GameWindow(master=tk_root)
        seen = []  # type: List[str]
        try:
            window.bind_key("<Key>", lambda event: seen.append(event.keysym))

            def press_then_close() -> None:
                window._root.event_generate("<Key-a>", when="now")
                window.close()

            window.after(300, press_then_close)
            window.after(5000, window.close)
            window.show()
            window._root.focus_force()
            window.run()
        finally:
            window.close()

        assert seen == ["a"], "the key never arrived, so this proves nothing"
        assert intent_for("a") is None


@pytest.mark.needs_window
class TestWhatCanBeCheckedOnTheRealGame:
    """Everything an agent can settle about the running game, in one window.

    One window rather than six, because each one is a disturbance on
    somebody's desk and none of these checks needs its own. Section 1.5
    applies without exception; the pattern is WI-7's, unchanged.

    **What is deliberately absent:** anything about how it *looks*. This can
    ask Tk what the title string is; it cannot see the titlebar. It can ask
    where the window was placed; it cannot see whether that is a sensible
    place on this person's desk. Those are in the human pack, and the pack is
    only honest if what is left in it is genuinely irreducible.
    """

    def test_the_running_game_is_titled_sized_and_placed_as_specified(
        self, tk_root
    ) -> None:
        """WIN-1, WIN-2, WIN-3 and WI-14b's placement, on the real thing.

        Read from inside an ``after`` callback while the window is up, then
        closed by the same callback — so the failure mode of every assertion
        is a closed window and a red test.
        """
        from terminal_game.shell import placement
        from terminal_game.shell.game import build_game

        game = build_game(master=tk_root, seed=11)
        seen = {}  # type: Dict[str, object]
        try:
            game.start()
            intended = game.place()

            def look_then_close() -> None:
                window = game.window
                seen["mapped"] = window.is_on_screen()
                seen["title"] = window.title
                seen["size"] = window.pixel_size
                seen["position"] = window.position()
                seen["ground"] = window.ground
                # Lane B's 1.4 check, the half an agent can do: Tk accepts an
                # absolute coordinate and reports the same one back. Whether
                # Tk's (0, 0) is the display server's (0, 0) needs an eye.
                window.move_to(placement.Point(600, 300))
                seen["round_trip"] = window.position()
                window.close()

            game.window.show()
            game.window.after(400, look_then_close)
            game.window.after(5000, game.window.close)  # always an exit
            game.window.run()
        finally:
            game.window.close()

        assert seen.get("mapped") is True, "the window never reached the screen"
        assert seen["title"] == "Terminal Game"        # WIN-3
        assert seen["size"] == (400, 570)              # WIN-2
        assert seen["ground"] == "#000000"             # WIN-2's black ground
        assert seen["position"] == intended            # WI-14b
        assert seen["round_trip"] == placement.Point(600, 300)
        assert not game.window.is_open
