"""The two entry points, as files on disk.

WIN-3 rests on facts about this repository's *file names* and on the child's
*first write*, neither of which any other test would notice breaking.
"""

import os
import stat
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAY = os.path.join(REPO_ROOT, "play")
CHILD = os.path.join(REPO_ROOT, "Terminal Game")

#: OSC 7 with an empty URL, terminated by BEL: clears Terminal's
#: working-directory title prefix.
CLEAR_DIRECTORY_PREFIX = b"\x1b]7;\x07"


class NamesTest(unittest.TestCase):
    def test_the_child_is_named_exactly_terminal_game(self):
        # ARCHITECTURE.md C2. Terminal's window title *is* this file's name.
        self.assertIn("Terminal Game", os.listdir(REPO_ROOT))

    def test_the_player_runs_play(self):
        self.assertIn("play", os.listdir(REPO_ROOT))


class ExecutableTest(unittest.TestCase):
    def test_both_entry_points_are_executable(self):
        for path in (PLAY, CHILD):
            mode = os.stat(path).st_mode
            self.assertTrue(
                mode & stat.S_IXUSR, "%s is not executable by its owner" % path
            )
            self.assertTrue(
                mode & stat.S_IXOTH, "%s is not executable by others" % path
            )

    def test_both_entry_points_name_the_pinned_interpreter(self):
        # Plan section 2.2: /usr/bin/python3, the one a player who has
        # installed nothing will have.
        for path in (PLAY, CHILD):
            with open(path, "rb") as handle:
                first_line = handle.readline()
            self.assertEqual(b"#!/usr/bin/python3\n", first_line, path)


class ChildBehaviourTest(unittest.TestCase):
    """Run the child directly. Safe: with no tty it returns at once."""

    def run_child(self):
        return subprocess.run(
            [CHILD],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )

    def test_the_childs_first_write_clears_the_directory_prefix(self):
        # WIN-3, step 2 of the recipe. Without it the title reads
        # "rodneybailey - Terminal Game".
        completed = self.run_child()
        self.assertTrue(
            completed.stdout.startswith(CLEAR_DIRECTORY_PREFIX),
            "the child's first write was %r" % completed.stdout[:16],
        )

    def test_the_child_paints_the_game_after_that(self):
        # WI-2's placeholder said "TERMINAL GAME" here; WI-4 replaced it with
        # the game. With no terminal the child paints one frame as plain text
        # and returns, so what comes back is a real picture of a real maze.
        completed = self.run_child()
        self.assertIn(b"arrows, q quits", completed.stdout)

    def test_what_the_child_paints_is_the_size_of_the_window(self):
        # 30 rows of 40 columns (WIN-2, SCRN-1). The status line is the last.
        completed = self.run_child()
        picture = completed.stdout.decode("utf-8").split("\x07", 1)[-1]
        rows = picture.rstrip("\n").split("\n")
        self.assertEqual(30, len(rows))
        for row in rows:
            self.assertEqual(40, len(row), repr(row))
        self.assertIn("q quits", rows[29])

    def test_the_child_exits_cleanly_when_there_is_no_terminal_to_read_from(self):
        # Rule 4 of section 2.6: never leave a process in a window that can
        # never be ended. Without a tty there is no key to press, so the child
        # must return rather than block.
        completed = self.run_child()
        self.assertEqual(0, completed.returncode)
        self.assertEqual(b"", completed.stderr)


if __name__ == "__main__":
    unittest.main()
