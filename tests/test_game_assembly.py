"""WI-13: the assembly's seams, with no window. A stand-in window records what it is asked to do.

These assert the joins only: that a key reaches the session through the input
translation, that a tick reaches the session, and that what is painted after
each is exactly the composer's frame for the session's state. What the session,
the translator and the composer each *do* is owned by their own tests.
"""

import random

import terminal_game.shell.game as game
from terminal_game.application.session import Session
from terminal_game.presentation.frame_composer import compose
from terminal_game.shell.placement import OFFSET, Rect


class StandInWindow:
    """Duck-types the parts of GameWindow that play() uses, and records them."""

    size = (400, 570)

    def __init__(self, script):
        self.script = script          # what to do once run() is called: a list of ("key", name) / ("tick",)
        self.painted = []
        self.placed = None
        self.closed = False

    def place(self, x, y):
        self.placed = (x, y)

    def paint(self, frame):
        self.painted.append(frame)

    def close(self):
        self.closed = True

    def run(self, on_key, on_tick):
        for step in self.script:
            if self.closed:
                break
            on_key(step[1]) if step[0] == "key" else on_tick()
        return 0


def session(seed=7):
    return Session.new(random.Random(seed))


def twin(seed=7):
    """An identical session to replay the same inputs against directly."""
    return Session.new(random.Random(seed))


def test_the_first_picture_is_the_composed_starting_state():
    s, w = session(), StandInWindow([])
    game.play(s, w)
    assert w.painted == [compose(twin().state)]


def test_each_key_is_translated_into_the_session_and_the_new_state_is_painted():
    s, w = session(), StandInWindow([("key", "Up"), ("key", "Left"), ("key", "a")])
    game.play(s, w)
    t = twin()
    expected = [compose(t.state)]
    for intent in ("up", "left", None):
        t.handle(intent)
        expected.append(compose(t.state))
    assert w.painted == expected


def test_each_tick_reaches_the_session_and_the_new_state_is_painted():
    s, w = session(), StandInWindow([("tick",), ("tick",)])
    game.play(s, w)
    t = twin()
    expected = [compose(t.state)]
    for _ in range(2):
        t.tick()
        expected.append(compose(t.state))
    assert w.painted == expected
    assert expected[1] != expected[0]   # the tick really changed the picture (the ghost moved)


def test_quit_closes_the_window_instead_of_painting():
    s, w = session(), StandInWindow([("key", "q"), ("tick",)])
    assert game.play(s, w) == 0
    assert w.closed and len(w.painted) == 1


def test_the_window_is_placed_from_the_anchor_with_its_outer_size():
    anchor, main = Rect(100, 200, 600, 400), Rect(0, 33, 1512, 949)
    w = StandInWindow([])
    game.play(session(), w, anchor, [main])
    assert w.placed == (100 + OFFSET, 200 + OFFSET)


def test_without_displays_the_window_is_left_where_the_toolkit_puts_it():
    w = StandInWindow([])
    game.play(session(), w, None, [])
    assert w.placed is None


def test_main_finds_the_anchor_before_the_window_exists_and_uses_a_fresh_random_source(monkeypatch):
    calls = []
    monkeypatch.setattr(game, "find_anchor", lambda: calls.append("anchor") or None)
    monkeypatch.setattr(game, "visible_displays", lambda: calls.append("displays") or [Rect(0, 33, 1512, 949)])

    def window():
        calls.append("window")
        return StandInWindow([("key", "q")])

    sessions = []
    real_new = Session.new
    monkeypatch.setattr(game.Session, "new", classmethod(lambda cls, rng: sessions.append(rng) or real_new(rng)))
    monkeypatch.setattr(game, "GameWindow", window)
    assert game.main() == 0
    assert calls == ["anchor", "displays", "window"]
    assert isinstance(sessions[0], random.Random)
    game.main()
    assert sessions[0] is not sessions[1]    # a new source each run (C2 shows the mazes differ, on screen)


def test_placement_uses_the_outer_height_drawing_area_plus_title_bar():
    main = Rect(0, 33, 1512, 949)
    w = StandInWindow([])
    game.play(session(), w, Rect(100, 900, 50, 50), [main])   # anchor near the bottom: clamped up
    assert w.placed == (100 + OFFSET, 33 + 949 - (570 + game.TITLE_BAR_POINTS))
    assert game.TITLE_BAR_POINTS == 32
