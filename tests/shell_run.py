"""Start the shell driver the way a person starts a program: from a terminal. Test support only.

The driver runs with a pseudo-terminal as its stdin, stdout and stderr, so
"writes nothing to the terminal it was started from" (WI-3/C1) is read off
the terminal itself. A hard timeout kills it if it hangs; a killed process
takes its window with it, and no terminal window is involved to raise a
"terminate running processes?" sheet.
"""

import json
import os
import re
import pty
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DRIVER = HERE / "shell_driver.py"
TIMEOUT_S = 60

#: Passed on the driver's own command line (AppKit's argument domain: this one
#: process, nothing persisted). After any Python process crashes on this Mac,
#: every later Python+Tk start shows a modal "reopen windows?" alert and waits
#: for a person to answer it (measured 2026-09-23: TkpInit blocked in
#: NSPersistentUIRestorer promptToIgnorePersistentStateWithCrashHistory). The
#: game has no windows to restore, and a test must never wait on a dialog.
HARNESS_ARGS = ["-ApplePersistence", "NO"]

#: AppKit announces the argument on stderr, once, in exactly this form. It is
#: the harness talking, not the program, so it is the one line removed before
#: the terminal is inspected (see :func:`program_output`).
HARNESS_ECHO = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+ Python\[\d+:\d+\] ApplePersistence=NO$")


@dataclass
class Run:
    scenario: str
    outdir: Path
    status: int | None = None          # None: it had to be killed
    terminal: str = ""                 # everything written to the terminal
    exited_at: float = 0.0             # time.time() when the parent saw it exit
    pid: int = 0
    result: dict = field(default_factory=dict)
    stragglers: bool = False           # something in its process group outlived the driver
    exit_record: dict = field(default_factory=dict)

    def load(self) -> None:
        for name, attr in (("result.json", "result"), ("exit.json", "exit_record")):
            path = self.outdir / name
            if path.exists():
                setattr(self, attr, json.loads(path.read_text()))


def run_driver(scenario: str, outdir: Path, *, on_ready=None, python: str = sys.executable, driver: Path = DRIVER) -> Run:
    """Run ``scenario`` to completion under a pseudo-terminal and return what happened.

    ``on_ready(run)``, if given, is called once ``result.json`` first appears
    (the driver writes it when it is ready to be acted on from outside).
    """
    outdir.mkdir(parents=True, exist_ok=True)
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [python, str(driver), scenario, str(outdir), *HARNESS_ARGS],
        stdin=slave, stdout=slave, stderr=slave, cwd=REPO, close_fds=True,
        process_group=0,   # its own group, so its screencapture and swift children go with it
    )
    os.close(slave)
    chunks: list[bytes] = []

    def pump():
        while True:
            try:
                data = os.read(master, 4096)
            except OSError:
                return
            if not data:
                return
            chunks.append(data)

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    run = Run(scenario, outdir, pid=process.pid)
    ready_called = False
    deadline = time.monotonic() + TIMEOUT_S
    while process.poll() is None and time.monotonic() < deadline:
        if on_ready and not ready_called and (outdir / "result.json").exists():
            ready_called = True
            on_ready(run)
        time.sleep(0.005)
    if process.poll() is None:
        run.status = None
    else:
        run.status = process.returncode
    # Whatever happened, nothing the driver started outlives the run: kill and reap the
    # whole process group (the driver, and any screencapture or swift it had running).
    run.stragglers = _reap_group(process)
    run.exited_at = time.time()
    reader.join(timeout=2)
    os.close(master)
    run.terminal = b"".join(chunks).decode("utf-8", "replace")
    run.load()
    return run


def _reap_group(process: subprocess.Popen) -> bool:
    """SIGKILL whatever is left of the driver's process group and reap the driver.

    Returns True if anything was left to kill. After a driver that exited by
    itself, that means one of its children outlived it.
    """
    try:
        os.killpg(process.pid, signal.SIGKILL)
        anything = True
    except ProcessLookupError:
        anything = False
    process.wait()
    return anything


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def program_output(terminal: str) -> str:
    """What the program wrote to its terminal, less the one line AppKit prints for HARNESS_ARGS."""
    lines = terminal.replace("\r\n", "\n").split("\n")
    kept, removed = [], 0
    for line in lines:
        if removed == 0 and HARNESS_ECHO.match(line):
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept)
