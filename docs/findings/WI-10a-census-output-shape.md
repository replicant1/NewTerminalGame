# WI-10a — what `osascript` prints for the window census

Measured 2026-09-11 on macOS 25.6.0 (Darwin), Terminal.app, `/usr/bin/osascript`.

WI-10a replaced the census

```applescript
tell application "Terminal"
	set out to ""
	repeat with w in windows
		if visible of w then set out to out & (id of w as text) & linefeed
	end repeat
	return out
end tell
```

with

```applescript
tell application "Terminal" to get id of every window whose visible is true
```

The old one returned a **string** the script had built by hand. The new one
returns a **list**, and `osascript` prints a list its own way. That is a change
of wire format, so it was measured rather than assumed.

## The three shapes

| visible windows | stdout, raw | exit status | `parse_window_ids` |
| --- | --- | --- | --- |
| two | `367, 2486\n` | 0 | `[367, 2486]` |
| one | `367\n` | 0 | `[367]` |
| none | `\n` | 0 | `[]` |

Commands, verbatim:

```
$ /usr/bin/osascript -e 'tell application "Terminal" to get id of every window whose visible is true'
367, 2486

$ /usr/bin/osascript -e 'tell application "Terminal" to get id of every window whose id is 367' | od -c
0000000    3   6   7  \n

$ /usr/bin/osascript -e 'tell application "Terminal" to get id of every window whose visible is true and name is "___no_such_window___"' | od -c
0000000   \n
```

The last is the case worth checking hardest and it is the one a reader is most
likely to get wrong from memory: an **empty list is not an error and not an
empty accumulator string**. `osascript` prints a bare newline and exits 0.
`run_osascript` strips it to `""`, and `parse_window_ids("")` is `[]` — "no
visible windows", which is the truth.

## Why nothing downstream had to change

`parse_window_ids` already replaced `,` with a linefeed before splitting, so it
parses the comma-separated list as readily as the linefeed-separated string it
was written for. Its only caller, `visible_window_ids()`, therefore still gets
a list of ints. Nothing depends on the order: both assertions in
`tests/test_launch_smoke.py` sort it, and the smoke compares sets of ids.

## Separately: the all-windows census still grows across a close

Confirmed again while verifying WI-10a, and it is the reason the *visible*
census exists at all (WI-2):

```
before:  367, 2420, 2440, 2486
after:   367, 2420, 2440, 2486, 4632     <- 4632 was opened and closed
visible: 367, 2486                        <- both before and after
```

A closed window stays in `id of every window` and merely goes invisible. A
census over all windows can therefore never reconcile across a close; a census
over visible ones does, and did, in every round.

## What was *not* reproduced

The `Invalid index. (-1719)` failure itself. WI-10 observed it; four
open/close/census rounds here did not trigger it, which is what "race" means.
What these rounds did establish is that the new census agrees with the old one
exactly, on an undisturbed screen and immediately after a close, so the change
is behaviour-preserving where the old form worked at all.
