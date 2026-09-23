"""The program the shell's desktop tests run: a real GameWindow, driven by a script.

Test support, not a test. Run as ``python tests/shell_driver.py <scenario> <outdir>``
from the repository root; it writes ``<outdir>/result.json`` and any captures
into ``<outdir>``, and writes **nothing** to its terminal unless something
fails (WI-3/C1).

Every scenario ends the session itself within seconds. A hard deadline
(``SIGALRM``, default action) kills the process if anything hangs, and the window goes with it.
The only window it touches is its own.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import shell_appkit as appkit  # noqa: E402
import shell_testcard as card  # noqa: E402
from shell_screen import capture_command  # noqa: E402
from terminal_game.shell.window import GameWindow  # noqa: E402

DEADLINE_S = 40
SETTLE_MS = 400      # after mapping, before looking
PAINT_MS = 150       # after a paint, before capturing
PLACE_AT = (120, 140)  # where the card scenario places its window (WI-3/A3)


class Driver:
    def __init__(self, scenario: str, outdir: Path) -> None:
        self.scenario = scenario
        self.outdir = outdir
        self.result: dict = {"scenario": scenario, "pid": os.getpid()}
        self.keys: list[list] = []
        self.ticks: list[float] = []
        self.captures: list[str] = []
        kwargs = {}
        if scenario == "fallback":
            kwargs["families"] = ("No Such Typeface WI-3", "Courier New")
        elif scenario == "fallback-none":
            kwargs["families"] = ("No Such Typeface WI-3",)
        self.window = GameWindow(**kwargs)
        self.root = self.window.root
        if scenario == "card":
            self.window.place(*PLACE_AT)

    # -- the sequencer: a scenario is a generator yielding ms to wait, or a Popen to wait on

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
                self.root.after(10, lambda: poll(process))
            else:
                step()

        self.root.after(0, step)

    def capture(self, name: str) -> subprocess.Popen:
        x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
        w, h = self.window.size
        path = str(self.outdir / f"{name}.bmp")
        self.captures.append(name)
        return subprocess.Popen(capture_command(x, y, w, h, path))

    def facts(self) -> dict:
        root, canvas = self.root, self.window.canvas
        return {
            "title": root.title(),
            "family": self.window.family,
            "cell": list(self.window.cell_size),
            "size": list(self.window.size),
            "root_xywh": [root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()],
            "canvas_wh": [canvas.winfo_width(), canvas.winfo_height()],
            "canvas_xy_in_root": [canvas.winfo_x(), canvas.winfo_y()],
            "children": [str(w) for w in root.winfo_children()],
            "toplevels": [str(w) for w in root.winfo_children() if w.winfo_toplevel() is w],
            "item_types": sorted({canvas.type(i) for i in canvas.find_all()}),
            "item_count": len(canvas.find_all()),
            "ns_visible_windows": appkit.visible_window_count(),
            "ns_key_window": appkit.key_window_number(),
            "ns_app_active": appkit.is_active(),
            "focus": str(root.focus_get()),
            "tk_resizable": list(root.resizable()),
            "ns_style_resizable": appkit.window_is_resizable(),
            "zoom_button_enabled": appkit.title_button_enabled(appkit.ZOOM_BUTTON),
        }

    def finish(self) -> None:
        """Write the result and end the session the way the program would (WI-3/C12)."""
        self.result.update(keys=self.keys, ticks=self.ticks, captures=self.captures)
        self.result["close_called_at"] = time.time()
        (self.outdir / "result.json").write_text(json.dumps(self.result))
        self.window.close()

    # -- handlers ---------------------------------------------------------------

    def on_key(self, name: str) -> None:
        self.keys.append([name, time.monotonic()])
        if self.scenario == "raise-key":
            raise RuntimeError("deliberate failure in a key handler (WI-3/C14)")
        if self.scenario == "exit-key":
            raise SystemExit(3)  # tkinter lets SystemExit out of its loop rather than reporting it
        if name == "q" and self.result.get("quit_armed"):
            self.finish()

    def on_tick(self) -> None:
        self.ticks.append(time.monotonic())
        if self.scenario == "raise-tick" and len(self.ticks) == 3:
            raise RuntimeError("deliberate failure in a tick handler (WI-3/C14)")

    # -- scenarios ----------------------------------------------------------------

    def card(self):
        yield SETTLE_MS
        self.result["facts"] = self.facts()
        swift = subprocess.Popen(
            ["/usr/bin/swift", str(HERE / "shell_windows.swift"), str(os.getpid())],
            stdout=open(self.outdir / "windows.json", "w"),
        )
        frames = [("blank", card.blank())]
        frames += [(f"roles{k}", card.role_blocks(k)) for k in range(6)]
        frames += [(f"alphabet{k}", card.alphabet(k)) for k in range(5)]
        frames += [("border", card.border()), ("specimen", card.specimen_frame())]
        for name, frame in frames:
            self.window.paint(frame)
            yield PAINT_MS
            yield self.capture(name)
        # A malformed frame (its very last cell is bad) must change nothing (WI-3/A1).
        bad = card.specimen_frame()
        bad[-1][-1] = ("xx", "status")
        try:
            self.window.paint(bad)
            self.result["bad_frame_error"] = None
        except ValueError as error:
            self.result["bad_frame_error"] = str(error)
        yield PAINT_MS
        yield self.capture("after-bad-frame")
        # A text caret blinks; look at an empty picture six times over 1.5 s.
        self.window.paint(card.blank())
        for n in range(6):
            yield 250
            yield self.capture(f"blank-burst{n}")
        yield swift
        # Resizing, three ways a person or the system might try it.
        w, h = self.window.size
        attempts = {}
        appkit.post_mouse_drag(w - 1, 1, w + 150, -150)   # drag the bottom-right corner out
        yield 300
        attempts["corner_drag"] = self._sizes()
        appkit.click_title_button(appkit.ZOOM_BUTTON)       # the green zoom button
        yield 500
        attempts["zoom_button"] = self._sizes()
        self.root.geometry(f"{w + 200}x{h + 130}")          # a size request through Tk
        yield 300
        attempts["geometry_request"] = self._sizes()
        self.result["resize"] = attempts
        self.window.paint(card.border())
        yield PAINT_MS
        yield self.capture("border-after-resize")
        self.finish()

    def keys_and_ticks(self):
        self.window.paint(card.blank())
        yield SETTLE_MS
        self.result["facts"] = self.facts()
        yield self.capture("before-typing")
        names = ["Up", "Down", "Left", "Right", "q", "Q", "Q-caps-lock", "a", "z", "1",
                 "space", "Return", "Escape", "Tab", "BackSpace", "F1"]
        self.result["posted"] = names
        for name in names:
            appkit.post_key(name)
            yield 40
        yield PAINT_MS
        yield self.capture("after-typing")
        # Five seconds with no key pressed.
        self.result["idle_window"] = [time.monotonic(), None]
        yield 5000
        self.result["idle_window"][1] = time.monotonic()
        # Five seconds of keys as fast as this script can post them.
        self.result["focus_at_flood"] = self._focus()
        flood_keys_before = len(self.keys)
        self.result["flood_window"] = [time.monotonic(), None]
        end = time.monotonic() + 5.0
        while time.monotonic() < end:
            for name in ("a", "z", "Left", "Right"):
                appkit.post_key(name)
            yield 1
        self.result["flood_window"][1] = time.monotonic()
        yield 50
        self.result["flood_keys"] = len(self.keys) - flood_keys_before
        # The program ends the session on q (WI-3/C12).
        self.result["focus_at_quit"] = self._focus()
        self.result["quit_armed"] = True
        appkit.post_key("q")
        yield 2000   # finish() runs from the key handler long before this
        self.finish()  # only reached if q never ended the session

    def flip(self):
        a, b = card.specimen_frame(), card.shifted_specimen()
        self.window.paint(card.blank())
        yield SETTLE_MS
        yield self.capture("blank")   # the clip mask for this window
        self.window.paint(a)
        yield PAINT_MS
        yield self.capture("ref-a")
        self.window.paint(b)
        yield PAINT_MS
        yield self.capture("ref-b")
        frames = [a, b]
        state = {"n": 0, "paints": 0}
        end = time.monotonic() + 5.0

        def repaint():
            if time.monotonic() >= end:
                return
            state["n"] ^= 1
            self.window.paint(frames[state["n"]])
            state["paints"] += 1
            self.root.after(15, repaint)

        repaint()
        n = 0
        while time.monotonic() < end:
            yield self.capture(f"flip{n:03d}")
            n += 1
        yield 50
        self.result["paints"] = state["paints"]
        self.finish()

    def close_button(self):
        yield SETTLE_MS
        self.result["facts"] = self.facts()
        self.result["clicked_at"] = time.time()
        (self.outdir / "result.json").write_text(json.dumps(self.result))
        appkit.click_title_button(appkit.CLOSE_BUTTON)
        yield 3000
        self.finish()  # only reached if the expected ending never came

    def app_quit(self):
        yield SETTLE_MS
        self.result["facts"] = self.facts()
        self.result["menu_item"] = appkit.app_menu_quit_title()
        self.result["clicked_at"] = time.time()
        (self.outdir / "result.json").write_text(json.dumps(self.result))
        appkit.choose_quit_from_app_menu()
        yield 3000
        self.finish()  # only reached if the expected ending never came

    def raise_key(self):
        yield SETTLE_MS
        (self.outdir / "result.json").write_text(json.dumps({"ready_at": time.time(), "pid": os.getpid()}))
        appkit.post_key("a")
        yield 3000
        self.finish()  # only reached if the expected ending never came

    def raise_tick(self):
        yield 3000
        self.finish()  # only reached if the expected ending never came

    def fallback(self):
        self.window.paint(card.blank())
        yield SETTLE_MS
        self.result["facts"] = self.facts()
        yield self.capture("blank")
        self.window.paint(card.border())
        yield PAINT_MS
        yield self.capture("border")
        self.window.paint(card.specimen_frame())
        yield PAINT_MS
        yield self.capture("specimen")
        self.finish()

    def _focus(self) -> dict:
        return {"ns_app_active": appkit.is_active(), "ns_key_window": appkit.key_window_number(),
                "tk_focus": str(self.root.focus_get())}

    def _sizes(self) -> dict:
        return {
            "root": [self.root.winfo_width(), self.root.winfo_height()],
            "canvas": [self.window.canvas.winfo_width(), self.window.canvas.winfo_height()],
            "geometry": self.root.winfo_geometry(),
        }


SCENARIOS = {
    "card": Driver.card,
    "keys": Driver.keys_and_ticks,
    "flip": Driver.flip,
    "close-button": Driver.close_button,
    "app-quit": Driver.app_quit,
    "raise-key": Driver.raise_key,
    "raise-tick": Driver.raise_tick,
    "fallback": Driver.fallback,
    "fallback-none": Driver.fallback,
    "exit-key": Driver.raise_key,
}


def main() -> int:
    # The kernel's default action for SIGALRM kills the process outright. A Python
    # handler would not do: it only runs when the interpreter does, and a hang
    # inside Tk is a hang in native code (measured).
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(DEADLINE_S)
    scenario, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    if scenario == "resize-control":
        return resize_control(outdir)
    driver = Driver(scenario, outdir)
    driver.start(SCENARIOS[scenario](driver))
    status = driver.window.run(driver.on_key, driver.on_tick)
    (outdir / "exit.json").write_text(json.dumps({"run_returned_at": time.time(), "status": status}))
    return status


def resize_control(outdir: Path) -> int:
    """A plain Tk window that *is* resizable, dragged the same way. Not the shell's window."""
    import tkinter as tk

    root = tk.Tk()
    root.title("WI-3 resize control")
    root.geometry("400x570")
    tk.Canvas(root, background="#000000", highlightthickness=0).pack(fill="both", expand=True)
    result = {}

    def act():
        result["before"] = [root.winfo_width(), root.winfo_height()]
        appkit.post_mouse_drag(399, 1, 549, -149)
        root.after(400, done)

    def done():
        result["after"] = [root.winfo_width(), root.winfo_height()]
        (outdir / "result.json").write_text(json.dumps(result))
        root.destroy()

    root.after(SETTLE_MS, act)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
