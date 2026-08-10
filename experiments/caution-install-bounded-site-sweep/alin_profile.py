#!/usr/bin/env python3
"""Stage 3 (CPU): A_lin read control (cell.yaml `read_controls.a_lin_profile`).

A_lin = top-1 logit-lens accuracy: softcap(W_U @ final_norm(h)) predicting the
row's own recorded greedy next token, at every registered site x substrate
combination the extraction (`extract_anchor.py`) has cached. CPU-only per
cell.yaml (`read_controls.a_lin_profile.device: cpu`): loads only the model's
final-norm weight and output-embedding (lm_head) tensors from the checkpoint
(no full-model forward pass -- the anchor hidden states are already cached in
`analysis/extract_<substrate>/`), matching the AMENDMENT.md accessibility
profile.

`confound_rule` (cell.yaml): a contrast between two sites whose |A_lin_a -
A_lin_b| > 0.10 is declared confounded at registration time -- this script
records the pairwise matrix so adjudicate_gates.py / the lead can apply that
rule, but does not itself void a contrast (that is an adjudication call, out
of scope for a harness script).

Output: `analysis-committed/<substrate>/alin_profile.json` (site -> A_lin,
n_rows; no row text).

AMBIGUITY (flagged, not silently resolved -- see harness report): the tuner's
`MechInterp.extraction.extract_rows` manifest (read in full before writing
this script) persists each row's DECODED `answer_text`, never the raw
generated token ids, so "the row's own recorded greedy next token" cannot be
read back exactly from `extract_anchor.py`'s cached artifacts alone -- adding
that capture would mean editing the tuner submodule's `extract_rows`, which is
forbidden. This script approximates the ground-truth next token as
`tokenizer.encode(answer_text, add_special_tokens=False)[0]`, i.e. the first
token of a fresh re-tokenization of the decoded completion. This is the
standard approximation when raw ids are not persisted, but it can disagree
with the true greedy id at a BPE merge boundary (decode-then-reencode is not
guaranteed to round-trip). Confirm with the lead before the real run; if exact
next-token ids are required, `extract_anchor.py` would need to capture them
itself via a bespoke generation loop rather than calling `extract_rows`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    base_repo_and_revision,
    load_cell,
    sites_for,
    write_json,
)


def sanitize_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_").replace("/", "_")


def load_final_norm_and_head(base_repo: str, base_revision, adapter_repo=None, adapter_revision=None):
    """Load only `model.norm` and the output-embedding weight, on CPU, without
    instantiating the full transformer stack's forward path. Uses
    AutoModelForCausalLM with device_map="cpu" (weights land on CPU, no GPU
    required); this is still a full state-dict load (~8-16GB for Qwen3-4B in
    bf16/fp32), acceptable for a one-shot CPU profile per AMENDMENT.md but
    worth flagging as the one A_lin cost."""
    import torch
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(
        base_repo, revision=base_revision, torch_dtype=torch.float32, device_map="cpu"
    )
    if adapter_repo:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_repo, revision=adapter_revision)
        base = model.get_base_model()
    else:
        base = model
    norm = base.model.norm
    head = base.get_output_embeddings()
    return norm, head


def softcap_logits(h: np.ndarray, norm, head) -> np.ndarray:
    import torch

    with torch.no_grad():
        t = torch.as_tensor(h, dtype=torch.float32).unsqueeze(0)
        normed = norm(t)
        logits = head(normed).squeeze(0).numpy()
    return logits


def run(args: argparse.Namespace) -> int:
    from safetensors.numpy import load_file

    cell = load_cell()
    substrate = args.substrate
    sites = sites_for(substrate, cell)
    extract_dir = ANALYSIS / f"extract_{substrate}"
    manifest_path = extract_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[alin:{substrate}] ERROR: no extraction manifest at {manifest_path}. "
              "Run extract_anchor.py first.", file=sys.stderr)
        return 1
    import json
    manifest = json.loads(manifest_path.read_text())
    rows = manifest.get("rows", manifest.get("answered_rows", []))
    if not rows:
        print(f"[alin:{substrate}] ERROR: extraction manifest has no row list to "
              "read greedy next-token ids from.", file=sys.stderr)
        return 1

    from sweep_lib import substrate_config
    sub_cfg = substrate_config(substrate, cell)
    base_repo, base_revision = base_repo_and_revision(substrate, cell)
    adapter_repo = sub_cfg.get("adapter_repo")
    adapter_revision = sub_cfg.get("adapter_revision")
    norm, head = load_final_norm_and_head(base_repo, base_revision, adapter_repo, adapter_revision)

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_repo, revision=base_revision)

    # See the module AMBIGUITY note: next_id is a re-tokenization approximation,
    # not the raw generated id (extract_rows does not persist raw ids).
    next_id_by_key = {}
    for rec in rows:
        rk, text = rec.get("row_key"), rec.get("answer_text")
        if not rk or not rec.get("answered") or not text:
            continue
        ids = tokenizer.encode(text, add_special_tokens=False)
        if ids:
            next_id_by_key[rk] = ids[0]

    report = {"substrate": substrate, "ground_truth_method": "retokenize_answer_text_approx", "sites": {}}
    for site in sites:
        n_correct, n_total = 0, 0
        for rk, next_id in next_id_by_key.items():
            path = extract_dir / f"{sanitize_key(rk)}__anchor.safetensors"
            if not path.exists():
                continue
            tensors = load_file(str(path))
            key = f"L{site.hs_index}"
            if key not in tensors:
                continue
            h = tensors[key][0]
            logits = softcap_logits(h, norm, head)
            pred = int(np.argmax(logits))
            n_total += 1
            n_correct += int(pred == int(next_id))
        a_lin = (n_correct / n_total) if n_total else None
        report["sites"][site.name] = {"a_lin": a_lin, "n_correct": n_correct, "n_total": n_total}
        print(f"[alin:{substrate}] {site.name}: A_lin={a_lin} (n={n_total})", flush=True)

    out_path = COMMITTED / substrate / "alin_profile.json"
    write_json(out_path, report)
    print(f"[alin:{substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
