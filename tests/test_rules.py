"""WI-10 — the rules and the outcome. END-1, END-2, END-3, GAME-2, END-5.

**The question these tests have to answer is what a green suite would look like
if the two lines in `outcome_of` were the other way round.** The answer is: it
would look exactly like this one, except for the states where the player and
the ghost share a square *and* no dots remain. Reverse the order and those read
as a win instead of a loss.

So that state is tested three ways — constructed directly, arrived at by the
player eating the last dot on the ghost's square, and arrived at by the ghost
stepping onto a player who has just eaten the last dot elsewhere — and each of
those tests asserts `CAUGHT` where a reversed implementation would say
`CLEARED`. Every other test in this file passes under either order, and that is
precisely why they are not enough on their own.
"""

from __future__ import annotations

import unittest

from terminalgame.domain.game_state import GameState, Outcome, new_game
from terminalgame.domain.maze import EAST, NORTH, SOUTH, WEST, Maze
from terminalgame.domain.rules import (
    advance_ghost,
    advance_player,
    outcome_of,
    settle,
)

#    01234
#  0 #####
#  1 #   #
#  2 # # #
#  3 #   #
#  4 #####
RING = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


def ring_maze():
    return Maze.from_text("\n".join(RING))


def state_on_ring(player=(1, 1), ghost=(3, 3), dots=None, score=0,
                  heading=EAST, outcome=Outcome.PLAYING):
    maze = ring_maze()
    if dots is None:
        dots = set(maze.corridor_squares()) - {player}
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=heading, dots=dots, score=score,
                     outcome=outcome)


class MeetingTheGhost(unittest.TestCase):
    """END-1 — lost the moment the two share a square, whoever walked in."""

    def test_sharing_a_square_is_a_loss(self):
        self.assertEqual(
            Outcome.CAUGHT,
            outcome_of(state_on_ring(player=(2, 1), ghost=(2, 1))))

    def test_it_is_a_loss_when_the_player_walked_into_the_ghost(self):
        before = state_on_ring(player=(2, 1), ghost=(3, 1))
        after = advance_player(before, EAST)
        self.assertEqual((3, 1), after.player)
        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_it_is_a_loss_when_the_ghost_walked_into_the_player(self):
        before = state_on_ring(player=(3, 1), ghost=(2, 1))
        after = advance_ghost(before, (3, 1), EAST)
        self.assertEqual((3, 1), after.ghost)
        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_standing_apart_is_not_a_loss(self):
        self.assertEqual(
            Outcome.PLAYING,
            outcome_of(state_on_ring(player=(1, 1), ghost=(3, 3))))

    def test_being_one_square_apart_is_not_yet_a_loss(self):
        # Passing beside each other is not meeting; only the same square is.
        self.assertEqual(
            Outcome.PLAYING,
            outcome_of(state_on_ring(player=(1, 1), ghost=(2, 1))))


class EatingTheLastDot(unittest.TestCase):
    """END-2 and GAME-2 — won when the last dot is eaten."""

    def test_no_dots_left_is_a_win(self):
        self.assertEqual(
            Outcome.CLEARED,
            outcome_of(state_on_ring(player=(1, 1), ghost=(3, 3), dots=set())))

    def test_one_dot_left_is_not_yet_a_win(self):
        self.assertEqual(
            Outcome.PLAYING,
            outcome_of(state_on_ring(player=(1, 1), ghost=(3, 3),
                                     dots={(2, 3)})))

    def test_the_move_that_takes_the_last_dot_wins_the_game(self):
        before = state_on_ring(player=(2, 1), ghost=(3, 3), dots={(3, 1)})
        after = advance_player(before, EAST)
        self.assertEqual(Outcome.CLEARED, after.outcome)
        self.assertEqual(1, after.score)
        self.assertEqual(0, after.dots_remaining)


class TheLastDotOnTheGhostsSquare(unittest.TestCase):
    """END-3 — and the only place the order of the two tests shows.

    Every one of these asserts `CAUGHT` on a state where the player and the
    ghost share a square and no dots remain. A `outcome_of` that asked about
    dots first would answer `CLEARED` to all three, and would pass every other
    test in this file.
    """

    def test_a_constructed_state_with_both_conditions_is_a_loss(self):
        both = state_on_ring(player=(3, 1), ghost=(3, 1), dots=set())
        self.assertEqual(0, len(both.dots), "no dots left — a win, on its own")
        self.assertEqual(both.player, both.ghost, "together — a loss, on its own")
        self.assertEqual(Outcome.CAUGHT, outcome_of(both))

    def test_eating_the_last_dot_on_the_ghosts_square_is_a_loss(self):
        """END-3 in its own words, arrived at by a real move.

        The ghost stands on the last dot — which is possible because START-3
        excepts only the player's starting square, so the ghost's square is
        dotted from the beginning (WI-7).
        """
        before = state_on_ring(player=(2, 1), ghost=(3, 1), dots={(3, 1)})
        after = advance_player(before, EAST)

        # The dot really was eaten: this is a loss *instead of* a win, not a
        # move that failed to happen.
        self.assertEqual(1, after.score)
        self.assertEqual(0, after.dots_remaining)
        self.assertEqual((3, 1), after.player)
        self.assertEqual(after.player, after.ghost)

        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_the_ghost_stepping_onto_a_player_who_just_cleared_is_a_loss(self):
        # The other way round: no dots left, and the ghost walks in. Still a
        # loss, because the collision is asked about first.
        before = state_on_ring(player=(3, 1), ghost=(2, 1), dots=set())
        after = advance_ghost(before, (3, 1), EAST)
        self.assertEqual(Outcome.CAUGHT, after.outcome)

    def test_clearing_the_board_away_from_the_ghost_is_still_a_win(self):
        # The control for the three above: same "no dots left", ghost
        # elsewhere, and now it is the win. If this said CAUGHT the collision
        # test would be firing when it should not.
        before = state_on_ring(player=(2, 1), ghost=(1, 3), dots={(3, 1)})
        after = advance_player(before, EAST)
        self.assertEqual(Outcome.CLEARED, after.outcome)


class StillPlaying(unittest.TestCase):

    def test_dots_remaining_and_the_two_apart_is_still_playing(self):
        self.assertEqual(
            Outcome.PLAYING,
            outcome_of(state_on_ring(player=(1, 1), ghost=(3, 3),
                                     dots={(2, 1), (2, 3)})))

    def test_an_ordinary_move_leaves_the_game_playing(self):
        before = state_on_ring(player=(1, 1), ghost=(3, 3))
        after = advance_player(before, EAST)
        self.assertEqual(Outcome.PLAYING, after.outcome)
        self.assertEqual((2, 1), after.player)

    def test_a_fresh_game_is_playing(self):
        for seed in range(10):
            self.assertEqual(Outcome.PLAYING, outcome_of(new_game(seed)))


class ReadingTheOutcomeChangesNothing(unittest.TestCase):

    def test_outcome_of_does_not_touch_the_state(self):
        before = state_on_ring(player=(2, 1), ghost=(2, 1))
        snapshot = {field: getattr(before, field) for field in GameState.FIELDS}
        outcome_of(before)
        for field, value in snapshot.items():
            self.assertEqual(value, getattr(before, field))

    def test_settle_returns_the_same_state_when_nothing_has_changed(self):
        playing = state_on_ring(player=(1, 1), ghost=(3, 3))
        self.assertIs(playing, settle(playing))

    def test_settle_writes_the_outcome_when_it_has_changed(self):
        together = state_on_ring(player=(2, 1), ghost=(2, 1))
        self.assertEqual(Outcome.PLAYING, together.outcome)
        self.assertEqual(Outcome.CAUGHT, settle(together).outcome)


class OnceItHasEndedItHasEnded(unittest.TestCase):
    """END-5 — "everything stops"."""

    def test_the_arrow_keys_do_nothing_after_a_loss(self):
        over = state_on_ring(player=(2, 1), ghost=(2, 1),
                             outcome=Outcome.CAUGHT)
        for direction in (EAST, WEST, NORTH, SOUTH):
            self.assertIs(over, advance_player(over, direction))

    def test_the_arrow_keys_do_nothing_after_a_win(self):
        over = state_on_ring(player=(1, 1), ghost=(3, 3), dots=set(),
                             outcome=Outcome.CLEARED)
        for direction in (EAST, SOUTH):
            self.assertIs(over, advance_player(over, direction))

    def test_the_same_presses_would_have_worked_a_moment_earlier(self):
        # Without this, the two tests above pass against an advance_player
        # that never advances anything.
        playing = state_on_ring(player=(1, 1), ghost=(3, 3), dots=set(),
                                outcome=Outcome.PLAYING)
        self.assertIsNot(playing, advance_player(playing, EAST))

    def test_the_ghost_stands_still_after_the_game_has_ended(self):
        over = state_on_ring(player=(1, 1), ghost=(3, 3), dots=set(),
                             outcome=Outcome.CLEARED)
        self.assertIs(over, advance_ghost(over, (3, 1), NORTH))

    def test_a_win_cannot_be_turned_into_a_loss_afterwards(self):
        """The trap in recomputing an outcome that is already decided.

        `outcome_of` is a pure function of where the actors are and how many
        dots are left. A won game in which the ghost is later found on the
        player would therefore *read* as a loss — so `settle` must not ask
        again. END-5 says the ending a game got is the ending it keeps.
        """
        won_but_together = state_on_ring(player=(2, 1), ghost=(2, 1),
                                         dots=set(), outcome=Outcome.CLEARED)
        # Read cold, this state says CAUGHT ...
        self.assertEqual(Outcome.CAUGHT, outcome_of(won_but_together))
        # ... and settling it must not take the win away.
        self.assertEqual(Outcome.CLEARED, settle(won_but_together).outcome)
        self.assertIs(won_but_together, settle(won_but_together))

    def test_a_loss_stays_a_loss_even_once_the_board_is_empty(self):
        lost = state_on_ring(player=(2, 1), ghost=(3, 3), dots=set(),
                             outcome=Outcome.CAUGHT)
        self.assertEqual(Outcome.CAUGHT, settle(lost).outcome)


class TheGhostStep(unittest.TestCase):
    """`advance_ghost` — what a ghost move may and may not do."""

    def test_it_puts_the_ghost_where_it_was_told_and_turns_it(self):
        before = state_on_ring(player=(1, 1), ghost=(3, 3), heading=NORTH)
        after = advance_ghost(before, (3, 2), NORTH)
        self.assertEqual((3, 2), after.ghost)
        self.assertIs(NORTH, after.ghost_heading)

    def test_it_never_eats_a_dot_or_changes_the_score(self):
        """SCORE-4 — the ghost neither eats dots nor hides them."""
        before = state_on_ring(player=(1, 1), ghost=(3, 3),
                               dots={(3, 2), (2, 1)}, score=5)
        after = advance_ghost(before, (3, 2), NORTH)
        self.assertEqual(before.dots, after.dots)
        self.assertEqual(5, after.score)
        self.assertTrue(after.dot_at((3, 2)), "the ghost hid the dot it stood on")

    def test_it_never_moves_the_player(self):
        before = state_on_ring(player=(1, 1), ghost=(3, 3))
        self.assertEqual((1, 1), advance_ghost(before, (3, 2), NORTH).player)

    def test_it_has_no_opinion_about_where_the_ghost_should_go(self):
        # It takes the square the policy chose. Whether that square is a
        # sensible one is WI-9's question, and this deliberately does not ask:
        # a policy bug must show up in the policy's tests, not be masked here.
        before = state_on_ring(player=(1, 1), ghost=(1, 3))
        self.assertEqual((3, 1), advance_ghost(before, (3, 1), EAST).ghost)


class APlayedGameEndsOneWayOrTheOther(unittest.TestCase):
    """The two endings, reached by playing rather than by construction."""

    def test_a_game_can_be_won_by_eating_every_dot(self):
        # A three-dot game the player can finish without ever reaching the
        # ghost: east, east, south eats all three and stops at (3, 2), one
        # square short of the ghost at (3, 3).
        state = state_on_ring(player=(1, 1), ghost=(3, 3),
                              dots={(2, 1), (3, 1), (3, 2)})
        for direction in (EAST, EAST):
            state = advance_player(state, direction)
            self.assertEqual(Outcome.PLAYING, state.outcome)

        state = advance_player(state, SOUTH)
        self.assertEqual(3, state.score)
        self.assertEqual(0, state.dots_remaining)
        self.assertNotEqual(state.player, state.ghost)
        self.assertEqual(Outcome.CLEARED, state.outcome)

    def test_a_game_can_be_lost_by_walking_into_the_ghost(self):
        state = state_on_ring(player=(1, 1), ghost=(3, 1))
        state = advance_player(state, EAST)   # to (2, 1)
        self.assertEqual(Outcome.PLAYING, state.outcome)
        state = advance_player(state, EAST)   # to (3, 1) — the ghost
        self.assertEqual(Outcome.CAUGHT, state.outcome)

    def test_the_game_stops_dead_at_the_ending_it_reached(self):
        state = state_on_ring(player=(1, 1), ghost=(3, 1))
        state = advance_player(state, EAST)
        state = advance_player(state, EAST)   # caught
        ended = state
        for direction in (WEST, NORTH, SOUTH, EAST):
            state = advance_player(state, direction)
        self.assertIs(ended, state)


if __name__ == "__main__":
    unittest.main()
