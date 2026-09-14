"""The desktop automation adapter: script text in, typed values out.

One class, one responsibility — turn each operation into a bounded
:class:`~launcher.script.ScriptCall`, hand it to the runner, and parse the
answer back into a number, a rectangle or a boolean. It holds no state about
which window is the game's; that belongs to the policy layer, which is what
keeps caution C1 checkable — every method here takes the window id it is to act
on, so there is no "current window" for anything to drift onto.
"""

from launcher import script
from launcher.geometry import Point, Rect, Size
from launcher.runner import AutomationError


class Desktop(object):
    def __init__(self, runner, settings=None):
        self.runner = runner
        self.settings = settings or WindowSettings()

    # -- before anything is created -------------------------------------

    def reference_window(self):
        """The frame of the window the player was last looking at."""
        return self._rect(script.reference_window_geometry(), "reference window")

    def visible_screen(self):
        """The bounds of the desktop."""
        return self._rect(script.visible_screen_bounds(), "screen bounds")

    # -- creation, and the identity it yields ---------------------------

    def open_window_running(self, command):
        """Open a window running ``command`` and return its captured id."""
        answer = self.runner.run(script.open_window_running(command))
        return self._int(answer, "window id")

    # -- everything after creation names that id ------------------------

    def configure(self, window_id):
        self.runner.run(
            script.configure_window(
                window_id,
                columns=self.settings.columns,
                rows=self.settings.rows,
                title=self.settings.title,
                font_name=self.settings.font_name,
                font_size=self.settings.font_size,
            )
        )

    def window_size(self, window_id):
        answer = self.runner.run(script.window_size(window_id))
        width, height = self._ints(answer, 2, "window size")
        return Size(width, height)

    def move(self, window_id, point):
        answer = self.runner.run(script.set_window_position(window_id, point))
        x, y = self._ints(answer, 2, "window position")
        return Point(x, y)

    def is_busy(self, window_id):
        return self._bool(self.runner.run(script.window_is_busy(window_id)))

    def processes(self, window_id):
        """The names of the processes running in the captured window.

        Empty when nothing is. More trustworthy than :meth:`is_busy` once the
        window has been given its grid — see
        :func:`launcher.script.window_processes`.
        """
        answer = self.runner.run(script.window_processes(window_id))
        return [name for name in answer.strip().split("|") if name.strip()]

    def close(self, window_id):
        self.runner.run(script.close_window(window_id))

    def is_visible(self, window_id):
        answer = self.runner.run(script.window_is_visible(window_id)).strip().lower()
        if answer == "gone":
            return False
        return self._bool(answer)

    # -- parsing --------------------------------------------------------

    def _rect(self, call, what):
        left, top, right, bottom = self._ints(self.runner.run(call), 4, what)
        return Rect(left, top, right, bottom)

    def _ints(self, answer, count, what):
        parts = [part.strip() for part in answer.split(",")]
        if len(parts) != count:
            raise AutomationError(
                "expected %d numbers for the %s, got %r" % (count, what, answer)
            )
        return tuple(self._int(part, what) for part in parts)

    @staticmethod
    def _int(text, what):
        try:
            return int(float(text.strip()))
        except (TypeError, ValueError):
            raise AutomationError("expected a number for the %s, got %r" % (what, text))

    @staticmethod
    def _bool(text):
        answer = text.strip().lower()
        if answer == "true":
            return True
        if answer == "false":
            return False
        raise AutomationError("expected true or false, got %r" % (text,))


class WindowSettings(object):
    """What WIN-2 and WIN-3 ask the window to look like."""

    def __init__(
        self,
        columns=script.COLUMNS,
        rows=script.ROWS,
        title=script.TITLE,
        font_name=script.FONT_NAME,
        font_size=script.FONT_SIZE,
    ):
        self.columns = columns
        self.rows = rows
        self.title = title
        self.font_name = font_name
        self.font_size = font_size
