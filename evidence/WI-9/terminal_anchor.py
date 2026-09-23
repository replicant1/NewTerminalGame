"""WI-9/C6: run the anchor query from a real Terminal window and compare it with what Terminal reports.

    .venv/bin/python evidence/WI-9/terminal_anchor.py

Opens **one** new Terminal window (Terminal comes to the front, as it does
when a person types the game's command into it), runs
``evidence/WI-9/report_anchor.py`` in it, waits for that to finish and for the
window's process to exit, then closes that window, by the id captured when it
was made, and checks it is gone. It touches no other window. It prints the
anchor next to Terminal's own ``bounds of front window`` and whether they
agree, and writes both to ``evidence/WI-9/terminal-anchor-<sha>.json``.

Terminal's ``bounds`` are ``{left, top, right, bottom}``; the anchor is
``(x, y, width, height)``. They agree when ``x, y = left, top`` and
``width, height = right - left, bottom - top``.
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def osa(script: str, timeout: float = 15) -> str:
    done = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip())
    return done.stdout.strip()


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    out = Path(tempfile.mkdtemp(prefix="wi9-")) / "anchor.json"
    command = f"cd '{REPO}' && .venv/bin/python evidence/WI-9/report_anchor.py '{out}'; exit"
    window_id = osa(
        'tell application "Terminal"\n'
        "  activate\n"
        f'  set t to do script "{command}"\n'
        "  return id of front window\n"
        "end tell"
    )
    print(f"opened Terminal window id {window_id}")
    try:
        deadline = time.monotonic() + 20
        while not out.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        # Let the window's process finish before anything closes it.
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                busy = osa(f'tell application "Terminal" to get busy of tab 1 of window id {window_id}')
            except RuntimeError:
                busy = "gone"   # the profile closed it when the shell exited
            if busy != "true":
                break
            time.sleep(0.2)
    finally:
        try:
            busy = osa(f'tell application "Terminal" to get busy of tab 1 of window id {window_id}')
        except RuntimeError:
            busy = "gone"
        if busy == "false":
            osa(f'tell application "Terminal" to close window id {window_id}')
        elif busy == "true":
            print(f"window {window_id} still busy; NOT closing it (that would raise a sheet)")
        try:
            visible = osa(f'tell application "Terminal" to get visible of window id {window_id}')
        except RuntimeError:
            visible = "gone"
        print(f"window {window_id} after closing: visible={visible}")
    if not out.exists():
        print("no report was written")
        return 1
    record = json.loads(out.read_text())
    said = [int(float(v)) for v in record["terminal_says"].replace(" ", "").split(",")]
    term_id, left, top, right, bottom = said
    expected = [left, top, right - left, bottom - top]
    record.update(head=sha, window_opened=int(window_id), terminal_rect=expected,
                  agree=record["anchor"] == expected, taken_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(f"anchor (x, y, w, h)          : {record['anchor']}  found in {record['anchor_ms']} ms, owner {record['anchor_window']}")
    print(f"Terminal front window id {term_id}: bounds {{{left}, {top}, {right}, {bottom}}} -> (x, y, w, h) {expected}")
    print(f"agree: {record['agree']}")
    dest = REPO / "evidence" / "WI-9" / f"terminal-anchor-{sha}.json"
    dest.write_text(json.dumps(record, indent=1))
    print(f"written: {dest.relative_to(REPO)}")
    return 0 if record["agree"] else 1


if __name__ == "__main__":
    sys.exit(main())
