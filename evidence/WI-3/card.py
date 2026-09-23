"""WI-3 test card: the shell's real window showing the specimen picture. Evidence, not production.

Run from the repository root:

    .venv/bin/python evidence/WI-3/card.py

A window titled "Terminal Game" opens showing the specimen picture from
docs/FUNCTIONAL_REQUIREMENTS.md §3 in the six colour roles. The arrow keys
move the yellow marker one grid square (two cells) at a time; the pink marker
moves one square per tick along the bottom corridor, about seven times a
second. Walls are ignored: this is a test card, not the game. ``q`` or ``Q``
closes it, as do the title-bar close button and Quit in the application menu.

    .venv/bin/python evidence/WI-3/card.py --observe <dir>

does the same unattended: it photographs the window (title bar included) as
PNGs in <dir>, presses three arrow keys into its own window, photographs it
again, writes a transcript, and closes itself. Nothing else is touched.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

import shell_testcard  # noqa: E402
from terminal_game.shell.frame import COLUMNS, ROWS  # noqa: E402
from terminal_game.shell.palette import BACKGROUND, DOT, GHOST, PLAYER  # noqa: E402
from terminal_game.shell.window import GameWindow  # noqa: E402

MOVES = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
SQUARES_ACROSS, SQUARES_DOWN = 19, 29


class Card:
    def __init__(self) -> None:
        self.base = shell_testcard.specimen_frame()
        # Take the actors out of the specimen and draw them as markers instead.
        lines = shell_testcard.specimen_lines()
        self.player = self.ghost = None
        for r, line in enumerate(lines[:SQUARES_DOWN]):
            if "▐█▌" in line:
                self.player = [(line.index("▐█▌") + 1) // 2, r]
            if "▗█▖" in line:
                self.ghost = [(line.index("▗█▖") + 1) // 2, r]
        for r in range(SQUARES_DOWN):
            for c in range(COLUMNS):
                if self.base[r][c][1] in (PLAYER, GHOST):
                    self.base[r][c] = ("▪", DOT) if c % 2 == 0 else (" ", BACKGROUND)
        self.ghost_step = 1
        self.window = GameWindow()
        self.keys = []
        self.ticks = 0

    def frame(self):
        frame = [list(row) for row in self.base]
        for (col, row), role, glyphs in ((self.player, PLAYER, "▐█▌"), (self.ghost, GHOST, "▗█▖")):
            centre = 2 * col
            for offset, glyph in zip((-1, 0, 1), glyphs):
                if 0 <= centre + offset < COLUMNS:
                    frame[row][centre + offset] = (glyph, role)
        return frame

    def on_key(self, name: str) -> None:
        self.keys.append(name)
        if name in ("q", "Q"):
            self.window.close()
            return
        if name in MOVES:
            dx, dy = MOVES[name]
            self.player[0] = min(max(self.player[0] + dx, 0), SQUARES_ACROSS - 1)
            self.player[1] = min(max(self.player[1] + dy, 0), SQUARES_DOWN - 1)
            self.window.paint(self.frame())

    def on_tick(self) -> None:
        self.ticks += 1
        col = self.ghost[0] + self.ghost_step
        if not 1 <= col <= SQUARES_ACROSS - 2:
            self.ghost_step = -self.ghost_step
            col = self.ghost[0] + self.ghost_step
        self.ghost[0] = col
        self.window.paint(self.frame())


def observe(card: Card, outdir: Path) -> None:
    """Photograph the running card, press three arrows, photograph again, then close."""
    import shell_appkit as appkit

    root = card.window.root
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    transcript = {"head": sha, "taken_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    def shot(name):
        # The whole window, title bar included: Tk's content origin less the 32-point title bar.
        x, y = root.winfo_rootx(), root.winfo_rooty() - 32
        w, h = card.window.size
        path = outdir / f"card-{sha}-{name}.png"
        subprocess.run(["/usr/sbin/screencapture", "-x", "-t", "png", "-R", f"{x},{y},{w},{h + 32}", str(path)], check=True)
        transcript.setdefault("shots", []).append(path.name)

    def first():
        transcript.update(
            title=root.title(), family=card.window.family, cell=card.window.cell_size, size=card.window.size,
            player_start=list(card.player),
        )
        shot("specimen")
        for name in ("Up", "Up", "Left"):
            appkit.post_key(name)
        root.after(400, second)

    def second():
        transcript.update(keys=list(card.keys), player_after=list(card.player), ticks=card.ticks)
        shot("after-keys")
        (outdir / f"card-{sha}-transcript.json").write_text(json.dumps(transcript, indent=1))
        card.window.close()

    root.after(600, first)


def main() -> int:
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    card = Card()
    card.window.paint(card.frame())
    if len(sys.argv) >= 3 and sys.argv[1] == "--observe":
        signal.alarm(20)   # unattended: never outlive a hang
        outdir = Path(sys.argv[2])
        outdir.mkdir(parents=True, exist_ok=True)
        observe(card, outdir)
    return card.window.run(card.on_key, card.on_tick)


if __name__ == "__main__":
    sys.exit(main())
