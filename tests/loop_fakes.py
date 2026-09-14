"""Stand-ins for the clock and the screen, for testing the game loop.

The whole difficulty of testing WI-11 is that the loop's correctness is about
*when* things happen, and the only place a single-threaded loop can wait is
inside `read_key`. So the fake screen is where the clock moves:

    read_key(timeout) advances the clock to whichever comes first —
    the moment the next scripted key was pressed, or the timeout's deadline.

That is exactly what a real terminal does, and it is what makes "a key arriving
early does not postpone the tick" a thing a test can state. A fake that let the
test drive the clock itself would be asking the test to decide the answer.
"""

from __future__ import annotations

from terminalgame.screen.port import Frame, Key, Screen


class RanOutOfScript(AssertionError):
    """The loop read more keys than the test had anything to say about.

    Raised rather than returning `None` for ever, because a loop that never
    quits would otherwise hang the suite instead of failing it.
    """


class FakeClock(object):
    """A clock that only moves when something waits."""

    def __init__(self, start=0.0):
        self.now = start

    def time(self):
        return self.now

    def advance_to(self, when):
        if when > self.now:
            self.now = when


class ScriptedScreen(Screen):
    """A screen with keys pressed at scheduled times, and a record of frames.

    `keys` is a sequence of `(when, key)` in ascending order of `when`, each
    `when` an absolute time on the same clock the loop is given.
    """

    def __init__(self, clock, keys=(), width=40, height=30, read_limit=100000):
        self.clock = clock
        self.pending = list(keys)
        self._width = width
        self._height = height
        self.presented = []
        self.reads = []
        self.read_limit = read_limit

    # -- the port ---------------------------------------------------------

    def size(self):
        return (self._width, self._height)

    def new_frame(self):
        return Frame(self._width, self._height)

    def present(self, frame):
        self.presented.append(frame)

    def read_key(self, timeout_seconds):
        if len(self.reads) >= self.read_limit:
            raise RanOutOfScript(
                "the loop has read %d keys without quitting" % (len(self.reads),))
        timeout_seconds = max(0.0, timeout_seconds)
        deadline = self.clock.now + timeout_seconds
        self.reads.append(timeout_seconds)

        if self.pending and self.pending[0][0] <= deadline:
            when, key = self.pending.pop(0)
            self.clock.advance_to(when)
            return key

        self.clock.advance_to(deadline)
        return None

    # -- what a test wants to know afterwards ------------------------------

    @property
    def frames_presented(self):
        return len(self.presented)


class CountingGhost(object):
    """The ghost's policy, wrapped so a test can count the ticks it was asked
    for — and check it was never handed the player.

    The real policy's signature is `(maze, square, heading, random_source)`,
    which does not include the player at all; this records each call so a test
    can assert on how many there were and what they were about.
    """

    def __init__(self, policy):
        self.policy = policy
        self.calls = []

    def __call__(self, maze, square, heading, random_source):
        self.calls.append((square, heading))
        return self.policy(maze, square, heading, random_source)

    @property
    def ticks(self):
        return len(self.calls)


class StillGhost(object):
    """A ghost that never goes anywhere.

    For tests about the loop's timing rather than the ghost's movement: it
    keeps the state unchanged from tick to tick, so the only thing that can
    make a frame be redrawn is the player.
    """

    def __init__(self):
        self.ticks = 0

    def __call__(self, maze, square, heading, random_source):
        self.ticks += 1
        return tuple(square), heading


def arrows(*names):
    """`arrows("up", "left")` — the key objects, by name."""
    by_name = {"up": Key.UP, "down": Key.DOWN, "left": Key.LEFT,
               "right": Key.RIGHT}
    return [by_name[name] for name in names]


def at(times, keys):
    """Pair up scheduled times with keys, for `ScriptedScreen`."""
    return list(zip(times, keys))
