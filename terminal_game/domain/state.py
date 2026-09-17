"""Where a game starts, and what a game in progress consists of.

Two things live here.

**The opening position** — START-1 to START-4.  The player on the corridor
square nearest the grid centre, the ghost on the corridor square at the
greatest straight-line distance from the player, a dot on every corridor
square except the player's, and a score of zero.

**The state itself**, and the vocabulary for how a game ends.  :class:`Outcome`
names the three answers — undecided, caught, cleared — which WI-10 sets and
WI-12 renders.

**What is deliberately not here.**  END-1, END-2 and END-3 say *when* a game is
caught or cleared, and section 4 of the plan traces all three to WI-10.  This
module owns the words and the field they are kept in; it does not decide which
word applies.  SCORE-1, SCORE-2 and SCORE-3 likewise: :meth:`GameState.ate_dot_at`
is the one operation that can change the score, and WI-10 owns when to call it.

**SCORE-5, "the score never goes down", is structural.**  A :class:`GameState`
is immutable with read-only properties, and of the four transitions exactly one
touches the score, by adding one to it.  There is no setter to misuse and no
subtraction anywhere in the module.
"""

from __future__ import annotations

import enum
from typing import FrozenSet, Iterable, Optional, Tuple

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position

#: The middle of the grid.  19 x 29 has a true centre square rather than a
#: crossing point, so START-1's "nearest the middle" has something exact to be
#: near.  **It is not always corridor** — its row is even, so it is a connector
#: on the carving lattice rather than a cell, and is carved only when that wall
#: happens to be opened: about half of real games.  See
#: ``docs/findings/WI-2-odd-cell-lattice.md``.
CENTRE = Position(WIDTH // 2, HEIGHT // 2)


class Outcome(enum.Enum):
    """How a game stands.  The whole vocabulary, and only these three.

    ``UNDECIDED`` while it is still being played; ``CAUGHT`` when the player
    and the ghost have met (END-1); ``CLEARED`` when the last dot has been
    eaten (END-2).  **Which one applies, and in what order they are tested, is
    WI-10's** — END-3 turns entirely on that order and it is not settled here.
    """

    UNDECIDED = "undecided"
    CAUGHT = "caught"
    CLEARED = "cleared"

    def __str__(self) -> str:
        return self.value


def distance_squared(one: Position, other: Position) -> int:
    """Straight-line grid distance between two squares, squared.

    START-2 says the ghost starts furthest from the player *"measured across
    the grid rather than along the corridors"* — as the crow flies, ignoring
    walls entirely.

    Squared, and therefore an exact integer.  Two squares are ordered the same
    way by the square of their distance as by the distance itself, so nothing
    is lost, and comparing integers cannot go wrong the way comparing floats
    eventually does.
    """
    dx = one.x - other.x
    dy = one.y - other.y
    return dx * dx + dy * dy


def _reading_order(position: Position) -> Tuple[int, int]:
    return (position.y, position.x)


def nearest_corridor_to(maze: Maze, target: Position) -> Position:
    """The corridor square closest to ``target`` as the crow flies.

    **Ties are broken in reading order** — topmost, then leftmost — which is
    the tie-break START-1 needs in order to be the same on every run.  It
    fires often rather than rarely: when the centre square is wall, the two
    squares one step above and below it are both at distance one, and this is
    what chooses between them.
    """
    corridors = maze.corridors()
    if not corridors:
        raise ValueError("a maze with no corridor squares has nowhere to start")
    return min(
        corridors, key=lambda p: (distance_squared(p, target), _reading_order(p))
    )


def furthest_corridor_from(maze: Maze, target: Position) -> Position:
    """The corridor square furthest from ``target`` as the crow flies.

    Straight-line, **not** along the corridors: START-2 says so explicitly, and
    the two give different answers in any maze worth the name.

    Ties are broken in reading order, the same way and for the same reason as
    :func:`nearest_corridor_to`.  Assumption P7 says the tie is mine to break
    so long as a test pins it, and reading order is the one order WI-1 already
    guarantees is stable.
    """
    corridors = maze.corridors()
    if not corridors:
        raise ValueError("a maze with no corridor squares has nowhere to start")
    return min(
        corridors, key=lambda p: (-distance_squared(p, target), _reading_order(p))
    )


class GameState:
    """Everything a game in progress consists of.

    Immutable.  Every transition returns a new state, which is what lets WI-10
    work out what a turn would do before committing to it, and what makes
    "the score never goes down" checkable rather than hoped for.
    """

    __slots__ = ("_maze", "_dots", "_player", "_ghost", "_score", "_outcome")

    def __init__(
        self,
        maze: Maze,
        dots: Iterable[Position],
        player: Position,
        ghost: Position,
        score: int = 0,
        outcome: Outcome = Outcome.UNDECIDED,
    ) -> None:
        if score < 0:
            raise ValueError("a score cannot be negative (SCORE-5); got {}".format(score))
        self._maze = maze
        self._dots = frozenset(dots)  # type: FrozenSet[Position]
        self._player = player
        self._ghost = ghost
        self._score = score
        self._outcome = outcome

    # -- reading ----------------------------------------------------------

    @property
    def maze(self) -> Maze:
        return self._maze

    @property
    def dots(self) -> FrozenSet[Position]:
        """The corridor squares that still hold a dot.

        A dot under an actor is still in here: SCORE-4 says the ghost neither
        eats dots nor hides them, and the presentation layer decides what is
        drawn on top of what.
        """
        return self._dots

    @property
    def player(self) -> Position:
        return self._player

    @property
    def ghost(self) -> Position:
        return self._ghost

    @property
    def score(self) -> int:
        return self._score

    @property
    def outcome(self) -> Outcome:
        return self._outcome

    @property
    def is_over(self) -> bool:
        return self._outcome is not Outcome.UNDECIDED

    @property
    def dots_remaining(self) -> int:
        return len(self._dots)

    def has_dot_at(self, position: Position) -> bool:
        return position in self._dots

    # -- changing ---------------------------------------------------------

    def _with(
        self,
        dots: Optional[FrozenSet[Position]] = None,
        player: Optional[Position] = None,
        ghost: Optional[Position] = None,
        score: Optional[int] = None,
        outcome: Optional[Outcome] = None,
    ) -> "GameState":
        return GameState(
            self._maze,
            self._dots if dots is None else dots,
            self._player if player is None else player,
            self._ghost if ghost is None else ghost,
            self._score if score is None else score,
            self._outcome if outcome is None else outcome,
        )

    def with_player_at(self, position: Position) -> "GameState":
        """Put the player on ``position``.  Moves, and does nothing else.

        Whether the move was legal is CTRL-3's question and WI-10's; whether
        it eats a dot is SCORE-1's, and also WI-10's, through
        :meth:`ate_dot_at`.
        """
        return self._with(player=position)

    def with_ghost_at(self, position: Position) -> "GameState":
        """Put the ghost on ``position``.

        No dot is touched.  SCORE-4: *"the ghost neither eats dots nor hides
        them; a dot under the ghost is still there to be taken."*
        """
        return self._with(ghost=position)

    def ate_dot_at(self, position: Position) -> "GameState":
        """Take the dot on ``position``, if there is one, and score it.

        **The only operation in this module that changes the score, and it can
        only add one.** That is the whole of SCORE-5: there is no setter, no
        subtraction and no other caller.

        A square whose dot has already been eaten returns the state unchanged,
        which is SCORE-3 — so WI-10 may call this on every move without first
        having to ask.
        """
        if position not in self._dots:
            return self
        return self._with(dots=self._dots - {position}, score=self._score + 1)

    def decided(self, outcome: Outcome) -> "GameState":
        """Record how the game ended.  WI-10 decides which word applies."""
        return self._with(outcome=outcome)

    # -- comparing and showing -------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameState):
            return NotImplemented
        return (
            self._maze == other._maze
            and self._dots == other._dots
            and self._player == other._player
            and self._ghost == other._ghost
            and self._score == other._score
            and self._outcome is other._outcome
        )

    def __hash__(self) -> int:
        return hash(
            (self._maze, self._dots, self._player, self._ghost, self._score, self._outcome)
        )

    def __repr__(self) -> str:
        return (
            "<GameState player={} ghost={} score={} dots={} {}>".format(
                self._player,
                self._ghost,
                self._score,
                len(self._dots),
                self._outcome,
            )
        )


def new_game(maze: Maze) -> GameState:
    """The state a game begins in — START-1 to START-4.

    * **START-1** the player on the corridor square nearest the grid centre;
    * **START-2** the ghost on the corridor square at the greatest
      straight-line distance from the player, not the greatest walking
      distance;
    * **START-3** a dot on every corridor square except the player's;
    * **START-4** the score at zero, and the game undecided.

    The ghost's square keeps its dot. START-3 excepts the player's square and
    only the player's, and SCORE-4 says a dot under the ghost is still there to
    be taken.
    """
    player = nearest_corridor_to(maze, CENTRE)
    ghost = furthest_corridor_from(maze, player)
    dots = frozenset(maze.corridors()) - {player}
    return GameState(maze=maze, dots=dots, player=player, ghost=ghost)
