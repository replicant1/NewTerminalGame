"""The screen edge of the game process.

`port` is the interface the rest of the game speaks; `curses_adapter` is the
only module in the whole system that knows the `curses` module exists.
Nothing above the port imports curses.
"""
