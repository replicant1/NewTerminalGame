"""Shell layer: the window, the toolkit's event loop, the tick timer, key capture,
the character grid surface and the anchor query.

The only layer that may import ``tkinter`` or any operating-system or windowing
API.  It may import from every layer below it (IMPLEMENTATION_PLAN.md section 1.4).

**Only characters are drawn** (SCRN-2, architecture caution C5). On a Tk
canvas nothing stops a later change drawing an image or a rectangle standing
in for a glyph, so the rule is written here, where a developer will meet it,
and re-checked by ``tests/test_shell_characters_only.py``: the shell creates
canvas text items on a black background and nothing else.
"""
