# Orchestration monitor

A browser view of a conductor run: what each agent is doing, what it is waiting
on you for, and every document it has produced.

```
/usr/bin/python3 orchestration/server.py        # then open http://127.0.0.1:8765/
```

Standard library only. No install, no build step, no dependencies.

## What it shows

One scrollable pane per agent, in workflow order — architect, then technical
lead, then one per developer — each rendering that agent's append-only progress
log with the line types colour-coded. `ASK` and `BLOCKED` are highlighted,
because those are the ones that stall a run.

The right-hand panel has three tabs:

* **Asks** — every `ASK` and `BLOCKED` line pulled out of every log into one
  queue, with a box to type an answer. Also lists requests queued for the
  Claude session.
* **Files** — every document any agent has written: progress logs, PR
  summaries, findings, completion records, and the design documents. Click to
  read it in the browser.
* **Git** — HEAD, branches with merged/ahead status, the working tree, the
  worktree list, and recent commits across all branches.

## Monitor, not driver

The tool does not start or stop agents. It cannot: agents are spawned by the
Claude session working on the project, through tools this server has no access
to. **Start**, **Stop** and **Send answer** write a JSON file into
`orchestration/requests/`, which that session reads and acts on. They therefore
work while the conversation is live, and do nothing when it is not.

That is a deliberate choice rather than a limitation to route around. A run
started here would be a second, unsupervised session, and the things that have
gone wrong in practice — a launcher opening dialogs on the screen, a developer
blocked on an unmerged file, an architect asking a question nobody answered —
were all caught by the supervising session, not by a log.

## Worktrees, and why there is an archive

Developers work in `.claude/worktrees/agent-*/`, each a separate checkout, so
their progress logs are **not** in the main `docs/progress/` until their branch
merges. The monitor reads both, and mirrors everything it finds into
`orchestration/archive/<worktree>/` on every poll.

That mirror is the point: a worktree is removed when its developer finishes or
is stopped, and anything uncommitted disappears with it. The archive keeps the
record, and finished agents keep a pane, greyed out.

Permissions need no special handling — every worktree is a plain directory in
the repository owned by the same user as the server.

## Safety

`/api/artifact` resolves the requested path and refuses anything outside the
project directory, so the file browser cannot be used to read the rest of the
disk. The server binds to 127.0.0.1 by default. Nothing here writes to the
project: the only paths it creates are `orchestration/archive/` and
`orchestration/requests/`.
