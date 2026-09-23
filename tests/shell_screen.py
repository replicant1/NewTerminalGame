"""Read what actually reached the screen, for the shell's desktop tests. Test support only.

Tk will report whatever it was told (``itemcget`` returns the record, painted
or not), so the shell's claims about the picture are checked against the
framebuffer: ``screencapture`` of the window's own rectangle, taken from Tk's
geometry, decoded here with ``struct`` alone. (Run 7 lost a whole run to a
toolkit that mapped windows and painted nothing while every test passed.)

Nothing here opens, moves or closes a window. ``capture`` photographs a
rectangle; ``windows_of`` lists one process's on-screen windows.
"""

import json
import os
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent


@dataclass
class Image:
    """A decoded 32-bit capture: ``width`` x ``height`` device pixels, rows top first."""

    width: int
    height: int
    data: bytes  # BGRA, top row first

    def rgb(self, x: int, y: int) -> tuple[int, int, int]:
        i = (y * self.width + x) * 4
        b, g, r = self.data[i], self.data[i + 1], self.data[i + 2]
        return r, g, b


def capture_command(x: int, y: int, width: int, height: int, path: str) -> list[str]:
    """The ``screencapture`` command for a rectangle in screen points (no sound, BMP)."""
    return ["/usr/sbin/screencapture", "-x", "-t", "bmp", "-R", f"{x},{y},{width},{height}", path]


def read_bmp(path: str | os.PathLike) -> Image:
    """Decode the 32 bpp BMP that ``screencapture -t bmp`` writes."""
    raw = Path(path).read_bytes()
    if raw[:2] != b"BM":
        raise ValueError(f"{path} is not a BMP")
    offset = struct.unpack_from("<I", raw, 10)[0]
    width, height = struct.unpack_from("<ii", raw, 18)
    bpp = struct.unpack_from("<H", raw, 28)[0]
    if bpp != 32:
        raise ValueError(f"{path}: expected 32 bits per pixel, got {bpp}")
    top_down = height < 0
    height = abs(height)
    stride = width * 4
    pixels = raw[offset: offset + stride * height]
    if not top_down:
        pixels = b"".join(pixels[r * stride:(r + 1) * stride] for r in range(height - 1, -1, -1))
    return Image(width, height, pixels)


def cell_pixels(image: Image, col: int, row: int, cell_w: float, cell_h: float, inset: int = 0):
    """Every (r, g, b) inside cell (col, row), in device pixels, less ``inset`` pixels each side."""
    x0, x1 = round(col * cell_w) + inset, round((col + 1) * cell_w) - inset
    y0, y1 = round(row * cell_h) + inset, round((row + 1) * cell_h) - inset
    return [image.rgb(x, y) for y in range(y0, y1) for x in range(x0, x1)]


def cell_difference(a: Image, b: Image, col: int, row: int, cell_w: float, cell_h: float) -> float:
    """Mean absolute channel difference between the same cell in two captures (0-255)."""
    pa = cell_pixels(a, col, row, cell_w, cell_h)
    pb = cell_pixels(b, col, row, cell_w, cell_h)
    total = sum(abs(p - q) for u, v in zip(pa, pb) for p, q in zip(u, v))
    return total / (3 * len(pa))


def windows_of(pid: int) -> list[dict]:
    """The window server's on-screen windows for ``pid`` (id, layer, name, x, y, width, height)."""
    out = subprocess.run(
        ["/usr/bin/swift", str(HERE / "shell_windows.swift"), str(pid)],
        capture_output=True, text=True, timeout=60, check=True,
    ).stdout
    return json.loads(out)
