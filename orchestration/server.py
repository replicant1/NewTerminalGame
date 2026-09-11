#!/usr/bin/env python3
"""Orchestration monitor: watch a conductor run from a browser.

    /usr/bin/python3 orchestration/server.py [--port 8765]

Then open http://127.0.0.1:8765/

Monitor-only by design.  The run is started and stopped by the Claude session
driving the project; the buttons here write request files into
``orchestration/requests/`` which that session picks up.  Nothing in this file
spawns an agent, kills a process, or writes anywhere inside the project except
``orchestration/``.

Standard library only, matching the project itself.  No build step, no install.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent                       # the project repository
STATIC = HERE / "static"
ARCHIVE = HERE / "archive"               # artifacts copied out of worktrees
REQUESTS = HERE / "requests"             # button presses, for the Claude session

#: Every line type the agent definitions can emit, and how loudly to show it.
#: Anything unrecognised still renders, as "note" -- a log that silently drops
#: lines it does not understand is worse than a noisy one.
LINE_KINDS = {
    "ASK": "ask", "BLOCKED": "ask", "ASSUME": "assume",
    "DISPATCH": "trace", "REPORT": "verify", "MERGE": "good",
    "RISK": "warn", "CONTRADICT": "warn", "MUTATE": "warn",
    "DONE": "good", "COMMIT": "good", "TEST": "good",
    "START": "start", "PLAN": "plan", "READ": "plan", "DRAFT": "plan",
    "WEIGH": "weigh", "DECIDE": "decide", "VERIFY": "verify",
    "TRACE": "trace", "ITERATION": "trace", "ITEM": "trace", "ASSIGN": "trace",
    "NOTE": "note",
}
#: An optional leading UTC stamp, "14:32:07Z  ", written by the agent itself.
STAMP_RE = re.compile(r"^\s*(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})Z\s+")
#: The text after the kind is optional: with the timestamp moved to the front
#: of the line, a bare "START" carries no payload at all.
KIND_RE = re.compile(r"^\s*(?:(?P<item>[A-Z]{1,4}-\d+[a-z]?)\s+)?(?P<kind>[A-Z]{3,10})(?:\s+(?P<text>.*))?$")
#: An ISO timestamp the agent wrote itself, e.g. on a START line.
ISO_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(Z)?")

ACK_FILE = HERE / "archive" / ".acknowledged.json"
SEEN_FILE = HERE / "archive" / ".first-seen.json"
_seen = {}
#: Per-log line counts, so a log that shrinks can be recognised as a new agent
#: overwriting its predecessor's file rather than as lines disappearing.
_gen = {}


def ask_key(text):
    return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:12]


def load_acks():
    try:
        return set(json.loads(ACK_FILE.read_text()))
    except Exception:
        return set()


def save_acks(keys):
    try:
        ACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        ACK_FILE.write_text(json.dumps(sorted(keys)))
    except OSError:
        pass


def load_seen():
    global _seen
    try:
        _seen = json.loads(SEEN_FILE.read_text())
    except Exception:
        _seen = {}


def new_generation(pane_id, count):
    """True when this log has been rewritten from the start.

    Agents are told to overwrite a log file that is not theirs, so a run that
    replaces a predecessor produces a *shorter* file.  Without noticing that,
    a line whose text recurs between runs -- `READ docs/FUNCTIONAL_REQUIREMENTS.md`
    will recur in every run there ever is -- keeps the first run's timestamp
    forever, and the whole column quietly becomes fiction.
    """
    prev = _gen.get(pane_id)
    _gen[pane_id] = count
    if prev is not None and count < prev:
        for key in [k for k in _seen if k.startswith(pane_id + "|")]:
            del _seen[key]
        return True
    return False


def first_seen(pane_id, text):
    """When this line was first observed by the monitor.

    The agents timestamp only their START line, so for every other line the
    honest answer is "when the poller first saw it".  That is accurate to the
    poll interval and is marked as inferred in the UI, so it is never mistaken
    for something the agent claimed.
    """
    key = pane_id + "|" + hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:12]
    if key not in _seen:
        _seen[key] = time.time()
        try:
            SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            SEEN_FILE.write_text(json.dumps(_seen))
        except OSError:
            pass
    return _seen[key]


def sh(args, cwd=ROOT):
    try:
        p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=10)
        return p.stdout.strip()
    except Exception:
        return ""


def parse_log(path, pane_id=""):
    """A progress log to a list of {kind, item, text, ts, tsSource}."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("```"):
            continue
        stamp = None
        sm = STAMP_RE.match(line)
        if sm:
            stamp = (int(sm.group("h")), int(sm.group("m")), int(sm.group("s")))
            line = line[sm.end():]
        m = KIND_RE.match(line)
        if m and m.group("kind") in LINE_KINDS:
            out.append({
                "kind": LINE_KINDS[m.group("kind")],
                "label": m.group("kind"),
                "item": m.group("item") or "",
                "text": (m.group("text") or "").rstrip(),
                "stamp": stamp,
            })
        else:
            # Continuation or free text: attach to the previous entry so a
            # wrapped line is not orphaned into its own row.
            if out:
                out[-1]["text"] += " " + line.strip()
            else:
                out.append({"kind": "note", "label": "", "item": "", "text": line.rstrip()})
    new_generation(pane_id or str(path), len(out))
    today = datetime.datetime.now(datetime.timezone.utc).date()
    for entry in out:
        if entry.get("stamp"):
            # A stamp the agent wrote as it appended the line: authoritative.
            h, mi, sec = entry["stamp"]
            entry["ts"] = datetime.datetime(
                today.year, today.month, today.day, h, mi, sec,
                tzinfo=datetime.timezone.utc).timestamp()
            entry["tsSource"] = "log"
            continue
        m = ISO_RE.search(entry["text"])
        if m:
            try:
                naive = datetime.datetime.strptime(
                    m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M:%S")
                # The agents are told to log ISO8601 and write it in UTC with a
                # trailing Z. Reading that as local time put START an hour or
                # eleven away from the line after it.
                if m.group(3):
                    naive = naive.replace(tzinfo=datetime.timezone.utc)
                entry["ts"] = naive.timestamp()
                entry["tsSource"] = "log"
                continue
            except ValueError:
                pass
        entry["ts"] = first_seen(pane_id or str(path), entry["text"])
        entry["tsSource"] = "seen"
    return out


def session_health():
    """Is the Claude session that owns these worktrees still alive?

    A worktree lock reads "claude agent agent-<id> (pid N ...)", but N is the
    *session* pid, not the agent's -- every lock on this machine carries the
    same one. So it cannot tell you whether a particular agent is running. What
    it does tell you is whether the session hosting the whole run is alive,
    which is worth knowing: if that is gone, every agent is gone with it.
    """
    pid = None
    base = ROOT / ".git" / "worktrees"
    if base.is_dir():
        for d in base.iterdir():
            lock = d / "locked"
            if lock.is_file():
                m = re.search(r"pid (\d+)", lock.read_text(errors="replace"))
                if m:
                    pid = int(m.group(1))
                    break
    alive = None
    if pid:
        try:
            os.kill(pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        except PermissionError:
            alive = True
    return {"pid": pid, "alive": alive}


def worktrees():
    """[(name, path)] for each agent worktree that currently exists."""
    found = []
    base = ROOT / ".claude" / "worktrees"
    if base.is_dir():
        for d in sorted(base.iterdir()):
            if d.is_dir():
                found.append((d.name, d))
    return found


def archive_artifacts():
    """Copy every agent .md/.json out of the worktrees before they are removed.

    Worktrees are deleted between iterations, and anything a developer has not
    committed goes with them.  This is cheap insurance: a mirror under
    orchestration/archive/, refreshed on every poll, keyed by worktree name.
    """
    copied = 0
    for name, path in worktrees():
        for sub in ("docs/progress", "docs/prs", "docs/findings", "docs/completions"):
            src = path / sub
            if not src.is_dir():
                continue
            dst = ARCHIVE / name / sub
            dst.mkdir(parents=True, exist_ok=True)
            for f in src.iterdir():
                if f.is_file() and f.suffix in (".md", ".json"):
                    target = dst / f.name
                    try:
                        if not target.exists() or f.stat().st_mtime > target.stat().st_mtime:
                            shutil.copy2(f, target)
                            copied += 1
                    except OSError:
                        pass
    return copied


def finished_by_log(lines):
    """An agent that has written DONE has said so itself.

    Worktree removal is the other signal, but it lags: a developer reports,
    writes DONE, and its worktree sits there until the conductor tidies up. In
    between, the monitor was still showing it as working.
    """
    for line in reversed(lines):
        if line["label"]:
            return line["label"] == "DONE"
    return False


def silence_state(mtime, live):
    """How long since this log was written -- NOT whether the agent is alive.

    There is no per-agent liveness signal on disk, so this is the honest
    measure and the UI names it as silence rather than as death. An agent can
    be alive and quiet for a long time: one technical lead ran eight minutes
    before writing its first line.
    """
    if not live:
        return "gone"
    if not mtime:
        return "silent"
    age = time.time() - mtime
    if age < 30:
        return "writing"
    if age < 180:
        return "quiet"
    return "silent"


def panes():
    """One pane per agent, in workflow order: architect, lead, then developers."""
    result = []

    for name, filename in (("conductor", "conductor.md"),
                           ("architect", "architect.md"),
                           ("technical-lead", "technical-lead.md")):
        p = ROOT / "docs" / "progress" / filename
        if p.exists():
            result.append({
                "id": name, "title": name, "role": name,
                "source": str(p.relative_to(ROOT)),
                "lines": parse_log(p, name),
                "mtime": p.stat().st_mtime,
                "live": True,
                "state": ("done" if finished_by_log(parse_log(p, name))
                          else silence_state(p.stat().st_mtime, True)),
            })

    # Developers: one pane per worktree, titled by the branch it is on.
    for name, path in worktrees():
        branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path) or "?"
        # A worktree branches from main, which carries every merged work item's
        # log, so globbing *.md here would render the architect, the lead and
        # every finished item into this developer's pane. Show only the log for
        # the branch this worktree is actually on.
        pdir = path / "docs" / "progress"
        logs = []
        if pdir.is_dir():
            own = pdir / (branch + ".md")
            if own.is_file():
                logs = [own]
            else:
                # No log for this branch yet: fall back to the most recently
                # written one, which is the item it is working on.
                cand = sorted(pdir.glob("*.md"), key=lambda f: f.stat().st_mtime)
                logs = cand[-1:] if cand else []
        lines, sources, mtime = [], [], 0
        for f in logs:
            lines.extend(parse_log(f, name + '/' + f.name))
            sources.append(f.name)
            mtime = max(mtime, f.stat().st_mtime)
        result.append({
            "id": name, "title": branch, "role": "developer",
            "source": ", ".join(sources) or "(no log yet)",
            "lines": lines, "mtime": mtime, "live": True,
            "worktree": name,
            "state": "done" if finished_by_log(lines) else silence_state(mtime, True),
        })

    # Panes for worktrees that have been removed, from the archive.
    live = {n for n, _ in worktrees()}
    if ARCHIVE.is_dir():
        for d in sorted(ARCHIVE.iterdir()):
            if d.name in live or not d.is_dir():
                continue
            logs = sorted((d / "docs" / "progress").glob("*.md")) if (d / "docs" / "progress").is_dir() else []
            if not logs:
                continue
            lines = []
            for f in logs:
                lines.extend(parse_log(f, d.name + '/' + f.name))
            # Name it after the work item it was doing, not the agent id --
            # "agent-a03b510f6bc1a4e92" identifies nothing a reader knows.
            title = logs[-1].stem if logs else d.name[:20]
            result.append({
                "id": d.name, "title": title,
                "role": "developer", "source": "archived",
                "lines": lines, "mtime": 0, "live": False, "worktree": d.name,
                "state": "gone",
            })
    return result


def run_clock():
    """When this run began, taken from the agents' own logs.

    The earliest timestamp any agent wrote is the honest anchor: it is when
    work started, not when this monitor was launched or when the page was
    opened. Those three differ by hours and conflating them would make the
    figure meaningless.
    """
    earliest, source = None, ""
    for pane in panes():
        for line in pane["lines"]:
            ts = line.get("ts")
            if not ts:
                continue
            if earliest is None or ts < earliest:
                earliest, source = ts, "%s %s" % (pane["title"], line["label"])
    return {"start": earliest, "source": source, "now": time.time()}


def in_hand():
    """What is actually being worked on right now.

    The progress bar says how far through the plan the project is; this says
    where the work is at this moment: which iteration the conductor opened,
    which items are out with a developer, and the last thing each of them said.
    """
    all_panes = panes()
    by_id = {p["id"]: p for p in all_panes}

    iteration = ""
    conductor = by_id.get("conductor")
    if conductor:
        for line in reversed(conductor["lines"]):
            if line["label"] == "PLAN":
                iteration = line["text"]
                break

    live = {n for n, _ in worktrees()}
    inflight = []
    for p in all_panes:
        if p.get("role") != "developer" or p.get("worktree") not in live:
            continue
        last = p["lines"][-1] if p["lines"] else None
        m = re.match(r"(wi-\d+[a-z]?|s-\d+|hv-\d+)", p["title"], re.I)
        inflight.append({
            "item": m.group(1).upper() if m else p["title"],
            "branch": p["title"],
            "state": p.get("state", ""),
            "mtime": p.get("mtime", 0),
            "last": (last["label"] + "  " + last["text"]) if last else "no log yet",
        })
    inflight.sort(key=lambda x: x["item"])

    waiting = sum(1 for a in asks() if not a["answered"] and not a["cleared"])
    last_merge = ""
    if conductor:
        for line in reversed(conductor["lines"]):
            if line["label"] == "MERGE":
                last_merge = line["text"]
                break

    return {"iteration": iteration, "inflight": inflight,
            "waiting": waiting, "lastMerge": last_merge}


def progress():
    """Roughly how far through the plan the project is.

    The work items come from the plan's own "### WI-n — title" headings, which
    is the list the technical lead actually wrote; an item counts as done when
    a merge commit for it is reachable from main. That is deliberately coarse:
    an item half-built on a branch counts for nothing, because a work item that
    has not landed is not progress anyone can use.
    """
    plan = ROOT / "docs" / "IMPLEMENTATION_PLAN.md"
    if not plan.is_file():
        return {"items": [], "done": 0, "total": 0, "percent": 0, "label": "no plan yet"}

    text = plan.read_text(encoding="utf-8", errors="replace")
    items = []
    for m in re.finditer(r"^###\s+(WI-\d+[a-z]?|S-\d+|HV-\d+)\s*[-—–]+\s*(.*)$", text, re.M):
        items.append({"id": m.group(1), "title": m.group(2).strip()})

    # The gantt block carries the schedule the plan actually asserts: which
    # iteration each item belongs to, and when it starts. Without it the bar
    # lays items out in numeric order and implies a sequence nobody claimed --
    # WI-8 and WI-9 start on the same day and are not one after the other.
    section, starts = None, {}
    sections, durations = {}, {}
    # "excludes weekends" makes the plan's durations working days, not calendar
    # days; the bar chart has to lay them out on the same axis or contiguous
    # work appears to have gaps at every weekend.
    excludes_weekends = bool(re.search(r"^\s*excludes\s+weekends\b", text, re.M | re.I))
    for line in text.split("\n"):
        t = line.strip()
        m = re.match(r"^section\s+(.*)$", t)
        if m:
            section = m.group(1).strip()
            continue
        m = re.match(r"^(WI-\d+[a-z]?|S-\d+|HV-\d+)\b.*?:(.*)$", t)
        if m and section:
            code = m.group(1)
            sections.setdefault(code, section)
            d = re.search(r"(\d{4}-\d{2}-\d{2})", m.group(2))
            if d:
                starts.setdefault(code, d.group(1))
            dur = re.search(r",\s*([\d.]+)\s*d\b", m.group(2))
            durations.setdefault(code, float(dur.group(1)) if dur else 0.0)
    for it in items:
        it["section"] = sections.get(it["id"], "")
        it["start"] = starts.get(it["id"], "")
        it["days"] = durations.get(it["id"], 0.0)

    log = sh(["git", "log", "main", "--oneline"]).lower()
    merged_branches = " ".join(sh(["git", "branch", "--merged", "main"]).split()).lower()

    # Items a developer is holding right now: a live worktree on a branch named
    # after the item. Distinct from "next", which is scheduled but unstarted.
    active = set()
    for name, path in worktrees():
        branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path).lower()
        m = re.match(r"(wi-\d+[a-z]?|s-\d+|hv-\d+)\b", branch)
        if m:
            active.add(m.group(1))
    for it in items:
        n = it["id"].lower()
        stem = n.replace("wi-", "wi-")
        it["active"] = n in active
        it["done"] = (("merge " + stem + "-") in log
                      or (stem + " complete") in log
                      or re.search(r"\b" + re.escape(stem) + r"-\S+", merged_branches) is not None)

    done = sum(1 for i in items if i["done"])
    total = len(items)

    # "Next" is every unfinished item the plan starts on its earliest
    # outstanding day -- items scheduled together are shown together, rather
    # than the lowest-numbered one being singled out as though the rest waited
    # on it.
    # An item being worked on is not "next"; it has already started.
    pending = [i for i in items if not i["done"] and not i["active"]]
    nxt = []
    if pending:
        dated = [i for i in pending if i["start"]]
        if dated:
            first = min(i["start"] for i in dated)
            nxt = [i["id"] for i in dated if i["start"] == first]
        else:
            nxt = [pending[0]["id"]]

    return {
        "items": items, "done": done, "total": total,
        "percent": int(round(100.0 * done / total)) if total else 0,
        "next": nxt,
        "excludesWeekends": excludes_weekends,
        "active": sorted(i["id"] for i in items if i["active"] and not i["done"]),
        "label": ("%d of %d work items merged" % (done, total)) if total else "no plan yet",
    }


def git_state():
    branches = []
    for line in sh(["git", "branch", "--format=%(refname:short)|%(objectname:short)"]).splitlines():
        if "|" in line:
            n, sha = line.split("|", 1)
            branches.append({
                "name": n, "sha": sha,
                "merged": n in sh(["git", "branch", "--merged", "main", "--format=%(refname:short)"]).splitlines(),
                "ahead": sh(["git", "rev-list", "--count", "main.." + n]) or "0",
            })
    return {
        "head": sh(["git", "log", "--oneline", "-1"]),
        "branches": branches,
        "commits": [l for l in sh(["git", "log", "--all", "--oneline", "-25"]).splitlines()],
        "status": [l for l in sh(["git", "status", "--short"]).splitlines()],
        "worktrees": [l for l in sh(["git", "worktree", "list"]).splitlines()],
    }


def artifact_tree():
    """Every agent-produced document, live or archived."""
    items = []

    def add(base, label):
        for sub in ("docs/progress", "docs/prs", "docs/findings", "docs/completions"):
            d = base / sub
            if not d.is_dir():
                continue
            for f in sorted(d.iterdir()):
                if f.is_file() and f.suffix in (".md", ".json"):
                    items.append({
                        "group": label, "name": f.name, "kind": sub.split("/")[-1],
                        "path": str(f.resolve()), "size": f.stat().st_size,
                        "mtime": f.stat().st_mtime,
                    })

    for doc in ("ARCHITECTURE.md", "IMPLEMENTATION_PLAN.md", "FUNCTIONAL_REQUIREMENTS.md",
                "ARCHITECTURE_RECOMMENDATION.md"):
        f = ROOT / "docs" / doc
        if f.is_file():
            items.append({"group": "main", "name": doc, "kind": "design",
                          "path": str(f.resolve()), "size": f.stat().st_size,
                          "mtime": f.stat().st_mtime})
    add(ROOT, "main")
    for name, path in worktrees():
        add(path, name)
    if ARCHIVE.is_dir():
        live = {n for n, _ in worktrees()}
        for d in sorted(ARCHIVE.iterdir()):
            if d.is_dir() and d.name not in live:
                add(d, "archive/" + d.name)
    return items


def asks():
    """Every ASK and BLOCKED line, with where it came from and whether answered."""
    answered = set()
    if REQUESTS.is_dir():
        for f in REQUESTS.glob("*.json"):
            try:
                r = json.loads(f.read_text())
                if r.get("kind") == "answer":
                    answered.add(r.get("question", "")[:120])
            except Exception:
                pass
    acked = load_acks()
    out = []
    for pane in panes():
        lines = pane["lines"]
        for i, line in enumerate(lines):
            if line["kind"] == "ask":
                # The ASSUME that follows says what the agent did in the
                # meantime, which is the first thing you want to know when
                # deciding how urgently to answer.
                assumption = ""
                for nxt in lines[i + 1:i + 3]:
                    if nxt["label"] == "ASSUME":
                        assumption = nxt["text"]
                        break
                out.append({
                    "from": pane["title"], "label": line["label"],
                    "item": line["item"], "text": line["text"],
                    "assumption": assumption,
                    "answered": line["text"][:120] in answered,
                    "key": ask_key(line["text"]),
                    "cleared": ask_key(line["text"]) in acked,
                })
    return out


def pending_requests():
    out = []
    if REQUESTS.is_dir():
        for f in sorted(REQUESTS.glob("*.json")):
            try:
                r = json.loads(f.read_text())
                r["file"] = f.name
                out.append(r)
            except Exception:
                pass
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # keep the console quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)

        if url.path in ("/", "/index.html"):
            return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")

        if url.path == "/api/state":
            archive_artifacts()
            return self._send(200, json.dumps({
                "root": str(ROOT), "now": time.time(),
                "panes": panes(), "git": git_state(), "session": session_health(),
                "progress": progress(), "now": in_hand(), "run": run_clock(),
                "asks": asks(), "requests": pending_requests(),
            }))

        if url.path == "/api/artifacts":
            return self._send(200, json.dumps(artifact_tree()))

        if url.path == "/api/artifact":
            want = pathlib.Path(q.get("path", [""])[0]).resolve()
            # Only ever serve files from inside the project or the archive.
            if not (str(want).startswith(str(ROOT)) and want.is_file()):
                return self._send(403, json.dumps({"error": "outside the project"}))
            return self._send(200, want.read_bytes(), "text/plain; charset=utf-8")

        return self._send(404, json.dumps({"error": "no such endpoint"}))

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(400, json.dumps({"error": "bad json"}))

        if url.path == "/api/request":
            REQUESTS.mkdir(parents=True, exist_ok=True)
            body["at"] = time.time()
            body["handled"] = False
            name = "%d-%s.json" % (int(time.time() * 1000), body.get("kind", "request"))
            (REQUESTS / name).write_text(json.dumps(body, indent=2))
            return self._send(200, json.dumps({"queued": name}))

        if url.path == "/api/ack":
            # Clearing an ASK does not answer it and does not touch the log --
            # the line stays in the agent's record forever. It only says "I
            # have seen this", so the queue shows what still wants attention.
            keys = load_acks()
            if body.get("all"):
                keys |= {a["key"] for a in asks()}
            elif body.get("none"):
                keys = set()
            else:
                keys |= set(body.get("keys") or [])
            save_acks(keys)
            return self._send(200, json.dumps({"cleared": len(keys)}))

        if url.path == "/api/dismiss":
            if body.get("all"):
                n = 0
                if REQUESTS.is_dir():
                    for f in REQUESTS.glob("*.json"):
                        f.unlink()
                        n += 1
                return self._send(200, json.dumps({"removed": n}))
            f = REQUESTS / os.path.basename(body.get("file", ""))
            if f.is_file():
                f.unlink()
            return self._send(200, json.dumps({"ok": True}))

        return self._send(404, json.dumps({"error": "no such endpoint"}))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    ARCHIVE.mkdir(exist_ok=True)
    REQUESTS.mkdir(exist_ok=True)
    load_seen()
    print("orchestration monitor -> http://%s:%d/   (project: %s)" % (args.host, args.port, ROOT))
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
