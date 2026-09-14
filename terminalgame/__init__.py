"""The game process.

This package is the game, and only the game. It never touches the desktop —
no window is moved, titled, sized or closed from in here (architecture caution
C11). The launcher is a separate process and shares no code with this one.
"""
