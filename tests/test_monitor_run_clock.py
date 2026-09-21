"""``date_stamped`` in the orchestration monitor: which day a stamp belongs to.

An agent writes ``HH:MM:SSZ`` and no date, so something has to supply one. The
monitor used to supply *today*, which is right only for a log being appended
right now — and wrong silently, because a time is still a time either way.

It was not cosmetic. ``progress()`` counts a work item done when its merge is
reachable since the run began, and takes that beginning from the conductor's
``START``. Dated to today, a finished project reported ``0 of 25``.

These tests pin the consequence rather than the shape: given a log file with a
known mtime, they assert **which day each line lands on**.
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import pathlib

import pytest

SERVER = pathlib.Path(__file__).resolve().parents[1] / "orchestration" / "server.py"


@pytest.fixture(scope="module")
def server():
    """Import server.py without running it. It guards on ``__main__``."""
    spec = importlib.util.spec_from_file_location("monitor_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _log(tmp_path, stamps, mtime):
    """A progress log whose lines carry ``stamps``, aged to ``mtime``."""
    path = tmp_path / "conductor.md"
    path.write_text("".join("%s  NOTE    line\n" % s for s in stamps))
    os.utime(path, (mtime.timestamp(), mtime.timestamp()))
    return path


def _utc(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


def test_a_log_is_dated_from_its_file_not_from_today(server, tmp_path):
    written = datetime.datetime(2026, 9, 17, 2, 38, 54, tzinfo=datetime.timezone.utc)
    path = _log(tmp_path, ["01:25:23Z", "02:38:54Z"], written)
    entries = server.parse_log(path)
    assert _utc(entries[0]["ts"]).date() == datetime.date(2026, 9, 17)
    assert _utc(entries[-1]["ts"]).date() == datetime.date(2026, 9, 17)


def test_the_last_line_lands_on_the_files_own_date(server, tmp_path):
    written = datetime.datetime(2026, 9, 17, 2, 38, 54, tzinfo=datetime.timezone.utc)
    path = _log(tmp_path, ["01:25:23Z", "02:38:54Z"], written)
    last = _utc(server.parse_log(path)[-1]["ts"])
    assert last == written


def test_a_run_over_midnight_steps_the_date_back(server, tmp_path):
    # Written just after midnight; the earlier lines belong to the day before.
    written = datetime.datetime(2026, 9, 18, 0, 20, 0, tzinfo=datetime.timezone.utc)
    path = _log(tmp_path, ["23:10:00Z", "23:55:00Z", "00:05:00Z", "00:20:00Z"], written)
    days = [_utc(e["ts"]).date() for e in server.parse_log(path)]
    assert days == [datetime.date(2026, 9, 17), datetime.date(2026, 9, 17),
                    datetime.date(2026, 9, 18), datetime.date(2026, 9, 18)]


def test_stamps_stay_in_order_across_that_boundary(server, tmp_path):
    written = datetime.datetime(2026, 9, 18, 0, 20, 0, tzinfo=datetime.timezone.utc)
    path = _log(tmp_path, ["23:10:00Z", "23:55:00Z", "00:05:00Z", "00:20:00Z"], written)
    stamps = [e["ts"] for e in server.parse_log(path)]
    assert stamps == sorted(stamps), "a log read out of order is worse than none"


def test_two_midnights_step_back_twice(server, tmp_path):
    written = datetime.datetime(2026, 9, 19, 1, 0, 0, tzinfo=datetime.timezone.utc)
    path = _log(tmp_path, ["10:00:00Z", "02:00:00Z", "01:00:00Z"], written)
    days = [_utc(e["ts"]).date() for e in server.parse_log(path)]
    assert days == [datetime.date(2026, 9, 17), datetime.date(2026, 9, 18),
                    datetime.date(2026, 9, 19)]


def test_a_live_log_still_lands_on_today(server, tmp_path):
    """The old behaviour was right for this case, and has to survive."""
    now = datetime.datetime.now(datetime.timezone.utc)
    path = _log(tmp_path, [now.strftime("%H:%M:%SZ")], now)
    assert _utc(server.parse_log(path)[0]["ts"]).date() == now.date()


def test_a_line_with_no_stamp_is_left_to_the_seen_clock(server, tmp_path):
    """Dating is for stamps. An unstamped line keeps its ``seen`` fallback,
    which is honest about being the time the monitor noticed the line rather
    than the time an agent wrote it."""
    path = tmp_path / "conductor.md"
    path.write_text("# Conductor\n\nprose with no stamp at all\n")
    sources = [e["tsSource"] for e in server.parse_log(path) if e.get("ts")]
    assert sources and set(sources) == {"seen"}


def test_dating_does_not_disturb_an_iso_line(server, tmp_path):
    """A line carrying a full ISO date already knows its day; leave it."""
    written = datetime.datetime(2026, 9, 17, 2, 38, 54, tzinfo=datetime.timezone.utc)
    path = tmp_path / "conductor.md"
    path.write_text("VERIFY  ran at 2026-09-14T09:00:00Z and it was green\n")
    os.utime(path, (written.timestamp(), written.timestamp()))
    entry = server.parse_log(path)[0]
    assert _utc(entry["ts"]).date() == datetime.date(2026, 9, 14)


class TestWhenTheRunEnded:
    """``run_clock`` has to know a finished run from a running one.

    Without an end it reports ``start`` and the caller counts to *now*, so a
    run that took an hour and a quarter on 17 September read ``100h`` four days
    later — a number that says how long ago it was under a label that says how
    long it took.
    """

    def _conductor(self, tmp_path, lines, mtime):
        d = tmp_path / "docs" / "progress"
        d.mkdir(parents=True)
        path = d / "conductor.md"
        path.write_text("".join(lines))
        os.utime(path, (mtime.timestamp(), mtime.timestamp()))
        return path

    def test_a_done_line_ends_the_run(self, server, tmp_path):
        written = datetime.datetime(2026, 9, 17, 2, 38, 54, tzinfo=datetime.timezone.utc)
        path = self._conductor(tmp_path, [
            "01:25:23Z  START   run 7\n",
            "02:38:54Z  DONE    RUN COMPLETE\n",
        ], written)
        entries = server.parse_log(path)
        start = next(e["ts"] for e in entries if e["label"] == "START")
        end = next(e["ts"] for e in entries if e["label"] == "DONE")
        assert end - start == 73 * 60 + 31, "run 7 took 1h13m31s"

    def test_a_run_with_no_done_has_not_ended(self, server, tmp_path):
        now = datetime.datetime.now(datetime.timezone.utc)
        path = self._conductor(tmp_path, [
            now.strftime("%H:%M:%SZ") + "  START   a run in progress\n",
        ], now)
        entries = server.parse_log(path)
        assert not [e for e in entries if e["label"] == "DONE"]


class TestAnUnstampedTail:
    """The mtime belongs to the last *line*, not the last *stamp*.

    ``parse_log`` keeps unstamped lines — prose, a wrapped continuation, a note
    somebody appended without reading the clock. One of those written after the
    final stamp carries the file's date forward with it, and if the tail crossed
    a midnight the anchor is a day ahead of the stamp it is pinning.
    """

    def test_a_tail_written_after_midnight_does_not_drag_the_log_forward(
            self, server, tmp_path):
        path = tmp_path / "conductor.md"
        path.write_text(
            "23:10:00Z  START   a run that began before midnight\n"
            "23:55:00Z  DONE    and finished before it too\n"
            "a note somebody appended afterwards, with no stamp on it\n"
        )
        # The note was written at 00:20 the next day; the last stamp was not.
        written = datetime.datetime(2026, 9, 18, 0, 20, 0,
                                    tzinfo=datetime.timezone.utc)
        os.utime(path, (written.timestamp(), written.timestamp()))

        days = [_utc(e["ts"]).date() for e in server.parse_log(path)
                if e.get("stamp")]
        assert days == [datetime.date(2026, 9, 17)] * 2, (
            "an unstamped tail past midnight dated every stamped line a day late"
        )

    def test_an_ordinary_log_is_not_dragged_backwards_by_the_slack(
            self, server, tmp_path):
        """The minute of slack must not fire on a normal log."""
        written = datetime.datetime(2026, 9, 17, 2, 38, 54,
                                    tzinfo=datetime.timezone.utc)
        path = _log(tmp_path, ["01:25:23Z", "02:38:54Z"], written)
        days = [_utc(e["ts"]).date() for e in server.parse_log(path)]
        assert days == [datetime.date(2026, 9, 17)] * 2


class TestRunClock:
    """``run_clock`` itself, with the panes stubbed.

    The tests above parse a ``DONE`` line; none of them asks ``run_clock`` what
    it made of one. A regression in that wiring — the field renamed, the loop
    breaking early, ``finished`` never set — would have passed the whole suite.
    """

    def _pane(self, role, lines, live=True):
        out = []
        for label, ts in lines:
            out.append({"label": label, "ts": ts, "text": label})
        return {"role": role, "lines": out, "live": live, "title": role}

    def test_a_done_freezes_the_clock(self, server, monkeypatch):
        monkeypatch.setattr(server, "panes", lambda: [
            self._pane("conductor", [("START", 1000.0), ("DONE", 5000.0)])])
        clock = server.run_clock()
        assert clock["start"] == 1000.0
        assert clock["end"] == 5000.0
        assert clock["finished"] is True

    def test_a_run_still_going_has_no_end(self, server, monkeypatch):
        monkeypatch.setattr(server, "panes", lambda: [
            self._pane("conductor", [("START", 1000.0), ("REPORT", 2000.0)])])
        clock = server.run_clock()
        assert clock["start"] == 1000.0
        assert clock["end"] is None
        assert clock["finished"] is False

    def test_the_last_done_wins(self, server, monkeypatch):
        """A conductor overwrites its log each run, but a resumed one can
        write two. The clock stops at the last."""
        monkeypatch.setattr(server, "panes", lambda: [
            self._pane("conductor",
                       [("START", 1000.0), ("DONE", 4000.0), ("DONE", 6000.0)])])
        assert server.run_clock()["end"] == 6000.0

    def test_with_no_conductor_it_falls_back_and_is_not_finished(
            self, server, monkeypatch):
        monkeypatch.setattr(server, "panes", lambda: [
            self._pane("developer", [("START", 3000.0), ("DONE", 9000.0)])])
        clock = server.run_clock()
        assert clock["start"] == 3000.0
        assert clock["finished"] is False, (
            "only a conductor's DONE ends a run; a developer finishing does not"
        )
