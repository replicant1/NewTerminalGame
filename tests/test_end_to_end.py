"""WI-16 — the assembled game, driven through the journeys no unit test covers.

Everything here plays a **whole game**: a real maze, the real resolver, the
real ghost policy, the real composer and the real surface, joined exactly as
``build_game`` joins them.  What is asserted is what a player would see at the
end of it.

**Headless throughout.** ``build_game(master=tk_root)`` builds the window
withdrawn and ``start()`` is never called, so no timer runs and nothing
reaches the screen; ``Game.tick()`` is public and is what drives time here.
There is exactly one Tk interpreter in the suite — the session fixture's —
because a second ``tkinter.Tk()`` can crash this build (measured under WI-6).

**The positions are built; the verdicts are not.** Every board below is set up
and then *played*, and the outcome is whatever the rules produce. No test
stamps an outcome and expects it to be believed: ``GameState.outcome`` is a
cache the resolver writes, ``turn.outcome_of`` is the derived truth, and on a
hand-built board they can disagree.

What is deliberately **not** re-asserted here: the turn resolver's step order
(``tests/test_turn.py``), the session's three states
(``tests/test_session.py``), the status strings (``tests/test_status.py``),
the composer's mapping (``tests/test_frame.py``) or the painter
(``tests/test_surface.py``).  These are journeys, not a second opinion.
"""

from __future__ import annotations

import pytest

from terminal_game.domain.state import Outcome
from terminal_game.presentation.frame import GHOST_GLYPHS, PLAYER_GLYPHS, STATUS_ROW
from terminal_game.presentation.status import status_text
from terminal_game.shell.game import build_game

# A corridor ring with no dead ends, well clear of the border.  Small enough
# that a whole game is a handful of turns, and — being a ring — it has no
# junctions at all, so the ghost never consults the random source and the
# journeys below do not depend on a seed.  That is stated rather than relied
# on quietly: see `test_the_journeys_do_not_depend_on_the_seed`.
RING = """
    .......
    .#####.
    .#####.
    .#####.
    .......
"""
RING_AT = (6, 12)

#: Two corridor squares side by side, and nothing else.  ``new_game`` puts the
#: player on one and the ghost on the other, with the game's only dot on the
#: ghost's square — so one move eats the last dot *and* walks into the ghost.
#: **That is the END-3 board**: the two step orderings give different answers
#: on it, and on no board in an ordinary maze.
END3_BOARD = ".."
END3_AT = (9, 14)

_KEY = {(1, 0): "Right", (-1, 0): "Left", (0, 1): "Down", (0, -1): "Up"}


def follow_the_corridor(game, heading, limit=400):
    """Play the player like the ghost plays itself: straight on, else turn.

    Never turns back the way it came, so on a ring it circulates. Returns the
    number of turns taken. A turn is one player move followed by one tick, so
    the ghost really is moving throughout.
    """
    turns = 0
    while game.outcome is Outcome.UNDECIDED and turns < limit:
        back = (-heading[0], -heading[1])
        for step in [heading] + [d for d in _KEY if d not in (heading, back)]:
            before = game.state.player
            game.handle_key(_KEY[step])
            if game.state.player != before:
                heading = step
                break
        if game.outcome is Outcome.UNDECIDED:
            game.tick()
        turns += 1
    return turns


@pytest.fixture
def ring_game(tk_root, draw):
    """A game on the ring, built but not started: no timer, nothing on screen."""
    def build(seed=0):
        return build_game(
            master=tk_root, seed=seed, maze=draw(RING, at=RING_AT)
        )
    return build


@pytest.fixture
def end3_game(tk_root, draw):
    """A game on the two-square END-3 board."""
    def build(seed=0):
        return build_game(
            master=tk_root, seed=seed, maze=draw(END3_BOARD, at=END3_AT)
        )
    return build


class TestAGamePlayedToAWin:
    """A complete playthrough that clears the maze. END-2, GAME-2, SCORE-2."""

    def test_the_game_is_won(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (-1, 0))
        assert game.outcome is Outcome.CLEARED

    def test_every_dot_was_eaten(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (-1, 0))
        assert game.state.dots_remaining == 0

    def test_the_final_score_is_one_for_every_dot_eaten(self, ring_game):
        game = ring_game()
        started_with = game.state.dots_remaining
        follow_the_corridor(game, (-1, 0))
        assert game.state.score == started_with == 19

    def test_the_status_line_says_cleared_with_the_final_score(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (-1, 0))
        assert game.field.row_text(STATUS_ROW).rstrip() == status_text(
            Outcome.CLEARED, game.state.score
        )

    def test_the_ghost_was_moving_throughout(self, ring_game):
        # Otherwise the "win" would just be a walk round an empty board, and
        # GHOST-1 would be untested by this journey.
        game = ring_game()
        started_at = game.state.ghost
        follow_the_corridor(game, (-1, 0))
        assert game.state.ghost != started_at


class TestAGamePlayedToALoss:
    """A complete playthrough that ends in the ghost. END-1."""

    def test_the_game_is_lost(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.outcome is Outcome.CAUGHT

    def test_the_two_are_on_one_square(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.state.player == game.state.ghost

    def test_dots_are_left_uneaten(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.state.dots_remaining > 0

    def test_the_status_line_says_caught_with_the_final_score(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.field.row_text(STATUS_ROW).rstrip() == status_text(
            Outcome.CAUGHT, game.state.score
        )

    def test_the_picture_shows_the_ghost_over_the_player(self, ring_game):
        # END-4: *"when both actors are on one square the ghost is what you
        # see"*. The last picture the player is left looking at has to show
        # what happened, and this is the journey that produces the case.
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        square = game.state.player
        column, row = 2 * square.x, square.y
        centre = game.field[column, row].glyph
        assert centre == GHOST_GLYPHS[1]
        assert [game.field[column + offset, row].glyph for offset in (-1, 0, 1)] == list(
            GHOST_GLYPHS
        )

    def test_no_part_of_the_player_shows_through(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        square = game.state.player
        flanks = [
            game.field[2 * square.x + offset, square.y].glyph for offset in (-1, 1)
        ]
        assert PLAYER_GLYPHS[0] not in flanks
        assert PLAYER_GLYPHS[2] not in flanks


class TestTheEndThreeBoardPlayedToItsDecision:
    """END-3: *"eating the last dot on the ghost's square is a loss"*.

    The two step orderings — eat then test the win, versus test the collision
    first — give **different answers** on this board and the same answer on
    every other. It is now structural in the resolver, so what this journey
    establishes is that the assembled game behaves that way end to end, not
    that the resolver does. Assert the seam, not both sides of it.
    """

    def test_the_board_really_is_the_discriminating_one(self, end3_game):
        # Otherwise the assertion below would pass on any board at all. One
        # dot, and it is on the ghost's square.
        game = end3_game()
        assert game.state.dots_remaining == 1
        assert game.state.ghost in game.state.dots
        assert game.state.player != game.state.ghost

    def test_it_is_a_loss_and_not_a_win(self, end3_game):
        game = end3_game()
        toward = "Right" if game.state.ghost.x > game.state.player.x else "Left"
        game.handle_key(toward)
        assert game.outcome is Outcome.CAUGHT
        assert game.outcome is not Outcome.CLEARED

    def test_the_last_dot_was_eaten_on_the_way(self, end3_game):
        # Both halves happened: the board is cleared of dots *and* lost. If
        # the move had been refused, or the dot left uneaten, the board would
        # not be the one END-3 is about.
        game = end3_game()
        toward = "Right" if game.state.ghost.x > game.state.player.x else "Left"
        game.handle_key(toward)
        assert game.state.dots_remaining == 0
        assert game.state.score == 1

    def test_the_status_line_says_caught(self, end3_game):
        # What the player is left looking at. A board with no dots left that
        # announced CLEARED would be END-3 broken in the one place the player
        # would actually notice.
        game = end3_game()
        toward = "Right" if game.state.ghost.x > game.state.player.x else "Left"
        game.handle_key(toward)
        assert game.field.row_text(STATUS_ROW).rstrip() == status_text(
            Outcome.CAUGHT, 1
        )
        assert "CLEARED" not in game.field.row_text(STATUS_ROW)


class TestAfterTheDecisionTheGameIsFrozen:
    """END-5: the last picture stays, and nothing moves it."""

    @pytest.fixture
    def decided(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.outcome is Outcome.CAUGHT
        return game

    def test_a_tick_moves_nothing(self, decided):
        before = (decided.state.player, decided.state.ghost, decided.state.score)
        decided.tick()
        assert (decided.state.player, decided.state.ghost, decided.state.score) == before

    def test_an_arrow_moves_nothing(self, decided):
        before = (decided.state.player, decided.state.ghost, decided.state.score)
        for key in ("Up", "Down", "Left", "Right"):
            decided.handle_key(key)
        assert (decided.state.player, decided.state.ghost, decided.state.score) == before

    def test_it_stays_frozen_however_long_you_leave_it(self, decided):
        before = decided.field.rows()
        before = list(before)
        for _ in range(50):
            decided.tick()
            decided.handle_key("Up")
            decided.handle_key("Right")
        assert list(decided.field.rows()) == before

    def test_the_outcome_does_not_change(self, decided):
        for _ in range(20):
            decided.tick()
        assert decided.outcome is Outcome.CAUGHT

    def test_the_timer_is_not_left_running(self, decided):
        # A beat still firing into a decided game is a tick that moves
        # nothing, forever.
        assert not decided.timer_is_running


class TestQuitting:
    """END-6 and CTRL-4: ``q`` is accepted in Playing and in Decided."""

    @pytest.mark.parametrize("key", ["q", "Q"])
    def test_quitting_a_game_in_play_ends_it(self, ring_game, key):
        game = ring_game()
        assert game.is_running
        game.handle_key(key)
        assert not game.is_running

    @pytest.mark.parametrize("key", ["q", "Q"])
    def test_quitting_a_decided_game_ends_it(self, ring_game, key):
        game = ring_game()
        follow_the_corridor(game, (1, 0))
        assert game.outcome is Outcome.CAUGHT
        assert game.is_running          # decided is still running: END-5
        game.handle_key(key)
        assert not game.is_running

    def test_quitting_closes_the_window(self, ring_game):
        # WIN-5 under assumption P1: reaching Ended closes the window, and
        # with the entry point having nothing after run(), the process
        # follows.
        game = ring_game()
        assert game.window.is_open
        game.handle_key("q")
        assert not game.window.is_open

    def test_nothing_else_ends_the_game(self, ring_game):
        # CTRL-5: a representative spread of keys that mean nothing.
        game = ring_game()
        for key in ("a", "Z", "5", "F1", "Escape", "space", "Shift_L", "Return"):
            game.handle_key(key)
        assert game.is_running
        assert game.outcome is Outcome.UNDECIDED


class TestTheJourneysAreWorthTrusting:
    """Guards that keep the journeys above from passing for the wrong reason."""

    def test_the_journeys_do_not_depend_on_the_seed(self, ring_game):
        # Stated rather than assumed: a ring has no junctions, so the ghost
        # never consults the random source and every seed walks the same
        # maze. Measured on a two-loop fixture during WI-16's planning, where
        # seeds 7 and 8 gave an identical walk. **A test elsewhere that wants
        # different seeds to differ needs a maze with junctions.**
        outcomes = []
        for seed in (0, 1, 7, 42, 999):
            game = ring_game(seed=seed)
            follow_the_corridor(game, (-1, 0))
            outcomes.append((game.outcome, game.state.score))
        assert len(set(outcomes)) == 1

    def test_the_two_journeys_really_do_end_differently(self, ring_game):
        # The win and the loss differ only in which way the player sets off.
        # If they ever agreed, one of them would be proving nothing.
        won = ring_game()
        follow_the_corridor(won, (-1, 0))
        lost = ring_game()
        follow_the_corridor(lost, (1, 0))
        assert won.outcome is Outcome.CLEARED
        assert lost.outcome is Outcome.CAUGHT

    def test_a_journey_reaches_a_decision_rather_than_running_out(self, ring_game):
        # `follow_the_corridor` stops at a limit as well as at a decision. A
        # journey that hit the limit would report whatever it had, silently.
        game = ring_game()
        turns = follow_the_corridor(game, (-1, 0))
        assert turns < 400
        assert game.outcome is not Outcome.UNDECIDED


class TestTheDefaultSuitePutsNoWindowOnTheScreen:
    """WI-16's own bar, for the assembled game rather than for the surface."""

    def test_a_built_game_is_not_on_screen(self, ring_game):
        game = ring_game()
        assert not game.window.is_on_screen()

    def test_playing_a_whole_game_puts_nothing_on_screen(self, ring_game):
        game = ring_game()
        follow_the_corridor(game, (-1, 0))
        assert not game.window.is_on_screen()
        assert not game.window._root.winfo_viewable()

    def test_building_a_game_starts_no_timer(self, ring_game):
        # `start()` is what begins the beat, and no journey here calls it.
        # A real timer running inside the suite would make it wall-clock
        # dependent and would outlive the test.
        game = ring_game()
        assert not game.timer_is_running

    def test_the_session_root_was_never_mapped(self, tk_root):
        assert tk_root.state() == "withdrawn"
        assert not tk_root.winfo_ismapped()
        assert not tk_root.winfo_viewable()
