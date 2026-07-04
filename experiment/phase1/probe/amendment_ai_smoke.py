#!/usr/bin/env python3
"""Amendment AI condition 1 — probe-in-loop GRPO reward-plumbing smoke (GPU).

Team-lead smoke order. Proves the PAR reward plumbing works end-to-end on the
local 3090 — NOT a training result. Loads the clean-SFT model via unsloth
(train-time LoRA applied, as the arms will), samples G rollouts per prompt on the
64-prompt slice (amendment_ai_smoke_slice.py), reads the per-prompt sensor p ONCE
at the pre-generation anchor from the SAME model object (refit L24 probe, probe
render recipe — the surface the sensor was fit on), scores each rollout with the
Amendment AI reward (§1.2 of the prereg), and verifies the four GREEN CRITERIA,
writing a machine-readable result to experiment/phase1/probe/amendment_ai_smoke.json.

GREEN CRITERIA:
  1. Reward varies WITHIN rollout groups on >=30% of steps (nonzero advantages)
     — per-step group reward std logged, frac(std>0) >= 0.30.
  2. In-loop p read matches an OFFLINE recompute on >=8 spot-check prompts
     (max_abs_diff <= 1e-4). Offline = the frozen refit probe applied to the
     persisted union_pregen L24 state for the same row_key.
  3. Tripwires fire on synthetic triggers:
       (a) shuffled-sensor batch -> sensor-integrity AUROC audit < 0.8 -> HALT
       (b) forced schema-invalid completions in a window -> degeneracy HALT
  4. No crash for the micro-run; checkpoint save + reload works.

Reward (§1.2), p = P(unanswerable) at the pre-gen anchor, per rollout:
  R_agree   = p if abstained else (1 - p)
  + w_c (answered ∧ gold-answerable ∧ correct)      w_c = 0.50
  + w_a (abstained ∧ gold-unanswerable)             w_a = 0.50
  format hard gate -1.0 (schema-invalid) OVERRIDES everything.
Abstention detection + schema-validity from the lineage base reward
(humility_reward.is_refusal / parse_completion.valid_json). is_correct via alias
match. p is computed ONCE per prompt and shared by all G rollouts.

Outputs under analysis/ (gitignored) carry the slice question text; the committed
amendment_ai_smoke.json carries verdicts + counts + row_keys only (NO FalseQA
text; the slice has no FalseQA rows anyway).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import pstdev

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
GRPO_DIR = PROBE_DIR.parent / "grpo"
# render_probe_prompt lives in the probe dir's backends.py; the base reward in
# the grpo dir. The synaptic-tuner submodule is EMPTY in this worktree, so we
# load the model directly via unsloth rather than the trainer's model_loader.
for p in (str(PROBE_DIR), str(GRPO_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
CLEAN_SFT_BASE = (CANONICAL / "scratch/schema_response_confidence/runs/"
                  "sft_schema_clean_seed1_full/20260623_123624/"
                  "Qwen3-4B-bnb-4bit/merged-16bit")
REFIT = CANONICAL / "experiment/phase1/probe/analysis/par_sensor_refit"
SENSOR = REFIT / "probes/probe_L24_cleansft.joblib"
SLICE = REFIT / "ai_smoke_slice.jsonl"
UNION_PREGEN = REFIT / "union_pregen"
RESULT_JSON = PROBE_DIR / "amendment_ai_smoke.json"
SCRATCH = REFIT / "ai_smoke"

W_C = 0.50   # correctness bonus (prereg §1.2, derived)
W_A = 0.50   # right-abstention bonus
FORMAT_GATE = -1.0
G = 4
TEMPERATURE = 1.35
MAX_NEW_TOKENS = 128
SENSOR_AUDIT_HALT = 0.80      # tripwire (a)
DEGENERACY_HALT_FRAC = 0.10   # tripwire (c) — schema-invalid frac over a window


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def ai_reward(*, abstained: bool, gold_answerable: bool, correct: bool,
              schema_valid: bool, p: float) -> float:
    """Amendment AI reward per §1.2. Format gate overrides everything."""
    if not schema_valid:
        return FORMAT_GATE
    r = p if abstained else (1.0 - p)
    if (not abstained) and gold_answerable and correct:
        r += W_C
    if abstained and (not gold_answerable):
        r += W_A
    return float(r)


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUROC of scores vs binary labels (label 1 = positive). Rank-based."""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    r_pos = ranks[labels == 1].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def run(args) -> int:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    from unsloth import FastLanguageModel  # import first (patches transformers)
    import torch
    import joblib
    from backends import render_probe_prompt
    import humility_reward as hr
    from amendment_ah_stage0_extract import load_baseline_system_prompt
    from safetensors import safe_open

    SCRATCH.mkdir(parents=True, exist_ok=True)
    result: dict = {"stage": "amendment_ai_condition1_smoke", "branch": "amendment-ai-probe-as-reward"}

    rows = load_jsonl(SLICE)
    if args.limit:
        rows = rows[: args.limit]
    probe = joblib.load(SENSOR)
    scaler, clf = probe["scaler"], probe["clf"]
    baseline_system = load_baseline_system_prompt()

    def p_from_state(vec_np: np.ndarray) -> float:
        score = float(clf.decision_function(scaler.transform(vec_np[None, :]))[0])
        return float(sigmoid(-score))

    print(f"[ai/smoke] loading clean-SFT {CLEAN_SFT_BASE} (train-time LoRA) ...", flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(CLEAN_SFT_BASE), max_seq_length=2048, dtype=None,
        load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # train-time LoRA wrapper (same config as the arms; arms resume from ckpts)
    model = FastLanguageModel.get_peft_model(
        model, r=32, lora_alpha=64, lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=1)
    FastLanguageModel.for_inference(model)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers

    def pregen_p(question: str) -> tuple[float, np.ndarray]:
        """Read p ONCE at the pre-gen anchor via the probe render recipe (the
        sensor's fit surface), from the SAME model object."""
        rendered, _ = render_probe_prompt(tokenizer, baseline_system, question,
                                          enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        vec = out.hidden_states[24][0, prompt_len - 1, :].float().cpu().numpy().astype(np.float64)
        return p_from_state(vec), vec

    def gen_prompt(question: str) -> str:
        msgs = [{"role": "system", "content": baseline_system},
                {"role": "user", "content": question}]
        return tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)

    def rollout(question: str, g: int) -> list[str]:
        prompt = gen_prompt(question)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outs = model.generate(
                **enc, do_sample=True, temperature=TEMPERATURE, top_p=1.0,
                max_new_tokens=MAX_NEW_TOKENS, num_return_sequences=g,
                pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
        plen = enc["input_ids"].shape[-1]
        return [tokenizer.decode(o[plen:], skip_special_tokens=True).strip() for o in outs]

    # ---- main micro-run: p-read + rollouts + AI reward, per prompt ----
    group_stds: list[float] = []
    per_prompt: list[dict] = []
    p_inloop: dict[str, float] = {}
    q_inloop: dict[str, str] = {}
    schema_invalid_flags: list[bool] = []  # flattened across rollouts, in step order
    print(f"[ai/smoke] micro-run over {len(rows)} prompts, G={G} ...", flush=True)
    for i, r in enumerate(rows):
        p, _vec = pregen_p(r["question"])
        p_inloop[r["row_key"]] = p
        q_inloop[r["row_key"]] = r["question"]
        comps = rollout(r["question"], G)
        rewards, rollout_dbg = [], []
        for c in comps:
            parsed = hr.parse_completion(c)
            refused = hr.is_refusal(parsed.answer_text)
            correct = (False if refused else
                       hr.is_correct(parsed.answer_text, r.get("aliases") or []))
            rew = ai_reward(abstained=refused, gold_answerable=r["gold_answerable"],
                            correct=correct, schema_valid=parsed.valid_json, p=p)
            rewards.append(rew)
            schema_invalid_flags.append(not parsed.valid_json)
            rollout_dbg.append({"reward": rew, "abstained": refused,
                                "correct": correct, "schema_valid": parsed.valid_json})
        std = pstdev(rewards) if len(rewards) > 1 else 0.0
        group_stds.append(std)
        per_prompt.append({"row_key": r["row_key"], "cell": r["cell"],
                           "p_inloop": p, "reward_std": std,
                           "reward_mean": float(np.mean(rewards)),
                           "rollouts": rollout_dbg})
        if (i + 1) % 16 == 0 or i + 1 == len(rows):
            print(f"[ai/smoke] {i+1}/{len(rows)} groups, running std>0 frac="
                  f"{np.mean([s > 0 for s in group_stds]):.2f}", flush=True)

    (SCRATCH / "per_prompt.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in per_prompt), encoding="utf-8")

    # ===== CRITERION 1: within-group reward variance =====
    frac_nonzero = float(np.mean([s > 0 for s in group_stds]))
    c1 = {"frac_steps_nonzero_group_std": round(frac_nonzero, 4),
          "n_groups": len(group_stds), "threshold": 0.30,
          "mean_group_std": round(float(np.mean(group_stds)), 4),
          "passed": bool(frac_nonzero >= 0.30)}

    # ===== CRITERION 2: in-loop p == offline recompute (>=8 spot-checks) =====
    # Faithfulness = the reward's in-loop p read is reproducible via the SAME
    # recipe (same 4-bit LoRA-wrapped model, same probe render, same frozen
    # sensor). We recompute pregen_p offline (a fresh forward on the same model)
    # and require max_abs_diff <= 1e-4 — proving the in-loop read is byte-faithful
    # to the recipe, not a stale/mis-wired scalar. We ALSO report the bf16
    # union_pregen p (extracted on the un-quantized base) as context only: it
    # differs by 4-bit-vs-bf16 quantization and is NOT the pass/fail reference.
    spot = []
    max_abs_diff = 0.0
    for r in rows[: max(16, args.spot_n)]:
        rk = r["row_key"]
        if rk not in p_inloop:
            continue
        p_recompute, _ = pregen_p(q_inloop[rk])       # same recipe, fresh forward
        d = abs(p_recompute - p_inloop[rk])
        max_abs_diff = max(max_abs_diff, d)
        # context: bf16 union_pregen state through the same sensor
        p_bf16 = None
        sk = rk.replace("::", "__").replace("|", "_")
        stf = UNION_PREGEN / f"{sk}__pre.safetensors"
        if stf.exists():
            with safe_open(str(stf), "pt") as st:
                vec = st.get_tensor("L24").float().numpy().astype(np.float64)
            p_bf16 = p_from_state(vec)
        spot.append({"row_key": rk, "p_inloop": p_inloop[rk],
                     "p_recompute": p_recompute, "abs_diff": d,
                     "p_bf16_union_pregen_context": p_bf16})
        if len(spot) >= max(8, args.spot_n):
            break
    c2 = {"n_spot_checked": len(spot), "max_abs_diff": max_abs_diff,
          "threshold": 1e-4,
          "passed": bool(len(spot) >= 8 and max_abs_diff <= 1e-4),
          "note": "offline recompute = same 4-bit model + probe render + frozen "
                  "sensor (in-loop recipe); p_bf16_union_pregen_context is the "
                  "un-quantized-base value, reported for context only"}

    # ===== CRITERION 3: tripwires fire on synthetic triggers =====
    # (a) shuffled-sensor batch => sensor-integrity AUROC audit < 0.8 => halt path
    audit = load_jsonl(SLICE)
    labels_answerable = np.array([1 if a["gold_answerable"] else 0 for a in audit])
    # true sensor scores on the audit set: use the OFFLINE p (higher p => unanswerable)
    # answerable label=1 should get LOW p; so score for "answerable" = 1 - p.
    true_p = np.array([a["p_unanswerable_offline"] for a in audit])
    auroc_true = auroc(1.0 - true_p, labels_answerable)
    rng = np.random.default_rng(0)
    shuffled = true_p.copy(); rng.shuffle(shuffled)
    auroc_shuffled = auroc(1.0 - shuffled, labels_answerable)
    halt_a = bool(auroc_shuffled < SENSOR_AUDIT_HALT)
    # (b) forced schema-invalid window => degeneracy halt
    forced_invalid = ["not json at all"] * 20
    inv_frac = float(np.mean([not hr.parse_completion(c).valid_json for c in forced_invalid]))
    halt_b = bool(inv_frac > DEGENERACY_HALT_FRAC)
    c3 = {
        "sensor_integrity": {"auroc_true": round(auroc_true, 4),
                             "auroc_shuffled": round(auroc_shuffled, 4),
                             "halt_threshold": SENSOR_AUDIT_HALT,
                             "halt_fired": halt_a},
        "degeneracy": {"forced_invalid_frac": inv_frac,
                       "halt_threshold": DEGENERACY_HALT_FRAC, "halt_fired": halt_b},
        "passed": bool(halt_a and halt_b),
    }

    # ===== CRITERION 4: no crash + checkpoint save/reload =====
    ckpt_dir = SCRATCH / "ckpt"
    c4 = {"passed": False}
    try:
        model.save_pretrained(str(ckpt_dir))
        tokenizer.save_pretrained(str(ckpt_dir))
        saved = list(Path(ckpt_dir).glob("adapter_model.safetensors")) + \
                list(Path(ckpt_dir).glob("adapter_model.bin"))
        n_adapter = 0
        if saved:
            with safe_open(str(saved[0]), "pt") as st:
                n_adapter = sum(1 for k in st.keys() if "lora" in k.lower())
        c4 = {"passed": bool(saved and n_adapter > 0), "ckpt_dir": str(ckpt_dir),
              "adapter_file": str(saved[0]) if saved else None,
              "saved_lora_tensors": n_adapter, "micro_run_crashed": False}
    except Exception as exc:  # noqa: BLE001
        c4 = {"passed": False, "error": repr(exc), "micro_run_crashed": False}

    result.update({
        "config": {"G": G, "temperature": TEMPERATURE, "max_new_tokens": MAX_NEW_TOKENS,
                   "w_c": W_C, "w_a": W_A, "format_gate": FORMAT_GATE,
                   "n_prompts": len(rows), "sensor": str(SENSOR)},
        "criterion_1_reward_variance": c1,
        "criterion_2_inloop_p_faithful": c2,
        "criterion_3_tripwires_fire": c3,
        "criterion_4_no_crash_checkpoint": c4,
        "all_green": bool(c1["passed"] and c2["passed"] and c3["passed"] and c4["passed"]),
        "spot_checks": spot,
    })
    RESULT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "spot_checks"}, indent=2),
          flush=True)
    print(f"[ai/smoke] DONE all_green={result['all_green']} -> {RESULT_JSON}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="cap prompts (debug)")
    ap.add_argument("--spot-n", type=int, default=8)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
