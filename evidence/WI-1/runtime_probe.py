"""WI-1/C2 against real interpreters, on a commit's real tree.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-1/runtime_probe.py                   # HEAD
    .venv/bin/python evidence/WI-1/runtime_probe.py --commit 8bc9496  # control: the base

It exports the commit into a scratch directory and runs the default suite
command there twice, under interpreters that are not the pin:

1. **The wrong interpreter.**  A venv built from ``/usr/bin/python3`` (Apple's
   CPython 3.9 with Tk 8.5), with pytest installed into it: exactly what
   ``verifier.md``'s setup command builds (IMPLEMENTATION_PLAN.md section 1.10,
   X1).  The venv is built afresh in a temporary directory; pip needs the
   network or its cache.
2. **The pinned interpreter without a working Tk.**  This repository's
   ``.venv`` (CPython 3.14 at the pinned path), with a ``_tkinter.py`` placed
   first on ``PYTHONPATH`` that raises ``ImportError``, which is how Homebrew's
   3.14 shipped until September 2026.  No production file is touched.

For each it prints the command's own output and a verdict: HOLDS when the suite
stopped without running tests and its message names the interpreter and Tk it
found and the ones it wants; DOES NOT HOLD otherwise.  On the base both runs
simply pass, because nothing checks.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exporting  # noqa: E402

WANTED = "wanted: CPython 3.14 at /opt/homebrew/bin/python3.14, Tk 9"


def verdict(label, status, output, found_marks):
    ran_tests = any(word in output for word in (" passed", " failed"))
    wanted = WANTED in output
    found = all(mark in output for mark in found_marks)
    holds = status != 0 and not ran_tests and wanted and found
    print("WI-1/C2 %s (%s): exit %d; tests ran: %s; names what it found (%s): %s; "
          "names what it wants: %s"
          % ("HOLDS" if holds else "DOES NOT HOLD", label, status,
             "yes" if ran_tests else "no", " + ".join(found_marks),
             "yes" if found else "no", "yes" if wanted else "no"))
    return holds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="HEAD")
    commit = parser.parse_args().commit
    tree = exporting.export(commit)
    print("commit %s exported to %s" % (exporting.resolve(commit), tree))
    scratch = Path(tempfile.mkdtemp(prefix="wi1-runtime-"))

    # 1. /usr/bin/python3 (3.9, Tk 8.5), set up the way verifier.md does it.
    venv39 = scratch / "venv39"
    build = [["/usr/bin/python3", "-m", "venv", str(venv39)],
             [str(venv39 / "bin" / "python"), "-m", "pip", "install", "-q",
              "--disable-pip-version-check", "pytest"]]
    for command in build:
        status, output = exporting.run(command, tree)
        if status != 0:
            exporting.show("building the 3.9 venv", command, status, output)
            print("WI-1/C2 COULD NOT RUN: the 3.9 venv could not be built")
            return 2
    wrong = [str(venv39 / "bin" / "python"), "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    status1, out1 = exporting.run(wrong, tree)
    exporting.show("default command under /usr/bin/python3's venv", wrong, status1, out1)

    # 2. The pinned interpreter with _tkinter hidden.
    hide = scratch / "no_tk"
    hide.mkdir()
    (hide / "_tkinter.py").write_text(
        "raise ImportError('simulated: this interpreter has no _tkinter')\n")
    env = dict(os.environ, PYTHONPATH=str(hide))
    pinned = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    status2, out2 = exporting.run(pinned, tree, env=env)
    exporting.show("default command under the pinned venv, _tkinter hidden", pinned, status2, out2)

    print()
    first = verdict("wrong interpreter", status1, out1,
                    ["found:  CPython 3.9", "Tk 8.5"])
    second = verdict("pinned interpreter, no Tk", status2, out2,
                     ["found:  CPython 3.14", "no working Tk (ImportError: simulated"])
    return 0 if (first and second) else 1


if __name__ == "__main__":
    sys.exit(main())
