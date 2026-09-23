# The multi-agent workflow (as of the end of run 8)

How this project turns a specification into a finished application: which agents take part, what each one receives and hands on, where the gates are, and where the user comes in.

Every rule shown here comes from `.claude/agents/*.md`, `.claude/shared/*.md` and `docs/IMPLEMENTATION_PLAN.md`. When a diagram and one of those files disagree, the file governs.

---

## 1. The whole run

```mermaid
flowchart TB
  USER(("User"))

  subgraph S1["1 · Setup"]
    direction LR
    FR[/"FUNCTIONAL_REQUIREMENTS.md<br/>49 requirement codes"/]
    ARCH[/"ARCHITECTURE.md<br/>candidate architectures<br/>(architect's output; fixed input in runs 7-8)"/]
    COND["Conductor<br/>(the user's session)"]
    LEAD["Technical lead<br/>(own worktree)"]
    PLAN[/"IMPLEMENTATION_PLAN.md<br/>work items · risk floors ·<br/>CLAIMS (some 'needs eyes')"/]
    FR --> COND
    COND -- "mode · team size ·<br/>candidate · measurements" --> LEAD
    ARCH --> LEAD
    FR --> LEAD
    LEAD -- "writes, lands as<br/>AMEND-0 (LOW PR)" --> PLAN
  end

  subgraph S2["2 · Build, one work item at a time (x3 lanes in parallel)"]
    direction LR
    DEV["Developer<br/>(own worktree, r8/ branch)"]
    PR[/"Pull request<br/>body = the brief:<br/>claims → evidence → diff map →<br/>needs-eyes scripts → status block"/]
    EVID[/"evidence/&lt;ITEM&gt;/<br/>harnesses · observations"/]
    COP["Copilot<br/>(one advisory pass)"]
    DEV -- "code + tests" --> PR
    DEV -- builds --> EVID
    PR -- "ready" --> COP
    COP -- "comments →<br/>REVIEW-REPLY" --> DEV
  end

  subgraph S3["3 · Verify (one verifier per round)"]
    direction LR
    VER["Verifier<br/>(own worktree,<br/>GitHub App identity)"]
    VERD[/"GitHub review at head sha<br/>+ per-claim statuses"/]
    VER -- "re-runs evidence + suite;<br/>controls, diff map, probe by tier" --> VERD
  end

  subgraph S4["4 · Land"]
    direction LR
    MAIN[("main")]
  end

  USER -- "answers setup questions" --> COND
  PLAN -- "read from main" --> DEV
  COND -- "dispatch: item, branch,<br/>verifier login, window rules" --> DEV
  PR -- "VERIFY-REQUEST<br/>(conductor spawns verifier)" --> VER
  EVID --> VER
  VERD -- "REQUEST-CHANGES:<br/>next round" --> DEV
  VERD -- "APPROVE, LOW / MEDIUM:<br/>developer merges" --> MAIN
  VERD -- "APPROVE + HUMAN-GATE<br/>(HIGH or needs eyes)" --> USER
  USER -- "merges = sign-off,<br/>or sends it back" --> MAIN
  VERD -. "BLOCKED → conductor →<br/>lead rules or AMEND-n" .-> LEAD

  classDef agent fill:#e8f0fe,stroke:#3b6fd6,color:#111;
  classDef human fill:#fff4d6,stroke:#c08a00,color:#111;
  classDef art fill:#f3f3f3,stroke:#888,color:#111;
  class COND,LEAD,DEV,COP,VER agent;
  class USER human;
  class FR,ARCH,PLAN,PR,EVID,VERD art;
```

Every run also leaves a trail: each agent's `docs/progress/<branch>.md` log, one `docs/completions/` record per lane per iteration, and `docs/findings/` for measurements worth keeping. The conductor's own log, `docs/progress/conductor.md`, is git-ignored.

---

## 2. One work item, from dispatch to merge

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant C as Conductor
  participant D as Developer
  participant GH as GitHub PR
  participant CP as Copilot
  participant V as Verifier

  C->>D: dispatch (item, branch r8/…, base, verifier login)
  D->>D: START line in docs/progress/<branch>.md
  C->>C: confirm START (dispatching ≠ starting)
  D->>GH: push branch, open DRAFT PR (brief as body)
  D->>D: code, tests, evidence/<ITEM>/, diff map
  D->>GH: mark ready
  GH->>CP: automatic review (~4 min)
  CP-->>GH: comments
  D->>GH: fix or dispute — REVIEW-REPLY on every thread
  D->>GH: comment "VERIFY-REQUEST: <ITEM> round n risk <tier> head <sha>"
  C->>GH: watcher sees the request
  C->>V: spawn (PR number, item, relayed rulings)
  V->>V: check out head detached, build venv
  V->>V: re-run every claim's evidence + full suite
  V->>V: MEDIUM+: controls on base, diff map. HIGH: walk-through, observations, probe
  V->>GH: review (APPROVE / REQUEST-CHANGES) + VERIFIER-STATUS block
  V-->>C: report (worktree, statuses, waiting-on-human)
  C->>C: reap the verifier's worktree

  alt changes requested
    D->>GH: fix, REVIEW-REPLY, new VERIFY-REQUEST (round n+1)
  else approved, LOW or MEDIUM, no needs-eyes claim
    D->>GH: check gate (approval by verifier login, at head) → merge
    D->>D: merge origin/main back, re-run suite, MERGE line
  else approved, HIGH or needs-eyes (HUMAN-GATE)
    D-->>C: "waiting on a human" — never merges
    C->>U: PR link, claims, verifier statuses, 2-minute scripts
    alt user accepts
      U->>GH: merges (or tells the conductor "merge #N", quoted verbatim)
    else user rejects
      U->>C: what they saw
      C->>D: rework round with the user's exact words
    end
  end
```

---

## 3. What each tier owes

The table is the one plan §1.9 must carry.

| | LOW | MEDIUM | HIGH |
|---|---|---|---|
| Claims (the lead's, written before code) | yes | yes | yes |
| Evidence the developer owes | executable | + controls on the base commit | + walk-through + observation |
| Verifier re-runs evidence and suite at the head | yes | yes | yes |
| Verifier runs the suite on the head merged with current `main` | yes | yes | yes |
| Verifier maps every hunk to a claim | — | yes | yes |
| Verifier probes an edge case nobody claimed | — | — | yes |
| **The user** | only for a needs-eyes claim | only for a needs-eyes claim | always: reads the brief, runs the scripts, merges |

A developer or the verifier may **raise** a tier, and nobody may lower one. Plan amendments are always LOW and never go to the user.

---

## 4. Agents at a glance

| Agent | Receives | Produces | Never does |
|---|---|---|---|
| **Conductor** | the specification; mode, team size, candidate and scope from the user | spawns every other agent; relays reports and rulings; brings the user to human gates; `docs/progress/conductor.md` (git-ignored) | merges, writes code, settles conflicts, records a human verdict it was not given in the user's words |
| **Architect** | the specification | `docs/ARCHITECTURE.md` with candidate architectures | (skipped in runs 7 and 8: the architecture is a fixed input) |
| **Technical lead** | the architecture; mode, team size, candidate | the plan: iterations, work items, risk floors, **claims**, needs-eyes marks; `AMEND-n` PRs; rulings on `BLOCKED` | decides file layout, merges work items, lowers a floor |
| **Developer** | a work item, its branch and base, the verifier login | code, tests, `evidence/<ITEM>/`, the brief (PR body), progress log, completion record; merges its own LOW/MEDIUM PR | removes or weakens a plan claim, merges a human-gated PR, mutates working code to watch a test fail |
| **Copilot** | a PR marked ready | one advisory review, never re-run | approves |
| **Verifier** | a PR number and item code | re-run evidence; per-claim statuses (`REPRODUCED`, `HOLLOW`, `CONTROL INVALID`, `NO EVIDENCE`, `NEEDS EYES`, …); a GitHub review under its own identity; the PR's status block | writes or fixes code, merges, speaks for the user |
| **User** | the setup questions; human-gated PRs | answers; the **merge** that signs off HIGH and needs-eyes work | — |

---

## 5. Signals on a pull request

| Marker | Written by | Means |
|---|---|---|
| `VERIFY-REQUEST: <ITEM> round n risk <tier> head <sha>` | developer (or lead, for `AMEND-n`) | ready for the verifier. The conductor spawns one. |
| `REVIEW-REPLY: FIXED <sha>` / `REVIEW-REPLY: DISPUTE` | developer | a Copilot or verifier finding is answered |
| `VERIFY-VERDICT: APPROVE / REQUEST-CHANGES / BLOCKED …` | verifier | the round's result; a real GitHub review bound to the head sha |
| `<!-- VERIFIER-STATUS:BEGIN/END -->` | verifier only | per-claim status at the head it ran, inside the PR body |
| `HUMAN-GATE: <ITEM> — <HIGH / needs eyes: ids>` | verifier | approved by the machine; **the user merges** |
