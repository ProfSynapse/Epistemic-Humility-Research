#!/usr/bin/env python3
"""Amendment AI — training tripwires (prereg §1.5) as a TrainerCallback.

Every CHECK_EVERY steps:
  (a) Sensor integrity: the FROZEN v2 probe's AUROC vs gold on the FIXED audit set
      (audit_set.jsonl, the representative class-balanced set frozen at prepare
      time — the same construct the smoke's C3 used). Read live from the policy at
      the probe-render anchor. < 0.8 => HALT (Goodhart on the sensor).
  (b) Behavior floor: rolling abstain rate over the last CHECK_EVERY steps of the
      reward's per-step log outside [0.10, 0.90] => HALT.
  (c) Degeneracy: schema-invalid fraction over the same window > 0.10 => HALT.

HALT = write <run_dir>/HALT.json (reason + values + step) and set
control.should_training_stop = True. Nothing is deleted. Every check's values are
appended to <run_dir>/audit_log.jsonl regardless of halt.

The probe read reuses amendment_ai_par_reward's live-model read helpers so the
audit AUROC is measured on exactly the sensor surface the reward consumes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from transformers import TrainerCallback

import amendment_ai_par_reward as par

CHECK_EVERY = 100
SENSOR_HALT = 0.80
ABSTAIN_LO, ABSTAIN_HI = 0.10, 0.90
DEGENERACY_HALT = 0.10


def _auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos = int((labels == 1).sum()); neg = int((labels == 0).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    return float((ranks[labels == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


class AmendmentAITripwireCallback(TrainerCallback):
    def __init__(self, run_dir: Path, audit_path: Path, reward_log_path: Path):
        self.run_dir = Path(run_dir)
        self.audit = [json.loads(l) for l in Path(audit_path).open(encoding="utf-8") if l.strip()]
        self.reward_log_path = Path(reward_log_path)
        self.audit_log = self.run_dir / "audit_log.jsonl"
        self.halted = False

    # ---- sensor integrity: live probe read on the fixed audit set ----
    def _sensor_auroc(self) -> float:
        labels = np.array([1 if a["label"] == "known" else 0 for a in self.audit])
        p = np.array([par._read_pregen_p(a["question"]) for a in self.audit])
        # answerable (label=1) should read LOW p; score for answerable = 1 - p
        return _auroc(1.0 - p, labels)

    # ---- behavior + degeneracy: from the reward's per-step log window ----
    def _behavior_window(self, step: int):
        if not self.reward_log_path.exists():
            return None, None, 0
        lo = step - CHECK_EVERY
        abst, sviol, n = 0, 0, 0
        with self.reward_log_path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                ev = json.loads(line)
                if ev.get("step", -1) <= lo:
                    continue
                for r in ev.get("rows", []):
                    n += 1
                    abst += int(bool(r.get("abstained")))
                    sviol += int(not r.get("schema_valid", True))
        if n == 0:
            return None, None, 0
        return abst / n, sviol / n, n

    def _halt(self, control, reason: str, values: dict, step: int):
        self.halted = True
        payload = {"halted_at_step": step, "reason": reason, "values": values,
                   "at": datetime.now(timezone.utc).isoformat()}
        (self.run_dir / "HALT.json").write_text(json.dumps(payload, indent=2))
        control.should_training_stop = True
        print(f"[tripwire] HALT at step {step}: {reason} {values}", flush=True)

    def on_step_end(self, args, state, control, **kwargs):
        step = int(state.global_step)
        if self.halted or step == 0 or step % CHECK_EVERY != 0:
            return control
        auroc = self._sensor_auroc()
        abst, sviol, n = self._behavior_window(step)
        rec = {"step": step, "sensor_auroc": round(auroc, 4),
               "abstain_rate": (None if abst is None else round(abst, 4)),
               "schema_invalid_frac": (None if sviol is None else round(sviol, 4)),
               "window_n": n, "at": datetime.now(timezone.utc).isoformat()}
        with self.audit_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"[tripwire] step {step}: {rec}", flush=True)

        if not np.isnan(auroc) and auroc < SENSOR_HALT:
            self._halt(control, "sensor_integrity_below_0.8",
                       {"sensor_auroc": auroc}, step)
        elif abst is not None and not (ABSTAIN_LO <= abst <= ABSTAIN_HI):
            self._halt(control, "abstain_rate_out_of_band",
                       {"abstain_rate": abst, "band": [ABSTAIN_LO, ABSTAIN_HI]}, step)
        elif sviol is not None and sviol > DEGENERACY_HALT:
            self._halt(control, "schema_invalid_over_10pct",
                       {"schema_invalid_frac": sviol}, step)
        return control
