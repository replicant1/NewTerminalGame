"""WI-12 evidence harness: scripted sessions, printed event by event.

Evidence, not a test: the suite never collects it. tests/test_session.py
asserts the same things; this prints what happened at each event, so a reader
can follow the phases.

It drives the session exactly as the brief tells the shell to (WI-13): key
names go through WI-6's translate(), and after every event the harness either
"closes" (the session ended) or composes a frame with WI-10's compose() and
records its status row, where the real shell would paint. No window is opened.

Run from the repository root:

    .venv/bin/python evidence/WI-12/session_transcript.py

Each check ends PASS or FAIL; the last line is ALL PASS or SOME FAIL, and the
exit status is 0 only for ALL PASS.
"""

from __future__ import annotations

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from terminal_game.application.session import Session  # noqa: E402
from terminal_game.domain.game_setup import new_game  # noqa: E402
from terminal_game.domain.game_state import PLAYING as UNDECIDED, GameState  # noqa: E402
from terminal_game.domain.maze import Maze  # noqa: E402
from terminal_game.domain.maze_generator import generate_maze  # noqa: E402
from terminal_game.presentation.frame_composer import compose  # noqa: E402
from terminal_game.presentation.input_translation import translate  # noqa: E402

CORRIDOR = Maze.from_rows(["#########", "#.......#", "#########"])


class NoDraws:
    def choice(self, seq):
        raise AssertionError("unexpected draw")


class FakeWindow:
    """Stands where WI-3's GameWindow would: records paints and a close."""

    def __init__(self):
        self.painted = []
        self.closed = False

    def paint(self, frame):
        self.painted.append("".join(ch for ch, _ in frame[-1]).rstrip())

    def close(self):
        self.closed = True


def drive(session, events):
    """Run events ('tick' or a key name) through the shell's wiring; return a transcript."""
    window = FakeWindow()
    lines = []

    def after_event(label):
        if session.ended:
            window.close()
            lines.append(f"    {label:<12} phase {session.phase:<8} -> window closed")
        else:
            window.paint(compose(session.state))
            s = session.state
            lines.append(f"    {label:<12} phase {session.phase:<8} player {s.player} ghost {s.ghost} status '{window.painted[-1]}'")

    for ev in events:
        if window.closed:
            # after close the shell delivers nothing more, but prove the session ignores it anyway (C10)
            session.tick() if ev == "tick" else session.handle(translate(ev))
            lines.append(f"    {ev:<12} phase {session.phase:<8} (after close: ignored)")
            continue
        if ev == "tick":
            session.tick()
        else:
            session.handle(translate(ev))
        after_event(ev)
    return lines, window


def main() -> int:
    results = []
    out = []

    # 1. Caught: player (4, 1), ghost (1, 1) walking east; arrows after the catch, then q.
    s = Session(new_game(CORRIDOR), NoDraws())
    lines, win = drive(s, ["tick", "tick", "tick", "Right", "Left", "tick", "a", "Q", "tick", "Up"])
    out += ["  caught on the corridor #.......#:"] + lines
    after_catch = [l for l in lines[3:7]]
    results.append(("C1/C2", "each tick moved the ghost one square with no key pressed", lines[0].count("ghost (2, 1)") == 1 and "ghost (3, 1)" in lines[1]))
    results.append(("C4/C6/C7", "after the catching tick, arrows, a tick and 'a' changed nothing", all("player (4, 1) ghost (4, 1)" in l and "CAUGHT  score 0" in l for l in after_catch)))
    results.append(("C5", "Q after the ending closed the window", win.closed))
    results.append(("C10", "a tick and a key after close were ignored without error", s.phase == "ended"))

    # 2. Won: player (2, 1) beside the last dot; q ends it.
    s = Session(GameState(CORRIDOR, (2, 1), (7, 1), frozenset({(3, 1)}), 5, UNDECIDED, (-1, 0)), NoDraws())
    lines, win = drive(s, ["Right", "tick", "Left", "q"])
    out += ["  won on the corridor:"] + lines
    results.append(("C4", "after the win a tick and an arrow changed nothing", all("player (3, 1) ghost (7, 1)" in l and "CLEARED  score 6" in l for l in lines[:3])))
    results.append(("C5", "q after the win closed the window", win.closed))

    # 3. Quit while playing on a generated maze.
    s = Session.new(random.Random(4))
    lines, win = drive(s, ["tick", "Down", "tick", "q"])
    out += ["  generated maze (seed 4), quit while playing:"] + lines
    results.append(("C5", "q while playing closed the window at once", win.closed and len(lines) == 4))

    # 4. C9: same maze, source and inputs, twice, over 1,000 seeds.
    same = 0
    for seed in range(1000):
        ends = []
        for _ in range(2):
            session = Session(new_game(generate_maze(random.Random(seed))), random.Random(50_000 + seed))
            script = random.Random(90_000 + seed)
            for _ in range(400):
                session.tick() if script.random() < 0.5 else session.handle(script.choice(["up", "down", "left", "right", None]))
            ends.append((session.phase, session.state))
        same += ends[0] == ends[1]
    results.append(("C9", f"identical end states for the same maze, source and inputs: {same}/1000", same == 1000))

    print("WI-12 session control, driven as the shell will drive it")
    print("\n".join(out))
    print()
    for code, text, ok in results:
        print(f"  {code:<9} {text}  {'PASS' if ok else 'FAIL'}")
    ok = all(r[2] for r in results)
    print("\nALL PASS" if ok else "\nSOME FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
