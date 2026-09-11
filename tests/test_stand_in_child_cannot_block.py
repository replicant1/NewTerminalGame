"""The one property of the smoke's stand-in child that is a safety rule.

Kept when the rest of the harness's self-referential tests were removed. This
is not a test about the test harness: §2.6 rule 4 says never launch, in a
window you opened, anything you cannot end. A stand-in child that blocks for
ever is a window that cannot be closed without Terminal's modal confirmation
sheet -- which only a human can dismiss, and which blocks every subsequent
AppleScript call in the system until they do.

The rest of ``launch-smoke``'s behaviour is exercised by running it: it is
stage 2 of ``./verify``.
"""

import importlib.machinery
import importlib.util
import os
import subprocess
import tempfile
import unittest

from termgame import window

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE_PATH = os.path.join(REPO_ROOT, "launch-smoke")


def load_smoke():
    """Import ``launch-smoke``, which has no ``.py`` extension by design."""
    loader = importlib.machinery.SourceFileLoader("launch_smoke", SMOKE_PATH)
    spec = importlib.util.spec_from_loader("launch_smoke", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


smoke = load_smoke()


class TheStandInChildCannotBlock(unittest.TestCase):
    """§2.6 rule 4, which is about the user's machine and not about testing."""

    def test_it_ends_by_itself_and_never_blocks_for_ever(self):
        # If this ever gains an input(), a read, a cat or an unbounded wait,
        # the smoke gains a window it cannot close.
        source = smoke.child_source(1.0)
        for forbidden in ("input(", "sys.stdin", "os.read", "while True"):
            self.assertNotIn(forbidden, source, "the stand-in child can block")
        self.assertIn("time.sleep(1.0)", source)

    def test_the_child_it_writes_really_does_exit(self):
        # Run it. Not in a window -- just as a process, with no tty.
        directory = tempfile.mkdtemp(prefix="termgame-smoke-test-")
        path = os.path.join(directory, window.CHILD_NAME)
        try:
            with open(path, "w") as handle:
                handle.write(smoke.child_source(0.1))
            os.chmod(path, 0o755)
            done = subprocess.run(
                [path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertTrue(done.stdout.startswith(b"\x1b]7;\x07"))
        finally:
            if os.path.exists(path):
                os.remove(path)
            os.rmdir(directory)


if __name__ == "__main__":
    unittest.main()
