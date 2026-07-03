#!/usr/bin/env python3
"""Amendment AH MAIN RUN (script 2/3) — primed pre-gen instrumentation (GPU).

Locked spec §6 (gate-free instrumentation). Runs primed pre-generation anchor
extraction and scores the primed states on the frozen doubt (L20/L24/L28) and
caution axes, then reports deltas vs the row's EXISTING baseline (A0/unprimed)
state. Question: does an incongruent prime move either readout differently than
a congruent one?

Primed surface = byte-frozen AF harness, EXACTLY the main-run generation prompt
but forward-only (no decode):
  system = prime + " " + baseline_system, render_probe_prompt(enable_thinking=False),
  anchor = prompt_len-1, persist not needed (we score inline), batch=1.

Which prime per row (matches the generation arms, §3.3):
  release rows              -> A-certain (PRIME_HIGH)
  muzzle + positive-control -> A-doubt   (PRIME_LOW)

Baseline (unprimed) states already exist under the Stage-0 pregen dirs
(pool rows carry pregen_dir + safe_key); we read L20/L24/L28 from there and
score with the same frozen probes + caution axis, so the delta is primed-minus-
baseline on identical rows.

Outputs (canonical, gitignored) under analysis/ah_main/instrumentation/:
  primed_readout.jsonl  per-row {doubt_L*, caution_dist} baseline vs primed + deltas
  instrumentation_summary.json  congruent-vs-incongruent delta means per contrast
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml
import joblib
from safetensors import safe_open

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import MODEL_NAME  # noqa: E402
from amendment_af_generate import PRIME_HIGH, PRIME_LOW  # noqa: E402
from amendment_ah_redesign_collinearity import load_af_caution  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AC_CONFIG = PROBE_DIR / "config" / "phase3_ac_doubt_coupled_intervention.yaml"
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
DEFAULT_POOL = STAGE0 / "expansion" / "pool_v21.jsonl"
CAND_FILES = [STAGE0 / "candidates.jsonl",
              STAGE0 / "expansion" / "expansion_candidates.jsonl"]
PROBES = STAGE0 / "probes"
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_main/instrumentation"

LAYERS = ["L20", "L24", "L28"]


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)["prompt"]["system"]


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_questions():
    q = {}
    for f in CAND_FILES:
        for r in load_jsonl(f):
            q[r["row_key"]] = r["question"]
    return q


def load_probes():
    return {ly: joblib.load(PROBES / f"probe_{ly}.joblib") for ly in LAYERS}


def score_probe(probe, v):
    return float(probe["clf"].decision_function(probe["scaler"].transform(v[None, :]))[0])


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_jsonl(Path(args.pool).resolve())
    questions = load_questions()
    probes = load_probes()
    clf_c, sign, base_sd, _cv = load_af_caution()

    def prime_for(contrast):
        return PRIME_HIGH if contrast == "release" else PRIME_LOW

    print(f"[ah/instr] loading RAW base {MODEL_NAME} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device

    def primed_anchor(question, prime):
        system_prompt = prime + " " + baseline_system
        rendered, _ = render_probe_prompt(tokenizer, system_prompt, question,
                                          enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        return {ly: hs[int(ly[1:])][0, prompt_len - 1, :].float().cpu().numpy()
                    .astype(np.float64) for ly in LAYERS}

    rows_out = []
    t0 = time.time()
    for i, r in enumerate(pool):
        sk = r["safe_key"]
        pregen_dir = Path(r["pregen_dir"])
        # baseline (unprimed) states
        base_vecs = {}
        with safe_open(str(pregen_dir / f"{sk}__pre.safetensors"), "pt") as st:
            for ly in LAYERS:
                base_vecs[ly] = st.get_tensor(ly).float().numpy().astype(np.float64)
        prime = prime_for(r["contrast"])
        primed_vecs = primed_anchor(questions[r["row_key"]], prime)

        rec = {"row_key": r["row_key"], "safe_key": sk,
               "contrast": r["contrast"], "congruent": r["congruent"],
               "stratum": r["stratum"], "gold_class": r["gold_class"],
               "prime": prime}
        for ly in LAYERS:
            b = score_probe(probes[ly], base_vecs[ly])
            p = score_probe(probes[ly], primed_vecs[ly])
            rec[f"doubt_{ly}_baseline"] = round(b, 4)
            rec[f"doubt_{ly}_primed"] = round(p, 4)
            rec[f"doubt_{ly}_delta"] = round(p - b, 4)
        cb = sign * clf_c.decision_function(base_vecs["L24"][None, :])[0]
        cp = sign * clf_c.decision_function(primed_vecs["L24"][None, :])[0]
        rec["caution_baseline"] = round(float(cb), 4)
        rec["caution_primed"] = round(float(cp), 4)
        rec["caution_delta"] = round(float(cp - cb), 4)
        rec["caution_delta_z"] = round(float((cp - cb) / base_sd), 4)
        rows_out.append(rec)
        if (i + 1) % 100 == 0 or (i + 1) == len(pool):
            el = time.time() - t0
            print(f"[ah/instr] {i+1}/{len(pool)} {el:.0f}s ({(i+1)/el:.2f}/s)",
                  flush=True)

    with (out_dir / "primed_readout.jsonl").open("w", encoding="utf-8") as fh:
        for rec in rows_out:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # summary: congruent vs incongruent delta means per contrast (descriptive)
    def block(rows):
        if not rows:
            return None
        out = {"n": len(rows)}
        for key in [f"doubt_{ly}_delta" for ly in LAYERS] + ["caution_delta", "caution_delta_z"]:
            vals = np.array([x[key] for x in rows])
            out[key] = {"mean": round(float(vals.mean()), 4),
                        "sd": round(float(vals.std()), 4)}
        return out

    summary = {"amendment": "AH", "stage": "instrumentation_primed_readout",
               "n_total": len(rows_out),
               "note": "Descriptive (gate-free, spec §6). Delta = primed - baseline "
                       "on identical rows; positive doubt_delta = prime pushed the "
                       "readout more certain; positive caution_delta = more refusal-side.",
               "by_cell": {}}
    for contrast in ["release", "muzzle", "positive_control"]:
        for cong in [True, False]:
            sub = [x for x in rows_out if x["contrast"] == contrast and x["congruent"] == cong]
            if sub:
                summary["by_cell"][f"{contrast}_{'congruent' if cong else 'incongruent'}"] = block(sub)
    (out_dir / "instrumentation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(f"[ah/instr] DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
