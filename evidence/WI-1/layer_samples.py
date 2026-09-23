"""WI-1/C3 and C4: the layer check, run from its command line on sample trees
and on the real tree, so its own report is what you read.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-1/layer_samples.py

Three runs of ``python -m tools.layer_check <root>``:

1. **A sample tree with bad imports** (C3): one of each kind the rule forbids.
   Each should come back as a ``VIOLATION`` line naming the importing module,
   the line, and what it imported, and the check should FAIL (exit 1).
2. **A sample tree whose presentation layer has no module** (C4): the counts
   line should show ``presentation 0``, a ``PROBLEM`` line should say it
   examined no module there, and the check should FAIL (exit 1).
3. **The real tree** (C3, C4): the counts line should show at least one module
   in every layer, no ``VIOLATION`` or ``PROBLEM`` lines, and PASS (exit 0).

The sample trees are written to a temporary directory with the same
``[tool.terminal_game.layers]`` declaration as this repository's
``pyproject.toml``, copied from it.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BAD_IMPORTS = {
    "terminal_game/shell/window.py": "import tkinter\n",
    "terminal_game/presentation/frames.py": "import tkinter\n",
    "terminal_game/application/session.py": "import time\nfrom ..presentation import frames\n",
    "terminal_game/domain/maze.py": "import terminal_game.shell.window\n",
    "terminal_game/domain/ghost.py": "import random\nstep = random.choice\n",
}

EXPECTED_BAD = [
    "terminal_game.presentation.frames:1 imports tkinter  [toolkit-or-os]",
    "terminal_game.application.session:1 imports time  [clock]",
    "terminal_game.application.session:2 imports terminal_game.presentation.frames  [upward]",
    "terminal_game.domain.maze:1 imports terminal_game.shell.window  [upward]",
    "terminal_game.domain.ghost:2 imports random.choice  [randomness]",
]


def declaration() -> str:
    text = (REPO / "pyproject.toml").read_text()
    table = re.search(r"^\[tool\.terminal_game\.layers\]\n(?:[^\[].*\n?)*", text, re.M)
    return table.group(0)


def sample(modules: dict, skip_layer: str = "") -> Path:
    root = Path(tempfile.mkdtemp(prefix="wi1-layers-"))
    (root / "pyproject.toml").write_text(declaration())
    base = {"terminal_game/__init__.py": ""}
    for layer in ("shell", "presentation", "application", "domain"):
        if layer != skip_layer:
            base["terminal_game/%s/__init__.py" % layer] = ""
    for name, source in {**base, **modules}.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    if skip_layer:
        (root / "terminal_game" / skip_layer).mkdir(parents=True, exist_ok=True)
    return root


def run(title: str, root: Path):
    command = [sys.executable, "-m", "tools.layer_check", str(root)]
    done = subprocess.run(command, cwd=str(REPO), capture_output=True, text=True)
    print("---- %s" % title)
    print("$ python -m tools.layer_check %s    (exit %d)" % (root, done.returncode))
    for line in (done.stdout + done.stderr).rstrip().splitlines():
        print("    " + line)
    return done.returncode, done.stdout


def main() -> int:
    ok = True
    status, out = run("1. sample tree with bad imports", sample(BAD_IMPORTS))
    missing = [e for e in EXPECTED_BAD if ("VIOLATION " + e) not in out]
    extra = len(re.findall(r"^VIOLATION ", out, re.M)) - len(EXPECTED_BAD)
    c3_sample = status == 1 and not missing and extra == 0
    ok &= c3_sample
    print("WI-1/C3 %s (sample): exit %d; %d of %d expected violations named; %d unexpected"
          % ("HOLDS" if c3_sample else "DOES NOT HOLD", status,
             len(EXPECTED_BAD) - len(missing), len(EXPECTED_BAD), max(extra, 0)))
    for e in missing:
        print("    missing: " + e)

    status, out = run("2. sample tree with an empty presentation layer",
                      sample({"terminal_game/domain/maze.py": ""}, skip_layer="presentation"))
    c4_sample = (status == 1 and "presentation 0" in out
                 and "PROBLEM   examined no module in the presentation layer" in out)
    ok &= c4_sample
    print("WI-1/C4 %s (sample): exit %d; counts line shows presentation 0 and the check fails on it"
          % ("HOLDS" if c4_sample else "DOES NOT HOLD", status))

    status, out = run("3. the real tree", REPO)
    counts = dict((name, int(n)) for name, n in re.findall(r"(\w+) (\d+)", out.splitlines()[0]))
    every_layer = all(counts.get(name, 0) >= 1
                      for name in ("shell", "presentation", "application", "domain"))
    real = status == 0 and every_layer and "VIOLATION" not in out and "PROBLEM" not in out
    ok &= real
    print("WI-1/C3+C4 %s (real tree): exit %d; no violations; modules examined per layer: %s"
          % ("HOLDS" if real else "DOES NOT HOLD", status,
             ", ".join("%s %d" % item for item in counts.items())))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
