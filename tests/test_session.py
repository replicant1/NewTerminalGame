"""WI-12: session control (plan §4, WI-12/C1-C10).

Scenarios use hand-built corridors, whose outcome can be read off the picture,
and generated mazes for the claims about many games.
"""

from __future__ import annotations

import random

import pytest

from terminal_game.application import session as sess
from terminal_game.application.session import DECIDED, ENDED, PLAYING, QUIT, Session
from terminal_game.domain.game_setup import new_game
from terminal_game.domain.game_state import LOST, WON, GameState
from terminal_game.domain.game_state import PLAYING as UNDECIDED
from terminal_game.domain.maze import Maze
from terminal_game.domain.maze_generator import generate_maze
from terminal_game.presentation import input_translation as wi6
from terminal_game.presentation.input_translation import translate

ARROWS = ("up", "down", "left", "right")
CORRIDOR = Maze.from_rows(["#########", "#.......#", "#########"])


class NoDraws:
    def choice(self, seq):
        raise AssertionError(f"unexpected random draw from {seq!r}")


def caught_at_tick_3():
    """Setup on the corridor: player (4, 1), ghost (1, 1). The ghost walks east
    (2, 1), (3, 1), then (4, 1): caught on the third tick, with no draws."""
    s = Session(new_game(CORRIDOR), NoDraws())
    assert (s.state.player, s.state.ghost) == ((4, 1), (1, 1))
    return s


def about_to_win():
    """Player (2, 1) beside the last dot at (3, 1); the ghost far off at (7, 1)."""
    state = GameState(CORRIDOR, (2, 1), (7, 1), frozenset({(3, 1)}), 5, UNDECIDED, (-1, 0))
    return Session(state, NoDraws())


def decided_sessions():
    lost = caught_at_tick_3()
    for _ in range(3):
        lost.tick()
    won = about_to_win()
    won.handle("right")
    assert (lost.state.outcome, won.state.outcome) == (LOST, WON)
    return {"lost": lost, "won": won}


def snapshot(s):
    return (s.phase, s.state)


# --- C1 ---------------------------------------------------------------------

def test_c1_a_new_session_is_already_playing_and_the_first_tick_moves_the_ghost():
    for seed in range(200):
        s = Session.new(random.Random(seed))
        assert s.phase == PLAYING, seed
        start = s.state.ghost
        s.tick()
        assert s.state.ghost != start, seed


# --- C2 ---------------------------------------------------------------------

def test_c2_while_playing_each_tick_moves_the_ghost_exactly_one_square():
    for seed in range(200):
        s = Session.new(random.Random(seed))
        for _ in range(300):
            if s.phase != PLAYING:
                break
            before = s.state.ghost
            s.tick()
            after = s.state.ghost
            assert abs(after[0] - before[0]) + abs(after[1] - before[1]) == 1, seed


def test_c2_key_presses_between_ticks_neither_add_ghost_moves_nor_remove_them():
    compared = 0
    for seed in range(200):
        quiet = Session.new(random.Random(seed))
        busy = Session.new(random.Random(seed))
        keys = random.Random(5_000 + seed)
        quiet_path, busy_path = [], []
        for _ in range(200):
            for _ in range(keys.randrange(4)):  # 0 to 3 key presses between ticks
                busy.handle(keys.choice(ARROWS + (None,)))
            if busy.phase != PLAYING or quiet.phase != PLAYING:
                break  # either game decided (the quiet player can be caught too): ticks rightly stop
            ghost_before = busy.state.ghost
            quiet.tick()
            busy.tick()
            quiet_path.append(quiet.state.ghost)
            busy_path.append(busy.state.ghost)
            assert busy.state.ghost != ghost_before, seed  # a tick is never lost
        assert busy_path == quiet_path, seed  # nor are any added: one move per tick, the same moves
        compared += len(busy_path)
    assert compared > 10_000, f"only {compared} ticks compared, so the check said little"


# --- C3 ---------------------------------------------------------------------

def test_c3_each_arrow_press_moves_the_player_at_most_one_square():
    for seed in range(200):
        s = Session.new(random.Random(seed))
        keys = random.Random(7_000 + seed)
        for _ in range(300):
            before = s.state.player
            s.handle(keys.choice(ARROWS))
            after = s.state.player
            assert abs(after[0] - before[0]) + abs(after[1] - before[1]) <= 1, seed


def test_c3_with_no_key_presses_the_player_never_moves_however_many_ticks_pass():
    for seed in range(200):
        s = Session.new(random.Random(seed))
        start = s.state.player
        for _ in range(500):
            s.tick()
            assert s.state.player == start, seed


# --- C4, C6, C7 ---------------------------------------------------------------

@pytest.mark.parametrize("ending", ["lost", "won"])
def test_c4_once_decided_ticks_and_arrows_change_nothing_the_shell_would_paint(ending):
    s = decided_sessions()[ending]
    assert s.phase == DECIDED
    frozen = s.state
    for _ in range(50):
        s.tick()
        for arrow in ARROWS:
            s.handle(arrow)
    assert s.state == frozen
    assert s.phase == DECIDED


@pytest.mark.parametrize("ending", ["lost", "won"])
def test_c6_after_the_game_is_decided_quit_is_the_only_input_with_any_effect(ending):
    s = decided_sessions()[ending]
    before = snapshot(s)
    for name in ["Up", "Down", "Left", "Right", "a", "space", "Return", "Escape", "F1", "Shift_L", "1"]:
        s.handle(translate(name))
        s.tick()
        assert snapshot(s) == before, name
    s.handle(translate("q"))
    assert s.phase == ENDED


def test_c7_an_arrow_right_after_the_catching_tick_does_not_move_the_player():
    s = caught_at_tick_3()
    s.tick()
    s.tick()
    s.tick()  # the catching tick
    assert (s.state.outcome, s.state.player, s.state.ghost) == (LOST, (4, 1), (4, 1))
    for arrow in ARROWS:
        s.handle(arrow)
        assert s.state.player == (4, 1)
    assert s.phase == DECIDED


# --- C5 ---------------------------------------------------------------------

@pytest.mark.parametrize("key", ["q", "Q"])
def test_c5_q_ends_the_session_at_once_while_playing(key):
    s = Session.new(random.Random(1))
    s.handle(translate(key))
    assert s.phase == ENDED and s.ended


@pytest.mark.parametrize("key", ["q", "Q"])
@pytest.mark.parametrize("ending", ["lost", "won"])
def test_c5_q_ends_the_session_at_once_after_the_game_is_decided(key, ending):
    s = decided_sessions()[ending]
    s.handle(translate(key))
    assert s.phase == ENDED and s.ended


# --- C8 ---------------------------------------------------------------------

@pytest.mark.parametrize("ending", ["lost", "won"])
def test_c8_no_sequence_of_inputs_leads_back_from_an_ending(ending):
    events = random.Random(11)
    for trial in range(200):
        s = decided_sessions()[ending]
        frozen = s.state
        for _ in range(100):
            choice = events.randrange(7)
            if choice == 6:
                s.tick()
            else:
                s.handle((ARROWS + (None, QUIT))[choice])
            assert s.phase in (DECIDED, ENDED), trial
            assert s.state == frozen, trial  # no new game, no restored player, no resumed play
            assert s.state.outcome == (LOST if ending == "lost" else WON)


# --- C9 ---------------------------------------------------------------------

def run_script(seed, script_seed):
    maze = generate_maze(random.Random(seed))
    s = Session(new_game(maze), random.Random(50_000 + seed))
    script = random.Random(script_seed)
    for _ in range(600):
        if script.random() < 0.5:
            s.tick()
        else:
            s.handle(script.choice(ARROWS + (None,)))
    return s


def test_c9_the_same_maze_random_source_and_inputs_end_in_identical_states():
    differing_scripts = 0
    for seed in range(300):
        a = run_script(seed, 90_000 + seed)
        b = run_script(seed, 90_000 + seed)
        assert (a.phase, a.state) == (b.phase, b.state), seed
        c = run_script(seed, 1 + 90_000 + seed)
        differing_scripts += (c.phase, c.state) != (a.phase, a.state)
    assert differing_scripts > 250, "different inputs should mostly end differently, or the check says little"


# --- C10 --------------------------------------------------------------------

def test_c10_ticks_and_keys_after_the_session_has_ended_are_ignored_without_error():
    for start in ("playing", "lost", "won"):
        s = Session.new(random.Random(2)) if start == "playing" else decided_sessions()[start]
        s.handle(QUIT)
        ended_state = s.state
        for _ in range(20):
            s.tick()
            for intent in ARROWS + (None, QUIT):
                s.handle(intent)
        assert (s.phase, s.state) == (ENDED, ended_state), start


# --- A claims ------------------------------------------------------------------

def test_a1_the_sessions_intents_are_wi6s_own():
    """The seam with WI-6: every intent translate() can produce is one handle() accepts, with the same meaning."""
    assert (sess.UP, sess.DOWN, sess.LEFT, sess.RIGHT, sess.QUIT) == (
        wi6.MOVE_UP, wi6.MOVE_DOWN, wi6.MOVE_LEFT, wi6.MOVE_RIGHT, wi6.QUIT)
    s = Session(GameState(CORRIDOR, (4, 1), (1, 1), frozenset(), 0, UNDECIDED, None), NoDraws())
    s.handle(translate("Right"))
    assert s.state.player == (5, 1)
    s.handle(translate("Left"))
    assert s.state.player == (4, 1)
    s.handle(translate("a"))
    assert s.state.player == (4, 1) and s.phase == PLAYING


@pytest.mark.parametrize("bad", ["jump", "Up", "q", "", 3, [], {}, ("up",)])
def test_a2_an_intent_that_wi6_could_not_have_produced_is_refused(bad):
    s = Session.new(random.Random(0))
    with pytest.raises(ValueError, match="an intent is one of"):
        s.handle(bad)


def test_a3_session_new_lays_out_the_maze_with_the_source_it_is_handed_and_sets_up():
    for seed in range(50):
        assert Session.new(random.Random(seed)).state == new_game(generate_maze(random.Random(seed)))
    assert Session.new(random.Random(1)).state.maze != Session.new(random.Random(2)).state.maze
