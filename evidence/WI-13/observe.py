"""WI-13 observations: the scripted runs, photographed, saved as PNGs named with the head sha.

    .venv/bin/python evidence/WI-13/observe.py

Runs ``tests/game_driver.py`` three times (ghost-and-key, loss, win), each one
short window that ends itself with ``q``/``Q``, and converts the captures to
PNG with macOS's own ``sips``:

* ``game-<sha>-start.png``: the first picture (C9);
* ``game-<sha>-before-key.png`` / ``-after-key.png``: one arrow onto a dot (C4);
* ``game-<sha>-loss.png``: the final picture of a loss (C5);
* ``game-<sha>-win.png``: the final picture of a win (C6);

plus ``game-<sha>-transcript.json`` with what each run recorded.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests"))

from shell_run import run_driver  # noqa: E402

OUT = REPO / "evidence" / "WI-13"
PICK = {"ghost-and-key": {"start": "start", "before-key": "before-key", "after-key": "after-key"},
        "loss": {"final": "loss"}, "win": {"final": "win"}}


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    transcript = {"head": sha, "runs": {}}
    work = Path(tempfile.mkdtemp(prefix="wi13-observe-"))
    for scenario, picks in PICK.items():
        run = run_driver(scenario, work / scenario, driver=REPO / "tests" / "game_driver.py")
        transcript["runs"][scenario] = {"status": run.status, "result": run.result}
        for capture, label in picks.items():
            png = OUT / f"game-{sha}-{label}.png"
            subprocess.run(["/usr/bin/sips", "-s", "format", "png", str(work / scenario / f"{capture}.bmp"),
                            "--out", str(png)], check=True, capture_output=True)
            print(f"{scenario}: {png.relative_to(REPO)}")
    (OUT / f"game-{sha}-transcript.json").write_text(json.dumps(transcript, indent=1))
    print(f"written: evidence/WI-13/game-{sha}-transcript.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
