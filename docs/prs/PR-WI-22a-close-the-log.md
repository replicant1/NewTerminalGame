# WI-22a — close WI-22's progress log

Documents only. No code, no tests, no behaviour.

WI-22 merged as [#64](https://github.com/replicant1/NewTerminalGame/pull/64) and its
progress log needed three more lines after the merge: the `MERGE` line, the post-merge
`TEST` count, and the `DONE` line. The first two went into #64's branch before it landed;
these did not, and this branch carries them.

It also carries a repair the log has to own rather than hide. **Three early lines never
reached the file** — two `READ` lines and the `TEST` line holding the pre-change baseline.
They were written with a brace-group append (`{ printf …; printf …; } >> file`) that
silently wrote nothing, and the loss was only noticed when the finished log was read back.

Backfilling them with their original timestamps would have been the wrong repair: a stamp
invented after the fact looks authoritative and is not. So the log now says what happened,
at the time that sentence was written, and restates the lost measurement as a `VERIFY`
line with the time it was *recorded* rather than the time it was *taken*:

```
NOTE    three early lines never reached this file … Not backfilled.
VERIFY  baseline before any edit, measured at about 05:33Z on main at 238f4dd
        -> 740 passed, 0 failed, 0 skipped
```

That baseline is the same number quoted in #64's body and in
`docs/completions/COMPLETION-M5-DEV-B.md`, and the same one the conductor's brief gave for
`main`. It is recoverable independently: `main` at `238f4dd` still runs 740.

## Suite

Unchanged by this branch, and re-run on it anyway:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

**747 passed, 0 failed, 0 skipped.**

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
