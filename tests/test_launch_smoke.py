"""The one live smoke: a real Terminal window, opened and closed by id.

**Read plan section 2.6 before touching this file.** It runs on a real
person's desktop. Everything it does is done to a window it created and whose
id it captured at the moment of creation; it never addresses any other window,
and it closes what it opened on the failure path as well as the success path.

It is skipped without a controlling tty -- no agent in this project has one --
because a test that opens windows should only ever run when a person is there
to see it. That means the whole of it is skipped in CI and in every agent
session; it exists for the human check, and for whoever runs the suite from a
real terminal.

The child it runs exits by itself in well under a second. Nothing here ever
launches something that blocks for ever: there would then be no way to end it,
and closing its window would raise a modal sheet that only a human can dismiss
and that blocks every later AppleScript call in the system.
"""

import os
import subprocess
import tempfile
import unittest

from termgame import window


def has_controlling_tty():
    try:
        os.ttyname(0)
        return True
    except OSError:
        return False


def terminal_is_running():
    try:
        answer = subprocess.run(
            [
                "/usr/bin/osascript",
                "-e",
                'tell application "System Events" to (name of processes) contains "Terminal"',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=20,
        )
        return answer.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


@unittest.skipUnless(
    has_controlling_tty(), "no controlling tty: nobody is watching this screen"
)
@unittest.skipUnless(terminal_is_running(), "Terminal.app is not running")
class LaunchSmokeTest(unittest.TestCase):
    """WIN-1 and WIN-5 against the real Terminal."""

    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="termgame-smoke-")
        self.child = os.path.join(self.directory, "quick-exit")
        with open(self.child, "w") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        os.chmod(self.child, 0o755)
        self.before = window.visible_window_ids()
        self.window_id = None

    def tearDown(self):
        # Unconditional: a failed assertion must not leave a window behind.
        if self.window_id is not None:
            try:
                window.close_when_idle(self.window_id, timeout=20)
            except window.WindowError:
                pass
        for path in (self.child,):
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(self.directory)

    def open_window(self):
        self.window_id = window.open_game_window(
            "exec " + window.shell_quote(self.child)
        )
        return self.window_id

    def test_a_window_is_created_and_closed_by_the_id_that_was_captured(self):
        window_id = self.open_window()
        self.assertNotIn(
            window_id, self.before, "the new window reused an existing id"
        )
        self.assertIn(window_id, window.visible_window_ids())

        self.assertTrue(
            window.wait_until_idle(window_id, timeout=20),
            "the child did not exit within 20s; window %d left open" % window_id,
        )
        self.assertTrue(window.close_window(window_id))
        self.window_id = None

        self.assertFalse(window.window_is_visible(window_id))
        self.assertEqual(
            sorted(self.before),
            sorted(window.visible_window_ids()),
            "Terminal's visible windows are not what they were before",
        )

    def test_the_window_can_be_sized_and_read_back(self):
        # WIN-2, as far as an agent can take it: the settings are applied to
        # the tab of the window we created. Whether 18pt is comfortable is
        # human check H4.
        window_id = self.open_window()
        window.configure_window(window_id)
        answer = window.run_osascript(
            'tell application "Terminal"\n'
            "\tset t to tab 1 of (first window whose id is %d)\n"
            '\treturn ((number of columns of t) as text) & " " & '
            '((number of rows of t) as text) & " " & (font name of t) & " " & '
            "((font size of t) as text)\n"
            "end tell" % window_id
        )
        self.assertEqual("40 30 Menlo-Regular 18", answer)


if __name__ == "__main__":
    unittest.main()
