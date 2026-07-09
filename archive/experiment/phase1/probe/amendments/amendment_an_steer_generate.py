#!/usr/bin/env python3
"""Amendment AN: propensity-selected, caution-actuated steered generation (GPU).

SPEC: experiments/selected-setpoint-regulator/AMENDMENT.md sections
3.2/3.3/4. Regenerates the AL-prep A0 surface (1,662 rows) under one AN arm,
applying the AC COUPLE setpoint write to the arm's FLAGGED rows and generating
every other row untouched. Byte-identical load path, prompt render, and decode
to the AL A0 baseline / AL steered arms (amendment_al_steer_generate.py): the
clean-SFT merged base in 4-bit, the AI-TRUE LoRA applied, greedy batch-1,
max_new_tokens=96, enable_thinking=False. Baseline is FROZEN and reused, never
regenerated.

THE WRITE (Amendment AC couple mechanism, section 3.2): at L35 (the OUTPUT of
decoder layer index 34, read as hidden_states[35]), at every position from the
pre-generation anchor onward,

    h' = h - (h . c_hat) c_hat + g * sigma * c_hat

where c_hat = unit(theta) is the AI-TRUE-REFIT caution_perp direction, sigma its
fitted scale, and g the arm's per-row gain from the AN selection manifest. This
ERASES the caution_perp coordinate and WRITES the commanded setpoint g*sigma on
it (positive g => setpoint UP toward refusal; negative g => DOWN toward
answering). Rows NOT in the arm's gain map generate untouched (no-op), matching
AL's pushed/unpushed split.

Arms (manifest keys, amendment_an_build_maps.py): primary | control |
bidirectional | primary_gain_p1 | primary_gain_p3.

Smoke (--smoke N --readback): steers a mix of flagged confabs + flagged corrects
+ unflagged rows, and for flagged rows re-reads the post-write hidden at the
anchor from the steered forward pass, projecting onto c_hat to verify the
caution_perp coordinate moved to the COMMANDED setpoint g*sigma (erase-and-write
lands the coordinate at exactly g*sigma regardless of the pre-write value), while
unflagged rows shift 0. Writes a readback report and STOPS before the full run so
a write failure never burns the full sweep.

Outputs (UNTRACKED) under analysis/amendment_an_prep/amendment_an_run/<tag>/:
  gen/data/rows.jsonl   same schema as the AL steered arms (row_key, pushed,
                        refused, answered, schema_valid, degenerate, answer_text)
  readback.json         (smoke only) per-row commanded vs observed setpoint

Usage:
  python amendment_an_steer_generate.py --arm primary --smoke 40 --readback
  python amendment_an_steer_generate.py --arm primary
  python amendment_an_steer_generate.py --arm control
  python amendment_an_steer_generate.py --arm bidirectional
  python amendment_an_steer_generate.py --arm primary_gain_p1 --flagged-only --tag primary_gain_p1
  python amendment_an_steer_generate.py --arm primary_gain_p3 --flagged-only --tag primary_gain_p3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from amendment_s_correctness_probe_extract import _content_end_index  # noqa: E402
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, safe_key_for,
)

CANONICAL = repo_root()
AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
AN_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_an_prep"
RUN_DIR = AN_PREP / "amendment_an_run"
BASE_MODEL = str(CANONICAL / "scratch/schema_response_confidence/runs/"
                 "sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit")
ADAPTER = str(CANONICAL / "scratch/schema_response_confidence/runs/"
              "amendment_ai_grpo_true_seed1/20260703_234933/final_model")
# caution_perp is fit at L35 == OUTPUT of decoder layer index 34 (hs[0]=embeds,
# so hidden_states[35] is layer idx 34's output). The direction JSON records
# layer=35, block=34; we assert the manifest agrees.
STEER_LAYER_IDX = 34
READ_HS_INDEX = 35
MAX_NEW_TOKENS = 96
DEGEN_RUN = 12


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def is_degenerate(text: str) -> bool:
    if not text.strip():
        return True
    toks = text.split()
    run = 1
    for i in range(1, len(toks)):
        if toks[i] == toks[i - 1]:
            run += 1
            if run >= DEGEN_RUN:
                return True
        else:
            run = 1
    return False


def build_model():
    from unsloth import FastLanguageModel
    from peft import PeftModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL, max_seq_length=2048, dtype=None, load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = PeftModel.from_pretrained(model, ADAPTER, revision=None)
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def get_decoder_layers(model):
    """Return the ModuleList of decoder layers, unwrapping PEFT/Unsloth."""
    cur = model
    seen = 0
    while seen < 6:
        if hasattr(cur, "layers"):
            return cur.layers
        if hasattr(cur, "model"):
            cur = cur.model
        elif hasattr(cur, "base_model"):
            cur = cur.base_model
        else:
            break
        seen += 1
    raise RuntimeError("could not locate decoder layers")


class ANCouple:
    """Forward hook: apply the AC couple write to output[0] at the anchor during
    prefill and at every generated position during decode.

        h' = h - (h . c_hat) c_hat + g * sigma * c_hat

    c_hat is unit-norm; sigma is the fixed scale; g is the CURRENT row's gain,
    set by the caller before each generate/forward. When g is None (unflagged
    row) the hook is a no-op. Enabled only while `self.active` is True so the
    same model serves flagged and unflagged rows without re-registering.
    """

    def __init__(self, c_hat, sigma):
        import torch
        self.torch = torch
        self.c_hat = c_hat  # unit-norm torch tensor (hidden_dim,)
        self.sigma = float(sigma)
        self.g = None  # per-row gain; None => no-op
        self.active = False

    def __call__(self, module, inputs, output):
        if not self.active or self.g is None:
            return output
        torch = self.torch
        if isinstance(output, tuple):
            hidden = output[0]
            rest = output[1:]
        else:
            hidden = output
            rest = None
        c = self.c_hat.to(hidden.device).to(hidden.dtype)
        setpoint = float(self.g) * self.sigma
        hidden = hidden.clone()
        batch, seq_len, hidden_dim = hidden.shape
        pos = slice(-1, None) if seq_len > 1 else slice(0, 1)
        # erase the c_hat coordinate then write the commanded setpoint on it
        proj = (hidden[:, pos, :] @ c).unsqueeze(-1)  # [batch, 1, 1]
        hidden[:, pos, :] = hidden[:, pos, :] - proj * c + setpoint * c
        if rest is not None:
            return (hidden,) + rest
        return hidden


def main() -> int:
    import torch
    from backends import render_probe_prompt
    import scorers

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True,
                    choices=["primary", "control", "bidirectional",
                             "primary_gain_p1", "primary_gain_p3"])
    ap.add_argument("--flagged-only", action="store_true",
                    help="generate ONLY the flagged rows (ladder / bidirectional)")
    ap.add_argument("--smoke", type=int, default=0,
                    help="generate only N rows (mix of flagged/unflagged) and stop")
    ap.add_argument("--readback", action="store_true",
                    help="smoke: verify the anchor caution_perp coordinate landed")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    tag = args.tag or args.arm
    if args.smoke:
        tag = f"smoke_{tag}"
    out_dir = RUN_DIR / tag / "gen" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((RUN_DIR / "an_selection_manifest.json").read_text())
    direction = json.loads((AN_PREP / "caution_perp_direction_L35_ai_true.json").read_text())
    theta = np.array(direction["theta"], dtype=np.float32)
    theta_norm = float(np.linalg.norm(theta))
    if theta_norm == 0.0:
        raise ValueError("zero-norm theta")
    c_hat = theta / theta_norm  # unit direction
    sigma = float(direction["sigma"])
    assert int(direction["block"]) == STEER_LAYER_IDX, (
        f"direction block {direction['block']} != steer layer idx {STEER_LAYER_IDX}")
    assert int(manifest["sigma"]) == int(sigma) or abs(manifest["sigma"] - sigma) < 1e-6

    arm = manifest["arms"][args.arm]
    gains_by_key = {k: float(v) for k, v in arm["gains"].items()}
    flagged_keys = set(arm["flagged_keys"])
    print(f"[an-couple] arm={args.arm} tag={tag} sigma={sigma:.4f} "
          f"theta_norm={theta_norm:.4f} flagged={len(flagged_keys)} "
          f"gain={arm['gain']:+g}", flush=True)

    # baseline graded rows define the row set + question text (same file the AL
    # steered arms read).
    base_rows = load_jsonl(AL_PREP / "true_a0" / "gen/data/rows_graded.jsonl")
    base_by_key = {r["row_key"]: r for r in base_rows}
    row_order = [r["row_key"] for r in base_rows]

    # smoke selection: flagged confabs + flagged corrects + unflagged corrects
    if args.smoke:
        flagged = [k for k in row_order if k in flagged_keys]
        flagged_confab = [k for k in flagged
                          if base_by_key[k]["confab_on_unanswerable"]][:16]
        flagged_correct = [k for k in flagged
                           if base_by_key[k]["gold_class"] == "answerable"
                           and base_by_key[k]["answered"]
                           and base_by_key[k]["correct"] is True][:8]
        unflagged_correct = [k for k in row_order if k not in flagged_keys
                             and base_by_key[k]["gold_class"] == "answerable"
                             and base_by_key[k]["answered"]
                             and base_by_key[k]["correct"] is True][:8]
        sel_keys = flagged_confab + flagged_correct + unflagged_correct
        sel_keys = sel_keys[: args.smoke]
    elif args.flagged_only:
        sel_keys = [k for k in row_order if k in flagged_keys]
    else:
        sel_keys = list(row_order)
    print(f"[an-couple] generating {len(sel_keys)} rows", flush=True)

    baseline_system = load_baseline_system_prompt()
    model, tokenizer = build_model()
    device = next(model.parameters()).device
    layers = get_decoder_layers(model)
    n_layers = len(layers)
    assert n_layers >= STEER_LAYER_IDX + 1, f"only {n_layers} layers"
    print(f"[an-couple] n_layers={n_layers} steering layer idx={STEER_LAYER_IDX} "
          f"(reads as hidden_states[{READ_HS_INDEX}])", flush=True)

    c_t = torch.from_numpy(c_hat)
    push = ANCouple(c_t, sigma)
    handle = layers[STEER_LAYER_IDX].register_forward_hook(push)

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = ([tokenizer.eos_token_id, im_end]
                       if tokenizer.eos_token_id is not None else im_end)

    def anchor_hidden(rendered, gain):
        """Forward-only; return hidden_states[READ_HS_INDEX] at prompt_len-1.
        If gain is not None the hook writes the setpoint, so the returned state
        is POST-write."""
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        push.g = gain
        push.active = gain is not None
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        push.active = False
        push.g = None
        h = out.hidden_states[READ_HS_INDEX][0, prompt_len - 1, :].float().cpu().numpy()
        return h, prompt_len

    # ---- readback smoke ----
    if args.smoke and args.readback:
        print("[an-couple] readback: verifying anchor caution_perp coordinate ...",
              flush=True)
        c64 = c_hat.astype(np.float64)
        readback = []
        for k in sel_keys:
            rendered, _ = render_probe_prompt(
                tokenizer, baseline_system, base_by_key[k]["question"],
                enable_thinking=False)
            is_flagged = k in flagged_keys
            gain = gains_by_key.get(k) if is_flagged else None
            h0, _ = anchor_hidden(rendered, gain=None)
            h1, _ = anchor_hidden(rendered, gain=gain)
            p0 = float(h0 @ c64)
            p1 = float(h1 @ c64)
            commanded = (float(gain) * sigma) if is_flagged else 0.0
            readback.append({
                "row_key": k, "flagged": is_flagged, "gain": gain,
                "coord_baseline": round(p0, 4),
                "coord_steered": round(p1, 4),
                "observed_setpoint": round(p1, 4),
                "commanded_setpoint": round(commanded, 4),
                "abs_error": round(abs(p1 - commanded), 4),
            })
        flagged_rb = [r for r in readback if r["flagged"]]
        unf_rb = [r for r in readback if not r["flagged"]]
        # erase-and-write lands the coordinate at exactly commanded=g*sigma; the
        # observed post-write coordinate should equal commanded within tolerance.
        mean_obs = float(np.mean([r["observed_setpoint"] for r in flagged_rb])) if flagged_rb else 0.0
        mean_cmd = float(np.mean([r["commanded_setpoint"] for r in flagged_rb])) if flagged_rb else 0.0
        max_err = float(np.max([r["abs_error"] for r in flagged_rb])) if flagged_rb else 0.0
        # unflagged rows must not move (hook off): coordinate is unchanged, i.e.
        # steered == baseline; the "observed shift" is |p1 - p0|.
        mean_unf_shift = float(np.mean([abs(r["coord_steered"] - r["coord_baseline"])
                                        for r in unf_rb])) if unf_rb else 0.0
        tol = 0.05 * abs(mean_cmd) if mean_cmd else 0.5
        write_ok = max_err <= max(tol, 0.5)
        parity_ok = mean_unf_shift <= 1e-3
        ok = bool(write_ok and parity_ok)
        rb_report = {
            "arm": args.arm, "tag": tag, "sigma": sigma,
            "n_flagged": len(flagged_rb), "n_unflagged": len(unf_rb),
            "mean_observed_setpoint_flagged": round(mean_obs, 4),
            "mean_commanded_setpoint_flagged": round(mean_cmd, 4),
            "max_abs_setpoint_error_flagged": round(max_err, 4),
            "tolerance": round(max(tol, 0.5), 4),
            "mean_abs_coord_shift_unflagged": round(mean_unf_shift, 6),
            "write_ok": bool(write_ok),
            "unflagged_parity_ok": bool(parity_ok),
            "injection_ok": ok,
            "rows": readback,
        }
        (RUN_DIR / tag / "readback.json").write_text(json.dumps(rb_report, indent=2))
        print(f"[an-couple] READBACK: flagged observed setpoint={mean_obs:.4f} "
              f"commanded={mean_cmd:.4f} max_err={max_err:.4f} (tol {max(tol,0.5):.3f}) "
              f"unflagged |shift|={mean_unf_shift:.2e} OK={ok}", flush=True)
        print(f"[an-couple] readback -> {RUN_DIR / tag / 'readback.json'}", flush=True)
        handle.remove()
        return 0 if ok else 4

    # ---- generation ----
    rows_path = out_dir / "rows.jsonl"
    done = set()
    prior = []
    if rows_path.exists() and not args.overwrite:
        for pr in load_jsonl(rows_path):
            done.add(pr["row_key"])
            prior.append(pr)
        print(f"[an-couple] RESUME: {len(done)} present", flush=True)

    counts = {"answered": 0, "refused": 0, "ungradeable": 0,
              "degenerate": 0, "schema_valid": 0, "flagged": 0}
    t0 = time.time()
    written = len(done)
    with rows_path.open("w", encoding="utf-8") as fh:
        for pr in prior:
            fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        fh.flush()
        for k in sel_keys:
            if k in done:
                continue
            is_flagged = k in flagged_keys
            gain = gains_by_key.get(k) if is_flagged else None
            rendered, _ = render_probe_prompt(
                tokenizer, baseline_system, base_by_key[k]["question"],
                enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            push.g = gain
            push.active = is_flagged and gain is not None
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            push.active = False
            push.g = None
            full_list = gen.sequences[0].tolist()
            answer_text = tokenizer.decode(
                full_list[prompt_len:], skip_special_tokens=True).strip()
            refused = bool(scorers.is_stated_confidence_refusal(answer_text))
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = bool((content_end is not None) and bool(answer_text)
                            and not refused)
            parsed = scorers.parse_stated_confidence(answer_text)
            schema_valid = bool(parsed.stated_confidence is not None)
            degenerate = is_degenerate(answer_text)

            if answered:
                counts["answered"] += 1
            elif refused:
                counts["refused"] += 1
            else:
                counts["ungradeable"] += 1
            counts["degenerate"] += int(degenerate)
            counts["schema_valid"] += int(schema_valid)
            counts["flagged"] += int(is_flagged)

            fh.write(json.dumps({
                "row_key": k, "safe_key": safe_key_for(k),
                "pushed": is_flagged, "gain": gain, "arm": args.arm,
                "refused": refused, "answered": answered,
                "schema_valid": schema_valid, "degenerate": degenerate,
                "answer_text": answer_text,
                "prompt_len": prompt_len,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            written += 1
            if written % 50 == 0 or written == len(sel_keys):
                el = time.time() - t0
                print(f"[an-couple] {written}/{len(sel_keys)} {el:.0f}s "
                      f"({written / max(el, 1e-9):.2f}/s) {counts}", flush=True)

    handle.remove()
    manifest_out = {
        "arm": args.arm, "tag": tag, "sigma": sigma, "gain": arm["gain"],
        "n_generated": written, "counts": counts,
        "n_flagged_in_arm": len(flagged_keys),
        "steer_layer_idx": STEER_LAYER_IDX, "read_hs_index": READ_HS_INDEX,
        "base_model": BASE_MODEL, "adapter": ADAPTER,
        "max_new_tokens": MAX_NEW_TOKENS,
        "runtime_sec": round(time.time() - t0, 1),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest_out, indent=2))
    print(json.dumps(manifest_out, indent=2), flush=True)
    print(f"[an-couple] DONE {written} rows -> {rows_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
