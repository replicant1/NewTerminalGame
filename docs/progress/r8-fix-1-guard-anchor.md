05:25:53Z  FIX-1 START   follow-up: characters-only guard false positive on create_string_buffer after WI-3 and WI-9 both landed (main 53e89be red: 1 failed)
05:25:53Z  FIX-1 VERIFY  control: base 53e89be tests/test_shell_characters_only.py -> 1 failed, 2 passed (anchor.py:108 create_string_buffer); default suite 1 failed, 545 passed
05:25:53Z  FIX-1 DECIDE  name the eight non-text canvas item types and the image makers explicitly, because a prefix match catches ctypes names that draw nothing
05:25:53Z  FIX-1 TEST    guard 4 passed; default 547 passed, 0 failed, 1 skipped, 17 deselected
05:29:41Z  FIX-1 NOTE    renamed from r8/wi-3-guard-fix (#134) to r8/fix-1-guard-anchor at the conductor's request; #134 to be closed
05:29:41Z  FIX-1 RISK    FIX-1 MEDIUM, because it changes WI-3/C8's guard (test only); not raised to HIGH: no window code changes
05:29:41Z  FIX-1 CLAIM   A2 executable -- the real window.py source with a create_line/create_rectangle/create_image added in memory is reported
05:29:41Z  FIX-1 TEST    guard 5 passed; default 548 passed, 0 failed, 1 skipped, 17 deselected
05:37:01Z  FIX-1 REVIEW  Copilot 05:33:23Z 'Needs a closer look', no inline findings; overview asks for image-maker coverage (valid: BitmapImage and image_create had no control)
05:37:01Z  FIX-1 DECIDE  add image-maker control and scan string constants for Tcl words and whole create commands (A4), because drawing through tk.call/eval would otherwise pass the guard
05:37:01Z  FIX-1 TEST    guard 7 passed; default 550 passed, 0 failed, 1 skipped, 17 deselected
