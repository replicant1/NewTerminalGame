"""WI-9/C6, the inside half: run *from a Terminal window*, find the anchor and ask Terminal about its front window.

Started by ``evidence/WI-9/terminal_anchor.py`` in a Terminal window it opens.
Writes ``<out>`` (JSON) and exits within seconds; the kernel kills it at 15 s
whatever happens, so the window that runs it can always be closed without a
"terminate running processes?" sheet.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

signal.signal(signal.SIGALRM, signal.SIG_DFL)
signal.alarm(15)

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from terminal_game.shell import anchor  # noqa: E402
from terminal_game.shell.placement import Rect, display_for, place  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1])
    start = time.monotonic()
    found = anchor.find_anchor()
    elapsed = time.monotonic() - start
    front = anchor.frontmost_window(anchor.on_screen_windows(), os.getpid())
    # What Terminal itself says its front window is (read-only: get, never set).
    said = subprocess.run(
        ["/usr/bin/osascript", "-e", 'tell application "Terminal" to get {id, bounds} of front window'],
        capture_output=True, text=True, timeout=10,
    )
    displays = anchor.visible_displays()
    x, y = place(found, (400, 602), displays)   # the game window's outer size
    game = Rect(x, y, 400, 602)
    record = {
        "displays": [[d.x, d.y, d.width, d.height] for d in displays],
        "placed_at": [x, y],
        "anchor_display": None if found is None else displays.index(display_for(found, displays)),
        "placed_wholly_on_display": [i for i, d in enumerate(displays) if d.contains(game)],
        "anchor": None if found is None else [found.x, found.y, found.width, found.height],
        "anchor_ms": round(elapsed * 1000, 1),
        "anchor_window": None if front is None else {"id": front["id"], "owner": front["owner"], "pid": front["pid"]},
        "terminal_says": said.stdout.strip(),
        "terminal_error": said.stderr.strip(),
    }
    out.write_text(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
