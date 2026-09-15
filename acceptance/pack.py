# -*- coding: utf-8 -*-
"""The automated exercises: the real launcher, the real game, a real window.

Each exercise returns an :class:`Observation` — what it did, what it saw, and
whether what it saw is what the requirement asks for. Exercises **report**;
they do not assert, because this pack is run by a person who needs to see the
numbers even when they are right.

## How this pack ends the game it starts

M0's ``--hold`` was scaffolding and the real game exits on ``q`` and never on a
timer, so **anything starting a game with nobody at the keyboard has to arrange
its own way out.** This pack writes ``q`` into the tab it created:

    do script "q" in selected tab of window id N

WI-3 measured that reaching the game in 0.14 s. It names the captured window id
like every other call, so it does not depend on which window has focus and
cannot type into whatever the person at the machine is looking at.
``System Events``-style keystroke injection is deliberately not used.

**This is a harness technique and it lives here rather than in ``launcher/``**,
because nothing in the launcher sends input to the game and nothing should.

## The window is reaped by construction

:class:`WindowUnderTest` captures the id at the moment of creation and closes
it in a ``finally``, so a failure anywhere inside cannot leave one behind. It
**never closes a window something is still running in** — if the game will not
end within the bound it leaves the window and names its id, because closing it
raises the modal sheet that blocks every later automation call including the
cleanup itself (caution C2 beats C3, plan §11.3).
"""

from __future__ import annotations

import collections
import time

from launcher import script
from launcher.desktop import Desktop
from launcher.geometry import Point, Size
from launcher.runner import AutomationError, OsascriptRunner

#: How long to wait for the game to appear in the tab's process list before
#: giving up on it. Bounded, like everything else here.
START_TIMEOUT = 15.0
#: How long to wait for it to go after `q`. WI-3 measured 0.14 s.
QUIT_TIMEOUT = 15.0
#: How often to ask.
POLL = 0.1
#: How long any one automation call may take.
CALL_TIMEOUT = 10.0


class Observation(collections.namedtuple(
        "Observation", "name codes ok detail")):
    """What one exercise saw.

    ``ok`` is ``True``, ``False``, or ``None`` for "observed, not judged" —
    the third case matters, because several of these record a number for a
    person to look at rather than a pass or a fail.
    """

    def __str__(self):
        mark = {True: "ok  ", False: "FAIL", None: "note"}[self.ok]
        return "[%s] %-34s %-28s %s" % (
            mark, self.name, ",".join(self.codes), self.detail)


def _bounded(body, timeout=CALL_TIMEOUT):
    """Wrap a script so the Apple event itself cannot wait for ever (C4).

    The pack writes its own rather than importing the launcher's private
    helper: it depends on the launcher's public vocabulary and none of its
    internals.
    """
    return "with timeout of %d seconds\n%s\nend timeout" % (int(timeout), body)


def type_into_tab(window_id, text, timeout=CALL_TIMEOUT):
    """Write `text` into the captured window's tab, as terminal input.

    Names the captured id and nothing else. This is how the pack ends a game
    that nothing else bounds.
    """
    ref = script.window_ref(window_id)
    body = ('tell application "Terminal"\n'
            "\tdo script %s in selected tab of %s\n"
            "end tell" % (script.applescript_string(text), ref))
    return script.ScriptCall("type_into_tab", _bounded(body, timeout) + '\n"sent"',
                             timeout)


def tab_contents(window_id, timeout=CALL_TIMEOUT):
    """Everything the captured window's tab is showing, as text."""
    ref = script.window_ref(window_id)
    body = ("try\n"
            '\ttell application "Terminal"\n'
            "\t\tset shown to contents of selected tab of %s\n"
            "\tend tell\n"
            "on error\n"
            '\tset shown to ""\n'
            "end try" % (ref,))
    return script.ScriptCall("tab_contents", _bounded(body, timeout) + "\nshown as text",
                             timeout)


def window_title(window_id, timeout=CALL_TIMEOUT):
    """What the captured window's title bar says."""
    ref = script.window_ref(window_id)
    body = ("try\n"
            '\ttell application "Terminal"\n'
            "\t\tset shown to name of %s\n"
            "\tend tell\n"
            "on error\n"
            '\tset shown to ""\n'
            "end try" % (ref,))
    return script.ScriptCall("window_title", _bounded(body, timeout) + "\nshown as text",
                             timeout)


def visible_window_count(timeout=CALL_TIMEOUT):
    """How many Terminal windows are visible.

    ``visible is true``, never ``exists``: Terminal keeps a window object
    addressable after a close, and ``id of every window`` was measured
    reporting one the launcher had already closed.
    """
    body = ('tell application "Terminal"\n'
            "\tset n to count of (every window whose visible is true)\n"
            "end tell")
    return script.ScriptCall("visible_window_count",
                             _bounded(body, timeout) + "\nn as text", timeout)


def looks_like_a_frame(shown):
    """Has the game painted a screenful, or is the tab still a shell?

    **Row count only, deliberately.** The obvious stronger test — thirty rows
    that all fit the window — would make the width check below unreachable:
    a picture one column too wide would stop counting as a picture, and the
    SCRN-1 failure it represents could never be reported. A predicate that
    swallows the failure it is meant to surface is worse than a loose one.

    Thirty rows is enough to tell the two apart in practice. The shell state
    this is distinguishing from was measured at **3 rows** — a login line and
    the echo of the command. If a long scrollback ever did reach thirty rows,
    the width check reports it as a failure, which is the right outcome rather
    than a silent pass.
    """
    rows = shown.splitlines() if shown else []
    return len(rows) >= 30


class WindowUnderTest(object):
    """One window, captured at creation and reaped whatever happens.

    Use it as a context manager. On the way out it ends the game with ``q``,
    waits for the process list to empty, and closes by the captured id — and
    if the game will not end it **leaves the window open and records its id**,
    because closing it would raise the sheet.

    "On the way out" includes the way in. A failure between creating the
    window and handing back ``self`` never reaches ``__exit__`` — Python runs
    it only for an ``__enter__`` that returned — so ``__enter__`` reaps for
    itself before re-raising. :meth:`reap` never raises, so the failure that
    caused it is the one the caller sees.
    """

    def __init__(self, runner, command, clock=time.time, sleeper=time.sleep):
        self.runner = runner
        self.desktop = Desktop(runner)
        self.command = command
        self.clock = clock
        self.sleeper = sleeper
        self.window_id = None
        self.abandoned = None
        self.events = []

    # -- the life of the window -------------------------------------------

    def __enter__(self):
        self.opened_at = self.clock()
        self.window_id = self.desktop.open_window_running(self.command)
        self._note("window %d created" % self.window_id)
        try:
            self.desktop.configure(self.window_id)
        except BaseException:
            # `__exit__` cannot cover this gap: Python calls it only for an
            # `__enter__` that RETURNED. So everything between the window
            # existing and `self` being handed back has to reap for itself, or
            # a refused permission here leaves a window on the player's
            # desktop that nothing in this pack will ever close.
            # `WindowLauncher.open` has always done this; this did not.
            self.reap()
            raise
        self._note("configured")
        return self

    def __exit__(self, kind, value, traceback):
        self.reap()
        return False        # never swallow the failure it was cleaning up after

    def _note(self, what):
        self.events.append((self.clock() - self.opened_at, what))

    # -- what it can do ----------------------------------------------------

    def wait_for_the_game(self, timeout=START_TIMEOUT):
        """Wait until something is actually running in the tab.

        Not the same as "the window exists". A command that fails at once —
        a wrong directory, a missing module — leaves an empty process list
        that looks exactly like a finished game, so the pack waits for the
        game to *appear* before it believes anything about it ending.
        """
        deadline = self.clock() + timeout
        while self.clock() < deadline:
            if self.desktop.processes(self.window_id):
                self._note("game running")
                return True
            self.sleeper(POLL)
        self._note("game never started")
        return False

    def contents(self):
        return self.runner.run(tab_contents(self.window_id))

    def wait_for_the_picture(self, timeout=START_TIMEOUT):
        """Wait until the tab is showing a frame rather than a shell.

        **"Something is running" is not "the game has drawn."** The command
        the launcher sends spends its first moments in a shell loop waiting
        for the window to reach 40 x 30, so the process list goes non-empty
        well before anything is on the screen — measured at +0.40 s against a
        picture that had not yet appeared. A capture taken then reads back the
        shell's echo of the command, which is 389 columns wide and looks
        exactly like a catastrophic SCRN-1 failure.

        The signal used here is the requirement itself: SCRN-1 says the
        picture is 30 rows of at most 40 columns. So the pack waits until the
        tab shows that, and if it never does it says so rather than judging
        whatever the shell happened to leave behind.
        """
        deadline = self.clock() + timeout
        last = ""
        while self.clock() < deadline:
            last = self.contents()
            if looks_like_a_frame(last):
                self._note("picture drawn")
                return last
            self.sleeper(POLL)
        self._note("no picture ever appeared")
        return last

    def title(self):
        return self.runner.run(window_title(self.window_id))

    def size(self):
        return self.desktop.window_size(self.window_id)

    def send_quit(self):
        """End the game the only way the game itself allows."""
        self.runner.run(type_into_tab(self.window_id, "q"))
        self._note("q sent")

    def wait_until_gone(self, timeout=QUIT_TIMEOUT):
        deadline = self.clock() + timeout
        while self.clock() < deadline:
            if not self.desktop.processes(self.window_id):
                self._note("game gone")
                return True
            self.sleeper(POLL)
        self._note("game still running")
        return False

    # -- and how it always ends -------------------------------------------

    def reap(self):
        """Close the captured window — but never one with a game still in it."""
        if self.window_id is None:
            return
        window_id, self.window_id = self.window_id, None
        try:
            if self.desktop.processes(window_id):
                self.send_quit_to(window_id)
                if not self._wait_empty(window_id, QUIT_TIMEOUT):
                    self.abandoned = window_id
                    self._note("window %d LEFT OPEN: something is still "
                               "running in it, and closing it would raise a "
                               "modal sheet that blocks every later call"
                               % window_id)
                    return
            self.desktop.close(window_id)
            gone = not self.desktop.is_visible(window_id)
            self._note("window %d closed, visible=%s" % (window_id, not gone))
        except BaseException as error:
            # Never raises, like `WindowLauncher.reap` and for the same reason:
            # this runs on the failure path, where an exception of its own
            # would bury the failure it was called to clean up after. An
            # `AutomationError` is the expected way in; anything else still
            # must not escape.
            self.abandoned = window_id
            self._note("window %d could not be reaped: %s" % (window_id, error))

    def send_quit_to(self, window_id):
        self.runner.run(type_into_tab(window_id, "q"))

    def _wait_empty(self, window_id, timeout):
        deadline = self.clock() + timeout
        while self.clock() < deadline:
            if not self.desktop.processes(window_id):
                return True
            self.sleeper(POLL)
        return False


# -- the exercises ---------------------------------------------------------


def census(runner):
    return int(runner.run(visible_window_count()).strip())


def exercise_a_whole_session(runner, command, clock=time.time,
                             sleeper=time.sleep):
    """Open a window, let the game run, end it with `q`, take the window back.

    Establishes the join end to end, and the `q` path as terminal input —
    which is END-6 and WIN-5 as far as a machine can take them. A person
    pressing a real key is `A_REAL_KEYBOARD` in the register.
    """
    observations = []
    before = census(runner)
    window = WindowUnderTest(runner, command, clock=clock, sleeper=sleeper)
    started = gone = False
    shown = ""
    seen = {}
    with window:
        started = window.wait_for_the_game()
        if started:
            # Everything about the window has to be read WHILE IT IS OPEN.
            # Reading it afterwards would ask the desktop about a window that
            # is gone and get an error that looks like a failed requirement.
            shown = window.wait_for_the_picture()
            seen["size"] = _try(window.size)
            seen["title"] = _try(window.title)
            window.send_quit()
            gone = window.wait_until_gone()

    observations.append(Observation(
        "the game starts in its window", ("GAME-1", "WIN-1"), bool(started),
        "process list became non-empty" if started
        else "nothing ever ran in the tab — is the command right?"))
    observations.append(Observation(
        "`q` ends the game", ("END-6", "CTRL-4"), bool(gone),
        "gone after q" if gone else "still running after q"))
    after = census(runner)
    observations.append(Observation(
        "nothing is left on the desktop", ("WIN-5",), after == before,
        "visible windows %d before, %d after%s" % (
            before, after,
            "" if window.abandoned is None
            else "; window %d LEFT OPEN on purpose" % window.abandoned)))
    return observations, shown, seen, window


def _try(question):
    """Ask the desktop something, and keep the error instead of raising it.

    An exercise that raised here would lose every observation taken before it,
    including the ones that say whether the window was cleaned up.
    """
    try:
        return question()
    except AutomationError as error:
        return error


def exercise_the_picture(shown):
    """What the tab was showing, judged only on what text can show.

    **Deliberately not compared against a fixed picture**, and the reason
    outlasts the walking skeleton this was first written against. The pack runs
    `game_command()` with no seed, so MAZE-4 gives it a different maze every
    time and there is no fixed frame to pin. Seeding it would buy one at the
    price of no longer exercising the thing this pack exists for — the real
    command, exactly as a player gets it.

    So this judges the shape instead, which is what SCRN-1 actually states and
    what holds for every maze the generator can produce: thirty rows, none of
    them wider than forty columns. What the picture *contains* is reported as a
    number for a person to compare against the specification, not judged here.
    """
    rows = shown.splitlines() if shown else []
    drawn = looks_like_a_frame(shown)
    observations = [Observation(
        "the game drew a picture at all", ("SCRN-1", "SCRN-2"), drawn,
        "%d rows captured%s" % (
            len(rows),
            "" if drawn else " — this is not a frame; the tab was still "
                             "showing a shell, or the game never drew"))]
    if not drawn:
        return observations
    frame = rows[-30:]
    widths = [len(row) for row in frame]
    observations.append(Observation(
        "the picture fits the window", ("SCRN-1", "MAZE-1"),
        max(widths) <= 40, "30 rows, widest %d columns" % max(widths)))
    observations.append(Observation(
        "what the picture contains", ("SCRN-1",), None,
        "30 rows of %d..%d columns — a person compares this with the "
        "specification's picture; no machine here can check the colours"
        % (min(widths), max(widths))))
    return observations


def exercise_the_window(seen):
    """Size and title — the parts of WIN-2 and WIN-3 that are numbers or text.

    Takes what was read while the window was open, not the window: by the time
    this runs the window is gone, which is as it should be.
    """
    observations = []
    size = seen.get("size")
    if isinstance(size, Size):
        observations.append(Observation(
            "the window is the size asked for", ("WIN-2",), None,
            "%d x %d points — measured 357 x 558 for 40 x 30 at Menlo 14; "
            "whether it is legible is a human check"
            % (size.width, size.height)))
    else:
        observations.append(Observation(
            "the window is the size asked for", ("WIN-2",), False,
            "not read: %s" % (size,)))
    title = seen.get("title")
    if isinstance(title, str):
        observations.append(Observation(
            "the title bar", ("WIN-3",), None,
            "reads %r — WIN-3 asks for 'Terminal Game' and this bar also "
            "carries components governed by the player's saved profile, which "
            "A3 forbids changing. NOT VERIFIED." % (title,)))
    else:
        observations.append(Observation(
            "the title bar", ("WIN-3",), False, "not read: %s" % (title,)))
    return observations


def run(command, runner=None, clock=time.time, sleeper=time.sleep):
    """The whole pack. Returns every observation, in order, and the window."""
    if runner is None:
        runner = OsascriptRunner()
    observations, shown, seen, window = exercise_a_whole_session(
        runner, command, clock=clock, sleeper=sleeper)
    observations.extend(exercise_the_picture(shown))
    observations.extend(exercise_the_window(seen))
    return observations, shown, window
