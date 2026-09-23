"""The shell: the only layer that may import ``tkinter`` or any windowing API.

It owns the window, the character grid drawn in it, key capture, the tick
timer and closing the window (IMPLEMENTATION_PLAN.md §1.4, layer 1).

**Only characters are drawn** (SCRN-2, architecture caution C5). On a Tk
canvas nothing stops a later change drawing an image or a rectangle standing
in for a glyph, so the rule is written here, where a developer will meet it,
and re-checked by ``tests/test_shell_characters_only.py``: the shell creates
canvas text items on a black background and nothing else.
"""
