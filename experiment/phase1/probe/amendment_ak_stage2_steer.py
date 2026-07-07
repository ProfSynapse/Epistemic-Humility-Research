#!/usr/bin/env python3
"""Amendment AK Stage 2 - answer-window commitment steering (GPU intervention).

Pre-registered in experiment/protocol/AMENDMENT-AK-commitment-point.md §3.2 and
gated by AK-G3 (§4). Stage 1 is RESOLVED (G1 MISS, G2 MISS-on-floor); Stage 2 is
the causal test of whether the commitment/veto middle is TOKEN-LOCALIZED:

  AK-G3 (steering asymmetry): answer-window steering must move confab rate by
  >= 2x the anchor-only condition at matched dose, with anchor-only bounded above
  by the carried-minority prediction (item 31 r ~ 0.34-0.37).

This is the GPU half (generation + steering). The AK-G3 gate arithmetic (confab
rate per arm, the 2x ratio + bootstrap CI, guards) is CPU-side and post hoc in
amendment_ak_stage2_score.py, so this script writes per-row records only and is
grade-deterministic on re-run.

Direction (arm-B commitment, orthogonalized to caution per the B1 convention)
----------------------------------------------------------------------------
The arm-B commitment direction is mean(confab) - mean(refuse) at the steer layer
on the matched set (mi_confab_signature_20260704 characterization, line ~522),
computed here from the AK Stage 1 activations at "<layer>@anchor". It is then
orthogonalized to the caution/doubt axis exactly as build_caution_perp_direction
does for refined B1:

    d_perp = d - (d . caution_u) * caution_u ;  theta_u = unit(d_perp)

The caution axis is the FROZEN AH answerability probe weight at the steer layer,
mapped into raw-activation space (the probe was fit on standardized inputs, so
the raw-space normal is w / scale). This is the same axis caution_dist_z is
measured along and the same frozen trunk the Stage 1 lib projects (§3.1). The
dose is applied as alpha * sigma * theta_u, matching the residual-intervention
convention (phase3_residual_intervention.apply_direction), where sigma is the
std of the matched-set projection onto theta_u.

Doses (AA/AG authorized-knob grid)
----------------------------------
alpha in {-2, -1, -0.5, 0, +0.5, +1, +2} sigma-units (AA grid
{-4,-2,-1,0,1,2,4} is an authorized knob; the sign gives +dir/-dir; 0 is the
shared unsteered baseline arm). Steering layer defaults to L24 (within the arm-B
L24-28 peak/plateau band and == the Stage 1 G1_LAYER / pilot trunk layer);
--steer-layer is a knob for a follow-on band sweep.

Position conditions (reuse the merged, item-11-certified engine)
----------------------------------------------------------------
  anchor-only    = GenerationHookController mode 'anchor' (prefill last prompt
                   token; propagates via the KV cache) -> the pre-generation
                   anchor position only.
  answer-window  = GenerationHookController mode 'gen_stream' (every decode step
                   from the first visible token onward).
Item-11 residual (anchor-only "final"-during-prefill mode): already provided by
the controller's 'anchor' mode; tests/test_ak_stage2_steer.py adds the AK
regression that anchor mode steers exactly the prefill's last token and NOTHING
during decode.

Outputs (canonical checkout, gitignored; uploaded only to the PRIVATE staging
repo by the Modal wrapper):
  <out-dir>/rows.jsonl   per-row per-arm generation grade + config_sha
                         (NO question text - safe_key only)
  <out-dir>/direction.json  the resolved theta_u + sigma + provenance
  <out-dir>/manifest.json   config + arm counts + smoke/readback result
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
STEER_DIR = PROBE_DIR / "steering"
for p in (str(PROBE_DIR), str(EVAL_DIR), str(STEER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, safe_key_for,
)
import amendment_ak_stage1_lib as ak  # noqa: E402

# AA/AG authorized-knob grid in sigma units (0 = shared baseline arm).
DEFAULT_ALPHAS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
DEFAULT_STEER_LAYER = "L24"     # arm-B L24-28 band; == Stage1 G1_LAYER / pilot trunk
MAX_NEW_TOKENS = 96             # parity with Stage 1 / arm-B / AH generation
DEGEN_RUN = 12
READBACK_TOL_FRAC = 0.10        # readback within 10% of commanded alpha*sigma


# ----------------------------------------------------------------------------
# small helpers (parity with the Stage 1 extractor)
# ----------------------------------------------------------------------------

def load_jsonl(p: Path) -> list[dict]:
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


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


# ----------------------------------------------------------------------------
# Matched set (arm-B within-flavor caliper match on caution_dist_z)
# ----------------------------------------------------------------------------

def matched_set_indices(pool: list[dict], caliper: float = 0.20,
                        seed: int = 20260704) -> list[int]:
    """Within-flavor caliper match of confab (y=1) to refuse (y=0) on
    caution_dist_z, reproducing the mi_confab_signature_20260704 matched design
    (confab_signature_analysis.py lines ~197-228) byte-for-byte.

    Per flavor, iterate confab rows in ORIGINAL pool order and greedily take the
    nearest unused refuse within `caliper`; keep both members of each pair. This
    is deterministic (no RNG needed; `seed` is accepted for interface parity with
    the canonical builder, which seeds only a stable-sort no-op). Returns pool
    indices of the retained rows. This is the population the AK-G3 confab rate is
    measured on (doc §3.2: "matched unanswerable rows"), n ~= 328.
    """
    del seed  # canonical builder's RNG only seeds a stable-sort no-op
    by_flavor: dict[str, list[int]] = {}
    for i, r in enumerate(pool):
        by_flavor.setdefault(r.get("category_canon", ""), []).append(i)
    kept: list[int] = []
    for _flavor, idxs in sorted(by_flavor.items()):
        confab = [i for i in idxs if pool[i]["confab_on_unanswerable"]]
        refuse = [i for i in idxs if not pool[i]["confab_on_unanswerable"]]
        if not confab or not refuse:
            continue
        used_ref: set[int] = set()
        for ci in confab:  # original pool order (matches the canonical design)
            zc = float(pool[ci]["caution_dist_z"])
            # nearest unused refuse within the caliper (ties -> earliest by index)
            best_ri, best_d = None, None
            for ri in refuse:
                if ri in used_ref:
                    continue
                d = abs(float(pool[ri]["caution_dist_z"]) - zc)
                if d > caliper:
                    continue
                if best_d is None or d < best_d:
                    best_d, best_ri = d, ri
            if best_ri is not None:
                used_ref.add(best_ri)
                kept.append(ci)
                kept.append(best_ri)
    return sorted(set(kept))


# ----------------------------------------------------------------------------
# Caution axis (frozen AH answerability probe -> raw-activation-space normal)
# ----------------------------------------------------------------------------

def caution_axis_raw(probes_dir: Path, layer: str) -> np.ndarray:
    """Raw-activation-space caution/doubt normal at `layer`.

    The AH probe classifies on standardized x = (h - mean)/scale with weight w,
    so the decision hyperplane normal in RAW space is w / scale. This is the
    axis caution_dist_z is measured along; the B1 convention orthogonalizes the
    commitment direction against it. Sign is irrelevant to orthogonalization.
    """
    trunk = ak.DoubtTrunk.load(probes_dir, layer)
    return unit(trunk._w / trunk._scale)


# ----------------------------------------------------------------------------
# Commitment direction from Stage 1 activations
# ----------------------------------------------------------------------------

def build_commitment_perp(stage1_dir: Path, pool: list[dict],
                          matched_idx: list[int], layer: str,
                          caution_u: np.ndarray) -> dict:
    """arm-B commitment direction on the matched set, orthogonalized to caution.

    d = mean(confab@anchor) - mean(refuse@anchor) over the matched set at
    `layer`; d_perp = d - (d.caution_u) caution_u; theta_u = unit(d_perp).
    sigma = std of matched-set projections onto theta_u (dose scale). Requires
    the Stage 1 raw-base arm's activations (same config_sha 0dcb65d0062db64a).
    """
    confab_vecs, refuse_vecs = [], []
    proj_all = []
    for i in matched_idx:
        r = pool[i]
        sk = safe_key_for(r["row_key"])
        v = ak.load_vec(stage1_dir, sk, layer, "anchor")
        if v is None:
            continue
        (confab_vecs if r["confab_on_unanswerable"] else refuse_vecs).append(v)
    if not confab_vecs or not refuse_vecs:
        raise RuntimeError(
            f"empty confab/refuse at {layer}@anchor "
            f"(confab={len(confab_vecs)} refuse={len(refuse_vecs)}); "
            "check the Stage 1 raw-base tensor dir")
    mc = np.mean(np.stack(confab_vecs), axis=0)
    mr = np.mean(np.stack(refuse_vecs), axis=0)
    d = mc - mr
    align = float(unit(d) @ caution_u)
    d_perp = d - (d @ caution_u) * caution_u
    perp_frac = float(np.linalg.norm(d_perp) / (np.linalg.norm(d) + 1e-12))
    theta_u = unit(d_perp)
    for v in confab_vecs + refuse_vecs:
        proj_all.append(float(v @ theta_u))
    sigma = float(np.std(np.asarray(proj_all)))
    return {
        "schema_version": "ak-stage2-commitment-perp/v1",
        "layer": layer,
        "block": int(layer[1:]) - 1,
        "theta": [float(x) for x in theta_u],
        "sigma": sigma,
        "hidden_dim": int(theta_u.shape[0]),
        "raw_cos_commitment_caution": align,
        "perp_fraction_of_commitment": perp_frac,
        "n_confab_matched": len(confab_vecs),
        "n_refuse_matched": len(refuse_vecs),
        "convention": ("d = mean(confab)-mean(refuse) @ <layer>@anchor on matched "
                       "set; d_perp = d - (d.caution_u) caution_u; B1 convention; "
                       "dose = alpha*sigma*unit(d_perp)"),
    }


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------

def build_model(base_path: str, load_in_4bit: bool):
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_path, max_seq_length=2048, dtype=None,
        load_in_4bit=load_in_4bit)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastLanguageModel.for_inference(model)
    return model, tokenizer


# ----------------------------------------------------------------------------
# Steering run
# ----------------------------------------------------------------------------

def run_steer(args) -> int:
    import torch
    import scorers
    from backends import render_probe_prompt
    from confidence_steer import SteeringHook, get_decoder_layer
    from steering_common import GenerationHookController

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_jsonl(Path(args.pool))
    layer = args.steer_layer
    layer_idx = int(layer[1:])

    probes_dir = Path(args.probes_dir).resolve()
    caution_u = caution_axis_raw(probes_dir, layer)

    stage1_dir = Path(args.stage1_dir).resolve()
    matched_idx = matched_set_indices(pool, caliper=args.caliper,
                                      seed=args.match_seed)
    if args.limit:
        matched_idx = matched_idx[: args.limit]
    dir_info = build_commitment_perp(stage1_dir, pool, matched_idx, layer,
                                     caution_u)
    (out_dir / "direction.json").write_text(json.dumps(dir_info, indent=2),
                                            encoding="utf-8")
    theta = np.asarray(dir_info["theta"], dtype=np.float32)
    sigma = float(dir_info["sigma"])

    alphas = [float(a) for a in args.alphas.split(",")] if args.alphas \
        else list(DEFAULT_ALPHAS)
    if 0.0 not in alphas:
        alphas = [0.0] + alphas
    positions = ["anchor", "gen_stream"] if not args.smoke \
        else ["anchor", "gen_stream"]

    config_payload = {
        "amendment": "AK", "stage": "stage2_commitment_steer",
        "base_model": args.base_model, "load_in_4bit": bool(args.load_in_4bit),
        "checkpoint_tag": "raw-base", "model_tag": MODEL_TAG,
        "baseline_system_prompt": baseline_system, "prime": "NONE-baseline-only",
        "enable_thinking": False, "decode": "greedy", "do_sample": False,
        "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS,
        "steer_layer": layer, "steer_block": layer_idx - 1,
        "alphas_sigma_units": alphas, "positions": positions,
        "dose_formula": "h += alpha*sigma*theta_u at steered positions",
        "sigma": sigma, "match_caliper_z": args.caliper,
        "match_seed": args.match_seed, "n_matched": len(matched_idx),
        "direction_provenance": {k: v for k, v in dir_info.items()
                                 if k != "theta"},
    }
    config_sha = _config_sha(config_payload)

    print(f"[ak/stage2] layer={layer} sigma={sigma:.4f} "
          f"n_matched={len(matched_idx)} alphas={alphas} "
          f"perp_frac={dir_info['perp_fraction_of_commitment']:.3f} "
          f"cos(commit,caution)={dir_info['raw_cos_commitment_caution']:.3f} "
          f"config_sha={config_sha}", flush=True)

    model, tokenizer = build_model(args.base_model, args.load_in_4bit)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    if layer_idx > n_layers:
        raise RuntimeError(f"steer layer {layer} > n_layers {n_layers}")

    d_tensor = torch.from_numpy(theta).to(device)
    hook = SteeringHook(d=d_tensor, alpha=0.0, position="anchor")
    controller = GenerationHookController(hook)
    layer_module = get_decoder_layer(model, layer_idx)
    handle = layer_module.register_forward_hook(controller)

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

    def generate(question: str, mode: str, alpha_sigma: float):
        rendered, _mode = render_probe_prompt(
            tokenizer, baseline_system, question, enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        controller.begin_pass(mode, alpha_sigma)
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                num_beams=1, eos_token_id=eos_for_gen,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                return_dict_in_generate=True)
        full = gen.sequences[0].tolist()
        new_ids = full[prompt_len:]
        answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        content_end = _content_end_index(full, prompt_len, special_ids)
        return answer_text, content_end, prompt_len, len(new_ids)

    def grade(answer_text: str, content_end):
        refused = scorers.is_stated_confidence_refusal(answer_text)
        answered = ((content_end is not None) and bool(answer_text)
                    and not refused)
        # AK pool is unanswerable-only: confab == answered on unanswerable.
        confab = bool(answered)
        return refused, answered, confab, is_degenerate(answer_text)

    # ------------------------------------------------------------------
    # readback (--smoke or --readback): the commanded projection must move by
    # ~alpha*sigma at steered positions and stay put elsewhere. Uses the
    # steered-minus-unsteered DELTA at the layer output (the gpu_equivalence_cell
    # logic) so the model's own numerics cancel.
    # ------------------------------------------------------------------
    readback = {"performed": False}
    if args.smoke or args.readback:
        readback = _readback_check(
            model, tokenizer, controller, hook, layer_module, theta, sigma,
            device, baseline_system, pool[matched_idx[0]]["question"],
            render_probe_prompt, tol_frac=READBACK_TOL_FRAC)
        print(f"[ak/stage2] readback {readback}", flush=True)
        if not readback.get("passed"):
            handle.remove()
            raise RuntimeError(f"AK Stage 2 readback FAILED: {readback}")

    # ------------------------------------------------------------------
    # arms: {each alpha} x {each position}. alpha=0 is the shared baseline; it
    # is generated ONCE per position (identical under both modes since alpha=0
    # never steers) but we key it per (position, alpha) for a uniform record set.
    # ------------------------------------------------------------------
    rows_path = out_dir / "rows.jsonl"
    counts: dict[str, int] = {}
    t0 = time.time()
    written = 0
    with rows_path.open("w", encoding="utf-8") as fh:
        for i in matched_idx:
            r = pool[i]
            question = r["question"]
            sk = safe_key_for(r["row_key"])
            for position in positions:
                for alpha in alphas:
                    dose = alpha * sigma
                    answer_text, content_end, plen, n_gen = generate(
                        question, position, dose)
                    refused, answered, confab, degen = grade(
                        answer_text, content_end)
                    arm_id = f"{position}@a{alpha:+g}"
                    counts[arm_id] = counts.get(arm_id, 0) + int(confab)
                    fh.write(json.dumps({
                        "row_key": r["row_key"], "safe_key": sk,
                        "confab_baseline": bool(r["confab_on_unanswerable"]),
                        "caution_dist_z": r.get("caution_dist_z"),
                        "category_canon": r.get("category_canon", ""),
                        "position": position, "alpha": alpha,
                        "alpha_sigma": dose, "arm_id": arm_id,
                        "refused": refused, "answered": answered,
                        "confab": confab, "degenerate": degen,
                        "n_generated": n_gen, "prompt_len": plen,
                        "config_sha": config_sha,
                        # NO question / answer text (safe_key + grades only)
                    }, ensure_ascii=False) + "\n")
                    fh.flush()
                    written += 1
            if (written // max(len(positions) * len(alphas), 1)) % 25 == 0:
                el = time.time() - t0
                print(f"[ak/stage2] {written} gens {el:.0f}s "
                      f"({written/max(el,1e-6):.2f}/s)", flush=True)
    handle.remove()

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": int(theta.shape[0]), "n_matched": len(matched_idx),
        "n_generations": written, "arm_confab_counts": counts,
        "readback": readback, "runtime_sec": round(time.time() - t0, 1),
        "controller_pass_log_len": len(controller.pass_log),
        "out_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[ak/stage2] DONE {written} generations -> {out_dir}", flush=True)
    return 0


def _readback_check(model, tokenizer, controller, hook, layer_module, theta,
                    sigma, device, system_prompt, question,
                    render_probe_prompt, tol_frac: float) -> dict:
    """Verify the commanded projection moves by ~alpha*sigma at the steered
    position and stays ~0 elsewhere, using the steered-minus-unsteered delta.

    anchor mode: the delta at the LAST prompt token (prefill) must be ~alpha*sigma
      along theta; other positions ~0.
    gen_stream mode: the delta at the first DECODE step must be ~alpha*sigma.
    """
    import torch

    theta_t = torch.from_numpy(theta).to(device)
    alpha = 1.0
    dose = alpha * sigma
    rendered, _ = render_probe_prompt(tokenizer, system_prompt, question,
                                      enable_thinking=False)
    enc = tokenizer(rendered, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])

    captured = {}

    def _capture(name):
        def hook_fn(module, inputs, output):
            h = output[0] if isinstance(output, tuple) else output
            captured[name] = h.detach().float().cpu()
        return hook_fn

    # ---- anchor mode: single prefill forward, steered vs unsteered ----
    cap_handle = layer_module.register_forward_hook(_capture("anchor_steer"))
    controller.begin_pass("anchor", dose)
    with torch.no_grad():
        model(**enc, use_cache=False)
    cap_handle.remove()
    cap_handle = layer_module.register_forward_hook(_capture("anchor_base"))
    controller.begin_pass("off", 0.0)
    with torch.no_grad():
        model(**enc, use_cache=False)
    cap_handle.remove()

    hs = captured["anchor_steer"][0]      # (seq, hidden)
    hb = captured["anchor_base"][0]
    delta = (hs - hb).numpy()             # steered - unsteered
    theta_np = theta.astype(np.float64)
    proj = delta @ theta_np               # (seq,)
    last = prompt_len - 1
    proj_last = float(proj[last])
    # every other position's projection magnitude
    other = np.delete(np.abs(proj), last)
    other_max = float(other.max()) if other.size else 0.0
    tol = tol_frac * abs(dose)
    anchor_ok = (abs(proj_last - dose) <= max(tol, 1e-3)
                 and other_max <= max(tol, 1e-3))

    return {
        "performed": True, "alpha": alpha, "sigma": sigma,
        "commanded_dose": dose,
        "anchor_proj_at_last_prompt_tok": proj_last,
        "anchor_other_pos_max_abs": other_max,
        "tol": max(tol, 1e-3), "anchor_ok": bool(anchor_ok),
        "passed": bool(anchor_ok),
        "note": ("anchor delta at last prompt token ~= alpha*sigma and ~0 "
                 "elsewhere; gen_stream per-decode steering is exercised by the "
                 "full-run pass_log and the CPU controller regression test"),
    }


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True,
                    help="ak_stage1_pool.jsonl (private staging; carries the "
                         "confab labels + caution_dist_z for the matched set)")
    ap.add_argument("--stage1-dir", required=True,
                    help="AK Stage 1 raw-base tensor dir (rows.jsonl + "
                         "<safe_key>.safetensors with <layer>@anchor)")
    ap.add_argument("--probes-dir", required=True,
                    help="analysis/ah_stage0/probes (frozen AH answerability "
                         "probes; caution axis source)")
    ap.add_argument("--base-model", default=MODEL_NAME,
                    help="raw instruct base (arm-B native surface)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--steer-layer", default=DEFAULT_STEER_LAYER,
                    help="steering layer within the arm-B L24-28 band")
    ap.add_argument("--alphas", default=",".join(str(a) for a in DEFAULT_ALPHAS),
                    help="comma alphas in sigma units (0 always included)")
    ap.add_argument("--caliper", type=float, default=0.20,
                    help="within-flavor caution_dist_z match caliper")
    ap.add_argument("--match-seed", type=int, default=20260704)
    ap.add_argument("--load-in-4bit", action="store_true", default=True)
    ap.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap matched rows (smoke uses this)")
    ap.add_argument("--smoke", action="store_true",
                    help="pre-registered smoke: force the readback check and a "
                         "small run; combine with --limit 10 --alphas 1")
    ap.add_argument("--readback", action="store_true",
                    help="run the readback check before the arms (implied by "
                         "--smoke)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    return run_steer(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
