03:55:29Z  WI-9 START   WI-9 Anchor and placement (Dev C, lane C), branch r8/wi-9-anchor-placement from origin/main b1adc97, non-local mode, MEDIUM floor
03:56:39Z  WI-9 READ    docs/IMPLEMENTATION_PLAN.md §4 WI-9 (C1-C6), §1.8 Q7; README layers; tools/layer_check (shell unrestricted per the lead's ruling relayed by the conductor)
03:56:39Z  WI-9 VERIFY  frontmost application now is Google Chrome (the user's), this session runs under Terminal (pid 17454) via login/zsh/script/claude
03:56:39Z  WI-9 DECIDE  anchor = first on-screen layer-0 window in CGWindowListCopyWindowInfo's front-to-back order, alpha > 0, at least 40x40, not our own pid; ctypes into CoreGraphics/CoreFoundation, because it needs no permission, activates nothing and answers in milliseconds (swift would take ~1 s)
03:56:39Z  WI-9 DECIDE  visible screen areas from NSScreen visibleFrame via the ObjC runtime, flipped to top-left global points, because CGDisplayBounds includes the menu bar and Dock
03:56:39Z  WI-9 DECIDE  both in terminal_game/shell (anchor.py query, placement.py pure policy), because the shell is the platform layer and the policy is only ever used by it
03:59:18Z  WI-9 VERIFY  real window list: 29 windows in 16.9 ms; anchor = a Chrome window on the left display Rect(-3351,-1398,2248,1374) in 1.6 ms; displays: main (0,33,1512,949), left (-3509,-1440,2560,1440), middle (-949,-1440,2560,1440)
03:59:18Z  WI-9 VERIFY  NSScreen gives the secondary displays' visible area as the whole display although Control Centre's menu-bar items sit at y=-1440 height 30; trimming the main display's 33-pt menu bar where nothing was taken off the top
03:59:18Z  WI-9 TEST    default: 403 passed, 0 failed, 1 skipped (tests/test_placement.py 17 passed)
03:59:48Z  WI-9 COMMIT  57082c2 WI-9: the anchor query and the placement policy
03:59:48Z  WI-9 NOTE    draft PR #132
04:00:43Z  WI-9 VERIFY  C6 harness run 1 (one Terminal window, id 21189, opened, process exited, closed by id, visible=false): anchor [322,-1367,597,385] in 23.4 ms owned by Terminal window 21189 = Terminal's bounds {322,-1367,919,-982}; agree True, on the middle (secondary) display
04:00:43Z  WI-9 DECIDE  add the real placement to the C6 report (place(anchor, 400x602, visible_displays()) and which display holds it) so C4 also has a real-desktop demonstration; one more Terminal window
04:01:55Z  WI-9 VERIFY  C6 harness run 2: agree True again; with the real displays the game window is placed at (362,-1327), wholly on display 2, the anchor's display
04:01:55Z  WI-9 DECIDE  NSScreen flip and menu-bar trim moved into pure to_global() so it is tested with the measured numbers (A2); place() with no display raises (A1)
04:01:55Z  WI-9 TEST    default: 406 passed, 0 failed, 1 skipped
04:03:06Z  WI-9 RISK    WI-9 MEDIUM, because it reads other windows and computes a position (plan floor; not raised)
04:03:06Z  WI-9 DRAFT   docs/prs/PR-WI-9-anchor-placement.md: C1-C6 word for word, A1-A2, diff map, WI-13 usage, findings
04:03:06Z  WI-9 CLAIM   C1-C5, A1, A2 executable -- tests/test_placement.py -k <claim>_; C6 executable -- evidence/WI-9/terminal_anchor.py (one Terminal window, reaped)
04:03:24Z  WI-9 REVIEW  marked #132 ready at 04:03:13Z; waiting for Copilot (limit 04:18:13Z)
04:10:23Z  WI-9 REVIEW  Copilot 04:08:23Z 'Changes recommended', 1 thread: rounding a clamped fractional bound can cross the display edge (valid); overview also asked for harness identity/cleanup care
04:10:23Z  WI-9 VERIFY  C6 harness run 3 (with tty identity check): window 21451 provably ours, closed, visible=false; agree True; placed (362,-1327) wholly on display 2
04:10:23Z  WI-9 TEST    default: 408 passed, 0 failed, 1 skipped (tests/test_placement.py 22 passed)
