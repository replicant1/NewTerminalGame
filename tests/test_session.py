"""WI-11 — the session's three states, and what each of them accepts.

**Every "nothing happened" test here is paired with a control that proves the
same action *would* have happened while Playing.** That is the whole
discipline of this file: a test that a tick moves nothing in Decided is
worthless unless the identical tick, on the identical board, visibly moves the
ghost in Playing — otherwise it might be passing because the tick does nothing
anywhere, or because the board had nowhere to go. The controls are not
duplicates of the assertions; they are what makes the assertions mean
anything.

**This file also holds up END-3.** WI-10 made the outcome a derived total
function, so *"eating the last dot on the ghost's square is a loss, not a
win"* is true by the shape of an expression rather than by the order of two
statements. A derived outcome is only stable while the state is, and **Decided
is what keeps the state still.** So
:func:`test_a_decided_game_is_unchanged_not_merely_ignored` is an END-3 test
as much as an END-5 one, and it is why the assertions are about the board
being *equal*, not merely about the session *ignoring* things.

Not here: what a move does (WI-10), what the outcome of a board is (WI-10),
where the ghost goes (WI-9), what a key means (WI-13).
"""

from __future__ import annotations

import random
from typing import Callable, List, Sequence

import pytest

from terminal_game.application import session as session_module
from terminal_game.application import turn as turn_module
from terminal_game.application.session import (
    INITIAL_GHOST_HEADING,
    Phase,
    Session,
)
from terminal_game.application.turn import Intent
from terminal_game.domain import state as state_module
from terminal_game.domain.maze import Direction, Maze, Position
from terminal_game.domain.state import GameState, Outcome, new_game

SEED = 20260917


class Chooser:
    """A random source that picks by rule, so a tick is predictable."""

    def __init__(self, pick: Callable[[Sequence[Direction]], Direction]) -> None:
        self._pick = pick

    def choice(self, seq: Sequence[Direction]) -> Direction:
        return self._pick(seq)


def first_choice() -> Chooser:
    return Chooser(lambda seq: seq[0])


def corridor_row(y: int, xs: range) -> Maze:
    """An all-wall maze with one straight east-west corridor carved in it."""
    return Maze.all_walls().with_corridors_at([Position(x, y) for x in xs])


def playable() -> GameState:
    """A board with room for both actors to move and dots left to eat.

    Player at (4, 10) heading into a clear run east; ghost at (12, 10) with a
    clear run of its own. Dots everywhere but the player's square, as START-3
    would have it.
    """
    maze = corridor_row(10, range(3, 16))
    squares = [Position(x, 10) for x in range(3, 16)]
    return GameState(
        maze=maze,
        dots=frozenset(squares) - {Position(4, 10)},
        player=Position(4, 10),
        ghost=Position(12, 10),
    )


def about_to_be_caught() -> GameState:
    """The player one step west of the ghost, with dots still on the board.

    Moving east is a loss and is not the last dot, so the decision is
    unambiguously CAUGHT and unambiguously not CLEARED.
    """
    maze = corridor_row(10, range(3, 16))
    squares = [Position(x, 10) for x in range(3, 16)]
    return GameState(
        maze=maze,
        dots=frozenset(squares) - {Position(7, 10)},
        player=Position(7, 10),
        ghost=Position(8, 10),
    )


def decided_session(on_end: Callable[[], None] = None) -> Session:
    """A session that has already been played to a loss."""
    session = Session(about_to_be_caught(), first_choice(), on_end=on_end)
    session.handle(Intent.MOVE_EAST)
    assert session.phase is Phase.DECIDED, "fixture did not reach a decision"
    assert session.outcome is Outcome.CAUGHT
    return session


# --------------------------------------------------------------------------
# START-5 — under way the moment it exists
# --------------------------------------------------------------------------


def test_a_session_is_playing_the_moment_it_is_made() -> None:
    """START-5: *"the game is under way the moment the window opens"*.

    There is no state to pass through before play, so the very first thing
    that can be observed about a session is that it is already Playing.
    """
    session = Session(playable(), first_choice())
    assert session.phase is Phase.PLAYING
    assert session.accepts_play
    assert session.is_running


def test_a_tick_works_before_anything_is_pressed() -> None:
    """START-5's other half: *"the ghost is already moving"*.

    No call precedes the first tick, and the ghost moves on it.
    """
    session = Session(playable(), first_choice())
    before = session.game.ghost
    session.tick()
    assert session.game.ghost != before


def test_there_is_no_way_to_start_or_restart_a_session() -> None:
    """START-5 and GAME-3, as an architecture guard on the public names.

    A ready state or a restart edge would have to be spelled somewhere, and
    the cheapest way to keep them out is to notice a method appearing.
    """
    public = {name for name in dir(Session) if not name.startswith("_")}
    forbidden = {
        name
        for name in public
        for word in ("start", "begin", "restart", "reset", "pause", "resume",
                     "life", "lives", "level", "timer")
        if word in name.lower()
    }
    assert not forbidden, "GAME-3 says none of these exist: {}".format(
        sorted(forbidden)
    )


# --------------------------------------------------------------------------
# GAME-3 — met by absence
# --------------------------------------------------------------------------


def test_there_are_exactly_three_phases() -> None:
    """*"Three states and no more."*"""
    assert [phase.name for phase in Phase] == ["PLAYING", "DECIDED", "ENDED"]
    assert len(Phase) == 3


def test_nothing_ever_returns_a_session_to_playing() -> None:
    """GAME-3, as behaviour rather than as a naming convention.

    Every input is applied to a session in every phase, and Playing is never
    re-entered. This is what "no restart edge" means when it is a fact about
    transitions rather than about method names.
    """
    inputs = list(Intent) + ["tick", "quit"]

    for reach_phase in (Phase.PLAYING, Phase.DECIDED, Phase.ENDED):
        for action in inputs:
            session = Session(playable(), first_choice())
            if reach_phase is Phase.DECIDED:
                session = decided_session()
            elif reach_phase is Phase.ENDED:
                session.quit()
            started_in = session.phase
            assert started_in is reach_phase

            if action == "tick":
                session.tick()
            elif action == "quit":
                session.quit()
            else:
                session.handle(action)

            if started_in is not Phase.PLAYING:
                assert session.phase is not Phase.PLAYING, (
                    "{} in {} went back to Playing".format(action, started_in)
                )


# --------------------------------------------------------------------------
# END-5 — Decided stops everything, and the controls that prove it
# --------------------------------------------------------------------------


def test_a_tick_moves_the_ghost_while_playing() -> None:
    """The control for the test below. Without it, "nothing moved" proves nothing.

    Same board, same random source, same call — in Playing the ghost visibly
    moves, so a later assertion that it does not move in Decided is about the
    phase and not about the tick being inert or the ghost being boxed in.
    """
    session = Session(playable(), first_choice())
    before = session.game.ghost
    session.tick()
    assert session.game.ghost != before


def test_in_decided_a_tick_moves_nothing() -> None:
    """END-5: *"the last picture stays on the screen"*, so a tick must not stir it."""
    session = decided_session()
    frozen = session.game
    heading = session.ghost_heading

    for _ in range(20):
        session.tick()

    assert session.game == frozen
    assert session.game.ghost == frozen.ghost
    assert session.ghost_heading is heading
    assert session.phase is Phase.DECIDED


def test_an_arrow_moves_the_player_while_playing() -> None:
    """The control for the test below, on the same board the decision came from."""
    session = Session(about_to_be_caught(), first_choice())
    before = session.game.player
    session.handle(Intent.MOVE_WEST)
    assert session.game.player != before
    assert session.phase is Phase.PLAYING


def test_in_decided_an_arrow_changes_nothing() -> None:
    """END-5, for every direction rather than one.

    The control above shows that west is a legal move on this board while
    Playing, so this is the phase refusing it rather than a wall doing so.
    """
    session = decided_session()
    frozen = session.game

    for intent in (
        Intent.MOVE_NORTH,
        Intent.MOVE_SOUTH,
        Intent.MOVE_EAST,
        Intent.MOVE_WEST,
    ):
        session.handle(intent)
        assert session.game == frozen, "{} disturbed a decided game".format(intent)

    assert session.phase is Phase.DECIDED


def test_a_decided_game_is_unchanged_not_merely_ignored() -> None:
    """**This is an END-3 test as much as an END-5 one.**

    WI-10 made the outcome a derived total function of the state, which is
    what stops *"the last dot on the ghost's square"* being a question of
    statement order. A derived outcome is only as stable as the state it is
    derived from — so if anything here could alter the board after a decision,
    the outcome could change under it and END-3 would break again in a new
    way, in this file rather than in the resolver.

    So the assertion is deliberately about equality of the whole board and of
    the outcome, after a mixture of every input, and not about the session
    merely declining to act.
    """
    session = decided_session()
    frozen = session.game
    assert frozen.outcome is Outcome.CAUGHT

    for _ in range(10):
        session.tick()
        for intent in (Intent.MOVE_NORTH, Intent.MOVE_EAST, Intent.MOVE_WEST):
            session.handle(intent)

    assert session.game == frozen
    assert session.game.score == frozen.score
    assert session.game.dots == frozen.dots
    assert session.outcome is Outcome.CAUGHT


# --------------------------------------------------------------------------
# END-6 and CTRL-4 — quit, from anywhere
# --------------------------------------------------------------------------


def test_quit_is_accepted_while_playing() -> None:
    """CTRL-4: *"pressing q quits at once, at any point in the game"*."""
    session = Session(playable(), first_choice())
    session.handle(Intent.QUIT)
    assert session.phase is Phase.ENDED
    assert not session.is_running


def test_quit_is_accepted_while_decided() -> None:
    """END-6: *"q is the only way to leave a finished game"* — so it must work."""
    session = decided_session()
    session.handle(Intent.QUIT)
    assert session.phase is Phase.ENDED
    assert not session.is_running


def test_in_decided_quit_is_the_only_thing_accepted() -> None:
    """END-6 stated as the exclusion it is, on one session rather than two.

    Every other intent leaves the phase alone; quit is what changes it.
    """
    session = decided_session()
    for intent in (
        Intent.MOVE_NORTH,
        Intent.MOVE_SOUTH,
        Intent.MOVE_EAST,
        Intent.MOVE_WEST,
    ):
        session.handle(intent)
        assert session.phase is Phase.DECIDED

    session.handle(Intent.QUIT)
    assert session.phase is Phase.ENDED


# --------------------------------------------------------------------------
# WIN-5 under assumption P1 — Ended is what ends it
# --------------------------------------------------------------------------


def test_a_decided_session_is_still_running() -> None:
    """The distinction WIN-5 and END-5 turn on, and contradiction C-1 settles.

    Deciding an outcome does **not** end the session. The last picture stays
    up (END-5) until the player presses ``q`` (END-6). If this were false the
    window would vanish at the moment of the decision, which is the reading
    the plan proceeds *against*.
    """
    session = decided_session()
    assert session.phase is Phase.DECIDED
    assert session.is_running
    assert not session.accepts_play


def test_reaching_ended_calls_back_exactly_once() -> None:
    """WIN-5's seam to the Shell.

    Application names no process and no toolkit, so ending is a callback the
    Shell supplies. It must fire when Ended is reached and not before.
    """
    calls = []  # type: List[int]
    session = Session(playable(), first_choice(), on_end=lambda: calls.append(1))

    session.tick()
    session.handle(Intent.MOVE_EAST)
    assert calls == [], "on_end fired while the game was still being played"

    session.handle(Intent.QUIT)
    assert calls == [1]


def test_quitting_twice_ends_once() -> None:
    """The Shell may hear about a quit twice — a key, and a closing window.

    Neither should have to know whether the other got there first, so quit is
    idempotent and the callback fires once.
    """
    calls = []  # type: List[int]
    session = Session(playable(), first_choice(), on_end=lambda: calls.append(1))
    session.quit()
    session.quit()
    session.handle(Intent.QUIT)
    assert calls == [1]
    assert session.phase is Phase.ENDED


def test_an_ended_session_accepts_nothing_at_all() -> None:
    """There is nowhere to go from Ended, and nothing to change."""
    session = Session(playable(), first_choice())
    session.quit()
    frozen = session.game

    session.tick()
    session.handle(Intent.MOVE_EAST)

    assert session.game == frozen
    assert session.phase is Phase.ENDED


# --------------------------------------------------------------------------
# Reaching Decided, and the ghost's heading
# --------------------------------------------------------------------------


def test_a_decision_moves_the_session_to_decided() -> None:
    """The one transition out of Playing that is not a quit.

    The session reads the outcome off the state rather than being told, so its
    idea of *over* cannot disagree with the resolver's.
    """
    session = Session(about_to_be_caught(), first_choice())
    assert session.phase is Phase.PLAYING
    session.handle(Intent.MOVE_EAST)
    assert session.phase is Phase.DECIDED
    assert session.outcome is Outcome.CAUGHT
    assert session.game.is_over


def test_a_ghost_walking_into_the_player_decides_it_too() -> None:
    """END-1's other arm, reached through a tick rather than through a key."""
    maze = corridor_row(10, range(3, 16))
    squares = [Position(x, 10) for x in range(3, 16)]
    state = GameState(
        maze=maze,
        dots=frozenset(squares) - {Position(9, 10)},
        player=Position(9, 10),
        ghost=Position(8, 10),
    )
    session = Session(state, first_choice(), heading=Direction.EAST)

    session.tick()

    assert session.phase is Phase.DECIDED
    assert session.outcome is Outcome.CAUGHT


def test_a_board_that_is_over_by_the_rules_starts_in_decided() -> None:
    """The session asks WI-10 what *over* means; it does not read a field.

    ``GameState.outcome`` is a field the resolver stamps, so a board built by
    hand can have the player and the ghost on one square and still carry
    ``UNDECIDED``. Trusting the field would make such a board **playable** —
    and since Decided is what holds END-3 up, that is exactly the crack to
    keep shut. This board is unstamped on purpose.
    """
    unstamped = about_to_be_caught().with_player_at(Position(8, 10))
    assert unstamped.outcome is Outcome.UNDECIDED, "fixture is not unstamped"
    assert unstamped.player == unstamped.ghost

    session = Session(unstamped, first_choice())

    assert session.phase is Phase.DECIDED
    assert not session.accepts_play
    assert session.outcome is Outcome.CAUGHT


def test_a_board_the_resolver_already_stamped_starts_in_decided_too() -> None:
    """The ordinary case — a board the resolver really did finish.

    Both actors on one square *and* stamped, which is the only combination
    the resolver can produce, so this is what a resumed or fixtured game
    actually looks like.
    """
    finished = about_to_be_caught().with_player_at(Position(8, 10)).decided(
        Outcome.CAUGHT
    )
    session = Session(finished, first_choice())
    assert session.phase is Phase.DECIDED
    assert not session.accepts_play
    assert session.outcome is Outcome.CAUGHT


def test_a_stamp_that_disagrees_with_the_board_does_not_decide_a_session() -> None:
    """The rules are the one source of truth, and the stamp is a cache of them.

    WI-10 made the outcome a derived total function precisely so there is
    **one** answer to "is this over". ``GameState.outcome`` is a field the
    resolver fills in from that function, so in production the two cannot
    disagree. Where they do — only ever on a hand-built board — the function
    wins, because saying otherwise would put back the second source of truth
    that structural END-3 removed.

    This board carries a ``CAUGHT`` stamp with the actors a square apart and
    dots still on the table. It is malformed, and the session treats it as
    what it demonstrably is rather than as what it claims.
    """
    mislabelled = about_to_be_caught().decided(Outcome.CAUGHT)
    assert mislabelled.player != mislabelled.ghost
    assert mislabelled.dots_remaining > 0

    session = Session(mislabelled, first_choice())

    assert session.phase is Phase.PLAYING
    assert session.outcome is Outcome.UNDECIDED


def test_a_playable_board_is_not_mistaken_for_a_finished_one() -> None:
    """The control for both tests above.

    Without it, "starts in Decided" could be true of every session, and
    neither test would be saying anything about the board it was handed.
    """
    session = Session(playable(), first_choice())
    assert session.phase is Phase.PLAYING
    assert session.accepts_play
    assert session.outcome is Outcome.UNDECIDED


def test_the_ghost_heading_is_carried_from_one_tick_to_the_next() -> None:
    """Nobody else holds it, so the session does — and GHOST-2 depends on it.

    Down a straight corridor the heading must survive each tick, or the ghost
    would forget which way it was going and GHOST-2 could not hold.
    """
    session = Session(playable(), first_choice(), heading=Direction.EAST)
    walk = []  # type: List[Position]
    for _ in range(3):
        session.tick()
        walk.append(session.game.ghost)
        assert session.ghost_heading is Direction.EAST

    assert walk == [Position(13, 10), Position(14, 10), Position(15, 10)]


def test_the_initial_heading_is_fixed_so_a_seeded_run_repeats() -> None:
    """An arbitrary choice, but not an unstable one.

    Nothing in the specification says which way the ghost first goes, and no
    other item claimed it. What matters is that it is the same every time, or
    WI-16's seeded playthroughs would not reproduce.
    """
    assert INITIAL_GHOST_HEADING is Direction.EAST
    assert Session(playable(), first_choice()).ghost_heading is INITIAL_GHOST_HEADING

    def walk() -> List[Position]:
        session = Session(playable(), random.Random(SEED))
        path = []  # type: List[Position]
        for _ in range(3):
            session.tick()
            path.append(session.game.ghost)
        return path

    assert walk() == walk()


# --------------------------------------------------------------------------
# One vocabulary, not two
# --------------------------------------------------------------------------


def test_the_session_and_the_resolver_share_one_vocabulary() -> None:
    """An identity guard, after WI-4b.

    Two modules that must agree on a type are exactly where things silently
    drift apart, and behaviour tests on both halves pass throughout. So the
    assertion is that these are the *same class objects*, not that they behave
    alike: ``Outcome`` and ``Intent`` each exist once.
    """
    assert session_module.Outcome is state_module.Outcome
    assert session_module.Intent is turn_module.Intent
    assert Session(playable(), first_choice()).outcome is Outcome.UNDECIDED


def test_the_repr_reports_the_outcome_the_session_actually_has() -> None:
    """``repr`` asks the same question every other reader here asks.

    It used to read the stored field, so a hand-built board could print
    ``Session(decided, undecided, ...)`` — the phase right and the outcome
    wrong. **``repr`` is what pytest prints in a traceback**, so a misleading
    one costs whoever is debugging a failed journey an hour chasing the wrong
    thing. Found by lane C reading ahead into WI-16.

    The board here is the awkward one on purpose: over by the rules, and
    never stamped.
    """
    unstamped = about_to_be_caught().with_player_at(Position(8, 10))
    assert unstamped.outcome is Outcome.UNDECIDED, "fixture is not unstamped"

    session = Session(unstamped, first_choice())
    text = repr(session)

    assert "decided" in text
    assert "caught" in text
    assert "undecided" not in text, text


def test_the_repr_still_says_undecided_while_a_game_is_being_played() -> None:
    """The control: ``repr`` must be capable of printing ``undecided``.

    Without this, the test above would also pass on a ``repr`` that had been
    hard-wired to say ``caught``.
    """
    text = repr(Session(playable(), first_choice()))
    assert "playing" in text
    assert "undecided" in text
