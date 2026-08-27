#!/usr/bin/env python3
"""QUALIFY mode separability on base-model readout: CPU-only hidden-state extraction.

Pre-registered in experiments/qualify-mode-separability-base-readout/AMENDMENT.md
(draft; pins at signing). Lab-diagnostic, exploratory, single model/seed.

Loads the pinned base checkpoint (unsloth/Qwen3-4B-bnb-4bit @ the exact
fresh-sft-epistemic-mode-token-grpo Stage-S starting revision) on CPU only,
renders each row's [system, user] turns with the same chat template and
enable_thinking=False used by that experiment's qualification runner, and
extracts the last-prompt-token hidden state at four depths (25/50/75/95% of
the model's 36 transformer blocks).

Rows: all 937 QUALIFY train rows plus a fixed-seed matched draw of 937
ABSTAIN and 937 ANSWER train rows (2811 total), plus the full 602-row dev
split. The 1,201-row held-out split is never opened by this script; a path
guard refuses to run if any resolved input path contains "heldout".

Incremental / kill-resume: every row's features are appended to a
fixed-record-length binary shard immediately after being computed, and the
row's key is appended to a companion JSONL index and flushed before moving to
the next row. Resume works by reading the index, skipping row_keys already
present, and appending from there -- both files stay append-only and are
never truncated or rewritten as a whole.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # hard CPU-only gate, set before any torch/transformers import

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent


def load_cell(cell_path: Path) -> dict:
    with open(cell_path) as f:
        return yaml.safe_load(f)


def resolve_and_guard(cell: dict) -> dict:
    """Resolve dataset paths relative to this file and refuse any heldout path."""
    paths = {}
    for key in ("train", "dev"):
        p = (HERE / cell["dataset"][key]["path"]).resolve()
        if "heldout" in str(p).lower():
            raise RuntimeError(f"REFUSED: resolved path for {key} contains 'heldout': {p}")
        paths[key] = p
    forbidden = (HERE / cell["dataset"]["heldout"]["path_forbidden"]).resolve()
    if forbidden.exists():
        pass  # existing on disk is fine; we simply never open it
    return paths


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def select_fit_population(train_rows: list[dict], cell: dict) -> list[dict]:
    fp = cell["fit_population"]
    by_mode: dict[str, list[dict]] = {"ABSTAIN": [], "QUALIFY": [], "ANSWER": []}
    for r in train_rows:
        by_mode[r["metadata"]["mode_label"]].append(r)

    qualify_rows = list(by_mode["QUALIFY"])
    assert len(qualify_rows) == cell["dataset"]["train"]["mode_counts"]["QUALIFY"], (
        f"expected {cell['dataset']['train']['mode_counts']['QUALIFY']} QUALIFY train rows, "
        f"got {len(qualify_rows)}"
    )

    rng = np.random.RandomState(fp["match_seed"])

    def matched_draw(pool: list[dict], n: int) -> list[dict]:
        idx = rng.permutation(len(pool))[:n]
        return [pool[i] for i in sorted(idx.tolist())]

    abstain_matched = matched_draw(by_mode["ABSTAIN"], fp["abstain_matched"])
    answer_matched = matched_draw(by_mode["ANSWER"], fp["answer_matched"])

    fit_rows = qualify_rows + abstain_matched + answer_matched
    assert len(fit_rows) == fp["total_fit_rows"], (
        f"expected {fp['total_fit_rows']} fit rows, got {len(fit_rows)}"
    )
    return fit_rows


def render_prompt(tokenizer, row: dict, enable_thinking: bool) -> str:
    convo = row["conversations"][:2]  # [system, user] only -- pre-generation
    assert convo[0]["role"] == "system" and convo[1]["role"] == "user", row["conversations"]
    return tokenizer.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True, enable_thinking=enable_thinking
    )


class ResumableFeatureWriter:
    """Fixed-record-length append-only binary shard + companion JSONL index.

    Record layout per row: len(depths) * hidden_size float32 values,
    concatenated in the order `depths` is given. Resume: read the index,
    build the set of already-written row_keys, skip them on the next pass.
    """

    def __init__(self, index_path: Path, features_path: Path, n_depths: int, hidden_size: int):
        self.index_path = index_path
        self.features_path = features_path
        self.record_floats = n_depths * hidden_size
        self.record_bytes = self.record_floats * 4
        index_path.parent.mkdir(parents=True, exist_ok=True)
        features_path.parent.mkdir(parents=True, exist_ok=True)
        self._done_keys = self._load_done_keys()

    def _load_done_keys(self) -> set[str]:
        if not self.index_path.exists():
            return set()
        keys = set()
        with open(self.index_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                keys.add(json.loads(line)["row_key"])
        return keys

    def is_done(self, row_key: str) -> bool:
        return row_key in self._done_keys

    def append(self, row_key: str, split: str, mode_label: str, k: int, vec: np.ndarray) -> None:
        assert vec.dtype == np.float32
        assert vec.size == self.record_floats, (vec.size, self.record_floats)
        with open(self.features_path, "ab") as fbin:
            fbin.write(vec.tobytes())
            fbin.flush()
            os.fsync(fbin.fileno())
        with open(self.index_path, "a") as fidx:
            fidx.write(json.dumps({
                "row_key": row_key, "split": split, "mode_label": mode_label, "k": k,
            }) + "\n")
            fidx.flush()
            os.fsync(fidx.fileno())
        self._done_keys.add(row_key)

    def n_done(self) -> int:
        return len(self._done_keys)


def run(args: argparse.Namespace) -> int:
    t_start = time.time()
    cell = load_cell(HERE / "cell.yaml")
    paths = resolve_and_guard(cell)

    depths = cell["extraction"]["depths_hidden_state_index"]
    hidden_size = cell["model"]["hidden_size"]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    assert not torch.cuda.is_available() or os.environ.get("CUDA_VISIBLE_DEVICES") == "", (
        "CUDA_VISIBLE_DEVICES must be empty; this script is CPU-only by hard requirement"
    )

    model_id = cell["model"]["hub_repo"]
    revision = cell["model"]["revision"]
    print(f"[extract] loading {model_id}@{revision} on CPU ...", file=sys.stderr)
    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, device_map="cpu")
    model.eval()
    assert model.config.num_hidden_layers == cell["model"]["num_hidden_layers"]
    print(f"[extract] loaded in {time.time() - t_start:.1f}s", file=sys.stderr)

    train_rows = load_rows(paths["train"])
    fit_rows = select_fit_population(train_rows, cell)
    dev_rows = load_rows(paths["dev"])
    assert len(dev_rows) == cell["dataset"]["dev"]["rows"]

    jobs = [(r, "fit") for r in fit_rows] + [(r, "dev") for r in dev_rows]
    if args.limit is not None:
        jobs = jobs[: args.limit]

    index_path = HERE / cell["output"]["extraction_index"]
    features_path = HERE / cell["output"]["extraction_features_dir"] / "combined.f32.bin"
    writer = ResumableFeatureWriter(index_path, features_path, n_depths=len(depths), hidden_size=hidden_size)
    print(f"[extract] {writer.n_done()} rows already done, {len(jobs)} requested", file=sys.stderr)

    enable_thinking = cell["model"]["enable_thinking"]
    n_processed = 0
    t_loop = time.time()
    with torch.no_grad():
        for row, split in jobs:
            row_key = row["metadata"]["row_key"]
            if writer.is_done(row_key):
                continue
            mode_label = row["metadata"]["mode_label"]
            k = row["metadata"]["correct_count"]

            prompt = render_prompt(tok, row, enable_thinking)
            enc = tok(prompt, return_tensors="pt")
            out = model(**enc, output_hidden_states=True)
            hs = out.hidden_states  # tuple len n_hidden_states, each [1, seq, hidden]

            vecs = [hs[d][0, -1, :].float().numpy() for d in depths]
            vec = np.concatenate(vecs).astype(np.float32)
            writer.append(row_key, split, mode_label, k, vec)
            n_processed += 1

            if n_processed % 20 == 0 or n_processed == len(jobs):
                elapsed = time.time() - t_loop
                rate = elapsed / max(n_processed, 1)
                print(
                    f"[extract] {n_processed}/{len(jobs)} this-run rows "
                    f"({writer.n_done()} total done), {rate:.3f}s/row, elapsed {elapsed:.1f}s",
                    file=sys.stderr,
                )

    total_elapsed = time.time() - t_start
    print(f"[extract] done: {n_processed} rows this run, {writer.n_done()} total, {total_elapsed:.1f}s wall", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="process at most N jobs (smoke runs)")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
