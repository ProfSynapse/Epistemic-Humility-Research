"""Gemma-4 KV-sharing seam toggle + the preflight assertions that make it trustworthy.

This is the one genuinely NEW instrument in this experiment. Everything else in
this directory is an unmodified copy of the parent
`j-space-cross-family-layer-contrast` instrument (see AMENDMENT.md "Instrument").

Architecture facts this module depends on, all read from the executing source
(`transformers==5.5.0`, `models/gemma4/modeling_gemma4.py`) and the pinned
checkpoint config (`google/gemma-4-E4B-it`, snapshot
`fee6332c1abaafb77f6f9624236c63aa2f1d0187`):

    num_hidden_layers        = 42
    num_kv_shared_layers     = 18
    first_kv_shared_layer_idx = 42 - 18 = 24
    donor(full_attention)     = block 23     # last full block in layer_types[:24]
    donor(sliding_attention)  = block 22     # last sliding block in layer_types[:24]

`Gemma4TextAttention.__init__` (`:1147-1160`) sets three per-module attributes
from those numbers -- `is_kv_shared_layer`, `kv_shared_layer_index`,
`store_full_length_kv` -- and `forward` (`:1198-1220`) branches on them: a
KV-shared layer skips `k_proj`/`v_proj` entirely and reads K/V out of
`past_key_values.shared_layers[donor]`.

Toggling those attributes is therefore sufficient to switch the mechanism off
WITHOUT touching weights, config, or any other computation. That is the point:
the OFF condition must differ from ON in the KV pathway and nowhere else.

NOTHING in this module is generic. It is Gemma-4-specific by construction and
must not be promoted into `synaptic-tuner/` (root CLAUDE.md ownership boundary).
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

import torch


# Verified from the pinned checkpoint config; asserted at runtime against the
# live config so a checkpoint swap cannot silently invalidate the design.
EXPECTED_NUM_HIDDEN_LAYERS = 42
EXPECTED_NUM_KV_SHARED_LAYERS = 18
EXPECTED_FIRST_KV_SHARED_LAYER_IDX = 24
EXPECTED_DONOR_BLOCKS = {"full_attention": 23, "sliding_attention": 22}
EXPECTED_DONOR_BLOCKS_TUPLE = (22, 23)


#: The KV condition whose artifacts keep the historical un-suffixed filenames.
DEFAULT_KV_SHARING = "on"
KV_SHARING_CHOICES = ("on", "off")


def condition_artifact(name: str, kv_sharing: str) -> str:
    """Filename for a per-KV-condition artifact.

    Same reasoning as `family_config.site_set_artifact`, one axis over: every
    output path in this instrument is fixed per family, so running the OFF
    condition would overwrite the ON condition's artifacts. That is worse here
    than for site sets, because the two conditions produce artifacts with
    IDENTICAL schemas over the SAME layers -- a clobber would be invisible on
    inspection and would silently turn the primary A1-vs-A2 contrast into a
    comparison of an arm against itself.

    `on` keeps the historical un-suffixed names, so the sharing-ON arm is
    byte-for-byte the pre-existing path. `off` gets `<stem>.kv_off.<ext>`.
    """
    if kv_sharing == DEFAULT_KV_SHARING:
        return name
    if kv_sharing not in KV_SHARING_CHOICES:
        raise ValueError(f"unknown kv_sharing {kv_sharing!r}; expected one of {KV_SHARING_CHOICES}")
    stem, dot, ext = name.rpartition(".")
    if not dot:
        return f"{name}.kv_{kv_sharing}"
    return f"{stem}.kv_{kv_sharing}.{ext}"


def refuse_to_write_through_symlink(path) -> None:
    """Guard: refuse to overwrite a path that is a symlink.

    This instrument's inputs are staged as relative symlinks into
    `experiments/common/artifacts/` and into the producing experiment's private
    `analysis/`. `anchor_extract.safetensors` in particular is a symlink to the
    parent's 341.7 MB CLEAN use_cache=True extract, which is the sole surviving
    copy and is not in version control. A stage that wrote to its default output
    path would follow that symlink and destroy it. Fail closed instead.
    """
    import os
    if os.path.islink(path):
        raise RuntimeError(
            f"refusing to write through symlink {path} -> {os.readlink(path)}. "
            "This path is a staged INPUT, not an output. Pass an explicit "
            "--out/--manifest, or use the condition-scoped default."
        )


def get_text_layers(model):
    """Return the `nn.ModuleList` of `Gemma4TextDecoderLayer`.

    `google/gemma-4-E4B-it` resolves to `Gemma4ForConditionalGeneration`, whose
    decoder blocks live at `model.model.language_model.layers` (three hops). This
    is the same path the shared tuner's `_LAYER_PATHS` gained at tuner commit
    `7a44eb3`; resolved here directly so this module does not depend on the
    tuner's fallback ordering.
    """
    for path in ("model.language_model.layers", "language_model.layers", "model.layers"):
        obj = model
        for part in path.split("."):
            if not hasattr(obj, part):
                obj = None
                break
            obj = getattr(obj, part)
        if obj is not None:
            return obj
    raise AttributeError("Could not locate Gemma-4 text decoder layers on this model")


def verify_architecture(model) -> dict:
    """Fail closed if the live model is not the architecture this design assumes."""
    layers = get_text_layers(model)
    cfg = model.config.get_text_config()
    n = cfg.num_hidden_layers
    k = getattr(cfg, "num_kv_shared_layers", 0)
    first = n - k
    if (n, k, first) != (
        EXPECTED_NUM_HIDDEN_LAYERS,
        EXPECTED_NUM_KV_SHARED_LAYERS,
        EXPECTED_FIRST_KV_SHARED_LAYER_IDX,
    ):
        raise AssertionError(
            f"KV-seam geometry changed: num_hidden_layers={n}, num_kv_shared_layers={k}, "
            f"first_kv_shared_layer_idx={first}; this experiment is registered against "
            f"(42, 18, 24) and every registered site index depends on it."
        )
    prev = list(cfg.layer_types[:first])
    donors = {t: len(prev) - 1 - prev[::-1].index(t) for t in set(prev)}
    if donors != EXPECTED_DONOR_BLOCKS:
        raise AssertionError(f"KV donor blocks changed: {donors} != {EXPECTED_DONOR_BLOCKS}")
    shared = [i for i, lyr in enumerate(layers) if lyr.self_attn.is_kv_shared_layer]
    if shared != list(range(first, n)):
        raise AssertionError(f"KV-shared block set is {shared}, expected {list(range(first, n))}")
    return {"n_hidden_layers": n, "num_kv_shared_layers": k,
            "first_kv_shared_layer_idx": first, "donors": donors,
            "kv_shared_blocks": shared}


def build_full_length_cache(model_or_config):
    """Build a 42-entry `Cache` -- one `CacheLayer` per block, NO slicing.

    REQUIRED to make the sharing-OFF patch run, and (see CALLER CONTRACT below)
    used in the sharing-ON arm too, so the cache object is a CONSTANT across arms
    rather than a second variable riding along with the KV flip.

    Flipping `is_kv_shared_layer` alone CRASHES, deterministically. This is not a
    risk assessment: `kv_seam_preflight.py` check 1 reproduces the live
    `IndexError` on a tiny model carrying the real KV-seam geometry, and check 2
    confirms this builder fixes it (4/4 PASS). Trace:

    `Gemma4TextModel.forward` builds its cache as `DynamicCache(config=...)`.
    `DynamicCache.__init__` (`cache_utils.py:1218-1220`) is shared-KV-aware and
    truncates before allocating:

        # Some models have shared layers thus no cache is needed for them
        if hasattr(decoder_config, "num_kv_shared_layers"):
            layer_types = layer_types[: -decoder_config.num_kv_shared_layers]

    For this checkpoint that allocates exactly 24 `CacheLayer` objects (indices
    0-23; preflight check 1 asserts `len(cache.layers) == 24` before it even
    looks for the crash). Because that `layers` list is non-empty,
    `Cache.__init__` (`cache_utils.py:871-872`) sets
    `layer_class_to_replicate = None`, which disables the lazy-growth branch in
    `Cache.update` (`cache_utils.py:927-930`). So a patched shared layer reaching
    `past_key_values.update(..., self.layer_idx)` at `modeling_gemma4.py:1216`
    indexes `self.layers[24]` on a 24-element list -> **IndexError on the first
    shared-layer forward call**. `shared_layers` is bolted onto the cache
    instance separately (`:1217-1220`) and is not `self.layers`, which is exactly
    why stock code never needed those 18 slots.

    `Gemma4TextModel.forward` only constructs its own truncated cache when
    `past_key_values is None`, and `generate`'s "Quick escape route 1"
    (`generation/utils.py:1818-1829`) returns untouched when the caller supplies
    a `Cache`. So supplying this object bypasses the slice entirely.

    API: this is `Cache(layers=[...])`, NOT `DynamicCache(layers=...)` --
    `DynamicCache.__init__` accepts only `config=` and would re-apply the slice.
    One `DynamicSlidingWindowLayer`/`DynamicLayer` per entry of
    `config.layer_types`, in order, no slicing. This is the exact construction
    the passing preflight uses.

    CALLER CONTRACT, enforced by G0-KV: a FRESH cache is built for EVERY
    `generate()` call in EVERY arm -- ON and OFF alike -- by this one function, so
    the two arms cannot differ in how the cache is constructed. Freshness: a
    `Cache` is stateful and reusing one across rows would leak the previous row's
    K/V. Identical construction: preflight check 4 establishes that under sharing
    ON this cache is token- AND logit-bit-identical to stock, which is the
    property that makes the swap inert and lets A1-vs-A2 isolate the KV variable.
    Supplying it in only one arm would forfeit that property and make the primary
    contrast uninterpretable.
    """
    from transformers.cache_utils import (
        Cache,
        DynamicLayer,
        DynamicSlidingWindowLayer,
    )

    cfg = model_or_config
    if hasattr(cfg, "config"):
        cfg = cfg.config
    if hasattr(cfg, "get_text_config"):
        cfg = cfg.get_text_config()

    sliding_window = getattr(cfg, "sliding_window", None)
    layers = []
    for layer_type in cfg.layer_types:
        if layer_type in ("sliding_attention", "chunked_attention"):
            layers.append(DynamicSlidingWindowLayer(sliding_window=sliding_window))
        else:
            layers.append(DynamicLayer())
    if len(layers) != cfg.num_hidden_layers:
        raise AssertionError(
            f"full-length cache has {len(layers)} layers, expected {cfg.num_hidden_layers}"
        )
    cache = Cache(layers=layers)
    if cache.layer_class_to_replicate is not None:
        raise AssertionError(
            "cache has a live lazy-growth path; the explicit layer list did not take effect"
        )
    return cache


def cache_layer_lengths(cache) -> list[int]:
    """Per-layer cached sequence length, for the G0-KV growth assertion."""
    return [int(layer.get_seq_length()) for layer in cache.layers]


@contextlib.contextmanager
def kv_sharing(model, enabled: bool):
    """Context manager: run the model with KV sharing ON (default) or OFF.

    OFF forces every block in 24..41 to recompute K/V from its own residual
    stream using its own retained `k_proj`/`v_proj`. Restores the original
    attribute values on exit, always.

    `is_kv_shared_layer` is a plain instance attribute set post-construction
    (`modeling_gemma4.py:1149`), not a buffer or parameter, so reassigning it is
    safe. `store_full_length_kv` is deliberately NOT touched: blocks 22 and 23
    keep writing `past_key_values.shared_layers` under OFF (`:1217-1220`), where
    nothing reads it. Leaving that write in place keeps the two conditions'
    control flow identical everywhere except the one branch under test.

    CALLER CONTRACT, enforced by G0-KV, not by this function: EVERY `generate()`
    call -- in EVERY arm, `enabled=True` and `enabled=False` alike -- MUST be
    passed a fresh `build_full_length_cache(model)` as `past_key_values=`. Under
    `enabled=False` this is what stops the run raising IndexError on the first
    shared-layer forward. Under `enabled=True` it is not needed to avoid a crash,
    and it is supplied anyway on purpose: it makes the cache object a constant
    across arms, so A1-vs-A2 varies the KV flag and nothing else. Preflight check
    4 verifies the ON-condition swap is token- and logit-bit-identical to stock.
    """
    layers = get_text_layers(model)
    saved = [(lyr.self_attn.is_kv_shared_layer, lyr.self_attn.kv_shared_layer_index)
             for lyr in layers]
    try:
        if not enabled:
            for lyr in layers:
                lyr.self_attn.is_kv_shared_layer = False
                lyr.self_attn.kv_shared_layer_index = None
        yield model
    finally:
        for lyr, (was_shared, donor_idx) in zip(layers, saved):
            lyr.self_attn.is_kv_shared_layer = was_shared
            lyr.self_attn.kv_shared_layer_index = donor_idx


@dataclass
class ProjectionCallCounts:
    k_proj: dict[int, int] = field(default_factory=dict)
    v_proj: dict[int, int] = field(default_factory=dict)


@contextlib.contextmanager
def count_kv_projection_calls(model):
    """Count actual `k_proj`/`v_proj` forward executions per block.

    The flag is not the evidence. This counts the projections that really ran,
    which is what the G0-KV preflight asserts on.
    """
    counts = ProjectionCallCounts()
    handles = []
    for i, lyr in enumerate(get_text_layers(model)):
        for name in ("k_proj", "v_proj"):
            mod = getattr(lyr.self_attn, name, None)
            if mod is None:
                continue
            store = getattr(counts, name)
            store[i] = 0

            def _hook(_m, _inp, _out, _store=store, _i=i):
                _store[_i] += 1

            handles.append(mod.register_forward_hook(_hook))
    try:
        yield counts
    finally:
        for h in handles:
            h.remove()


def donor_projection_diagnostic(model, enc) -> dict:
    """How much can the OFF condition possibly differ from ON? One forward pass.

    Registered as "Open questions at sign" #4 and authorized by the lead
    2026-07-25 to run BEFORE any GPU spend on the main run.

    Under sharing ON, every block in 24..41 attends over its donor's K/V. Under
    OFF, each recomputes K/V from its own residual stream with its own retained
    `k_proj`/`v_proj`. If those retained projections closely reproduce what the
    donor would have produced, the OFF manipulation is nearly a NO-OP -- and a
    negative A2 would then be uninformative rather than evidence about the KV
    pathway. That is a conclusion far cheaper to reach here than after a full
    dosed run.

    Method: run ONE forward with sharing ON, capturing (a) each shared block's
    own `k_proj`/`v_proj` output on its actual input, and (b) its donor's. The
    comparison is per-block cosine and relative L2 error over the flattened
    projection output.

    IMPORTANT about what this does and does not establish. A high cosine bounds
    how much OFF *can* differ at the projection output; it does not prove
    downstream behaviour is unchanged, because attention is nonlinear in K and
    small differences can amplify. Read a high cosine as "OFF is a weak
    manipulation, treat a null as uninformative", NOT as "OFF is provably
    inert". A low cosine is the cleanly interpretable direction.

    READ THE COSINE, NOT THE REL-L2. The hooks sit on the `k_proj`/`v_proj`
    modules, so they capture the projection output BEFORE
    `Gemma4TextAttention`'s `k_norm`/`v_norm` (`Gemma4RMSNorm` over head_dim,
    applied at `key_states = self.k_norm(key_states)`). Gemma's residual-stream
    norm grows with depth, so blocks 24..41 project a much larger-magnitude
    input than blocks 22/23 do, and `rel_l2_err` inherits that scale gap
    wholesale -- values of 3-14 are mostly the depth scale difference, which
    RMSNorm then removes. Cosine is scale-invariant and is the load-bearing
    statistic here. `rel_l2_err` is retained only because a cosine near zero
    with a rel-L2 near zero would be self-contradictory and worth catching.
    """
    layers = get_text_layers(model)
    geom = verify_architecture(model)
    first = geom["first_kv_shared_layer_idx"]
    donors = geom["donors"]
    cfg = model.config.get_text_config()

    own: dict[int, dict[str, torch.Tensor]] = {}
    handles = []

    def _mk(i, name):
        def _hook(_m, _inp, out):
            own.setdefault(i, {})[name] = out.detach().float().cpu()
        return _hook

    # Hook k_proj/v_proj on EVERY block. Under sharing ON the shared blocks skip
    # their projections entirely, so their hooks would never fire -- which is
    # exactly why the shared blocks are run a second time, OFF, below.
    for i, lyr in enumerate(layers):
        for name in ("k_proj", "v_proj"):
            mod = getattr(lyr.self_attn, name, None)
            if mod is not None:
                handles.append(mod.register_forward_hook(_mk(i, name)))
    try:
        with torch.no_grad():
            # OFF forces every shared block to actually execute its own
            # projections, so `own` gets populated for blocks 24..41. The donor
            # blocks (22, 23) are non-shared and execute under either condition.
            with kv_sharing(model, enabled=False):
                model(**enc, past_key_values=build_full_length_cache(model), use_cache=True)
    finally:
        for h in handles:
            h.remove()

    def _cmp(a: torch.Tensor, b: torch.Tensor) -> dict:
        av, bv = a.reshape(-1), b.reshape(-1)
        cos = float(torch.nn.functional.cosine_similarity(av, bv, dim=0))
        denom = float(torch.linalg.vector_norm(bv))
        rel = float(torch.linalg.vector_norm(av - bv) / denom) if denom else float("nan")
        return {"cosine": cos, "rel_l2_err": rel}

    per_block = {}
    for i in range(first, cfg.num_hidden_layers):
        donor_idx = donors[cfg.layer_types[i]]
        if i not in own or donor_idx not in own:
            continue
        per_block[i] = {
            "donor_block": donor_idx,
            "layer_type": cfg.layer_types[i],
            "k_proj": _cmp(own[i]["k_proj"], own[donor_idx]["k_proj"]),
            "v_proj": _cmp(own[i]["v_proj"], own[donor_idx]["v_proj"]),
        }

    def _summ(key: str, stat: str) -> dict:
        vals = [b[key][stat] for b in per_block.values()]
        if not vals:
            return {}
        t = torch.tensor(vals)
        return {"min": float(t.min()), "median": float(t.median()),
                "max": float(t.max()), "mean": float(t.mean())}

    return {
        "diagnostic": "donor_vs_own_kv_projection",
        "registered_as": "AMENDMENT.md 'Open questions at sign' #4",
        "n_blocks_compared": len(per_block),
        "shared_blocks": list(range(first, cfg.num_hidden_layers)),
        "donors": donors,
        "summary": {
            "k_proj_cosine": _summ("k_proj", "cosine"),
            "k_proj_rel_l2_err": _summ("k_proj", "rel_l2_err"),
            "v_proj_cosine": _summ("v_proj", "cosine"),
            "v_proj_rel_l2_err": _summ("v_proj", "rel_l2_err"),
        },
        "per_block": {str(k): v for k, v in per_block.items()},
        "interpretation_note": (
            "High cosine => the OFF condition is a WEAK manipulation and a negative "
            "A2 is uninformative, not evidence about the KV pathway. It does NOT "
            "prove OFF is inert: attention is nonlinear in K and small projection "
            "differences can amplify downstream. Low cosine is the cleanly "
            "interpretable direction."
        ),
        "measurement_caveat": (
            "READ THE COSINE, NOT THE REL-L2. These hooks capture k_proj/v_proj "
            "output BEFORE Gemma4TextAttention's k_norm/v_norm (Gemma4RMSNorm over "
            "head_dim). Gemma's residual norm grows with depth, so blocks 24..41 "
            "project a much larger-magnitude input than blocks 22/23; rel_l2_err "
            "inherits that scale gap wholesale and RMSNorm then removes it. Cosine "
            "is scale-invariant and is the load-bearing statistic."
        ),
    }


@contextlib.contextmanager
def capture_donor_keys(model, blocks=EXPECTED_DONOR_BLOCKS_TUPLE):
    """Capture the keys the two donor blocks compute.

    Under KV sharing ON, `shared_layers[22]` and `shared_layers[23]` are the ONLY
    keys any block in 24..41 ever attends over, so these two tensors are exactly
    what a residual write must move to be 'donor reaching'. Hooked on `k_norm`,
    which the donor blocks always execute (they are non-shared by construction);
    a shared block never reaches `k_norm`, which is why the probe sits here and
    not on block 24.
    """
    captured: dict[int, torch.Tensor] = {}
    handles = []
    layers = get_text_layers(model)
    for i in blocks:
        attn = layers[i].self_attn

        def _hook(_m, _inp, out, _i=i):
            k = out[0] if isinstance(out, tuple) else out
            captured[_i] = k.detach().float().cpu().clone()

        handles.append(attn.k_norm.register_forward_hook(_hook))
    try:
        yield captured
    finally:
        for h in handles:
            h.remove()
