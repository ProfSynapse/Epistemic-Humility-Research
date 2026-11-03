"""Thin, budget-aware wrapper around the installed host ``EngineCLI``.

Every MechInterp call goes through ``engine_host.cli_boundary.EngineCLI``.  The
host's ``run`` accepts explicit stdout/stderr streams, so JSON-emitting
verbs write directly into their private result file without process-wide file
 descriptor changes.  Authority flags are never added implicitly: ``--i-know-this-runs-on-gpu``
is passed only when the operator gave ``gpu_ack``.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .budget import Ledger
from .util import HarnessError



def parse_json_text(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            raise HarnessError("ENGINE_OUTPUT", "engine produced no JSON document")
        return json.JSONDecoder().raw_decode(text[start:])[0]


class Engine:
    def __init__(self, project_root: Path, plugin_roots, ledger: Ledger | None = None, *, cli=None):
        if cli is None:
            from engine_host.cli_boundary import EngineCLI

            cli = EngineCLI(Path(project_root), plugin_roots=tuple(plugin_roots))
        self.cli = cli
        self.ledger = ledger

    # -- JSON verbs ------------------------------------------------------------
    def run_json(self, args: list[str], out_path: Path) -> tuple[int, dict | None]:
        """Run a CPU JSON verb; stdout lands in ``out_path``. Returns (rc, document)."""
        rc = 0
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("wb") as sink:
                self.cli.run("mechinterp", args, stdout=sink)
        except subprocess.CalledProcessError as exc:
            rc = exc.returncode
        text = Path(out_path).read_text(encoding="utf-8", errors="replace") if Path(out_path).exists() else ""
        try:
            return rc, parse_json_text(text) if text.strip() else None
        except HarnessError:
            return rc, None

    # -- GPU verbs -------------------------------------------------------------
    def run_gpu(self, stage: str, args: list[str], *, gpu_ack: bool, planned_rows: int = 0) -> int:
        """Budget-gated engine call. Raises on refusal; returns the process exit code."""
        if self.ledger is None:
            raise HarnessError("LEDGER", "GPU stages require a budget ledger")
        if not gpu_ack:
            raise HarnessError("GPU_ACK", f"{stage}: pass --gpu-ack to authorize launching the GPU verb")
        # Inherited advisory lock stays held by the child until it exits, even
        # if the harness is killed. Parent-death guarding stops that child too.
        import fcntl
        lock_path = self.ledger.layout.local("budget/gpu-writer.lock", shared=True)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise HarnessError("ACTIVE_WRITER", "another engine owns the shared GPU ledger") from exc
            from .integrity import verify
            verify(self.ledger.cell, self.ledger.layout)
            timeout = self.ledger.reserve(stage, planned_rows)
            full = list(args) + ["--i-know-this-runs-on-gpu"]
            token = self.ledger.begin_gpu(stage)
            start, timed_out, rc = time.monotonic(), False, 0
            try:
                self.cli.run("mechinterp", full, timeout=timeout, guard_parent=True, pass_fds=(lock.fileno(),))
            except subprocess.TimeoutExpired:
                timed_out, rc = True, 124
            except subprocess.CalledProcessError as exc:
                rc = exc.returncode
            finally:
                elapsed = time.monotonic() - start
                # A timeout means the remaining budget was fully spent, whatever the clock says.
                self.ledger.add_gpu_seconds(stage, max(elapsed, timeout) if timed_out else elapsed, timed_out=timed_out, token=token)
        if timed_out:
            self.ledger.stop("gpu_hours_cap", stage=stage, note="engine call killed at the cap; no partial verdict")
            raise HarnessError("BUDGET_GPU", f"{stage}: stopped at the GPU-hour cap; no partial verdict")
        return rc
