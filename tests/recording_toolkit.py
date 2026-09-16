"""A :class:`Toolkit` that records what it was asked to do and opens nothing.

This is what makes the whole of WI-3 testable with no window on anybody's
desktop.  It records every call in one ordered list, so that a test can assert
not only *that* the window was closed but *when* it was closed relative to the
timer being stopped — which is the thing WI-3 has to get right.

Its name does not begin with ``test_``, so the suite never collects it as a
test module.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from terminal_game.shell.toolkit import KeyPress, Toolkit, WindowSpec


class RecordingToolkit(Toolkit):
    """Records calls; never touches a window server."""

    def __init__(self) -> None:
        #: Every call, in the order it was made: ``(name, detail)``.
        self.operations: List[Tuple[str, object]] = []
        #: The spec the window was created from, once it has been.
        self.window_spec: Optional[WindowSpec] = None
        #: A stand-in for the thing the character grid surface paints into.
        self.drawing_target = object()
        self.key_handler: Optional[Callable[[KeyPress], None]] = None
        self.close_handler: Optional[Callable[[], None]] = None
        self.event_loop_entered = False
        #: If set, called while the event loop is "running", so that a test
        #: can make something happen inside the loop.
        self.event_loop_body: Optional[Callable[[], None]] = None

        # handle -> (due_ms, delay_ms, callback). Virtual time, because a
        # real scheduler fires by when a callback is *due* and not by the
        # order things were asked for: the skeleton schedules its ten-second
        # deadline before the event loop starts the 143 ms tick, and firing
        # those in the order they were asked for would be nothing like what
        # happens.
        self._pending = {}
        self._next_handle = 1
        self.now_ms = 0

    # -- what the Toolkit seam requires --------------------------------

    def create_window(self, spec: WindowSpec):
        self.operations.append(("create_window", spec))
        self.window_spec = spec
        return self.drawing_target

    def destroy_window(self) -> None:
        self.operations.append(("destroy_window", None))

    def bind_key_handler(self, handler) -> None:
        self.operations.append(("bind_key_handler", None))
        self.key_handler = handler

    def bind_close_request(self, handler) -> None:
        self.operations.append(("bind_close_request", None))
        self.close_handler = handler

    def schedule_once(self, delay_ms: int, callback):
        handle = self._next_handle
        self._next_handle += 1
        self._pending[handle] = (self.now_ms + delay_ms, delay_ms, callback)
        self.operations.append(("schedule_once", delay_ms))
        return handle

    def cancel_scheduled(self, handle) -> None:
        self.operations.append(("cancel_scheduled", handle))
        self._pending.pop(handle, None)

    def run_event_loop(self) -> None:
        self.operations.append(("run_event_loop", None))
        self.event_loop_entered = True
        if self.event_loop_body is not None:
            self.event_loop_body()

    def stop_event_loop(self) -> None:
        self.operations.append(("stop_event_loop", None))

    # -- what a test drives it with ------------------------------------

    @property
    def names(self) -> List[str]:
        """Just the call names, in order."""
        return [name for name, _ in self.operations]

    @property
    def scheduled_delays(self) -> List[int]:
        """Every delay the Shell asked to be called back after."""
        return [detail for name, detail in self.operations if name == "schedule_once"]

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def count(self, name: str) -> int:
        return self.names.count(name)

    def index_of(self, name: str) -> int:
        return self.names.index(name)

    def fire_due_timer(self) -> int:
        """Fire whichever callback is due soonest; return the delay it asked for.

        Ties are broken by the order they were scheduled, as a real
        scheduler does. Virtual time moves forward to the moment it fired.
        """
        if not self._pending:
            raise AssertionError("nothing is scheduled")
        handle = min(self._pending, key=lambda h: (self._pending[h][0], h))
        due_ms, delay_ms, callback = self._pending.pop(handle)
        self.now_ms = due_ms
        callback()
        return delay_ms

    def press(self, keysym: str, char: str = "") -> KeyPress:
        """Deliver a key press through whatever handler was bound."""
        key = KeyPress(keysym=keysym, char=char)
        if self.key_handler is None:
            raise AssertionError("no key handler has been bound")
        self.key_handler(key)
        return key

    def request_close(self) -> None:
        """Ask to close, as the window's own close button would."""
        if self.close_handler is None:
            raise AssertionError("no close handler has been bound")
        self.close_handler()
