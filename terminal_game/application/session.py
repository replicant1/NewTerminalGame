"""Session control: the game's state machine, and what the shell drives.

(START-5, GHOST-1, CTRL-2, CTRL-4, END-5, END-6, GAME-3.)

A :class:`Session` is in one of three phases:

* :data:`PLAYING`: from the moment it is made (START-5). Each tick moves the
  ghost one square, and each arrow intent tries to move the player one square.
* :data:`DECIDED`: the game is won or lost. The final picture stays: ticks and
  arrows change nothing. Only quit has any effect (END-5, END-6; plan §1.8 Q2,
  reading A3).
* :data:`ENDED`: quit was given, while playing or after the ending. The shell
  closes the window. Anything arriving after that is ignored without error.

Nothing leads back from DECIDED or ENDED (GAME-3).

The shell drives it like this (plan §1.4: the shell composes and paints; the
application never calls upward)::

    session = Session.new(random.Random())
    def after_event():
        if session.ended:
            window.close()
        else:
            window.paint(compose(session.state))
    def on_key(name):
        session.handle(translate(name))   # WI-6's intent, or None
        after_event()
    def on_tick():
        session.tick()
        after_event()

Application layer: no clock, no toolkit, no presentation imports. Ticks and
intents arrive as calls; the random source is handed in, and the same maze,
random source and sequence of calls always end in the same state.
"""

from __future__ import annotations

from typing import Optional

from terminal_game.application.turn_resolution import move_player, step_ghost
from terminal_game.domain.game_setup import new_game
from terminal_game.domain.game_state import PLAYING as UNDECIDED
from terminal_game.domain.game_state import GameState
from terminal_game.domain.maze_generator import RandomSource, generate_maze

# The intents, as WI-6 (presentation.input_translation) names them. Plain
# strings, equal to WI-6's, so the application needs no presentation import.
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"
QUIT = "quit"

_INTENTS = (UP, DOWN, LEFT, RIGHT, QUIT)
_MOVES = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}

# The phases.
PLAYING = "playing"
DECIDED = "decided"
ENDED = "ended"


class Session:
    """One game, from the first tick to quit."""

    def __init__(self, state: GameState, rng: RandomSource) -> None:
        self._state = state
        self._rng = rng
        self._ended = False

    @classmethod
    def new(cls, rng: RandomSource) -> Session:
        """A fresh game: a maze laid out with ``rng``, set up, and ``rng`` kept for the ghost."""
        return cls(new_game(generate_maze(rng)), rng)

    @property
    def state(self) -> GameState:
        """The game as it stands: what the shell composes and paints."""
        return self._state

    @property
    def phase(self) -> str:
        if self._ended:
            return ENDED
        return PLAYING if self._state.outcome is UNDECIDED else DECIDED

    @property
    def ended(self) -> bool:
        """True once quit was given: the shell should close the window."""
        return self._ended

    def tick(self) -> None:
        """One tick of the ghost's timer: the ghost moves one square while playing."""
        if self.phase == PLAYING:
            self._state = step_ghost(self._state, self._rng)

    def handle(self, intent: Optional[str]) -> None:
        """One key press, as WI-6's intent: a move, quit, or ``None`` for any other key."""
        # Compared against a tuple, not looked up in a dict, so an unhashable value is refused too.
        if intent is not None and intent not in _INTENTS:
            raise ValueError(f"an intent is one of {list(_INTENTS)} or None, not {intent!r}")
        if self._ended:
            return
        if intent == QUIT:
            self._ended = True
        elif intent is not None and self.phase == PLAYING:
            self._state = move_player(self._state, _MOVES[intent])
