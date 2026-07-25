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
