# Progress Tracking

Create a suitably named (human readble) append-only log at `docs/progress/`, appended **as you go** — never written up at the end, which would defeat the point.

**Every line begins with a UTC timestamp.** The format is `HH:MM:SSZ` followed by two spaces, then the line as described below:

```
14:32:07Z  START   ...
14:32:09Z  READ    ...
```

Get it from the clock, not from memory — `date -u +%H:%M:%SZ` — and write it at the moment you append the line, never backfilled. The reader is watching a run unfold and needs to know when each thing actually happened; a stamp invented after the fact is worse than none, because it looks authoritative. Keep the `Z`: it says the time is UTC and stops it being read as local.

One line each, at least these moments:

- `START` — you have begun
- `READ    <what you read>` — the specification, an existing document, a file in the repository
- `WEIGH   <the choice> : <the options>` — a decision you are actively considering
- `DECIDE  <the choice> -> <what you chose>, because <one clause>` — and the reason, always
- `VERIFY  <what you measured> -> <the result>` — anything you actually ran or checked rather than assumed
- `DRAFT   <section>` — a section of the document written
- `RISK    <what could go wrong>` — a risk as you identify it, not saved up for the end
- `ASK     <what you need from a human>` — the moment you know, not when you finish
- `ASSUME  <which way you are proceeding, and what depends on it>` — always straight after an `ASK`
- `DONE    <document path>`

Prefix nothing; the line type is the prefix. Keep each to one line.

**Write the log from the first moment, not from the first result.** Put the `START` line down *before* you read anything — it is the signal that you exist and have begun. Then append each `READ` as you finish that file, not all of them at the end.

**Never go more than a few minutes without a line.** If you are in a long stretch of reading, thinking or drafting, say so as you go: one line per file read, one per section drafted, one per decision reached. A watcher cannot tell a long think from a crashed agent, and the whole purpose of this log is that somebody can help you while you still need helping. Silence is the one thing it must never contain.

Two consequences worth stating plainly:

- **A log written up at the end is worse than no log**, because it arrives after every moment at which it could have changed anything.
- **If a log file already exists when you start, it is not yours** — it belongs to an earlier agent, possibly one that was stopped. Overwrite it with your own `START` line rather than appending to it, or your first line will read as a continuation of somebody else's work.

`VERIFY` is the most valuable line you write. If you prototype a generator, parse a scripting dictionary, or check what a library actually does, say so on a `VERIFY` line with the number you got — the reader needs to know which parts were tested and which were reasoned.

## Other instructions
Instructions in the following shared files also apply:
- .claude/shared/ask-a-human.md