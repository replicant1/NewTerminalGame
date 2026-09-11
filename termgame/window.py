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
import signal
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

#: A display, as ``(left, top, width, height)``. Displays are read from
#: CoreGraphics and then moved into AppleScript's coordinate space, which is
#: *not* the same one -- see ``applescript_display_bounds``. Measured on this
#: machine: CoreGraphics reports (0, 0, 1512, 982) for the main display and two
#: more at (-3509, -1440) and (-949, -1440), each 2560 x 1440. This constant is
#: the conservative stand-in used when nothing can be read at all.
FALLBACK_SCREEN_BOUNDS = (0, 0, 1440, 900)

#: The menu bar (and, on this machine, the notch) occupy the top of the screen;
#: a window title bar placed above this is not reachable with the mouse.
MENU_BAR_HEIGHT = 38

#: How long the supervisor waits, on the failure path, for the child to exit
#: before giving up and leaving the window open rather than forcing it.
#:
#: **Why ten seconds.** Two transitions were measured (WI-2's findings, §3):
#: the tab goes from ``do script`` returning to holding the child's processes
#: in **0.25 s**, and from the child exiting to holding none in **0.19 s**.
#: Ten seconds is forty times the larger of those, so no amount of ordinary
#: AppleScript latency or machine load can trip it, and a child that crashed
#: a moment ago is always reaped inside it. It is also short enough that a
#: player who has just been shown an error is not left staring at a ``./play``
#: that appears to have hung. If it *does* expire, the game really is still
#: running, and the window is then deliberately left open -- forcing a close
#: on a busy tab raises the modal sheet (§2.6 rule 3), which is strictly worse
#: than one window the player can close themselves.
CLOSE_GRACE_SECONDS = 10.0

#: How long an empty tab is not yet read as "the game has ended". The tab is
#: momentarily process-free between ``do script`` returning and the child
#: appearing (measured at 0.25 s); this is eight times that.
STARTUP_GRACE_SECONDS = 2.0

#: How often the supervisor asks Terminal whether the game is still running.
POLL_SECONDS = 0.2

#: How long any single AppleScript is given. A modal sheet on a Terminal
#: window blocks every AppleScript call in the system, and this is what turns
#: that into a message instead of a process that never returns.
OSASCRIPT_TIMEOUT_SECONDS = 20.0

#: What ``./play`` exits with when it was interrupted rather than played.
#: 128 + SIGINT, the shell convention.
INTERRUPTED_EXIT_STATUS = 130

#: The answer every script that addresses our window gives when there is no
#: such window any more -- the player closed it themselves, or Terminal quit.
#: It is not an error: the goal state of the close is "that window is not on
#: the screen", and a window that is gone is already in it.
GONE = "gone"

#: The signals that must still end with the game window closed. ``SIGINT`` is
#: ^C in the terminal the player typed ``./play`` into; ``SIGTERM`` is a plain
#: ``kill``; ``SIGHUP`` is that terminal being closed out from under us.
INTERRUPT_SIGNALS = ("SIGINT", "SIGTERM", "SIGHUP")

OSASCRIPT = "/usr/bin/osascript"


class WindowError(RuntimeError):
    """An AppleScript call failed, or returned something unusable."""


class SupervisorInterrupted(RuntimeError):
    """A signal arrived while the supervisor was watching the game.

    Raised out of the signal handler so that the ``finally`` which closes the
    game window runs. A handler that merely set a flag would not: the
    supervisor spends its life inside ``osascript``, and nothing would look at
    the flag until the game ended on its own.
    """


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


def applescript_display_bounds(cg_displays):
    """CoreGraphics display rects, moved into the space AppleScript uses. Pure.

    **They are not the same space, and assuming they were put the game window
    on the wrong screen.** Measured on this machine, writing three positions to
    a window of our own and reading the same window's frame back out of
    ``CGWindowListCopyWindowInfo``:

    ==========================  ===========================
    written via AppleScript     CoreGraphics says
    ==========================  ===========================
    ``(600, 300)``              ``y = -1140``
    ``(-898, 76)``              ``y = -1364``
    ``(-3000, -1000)``          ``y = -1410`` (AppleScript
                                clamped the write to 30)
    ==========================  ===========================

    A constant offset of 1440 in y, none in x: AppleScript's origin is the top
    of the *topmost* display, CoreGraphics' is the top of the *main* one, and
    here the topmost display is 1440 px above it. So the shift is "move the
    topmost display's top to y = 0, leave x alone".

    AppleScript also refuses to place a window above y = 30 and clamps the
    write silently, which is why the game's own minimum is well below that.
    """
    if not cg_displays:
        return [FALLBACK_SCREEN_BOUNDS]
    topmost = min(top for (_, top, _, _) in cg_displays)
    return [
        (left, top - topmost, width, height)
        for (left, top, width, height) in cg_displays
    ]


def choose_display(reference, displays):
    """The display the reference window is on (WIN-4). Pure.

    *displays* must already be in AppleScript's space; see
    ``applescript_display_bounds``.

    "Somewhere visible" means visible *on the screen the player is looking
    at*, so the window is clamped within the reference's own display, not
    always within the main one. Measured: this machine has three displays and
    the one the reference window was on is not the main one, so clamping to
    the main display moved the game to a screen the player was not using.

    Falls back to the first display -- CoreGraphics lists the main display
    first -- when the reference is on no display at all.
    """
    if not displays:
        return FALLBACK_SCREEN_BOUNDS
    ref_x, ref_y = reference
    for bounds in displays:
        left, top, width, height = bounds
        if left <= ref_x < left + width and top <= ref_y < top + height:
            return bounds
    return displays[0]


def offset_position(
    reference,
    screen_bounds=FALLBACK_SCREEN_BOUNDS,
    window_size=GAME_WINDOW_PIXELS,
    offset=OFFSET,
    menu_bar=MENU_BAR_HEIGHT,
):
    """Where the game window goes: below and right of *reference* (WIN-4).

    Pure. The offset is clamped so the whole window stays on *screen_bounds* --
    a reference near the bottom-right corner would otherwise put most of the
    game off the edge, which is exactly what WIN-4 exists to prevent -- and so
    that its title bar stays clear of the menu bar.
    """
    ref_x, ref_y = reference
    win_w, win_h = window_size
    left, top, width, height = screen_bounds
    x = int(ref_x) + offset[0]
    y = int(ref_y) + offset[1]

    min_x = int(left)
    min_y = int(top) + menu_bar
    max_x = max(min_x, int(left) + int(width) - int(win_w))
    max_y = max(min_y, int(top) + int(height) - int(win_h))

    x = min(max(min_x, x), max_x)
    y = min(max(min_y, y), max_y)
    return (x, y)


def child_command(repo_root, child_name=CHILD_NAME):
    """The shell command Terminal runs in the new window.

    ``exec`` so the child replaces the shell and the tab stops being busy the
    instant the game exits. No arguments: an argument would change the active
    process name and break WIN-3.
    """
    path = os.path.join(repo_root, child_name)
    return "exec " + shell_quote(path)


def shell_quote(text):
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
    """Read the position of Terminal's frontmost *visible* window.

    This is the ONLY script in the project that mentions the front window, it
    is a read, and it runs before the game window exists. Nothing is ever
    written to, or closed by, the front window.

    Visible matters: measured, ``front window`` answered with a hidden window
    parked at (-898, 76), a position on none of this machine's three displays.
    Terminal's window list is in front-to-back order, so the first visible one
    is the frontmost window the player can actually see.
    """
    return (
        'tell application "Terminal"\n'
        "\trepeat with w in windows\n"
        "\t\tif visible of w then\n"
        "\t\t\tset p to position of w\n"
        '\t\t\treturn ((item 1 of p) as text) & " " & ((item 2 of p) as text)\n'
        "\t\tend if\n"
        "\tend repeat\n"
        '\treturn "none"\n'
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


def script_tab_state(window_id):
    """Is the game still running in our window? (WIN-5.)

    Returns ``"<busy> <process count>"``.

    **Measured, and it contradicts ARCHITECTURE.md section 6.3:** ``busy`` is
    **false** the whole time the game is running. Terminal does not count a
    process that is blocked reading from the tty as busy, and the game spends
    its whole life blocked on a keypress. (``exec /bin/sleep 4`` in the same
    window *does* report busy true, so it is the waiting-on-input that does
    it, not ``exec``.) Polling ``busy`` alone -- which is what the architecture
    prescribes -- closes the window about a second after opening it.

    ``count of processes of tab 1`` is the signal that works: measured 3 at
    0.25 s (the shell being replaced), 2 (``login``, ``Python``) for as long as
    the game runs, and 0 within 0.19 s of the child exiting.

    ``busy`` is still read, and still gates the close, because it is what
    Terminal itself uses to decide whether to raise the modal confirmation
    sheet, and it *is* briefly true while the exec happens.

    The read is wrapped so that a window which is *gone* answers ``gone``
    rather than raising. A player may close the game window themselves, and
    every script that addresses a window id that no longer exists fails with
    ``Can't get window 1 whose id = N. Invalid index. (-1719)`` (measured, WI-2
    findings §7). Letting that out of the poll would turn "the player closed
    the window" into a traceback from ``./play``.
    """
    return (
        'tell application "Terminal"\n'
        "\ttry\n"
        "\t\tset gameTab to tab 1 of %s\n"
        '\t\treturn ((busy of gameTab) as text) & " " & '
        "((count of processes of gameTab) as text)\n"
        "\ton error\n"
        '\t\treturn "gone"\n'
        "\tend try\n"
        "end tell" % _window(window_id)
    )


def script_close_window(window_id):
    """Close our window -- and only if its tab is idle (WIN-5).

    The test is inside the script so that it and the close cannot be separated
    by anything happening in between. Both halves matter: no process left means
    the game has really ended (``busy`` alone does not -- see
    ``script_tab_state``), and ``busy`` false is what stops Terminal raising
    the modal confirmation sheet. Returns ``closed``, ``busy`` or ``gone``.

    ``gone`` is the third answer and it is not an error: the window id no
    longer resolves, because the player closed the window themselves or
    Terminal quit. The goal state of a close is "that window is not on the
    screen", and a window that is gone is already in it. Only the *addressing*
    is wrapped -- if the tab is busy the script still returns ``busy`` and
    still does not close anything.
    """
    return (
        'tell application "Terminal"\n'
        "\ttry\n"
        "\t\tset gameWindow to %s\n"
        "\t\tset gameTab to tab 1 of gameWindow\n"
        "\ton error\n"
        '\t\treturn "gone"\n'
        "\tend try\n"
        "\tif busy of gameTab is false and (count of processes of gameTab) is 0 then\n"
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


def script_tab_geometry(window_id):
    """Read our tab's size and font back (WIN-2). A read, by id.

    Returns ``"<columns> <rows> <font name> <font size>"``. The launch smoke
    uses this to check the window it opened really is 40 x 30 in Menlo 18,
    rather than trusting that the write it issued took effect.
    """
    return (
        'tell application "Terminal"\n'
        "\tset gameTab to tab 1 of %s\n"
        '\treturn ((number of columns of gameTab) as text) & " " & '
        '((number of rows of gameTab) as text) & " " & '
        '(font name of gameTab) & " " & ((font size of gameTab) as text)\n'
        "end tell" % _window(window_id)
    )


def script_visible_window_ids():
    """Every *visible* Terminal window id, for a before/after census.

    Visible, not all: measured, a closed window stays in Terminal's ``windows``
    collection -- three probe runs left ids 3924, 3927 and 3930 in it after
    being closed -- and only ``visible`` goes false. A census over ``windows``
    therefore never matches itself across a close.

    This enumerates in order to *count*. Nothing is ever acted on as a result
    of this list.
    """
    return (
        'tell application "Terminal"\n'
        '\tset out to ""\n'
        "\trepeat with w in windows\n"
        "\t\tif visible of w then set out to out & (id of w as text) & linefeed\n"
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


def run_osascript(script, timeout=OSASCRIPT_TIMEOUT_SECONDS):
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


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class _CGRect(ctypes.Structure):
    _fields_ = [("origin", _CGPoint), ("size", _CGSize)]


def displays():
    """Every active display as ``(left, top, width, height)``, main first.

    CoreGraphics through ctypes: no TCC permission, no subprocess, no
    third-party module, and none of the AppleScript-to-Finder tricks that
    would raise a permission prompt on the player's screen. Returns a
    single conservative display if it cannot be read.
    """
    try:
        path = (
            ctypes.util.find_library("CoreGraphics")
            or "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        core_graphics = ctypes.cdll.LoadLibrary(path)
        core_graphics.CGGetActiveDisplayList.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        core_graphics.CGGetActiveDisplayList.restype = ctypes.c_int32
        core_graphics.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        core_graphics.CGDisplayBounds.restype = _CGRect

        count = ctypes.c_uint32(0)
        identifiers = (ctypes.c_uint32 * 16)()
        if core_graphics.CGGetActiveDisplayList(
            16, identifiers, ctypes.byref(count)
        ) != 0:
            return [FALLBACK_SCREEN_BOUNDS]
        found = []
        for index in range(count.value):
            rect = core_graphics.CGDisplayBounds(identifiers[index])
            if rect.size.width > 0 and rect.size.height > 0:
                found.append(
                    (
                        int(rect.origin.x),
                        int(rect.origin.y),
                        int(rect.size.width),
                        int(rect.size.height),
                    )
                )
        if found:
            return found
    except Exception:  # pragma: no cover - depends on the machine
        pass
    return [FALLBACK_SCREEN_BOUNDS]


def controlling_tty():
    """The supervisor's own tty, or None when it has no controlling terminal.

    Every agent in this project runs without one, which is why WIN-4 is a
    human check.
    """
    try:
        return os.ttyname(0)
    except OSError:
        return None


def _read_position(script, what, report):
    """One reference query, which is allowed to fail.

    The reference position is a nicety: WIN-4 wants the window *near* the one
    the player was looking at, and when that cannot be discovered the fixed
    fallback is a perfectly good answer. So a failure here must not stop the
    game from starting -- but it is *reported with its text*, never swallowed
    silently, because a query that has begun failing is worth knowing about.

    This is where "Terminal is not running", "the game was launched from
    something that is not Terminal" and "automation was refused" all land.
    """
    try:
        return parse_position(run_osascript(script))
    except WindowError as error:
        report("could not read %s (%s); falling back" % (what, error))
        return None


def reference_position(tty=None, report=None):
    """The position the game window is offset from, and where it came from.

    Neither query is allowed to stop the game starting; see ``_read_position``.
    """
    if report is None:
        report = _stderr_report
    if tty is None:
        tty = controlling_tty()
    tty_position = None
    if tty:
        tty_position = _read_position(
            script_reference_position(tty), "the launching window's position", report
        )
    front_position = None
    if tty_position is None:
        front_position = _read_position(
            script_front_position(), "Terminal's front window position", report
        )
    return choose_reference(tty_position, front_position)


def visible_window_ids():
    """Census of Terminal's visible windows -- proof nothing else changed."""
    return parse_window_ids(run_osascript(script_visible_window_ids()))


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


def parse_tab_state(text):
    """``"false 2"`` -> ``(False, 2)``. Pure.

    ``"gone"`` -- the window no longer exists -- reads as ``(False, 0)``, i.e.
    *not running*, and so does anything else unparseable. That direction is
    chosen deliberately and it is the safe one: reading an unparseable answer
    as "still running" would leave the player's window open for ever, while
    reading it as "ended" only ever leads to a close, and the close has its own
    busy guard inside the AppleScript (``script_close_window``) which is what
    actually keeps the modal sheet away.
    """
    parts = (text or "").split()
    busy = bool(parts) and parts[0].strip().lower() == "true"
    count = 0
    if len(parts) > 1:
        try:
            count = int(parts[1])
        except ValueError:
            count = 0
    return (busy, count)


def tab_state(window_id):
    """``(busy, process count)`` for our window's tab."""
    return parse_tab_state(run_osascript(script_tab_state(window_id)))


def is_running(window_id):
    """True while the game is still alive in our window (WIN-5).

    See ``script_tab_state``: ``busy`` alone is false throughout the game, so
    the process count is what actually answers the question.
    """
    busy, processes = tab_state(window_id)
    return busy or processes > 0


def window_name(window_id):
    """WIN-3, read back by id."""
    return run_osascript(script_window_name(window_id))


def tab_geometry(window_id):
    """WIN-2, read back by id: ``(columns, rows, font name, font size)``."""
    parts = run_osascript(script_tab_geometry(window_id)).rsplit(" ", 1)
    if len(parts) != 2:
        raise WindowError("could not read the tab's geometry from %r" % parts)
    head, size = parts
    head_parts = head.split(" ", 2)
    if len(head_parts) != 3:
        raise WindowError("could not read the tab's geometry from %r" % head)
    columns, rows, font_name = head_parts
    try:
        return (int(columns), int(rows), font_name, int(float(size)))
    except ValueError:
        raise WindowError("could not read the tab's geometry from %r" % head)


def window_is_visible(window_id):
    """After a close, Terminal keeps a stale window object: ask ``visible``."""
    answer = run_osascript(script_window_visible(window_id)).strip().lower()
    return answer == "true"


def wait_until_idle(
    window_id,
    timeout=None,
    poll=POLL_SECONDS,
    startup=STARTUP_GRACE_SECONDS,
    sleep=time.sleep,
):
    """Poll our window's tab until the game has ended (WIN-5).

    ``timeout=None`` waits as long as the player plays -- that is the whole
    job of the supervisor. Returns True when the game has ended, False when
    the timeout ran out with it still running.

    *startup* exists because the tab is momentarily process-free between
    ``do script`` returning and the child appearing; an empty tab is only read
    as "the game has ended" once the game has been seen running, or once the
    startup grace has passed (which is what lets a child that exits instantly
    still be waited on).
    """
    deadline = None if timeout is None else time.monotonic() + timeout
    began = time.monotonic()
    seen_running = False
    while True:
        if is_running(window_id):
            seen_running = True
        elif seen_running or time.monotonic() - began >= startup:
            return True
        if deadline is not None and time.monotonic() >= deadline:
            return False
        sleep(poll)


def close_window(window_id):
    """Close our window by id -- and only if the game has really ended.

    The condition is checked inside the AppleScript; see
    ``script_close_window``. Returns True when the window is off the screen --
    which covers both ``closed`` and ``gone``, a window that was already
    closed by the player. False means the tab was still busy and the window
    has deliberately been left alone.
    """
    return run_osascript(script_close_window(window_id)).strip() in ("closed", GONE)


def close_when_idle(
    window_id, timeout=CLOSE_GRACE_SECONDS, startup=0.0, sleep=time.sleep
):
    """Wait for the game to end, confirm it has, then close the window.

    This is the failure path's clean-up. No startup grace here, and that is
    deliberate: measured, the tab already holds processes 0.25 s after
    ``do script`` returns -- before any statement that could fail has run --
    so on this path an empty tab really does mean nothing is running. The
    grace belongs to the main wait, where reading an empty tab too eagerly
    would close the window on a live game.

    Returns True when the window was closed; False -- leaving the window open
    rather than forcing it -- when the game was still running.
    """
    if not wait_until_idle(
        window_id, timeout=timeout, startup=startup, sleep=sleep
    ):
        return False
    return close_window(window_id)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _InterruptsRaise(object):
    """While this is entered, an interrupting signal raises an exception.

    That is the whole trick behind "the supervisor itself is interrupted ->
    the window is still closed". ``finally`` blocks run when an exception
    passes through them and do not run when the process is killed outright, so
    every signal that can reasonably be recovered from is turned into an
    exception and the existing clean-up does the rest.

    Handlers are installed on entry and the previous ones put back on exit, so
    importing this module never changes the process's signal disposition and
    ``play`` behaves normally once the game is over.

    ``signal.signal`` only works on the main thread of the main interpreter;
    off it, it raises ``ValueError`` and this quietly does nothing. That is
    correct rather than merely convenient -- a supervisor running on a worker
    thread (the launch smoke does exactly that) has no business rewiring the
    whole process's signal handling, and its window is closed by the same
    ``finally`` regardless.
    """

    def __init__(self, signal_names=INTERRUPT_SIGNALS):
        self.signal_names = tuple(signal_names)
        self.installed = []

    def _handler(self, number, frame):
        raise SupervisorInterrupted("signal %d" % number)

    def __enter__(self):
        for name in self.signal_names:
            number = getattr(signal, name, None)
            if number is None:  # pragma: no cover - every POSIX has all three
                continue
            try:
                previous = signal.signal(number, self._handler)
            except (ValueError, OSError, RuntimeError):
                continue
            self.installed.append((number, previous))
        return self

    def __exit__(self, kind, value, traceback):
        while self.installed:
            number, previous = self.installed.pop()
            try:
                signal.signal(number, previous)
            except (ValueError, OSError, RuntimeError):  # pragma: no cover
                pass
        return False


def close_after_the_game(window_id, game_ended, close_grace, report):
    """Close the game window, by id, whatever brought us here.

    This is the one clean-up, shared by the success path, the failure path and
    the interrupt path, and it is careful about three things:

    * **It never raises.** It runs inside a ``finally``; an exception escaping
      it would replace the error that actually caused the failure with a
      complaint about the clean-up, and the player would never learn what went
      wrong. AppleScript failures are reported with their text instead.
    * **It never forces a busy tab.** ``close_window`` returns False when the
      game is still running, and the answer to that is to say so and leave the
      window alone -- the modal sheet is worse than an open window (§2.6).
    * **It confirms with ``visible``, not ``exists``.** Terminal keeps a stale
      window object after a close (measured, WI-2 findings §6), so ``exists``
      is true for a window that is not on the screen and proves nothing.

    Returns True when the window is confirmed off the screen.
    """
    try:
        # On the way out of a finished game the wait has already proved the
        # game is gone, so close at once -- WIN-5 is "as soon as the game
        # ends". Any other way out waits the grace period first.
        if game_ended:
            closed = close_window(window_id)
        else:
            closed = close_when_idle(window_id, timeout=close_grace)
    except WindowError as error:
        report(
            "could not close Terminal window id %d: %s. If it is still on "
            "screen, close it yourself." % (window_id, error)
        )
        return False

    if not closed:
        report(
            "the game is still running in Terminal window id %d, so it has "
            "been left open. Quit the game with q and close it yourself."
            % window_id
        )
        return False

    try:
        if window_is_visible(window_id):
            report(
                "Terminal window id %d was closed but still reports itself "
                "visible. Close it yourself." % window_id
            )
            return False
    except WindowError as error:
        report(
            "could not confirm Terminal window id %d has gone: %s"
            % (window_id, error)
        )
        return False
    return True


def supervise(
    root=None,
    settings=DEFAULT_SETTINGS,
    report=None,
    close_grace=CLOSE_GRACE_SECONDS,
    on_window_opened=None,
):
    """The whole of ``./play``: WIN-1..5, in order.

    Reads the reference position, opens the window, captures its id, applies
    the settings, positions it, waits for the game to end, and closes that
    window by that id -- on the failure path, and on the interrupt path, too.

    *on_window_opened*, when given, is handed the window id the instant it is
    captured and before anything is done with it. It exists so that a caller
    which is not watching stderr -- the launch smoke -- learns the id from the
    supervisor itself rather than by enumerating Terminal's windows and
    guessing which one is new.

    Returns 0, or ``INTERRUPTED_EXIT_STATUS`` if a signal ended the game
    rather than the player.
    """
    if root is None:
        root = repo_root()
    if report is None:
        report = _stderr_report

    reference, source = reference_position(report=report)
    screens = applescript_display_bounds(displays())
    target = offset_position(reference, choose_display(reference, screens))

    window_id = open_game_window(child_command(root))
    game_ended = False
    status = 0
    with _InterruptsRaise():
        try:
            if on_window_opened is not None:
                on_window_opened(window_id)
            configure_window(window_id, settings)
            move_window(window_id, target[0], target[1])
            report(
                "game window %d at %s (reference %s from %s)"
                % (window_id, target, reference, source)
            )
            game_ended = wait_until_idle(window_id, timeout=None)
        except SupervisorInterrupted as error:
            report(
                "interrupted (%s); closing Terminal window id %d"
                % (error, window_id)
            )
            status = INTERRUPTED_EXIT_STATUS
        finally:
            close_after_the_game(window_id, game_ended, close_grace, report)
    return status


def _stderr_report(message):
    sys.stderr.write("play: %s\n" % message)
    sys.stderr.flush()
