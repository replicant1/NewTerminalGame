"""The AppleScript adapter and the supervisor (WIN-1..5).

IMPURE. This is the only module in the project that shells out to
``osascript``, and it imports nothing from the pure core.

Read ARCHITECTURE.md section 6.3 and IMPLEMENTATION_PLAN.md section 2.6 before
changing anything here. The player's own shells, their editor and any agent
session are windows in the same application, so:

* the window ``id`` is captured at the moment the window is created, and every
  later statement addresses ``first window whose id is <that id>``;
* nothing here ever says ``front window`` except the one read-only query that
  looks for the reference position *before* a window of ours exists;
* nothing is ever closed by title, by index, or by enumerate-and-guess;
* a tab whose ``busy`` is true is never closed -- that raises a modal sheet
  which only a human can dismiss and which blocks every later AppleScript call;
* the failure path runs the same wait-then-close-by-id as the success path.

The AppleScript itself cannot be unit tested, so the decisions are pulled out
of it into pure functions -- ``choose_reference``, ``offset_position`` and the
``script_*`` composers -- and those are tested directly.
"""

import ctypes
import ctypes.util
import os
import subprocess
import sys
import time

# --------------------------------------------------------------------------
# Constants. Every number here was measured; see ARCHITECTURE.md section 7.
# --------------------------------------------------------------------------

#: The child executable's file name. LOAD-BEARING: Terminal composes the window
#: title from the active process name, so this name *is* the title (WIN-3).
#: Renaming it, or invoking it as ``python3 "Terminal Game"``, or passing it an
#: argument, all break WIN-3. (ARCHITECTURE.md C2.)
CHILD_NAME = "Terminal Game"

COLUMNS = 40  # WIN-2
ROWS = 30  # WIN-2
FONT_NAME = "Menlo-Regular"  # WIN-2
FONT_SIZE = 18  # WIN-2, human check H4
BACKGROUND_COLOR = (0, 0, 0)  # WIN-2, black

#: Measured: a 40x30 window in Menlo 18 is 477 x 707 px.
GAME_WINDOW_PIXELS = (477, 707)

#: "a little below and to the right" (WIN-4).
OFFSET = (30, 30)

#: Used when Terminal has no window at all to take a reference from.
FALLBACK_POSITION = (60, 60)

#: Used when the main display's size cannot be read.
FALLBACK_SCREEN = (1440, 900)

#: The menu bar (and, on this machine, the notch) occupy the top of the screen;
#: a window title bar placed above this is not reachable with the mouse.
MENU_BAR_HEIGHT = 38

#: How long the supervisor waits, on the failure path, for the child to exit
#: before giving up and leaving the window open rather than forcing it.
CLOSE_GRACE_SECONDS = 10.0

OSASCRIPT = "/usr/bin/osascript"


class WindowError(RuntimeError):
    """An AppleScript call failed, or returned something unusable."""


class WindowSettings(object):
    """The settings applied to the game window's tab (WIN-2, WIN-3)."""

    def __init__(
        self,
        columns=COLUMNS,
        rows=ROWS,
        font_name=FONT_NAME,
        font_size=FONT_SIZE,
        background_color=BACKGROUND_COLOR,
    ):
        self.columns = columns
        self.rows = rows
        self.font_name = font_name
        self.font_size = font_size
        self.background_color = tuple(background_color)

    def __repr__(self):  # pragma: no cover - diagnostic only
        return "WindowSettings(columns=%r, rows=%r, font_name=%r, font_size=%r)" % (
            self.columns,
            self.rows,
            self.font_name,
            self.font_size,
        )


DEFAULT_SETTINGS = WindowSettings()


# --------------------------------------------------------------------------
# Pure decisions. No I/O below this line until the osascript section.
# --------------------------------------------------------------------------


def choose_reference(tty_position, front_position, fallback=FALLBACK_POSITION):
    """Pick the position the game window is offset from (WIN-4).

    A pure function of what the two queries returned:

    * the Terminal window whose tab's ``tty`` is the supervisor's own -- that
      is precisely the window the player typed ``./play`` into;
    * otherwise Terminal's front window;
    * otherwise a fixed position.

    Returns ``(position, source)`` where source is ``"tty"``, ``"front"`` or
    ``"fallback"``.
    """
    if tty_position is not None:
        return (tuple(tty_position), "tty")
    if front_position is not None:
        return (tuple(front_position), "front")
    return (tuple(fallback), "fallback")


def offset_position(
    reference,
    screen_size=FALLBACK_SCREEN,
    window_size=GAME_WINDOW_PIXELS,
    offset=OFFSET,
    min_y=MENU_BAR_HEIGHT,
):
    """Where the game window goes: below and right of *reference* (WIN-4).

    Pure. The offset is clamped so the whole window stays on the screen -- a
    reference near the bottom-right corner would otherwise put most of the
    game off the edge, which is exactly what WIN-4 exists to prevent.
    """
    ref_x, ref_y = reference
    win_w, win_h = window_size
    screen_w, screen_h = screen_size
    x = int(ref_x) + offset[0]
    y = int(ref_y) + offset[1]

    max_x = max(0, int(screen_w) - int(win_w))
    max_y = max(min_y, int(screen_h) - int(win_h))

    x = min(max(0, x), max_x)
    y = min(max(min_y, y), max_y)
    return (x, y)


def child_command(repo_root, child_name=CHILD_NAME):
    """The shell command Terminal runs in the new window.

    ``exec`` so the child replaces the shell and the tab stops being busy the
    instant the game exits. No arguments: an argument would change the active
    process name and break WIN-3.
    """
    path = os.path.join(repo_root, child_name)
    return "exec " + _shell_single_quote(path)


def _shell_single_quote(text):
    return "'" + text.replace("'", "'\\''") + "'"


def _as_applescript_string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _window(window_id):
    """The one way this module ever names a window. Never a title, never an
    index, never ``front window``."""
    return "(first window whose id is %d)" % int(window_id)


def script_open_window(command):
    """Create a window running *command* and return its id (WIN-1).

    The id comes from the tab ``do script`` just returned -- the window is
    identified by having watched it appear, not by inspecting titles
    afterwards.
    """
    return (
        'tell application "Terminal"\n'
        "\tactivate\n"
        "\tset newTab to do script %s\n"
        "\tset newWindow to first window whose tabs contains newTab\n"
        "\treturn id of newWindow as text\n"
        "end tell" % _as_applescript_string(command)
    )


def script_reference_position(tty):
    """Read the position of the Terminal window whose tab 1 has this tty.

    Read-only. Returns ``"none"`` when there is no such window.
    """
    return (
        'tell application "Terminal"\n'
        "\trepeat with w in windows\n"
        "\t\ttry\n"
        "\t\t\tif tty of tab 1 of w is %s then\n"
        "\t\t\t\tset p to position of w\n"
        '\t\t\t\treturn ((item 1 of p) as text) & " " & ((item 2 of p) as text)\n'
        "\t\t\tend if\n"
        "\t\tend try\n"
        "\tend repeat\n"
        '\treturn "none"\n'
        "end tell" % _as_applescript_string(tty)
    )


def script_front_position():
    """Read the position of Terminal's frontmost window.

    This is the ONLY script in the project that mentions the front window, it
    is a read, and it runs before the game window exists. Nothing is ever
    written to, or closed by, the front window.
    """
    return (
        'tell application "Terminal"\n'
        '\tif (count of windows) is 0 then return "none"\n'
        "\tset p to position of front window\n"
        '\treturn ((item 1 of p) as text) & " " & ((item 2 of p) as text)\n'
        "end tell"
    )


def script_configure_window(window_id, settings=DEFAULT_SETTINGS):
    """40 x 30, Menlo 18, black, every scriptable title component off.

    ``title displays custom title`` is set false deliberately: setting it true
    appends a second *Terminal Game* and the title reads
    ``Terminal Game - Terminal Game`` (measured).
    """
    red, green, blue = settings.background_color
    return (
        'tell application "Terminal"\n'
        "\tset gameWindow to %s\n"
        "\tset gameTab to tab 1 of gameWindow\n"
        "\tset number of columns of gameTab to %d\n"
        "\tset number of rows of gameTab to %d\n"
        "\tset font name of gameTab to %s\n"
        "\tset font size of gameTab to %d\n"
        "\tset background color of gameTab to {%d, %d, %d}\n"
        "\tset title displays custom title of gameTab to false\n"
        "\tset title displays device name of gameTab to false\n"
        "\tset title displays shell path of gameTab to false\n"
        "\tset title displays window size of gameTab to false\n"
        "\tset title displays file name of gameTab to false\n"
        "end tell"
        % (
            _window(window_id),
            settings.columns,
            settings.rows,
            _as_applescript_string(settings.font_name),
            settings.font_size,
            red,
            green,
            blue,
        )
    )


def script_move_window(window_id, x, y):
    """Place the window we created at (x, y) (WIN-4)."""
    return (
        'tell application "Terminal"\n'
        "\tset position of %s to {%d, %d}\n"
        "end tell" % (_window(window_id), int(x), int(y))
    )


def script_tab_busy(window_id):
    """Is the game process still running? (WIN-5, and the modal-sheet guard.)"""
    return (
        'tell application "Terminal"\n'
        "\treturn (busy of tab 1 of %s) as text\n"
        "end tell" % _window(window_id)
    )


def script_close_window(window_id):
    """Close our window -- and only if its tab is idle (WIN-5).

    The busy test is inside the script so that the check and the close cannot
    be separated by the player quitting, or by anything else, in between.
    Returns ``closed`` or ``busy``.
    """
    return (
        'tell application "Terminal"\n'
        "\tset gameWindow to %s\n"
        "\tif busy of tab 1 of gameWindow is false then\n"
        "\t\tclose gameWindow\n"
        '\t\treturn "closed"\n'
        "\telse\n"
        '\t\treturn "busy"\n'
        "\tend if\n"
        "end tell" % _window(window_id)
    )


def script_window_visible(window_id):
    """``visible``, not ``exists``: Terminal keeps a stale window object after
    a close."""
    return (
        'tell application "Terminal"\n'
        "\ttry\n"
        "\t\treturn (visible of %s) as text\n"
        "\ton error\n"
        '\t\treturn "gone"\n'
        "\tend try\n"
        "end tell" % _window(window_id)
    )


def script_window_name(window_id):
    """Read our window's title back (WIN-3). A read, by id."""
    return (
        'tell application "Terminal"\n'
        "\treturn name of %s\n"
        "end tell" % _window(window_id)
    )


def script_window_ids():
    """Every Terminal window id, for a before/after census.

    This enumerates in order to *count*. Nothing is ever acted on as a result
    of this list.
    """
    return (
        'tell application "Terminal"\n'
        '\tset out to ""\n'
        "\trepeat with w in windows\n"
        "\t\tset out to out & (id of w as text) & linefeed\n"
        "\tend repeat\n"
        "\treturn out\n"
        "end tell"
    )


def parse_position(text):
    """``"12 34"`` -> ``(12, 34)``; ``"none"`` -> ``None``. Pure."""
    text = (text or "").strip()
    if not text or text == "none":
        return None
    parts = text.replace(",", " ").split()
    if len(parts) < 2:
        return None
    try:
        return (int(float(parts[0])), int(float(parts[1])))
    except ValueError:
        return None


def parse_window_ids(text):
    """The census output, one id per line. Pure."""
    ids = []
    for line in (text or "").replace(",", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ids.append(int(line))
        except ValueError:
            continue
    return ids


# --------------------------------------------------------------------------
# Impure: everything below actually talks to Terminal.app.
# --------------------------------------------------------------------------


def run_osascript(script, timeout=20.0):
    """Run one AppleScript and return its stdout, stripped."""
    try:
        completed = subprocess.run(
            [OSASCRIPT, "-"],
            input=script,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise WindowError(
            "osascript timed out after %.1fs. A modal sheet on a Terminal "
            "window blocks every AppleScript call; check the screen." % timeout
        )
    except OSError as exc:
        raise WindowError("could not run %s: %s" % (OSASCRIPT, exc))
    if completed.returncode != 0:
        raise WindowError(
            "osascript failed (%d): %s"
            % (completed.returncode, (completed.stderr or "").strip())
        )
    return (completed.stdout or "").strip()


def screen_size():
    """The main display's size in points, for the WIN-4 clamp.

    CoreGraphics through ctypes: no TCC permission, no subprocess, no
    third-party module. Falls back to a conservative size.
    """
    try:
        path = (
            ctypes.util.find_library("CoreGraphics")
            or "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        core_graphics = ctypes.cdll.LoadLibrary(path)
        core_graphics.CGMainDisplayID.restype = ctypes.c_uint32
        core_graphics.CGDisplayPixelsWide.restype = ctypes.c_size_t
        core_graphics.CGDisplayPixelsHigh.restype = ctypes.c_size_t
        core_graphics.CGDisplayPixelsWide.argtypes = [ctypes.c_uint32]
        core_graphics.CGDisplayPixelsHigh.argtypes = [ctypes.c_uint32]
        display = core_graphics.CGMainDisplayID()
        width = int(core_graphics.CGDisplayPixelsWide(display))
        height = int(core_graphics.CGDisplayPixelsHigh(display))
        if width > 0 and height > 0:
            return (width, height)
    except Exception:  # pragma: no cover - depends on the machine
        pass
    return FALLBACK_SCREEN


def controlling_tty():
    """The supervisor's own tty, or None when it has no controlling terminal.

    Every agent in this project runs without one, which is why WIN-4 is a
    human check.
    """
    try:
        return os.ttyname(0)
    except OSError:
        return None


def reference_position(tty=None):
    """The position the game window is offset from, and where it came from."""
    if tty is None:
        tty = controlling_tty()
    tty_position = None
    if tty:
        tty_position = parse_position(run_osascript(script_reference_position(tty)))
    front_position = None
    if tty_position is None:
        front_position = parse_position(run_osascript(script_front_position()))
    return choose_reference(tty_position, front_position)


def terminal_window_ids():
    """Census of Terminal's windows -- used to prove nothing else changed."""
    return parse_window_ids(run_osascript(script_window_ids()))


def open_game_window(command):
    """WIN-1. Returns the id of the window just created, and nothing else."""
    answer = run_osascript(script_open_window(command))
    try:
        return int(answer.strip())
    except (TypeError, ValueError):
        raise WindowError("could not read the new window's id from %r" % answer)


def configure_window(window_id, settings=DEFAULT_SETTINGS):
    """WIN-2, WIN-3."""
    run_osascript(script_configure_window(window_id, settings))


def move_window(window_id, x, y):
    """WIN-4."""
    run_osascript(script_move_window(window_id, x, y))


def is_busy(window_id):
    """True while the game process is still running in our window."""
    return run_osascript(script_tab_busy(window_id)).strip().lower() == "true"


def window_name(window_id):
    """WIN-3, read back by id."""
    return run_osascript(script_window_name(window_id))


def window_is_visible(window_id):
    """After a close, Terminal keeps a stale window object: ask ``visible``."""
    answer = run_osascript(script_window_visible(window_id)).strip().lower()
    return answer == "true"


def wait_until_idle(window_id, timeout=None, poll=0.2, sleep=time.sleep):
    """Poll ``busy of tab 1`` until the game process is gone (WIN-5).

    ``timeout=None`` waits as long as the player plays. Returns True when the
    tab went idle, False when the timeout ran out.
    """
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        if not is_busy(window_id):
            return True
        if deadline is not None and time.monotonic() >= deadline:
            return False
        sleep(poll)


def close_window(window_id):
    """Close our window by id, but never while its tab is busy."""
    return run_osascript(script_close_window(window_id)).strip() == "closed"


def close_when_idle(window_id, timeout=CLOSE_GRACE_SECONDS, sleep=time.sleep):
    """The one close path: wait for the child, confirm it is gone, then close.

    Used by the success path and the failure path alike. Returns True when the
    window was closed; False -- leaving the window open rather than forcing
    it -- when the child was still running.
    """
    if not wait_until_idle(window_id, timeout=timeout, sleep=sleep):
        return False
    return close_window(window_id)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def supervise(
    root=None,
    settings=DEFAULT_SETTINGS,
    report=None,
    close_grace=CLOSE_GRACE_SECONDS,
):
    """The whole of ``./play``: WIN-1..5, in order.

    Reads the reference position, opens the window, captures its id, applies
    the settings, positions it, waits for the game to end, and closes that
    window by that id -- on the failure path too.
    """
    if root is None:
        root = repo_root()
    if report is None:
        report = _stderr_report

    reference, source = reference_position()
    target = offset_position(reference, screen_size())

    window_id = open_game_window(child_command(root))
    try:
        configure_window(window_id, settings)
        move_window(window_id, target[0], target[1])
        report(
            "game window %d at %s (reference %s from %s)"
            % (window_id, target, reference, source)
        )
        wait_until_idle(window_id, timeout=None)
        return 0
    finally:
        if not close_when_idle(window_id, timeout=close_grace):
            report(
                "the game is still running in Terminal window id %d, so it has "
                "been left open. Quit the game with q and close it yourself."
                % window_id
            )


def _stderr_report(message):
    sys.stderr.write("play: %s\n" % message)
    sys.stderr.flush()
