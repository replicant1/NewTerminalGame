00:37:53Z  START   WI-2 — window, launcher, two executables; branch wi-2-window-launcher cut from main
00:38:04Z  READ    plan §2 ground rules and §5 WI-2 brief; next: ARCHITECTURE §6.3, §4, §7, §12
00:38:14Z  READ    ARCHITECTURE §4, §6.3, §7, §12 — WIN-3 recipe is measured; adopting it verbatim
00:39:31Z  WI-2 PLAN    window.py = AppleScript island + supervisor; pure decisions (offset, fallback chain, script text) extracted and unit-tested; play + 'Terminal Game' executables; placeholder entry point in loop.py
00:39:31Z  WI-2 ASK     A1 — does WIN-5 mean the window vanishes on the final frame, or when the player presses q? (with the user, unanswered)
00:39:31Z  WI-2 ASSUME  proceeding on the architect's assumption: q exits the child, the supervisor then closes the window. Affects one wait in the supervisor's close path, WI-8, WI-9, human check H2. Cheap to flip.
00:39:45Z  WI-2 NOTE    Terminal window census BEFORE: ids 367, 2486, 2420, 2440 (4 windows). tty reports 'not a tty', os.isatty(0) False — the live smoke will skip for me.
00:44:36Z  WI-2 NOTE    child with stdin not a tty: first bytes ESC]7;BEL then the static screen, exit 0 — cannot block forever without a terminal
00:45:52Z  WI-2 NOTE    draft PR #4 open against main (repo replicant1/NewTerminalGame). Now writing the tests.
00:46:59Z  WI-2 TEST    41 passed, 0 failed, 0 skipped (geometry + script text)
00:49:13Z  WI-2 TEST    69 passed, 0 failed, 0 skipped (adds executables, supervisor sequence, placeholder screen)
00:50:02Z  WI-2 NOTE    about to run the live probe: one window, opened by id, ended with a typed q, closed by that id, census before/after
00:52:38Z  WI-2 NOTE    live probe 1: WIN-3 REPRODUCES — window name read back exactly 'Terminal Game'; tab 40x30, Menlo-Regular 18; child reports '40 columns x 30 rows' from inside; position write landed exactly; closed by captured id; visible false after
00:52:38Z  WI-2 NOTE    CONTRADICTION with ARCHITECTURE 6.3 WIN-5: 'busy of tab 1' is FALSE while the exec'd Python child is running (measured: busy=false, processes=login,Python for 3s of play). The architect's poll would have closed the window a second after opening it.
00:52:38Z  WI-2 NOTE    probe 2: exec /bin/sleep gives busy=true; exec of the Python child gives busy=false. So it is not exec that does it — Terminal does not count a process blocked on tty input as busy.
00:52:38Z  WI-2 NOTE    probe 3: 'count of processes of tab 1' IS a sound exit signal — 3 at 0.25s, 2 while playing, 0 within 0.19s of the child exiting. busy is briefly true at 0.25-0.47s during the exec. Close guard becomes: busy false AND no processes.
00:52:38Z  WI-2 NOTE    probe 3: a closed window stays in Terminal's 'windows' collection (ids grew 3924, 3927, 3930) but its 'visible' goes false — a census must count VISIBLE windows. visible set was [367, 2486] before and after every probe.
00:56:22Z  WI-2 TEST    77 passed, 0 failed, 0 skipped (exit signal changed from busy to busy-or-process-count; close guarded by both)
01:01:37Z  WI-2 NOTE    probe 4: the real supervise() end to end — window opened, survived 3s of play (the old busy poll would have closed it), name 'Terminal Game', closed 0.372s after q, visible census [367, 2486] identical before and after
01:01:37Z  WI-2 NOTE    probe 5: AppleScript window positions and CGDisplayBounds are NOT the same space. Measured 3 points: AS(600,300)=CG y -1140; AS(-898,76)=CG y -1364; AS(-3000,-1000) clamped by AppleScript itself to y 30 = CG -1410. AS y = CG y + 1440, x unchanged — i.e. AS y origin is the top of the topmost display, AS x origin is the main display's left.
01:01:37Z  WI-2 NOTE    probe 5 consequence: the reference (-898,76) IS on a real display (the 2560x1440 to the left) once converted; without the conversion the clamp moved the game to the main display, i.e. to a screen the player was not looking at. AppleScript also refuses y below 30 and clamps silently.
01:02:39Z  WI-2 TEST    88 passed, 0 failed, 0 skipped; supervisor re-run places the window at (-868,106) = reference+30 on the player's own display
01:05:27Z  WI-2 NOTE    live smoke body run once with the tty skip lifted: 2 tests OK against the real Terminal, visible census [367, 2486] before and after
01:05:27Z  WI-2 NOTE    probe 6: ./play itself — window 3984 at (-868,106), name 'Terminal Game', play exited 0 within 0.24s of q, window gone, census unchanged
01:05:27Z  WI-2 NOTE    findings written to docs/findings/WI-2-terminal-window-id.md
01:05:37Z  WI-2 TEST    90 passed, 0 failed, 2 skipped (the live smoke, no controlling tty)
01:07:39Z  WI-2 NOTE    final Terminal census: all windows 367, 2486, 2420, 2440 — the exact four ids held before this run; visible 367, 2486. Every window I opened is closed.
01:07:39Z  WI-2 TEST    90 passed, 0 failed, 2 skipped on /usr/bin/python3 3.9.6; same counts on /opt/homebrew/bin/python3 3.14.7
01:07:39Z  WI-2 NOTE    PR #4 body updated and marked ready for review. Not merged, not approved, not closed — that is the conductor's.
