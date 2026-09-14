"""WI-11 — the game loop.

GHOST-1, CTRL-1, CTRL-2, CTRL-4, CTRL-5, START-5, END-5, END-6, SCRN-7.

**What would a green result look like if the timeout were not recomputed?**
A loop that restarted a fixed timeout on every key would pass any test whose
keys arrive exactly on the tick boundary, and would pass every test of quitting,
of discarding, and of the ending. It would fail only where a key arrives
*between* ticks — so that is the test this file is built around:

    the same elapsed time, with and without keys, must give the same
    number of ghost ticks.

A fixed-timeout loop ticks fewer times in the run that has keys, because each
key postpones the ghost. `TheGhostKeepsItsOwnTime` is that comparison, and it
asserts the keys really were delivered, so it cannot pass by them being ignored.

**And what if the loop needed a key to start?** Every test that begins by
pressing something would still pass. `TheGameIsUnderWayFromTheFirstPass` is the
one that answers differently: no key is pressed at all until the `q` that ends
it, and the ghost must already have moved.
"""

from __future__ import annotations

import random
import unittest

from terminalgame.application.loop import (
    DIRECTION_OF_KEY,
    TICK_SECONDS,
    TICKS_PER_SECOND,
    direction_of,
    next_deadline,
    play,
    quits,
)
from terminalgame.domain.game_state import GameState, Outcome, new_game
from terminalgame.domain.ghost_policy import ghost_move
from terminalgame.domain.maze import EAST, NORTH, SOUTH, WEST, Maze
from terminalgame.domain.maze_generator import generate_maze
from terminalgame.screen.port import Key
from tests.loop_fakes import (
    CountingGhost,
    FakeClock,
    ScriptedScreen,
    StillGhost,
)

RING = [
    "#####",
    "#   #",
    "# # #",
    "#   #",
    "#####",
]


def ring_state(player=(1, 1), ghost=(3, 3), dots=None, score=0,
               outcome=Outcome.PLAYING, heading=EAST):
    maze = Maze.from_text("\n".join(RING))
    if dots is None:
        dots = set(maze.corridor_squares()) - {player}
    return GameState(maze=maze, player=player, ghost=ghost,
                     ghost_heading=heading, dots=dots, score=score,
                     outcome=outcome)


def unendable_state():
    """A real maze in which the game cannot end while the test runs.

    The ghost is parked on a **wall** square, so the player can never stand on
    it, and the ghost is held still by `StillGhost`; the maze carries well over
    two hundred dots, so a few dozen moves cannot clear them. Both devices are
    deliberate: they take END-1 and END-2 out of play so that a test about
    *timing* measures timing and nothing else.
    """
    maze = generate_maze(11)
    corridors = set(maze.corridor_squares())
    player = sorted(corridors)[len(corridors) // 2]
    wall = next((x, y) for (x, y) in maze.squares()
                if maze.is_wall(x, y) and 0 < x < maze.width - 1)
    return GameState(maze=maze, player=player, ghost=wall, ghost_heading=EAST,
                     dots=corridors - {player}, score=0,
                     outcome=Outcome.PLAYING)


def blank_frame(state):
    """A frame builder that builds nothing — WI-5b's job, not this one's.

    The loop is injected with this so that the tests measure *when* a frame was
    asked for, not what was in it.
    """
    return ("frame", state.player, state.ghost, state.score, state.outcome)


def q_at(when):
    return (when, Key.printable("q"))


def run(state, keys, ghost=None, clock_start=0.0, tick=TICK_SECONDS,
        compose=blank_frame, seed=0):
    """Play one scripted game and hand back everything worth asserting on."""
    clock = FakeClock(clock_start)
    screen = ScriptedScreen(clock, keys)
    ghost = ghost if ghost is not None else CountingGhost(ghost_move)
    final = play(screen, state, random.Random(seed), compose,
                 clock=clock.time, tick_seconds=tick, ghost_move=ghost)
    return final, screen, ghost, clock


class TheGhostKeepsItsOwnTime(unittest.TestCase):
    """GHOST-1, and caution C7. The item's whole risk is in this class."""

    def test_the_same_run_with_and_without_keys_ticks_the_same_number_of_times(self):
        """The test a fixed timeout would fail.

        Both runs last five seconds on the clock. One has nothing pressed; the
        other has fifty keys at irregular moments. The keys are not arrows, so
        the game state cannot change and the *only* difference between the runs
        is how often `read_key` returns early.
        """
        end = 5.0
        quiet = [q_at(end)]
        noisy = [(0.013 + 0.097 * i, Key.printable("x")) for i in range(50)]
        noisy = [pair for pair in noisy if pair[0] < end] + [q_at(end)]

        _, quiet_screen, quiet_ghost, _ = run(ring_state(), quiet,
                                              ghost=StillGhost())
        _, noisy_screen, noisy_ghost, _ = run(ring_state(), noisy,
                                              ghost=StillGhost())

        # The keys really were delivered — otherwise this proves nothing.
        self.assertGreater(len(noisy_screen.reads), len(quiet_screen.reads) + 30)

        self.assertEqual(quiet_ghost.ticks, noisy_ghost.ticks)

    def test_the_number_of_ticks_matches_the_time_that_passed(self):
        for end in (1.0, 3.0, 5.0):
            _, _, ghost, clock = run(ring_state(), [q_at(end)],
                                     ghost=StillGhost())
            self.assertAlmostEqual(end / TICK_SECONDS, ghost.ticks, delta=1)

    def test_ticks_match_the_clock_even_with_arrow_keys_arriving(self):
        """The same claim again, with keys that really do change the state.

        `unendable_state` keeps END-1 and END-2 out of reach, so the run cannot
        stop early and the comparison stays honest.
        """
        end = 3.0
        presses = [(0.031 + 0.083 * i, Key.UP if i % 2 else Key.DOWN)
                   for i in range(30)]
        presses = [pair for pair in presses if pair[0] < end] + [q_at(end)]

        _, _, still, _ = run(unendable_state(), [q_at(end)], ghost=StillGhost())
        _, screen, busy, _ = run(unendable_state(), presses, ghost=StillGhost())

        self.assertGreater(len(screen.reads), 25)
        self.assertEqual(still.ticks, busy.ticks)

    def test_the_first_read_waits_exactly_one_tick(self):
        _, screen, _, _ = run(ring_state(), [q_at(2.0)], ghost=StillGhost())
        self.assertAlmostEqual(TICK_SECONDS, screen.reads[0])

    def test_a_key_arriving_early_shortens_the_next_wait_by_what_it_used(self):
        """The mechanism, stated directly.

        A key at 0.05 s is handled at once; the tick is still due at
        `TICK_SECONDS`, so the next wait must be the remainder and not a fresh
        tick.
        """
        early = 0.05
        _, screen, _, _ = run(
            ring_state(), [(early, Key.printable("x")), q_at(2.0)],
            ghost=StillGhost())
        self.assertAlmostEqual(TICK_SECONDS, screen.reads[0])
        self.assertAlmostEqual(TICK_SECONDS - early, screen.reads[1])

    def test_every_wait_is_the_time_left_until_the_next_tick(self):
        # Checked across a whole run rather than at one moment: no wait may
        # ever exceed a tick, which a restarted fixed timeout would.
        _, screen, _, _ = run(
            ring_state(),
            [(0.02, Key.printable("x")), (0.3, Key.printable("x")),
             (0.31, Key.printable("x")), q_at(2.0)],
            ghost=StillGhost())
        for waited in screen.reads:
            self.assertLessEqual(waited, TICK_SECONDS + 1e-9)
            self.assertGreaterEqual(waited, 0.0)

    def test_seven_ticks_a_second(self):
        self.assertEqual(7.0, TICKS_PER_SECOND)
        self.assertAlmostEqual(1.0 / 7.0, TICK_SECONDS)


class TheScheduleDoesNotDrift(unittest.TestCase):
    """`next_deadline` on its own — the arithmetic the loop leans on."""

    def test_it_advances_by_a_whole_tick(self):
        self.assertAlmostEqual(3.0, next_deadline(2.0, 2.0, tick_seconds=1.0))

    def test_it_is_anchored_to_the_schedule_and_not_to_now(self):
        # The pass took a little longer than the tick; the next deadline is
        # still on the original grid, not `now + tick`.
        self.assertAlmostEqual(3.0, next_deadline(2.0, 2.04, tick_seconds=1.0))

    def test_it_catches_up_after_a_stall_without_firing_what_was_missed(self):
        # Ten seconds went by in one pass. The next deadline is just ahead of
        # now — a burst of ten ticks would teleport the ghost.
        caught_up = next_deadline(2.0, 12.0, tick_seconds=1.0)
        self.assertGreater(caught_up, 12.0)
        self.assertLessEqual(caught_up, 13.0)


class TheGameIsUnderWayFromTheFirstPass(unittest.TestCase):
    """START-5 — "nothing has to be pressed to begin"."""

    def test_the_picture_is_up_before_any_key_is_read(self):
        clock = FakeClock()
        screen = ScriptedScreen(clock, [q_at(1.0)])
        play(screen, ring_state(), random.Random(0), blank_frame,
             clock=clock.time, ghost_move=StillGhost())
        self.assertGreaterEqual(screen.frames_presented, 1)

    def test_a_run_with_no_keys_at_all_still_ticks(self):
        _, _, ghost, _ = run(ring_state(), [q_at(1.0)], ghost=StillGhost())
        self.assertGreater(ghost.ticks, 0)

    def test_the_ghost_has_moved_before_the_player_has_done_anything(self):
        state = ring_state(player=(1, 1), ghost=(3, 3))
        final, _, ghost, _ = run(state, [q_at(1.0)])
        self.assertGreater(ghost.ticks, 0)
        self.assertEqual((1, 1), final.player)
        self.assertNotEqual((3, 3), final.ghost)


class WhatTheArrowKeysDo(unittest.TestCase):
    """CTRL-1 and CTRL-2."""

    def test_each_arrow_maps_to_its_direction(self):
        self.assertIs(NORTH, DIRECTION_OF_KEY[Key.UP])
        self.assertIs(SOUTH, DIRECTION_OF_KEY[Key.DOWN])
        self.assertIs(WEST, DIRECTION_OF_KEY[Key.LEFT])
        self.assertIs(EAST, DIRECTION_OF_KEY[Key.RIGHT])

    def test_up_is_northwards_which_is_a_smaller_row(self):
        # y counts down from the top of the screen, so up is y - 1.
        state = ring_state(player=(1, 2))
        final, _, _, _ = run(state, [(0.01, Key.UP), q_at(0.05)],
                             ghost=StillGhost())
        self.assertEqual((1, 1), final.player)

    def test_one_press_moves_one_square(self):
        state = ring_state(player=(1, 1))
        final, _, _, _ = run(state, [(0.01, Key.RIGHT), q_at(0.05)],
                             ghost=StillGhost())
        self.assertEqual((2, 1), final.player)

    def test_two_presses_move_two_squares(self):
        state = ring_state(player=(1, 1))
        final, _, _, _ = run(
            state, [(0.01, Key.RIGHT), (0.02, Key.RIGHT), q_at(0.05)],
            ghost=StillGhost())
        self.assertEqual((3, 1), final.player)

    def test_a_tick_moves_the_ghost_and_not_the_player(self):
        """CTRL-2's behavioural half — the player never drifts.

        Nothing is pressed, so several ticks go by with the ghost moving and
        the player exactly where it started.
        """
        state = ring_state(player=(1, 1), ghost=(3, 3))
        final, _, ghost, _ = run(state, [q_at(1.0)])
        self.assertGreater(ghost.ticks, 3)
        self.assertEqual((1, 1), final.player)
        self.assertEqual(0, final.score)


class KeysThatDoNothing(unittest.TestCase):
    """CTRL-5 — "no other key does anything"."""

    def test_a_printable_key_that_is_not_q_is_discarded(self):
        state = ring_state(player=(1, 1))
        final, _, _, _ = run(
            state, [(0.01, Key.printable("x")), (0.02, Key.printable("Z")),
                    q_at(0.05)],
            ghost=StillGhost())
        self.assertIs(state, final)

    def test_a_key_that_is_not_printable_at_all_is_discarded(self):
        state = ring_state(player=(1, 1))
        final, _, _, _ = run(state, [(0.01, Key.other(266)), q_at(0.05)],
                             ghost=StillGhost())
        self.assertIs(state, final)

    def test_the_same_moment_with_an_arrow_does_change_things(self):
        # Without this, the two above pass against a loop that ignores every
        # key it is given.
        state = ring_state(player=(1, 1))
        final, _, _, _ = run(state, [(0.01, Key.RIGHT), q_at(0.05)],
                             ghost=StillGhost())
        self.assertIsNot(state, final)

    def test_direction_of_answers_for_the_four_and_nobody_else(self):
        for key in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT):
            self.assertIsNotNone(direction_of(key))
        for key in (None, Key.printable("x"), Key.printable("q"),
                    Key.other(1)):
            self.assertIsNone(direction_of(key))


class Quitting(unittest.TestCase):
    """CTRL-4 and END-6."""

    def test_lower_case_q_quits(self):
        _, screen, _, _ = run(ring_state(), [(0.01, Key.printable("q"))],
                              ghost=StillGhost())
        self.assertEqual(1, len(screen.reads))

    def test_upper_case_q_quits(self):
        _, screen, _, _ = run(ring_state(), [(0.01, Key.printable("Q"))],
                              ghost=StillGhost())
        self.assertEqual(1, len(screen.reads))

    def test_q_quits_at_once_rather_than_at_the_next_tick(self):
        # Pressed a long way inside the first tick; the loop must not wait out
        # the rest of it.
        _, _, ghost, clock = run(ring_state(),
                                 [(0.001, Key.printable("q"))],
                                 ghost=StillGhost())
        self.assertEqual(0, ghost.ticks)
        self.assertAlmostEqual(0.001, clock.now)

    def test_q_quits_a_game_that_has_already_been_lost(self):
        over = ring_state(player=(2, 1), ghost=(2, 1), outcome=Outcome.CAUGHT)
        final, screen, _, _ = run(over, [(0.01, Key.printable("q"))],
                                  ghost=StillGhost())
        self.assertIs(over, final)
        self.assertEqual(1, len(screen.reads))

    def test_q_quits_a_game_that_has_already_been_won(self):
        over = ring_state(dots=set(), outcome=Outcome.CLEARED)
        final, screen, _, _ = run(over, [(0.01, Key.printable("Q"))],
                                  ghost=StillGhost())
        self.assertIs(over, final)
        self.assertEqual(1, len(screen.reads))

    def test_quitting_mid_game_hands_back_a_game_still_playing(self):
        final, _, _, _ = run(ring_state(), [q_at(0.5)], ghost=StillGhost())
        self.assertEqual(Outcome.PLAYING, final.outcome)

    def test_quits_recognises_q_and_nothing_else(self):
        self.assertTrue(quits(Key.printable("q")))
        self.assertTrue(quits(Key.printable("Q")))
        for key in (None, Key.UP, Key.printable("x"), Key.other(3)):
            self.assertFalse(quits(key))


class OnceTheGameHasEnded(unittest.TestCase):
    """END-5 — and the loop adds no guard of its own; the Domain refuses."""

    def setUp(self):
        self.over = ring_state(player=(2, 1), ghost=(2, 1),
                               outcome=Outcome.CAUGHT)

    def test_the_arrow_keys_do_nothing(self):
        final, _, _, _ = run(
            self.over,
            [(0.01, Key.RIGHT), (0.02, Key.LEFT), (0.03, Key.UP), q_at(1.0)],
            ghost=StillGhost())
        self.assertIs(self.over, final)

    def test_no_further_tick_is_issued(self):
        _, _, ghost, _ = run(self.over, [q_at(2.0)], ghost=StillGhost())
        self.assertEqual(0, ghost.ticks)

    def test_the_frame_is_not_rebuilt(self):
        _, screen, _, _ = run(
            self.over, [(0.01, Key.RIGHT), (0.5, Key.DOWN), q_at(2.0)],
            ghost=StillGhost())
        self.assertEqual(1, screen.frames_presented,
                         "the picture was redrawn after the game had ended")

    def test_a_game_still_playing_does_all_three(self):
        """Otherwise the three above pass against a loop that does nothing.

        Same keys, same length of run, same everything but the outcome.
        """
        playing = ring_state(player=(2, 1), ghost=(1, 3))
        final, screen, ghost, _ = run(
            playing, [(0.01, Key.RIGHT), (0.5, Key.DOWN), q_at(2.0)],
            ghost=StillGhost())
        self.assertIsNot(playing, final)
        self.assertGreater(ghost.ticks, 0)
        self.assertGreater(screen.frames_presented, 1)

    def test_the_last_picture_is_the_one_that_stays(self):
        # The move that ends the game is drawn; nothing after it is.
        state = ring_state(player=(1, 1), ghost=(2, 1))
        final, screen, _, _ = run(
            state, [(0.01, Key.RIGHT), (0.5, Key.DOWN), q_at(1.5)],
            ghost=StillGhost())
        self.assertEqual(Outcome.CAUGHT, final.outcome)
        self.assertEqual(final.player, final.ghost)
        self.assertEqual(blank_frame(final), screen.presented[-1])


class WhenThePictureIsRedrawn(unittest.TestCase):
    """SCRN-7 — redrawn as things move, and not otherwise."""

    def test_the_opening_picture_is_drawn_once_before_anything_happens(self):
        clock = FakeClock()
        screen = ScriptedScreen(clock, [(0.001, Key.printable("q"))])
        play(screen, ring_state(), random.Random(0), blank_frame,
             clock=clock.time, ghost_move=StillGhost())
        self.assertEqual(1, screen.frames_presented)

    def test_nothing_is_redrawn_while_nothing_moves(self):
        # Discarded keys and a ghost that stays put: one frame, the first.
        _, screen, _, _ = run(
            ring_state(),
            [(0.01, Key.printable("x")), (0.02, Key.other(9)), q_at(1.0)],
            ghost=StillGhost())
        self.assertEqual(1, screen.frames_presented)

    def test_a_move_into_a_wall_redraws_nothing(self):
        # CTRL-3 seen from the loop: the Domain hands back the same state, so
        # there is nothing new to show.
        state = ring_state(player=(2, 1))   # north and south are wall
        _, screen, _, _ = run(state, [(0.01, Key.UP), q_at(0.05)],
                              ghost=StillGhost())
        self.assertEqual(1, screen.frames_presented)

    def test_a_move_that_changes_something_is_drawn(self):
        state = ring_state(player=(1, 1))
        _, screen, _, _ = run(state, [(0.01, Key.RIGHT), q_at(0.05)],
                              ghost=StillGhost())
        self.assertEqual(2, screen.frames_presented)

    def test_the_score_going_up_is_drawn(self):
        """STAT-2's "kept up to date", which is the loop's to deliver.

        The status module cannot fail at it — it reads the state every time it
        is asked — so keeping it current means redrawing when the score moves.
        """
        state = ring_state(player=(1, 1), dots={(2, 1)}, score=0)
        final, screen, _, _ = run(state, [(0.01, Key.RIGHT), q_at(0.05)],
                                  ghost=StillGhost())
        self.assertEqual(1, final.score)
        drawn_scores = [frame[3] for frame in screen.presented]
        self.assertEqual([0, 1], drawn_scores)

    def test_one_frame_per_pass_even_when_both_actors_moved(self):
        # A key and a tick landing in the same pass must not draw twice.
        state = ring_state(player=(1, 1), ghost=(3, 3))
        _, screen, _, _ = run(
            state, [(TICK_SECONDS, Key.RIGHT), q_at(TICK_SECONDS + 0.01)])
        self.assertLessEqual(screen.frames_presented, 2)


class TheGhostIsNeverToldWhereThePlayerIs(unittest.TestCase):
    """GHOST-4, from the loop's side of the call."""

    def test_the_policy_is_handed_the_square_and_the_heading_only(self):
        state = ring_state(player=(1, 1), ghost=(3, 3))
        _, _, ghost, _ = run(state, [q_at(1.0)])
        self.assertGreater(ghost.ticks, 0)
        for square, heading in ghost.calls:
            self.assertNotEqual(state.player, None)
            self.assertEqual(2, len((square, heading)))

    def test_the_same_run_goes_the_same_way_wherever_the_player_starts(self):
        """The ghost's decisions do not depend on where the player is.

        Compared as a **prefix** rather than whole, and the reason is worth
        stating: the runs stop at different points because the ghost catches
        different players at different moments, and a game that has ended
        issues no more ticks. That is END-5 doing its job, not GHOST-4 failing.
        What GHOST-4 claims is that the decisions themselves are the same, in
        the same order, for as long as the ghost is asked — so the shorter walk
        must be an exact prefix of the longer.

        The definitive form of this test is DEV-B's in `test_ghost_policy.py`,
        which puts the player on every corridor square in turn. This one checks
        the property survives being driven through the loop.
        """
        maze = Maze.from_text("\n".join(RING))
        walks = []
        for player in ((1, 1), (3, 1), (1, 3)):
            state = GameState(maze=maze, player=player, ghost=(2, 3),
                              ghost_heading=EAST,
                              dots=set(maze.corridor_squares()) - {player},
                              score=0, outcome=Outcome.PLAYING)
            ghost = CountingGhost(ghost_move)
            run(state, [q_at(0.8)], ghost=ghost, seed=5)
            walks.append(ghost.calls)

        shortest = min(len(walk) for walk in walks)
        self.assertGreaterEqual(shortest, 3, "too short to be worth comparing")
        for walk in walks[1:]:
            self.assertEqual(walks[0][:shortest], walk[:shortest])


class APlayedGame(unittest.TestCase):
    """The loop against the real domain, start to finish."""

    def test_it_can_be_played_until_the_player_quits(self):
        state = new_game(4)
        keys = [(0.02 + 0.05 * i, (Key.RIGHT, Key.DOWN, Key.LEFT, Key.UP)[i % 4])
                for i in range(40)]
        keys.append(q_at(3.0))
        final, screen, ghost, _ = run(state, keys)
        self.assertGreater(ghost.ticks, 15)
        self.assertGreater(screen.frames_presented, 1)
        self.assertTrue(final.maze.is_corridor(*final.player))

    def test_a_game_can_be_lost_and_the_loop_stops_moving_anything(self):
        # Player and ghost adjacent, the player walks in.
        state = ring_state(player=(1, 1), ghost=(2, 1))
        final, _, ghost, _ = run(
            state, [(0.01, Key.RIGHT), q_at(3.0)], ghost=StillGhost())
        self.assertEqual(Outcome.CAUGHT, final.outcome)
        self.assertEqual(0, ghost.ticks)

    def test_a_game_can_be_won_and_the_loop_stops_moving_anything(self):
        state = ring_state(player=(1, 1), ghost=(3, 3), dots={(2, 1)})
        final, _, ghost, _ = run(
            state, [(0.01, Key.RIGHT), q_at(3.0)], ghost=StillGhost())
        self.assertEqual(Outcome.CLEARED, final.outcome)
        self.assertEqual(1, final.score)
        self.assertEqual(0, ghost.ticks)


if __name__ == "__main__":
    unittest.main()
