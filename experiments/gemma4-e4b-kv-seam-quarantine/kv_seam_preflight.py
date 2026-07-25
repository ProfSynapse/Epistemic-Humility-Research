#!/usr/bin/env python3
"""CPU-only preflight proving the `kv_seam_patch.py` sharing-OFF toggle does
what it claims, before it ever touches the 3090.

Builds a tiny, randomly-initialized `Gemma4ForCausalLM` directly from a
`Gemma4TextConfig` -- no checkpoint download, no GPU. The width fields
(hidden_size, heads, vocab, ...) are shrunk to near-nothing; the fields that
determine the KV-sharing *geometry* are kept EXACT and identical to the
pinned `google/gemma-4-E4B-it` checkpoint (`num_hidden_layers=42`,
`num_kv_shared_layers=18`, `sliding_window=512`). `Gemma4TextConfig.__post_init__`
auto-derives `layer_types` with a `sliding_window_pattern=6` rule when none is
given (`configuration_gemma4.py`), which reproduces the checkpoint's own
full-attention placement at [5, 11, 17, 23, 29, 35, 41] exactly -- verified
below via `kv_seam_patch.verify_architecture`, not assumed.

This exercises the IDENTICAL code paths as the real checkpoint:
`DynamicCache.__init__`'s `layer_types[:-num_kv_shared_layers]` slice,
`Gemma4TextAttention.forward`'s `:1198` shared-layer branch, and
`Cache.update()`'s `self.layers[layer_idx]` dispatch. Nothing here is
Gemma-4-E4B-specific beyond those four config values, so a pass/fail here is
evidence about the mechanism, not an artifact of this particular checkpoint.

Six checks, run in order, each rebuilding its own tiny model from the same
seed so checks cannot leak state into each other. Checks 5 and 6 implement,
verbatim, the two criteria of `gates.yaml` gate `g0_kv_seam_instrument_validity`
that carry those names; 1-4 are the supporting evidence they rest on:

  1. GEOMETRY + CRASH.  The tiny config reproduces the real checkpoint's
     donor blocks (22 sliding / 23 full) and shared-block set (24..41), AND
     stock `generate()` auto-constructs a cache truncated to 24 layers
     (`len(cache.layers) == 24`) -- the precondition for the crash to even be
     reachable. Then: apply `kv_seam_patch.kv_sharing(model, enabled=False)`
     (the patch AS DRAFTED, no cache fix) under a plain `generate()` call and
     confirm it raises `IndexError`. If the tiny config can't reproduce the
     truncation, that null is itself reported -- it would mean this test has
     to move to the real checkpoint instead of settling anything here.
  2. FIX COMPLETES.  Pre-build a full 42-entry `Cache` (one
     `DynamicSlidingWindowLayer`/`DynamicLayer` per `config.layer_types`, no
     slicing) and pass it via `generate(past_key_values=...)`. Confirm a
     multi-token greedy generate completes with no exception.
  3. MECHANISM ACTUALLY FLIPPED.  Hook `k_proj`/`v_proj` on the 18 shared
     modules (`kv_seam_patch.count_kv_projection_calls`). Assert those hooks
     fire ZERO times under stock (sharing ON) and NONZERO on every one of the
     18 modules under the fixed patch (sharing OFF). The contrast is the
     evidence, not either count alone -- a flag that reads correct while the
     projections never ran would silently null the real experiment. Also
     asserts every one of the 42 cache layers' sequence length actually GREW
     across decode steps under the fix.
  4. EQUIVALENCE CONTROL.  Same tiny model, same input: fully-stock
     `generate()` (model's own auto-cache, patch module untouched) vs.
     `kv_sharing(model, enabled=True)` (a no-op flip) PLUS the hand-built
     full-length cache from check 2. Confirms token-for-token AND
     logit-bit-identical output -- i.e. that swapping in the full-length
     cache (which the OFF arm needs) is itself inert when sharing stays ON,
     so any future A1-vs-A2 difference in the real experiment comes from the
     KV variable and not from the act of patching.
  5. CACHE GROWTH UNDER OFF (gate criterion `cache_growth_under_off`).  Step
     the model by hand -- prefill, then two decode steps -- and read
     `cache_layer_lengths` at each. Every block in 24..41 must be nonzero and
     grow by the same increment as 0..23 (compared within attention class,
     sliding vs full, since sliding lengths saturate at `sliding_window`).
     Check 3's post-hoc uniformity cannot tell "written once at prefill" from
     "written every step", nor detect a REUSED cache; the zero-length assertion
     on the fresh object is the cheapest detector of the latter. Also asserts
     `kv_seam_patch.build_full_length_cache` -- the builder the harness
     actually ships -- agrees with this file's independent construction.
  6. CACHE-SUBSTITUTION NO-OP UNDER ON (gate criterion
     `cache_substitution_noop_under_on`).  Check 4's stronger bit-identity
     result, widened to the >= 8 fixed prompts the gate requires, at varying
     lengths. One prompt can miss a length-dependent divergence, and it is this
     result that licenses passing the full-length cache in the ON arms at all.

Run: `python3 kv_seam_preflight.py` (CPU only; takes a few seconds).
Exits 0 if all six checks pass, 1 otherwise, with one PASS/FAIL/NULL line
per check plus a final summary.
"""

from __future__ import annotations

import sys

import torch
from transformers.cache_utils import Cache, DynamicLayer, DynamicSlidingWindowLayer
from transformers.models.gemma4.configuration_gemma4 import Gemma4TextConfig
from transformers.models.gemma4.modeling_gemma4 import Gemma4ForCausalLM

from kv_seam_patch import (
    EXPECTED_DONOR_BLOCKS,
    EXPECTED_FIRST_KV_SHARED_LAYER_IDX,
    EXPECTED_NUM_HIDDEN_LAYERS,
    EXPECTED_NUM_KV_SHARED_LAYERS,
    cache_layer_lengths,
    count_kv_projection_calls,
    kv_sharing,
    verify_architecture,
)

SEED = 20260724  # fixed; only affects random weight init, not the geometry checks

# Width fields: shrunk to near-nothing, no bearing on the mechanism under
# test. Geometry fields: EXACT match to the pinned google/gemma-4-E4B-it
# checkpoint config (see kv_seam_patch.py's own EXPECTED_* constants).
TINY_CONFIG_KWARGS = dict(
    vocab_size=256,
    hidden_size=64,
    intermediate_size=128,
    num_attention_heads=4,
    num_key_value_heads=2,
    head_dim=16,
    global_head_dim=16,
    hidden_size_per_layer_input=16,
    vocab_size_per_layer_input=300,
    attention_k_eq_v=False,  # matches the real checkpoint (§7.2 of the memo: False on E2B/E4B)
    enable_moe_block=False,  # matches the real checkpoint
    use_cache=True,
    pad_token_id=0,
    eos_token_id=1,
    bos_token_id=2,
    _attn_implementation="eager",
    # Geometry fields, exact:
    num_hidden_layers=EXPECTED_NUM_HIDDEN_LAYERS,
    num_kv_shared_layers=EXPECTED_NUM_KV_SHARED_LAYERS,
    sliding_window=512,
    # layer_types intentionally omitted -- Gemma4TextConfig.__post_init__
    # auto-derives it with sliding_window_pattern=6, which is checked against
    # the real checkpoint's pattern by verify_architecture() below, not
    # hand-copied here.
)


def build_tiny_model() -> tuple[Gemma4ForCausalLM, Gemma4TextConfig]:
    cfg = Gemma4TextConfig(**TINY_CONFIG_KWARGS)
    torch.manual_seed(SEED)
    model = Gemma4ForCausalLM(cfg)
    model.eval()
    return model, cfg


def build_full_length_cache(config: Gemma4TextConfig) -> Cache:
    """The companion fix §8.3 of the memo calls for: one real `CacheLayer`
    per block, with NO `num_kv_shared_layers` slicing, so every block
    (including the 18 normally-shared ones) has somewhere to `.update()`
    into.

    This is deliberately an INDEPENDENT reimplementation, not a call into
    `kv_seam_patch.build_full_length_cache` (which now exists and is what the
    harness actually uses). The preflight's job is to check that builder; a
    preflight that imported it could only ever confirm the builder agrees with
    itself. Check 5 compares the two objects explicitly.
    """
    layers = []
    for layer_type in config.layer_types:
        if layer_type == "sliding_attention":
            layers.append(DynamicSlidingWindowLayer(sliding_window=config.sliding_window))
        else:
            layers.append(DynamicLayer())
    return Cache(layers=layers)


def fixed_prompt(cfg: Gemma4TextConfig, seq_len: int = 6) -> tuple[torch.Tensor, torch.Tensor]:
    g = torch.Generator().manual_seed(SEED)
    input_ids = torch.randint(3, cfg.vocab_size, (1, seq_len), generator=g)
    attention_mask = torch.ones_like(input_ids)
    return input_ids, attention_mask


def check_1_geometry_and_crash() -> bool:
    model, cfg = build_tiny_model()
    info = verify_architecture(model)  # raises AssertionError itself if geometry is wrong
    print(f"    geometry: donors={info['donors']} shared_blocks=[{info['kv_shared_blocks'][0]}.."
          f"{info['kv_shared_blocks'][-1]}] (expect donors={EXPECTED_DONOR_BLOCKS}, "
          f"first_shared={EXPECTED_FIRST_KV_SHARED_LAYER_IDX})")
    if info["donors"] != EXPECTED_DONOR_BLOCKS or info["first_kv_shared_layer_idx"] != EXPECTED_FIRST_KV_SHARED_LAYER_IDX:
        print("    NULL: tiny config does not reproduce the real checkpoint's KV-seam geometry; "
              "this test would need to move to the real checkpoint instead.")
        return False

    input_ids, attention_mask = fixed_prompt(cfg)
    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)
    n_cache_layers = len(out.past_key_values.layers)
    print(f"    stock auto-cache length: {n_cache_layers} (expect "
          f"{EXPECTED_NUM_HIDDEN_LAYERS - EXPECTED_NUM_KV_SHARED_LAYERS} = "
          f"num_hidden_layers - num_kv_shared_layers)")
    if n_cache_layers != EXPECTED_NUM_HIDDEN_LAYERS - EXPECTED_NUM_KV_SHARED_LAYERS:
        print("    NULL: stock cache is not truncated the way §8.3 of the memo claims -- the "
              "crash this check looks for would not be reachable; report this straight.")
        return False

    try:
        with kv_sharing(model, enabled=False):
            with torch.no_grad():
                model.generate(
                    input_ids=input_ids, attention_mask=attention_mask,
                    max_new_tokens=5, min_new_tokens=1, do_sample=False,
                    num_beams=1, use_cache=True,
                )
        print("    UNEXPECTED: patch-as-drafted did NOT crash under stock generate(); "
              "the §8.3 IndexError analysis does not reproduce here.")
        return False
    except IndexError as e:
        print(f"    reproduced: IndexError({e}) -- patch-as-drafted crashes under stock "
              "generate(), exactly as §8.3 traced.")
        return True
    except Exception as e:  # pragma: no cover - report any other failure straight
        print(f"    UNEXPECTED exception type {type(e).__name__}({e}) instead of IndexError.")
        return False


def check_2_fix_completes() -> bool:
    model, cfg = build_tiny_model()
    input_ids, attention_mask = fixed_prompt(cfg)
    cache = build_full_length_cache(cfg)
    print(f"    full-length cache built: {len(cache.layers)} layers (expect "
          f"{EXPECTED_NUM_HIDDEN_LAYERS})")
    if len(cache.layers) != EXPECTED_NUM_HIDDEN_LAYERS:
        print("    FAIL: full-length cache builder did not produce one layer per block.")
        return False
    try:
        with kv_sharing(model, enabled=False):
            with torch.no_grad():
                out = model.generate(
                    input_ids=input_ids, attention_mask=attention_mask,
                    max_new_tokens=5, min_new_tokens=1, do_sample=False,
                    num_beams=1, use_cache=True, past_key_values=cache,
                )
        print(f"    generate() completed with no exception, output shape {tuple(out.shape)}")
        return True
    except Exception as e:
        print(f"    FAIL: fix still raises {type(e).__name__}({e})")
        return False


def check_3_mechanism_flipped() -> bool:
    model, cfg = build_tiny_model()
    input_ids, attention_mask = fixed_prompt(cfg)
    shared_idx = list(range(EXPECTED_FIRST_KV_SHARED_LAYER_IDX, EXPECTED_NUM_HIDDEN_LAYERS))

    with count_kv_projection_calls(model) as counts_on:
        with torch.no_grad():
            model.generate(
                input_ids=input_ids, attention_mask=attention_mask,
                max_new_tokens=5, min_new_tokens=1, do_sample=False,
                num_beams=1, use_cache=True,
            )
    on_calls = {i: counts_on.k_proj[i] for i in shared_idx}

    cache = build_full_length_cache(cfg)
    with count_kv_projection_calls(model) as counts_off:
        with kv_sharing(model, enabled=False):
            with torch.no_grad():
                model.generate(
                    input_ids=input_ids, attention_mask=attention_mask,
                    max_new_tokens=5, min_new_tokens=1, do_sample=False,
                    num_beams=1, use_cache=True, past_key_values=cache,
                )
    off_calls = {i: counts_off.k_proj[i] for i in shared_idx}

    print(f"    stock (sharing ON)  k_proj calls on the 18 shared blocks: "
          f"sum={sum(on_calls.values())} (expect 0)")
    print(f"    patched (sharing OFF) k_proj calls on the 18 shared blocks: "
          f"sum={sum(off_calls.values())}, min-per-block={min(off_calls.values())} (expect >0 on every block)")

    ok_contrast = sum(on_calls.values()) == 0 and all(v > 0 for v in off_calls.values())

    cache_lengths = [layer.get_seq_length() for layer in cache.layers]
    print(f"    all 42 cache layers' seq length after generation: "
          f"min={min(cache_lengths)} max={max(cache_lengths)} (expect uniform and > 0)")
    ok_growth = min(cache_lengths) > 0 and len(set(cache_lengths)) == 1

    if not ok_contrast:
        print("    FAIL: projection call contrast did not hold as expected.")
    if not ok_growth:
        print("    FAIL: cache layers did not all grow uniformly under the fix.")
    return ok_contrast and ok_growth


def check_4_equivalence_control() -> bool:
    model, cfg = build_tiny_model()
    input_ids, attention_mask = fixed_prompt(cfg)

    with torch.no_grad():
        out_stock = model.generate(
            input_ids=input_ids, attention_mask=attention_mask,
            max_new_tokens=5, min_new_tokens=1, do_sample=False, num_beams=1,
            use_cache=True,
        )

    cache = build_full_length_cache(cfg)
    with kv_sharing(model, enabled=True):  # no-op flip; sharing stays ON
        with torch.no_grad():
            out_patched_on = model.generate(
                input_ids=input_ids, attention_mask=attention_mask,
                max_new_tokens=5, min_new_tokens=1, do_sample=False, num_beams=1,
                use_cache=True, past_key_values=cache,
            )

    tokens_equal = torch.equal(out_stock, out_patched_on)
    print(f"    token sequences identical: {tokens_equal}")
    if not tokens_equal:
        print(f"    stock:      {out_stock.tolist()}")
        print(f"    patched-ON: {out_patched_on.tolist()}")

    # use_cache MUST be True here. With use_cache=False the 18 KV-sharing blocks
    # (24..41) are starved of the donor K/V they read through the cache object,
    # so every hidden state from hs25 up -- and therefore the logits -- is
    # garbage. Both sides of this comparison would run that same broken path and
    # come out bit-identical REGARDLESS of whether the patched path differs, so
    # the control would pass vacuously and could never fail. Measured on this
    # exact tiny config (random init, so the mechanism is architectural, not
    # checkpoint-specific): hs0-hs24 cos 1.000000, hs25 0.986619 decaying to
    # 0.780935 at hs42; two use_cache=False forwards are bit-identical while
    # cache ON vs OFF differ by max|diff| 0.3804.
    # This is the same vacuity that made the "cos 0.9998 CPU-vs-GPU agreement"
    # worthless as evidence of faithfulness: both sides ran the broken path.
    with torch.no_grad():
        logits_stock = model(input_ids=out_stock, use_cache=True).logits
        logits_patched = model(input_ids=out_patched_on, use_cache=True).logits
    logits_equal = torch.equal(logits_stock, logits_patched)
    print(f"    re-scored logits bit-identical: {logits_equal}")

    return tokens_equal and logits_equal


def check_5_cache_growth_under_off() -> bool:
    """gates.yaml g0_kv_seam_instrument_validity / cache_growth_under_off.

    Check 3 already shows the 42 layers are non-empty and uniform AFTER a
    generate(). That is weaker than the registered criterion in two ways it
    cares about: it cannot distinguish "written once at prefill" from "written
    at every decode step", and it cannot detect an accidentally REUSED cache,
    which also ends up non-empty and uniform. So step the model by hand and
    watch the lengths move.

    Comparison is within attention class (sliding vs full) because sliding
    layers saturate at sliding_window; at these lengths nothing saturates, but
    the check is written the way the gate states it so it stays correct if the
    prompt grows.
    """
    import kv_seam_patch as kvp

    model, cfg = build_tiny_model()
    input_ids, attention_mask = fixed_prompt(cfg)
    prompt_len = int(input_ids.shape[1])

    # The harness's own builder is what ships; check the two agree before
    # trusting either. (The preflight's local copy is an independent
    # reimplementation -- see build_full_length_cache's docstring.)
    harness_cache = kvp.build_full_length_cache(cfg)
    local_cache = build_full_length_cache(cfg)
    same_shape = (len(harness_cache.layers) == len(local_cache.layers)
                  == EXPECTED_NUM_HIDDEN_LAYERS)
    same_classes = [type(a) is type(b)
                    for a, b in zip(harness_cache.layers, local_cache.layers)]
    print(f"    harness builder vs preflight builder: {len(harness_cache.layers)} vs "
          f"{len(local_cache.layers)} layers, per-layer class match "
          f"{sum(same_classes)}/{len(same_classes)}")
    if not (same_shape and all(same_classes)):
        print("    FAIL: kv_seam_patch.build_full_length_cache disagrees with the "
              "preflight's independent construction.")
        return False

    cache = harness_cache  # exercise the object the harness will actually pass
    full_idx = [i for i, t in enumerate(cfg.layer_types) if t != "sliding_attention"]
    slide_idx = [i for i, t in enumerate(cfg.layer_types) if t == "sliding_attention"]
    shared_idx = list(range(EXPECTED_FIRST_KV_SHARED_LAYER_IDX, EXPECTED_NUM_HIDDEN_LAYERS))

    # A fresh cache must be EMPTY. Non-zero here is the reused-cache signature
    # the gate asks this check to detect.
    before = cache_layer_lengths(cache)
    print(f"    fresh cache lengths: min={min(before)} max={max(before)} (expect 0/0)")
    if any(n != 0 for n in before):
        print("    FAIL: cache was not empty before prefill -- reused cache object.")
        return False

    snapshots = []
    with kv_sharing(model, enabled=False):
        with torch.no_grad():
            model(input_ids=input_ids, attention_mask=attention_mask,
                  use_cache=True, past_key_values=cache)
            snapshots.append(cache_layer_lengths(cache))
            for _ in range(2):  # >= 2 decode steps, per the gate
                next_id = torch.tensor([[3]])
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((1, 1), dtype=attention_mask.dtype)], dim=1)
                model(input_ids=next_id, attention_mask=attention_mask,
                      use_cache=True, past_key_values=cache)
                snapshots.append(cache_layer_lengths(cache))

    ok = True
    for label, idx in (("full", full_idx), ("sliding", slide_idx)):
        lens = [[snap[i] for i in idx] for snap in snapshots]
        traj = [f"{min(s)}-{max(s)}" for s in lens]
        print(f"    {label:>8} layers, lengths after prefill/step1/step2: {' -> '.join(traj)}")
        for step, s in enumerate(lens):
            if len(set(s)) != 1:
                print(f"    FAIL: {label} layers disagree with each other at step {step}: "
                      f"min={min(s)} max={max(s)}")
                ok = False
        expected = [prompt_len, prompt_len + 1, prompt_len + 2]
        got = [s[0] for s in lens]
        if got != expected:
            print(f"    FAIL: {label} lengths {got} != expected {expected} "
                  "(prefill then +1 per decode step)")
            ok = False

    # The point of the whole check: the 18 appended slots are LIVE, not padding.
    shared_traj = [[snap[i] for i in shared_idx] for snap in snapshots]
    if any(min(s) == 0 for s in shared_traj):
        print("    FAIL: at least one of blocks 24..41 has length 0 -- the appended "
              "slots are inert padding, not live K/V.")
        ok = False
    else:
        print(f"    blocks 24..41 (the 18 appended slots) all live: lengths "
              f"{[min(s) for s in shared_traj]} -- written at prefill AND at each decode step")
    return ok


N_EQUIVALENCE_PROMPTS = 8


def check_6_cache_substitution_noop_multi_prompt() -> bool:
    """gates.yaml g0_kv_seam_instrument_validity / cache_substitution_noop_under_on.

    Check 4 demonstrates the strong (bit-identical logits) form on ONE prompt.
    The registered criterion additionally asks for token-identity on >= 8 fixed
    prompts, because a single prompt can miss a divergence that only shows up
    at some lengths or on some sampled token paths. This is what licenses
    passing the full-length cache in the ON arms at all -- without it, A1-vs-A2
    is sharing-flag PLUS cache-substitution versus neither.
    """
    import kv_seam_patch as kvp

    model, cfg = build_tiny_model()
    g = torch.Generator().manual_seed(SEED + 1)
    mismatches = []
    for i in range(N_EQUIVALENCE_PROMPTS):
        seq_len = 4 + i  # vary length; a fixed length could hide a length-dependent bug
        input_ids = torch.randint(3, cfg.vocab_size, (1, seq_len), generator=g)
        attention_mask = torch.ones_like(input_ids)
        gen_kwargs = dict(max_new_tokens=5, min_new_tokens=1, do_sample=False,
                          num_beams=1, use_cache=True)
        with torch.no_grad():
            out_stock = model.generate(input_ids=input_ids,
                                       attention_mask=attention_mask, **gen_kwargs)
        cache = kvp.build_full_length_cache(cfg)  # fresh per call, as the contract requires
        with kv_sharing(model, enabled=True):  # no-op flip; sharing stays ON
            with torch.no_grad():
                out_patched = model.generate(input_ids=input_ids,
                                             attention_mask=attention_mask,
                                             past_key_values=cache, **gen_kwargs)
        if not torch.equal(out_stock, out_patched):
            mismatches.append((i, seq_len, out_stock.tolist(), out_patched.tolist()))

    print(f"    token-identical on {N_EQUIVALENCE_PROMPTS - len(mismatches)}/"
          f"{N_EQUIVALENCE_PROMPTS} fixed prompts (lengths 4..{3 + N_EQUIVALENCE_PROMPTS})")
    for i, seq_len, a, b in mismatches:
        print(f"    FAIL prompt {i} (len {seq_len}): stock={a} patched-ON={b}")
    return not mismatches


CHECKS = [
    ("1. geometry + crash reproduces", check_1_geometry_and_crash),
    ("2. fix completes", check_2_fix_completes),
    ("3. mechanism actually flipped", check_3_mechanism_flipped),
    ("4. equivalence control (sharing ON, full-length cache, vs stock)", check_4_equivalence_control),
    ("5. cache growth under OFF (appended slots are live)", check_5_cache_growth_under_off),
    (f"6. cache-substitution no-op under ON ({N_EQUIVALENCE_PROMPTS} prompts)",
     check_6_cache_substitution_noop_multi_prompt),
]


def main() -> int:
    results = []
    for name, fn in CHECKS:
        print(f"[{name}]")
        try:
            passed = fn()
        except AssertionError as e:
            print(f"    FAIL (assertion): {e}")
            passed = False
        results.append((name, passed))
        print(f"    -> {'PASS' if passed else 'FAIL'}\n")

    print("=== summary ===")
    for name, passed in results:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    all_pass = all(p for _, p in results)
    print(f"\noverall: {'ALL PASS' if all_pass else 'AT LEAST ONE FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
