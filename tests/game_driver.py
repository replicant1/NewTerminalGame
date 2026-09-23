"""The program WI-13's desktop tests run: the assembled game, a fixed seed, driven by real key events.

Test support, not a test. ``python tests/game_driver.py <scenario> <outdir>``,
from the repository root, writes ``<outdir>/result.json`` plus captures and
the composed frame for each capture. It calls the same :func:`play` that
``python -m terminal_game`` calls; the only difference is the session it is
handed: ``Session.new(random.Random(SEED))``, the test-only fixed seed the plan
asks for, so a win and a loss can be planned.

Keys are real AppKit key events posted into the game's own queue
(``tests/shell_appkit.py``); the moves are planned by reading the session's
state, never by calling the session directly. Every scenario ends the session
with ``q`` or ``Q``; the kernel kills the process at 60 s if anything hangs.
"""

import json
import os
import random
import signal
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import shell_appkit as appkit  # noqa: E402
from shell_screen import capture_command  # noqa: E402
from terminal_game.application.session import DECIDED, Session  # noqa: E402
from terminal_game.domain.maze import DIRECTIONS  # noqa: E402
from terminal_game.presentation.frame_composer import compose  # noqa: E402
from terminal_game.shell import game  # noqa: E402
from terminal_game.shell.window import GameWindow  # noqa: E402

SEED = 13
DEADLINE_S = 60
SETTLE_MS = 400
KEY_FOR = {(0, -1): "Up", (0, 1): "Down", (1, 0): "Right", (-1, 0): "Left"}


def route(state, targets, avoid=frozenset()):
    """The first step of a shortest corridor path from the player to the nearest target, or None."""
    maze, start = state.maze, state.player
    if start in targets:
        return None
    seen = {start: None}
    queue = deque([start])
    while queue:
        square = queue.popleft()
        for d in DIRECTIONS:
            nxt = (square[0] + d[0], square[1] + d[1])
            if nxt in seen or not maze.is_corridor(nxt) or (nxt in avoid and nxt not in targets):
                continue
            seen[nxt] = square
            if nxt in targets:
                while seen[nxt] != start:
                    nxt = seen[nxt]
                return (nxt[0] - start[0], nxt[1] - start[1])
            queue.append(nxt)
    return None


def danger(state):
    """The ghost's square and every square it could reach in the next two steps."""
    near = {state.ghost}
    for _ in range(2):
        near |= {(s[0] + d[0], s[1] + d[1]) for s in near for d in DIRECTIONS}
    return frozenset(near)


def escape(state):
    """When no dot is safely reachable: step to the open neighbour furthest from the ghost, if that is further."""
    gx, gy = state.ghost
    here = abs(state.player[0] - gx) + abs(state.player[1] - gy)
    best, best_distance = None, here
    for d in DIRECTIONS:
        nxt = (state.player[0] + d[0], state.player[1] + d[1])
        distance = abs(nxt[0] - gx) + abs(nxt[1] - gy)
        if state.maze.is_corridor(nxt) and nxt != state.ghost and distance > best_distance:
            best, best_distance = d, distance
    return best


class Driver:
    def __init__(self, scenario: str, outdir: Path) -> None:
        self.scenario, self.outdir = scenario, outdir
        self.session = Session.new(random.Random(SEED))
        self.window = GameWindow()
        self.root = self.window.root
        self.result: dict = {"scenario": scenario, "pid": os.getpid(), "seed": SEED,
                             "dots_at_start": len(self.session.state.dots), "captures": {}}
        self.moves_posted = 0
        self.mapped_at = None
        self.root.bind("<Map>", self._mapped, add="+")

    def _mapped(self, event) -> None:
        if self.mapped_at is None and event.widget is self.root:
            self.mapped_at = time.monotonic()

    def start(self, generator) -> None:
        def step():
            item = next(generator, None)
            if item is None:
                return
            if isinstance(item, subprocess.Popen):
                poll(item)
            else:
                self.root.after(item, step)

        def poll(process):
            if process.poll() is None:
                self.root.after(5, lambda: poll(process))
            else:
                step()

        self.root.after(0, step)

    # -- looking --------------------------------------------------------------------

    def facts(self, state) -> dict:
        return {"player": list(state.player), "ghost": list(state.ghost), "score": state.score,
                "outcome": state.outcome, "dots": len(state.dots), "phase": self.session.phase}

    def capture(self, name: str):
        """Capture the drawing area while the state holds still; record the frame it should show.

        During play the ghost moves every tick, so the capture is started just
        after a state change and kept only if no change happened while it was
        taken. After the game is decided nothing changes, so it is taken at once.
        """
        for attempt in range(20):
            if self.session.phase != DECIDED:
                before = self.session.state
                while self.session.state is before:
                    yield 2
            state = self.session.state
            yield 20   # let Tk draw the change and the window server composite it
            x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
            w, h = self.window.size
            path = self.outdir / f"{name}.bmp"
            yield subprocess.Popen(capture_command(x, y, w, h, str(path)))
            if self.session.state is state:
                (self.outdir / f"{name}.frame.json").write_text(json.dumps(compose(state)))
                self.result["captures"][name] = {"attempts": attempt + 1, **self.facts(state)}
                return
        raise RuntimeError(f"could not take a still capture {name!r}")

    # -- acting -----------------------------------------------------------------------

    def regain_focus(self, phase: str):
        if appkit.is_active() and appkit.key_window_number():
            return
        self.result.setdefault("refocused", []).append(phase)
        self.root.focus_force()
        self.window.canvas.focus_set()
        yield 300

    def press(self, name: str):
        appkit.post_key(name)
        self.moves_posted += 1
        yield 1

    def walk(self, targets_of, avoid_of, limit_s: float):
        """Walk, one real key press at a time, until the game is decided or time runs out."""
        end = time.monotonic() + limit_s
        while self.session.phase != DECIDED and time.monotonic() < end:
            state = self.session.state
            avoid = avoid_of(state)
            step = route(state, frozenset(targets_of(state)) - avoid, avoid)
            if step is None and avoid:
                step = escape(state)
            if step is None:
                yield 10   # nothing to do yet: let the ghost move on
                continue
            yield from self.press(KEY_FOR[step])
            waited = 0
            while self.session.state.player == state.player and self.session.phase != DECIDED and waited < 200:
                yield 1
                waited += 1

    def finish(self, key: str):
        """End the session the way a person would: q or Q."""
        yield from self.regain_focus("quit")
        self.result["quit_key"] = key
        self.result["quit_posted_at"] = time.time()
        (self.outdir / "result.json").write_text(json.dumps(self.result))
        appkit.post_key(key)
        yield 3000
        self.result["quit_ignored"] = True
        (self.outdir / "result.json").write_text(json.dumps(self.result))
        self.window.close()

    # -- scenarios ----------------------------------------------------------------------

    def ghost_and_key(self):
        """C1 (the ghost moves within 0.5 s of the window opening), C3, C4, C9, then q during play."""
        # From the very start: watch for the ghost's first move, no key pressed.
        start_ghost = self.session.state.ghost
        while self.session.state.ghost == start_ghost:
            yield 1
        first_move_at = time.monotonic()
        self.result["first_ghost_move"] = {
            "mapped_to_first_move_s": None if self.mapped_at is None else first_move_at - self.mapped_at,
            "keys_posted_before": self.moves_posted,
            "from": list(start_ghost), "to": list(self.session.state.ghost),
        }
        yield SETTLE_MS
        yield from self.regain_focus("start")
        self.result["facts"] = {"size": list(self.window.size), "cell": list(self.window.cell_size)}
        yield from self.capture("start")
        # Five seconds with no key pressed: count the ghost's moves.
        last, moves, t0 = self.session.state.ghost, 0, time.monotonic()
        while time.monotonic() - t0 < 5.0:
            yield 2
            if self.session.state.ghost != last:
                moves += 1
                last = self.session.state.ghost
        self.result["ghost_moves_in_5s"] = moves
        self.result["ghost_window_s"] = time.monotonic() - t0
        # One arrow key onto a neighbouring square that still holds a dot.
        yield from self.regain_focus("key")
        state = self.session.state
        options = [d for d in DIRECTIONS
                   if (state.player[0] + d[0], state.player[1] + d[1]) in state.dots
                   and (state.player[0] + d[0], state.player[1] + d[1]) not in danger(state)]
        if not options:
            raise RuntimeError("no safe dotted neighbour from the start square")
        direction = options[0]
        yield from self.capture("before-key")
        before = self.session.state
        yield from self.press(KEY_FOR[direction])
        while self.session.state.player == before.player:
            yield 1
        self.result["key"] = {"name": KEY_FOR[direction], "before": self.facts(before),
                              "after": self.facts(self.session.state),
                              "target": [before.player[0] + direction[0], before.player[1] + direction[1]]}
        yield from self.capture("after-key")
        yield from self.finish("q")

    def loss(self):
        """C5: walk into the ghost, then watch the final picture for 3 s of ticks and keys; C7: Q."""
        yield SETTLE_MS
        yield from self.regain_focus("start")
        yield from self.walk(lambda s: {s.ghost}, lambda s: frozenset(), 20)
        self.result["decided"] = self.facts(self.session.state)
        self.result["moves_posted"] = self.moves_posted
        yield from self.capture("final")
        t0 = time.monotonic()
        while time.monotonic() - t0 < 3.2:
            for name in ("Up", "Left", "Down", "Right"):
                appkit.post_key(name)
            yield 50
        self.result["after_3s"] = self.facts(self.session.state)
        yield from self.capture("final-after-3s")
        yield from self.finish("Q")

    def win(self):
        """C6: eat every dot while keeping clear of the ghost, then watch the final picture; C7: q."""
        yield SETTLE_MS
        yield from self.regain_focus("start")
        yield from self.walk(lambda s: s.dots, danger, 45)
        self.result["decided"] = self.facts(self.session.state)
        self.result["moves_posted"] = self.moves_posted
        yield from self.capture("final")
        for name in ("Up", "Left", "Down", "Right") * 10:
            appkit.post_key(name)
            yield 50
        self.result["after_keys"] = self.facts(self.session.state)
        yield from self.capture("final-after-keys")
        yield from self.finish("q")

    def quit_playing(self):
        """C7: Q during play."""
        yield SETTLE_MS
        yield from self.regain_focus("start")
        self.result["phase_at_quit"] = self.session.phase
        yield from self.finish("Q")


SCENARIOS = {"ghost-and-key": Driver.ghost_and_key, "loss": Driver.loss, "win": Driver.win,
             "quit-playing": Driver.quit_playing}


def main() -> int:
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(DEADLINE_S)
    scenario, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    driver = Driver(scenario, outdir)
    driver.start(SCENARIOS[scenario](driver))
    status = game.play(driver.session, driver.window)
    (outdir / "exit.json").write_text(json.dumps({"run_returned_at": time.time(), "status": status}))
    return status


if __name__ == "__main__":
    sys.exit(main())
