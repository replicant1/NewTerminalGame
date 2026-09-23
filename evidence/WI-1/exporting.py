"""Shared by the WI-1 harnesses: put a commit's tree in a scratch directory.

Evidence, not a test.  Nothing here is collected by the suite.

A harness never writes into the working tree it is run from.  It exports the
commit under examination (HEAD by default, or the base commit for a control)
into a temporary directory with ``git archive`` and works there.  Only
production files come from the commit; the harness adds its own probe files,
which are test or evidence files, never production code.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: The commit WI-1 was cut from: ``main`` at the merge of PR #120.
BASE = "8bc9496"


def resolve(commit: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", commit],
                          check=True, capture_output=True, text=True).stdout.strip()


def export(commit: str) -> Path:
    """The tree of ``commit`` in a fresh temporary directory."""
    target = Path(tempfile.mkdtemp(prefix="wi1-%s-" % resolve(commit)))
    archive = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", commit],
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    return target


def run(command, cwd, env=None, timeout=300):
    """Run a command, returning (exit status, stdout + stderr)."""
    done = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True,
                          timeout=timeout)
    return done.returncode, done.stdout + done.stderr


def show(title: str, command, status: int, output: str, tail: int = 25) -> None:
    print("---- %s" % title)
    print("$ %s    (exit %d)" % (" ".join(str(c) for c in command), status))
    lines = output.rstrip().splitlines()
    if len(lines) > tail:
        print("    [... %d earlier lines ...]" % (len(lines) - tail))
    for line in lines[-tail:]:
        print("    " + line)
