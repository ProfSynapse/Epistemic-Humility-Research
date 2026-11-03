"""Private output budget accounting: hard GPU-hour and generated-row caps.

The ledger is append-only JSONL under the *shared* artifact root, so smokes and
the real launch count against the same caps.  Generated rows are counted from
the output files themselves (latest observed line count per file), which stays
correct across resumed runs.  Crossing a cap writes ``budget/STOP.json``; every
engine stage then refuses, and the roll-up reports an instrument stop rather
than an improvised partial verdict.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .config import Cell, Layout
from .util import HarnessError, append_jsonl, count_jsonl, read_jsonl, write_json


class Ledger:
    def __init__(self, cell: Cell, layout: Layout):
        self.cell, self.layout = cell, layout
        self.path = layout.local("budget/ledger.jsonl", shared=True)
        self.stop_path = layout.local("budget/STOP.json", shared=True)
        limits = cell.cell["limits"]
        self.max_rows = int(limits["maximum_generated_rows"])
        self.max_seconds = float(limits["maximum_gpu_hours"]) * 3600.0

    # -- reads ---------------------------------------------------------------
    def entries(self) -> list[dict]:
        return read_jsonl(self.path) if self.path.exists() else []

    def rows_by_file(self) -> dict[str, int]:
        latest: dict[str, int] = {}
        for e in self.entries():
            if e["kind"] == "outputs":
                latest[e["file"]] = int(e["rows"])
        return latest

    def generated_rows(self) -> int:
        return sum(self.rows_by_file().values()) + sum(int(e["rows"]) for e in self.entries() if e["kind"] == "probe_rows")

    def gpu_seconds(self) -> float:
        return sum(float(e["seconds"]) for e in self.entries() if e["kind"] == "gpu_seconds")

    def stopped(self) -> dict | None:
        return None if not self.stop_path.exists() else json.loads(self.stop_path.read_text())

    # -- writes ----------------------------------------------------------------
    def stop(self, reason: str, **detail) -> None:
        write_json(self.stop_path, {"reason": reason, "ts": time.time(), "detail": detail,
                                    "generated_rows": self.generated_rows(), "gpu_seconds": self.gpu_seconds()})

    def require_running(self) -> None:
        if (s := self.stopped()) is not None:
            raise HarnessError("BUDGET_STOPPED", f"launch stopped earlier: {s['reason']}")

    def begin_gpu(self, stage: str) -> str:
        token = f"{stage}-{time.time_ns()}"
        append_jsonl(self.path, {"kind": "gpu_start", "token": token, "stage": stage, "ts": time.time()})
        return token

    def settle_orphans(self) -> int:
        """A hard kill leaves a gpu_start with no gpu_seconds. Bill it up to now (conservative:
        it may include idle time before the resume, which can only stop the launch earlier)."""
        entries = self.entries()
        ended = {e.get("token") for e in entries if e["kind"] == "gpu_seconds" and e.get("token")}
        orphans = [e for e in entries if e["kind"] == "gpu_start" and e["token"] not in ended]
        for e in orphans:
            append_jsonl(self.path, {"kind": "gpu_seconds", "stage": e["stage"], "token": e["token"],
                                     "seconds": max(0.0, time.time() - e["ts"]), "orphan": True, "timed_out": False,
                                     "ts": time.time()})
        return len(orphans)

    def reserve(self, stage: str, planned_new_rows: int) -> float:
        """Refuse a stage that cannot fit; return the remaining GPU seconds (timeout)."""
        self.require_running()
        self.settle_orphans()
        if self.generated_rows() + planned_new_rows > self.max_rows:
            self.stop("generated_rows_cap", stage=stage, planned=planned_new_rows, cap=self.max_rows)
            raise HarnessError("BUDGET_ROWS", f"{stage}: {planned_new_rows} more rows would pass the "
                               f"{self.max_rows}-row cap ({self.generated_rows()} used)")
        remaining = self.max_seconds - self.gpu_seconds()
        if remaining <= 0:
            self.stop("gpu_hours_cap", stage=stage)
            raise HarnessError("BUDGET_GPU", f"{stage}: the {self.cell.cell['limits']['maximum_gpu_hours']} h cap is spent")
        append_jsonl(self.path, {"kind": "reserve", "stage": stage, "rows": planned_new_rows, "ts": time.time()})
        return remaining

    def record_outputs(self, rel: str, path: Path) -> int:
        # The physical artifact namespace includes smoke/<tag>. An untagged
        # job-relative key would replace the smoke count when the real run starts.
        rel = str(Path(path).resolve().relative_to(self.layout.artifacts_root.resolve()))
        rows = count_jsonl(path)
        append_jsonl(self.path, {"kind": "outputs", "file": rel, "rows": rows, "ts": time.time()})
        if self.generated_rows() > self.max_rows:
            self.stop("generated_rows_cap", file=rel, cap=self.max_rows)
        return rows

    def bill_probe_rows(self, token, rows):
        # The engine can generate two short gen_stream wiring probes before
        # writing any scored row. Bill their upper bound before launch so a
        # hard kill cannot erase them. A resumed call is conservatively rebilled.
        if rows:
            append_jsonl(self.path, {"kind": "probe_rows", "token": token, "rows": int(rows), "ts": time.time()})

    def add_gpu_seconds(self, stage: str, seconds: float, *, timed_out: bool = False, token: str | None = None) -> None:
        append_jsonl(self.path, {"kind": "gpu_seconds", "stage": stage, "seconds": float(seconds), "token": token,
                                 "timed_out": timed_out, "ts": time.time()})
        if self.gpu_seconds() >= self.max_seconds:
            self.stop("gpu_hours_cap", stage=stage)

    def summary(self) -> dict:
        return {"generated_rows": self.generated_rows(), "max_generated_rows": self.max_rows,
                "gpu_seconds": self.gpu_seconds(), "max_gpu_seconds": self.max_seconds,
                "stopped": self.stopped(), "rows_by_file": self.rows_by_file()}


def planned_new_rows(output: Path, total_expected: int) -> int:
    return max(0, total_expected - count_jsonl(output))
