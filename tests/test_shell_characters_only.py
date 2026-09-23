"""WI-3/C8: the shell draws characters and a black background, and nothing else.

SCRN-2 is a rule, not a fact of the medium, on a Tk canvas (architecture
caution C5, plan §1.1): nothing stops a later change drawing an image or a
rectangle standing in for a glyph. So the rule is re-checked here, on every
default run, against the shell's source: the only drawing call it may make is
``create_text``, and it may create no image.

A guard needs a control: the scanner is also shown catching each forbidden
call in a sample, and reporting how many shell modules it read, so it cannot
pass by reading nothing.
"""

import ast
from pathlib import Path

SHELL = Path(__file__).resolve().parent.parent / "terminal_game" / "shell"

FORBIDDEN_NAMES = {"PhotoImage", "BitmapImage", "image_create", "create_image", "create_bitmap"}


def drawing_violations(source: str, filename: str = "<sample>") -> list[str]:
    """Every call or name in ``source`` that would draw something other than text."""
    found = []
    for node in ast.walk(ast.parse(source, filename)):
        name = None
        if isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.Name):
            name = node.id
        if name is None:
            continue
        if (name.startswith("create_") and name != "create_text") or name in FORBIDDEN_NAMES:
            found.append(f"{filename}:{node.lineno} {name}")
    return found


def shell_sources() -> dict[str, str]:
    return {str(p.relative_to(SHELL.parent.parent)): p.read_text(encoding="utf-8") for p in sorted(SHELL.glob("*.py"))}


def test_the_shell_makes_no_drawing_call_but_create_text():
    sources = shell_sources()
    violations = [v for name, text in sources.items() for v in drawing_violations(text, name)]
    assert violations == []


def test_the_scan_reads_every_shell_module_including_the_window():
    names = set(shell_sources())
    assert "terminal_game/shell/window.py" in names
    assert len(names) >= 6
    # And the window module really does draw, so the scan is looking at the drawing code.
    assert "create_text" in shell_sources()["terminal_game/shell/window.py"]


def test_the_scan_catches_every_kind_of_non_text_drawing():
    sample = (
        "canvas.create_rectangle(0, 0, 10, 19, fill='blue')\n"
        "canvas.create_line(0, 0, 10, 0)\n"
        "canvas.create_oval(0, 0, 4, 4)\n"
        "canvas.create_polygon(0, 0, 1, 1, 2, 0)\n"
        "canvas.create_image(0, 0, image=img)\n"
        "canvas.create_window(0, 0, window=w)\n"
        "img = tk.PhotoImage(file='wall.png')\n"
        "canvas.create_text(0, 0, text='x')\n"
    )
    found = drawing_violations(sample)
    assert [f.split()[-1] for f in found] == [
        "create_rectangle", "create_line", "create_oval", "create_polygon",
        "create_image", "create_window", "PhotoImage",
    ]
