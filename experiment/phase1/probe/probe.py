#!/usr/bin/env python3
"""Phase 1 knowledge probe (Component A, WS-1).

Location: experiment/phase1/probe/probe.py
Reads:    experiment/phase1/probe/config/probe.yaml (pinned sampling config)
          datasets/triviaqa-rc-nocontext/train.jsonl (WS-0 fetch output)
Writes:   experiment/phase1/probe/<model_tag>/probe_results.jsonl  (A -> B contract)
          experiment/phase1/probe/<model_tag>/probe_manifest.json
          experiment/phase1/probe/<model_tag>/sensitivity_grid.json

One job: for every TriviaQA train-split question, estimate this model's
P_correct under its own generation and capture its wrong answers (the
downstream KTO/DPO negatives). It does NOT build training files (that is WS-2).

The probe is checkpointed and resumable: per-row results are appended to
probe_results.jsonl keyed by probe_pool_row_key; on restart, rows already
present are skipped. Per-question seeds are derived from the master seed plus
the question_id so a resumed run reproduces skipped questions exactly.

Real runs use the vLLM backend on a GPU and are gated on PROTOCOL.md v0.2
user sign-off. This module is importable and unit-testable with the stub
backend on a machine with no GPU and no network (see tests/).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from backends import (
    assert_no_generated_thinking,
    assert_no_generated_thinking_batch,
    build_backend,
)
from scoring import is_correct, normalize_question, p_correct

# Repo root is four levels up from this file
# (experiment/phase1/probe/probe.py -> worktree root).
REPO_ROOT = Path(__file__).resolve().parents[3]


def _rel(path: Path) -> str:
    """Path relative to REPO_ROOT for display, or absolute if outside it.

    Outputs normally land under the worktree, but tests write to a tmp dir
    outside REPO_ROOT; display must not raise there.
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def config_sha(config: dict) -> str:
    """Stable hash of the pinned config, stamped into every output row."""
    blob = json.dumps(config, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def derive_seed(master_seed: int, question_id: str) -> int:
    """Deterministic per-question seed so resumed runs reproduce exactly."""
    key = f"{master_seed}|{question_id}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_pool_path(config: dict) -> Path:
    """Resolve the probe pool path, honoring the documented fallback.

    Primary: the train split (WS-0). Fallback: the validation-remainder path
    if the config sets it (a recorded deviation; the leakage guard downstream
    makes it safe). The fallback path is used verbatim if present.
    """
    pool = config["probe_pool"]
    fallback = pool.get("fallback_validation_remainder")
    rel = fallback if fallback else pool["train_jsonl"]
    return (REPO_ROOT / rel).resolve()


def make_pool_row_key(source_index: int, question_id: str) -> str:
    """Stable row identity for pools where question_id is not unique."""
    return f"{source_index:012d}|{question_id}"


def iter_pool(pool_path: Path, id_prefix: str):
    """Yield one normalized probe-pool tuple per non-empty source row.

    TriviaQA train rows carry question, question_id, answer.normalized_aliases
    (lowercased) and answer.value (natural-case gold). The probe scores against
    the normalized aliases (normalization-invariant), but propagates answer.value
    so the downstream builder can use natural-case gold as the `known` target
    instead of a lowercased alias. answer_value is None if the row omits it
    (e.g. a custom fixture); callers fall back to the first alias.

    If a row lacks question_id, synthesize a stable one from the row index.
    """
    with pool_path.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            raw_id = row.get("question_id")
            question_id = str(raw_id) if raw_id else f"{id_prefix}{idx:06d}"
            row_key = make_pool_row_key(idx, question_id)
            answer = row.get("answer", {})
            aliases = [a for a in answer.get("normalized_aliases", []) if a]
            answer_value = answer.get("value") or None
            yield row_key, idx, question_id, row["question"], aliases, answer_value


def _subset_key(subset_seed: int, row_key: str) -> str:
    return hashlib.sha256(f"{subset_seed}|{row_key}".encode()).hexdigest()


def load_probe_pool(config: dict, pool_path: Path) -> tuple[list[tuple], dict]:
    """Load and deterministically cap the probe pool.

    The cap selects source rows by a stable hash of (subset_seed, row_key), then
    keeps source-file order for the selected rows. Row keys include source index
    plus question_id because TriviaQA train question_id is not unique.
    """
    pool_cfg = config["probe_pool"]
    id_prefix = pool_cfg["question_id_prefix"]
    rows = list(iter_pool(pool_path, id_prefix))
    source_count = len(rows)
    max_questions = pool_cfg.get("max_questions")
    subset_seed = int(pool_cfg.get("subset_seed", config["sampling"]["seed"]))

    if isinstance(max_questions, bool) or (
            max_questions is not None and int(max_questions) < 0):
        raise ValueError("probe_pool.max_questions must be null or a non-negative integer")

    selected_rows = rows
    selection_applied = False
    if max_questions is not None:
        max_questions = int(max_questions)
        if source_count > max_questions:
            selected_row_keys = {
                row_key for row_key, *_ in sorted(
                    rows,
                    key=lambda row: (_subset_key(subset_seed, row[0]), row[0]),
                )[:max_questions]
            }
            selected_rows = [row for row in rows if row[0] in selected_row_keys]
            selection_applied = True

    selection = {
        "source_question_count": source_count,
        "selected_question_count": len(selected_rows),
        "max_questions": max_questions,
        "subset_seed": subset_seed,
        "selection_applied": selection_applied,
        "selection_method": (
            "sha256(f'{subset_seed}|{probe_pool_row_key}') ascending; "
            "probe_pool_row_key is zero-based source_index plus question_id; "
            "selected rows processed in source order"
        ),
    }
    return selected_rows, selection


def assign_label(greedy_correct: bool, pc: float, labels_cfg: dict) -> str:
    """known / unknown / discard per the pre-registered bands."""
    if greedy_correct and pc >= labels_cfg["known_p_correct_min"]:
        return "known"
    if pc <= labels_cfg["unknown_p_correct_max"]:
        return "unknown"
    return "discard"


def load_done_row_keys(results_path: Path) -> tuple[set[str], int]:
    """Row keys already in the append-log and count of legacy unkeyed rows."""
    done: set[str] = set()
    if not results_path.exists():
        return done, 0
    legacy_rows = 0
    with results_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            row_key = record.get("probe_pool_row_key")
            if row_key:
                done.add(row_key)
            else:
                legacy_rows += 1
    return done, legacy_rows


def probe_one(backend, row_key, source_index, question_id, question, aliases,
              answer_value, config, cfg_sha):
    """Probe a single question and return its result record (A -> B schema).

    answer_value is the natural-case gold (TriviaQA answer.value) carried
    through for the builder's `known` target; it is an OPTIONAL schema field
    (None when the pool row omits it). Scoring still uses the normalized
    aliases, so answer_value never affects p_correct or the label.
    """
    s = config["sampling"]
    seed = derive_seed(s["seed"], question_id)

    sampled_answers = backend.generate_batch(
        question=question, n_samples=s["n_samples"],
        temperature=s["temperature"], top_p=s["top_p"],
        max_new_tokens=s["max_new_tokens"], seed=seed,
    )
    assert_no_generated_thinking_batch(
        sampled_answers, question=question, generation_kind="sampled"
    )
    sampled_correct = [is_correct(a, aliases) for a in sampled_answers]
    pc = p_correct(sampled_correct)

    greedy_answer = backend.generate_greedy(question, s["max_new_tokens"])
    assert_no_generated_thinking(
        greedy_answer, question=question, generation_kind="greedy"
    )
    greedy_correct = is_correct(greedy_answer, aliases)

    label = assign_label(greedy_correct, pc, config["labels"])

    return {
        "probe_pool_row_key": row_key,
        "probe_pool_source_index": source_index,
        "question_id": question_id,
        "question": question,
        "question_norm": normalize_question(question),
        "normalized_aliases": aliases,
        "answer_value": answer_value,
        "n_samples": s["n_samples"],
        "greedy_answer": greedy_answer,
        "greedy_correct": greedy_correct,
        "p_correct": pc,
        "sampled_answers": sampled_answers,
        "sampled_correct": sampled_correct,
        "label": label,
        "model_tag": config["model"]["model_tag"],
        "probe_config_sha": cfg_sha,
    }


def run_probe(config: dict, backend, out_dir: Path) -> Path:
    """Run the checkpointed probe over the pool, appending results. Returns path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / config["output"]["results_filename"]
    cfg_sha = config_sha(config)
    pool_path = resolve_pool_path(config)
    pool_rows, selection = load_probe_pool(config, pool_path)

    done, legacy_rows = load_done_row_keys(results_path)
    if legacy_rows:
        raise RuntimeError(
            f"{_rel(results_path)} contains {legacy_rows} legacy records "
            "without probe_pool_row_key. Duplicate question_ids make this "
            "append-log unsafe to resume with row-keyed probe_pool selection. "
            "Archive this partial append-log or choose a fresh model_tag/output "
            "directory before running with the capped probe_pool config."
        )
    selected_row_keys = {row_key for row_key, *_ in pool_rows}
    outside_done = done - selected_row_keys
    if outside_done:
        raise RuntimeError(
            f"{_rel(results_path)} contains {len(outside_done)} row keys "
            "outside the configured probe_pool subset. Archive this partial "
            "append-log or choose a fresh model_tag/output directory before "
            "running with the capped probe_pool config."
        )

    n_new = 0
    with results_path.open("a", encoding="utf-8") as fh:
        for row_key, source_index, question_id, question, aliases, answer_value in pool_rows:
            if row_key in done:
                continue
            record = probe_one(
                backend, row_key, source_index, question_id, question, aliases, answer_value,
                config, cfg_sha)
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            done.add(row_key)
            n_new += 1
    print(f"probe: wrote {n_new} new records to "
          f"{_rel(results_path)} "
          f"({len(done)} already present, skipped; "
          f"{selection['selected_question_count']} selected from "
          f"{selection['source_question_count']})")
    return results_path


def read_results(results_path: Path) -> list[dict]:
    with results_path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def sensitivity_grid(records: list[dict], sens_cfg: dict) -> dict:
    """Label-noise sensitivity analysis (architecture doc 3.6).

    For each (unknown_cutoff, known_cutoff) cell, report the split sizes and
    the fraction of unknown-labeled questions the greedy decode actually
    answered correctly (the Paper-1 43-51% analogue). Optionally subsamples
    the records for cost (point estimate at the pinned band is the headline).
    """
    pool = records
    cap = sens_cfg.get("max_questions")
    if cap is not None and len(pool) > cap:
        ordered = sorted(
            pool,
            key=lambda r: hashlib.sha256(
                f"{sens_cfg['subsample_seed']}|{r['question_id']}".encode()
            ).hexdigest(),
        )
        pool = ordered[:cap]

    cells = []
    for u_cut in sens_cfg["unknown_cutoffs"]:
        for k_cut in sens_cfg["known_cutoffs"]:
            unknown = [r for r in pool if r["p_correct"] <= u_cut]
            known = [r for r in pool
                     if r["greedy_correct"] and r["p_correct"] >= k_cut]
            answerable = sum(1 for r in unknown if r["greedy_correct"])
            cells.append({
                "unknown_cutoff": u_cut,
                "known_cutoff": k_cut,
                "n_unknown": len(unknown),
                "n_known": len(known),
                "unknown_greedy_answerable": answerable,
                "unknown_greedy_answerable_frac": (
                    answerable / len(unknown) if unknown else 0.0),
            })
    return {"n_questions_in_grid": len(pool), "cells": cells}


def write_manifest(config: dict, records: list[dict], out_dir: Path,
                   pool_path: Path) -> Path:
    """Provenance sidecar: config, sampling, prompt, split source, counts."""
    label_counts: dict[str, int] = {}
    for r in records:
        label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1
    manifest = {
        "model_tag": config["model"]["model_tag"],
        "model_name": config["model"]["model_name"],
        "enable_thinking": config["model"]["enable_thinking"],
        "sampling": config["sampling"],
        "prompt_system": config["prompt"]["system"],
        "split_source": _rel(pool_path),
        "probe_pool": load_probe_pool(config, pool_path)[1],
        "probe_config_sha": config_sha(config),
        "n_questions": len(records),
        "label_counts": label_counts,
        "labels_bands": config["labels"],
    }
    manifest_path = out_dir / config["output"]["manifest_filename"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_path


def finalize(config: dict, results_path: Path, out_dir: Path) -> None:
    """Post-probe: write manifest + sensitivity grid from the append-log."""
    records = read_results(results_path)
    pool_path = resolve_pool_path(config)
    write_manifest(config, records, out_dir, pool_path)
    if config["sensitivity"]["enabled"]:
        grid = sensitivity_grid(records, config["sensitivity"])
        (out_dir / config["output"]["sensitivity_filename"]).write_text(
            json.dumps(grid, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_config = Path(__file__).resolve().parent / "config" / "probe.yaml"
    parser.add_argument("--config", type=Path, default=default_config,
                        help="path to probe.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    out_dir = (Path(__file__).resolve().parent / config["model"]["model_tag"])
    system_prompt = config["prompt"]["system"]
    backend = build_backend(config, system_prompt)

    results_path = run_probe(config, backend, out_dir)
    finalize(config, results_path, out_dir)
    print(f"probe: manifest + sensitivity grid written to "
          f"{_rel(out_dir)}")


if __name__ == "__main__":
    main()
