"""The AppleScript the launcher would run, as text.

This module is pure: it builds source, it does not execute any. That matters
more than it might look. The dangerous thing about desktop automation is not
whether a Python method was called, it is *which window the script names* — so
the artefact worth asserting on in a test is the script text itself, and here it
is a return value.

Two rules are enforced structurally rather than by discipline:

* **Caution C1 — never act on "the front window".** Exactly one builder here
  looks at anything positional, :func:`reference_window_geometry`, and that one
  runs *before* any window is created. Every builder that touches the game's own
  window takes a ``window_id`` and addresses it as ``window id <n>``, which is
  the terminal application's by-id specifier. There is no builder that can name
  a window by its position or by its title, because none was written.
* **Caution C4 — every call is bounded.** Every builder returns a
  :class:`ScriptCall` carrying a timeout, and the source it carries is wrapped
  in AppleScript's own ``with timeout`` so the Apple Event cannot sit on the
  default sixty-second timeout either.

Assumption A3 is why every appearance property below is set on the *tab* rather
than on a ``settings set``: a settings set is one of the player's saved
profiles, and changing one would outlive the game.
"""

import collections
import math

#: WIN-2 — the window is exactly 40 characters wide and 30 rows deep.
COLUMNS = 40
ROWS = 30

#: WIN-3 — the window is titled "Terminal Game".
TITLE = "Terminal Game"

#: WIN-2 — a fixed-width typeface large enough to read comfortably. Menlo ships
#: with macOS, so nothing has to be installed, and it carries the box-drawing
#: and block glyphs the picture in the specification needs. Whether 14 point is
#: "large enough to read comfortably" is a judgement only a human at the screen
#: can make, and it is collected as a human check rather than asserted here.
FONT_NAME = "Menlo"
FONT_SIZE = 14

#: WIN-2 — on a black background. AppleScript colours are 16-bit per channel.
BLACK = (0, 0, 0)
WHITE = (65535, 65535, 65535)

#: Seconds. Creating a window is the slow one: the terminal has to start a login
#: shell, and on this machine that shell's start-up scripts were measured taking
#: over a second before the command even begins.
CREATE_TIMEOUT = 15.0
QUERY_TIMEOUT = 5.0
SET_TIMEOUT = 10.0


class ScriptCall(collections.namedtuple("ScriptCall", "name source timeout")):
    """One bounded piece of AppleScript, ready to run.

    ``name`` is for diagnostics and for tests that care about ordering;
    ``timeout`` is in seconds and is never optional.
    """

    __slots__ = ()


def applescript_string(text):
    """Quote ``text`` as an AppleScript string literal.

    Control characters are refused rather than escaped. The command string ends
    up being *typed into a shell*, so a newline in it would run a second command
    that nobody wrote, and there is no legitimate reason for one to be there.
    """
    for character in text:
        if ord(character) < 32 or ord(character) == 127:
            raise ValueError(
                "control character %r is not allowed in an AppleScript string"
                % (character,)
            )
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def window_ref(window_id):
    """The by-id specifier for a window: the only way this module names one."""
    return "window id %d" % (int(window_id),)


def _bounded(source, timeout):
    return "with timeout of %d seconds\n%s\nend timeout" % (
        max(1, int(math.ceil(timeout))),
        source,
    )


def _colour(rgb):
    return "{%d, %d, %d}" % rgb


def reference_window_geometry(timeout=QUERY_TIMEOUT):
    """Ask for the geometry of the window the player was last looking at.

    This is the one positional query in the launcher and it must be issued
    **before** anything is created — once the game's own window exists, it is
    the frontmost one, and the launcher would be measuring itself.

    Reading another application's window needs the macOS Accessibility
    permission (architecture assumption A2). A refusal surfaces as an error from
    this call, which the policy layer turns into a documented default position
    rather than an abort.

    Returns ``left,top,right,bottom``.
    """
    source = _bounded(
        'tell application "System Events"\n'
        "\tset frontProcess to first application process whose frontmost is true\n"
        "\tset referenceWindow to first window of frontProcess\n"
        "\tset {refX, refY} to position of referenceWindow\n"
        "\tset {refW, refH} to size of referenceWindow\n"
        "end tell",
        timeout,
    )
    result = (
        "(refX as text) & \",\" & (refY as text) & \",\" & "
        "((refX + refW) as text) & \",\" & ((refY + refH) as text)"
    )
    return ScriptCall("reference_window_geometry", source + "\n" + result, timeout)


def visible_screen_bounds(timeout=QUERY_TIMEOUT):
    """Ask for the bounds of the desktop.

    On a machine with more than one display this is the union of them all, so it
    is an outer bound rather than a guarantee of visibility — measured on the
    development machine as ``-3509,-1440,1611,982``, a rectangle much of which
    is over no display at all. The guarantee in
    :func:`launcher.geometry.target_position` comes from the reference window,
    not from this; this only stops a window being placed somewhere absurd.

    Returns ``left,top,right,bottom``.
    """
    source = _bounded(
        'tell application "Finder"\n'
        "\tset desktopBounds to bounds of window of desktop\n"
        "end tell",
        timeout,
    )
    result = (
        '(item 1 of desktopBounds as text) & "," & (item 2 of desktopBounds as text) '
        '& "," & (item 3 of desktopBounds as text) & "," '
        "& (item 4 of desktopBounds as text)"
    )
    return ScriptCall("visible_screen_bounds", source + "\n" + result, timeout)


def open_window_running(command, timeout=CREATE_TIMEOUT):
    """Open a new terminal window running ``command``, and capture its identity.

    ``do script`` returns the *tab* it started the command in, and the terminal
    offers no "window of this tab" property, so the window is found by asking
    which window contains that exact tab object. That is identity capture, not a
    positional guess: the tab is the one this very call just created, so no
    other window can match, and it is captured in the same script that creates
    it — there is no window between the two at which someone else's window could
    become "the newest".

    ``exec`` matters. Without it the login shell stays alive underneath the game
    and the tab would never go idle, so the launcher could never safely close
    the window; with it the shell is replaced by the game, and the tab reports
    itself idle the moment the game exits.

    Returns the window id as text.
    """
    shell_command = applescript_string("exec " + command)
    source = _bounded(
        'tell application "Terminal"\n'
        "\tset launchedTab to do script %s\n"
        "\tset launchedWindow to first window whose tabs contains launchedTab\n"
        "\tset launchedId to id of launchedWindow\n"
        "end tell" % (shell_command,),
        timeout,
    )
    return ScriptCall("open_window_running", source + "\nlaunchedId as text", timeout)


def configure_window(
    window_id,
    columns=COLUMNS,
    rows=ROWS,
    title=TITLE,
    font_name=FONT_NAME,
    font_size=FONT_SIZE,
    timeout=SET_TIMEOUT,
):
    """Apply WIN-2 and WIN-3 to the captured window and to nothing else.

    The font is set before the grid so that the window's pixel size has settled
    by the time anyone measures it.

    Every ``title displays ...`` switch the scripting dictionary exposes is
    turned off except the custom title. Two further components — the working
    directory the login shell publishes, and the name of the running process —
    are not in the dictionary at all and are controlled by the player's saved
    profile, which assumption A3 forbids changing. See
    ``docs/findings/WI-1-terminal-title-components.md``.
    """
    ref = window_ref(window_id)
    source = _bounded(
        'tell application "Terminal"\n'
        "\tset gameTab to selected tab of %(ref)s\n"
        "\tset font name of gameTab to %(font)s\n"
        "\tset font size of gameTab to %(size)d\n"
        "\tset font antialiasing of gameTab to true\n"
        "\tset background color of gameTab to %(bg)s\n"
        "\tset normal text color of gameTab to %(fg)s\n"
        "\tset cursor color of gameTab to %(bg)s\n"
        "\tset number of columns of gameTab to %(cols)d\n"
        "\tset number of rows of gameTab to %(rows)d\n"
        "\tset custom title of gameTab to %(title)s\n"
        "\tset title displays custom title of gameTab to true\n"
        "\tset title displays device name of gameTab to false\n"
        "\tset title displays shell path of gameTab to false\n"
        "\tset title displays window size of gameTab to false\n"
        "\tset title displays file name of gameTab to false\n"
        "end tell"
        % {
            "ref": ref,
            "font": applescript_string(font_name),
            "size": int(font_size),
            "bg": _colour(BLACK),
            "fg": _colour(WHITE),
            "cols": int(columns),
            "rows": int(rows),
            "title": applescript_string(title),
        },
        timeout,
    )
    return ScriptCall("configure_window", source + '\n"ok"', timeout)


def window_size(window_id, timeout=QUERY_TIMEOUT):
    """Measure the captured window in points. Returns ``width,height``."""
    source = _bounded(
        'tell application "Terminal"\n'
        "\tset {winW, winH} to size of %s\n"
        "end tell" % (window_ref(window_id),),
        timeout,
    )
    return ScriptCall(
        "window_size",
        source + '\n(winW as text) & "," & (winH as text)',
        timeout,
    )


def set_window_position(window_id, point, timeout=SET_TIMEOUT):
    """Move the captured window to ``point``. Returns ``x,y`` as it ended up."""
    source = _bounded(
        'tell application "Terminal"\n'
        "\tset position of %(ref)s to {%(x)d, %(y)d}\n"
        "\tset {movedX, movedY} to position of %(ref)s\n"
        "end tell"
        % {"ref": window_ref(window_id), "x": int(point.x), "y": int(point.y)},
        timeout,
    )
    return ScriptCall(
        "set_window_position",
        source + '\n(movedX as text) & "," & (movedY as text)',
        timeout,
    )


def window_is_busy(window_id, timeout=QUERY_TIMEOUT):
    """Is something still running in the captured window?

    Caution C2 turns on this answer. Closing a window whose process is alive
    raises a modal sheet that only a human can dismiss, and while it is up every
    later automation call hangs behind it. Returns ``true`` or ``false``; a
    window that has gone away answers ``false``, because nothing is running in a
    window that no longer exists.
    """
    ref = window_ref(window_id)
    source = _bounded(
        "try\n"
        '\ttell application "Terminal"\n'
        "\t\tset tabBusy to busy of selected tab of %s\n"
        "\tend tell\n"
        "on error\n"
        "\tset tabBusy to false\n"
        "end try" % (ref,),
        timeout,
    )
    return ScriptCall("window_is_busy", source + "\ntabBusy as text", timeout)


def close_window(window_id, timeout=SET_TIMEOUT):
    """Close the captured window, and only ever that one."""
    source = _bounded(
        'tell application "Terminal"\n'
        "\tclose %s\n"
        "end tell" % (window_ref(window_id),),
        timeout,
    )
    return ScriptCall("close_window", source + '\n"closed"', timeout)


def window_is_visible(window_id, timeout=QUERY_TIMEOUT):
    """Is the captured window still on screen?

    ``visible`` rather than ``exists``: the terminal keeps a window object
    around after a close, and it was measured answering ``visible`` = false
    while still being addressable. A window that cannot be addressed at all is
    reported as ``gone``, which is also not visible.
    """
    ref = window_ref(window_id)
    source = _bounded(
        "try\n"
        '\ttell application "Terminal"\n'
        "\t\tset stillVisible to (visible of %s) as text\n"
        "\tend tell\n"
        "on error\n"
        '\tset stillVisible to "gone"\n'
        "end try" % (ref,),
        timeout,
    )
    return ScriptCall("window_is_visible", source + "\nstillVisible", timeout)
