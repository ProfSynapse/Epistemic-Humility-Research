#!/usr/bin/env python3
"""Amendment AL step 2/3: radial anti-propensity steered generation (GPU).

Regenerates the AL-prep A0 surface (1,662 rows) under one steering arm, applying
the anti-propensity push to the arm's PUSHED rows and generating every other row
untouched. Byte-identical load path, prompt render, and decode to the AL-prep A0
baseline cell (amendment_ai_verdict_extract_gen.py --stage generate): clean-SFT
merged base in the 4-bit serving config, the AI-TRUE trained LoRA applied,
greedy batch-1, max_new_tokens=96, enable_thinking=False.

THE PUSH (amendment section 3.2): subtract alpha * d_raw from the residual
stream at the point read as hidden_states[24] -- i.e. the OUTPUT of decoder
layer index 23 -- at every position from the pre-generation anchor onward. Under
the KV cache that means: the last prompt token during prefill, and every
generated token during decode. d_raw and alpha come from the frozen selection
manifest (amendment_al_select_and_direction.py). The hook reuses the AA
SteeringHook injection contract (adds alpha*d to output[0]); here alpha is
NEGATIVE (-alpha*dose) so the push SUBTRACTS the propensity direction.

Arms (selection manifest keys): primary | control | secondary. Dose defaults to
1.0; the descriptive dose ladder passes --dose 0.5 / --dose 2.0 and restricts to
the primary pushed rows (--pushed-only) so the unpushed surface is not
regenerated.

Smoke (--smoke N --readback): steers a mix of pushed/unpushed rows, and for
pushed rows re-reads the post-steering hidden at the anchor from the steered
forward pass, projecting onto d_raw to verify the propensity reading moved by
approximately the commanded -alpha*dose. Writes a readback report and STOPS
before the full run so an injection failure never burns the full sweep.

Outputs (UNTRACKED) under analysis/amendment_al_prep/amendment_al_run/<tag>/:
  gen/data/rows.jsonl   same schema as the baseline generate stage
  readback.json         (smoke only) per-row commanded vs observed shift

Usage:
  python amendment_al_steer_generate.py --arm primary --smoke 20 --readback
  python amendment_al_steer_generate.py --arm primary
  python amendment_al_steer_generate.py --arm control
  python amendment_al_steer_generate.py --arm secondary
  python amendment_al_steer_generate.py --arm primary --dose 0.5 --pushed-only --tag primary_dose0p5
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
RUN_DIR = AL_PREP / "amendment_al_run"
BASE_MODEL = str(CANONICAL / "scratch/schema_response_confidence/runs/"
                 "sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit")
ADAPTER = str(CANONICAL / "scratch/schema_response_confidence/runs/"
              "amendment_ai_grpo_true_seed1/20260703_234933/final_model")
# hidden_states[24] == output of decoder layer index 23 (hs[0] = embeddings).
STEER_LAYER_IDX = 23
READ_HS_INDEX = 24
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
    m = model
    for attr in ("base_model", "model"):
        # PeftModel.base_model.model.model.layers ; unwrap defensively
        pass
    # walk to the object that has .layers
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


class ALPush:
    """Forward hook: subtract (alpha_eff) * d from output[0] at the anchor
    during prefill and at every generated position during decode.

    Under the HF KV cache the hooked layer fires once for prefill (seq_len ==
    prompt_len; steer the last token) and once per decode step (seq_len == 1;
    steer that single position). Enabled only while `self.active` is True, so the
    same model serves pushed and unpushed rows without re-registering.
    """

    def __init__(self, d, alpha_eff):
        import torch
        self.torch = torch
        self.d = d  # unit-norm direction, torch tensor (hidden_dim,)
        self.alpha_eff = float(alpha_eff)  # already signed/scaled (negative push)
        self.active = False
        self.readback = None  # if set to a list, append post-steer anchor hidden

    def __call__(self, module, inputs, output):
        if not self.active or self.alpha_eff == 0.0:
            return output
        torch = self.torch
        if isinstance(output, tuple):
            hidden = output[0]
            rest = output[1:]
        else:
            hidden = output
            rest = None
        batch, seq_len, hidden_dim = hidden.shape
        d = self.d.to(hidden.device).to(hidden.dtype)
        hidden = hidden.clone()
        if seq_len > 1:
            # prefill: steer the last (anchor) token
            hidden[:, -1, :] = hidden[:, -1, :] + self.alpha_eff * d
        else:
            # decode step: steer the single new position
            hidden[:, 0, :] = hidden[:, 0, :] + self.alpha_eff * d
        if rest is not None:
            return (hidden,) + rest
        return hidden


def main() -> int:
    import torch
    from backends import render_probe_prompt
    import scorers

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, choices=["primary", "control", "secondary"])
    ap.add_argument("--dose", type=float, default=1.0)
    ap.add_argument("--pushed-only", action="store_true",
                    help="generate ONLY the pushed rows (dose-ladder cells)")
    ap.add_argument("--smoke", type=int, default=0,
                    help="generate only N rows (mix of pushed/unpushed) and stop")
    ap.add_argument("--readback", action="store_true",
                    help="smoke: verify the anchor propensity projection moved")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    tag = args.tag or (f"{args.arm}" if args.dose == 1.0
                       else f"{args.arm}_dose{str(args.dose).replace('.', 'p')}")
    if args.smoke:
        tag = f"smoke_{tag}"
    out_dir = RUN_DIR / tag / "gen" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((RUN_DIR / "selection_manifest.json").read_text())
    d_raw = np.load(RUN_DIR / "d_raw.npy").astype(np.float32)
    alpha = float(manifest["steering"]["alpha"])
    alpha_eff = -alpha * args.dose  # SUBTRACT the propensity direction
    pushed_keys = set(manifest["arms"][args.arm]["row_keys"])
    print(f"[al-steer] arm={args.arm} dose={args.dose} alpha={alpha:.4f} "
          f"alpha_eff={alpha_eff:.4f} pushed={len(pushed_keys)} tag={tag}", flush=True)

    # baseline graded rows carry gold_class/question/aliases + baseline grade;
    # they define the row set and question text. (Question text used only to
    # render prompts; never written to output.)
    base_rows = load_jsonl(AL_PREP / "true_a0" / "gen/data/rows_graded.jsonl")
    base_by_key = {r["row_key"]: r for r in base_rows}
    row_order = [r["row_key"] for r in base_rows]

    # smoke row selection: mix pushed confabs + pushed refusals + unpushed correct
    if args.smoke:
        pushed = [k for k in row_order if k in pushed_keys]
        pushed_confab = [k for k in pushed
                         if base_by_key[k]["confab_on_unanswerable"]][:8]
        pushed_ref = [k for k in pushed if base_by_key[k]["refused"]][:8]
        unpushed_correct = [k for k in row_order if k not in pushed_keys
                            and base_by_key[k]["gold_class"] == "answerable"
                            and base_by_key[k]["answered"]
                            and base_by_key[k]["correct"] is True][:4]
        sel_keys = pushed_confab + pushed_ref + unpushed_correct
        sel_keys = sel_keys[: args.smoke]
    elif args.pushed_only:
        sel_keys = [k for k in row_order if k in pushed_keys]
    else:
        sel_keys = list(row_order)
    print(f"[al-steer] generating {len(sel_keys)} rows", flush=True)

    baseline_system = load_baseline_system_prompt()
    model, tokenizer = build_model()
    device = next(model.parameters()).device
    layers = get_decoder_layers(model)
    n_layers = len(layers)
    assert n_layers >= STEER_LAYER_IDX + 1, f"only {n_layers} layers"
    print(f"[al-steer] n_layers={n_layers} steering layer idx={STEER_LAYER_IDX} "
          f"(reads as hidden_states[{READ_HS_INDEX}])", flush=True)

    d_t = torch.from_numpy(d_raw)
    push = ALPush(d_t, alpha_eff)
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

    def anchor_hidden(rendered, steer):
        """Forward-only; return hidden_states[READ_HS_INDEX] at prompt_len-1.
        If steer, the hook is active so the returned state is POST-steering."""
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        push.active = bool(steer)
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        push.active = False
        h = out.hidden_states[READ_HS_INDEX][0, prompt_len - 1, :].float().cpu().numpy()
        return h, prompt_len

    readback = []
    if args.smoke and args.readback:
        print("[al-steer] readback: verifying anchor propensity shift ...", flush=True)
        dproj = d_raw.astype(np.float64)
        for k in sel_keys:
            rendered, _ = render_probe_prompt(
                tokenizer, baseline_system, base_by_key[k]["question"],
                enable_thinking=False)
            h0, _ = anchor_hidden(rendered, steer=False)
            is_pushed = k in pushed_keys
            h1, _ = anchor_hidden(rendered, steer=is_pushed)
            p0 = float(h0 @ dproj)
            p1 = float(h1 @ dproj)
            readback.append({
                "row_key": k, "pushed": is_pushed,
                "proj_baseline": round(p0, 4),
                "proj_steered": round(p1, 4),
                "observed_shift": round(p1 - p0, 4),
                "commanded_shift": round(alpha_eff if is_pushed else 0.0, 4),
            })
        pushed_rb = [r for r in readback if r["pushed"]]
        unp_rb = [r for r in readback if not r["pushed"]]
        mean_obs = float(np.mean([r["observed_shift"] for r in pushed_rb])) if pushed_rb else 0.0
        mean_unp = float(np.mean([abs(r["observed_shift"]) for r in unp_rb])) if unp_rb else 0.0
        # commanded is alpha_eff (negative); observed should track it. Accept if
        # mean observed shift is within 20% of commanded and same sign.
        ratio = mean_obs / alpha_eff if alpha_eff != 0 else 0.0
        ok = (ratio > 0.8) and (ratio < 1.2)
        rb_report = {
            "arm": args.arm, "dose": args.dose, "alpha_eff": alpha_eff,
            "n_pushed": len(pushed_rb), "n_unpushed": len(unp_rb),
            "mean_observed_shift_pushed": round(mean_obs, 4),
            "mean_abs_shift_unpushed": round(mean_unp, 4),
            "commanded_shift": round(alpha_eff, 4),
            "observed_over_commanded_ratio": round(ratio, 4),
            "injection_ok": bool(ok),
            "rows": readback,
        }
        (RUN_DIR / tag / "readback.json").write_text(json.dumps(rb_report, indent=2))
        print(f"[al-steer] READBACK: mean pushed shift={mean_obs:.4f} "
              f"commanded={alpha_eff:.4f} ratio={ratio:.4f} "
              f"unpushed |shift|={mean_unp:.4f} OK={ok}", flush=True)
        print(f"[al-steer] readback -> {RUN_DIR / tag / 'readback.json'}", flush=True)
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
        print(f"[al-steer] RESUME: {len(done)} present", flush=True)

    counts = {"answered": 0, "refused": 0, "ungradeable": 0,
              "degenerate": 0, "schema_valid": 0, "pushed": 0}
    t0 = time.time()
    written = len(done)
    with rows_path.open("w", encoding="utf-8") as fh:
        for pr in prior:
            fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        fh.flush()
        for k in sel_keys:
            if k in done:
                continue
            is_pushed = k in pushed_keys
            rendered, _ = render_probe_prompt(
                tokenizer, baseline_system, base_by_key[k]["question"],
                enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            push.active = is_pushed
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            push.active = False
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
            counts["pushed"] += int(is_pushed)

            fh.write(json.dumps({
                "row_key": k, "safe_key": safe_key_for(k),
                "pushed": is_pushed, "arm": args.arm, "dose": args.dose,
                "refused": refused, "answered": answered,
                "schema_valid": schema_valid, "degenerate": degenerate,
                "answer_text": answer_text,
                "prompt_len": prompt_len,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            written += 1
            if written % 50 == 0 or written == len(sel_keys):
                el = time.time() - t0
                print(f"[al-steer] {written}/{len(sel_keys)} {el:.0f}s "
                      f"({written / max(el, 1e-9):.2f}/s) {counts}", flush=True)

    handle.remove()
    manifest_out = {
        "arm": args.arm, "dose": args.dose, "tag": tag, "alpha": alpha,
        "alpha_eff": alpha_eff, "n_generated": written, "counts": counts,
        "n_pushed_in_arm": len(pushed_keys),
        "steer_layer_idx": STEER_LAYER_IDX, "read_hs_index": READ_HS_INDEX,
        "base_model": BASE_MODEL, "adapter": ADAPTER,
        "max_new_tokens": MAX_NEW_TOKENS,
        "runtime_sec": round(time.time() - t0, 1),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest_out, indent=2))
    print(json.dumps(manifest_out, indent=2), flush=True)
    print(f"[al-steer] DONE {written} rows -> {rows_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
