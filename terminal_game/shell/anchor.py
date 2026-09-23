"""The anchor, and the screen it may be placed on: two read-only platform queries.

**The anchor** is the window that was frontmost at start-up, in any
application (IMPLEMENTATION_PLAN.md §1.8 Q7). It is read from the window
server's on-screen window list, which comes front to back: the first ordinary
window (layer 0, not transparent, not a sliver) that does not belong to this
process. Started from Terminal, that is the Terminal window it was started
from.

**The displays** are each screen's *visible* area (less the menu bar and
the Dock), from ``NSScreen``, flipped into the top-left-origin global points
that :mod:`terminal_game.shell.placement` uses.

Neither query needs a permission or raises a consent prompt:
``CGWindowListCopyWindowInfo`` hands out window bounds and owners to anyone
(only window *titles* are withheld without Screen Recording, and this does
not ask for them). Neither activates, moves or changes any window. Both are
plain C calls through ``ctypes``, so there is nothing to install.

:func:`find_anchor` gives up after :data:`ANCHOR_TIMEOUT_S` and returns
``None``, as it does when there is no window or the query fails (WI-9/C3, C5).
"""

import ctypes
import ctypes.util
import os
import threading
from collections.abc import Callable

from terminal_game.shell.placement import Rect

#: WI-9/C5: finding the anchor finishes within 500 ms or gives up.
ANCHOR_TIMEOUT_S = 0.5

#: Smaller than this is not a window a person was looking at (a status sliver, a drag proxy).
MIN_SIDE = 40

_kCGWindowListOptionOnScreenOnly = 1
_kCGWindowListExcludeDesktopElements = 16
_kCFNumberSInt64Type = 4
_kCFNumberDoubleType = 13


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class _CGRect(ctypes.Structure):
    _fields_ = [("origin", _CGPoint), ("size", _CGSize)]


def _frameworks():
    cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    cg.CGWindowListCopyWindowInfo.restype = ctypes.c_void_p
    cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    cg.CGRectMakeWithDictionaryRepresentation.restype = ctypes.c_bool
    cg.CGRectMakeWithDictionaryRepresentation.argtypes = [ctypes.c_void_p, ctypes.POINTER(_CGRect)]
    cf.CFArrayGetCount.restype = ctypes.c_long
    cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
    cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
    cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
    cf.CFDictionaryGetValue.restype = ctypes.c_void_p
    cf.CFDictionaryGetValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    cf.CFNumberGetValue.restype = ctypes.c_bool
    cf.CFNumberGetValue.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
    cf.CFStringGetCString.restype = ctypes.c_bool
    cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    return cf, cg


def _key(cg, name: str):
    return ctypes.c_void_p.in_dll(cg, name).value


def on_screen_windows() -> list[dict]:
    """The window server's on-screen windows, front to back: layer, pid, owner, alpha, bounds.

    Read-only. Raises ``OSError`` if the window server does not answer.
    """
    cf, cg = _frameworks()
    keys = {k: _key(cg, "kCGWindow" + k) for k in ("Layer", "OwnerPID", "OwnerName", "Alpha", "Bounds", "Number")}
    array = cg.CGWindowListCopyWindowInfo(
        _kCGWindowListOptionOnScreenOnly | _kCGWindowListExcludeDesktopElements, 0
    )
    if not array:
        raise OSError("CGWindowListCopyWindowInfo returned nothing")
    windows = []
    try:
        for i in range(cf.CFArrayGetCount(array)):
            info = cf.CFArrayGetValueAtIndex(array, i)

            def number(key, kind=_kCFNumberSInt64Type):
                ref = cf.CFDictionaryGetValue(info, keys[key])
                if not ref:
                    return None
                out = ctypes.c_double() if kind == _kCFNumberDoubleType else ctypes.c_int64()
                return out.value if cf.CFNumberGetValue(ref, kind, ctypes.byref(out)) else None

            owner = ""
            ref = cf.CFDictionaryGetValue(info, keys["OwnerName"])
            if ref:
                buffer = ctypes.create_string_buffer(512)
                if cf.CFStringGetCString(ref, buffer, 512, 0x08000100):  # kCFStringEncodingUTF8
                    owner = buffer.value.decode("utf-8", "replace")
            rect = _CGRect()
            bounds = cf.CFDictionaryGetValue(info, keys["Bounds"])
            if not bounds or not cg.CGRectMakeWithDictionaryRepresentation(bounds, ctypes.byref(rect)):
                continue
            windows.append({
                "id": number("Number"),
                "layer": number("Layer"),
                "pid": number("OwnerPID"),
                "owner": owner,
                "alpha": number("Alpha", _kCFNumberDoubleType),
                "bounds": Rect(rect.origin.x, rect.origin.y, rect.size.width, rect.size.height),
            })
    finally:
        cf.CFRelease(array)
    return windows


def frontmost_window(windows: list[dict], own_pid: int) -> dict | None:
    """The first ordinary window in front-to-back order that is not ours, or ``None``. Pure."""
    for window in windows:
        bounds = window["bounds"]
        if (
            window["layer"] == 0
            and window["pid"] != own_pid
            and (window["alpha"] is None or window["alpha"] > 0)
            and bounds.width >= MIN_SIDE
            and bounds.height >= MIN_SIDE
        ):
            return window
    return None


def find_anchor(
    query: Callable[[], list[dict]] = on_screen_windows,
    timeout: float = ANCHOR_TIMEOUT_S,
    own_pid: int | None = None,
) -> Rect | None:
    """The frontmost window's bounds, or ``None`` if there is none, the query fails, or it takes too long."""
    own = os.getpid() if own_pid is None else own_pid
    answer: list = []

    def work():
        try:
            answer.append(frontmost_window(query(), own))
        except Exception:  # any failure of the platform query means: no anchor
            answer.append(None)

    worker = threading.Thread(target=work, name="anchor-query", daemon=True)
    worker.start()
    worker.join(timeout)
    if not answer or answer[0] is None:
        return None
    return answer[0]["bounds"]


# -- displays -------------------------------------------------------------------


class _NSRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("width", ctypes.c_double), ("height", ctypes.c_double)]


def visible_displays() -> list[Rect]:
    """Each display's visible area in global top-left-origin points, main display first.

    ``NSScreen`` measures from the bottom-left of the main display with y
    growing upwards; this flips each rectangle about the main display's height.
    """
    objc = ctypes.CDLL(ctypes.util.find_library("objc"))
    ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
    objc.objc_getClass.restype = ctypes.c_void_p
    objc.objc_getClass.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    send = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value

    def msg(restype, *argtypes):
        return ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(send)

    sel = lambda name: objc.sel_registerName(name.encode())  # noqa: E731
    screens = msg(ctypes.c_void_p)(objc.objc_getClass(b"NSScreen"), sel("screens"))
    count = msg(ctypes.c_ulong)(screens, sel("count"))
    rects = []
    for i in range(count):
        screen = msg(ctypes.c_void_p, ctypes.c_ulong)(screens, sel("objectAtIndex:"), i)
        frame = msg(_NSRect)(screen, sel("frame"))
        visible = msg(_NSRect)(screen, sel("visibleFrame"))
        rects.append((frame, visible))
    if not rects:
        return []
    main_frame, main_visible = rects[0]   # screens[0] is the main display, origin (0, 0)
    main_height = main_frame.height
    # NSScreen reports a secondary display's visible area as the whole display even
    # when a menu bar is drawn across its top (measured 2026-09-23: 2560 x 1440
    # visible, with Control Centre's menu-bar items at its top edge). So wherever
    # nothing was taken off the top, take off as much as the main display loses.
    menu_bar = (main_frame.y + main_frame.height) - (main_visible.y + main_visible.height)
    out = []
    for frame, visible in rects:
        top_inset = (frame.y + frame.height) - (visible.y + visible.height)
        height = visible.height - (menu_bar if top_inset <= 0 else 0)
        top = main_height - (visible.y + visible.height) + (menu_bar if top_inset <= 0 else 0)
        out.append(Rect(visible.x, top, visible.width, height))
    return out
