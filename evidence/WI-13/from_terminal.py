"""WI-13/C1, C2, C8: the README's one command, typed into a real Terminal window, twice.

    .venv/bin/python evidence/WI-13/from_terminal.py

For each of two launches this

1. opens **one** new Terminal window and types the README command into it
   (``.venv/bin/python -m terminal_game``, then ``exit``). Terminal comes to
   the front, as it does when a person types into it;
2. finds the game's window in the window server's list: the window titled
   ``Terminal Game`` whose process runs on that Terminal tab's tty;
3. reads Terminal's own bounds for its window and the game window's bounds,
   and photographs the game window's drawing area twice, half a second apart;
4. ends the game with SIGTERM to that one process (the harness cannot type
   ``q`` into another application's window without an Accessibility
   permission; ``q`` itself is proved by WI-13/C7 in the desktop tests);
5. waits until the Terminal tab's shell has exited, then closes that Terminal
   window by the id captured when it was made, only if its tty is still the
   one recorded, and confirms it is no longer visible.

It touches no other window. It prints what it measured and writes
``evidence/WI-13/from-terminal-<sha>.json`` and the captures beside it.
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

from shell_screen import capture_command, read_bmp  # noqa: E402
from terminal_game.shell.anchor import on_screen_windows  # noqa: E402
from terminal_game.shell.game import TITLE_BAR_POINTS  # noqa: E402
from terminal_game.shell.placement import OFFSET  # noqa: E402

OUT = REPO / "evidence" / "WI-13"
STATUS = " score 0    arrows, q quits"
ROLE_RGB = {"wall": (33, 33, 222), "dot": (183, 134, 10), "player": (255, 255, 0),
            "ghost": (255, 184, 255), "status": (3, 255, 255)}


def osa(script: str, timeout: float = 15) -> str:
    done = subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip())
    return done.stdout.strip()


def tty_of(pid: int) -> str:
    return subprocess.run(["ps", "-o", "tty=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()


def cell_roles(image, cw=20, ch=38):
    """For each of the 40 x 30 cells: the role whose exact colour appears in it most, or None if none does."""
    grid = []
    for r in range(30):
        row = []
        for c in range(40):
            counts = dict.fromkeys(ROLE_RGB, 0)
            for y in range(r * ch + 3, (r + 1) * ch - 3, 2):
                for x in range(c * cw + 3, (c + 1) * cw - 3, 2):
                    rgb = image.rgb(x, y)
                    for role, colour in ROLE_RGB.items():
                        if max(abs(a - b) for a, b in zip(rgb, colour)) <= 12:
                            counts[role] += 1
            best = max(counts, key=counts.get)
            row.append(best if counts[best] else None)
        grid.append(row)
    return grid


def launch(n: int, sha: str) -> dict:
    command = f"cd '{REPO}' && .venv/bin/python -m terminal_game; exit"
    window_id = osa('tell application "Terminal"\n  activate\n'
                    f'  do script "{command}"\n  return id of front window\nend tell')
    record = {"launch": n, "terminal_window": int(window_id)}
    try:
        tty = osa(f'tell application "Terminal" to get tty of tab 1 of window id {window_id}')
        record["tty"] = tty
        found, t0 = None, time.monotonic()
        while found is None and time.monotonic() - t0 < 15:
            for w in on_screen_windows():
                if w["layer"] == 0 and w["owner"].startswith("Python") and "/dev/" + tty_of(w["pid"]) == tty:
                    found = w
                    break
            time.sleep(0.05)
        if found is None:
            raise RuntimeError("the game's window never appeared")
        record["seen_after_s"] = round(time.monotonic() - t0, 2)
        record["game_pid"] = found["pid"]
        record["bounds_while_opening"] = [found["bounds"].x, found["bounds"].y, found["bounds"].width, found["bounds"].height]
        # macOS animates a new window open (it grows from about 99 %), so the bounds
        # are read again once it has settled (measured: 396 x 596 at first sight).
        time.sleep(0.8)
        settled = [w for w in on_screen_windows() if w["pid"] == found["pid"] and w["layer"] == 0]
        b = settled[0]["bounds"]
        record["game_bounds"] = [b.x, b.y, b.width, b.height]
        left, top, right, bottom = (int(v) for v in osa(
            f'tell application "Terminal" to get bounds of window id {window_id}').split(", "))
        record["terminal_bounds"] = [left, top, right - left, bottom - top]
        record["offset_from_terminal"] = [b.x - left, b.y - top]
        shots = []
        for k in range(2):
            path = OUT / f"from-terminal-{sha}-launch{n}-{k}.bmp"
            subprocess.run(capture_command(int(b.x), int(b.y + TITLE_BAR_POINTS), 400, 570, str(path)), check=True)
            shots.append(path)
            if k == 0:
                time.sleep(0.5)
        png = OUT / f"from-terminal-{sha}-launch{n}.png"
        subprocess.run(["/usr/sbin/screencapture", "-x", "-t", "png", "-R",
                        f"{int(b.x)},{int(b.y)},{int(b.width)},{int(b.height)}", str(png)], check=True)
        record["png"] = png.name
        grids = [cell_roles(read_bmp(p)) for p in shots]
        for p in shots:
            p.unlink()
        record["status_cells"] = [c for c in range(40) if grids[0][29][c] == "status"]
        record["status_expected"] = [c for c, ch in enumerate(STATUS) if ch != " "]
        record["player_cells"] = [(c, r) for r in range(29) for c in range(40) if grids[0][r][c] == "player"]
        record["ghost_cells"] = [[(c, r) for r in range(29) for c in range(40) if g[r][c] == "ghost"] for g in grids]
        record["wall_grid"] = ["".join("#" if grids[0][r][c] == "wall" else "." for c in range(40)) for r in range(29)]
        record["dot_cells"] = sum(1 for r in range(29) for c in range(40) if grids[0][r][c] == "dot")
    finally:
        pid = record.get("game_pid")
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            t0 = time.monotonic()
            while time.monotonic() - t0 < 5:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
        t0 = time.monotonic()
        busy = "true"
        while time.monotonic() - t0 < 10:
            try:
                busy = osa(f'tell application "Terminal" to get busy of tab 1 of window id {window_id}')
            except RuntimeError:
                busy = "gone"
            if busy != "true":
                break
            time.sleep(0.2)
        ours = False
        try:
            ours = osa(f'tell application "Terminal" to get tty of tab 1 of window id {window_id}') == record.get("tty")
        except RuntimeError:
            pass
        if busy == "false" and ours:
            osa(f'tell application "Terminal" to close window id {window_id}')
        try:
            record["terminal_window_visible_after"] = osa(f'tell application "Terminal" to get visible of window id {window_id}')
        except RuntimeError:
            record["terminal_window_visible_after"] = "gone"
    return record


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    launches = [launch(1, sha), launch(2, sha)]
    for r in launches:
        print(f"launch {r['launch']}: game window seen {r['seen_after_s']} s after the command; "
              f"Terminal at {r['terminal_bounds'][:2]}, game at {r['game_bounds'][:2]} "
              f"-> offset {r['offset_from_terminal']} (expected ({OFFSET}, {OFFSET}) unless clamped); "
              f"game size {r['game_bounds'][2:]}")
        print(f"   status row cells {r['status_cells'] == r['status_expected'] and 'match' or 'DIFFER'} ' score 0    arrows, q quits'; "
              f"player cells {r['player_cells']}; dots {r['dot_cells']}; ghost at {r['ghost_cells'][0]} then {r['ghost_cells'][1]} "
              f"-> moved within 0.5 s: {r['ghost_cells'][0] != r['ghost_cells'][1]}; Terminal window after: visible={r['terminal_window_visible_after']}")
    different = launches[0]["wall_grid"] != launches[1]["wall_grid"]
    differing_cells = sum(a != b for x, y in zip(launches[0]["wall_grid"], launches[1]["wall_grid"]) for a, b in zip(x, y))
    print(f"mazes differ between launches: {different} ({differing_cells} of 1160 maze cells differ in wall/not-wall)")
    failures = []
    for r in launches:
        n = r["launch"]
        walls = sum(row.count("#") for row in r["wall_grid"])
        if walls < 200:
            failures.append(f"launch {n}: only {walls} wall cells classified; the maze was not seen")
        if r["dot_cells"] < 100:
            failures.append(f"launch {n}: only {r['dot_cells']} dot cells classified")
        if r["status_cells"] != r["status_expected"]:
            failures.append(f"launch {n}: status row cells {r['status_cells']} != {r['status_expected']}")
        if len(r["player_cells"]) != 3:
            failures.append(f"launch {n}: player cells {r['player_cells']}")
        if len(r["ghost_cells"][0]) != 3 or r["ghost_cells"][0] == r["ghost_cells"][1]:
            failures.append(f"launch {n}: ghost {r['ghost_cells']} not seen moving within 0.5 s")
        dx, dy = r["offset_from_terminal"]
        if not (20 <= dx <= 60 and 20 <= dy <= 60):
            failures.append(f"launch {n}: offset {r['offset_from_terminal']} not 20-60 points each way")
        if r["game_bounds"][2:] != [400.0, 602.0]:
            failures.append(f"launch {n}: game window {r['game_bounds'][2:]}, not 400 x 602 points")
        if r["terminal_window_visible_after"] not in ("false", "gone"):
            failures.append(f"launch {n}: Terminal window {r['terminal_window']} still visible")
    if not different:
        failures.append("the two launches showed the same maze")
    record = {"head": sha, "taken_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "launches": launches, "mazes_differ": different, "differing_cells": differing_cells,
              "failures": failures}
    (OUT / f"from-terminal-{sha}.json").write_text(json.dumps(record, indent=1))
    print(f"written: evidence/WI-13/from-terminal-{sha}.json")
    for failure in failures:
        print("FAILED:", failure)
    print("all checks passed" if not failures else f"{len(failures)} check(s) FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
