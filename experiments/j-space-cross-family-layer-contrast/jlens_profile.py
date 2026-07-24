#!/usr/bin/env python3
"""Cross-family J-lens layer_profile wrapper.

Ported thinly around `j-space-localization-qwen3-4b/jlens.py`'s
`layer_profile()` (read in full before writing this: it is ALREADY
parameterized by `model_name` via its own `load_model()`, and by
`hs_indices` -- this experiment's only genericization need was a depth
sweep + band-selection rule per family, not a jlens.py fork). Do NOT modify
jlens.py; import it unchanged from its own experiment directory.

LOCKED band-selection rule (see AMENDMENT.md "Design" -> step 2, transcribed
here verbatim so the rule lives next to its implementation):

  midband candidates = the profiled hs_index at the effective-dimensionality-
  fraction peak, PLUS the profiled hs_indices immediately adjacent to it in
  the depth sweep (one on each side, where available). This is a literal
  reading of "peak +/- adjacent profiled layers" -- it does NOT assume any
  fixed offset (e.g. Qwen3-4B's own hs23/26/29 triple was a human read of a
  continuous band, not a formula) and does NOT assume Qwen3-4B's hs23-29
  band transfers to any other family.

  late reference = round(LATE_REFERENCE_DEPTH_FRACTION * n_hidden_layers),
  where LATE_REFERENCE_DEPTH_FRACTION = 34/36 (Qwen3-4B's own hs34 late
  write site over its 36 hidden layers) -- the depth-FRACTION analog, not
  the same absolute index, per this experiment's locked design.

This script does NOT run the J-lens correctness smoke (verbalize(final_layer,
v) vs direct unembed) that gated the original localization launch -- that
smoke is jlens.py's own `smoke` subcommand and should be re-run per family
before trusting a family's profile, since the smoke's PASS on Qwen3-4B does
not establish it passes on a different architecture. Callers should run
`python jlens.py smoke ...` (pointed at the family's own checkpoint) first;
this wrapper does not duplicate that gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCALIZATION_DIR = HERE.parent / "j-space-localization-qwen3-4b"
for p in (str(HERE), str(LOCALIZATION_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import jlens  # noqa: E402  -- unmodified import from the localization experiment
from family_config import FAMILY_SLUGS, load_family, save_family  # noqa: E402

LATE_REFERENCE_DEPTH_FRACTION = 34 / 36  # Qwen3-4B's own hs34 / 36 hidden layers


def default_depth_sweep(n_hidden_layers: int, n_points: int = 10) -> list[int]:
    """Evenly spaced hs_indices across [1, n_hidden_layers], always including
    the final layer. n_points defaults to roughly the same density as the
    localization experiment's own local smoke sweep
    (`--layers 2,6,10,14,18,22,26,30,34,36` for 36 layers)."""
    if n_hidden_layers < n_points:
        return list(range(1, n_hidden_layers + 1))
    step = n_hidden_layers / (n_points - 1)
    points = sorted({max(1, round(1 + i * step)) for i in range(n_points)})
    if points[-1] != n_hidden_layers:
        points[-1] = n_hidden_layers
    return sorted(set(points))


def select_band(per_layer: dict[int, dict], depth_sweep: list[int],
                 n_hidden_layers: int) -> dict:
    peak_hs = max(depth_sweep, key=lambda h: per_layer[h]["effective_dim_frac_mean"])
    idx = depth_sweep.index(peak_hs)
    neighbors = []
    if idx > 0:
        neighbors.append(depth_sweep[idx - 1])
    if idx < len(depth_sweep) - 1:
        neighbors.append(depth_sweep[idx + 1])
    midband_candidates_hs = sorted({peak_hs, *neighbors})
    late_reference_hs = min(
        n_hidden_layers, round(LATE_REFERENCE_DEPTH_FRACTION * n_hidden_layers)
    )
    return {
        "effective_dim_peak_hs": peak_hs,
        "midband_candidates_hs": midband_candidates_hs,
        "late_reference_hs": late_reference_hs,
        "late_reference_depth_fraction_used": LATE_REFERENCE_DEPTH_FRACTION,
    }


def run(args: argparse.Namespace) -> int:
    family = args.family
    cfg = load_family(family)
    repo = cfg["checkpoint"]["repo"]

    model, tokenizer = jlens.load_model(model_name=repo, device=args.device)
    # Nested-text-config families (gemma4, qwen3.5) keep num_hidden_layers and
    # hidden_size on config.text_config; mirror model_lib.py's established
    # resolution using the same families/<slug>.yaml loader fields
    # (family-generic, no special-casing). Gemma4Config forwards neither
    # attribute top-level. The imported jlens.py (do-NOT-modify, shared
    # verbatim with j-space-localization-qwen3-4b) reads
    # model.config.hidden_size directly inside layer_profile(), so the
    # resolved fields are ALSO mirrored onto model.config (set only when
    # absent) instead of modifying jlens.py.
    text_cfg = model.config
    if cfg["loader"].get("nested_text_config") and hasattr(model.config, "text_config"):
        text_cfg = model.config.text_config
        for _field in (cfg["loader"]["num_layers_field"],
                       cfg["loader"]["hidden_size_field"]):
            if not hasattr(model.config, _field):
                setattr(model.config, _field, getattr(text_cfg, _field))
    n_hidden_layers = getattr(text_cfg, cfg["loader"]["num_layers_field"])
    depth_sweep = args.layers or default_depth_sweep(n_hidden_layers, args.n_points)
    print(f"[jlens-profile:{family}] n_hidden_layers={n_hidden_layers} "
          f"depth_sweep={depth_sweep}", flush=True)

    prompts = jlens.load_corpus(Path(args.corpus), args.n_prompts, seed=args.seed)

    out_dir = HERE / "analysis-committed" / family
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_path = out_dir / "layer_profile.json"

    def on_layer_done(hs_index, per_layer_so_far):
        partial = {
            "family": family, "checkpoint_repo": repo,
            "n_hidden_layers": n_hidden_layers, "depth_sweep": depth_sweep,
            "n_prompts": len(prompts), "seed": args.seed,
            "per_layer": {str(k): v for k, v in per_layer_so_far.items()},
        }
        profile_path.write_text(json.dumps(partial, indent=2), encoding="utf-8")

    result = jlens.layer_profile(
        model, tokenizer, prompts, depth_sweep,
        n_random_dirs=args.n_random_dirs, seed=args.seed,
        on_layer_done=on_layer_done,
    )
    band = select_band(result["per_layer"], depth_sweep, n_hidden_layers)
    print(f"[jlens-profile:{family}] band selection: {band}", flush=True)

    profile_out = {
        "family": family, "checkpoint_repo": repo,
        "n_hidden_layers": n_hidden_layers, "depth_sweep": depth_sweep,
        "n_prompts": len(prompts), "n_random_dirs": args.n_random_dirs,
        "seed": args.seed,
        "per_layer": {str(k): v for k, v in result["per_layer"].items()},
        "band_selection": band,
    }
    profile_path.write_text(json.dumps(profile_out, indent=2), encoding="utf-8")

    cfg["band_selection"]["status"] = "resolved"
    cfg["band_selection"]["n_hidden_layers"] = n_hidden_layers
    cfg["band_selection"]["midband_candidates_hs"] = band["midband_candidates_hs"]
    cfg["band_selection"]["late_reference_hs"] = band["late_reference_hs"]
    cfg["band_selection"]["effective_dim_peak_hs"] = band["effective_dim_peak_hs"]
    save_family(family, cfg)
    print(f"[jlens-profile:{family}] wrote {profile_path} and updated "
          f"families/{family}.yaml band_selection", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--corpus", default=str(LOCALIZATION_DIR / "analysis" / "corpus_pool.jsonl"),
                    help="reuses the localization experiment's own corpus builder/"
                         "manifest scheme (private HF staging pool re-sample); see "
                         "jlens.py build-corpus / load_corpus")
    ap.add_argument("--n-prompts", type=int, default=1000)
    ap.add_argument("--n-random-dirs", type=int, default=6)
    ap.add_argument("--n-points", type=int, default=10,
                    help="depth-sweep density when --layers is not given")
    ap.add_argument("--layers", type=lambda s: [int(x) for x in s.split(",") if x.strip()],
                    default=None, help="explicit comma-separated hs_index depth sweep, "
                                        "overriding --n-points")
    ap.add_argument("--seed", type=int, default=20260707)
    ap.add_argument("--device", default="cuda")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
