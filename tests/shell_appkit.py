"""Drive this process's own AppKit objects, for the shell's desktop tests. Test support only.

Everything here acts on the calling process's *own* application: it posts
events into its own event queue, clicks its own window's buttons and picks
from its own application menu. None of it needs an accessibility or
automation permission, and none of it can touch another application's
windows, because it never addresses one.

What it is and is not evidence of:

* A posted key event enters the same AppKit path a real key press takes
  once the window server has delivered it to the application: NSApp's event
  queue, the key window, then Tk's own key handling. It skips the window
  server's choice of which application gets the key, which is why the tests
  also check that the game's window *is* the key window of the frontmost
  application.
* ``click_close_button`` and ``choose_quit_from_app_menu`` invoke the real
  title-bar button and the real menu item, through the controls themselves.
"""

import ctypes
import ctypes.util

_objc = ctypes.CDLL(ctypes.util.find_library("objc"))
ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
_objc.objc_getClass.restype = ctypes.c_void_p
_objc.objc_getClass.argtypes = [ctypes.c_char_p]
_objc.sel_registerName.restype = ctypes.c_void_p
_objc.sel_registerName.argtypes = [ctypes.c_char_p]
_SEND = ctypes.cast(_objc.objc_msgSend, ctypes.c_void_p).value

id_ = ctypes.c_void_p


class NSPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


def _msg(restype, *argtypes):
    return ctypes.CFUNCTYPE(restype, id_, id_, *argtypes)(_SEND)


def _cls(name: str) -> int:
    return _objc.objc_getClass(name.encode())


def _sel(name: str) -> int:
    return _objc.sel_registerName(name.encode())


def _call(obj, selector, restype=id_, argtypes=(), *args):
    return _msg(restype, *argtypes)(obj, _sel(selector), *args)


def _nsstring(text: str) -> int:
    return _call(_cls("NSString"), "stringWithUTF8String:", id_, (ctypes.c_char_p,), text.encode("utf-8"))


def _pystring(nsstring) -> str:
    if not nsstring:
        return ""
    raw = _call(nsstring, "UTF8String", ctypes.c_char_p)
    return raw.decode("utf-8") if raw else ""


def _app() -> int:
    return _call(_cls("NSApplication"), "sharedApplication")


def key_window():
    """This application's key window (an NSWindow pointer), or ``None``."""
    return _call(_app(), "keyWindow") or None


def key_window_number() -> int | None:
    window = key_window()
    return _call(window, "windowNumber", ctypes.c_long) if window else None


def is_active() -> bool:
    """Whether this application is the active (frontmost) one."""
    return bool(_call(_app(), "isActive", ctypes.c_bool))


# Virtual key codes and the characters AppKit attaches to them.
_FN = 0x800000          # NSEventModifierFlagFunction
_NUMPAD = 0x200000      # NSEventModifierFlagNumericPad
SHIFT = 0x20000         # NSEventModifierFlagShift
CAPS_LOCK = 0x10000     # NSEventModifierFlagCapsLock

KEYS = {
    # name: (keyCode, characters, charactersIgnoringModifiers, modifierFlags)
    "Up": (126, "", "", _FN | _NUMPAD),
    "Down": (125, "", "", _FN | _NUMPAD),
    "Left": (123, "", "", _FN | _NUMPAD),
    "Right": (124, "", "", _FN | _NUMPAD),
    "q": (12, "q", "q", 0),
    "Q": (12, "Q", "q", SHIFT),
    "Q-caps-lock": (12, "Q", "q", CAPS_LOCK),
    "a": (0, "a", "a", 0),
    "z": (6, "z", "z", 0),
    "1": (18, "1", "1", 0),
    "space": (49, " ", " ", 0),
    "Return": (36, "\r", "\r", 0),
    "Escape": (53, "\x1b", "\x1b", 0),
    "Tab": (48, "\t", "\t", 0),
    "BackSpace": (51, "\x7f", "\x7f", 0),
    "F1": (122, "", "", _FN),
}


def post_key(name: str) -> None:
    """Post a key-down and key-up for ``name`` (a key of :data:`KEYS`) to the key window."""
    code, chars, bare, flags = KEYS[name]
    window_number = key_window_number() or 0
    make = _msg(
        id_,
        ctypes.c_ulong, NSPoint, ctypes.c_ulong, ctypes.c_double, ctypes.c_long,
        id_, id_, id_, ctypes.c_bool, ctypes.c_ushort,
    )
    selector = _sel(
        "keyEventWithType:location:modifierFlags:timestamp:windowNumber:"
        "context:characters:charactersIgnoringModifiers:isARepeat:keyCode:"
    )
    post = _msg(None, id_, ctypes.c_bool)
    for event_type in (10, 11):  # NSEventTypeKeyDown, NSEventTypeKeyUp
        event = make(
            _cls("NSEvent"), selector, event_type, NSPoint(0, 0), flags, 0.0,
            window_number, None, _nsstring(chars), _nsstring(bare), False, code,
        )
        post(_app(), _sel("postEvent:atStart:"), event, False)


def _main_window():
    """The application's one visible titled window."""
    windows = _call(_app(), "windows")
    count = _call(windows, "count", ctypes.c_ulong)
    for i in range(count):
        window = _call(windows, "objectAtIndex:", id_, (ctypes.c_ulong,), i)
        if _call(window, "isVisible", ctypes.c_bool):
            return window
    return None


def visible_window_count() -> int:
    """How many of this application's NSWindows are visible."""
    windows = _call(_app(), "windows")
    count = _call(windows, "count", ctypes.c_ulong)
    return sum(
        1 for i in range(count)
        if _call(_call(windows, "objectAtIndex:", id_, (ctypes.c_ulong,), i), "isVisible", ctypes.c_bool)
    )


def _title_button(which: int):
    window = _main_window()
    return _call(window, "standardWindowButton:", id_, (ctypes.c_ulong,), which) if window else None


CLOSE_BUTTON, MINIATURIZE_BUTTON, ZOOM_BUTTON = 0, 1, 2


def title_button_enabled(which: int) -> bool | None:
    button = _title_button(which)
    return bool(_call(button, "isEnabled", ctypes.c_bool)) if button else None


def click_title_button(which: int) -> bool:
    """Click the window's own title-bar button (``performClick:``). False if there is none.

    The click is queued on the run loop rather than made here: a click made
    synchronously from inside a Tk callback re-enters Tk, which calls back
    into Python while ctypes has released the GIL, and the interpreter aborts
    (measured: "PyEval_RestoreThread: the function must be called with the
    GIL held"). Queued, it arrives from the event loop as a real click does.
    """
    button = _title_button(which)
    if not button:
        return False
    _call(
        button, "performSelector:withObject:afterDelay:", None,
        (id_, id_, ctypes.c_double), _sel("performClick:"), None, 0.0,
    )
    return True


def window_is_resizable() -> bool | None:
    """Whether the window's style mask includes NSWindowStyleMaskResizable (bit 3)."""
    window = _main_window()
    if not window:
        return None
    return bool(_call(window, "styleMask", ctypes.c_ulong) & 8)


def app_menu_quit_title() -> str:
    """The title of the application menu's Quit item (the one whose key is ``q``)."""
    item = _quit_item()
    return _pystring(_call(item[0], "title")) if item else ""


def _quit_item():
    main = _call(_app(), "mainMenu")
    if not main:
        return None
    app_menu = _call(_call(main, "itemAtIndex:", id_, (ctypes.c_long,), 0), "submenu")
    if not app_menu:
        return None
    n = _call(app_menu, "numberOfItems", ctypes.c_long)
    for i in range(n):
        item = _call(app_menu, "itemAtIndex:", id_, (ctypes.c_long,), i)
        if _pystring(_call(item, "keyEquivalent")) == "q":
            return item, app_menu, i
    return None


def choose_quit_from_app_menu() -> bool:
    """Pick the application menu's Quit item, as a click on it would. False if not found."""
    found = _quit_item()
    if not found:
        return False
    _, menu, index = found
    _call(menu, "performActionForItemAtIndex:", None, (ctypes.c_long,), index)
    return True


def post_mouse_drag(x0: float, y0: float, x1: float, y1: float, steps: int = 10) -> None:
    """Post a left-button press at window point (x0, y0), a drag to (x1, y1), and a release.

    Coordinates are in the key window's base coordinates (origin bottom-left).
    """
    window = _main_window()
    number = _call(window, "windowNumber", ctypes.c_long) if window else 0
    make = _msg(
        id_,
        ctypes.c_ulong, NSPoint, ctypes.c_ulong, ctypes.c_double, ctypes.c_long,
        id_, ctypes.c_long, ctypes.c_long, ctypes.c_float,
    )
    selector = _sel(
        "mouseEventWithType:location:modifierFlags:timestamp:windowNumber:"
        "context:eventNumber:clickCount:pressure:"
    )
    post = _msg(None, id_, ctypes.c_bool)
    points = [(x0, y0)] + [
        (x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps) for k in range(1, steps + 1)
    ]
    events = [(1, points[0], 1.0)]                      # NSEventTypeLeftMouseDown
    events += [(6, p, 1.0) for p in points[1:]]         # NSEventTypeLeftMouseDragged
    events += [(2, points[-1], 0.0)]                    # NSEventTypeLeftMouseUp
    for n, (event_type, (x, y), pressure) in enumerate(events):
        event = make(_cls("NSEvent"), selector, event_type, NSPoint(x, y), 0, 0.0, number, None, n, 1, pressure)
        post(_app(), _sel("postEvent:atStart:"), event, False)
