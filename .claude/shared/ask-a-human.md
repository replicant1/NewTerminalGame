# When you need an answer from a human

Nothing about writing an `ASK` line pauses you. You cannot wait for a reply: an agent has no way to receive one while it runs. So `ASK` records the question and makes it visible — it does not stop the work, and you must decide, deliberately, what to do next.

**Write the `ASK`, then immediately write an `ASSUME`.** The `ASSUME` line says which way you are proceeding and what rests on it:

```
14:32:07Z  ASK     may the game install a Terminal profile? a script cannot remove one
14:32:08Z  ASSUME  no profile; proceeding with the per-window title. Affects section 8,
                   the WIN-3 trace row, and human-check 3 — all cheap to flip
```

Naming the blast radius is the point. An answer that arrives later then has a known set of places to change, instead of sending somebody hunting through a finished document for everything that quietly depended on a guess.

**Never record an assumption as a ruling.** Only an answer actually relayed to you — arriving as a message, in your instructions, or quoted by the technical lead — may be written as a decision, and it is settled the moment it arrives. Do not write "the user ruled…" for something you inferred, and do not withdraw a genuine relayed answer later for want of confirmation: nobody will confirm it twice, and reopening a settled question costs a rewrite in both directions.

If the assumption turns out to be one you cannot sensibly make — the work would be wasted whichever way it went — then stop, report what you need, and leave the rest undone. That is a better outcome than a document built on a coin flip.
