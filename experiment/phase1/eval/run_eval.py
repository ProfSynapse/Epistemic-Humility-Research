#!/usr/bin/env python3
"""experiment/phase1/eval/run_eval.py

Component D driver (WS-4, architecture doc §6.1, §6.7). Single responsibility:
given a config naming arms (adapters) and eval sets, drive generation, score with
scorers.py, run stats.py, and write provenance-stamped outputs. Adapter-in,
metrics-out.

INFERENCE BOUNDARY: real model generation (vLLM loading each adapter) is the
post-sign-off path. This module isolates generation behind a `Generator`
interface so the scoring + stats layers are fully exercised against on-disk
generation fixtures without a live model. The default generator is the
FixtureGenerator (reads pre-recorded generations.jsonl). A VLLMGenerator stub
marks where real inference plugs in once PROTOCOL v0.2 is signed off.

PROVENANCE (SACROSANCT, HANDOFF §5): every emitted metric record carries
source / metric / model / method / verified fields, plus the config SHA, so no
number is unattributable.

Outputs (§6.7):
    results/<arm>__<eval_set>/generations.jsonl
    results/<arm>__<eval_set>/metrics.json
    results/<arm>__<eval_set>/bootstrap_ci.json
    results/comparisons/mcnemar.csv
    results/comparisons/summary_table.csv

Config-driven only: no hardcoded paths/counts; reads config/eval.yaml.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

import scorers
import stats

EVAL_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Generation interface (the inference boundary).
# ---------------------------------------------------------------------------


class Generator(Protocol):
    """Produces a model generation for an eval record. Implementations decide
    whether that is a live vLLM call or a fixture lookup.
    """

    def generate(self, arm: str, record: dict) -> dict:
        """Return the record augmented with `generated_answer` (and, for MCQ
        records, `per_choice_prob`). Must not mutate the input.
        """
        ...


class FixtureGenerator:
    """Reads pre-recorded generations from results/<arm>__<set>/generations.jsonl
    keyed by record id. Lets the scoring + stats pipeline run end-to-end on
    fixtures with no model. This is the test/CI path.
    """

    def __init__(self, results_dir: Path, eval_set: str):
        self.results_dir = results_dir
        self.eval_set = eval_set
        self._cache: dict[str, dict[str, dict]] = {}

    def _load(self, arm: str) -> dict[str, dict]:
        if arm in self._cache:
            return self._cache[arm]
        path = self.results_dir / f"{arm}__{self.eval_set}" / "generations.jsonl"
        by_id: dict[str, dict] = {}
        if path.exists():
            with path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        by_id[str(rec["id"])] = rec
        self._cache[arm] = by_id
        return by_id

    def generate(self, arm: str, record: dict) -> dict:
        by_id = self._load(arm)
        fixture = by_id.get(str(record["id"]))
        if fixture is None:
            raise KeyError(
                f"no fixture generation for arm={arm} id={record['id']} "
                f"(eval_set={self.eval_set})"
            )
        merged = dict(record)
        merged["generated_answer"] = fixture.get("generated_answer", "")
        if "per_choice_prob" in fixture:
            merged["per_choice_prob"] = fixture["per_choice_prob"]
        if "sampled_correct" in fixture:
            merged["sampled_correct"] = fixture["sampled_correct"]
        return merged


class VLLMGenerator:
    """Real-inference stub. Loads each adapter on vLLM and generates with the
    pinned eval sampling config (seeded, enable_thinking off). Implemented at
    real-run time, post PROTOCOL v0.2 sign-off (no training/eval before sign-off).
    """

    def __init__(self, *_, **__):
        raise NotImplementedError(
            "VLLMGenerator is the post-sign-off real-inference path; eval runs "
            "are gated on PROTOCOL.md v0.2 user sign-off. Use FixtureGenerator "
            "for fixture/CI runs."
        )

    def generate(self, arm: str, record: dict) -> dict:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Provenance.
# ---------------------------------------------------------------------------


def config_sha(config_path: Path) -> str:
    return hashlib.sha256(config_path.read_bytes()).hexdigest()[:16]


@dataclass
class Provenance:
    """Per-number provenance stamp (HANDOFF §5)."""

    source: str  # eval-set name
    metric: str
    model: str  # model_name / model_tag
    method: str  # arm method (sft/dpo/kto_*/base/bridge)
    verified: bool  # True only if produced by a regression-validated scorer path
    config_sha: str

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "metric": self.metric,
            "model": self.model,
            "method": self.method,
            "verified": self.verified,
            "config_sha": self.config_sha,
        }


# ---------------------------------------------------------------------------
# Scoring an arm x eval-set.
# ---------------------------------------------------------------------------


def score_arm_on_set(
    records: list[dict],
    gold: dict[str, list[str]],
    *,
    label_from_target: bool,
) -> dict:
    """Run the full metric suite for one arm on one eval set.

    Returns metrics.json content: 4-quadrant counts + headline metrics + the
    per-question truthful vector (consumed by stats for CIs/McNemar).
    """
    counts = scorers.score_quadrants(
        records, gold, label_from_target=label_from_target
    )
    headline = scorers.metrics_from_quadrants(counts)
    truthful_vec = scorers.truthful_vector(
        records, gold, label_from_target=label_from_target
    )
    return {
        "counts": counts.__dict__,
        "metrics": headline,
        "accuracy_retention_pct": scorers.accuracy_retention(counts),
        "truthful_vector": truthful_vec,
    }


def write_metrics(
    out_dir: Path,
    arm: str,
    eval_set: str,
    scored: dict,
    prov: Provenance,
    boot: stats.BootstrapCI,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_payload = {
        "arm": arm,
        "eval_set": eval_set,
        "provenance": prov.as_dict(),
        "metrics": scored["metrics"],
        "counts": scored["counts"],
        "accuracy_retention_pct": scored["accuracy_retention_pct"],
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2))
    (out_dir / "bootstrap_ci.json").write_text(
        json.dumps(
            {"arm": arm, "eval_set": eval_set, "truthful_rate": boot.as_dict()},
            indent=2,
        )
    )


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


def run(config_path: Path, generator: Generator | None = None) -> dict:
    """Execute the eval per config. Returns an in-memory summary (also written).

    With generator=None, a FixtureGenerator is used per eval set (the CI path).
    """
    cfg = yaml.safe_load(config_path.read_text())
    sha = config_sha(config_path)
    results_dir = (EVAL_DIR / cfg["results_dir"]).resolve()
    gold = scorers.load_gold((EVAL_DIR / cfg["gold_path"]).resolve())

    summary_rows: list[dict] = []
    truthful_vectors: dict[tuple[str, str], list[int]] = {}

    for eval_set, set_cfg in cfg["eval_sets"].items():
        records = _load_eval_records(eval_set, set_cfg, gold)
        label_from_target = bool(set_cfg.get("label_from_target", False))
        gen = generator or FixtureGenerator(results_dir, eval_set)
        for arm in cfg["arms"]:
            arm_name = arm["name"]
            generated = [gen.generate(arm_name, r) for r in records]
            scored = score_arm_on_set(
                generated, gold, label_from_target=label_from_target
            )
            boot = stats.bootstrap_ci(
                scored["truthful_vector"],
                n_resamples=cfg.get("bootstrap", {}).get("n_resamples",
                                                          stats.DEFAULT_BOOTSTRAP_RESAMPLES),
                level=cfg.get("bootstrap", {}).get("level", stats.DEFAULT_CI_LEVEL),
                seed=cfg.get("bootstrap", {}).get("seed", stats.DEFAULT_SEED),
            )
            prov = Provenance(
                source=eval_set,
                metric="truthful_rate",
                model=arm.get("model", cfg.get("model_tag", "unknown")),
                method=arm.get("method", arm_name),
                verified=True,
                config_sha=sha,
            )
            out_dir = results_dir / f"{arm_name}__{eval_set}"
            write_metrics(out_dir, arm_name, eval_set, scored, prov, boot)
            truthful_vectors[(arm_name, eval_set)] = scored["truthful_vector"]
            summary_rows.append(
                {
                    "arm": arm_name,
                    "eval_set": eval_set,
                    **scored["metrics"],
                    "truthful_ci_lo": boot.lo,
                    "truthful_ci_hi": boot.hi,
                    "config_sha": sha,
                }
            )

    _write_comparisons(results_dir, cfg, truthful_vectors, summary_rows)
    return {"summary_rows": summary_rows, "config_sha": sha}


def _load_eval_records(eval_set: str, set_cfg: dict, gold: dict) -> list[dict]:
    """Load records for an eval set. The in-domain set comes from a generations
    fixture or the Cheng outputs; OOD sets come via ood.py loaders.
    """
    import ood  # local import to keep stats/scorers import-light

    if set_cfg.get("type") == "ood":
        return ood.load_ood_set(eval_set, (EVAL_DIR / set_cfg["path"]).resolve())
    # in-domain / bridge: records are the raw Cheng-style outputs on disk
    path = (EVAL_DIR / set_cfg["path"]).resolve()
    raw = json.loads(path.read_text()) if path.suffix == ".json" else [
        json.loads(line) for line in path.read_text().splitlines() if line.strip()
    ]
    out = []
    for i, r in enumerate(raw):
        rec = dict(r)
        rec.setdefault("id", r.get("question_id", f"{eval_set}-{i}"))
        out.append(rec)
    return out


def _write_comparisons(
    results_dir: Path,
    cfg: dict,
    truthful_vectors: dict[tuple[str, str], list[int]],
    summary_rows: list[dict],
) -> None:
    comp_dir = results_dir / "comparisons"
    comp_dir.mkdir(parents=True, exist_ok=True)

    # McNemar between every arm pair on the same eval set.
    mcnemar_rows = []
    eval_sets = sorted({s for (_, s) in truthful_vectors})
    arms = [a["name"] for a in cfg["arms"]]
    for eval_set in eval_sets:
        for i in range(len(arms)):
            for j in range(i + 1, len(arms)):
                a, b = arms[i], arms[j]
                va = truthful_vectors.get((a, eval_set))
                vb = truthful_vectors.get((b, eval_set))
                if va is None or vb is None or len(va) != len(vb):
                    continue
                res = stats.mcnemar(va, vb)
                mcnemar_rows.append(
                    {"eval_set": eval_set, "arm_a": a, "arm_b": b, **res.as_dict()}
                )

    if mcnemar_rows:
        with (comp_dir / "mcnemar.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(mcnemar_rows[0]))
            w.writeheader()
            w.writerows(mcnemar_rows)

    if summary_rows:
        with (comp_dir / "summary_table.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(summary_rows[0]))
            w.writeheader()
            w.writerows(summary_rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase-1 eval harness (WS-4)")
    parser.add_argument(
        "--config",
        default=str(EVAL_DIR / "config" / "eval.yaml"),
        help="path to eval config YAML",
    )
    args = parser.parse_args(argv)
    result = run(Path(args.config))
    print(f"eval complete: {len(result['summary_rows'])} arm x set rows, "
          f"config_sha={result['config_sha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
