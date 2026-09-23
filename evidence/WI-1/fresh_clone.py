"""WI-1/C1: a fresh clone, set up by following the README, runs the suite.

Evidence, not a test.  Usage, from the repository root:

    .venv/bin/python evidence/WI-1/fresh_clone.py            # HEAD
    .venv/bin/python evidence/WI-1/fresh_clone.py --commit X

It clones the repository into a temporary directory and checks out the commit,
so nothing from this working tree (no ``.venv``, no untracked file) comes
along.  It then reads the README's **"## Setting up"** section, takes the first
``sh`` code block in it, and runs each of its lines in the clone, as written.
It does not know the setup commands itself: if the README's steps are wrong or
missing, this fails.

Then it runs the default suite command, ``.venv/bin/python -m pytest -q``,
exactly, and once more with ``-rA`` added so each test's outcome is printed by
name, and reports what happened to the tests that were in the repository
before WI-1: ``tests/test_code_reviewer_token.py`` and
``tests/test_monitor_run_clock.py``.  (One of the latter skips by design when a
run-7 log is not in the checkout; that skip is on the base too.)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exporting  # noqa: E402

INFRASTRUCTURE = ("tests/test_code_reviewer_token.py", "tests/test_monitor_run_clock.py")


def setup_block(readme: str):
    """The lines of the first ```sh block under '## Setting up'."""
    section = re.search(r"^## Setting up\n(.*?)(?=^## |\Z)", readme, re.S | re.M)
    if not section:
        return None
    block = re.search(r"^```sh\n(.*?)^```", section.group(1), re.S | re.M)
    if not block:
        return None
    return [line for line in block.group(1).splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="HEAD")
    commit = parser.parse_args().commit
    sha = exporting.resolve(commit)
    common = subprocess.run(["git", "-C", str(exporting.REPO), "rev-parse",
                             "--path-format=absolute", "--git-common-dir"],
                            check=True, capture_output=True, text=True).stdout.strip()
    clone = Path(tempfile.mkdtemp(prefix="wi1-clone-")) / "NewTerminalGame"
    for command in (["git", "clone", "--quiet", "--no-checkout", common, str(clone)],
                    ["git", "-C", str(clone), "checkout", "--quiet", sha]):
        status, output = exporting.run(command, exporting.REPO)
        if status != 0:
            exporting.show("cloning", command, status, output)
            print("WI-1/C1 COULD NOT RUN: the clone failed")
            return 2
    print("fresh clone of %s at %s" % (sha, clone))

    readme = clone / "README.md"
    steps = setup_block(readme.read_text()) if readme.is_file() else None
    if not steps:
        print("WI-1/C1 DOES NOT HOLD: README.md has no '## Setting up' section "
              "with an sh block of steps")
        return 1
    for step in steps:
        status, output = exporting.run(["/bin/sh", "-c", step], clone, timeout=600)
        exporting.show("README setup step", [step], status, output, tail=8)
        if status != 0:
            print("WI-1/C1 DOES NOT HOLD: the README step %r failed" % step)
            return 1

    suite = [".venv/bin/python", "-m", "pytest", "-q"]
    status, output = exporting.run(suite, clone)
    exporting.show("the default suite command, exactly", suite, status, output, tail=4)
    status_a, output_a = exporting.run(suite + ["-rA"], clone)

    counts = {}
    for path in INFRASTRUCTURE:
        outcomes = re.findall(r"^(PASSED|FAILED|ERROR) %s::" % re.escape(path), output_a, re.M)
        skips = re.findall(r"^SKIPPED \[\d+\] %s:" % re.escape(path), output_a, re.M)
        counts[path] = (outcomes.count("PASSED"), len(outcomes) - outcomes.count("PASSED"),
                        len(skips))
        print("    %s: %d passed, %d failed or errored, %d skipped"
              % ((path,) + counts[path]))
    infra_ok = all(passed > 0 and bad == 0 for passed, bad, _ in counts.values())
    summary = output.strip().splitlines()[-1] if output.strip() else ""
    holds = status == 0 and status_a == 0 and infra_ok
    print()
    print("WI-1/C1 %s: README setup ran %d step(s); default suite exit %d, '%s'; "
          "existing infrastructure tests all passed: %s"
          % ("HOLDS" if holds else "DOES NOT HOLD", len(steps), status, summary,
             "yes" if infra_ok else "no"))
    return 0 if holds else 1


if __name__ == "__main__":
    sys.exit(main())
