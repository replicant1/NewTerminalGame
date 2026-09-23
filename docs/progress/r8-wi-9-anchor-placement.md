03:55:29Z  WI-9 START   WI-9 Anchor and placement (Dev C, lane C), branch r8/wi-9-anchor-placement from origin/main b1adc97, non-local mode, MEDIUM floor
03:56:39Z  WI-9 READ    docs/IMPLEMENTATION_PLAN.md §4 WI-9 (C1-C6), §1.8 Q7; README layers; tools/layer_check (shell unrestricted per the lead's ruling relayed by the conductor)
03:56:39Z  WI-9 VERIFY  frontmost application now is Google Chrome (the user's), this session runs under Terminal (pid 17454) via login/zsh/script/claude
03:56:39Z  WI-9 DECIDE  anchor = first on-screen layer-0 window in CGWindowListCopyWindowInfo's front-to-back order, alpha > 0, at least 40x40, not our own pid; ctypes into CoreGraphics/CoreFoundation, because it needs no permission, activates nothing and answers in milliseconds (swift would take ~1 s)
03:56:39Z  WI-9 DECIDE  visible screen areas from NSScreen visibleFrame via the ObjC runtime, flipped to top-left global points, because CGDisplayBounds includes the menu bar and Dock
03:56:39Z  WI-9 DECIDE  both in terminal_game/shell (anchor.py query, placement.py pure policy), because the shell is the platform layer and the policy is only ever used by it
03:59:18Z  WI-9 VERIFY  real window list: 29 windows in 16.9 ms; anchor = a Chrome window on the left display Rect(-3351,-1398,2248,1374) in 1.6 ms; displays: main (0,33,1512,949), left (-3509,-1440,2560,1440), middle (-949,-1440,2560,1440)
03:59:18Z  WI-9 VERIFY  NSScreen gives the secondary displays' visible area as the whole display although Control Centre's menu-bar items sit at y=-1440 height 30; trimming the main display's 33-pt menu bar where nothing was taken off the top
03:59:18Z  WI-9 TEST    default: 403 passed, 0 failed, 1 skipped (tests/test_placement.py 17 passed)
