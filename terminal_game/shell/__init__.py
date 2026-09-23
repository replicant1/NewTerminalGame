"""Shell layer: the window, the toolkit's event loop, the tick timer, key capture,
the character grid surface and the anchor query.

The only layer that may import ``tkinter`` or any operating-system or windowing
API.  It may import from every layer below it (IMPLEMENTATION_PLAN.md section 1.4).
"""
