"""The six colour roles and the colour the shell paints each one in.

Pure data; no toolkit. The roles are named in IMPLEMENTATION_PLAN.md §4:
wall blue, dot dim gold, player bright yellow, ghost pink, status cyan,
background black. The exact values are the shell's to choose.
"""

WALL = "wall"
DOT = "dot"
PLAYER = "player"
GHOST = "ghost"
STATUS = "status"
BACKGROUND = "background"

ROLES = (WALL, DOT, PLAYER, GHOST, STATUS, BACKGROUND)

#: Role name -> Tk colour. A frame names a role; the shell alone knows its colour.
COLOURS = {
    WALL: "#2121de",        # the classic maze blue
    DOT: "#b8860b",         # dark goldenrod: gold, and dimmer than the player
    PLAYER: "#ffff00",      # bright yellow
    GHOST: "#ffb8ff",       # pink
    STATUS: "#00ffff",      # cyan
    BACKGROUND: "#000000",  # black
}


def colour_of(role: str) -> str:
    """The colour for ``role``. Raises ``ValueError`` naming an unknown role."""
    try:
        return COLOURS[role]
    except (KeyError, TypeError):
        raise ValueError(f"unknown colour role {role!r}; expected one of {ROLES}") from None
