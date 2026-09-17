# Orchestration monitor

A browser view of a conductor run: what each agent is doing, what it is waiting
on you for, and every document it has produced.

```
/usr/bin/python3 orchestration/server.py        # then open http://127.0.0.1:8765/
```

Standard library only. No install, no build step, no dependencies.

## What it shows

One scrollable pane per agent, in workflow order — conductor, architect,
technical lead, then one per developer — each rendering that agent's append-only progress
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
* **Timeline** — every agent's lines in one column, in time order, instead of
  one pane each. See below.

## The timeline, and how far to trust it

The panes answer "what is this agent doing"; the timeline answers "what
happened, in what order" — the question you actually have when a run has gone
wrong. It is the same lines, drawn from the same panes, merged and sorted by
their stamps.

By default it shows **significant lines from live agents**: `START`, `PLAN`,
`DISPATCH`, `REPORT`, `MERGE`, `ASK`, `BLOCKED`, `DECIDE`, `RISK`, `DONE`.
That is a couple of hundred rows rather than the nine thousand a whole
history holds. Two checkboxes widen it — *every line*, and *finished agents
too* — and the count beside them says how much of the whole you are seeing.

**Two things make the order less trustworthy than a single column implies,
and both are shown rather than hidden:**

* **A stamp an agent recalled rather than read.** Agents are told to take the
  time from `date -u` as they append each line. One that stops doing so
  leaves a signature: its stamps land on exact minutes. Where more than half
  of an agent's stamps do, the timeline says so and names it — on the run in
  this repository, the conductor wrote 84% of its stamps on a round minute
  while the architect and every developer wrote none.
* **A stamp carries a time but no date.** `HH:MM:SSZ` is all an agent writes,
  so every line is placed on today. That is right within one run and wrong
  across several, which is why finished agents are off by default: they are
  from earlier runs and would interleave as though they ran alongside this
  one.

Neither is worth fixing in the monitor. The first is an agent that stopped
following its instructions, and the second is a log format — both belong
upstream of here.

## Which repository it is reporting on

With real pull requests, each developer merges its own PR **on the server**.
Nothing in that path touches this checkout, so local `main` can sit still for
an entire run while the work lands. Run 7 landed seventeen merges while local
`main` was 61 commits behind; the Git tab correctly reported every branch as
unmerged, and the headline read near zero, because it was asking a repository
the run was not using.

So the server now **fetches** at the top of each poll — throttled to once
every twenty seconds, since the page polls every three — and measures merge
state against `origin/main` when the run is using pull requests, and local
`main` when it is not. `run_mode()` already decided which; that decision is
now what picks the branch.

Fetching only moves refs. It never touches the working tree, so it is safe to
do underneath a live run and underneath you.

Two things are shown rather than assumed, at the top of the Git tab:

* **Which branch the merged/ahead answers were measured against.**
* **How far local `main` has drifted from `origin/main`.** Your checkout not
  having the run's code is a real thing to know — you cannot run the suite or
  read the code from a tree that is sixty commits behind — and it is not the
  monitor's business to fix it for you.

If the fetch fails, the tab says so instead of quietly serving yesterday's
refs.

**Why run 6 never showed this.** Its conductor kept its progress log as a
tracked file on `main` and committed it every couple of minutes, and every one
of those commits had to pull first — forty-eight pulls in the reflog. That
housekeeping, which nothing asked for, was the only reason this tool told the
truth. Run 7's conductor had byte-identical instructions and left its log
untracked, and the pulls stopped. Accuracy that rests on a habit an agent does
not know it has is accuracy you will lose without being told.

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
