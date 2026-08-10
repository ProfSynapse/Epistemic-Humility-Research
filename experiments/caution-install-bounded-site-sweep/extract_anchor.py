#!/usr/bin/env python3
"""Stage 2 (AMENDMENT.md Run plan): full-depth anchor extraction, per
substrate. GPU, `mechinterp extract`-equivalent (calls the tuner's real
`MechInterp.extraction.extract_rows` directly rather than shelling out to the
CLI, so the pinned-adapter-revision loader installs cleanly -- see
sweep_lib.install_pinned_loader). G0b gated (answer capture, seam continuity
-- both computed and recorded here, in this substrate's own manifest.json).

Seam continuity (2026-08-10 BLOCKER #9 correction): gates.yaml
g0b_seam_continuity's registered quantity is CACHE-CONDITION INVARIANCE of
the SAME hidden state -- the reference min cos 1.000000 comes from capturing
identical states two ways, not from comparing DIFFERENT adjacent layers of
one forward pass. The prior implementation here measured adjacent-layer
cosine within a single pass (a materially different, always-fails-a-0.999-
floor quantity: real residual streams evolve substantially layer to layer;
a live re-review measured min 0.043 on healthy committed data and it hard-
stopped this stage). See `run_seam_check()` below for the corrected
check: a fixed, seeded 32-row subset run forward TWICE via direct
`transformers` calls (never through the tuner's capture path, which
hardcodes `use_cache`), once with `use_cache=True` and once with
`use_cache=False`, min cosine per (row, hidden-state layer) between the two
runs. Floor stays the registered 0.999.

cell.yaml `extraction`: anchor = final_prompt_token, dtype float32, full_depth
= true (captures every hidden-state layer in one forward pass, independent of
how many of those layers this cell's seven registered sites actually use --
matching the budget note "independent of site count"), use_cache = true.

Rows extracted, trained substrate: every row in rows_with_text.jsonl that has
a split assignment (FIT + HELD-OUT for confab/known_correct_answered,
FIT-only for unknown_refused), joined against split_manifest.json on the fly
(no separate "rows_with_split" materialization step, matching the
predecessor cells' convention).

Rows extracted, raw_base substrate (2026-08-10 lead adjudication of F8):
rep2's registered 221-row multi-source held-out confab pool
(`sweep_lib.raw_base_anchor_pool()`, per AMENDMENT.md's G4 block), all
assigned split="held_out" -- see `_raw_base_joined_rows()` below.

Output: `analysis/extract_<substrate>/` (safetensors per row + manifest.json).
Must run once per substrate before build_directions.py / alin_profile.py.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    base_repo_and_revision,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    load_split_manifest,
    raw_base_anchor_pool,
    rows_with_text_path,
    split_manifest_path,
    substrate_config,
    write_json,
)


def _raw_base_joined_rows() -> list[dict]:
    """2026-08-10 wiring pass (lead adjudication of F8's raw_base gap):
    raw_base's confab population is rep2's registered 221-row multi-source
    held-out pool (AMENDMENT.md G4 block), not a re-mined pool -- see
    sweep_lib.raw_base_anchor_pool()'s docstring for the full reasoning and
    why it hard-fails rather than falls back to anything else.

    That committed pool carries row_key/role/source/category_canon only,
    never question text (rep2's own containment policy). Question text for
    these exact 221 row_keys must still be populated into
    rows_with_text_path("raw_base") by some other means before this can
    actually run generation; this function verifies that precisely -- which
    of the 221 registered row_keys have text and which don't -- instead of
    the old blanket "no mining stage exists" error. All 221 rows are
    assigned split="held_out": rep2's own methodology evaluates this pool as
    ONE evidential population (full_summary.json's confab_tighten.n == 221,
    no internal fit/held-out split), and G4's registered comparison is
    against that same full-population rate."""
    pool = raw_base_anchor_pool()  # hard-fails on missing/mismatched rep2 artifacts
    text_by_key = {r["row_key"]: r for r in load_jsonl(rows_with_text_path("raw_base"))}
    missing = [r["row_key"] for r in pool["rows"] if r["row_key"] not in text_by_key]
    # ALSO(a) (2026-08-10 lead adjudication): presence of a row_key alone
    # does not guarantee its role field agrees with rep2's own pool (a stray
    # row staged under the wrong role would silently join in as "confab").
    # Check role == "confab" explicitly for every present row too.
    wrong_role = [
        r["row_key"] for r in pool["rows"]
        if r["row_key"] in text_by_key and text_by_key[r["row_key"]].get("role") != "confab"
    ]
    if missing or wrong_role:
        raise RuntimeError(
            f"{rows_with_text_path('raw_base')} is missing question text for "
            f"{len(missing)}/{pool['n_confab']} of rep2's registered raw_base "
            f"anchor pool row_keys (first 5: {missing[:5]}), and "
            f"{len(wrong_role)}/{pool['n_confab']} present row_keys carry a "
            f"role other than 'confab' (first 5: {wrong_role[:5]}). This file "
            "must be populated with real text AND role: \"confab\" for ALL "
            f"221 row_keys named in {pool['pool_path']} before extraction can "
            "run for raw_base -- see sweep_lib.raw_base_anchor_pool()'s "
            "docstring: rep2's own committed manifest deliberately does not "
            "carry text, by its own containment policy."
        )
    out = []
    for r in pool["rows"]:
        text_row = text_by_key[r["row_key"]]
        out.append({**r, "question": text_row.get("question"), "aliases": text_row.get("aliases", []),
                     "split": "held_out"})
    return out


def joined_rows(substrate: str) -> list[dict]:
    if substrate == "raw_base":
        return _raw_base_joined_rows()

    rows_path = rows_with_text_path(substrate)
    rows = {r["row_key"]: r for r in load_jsonl(rows_path)}
    split_manifest = load_split_manifest(substrate)
    split = split_manifest.get("rows", [])
    if not split:
        raise RuntimeError(
            f"{split_manifest_path(substrate)} is empty or missing; "
            "run split_fit_heldout.py first."
        )
    out = []
    for sr in split:
        row = rows.get(sr["row_key"])
        if row is None:
            continue
        out.append({**row, "split": sr["split"]})
    return out


def select_seam_check_rows(rows: list[dict], cell: dict, n: int = 32) -> list[dict]:
    """Fixed, seeded 32-row subset selection for the seam-continuity check
    (BLOCKER #9). Deterministic from cell.yaml's registered seed so the
    exact same rows are checked on every run; the selected row_keys are
    recorded in the output (run_seam_check's
    g0b_seam_continuity_selected_row_keys) for reproducibility, not just the
    seed."""
    seed = int(cell["seed"])
    by_key = {r["row_key"]: r for r in rows}
    row_keys_sorted = sorted(by_key)
    rng = random.Random(f"{seed}:seam_check")
    selected_keys = rng.sample(row_keys_sorted, min(n, len(row_keys_sorted)))
    return [by_key[k] for k in sorted(selected_keys)]


def seam_cosine_between_runs(hs_cache_true: list, hs_cache_false: list) -> dict:
    """Pure math, no model/tokenizer required (CPU-smoke-testable per
    BLOCKER #9's instruction): given two same-length lists of per-layer
    anchor-token hidden-state vectors for ONE row -- one captured with
    use_cache=True, one with use_cache=False -- computes the cosine
    similarity at each matching layer index and returns the minimum. This is
    the registered quantity: cache-condition invariance of the SAME hidden
    state, not a comparison between different layers."""
    assert len(hs_cache_true) == len(hs_cache_false), (
        f"hidden-state layer count mismatch between runs: "
        f"{len(hs_cache_true)} vs {len(hs_cache_false)}"
    )
    cosines = []
    for a, b in zip(hs_cache_true, hs_cache_false):
        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            cosines.append(None)
            continue
        cosines.append(float(np.dot(a, b) / (na * nb)))
    valid = [(i, c) for i, c in enumerate(cosines) if c is not None]
    if not valid:
        return {"min_cos": None, "min_cos_layer": None, "n_layers_compared": 0}
    min_layer, min_cos = min(valid, key=lambda t: t[1])
    return {"min_cos": min_cos, "min_cos_layer": min_layer, "n_layers_compared": len(valid)}


def run_seam_check(model, tokenizer, rows: list[dict], cell: dict) -> dict:
    """GPU driver for BLOCKER #9's corrected seam-continuity check. Reuses
    the SAME already-loaded model/tokenizer (loads the substrate once, per
    the lead's instruction), so this is a standalone step inside stage 2's
    window, not a second model load. Runs each selected row forward TWICE
    via DIRECT `transformers` calls (`model(**enc, output_hidden_states=True,
    use_cache=...)`) -- never through `MechInterp.extraction.extract_rows` /
    the tuner's capture path, which hardcodes `use_cache` and so cannot
    exercise both conditions. Anchor position = final prompt token (index
    -1 of the encoded prompt, no generation involved), matching this
    stage's own `extraction.anchor = final_prompt_token` convention."""
    import torch

    from render_sweep import render as render_fn

    selected = select_seam_check_rows(rows, cell)
    per_row = []
    min_cos, min_pair, n_compared = None, None, 0
    device = next(model.parameters()).device
    for row in selected:
        prompt = render_fn(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out_true = model(**enc, output_hidden_states=True, use_cache=True)
            out_false = model(**enc, output_hidden_states=True, use_cache=False)
        hs_true = [h[0, -1, :].detach().to(torch.float64).cpu().numpy() for h in out_true.hidden_states]
        hs_false = [h[0, -1, :].detach().to(torch.float64).cpu().numpy() for h in out_false.hidden_states]
        stats = seam_cosine_between_runs(hs_true, hs_false)
        per_row.append({"row_key": row["row_key"], **stats})
        n_compared += stats["n_layers_compared"]
        if stats["min_cos"] is not None and (min_cos is None or stats["min_cos"] < min_cos):
            min_cos, min_pair = stats["min_cos"], (row["row_key"], stats["min_cos_layer"])
    return {
        "g0b_seam_continuity_min_cos": min_cos,
        "g0b_seam_continuity_n_pairs_compared": n_compared,
        "g0b_seam_continuity_min_pair_row_key": min_pair[0] if min_pair else None,
        "g0b_seam_continuity_min_pair_layer": min_pair[1] if min_pair else None,
        "g0b_seam_continuity_selected_row_keys": sorted(r["row_key"] for r in selected),
        "g0b_seam_continuity_n_rows_checked": len(selected),
        "g0b_seam_continuity_per_row": per_row,
        "g0b_seam_continuity_pass": bool(min_cos is not None and min_cos >= 0.999),
    }


def run(args: argparse.Namespace) -> int:
    guard_msg = (
        "Refusing to run a GPU extraction without --i-know-this-runs-on-gpu. "
        "This loads a model and runs generation."
    )
    if not args.i_know_this_runs_on_gpu:
        print(guard_msg, file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    rows = joined_rows(args.substrate)
    print(f"[extract:{args.substrate}] {len(rows)} rows to extract (FIT + HELD-OUT "
          "confab/known_correct_answered, FIT-only unknown_refused)", flush=True)
    if not rows:
        print(f"[extract] ERROR: no rows found after joining {rows_with_text_path(args.substrate)} "
              f"against {split_manifest_path(args.substrate)}.", file=sys.stderr)
        return 1

    from MechInterp.extraction import PositionSpec, extract_rows

    adapter = sub_cfg.get("adapter_repo")
    adapter_revision = sub_cfg.get("adapter_revision")
    install_pinned_loader(adapter_revision)
    from MechInterp.cli import _load_model_and_tokenizer  # picks up the monkeypatch

    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    model, tokenizer = _load_model_and_tokenizer(base_repo, adapter, base_revision)

    spec = PositionSpec(families=["anchor"], every_k=4, layers=None)  # full_depth: true
    out_dir = ANALYSIS / f"extract_{args.substrate}"
    manifest = extract_rows(
        model, tokenizer, rows,
        render_fn=_render_fn(), content_end_fn=_content_end_fn(),
        spec=spec, out_dir=out_dir,
        max_new_tokens=args.max_new_tokens,  # anchor family is prefill-only; kept small
    )
    n_answered = manifest["n_answered"]
    capture_rate = n_answered / manifest["n_rows"] if manifest["n_rows"] else 0.0
    print(f"[extract:{args.substrate}] captured {n_answered}/{manifest['n_rows']} "
          f"(capture_rate={capture_rate:.4f}) -> {out_dir}", flush=True)

    manifest["substrate"] = args.substrate
    manifest["adapter_repo"] = adapter
    manifest["adapter_revision"] = adapter_revision
    manifest["base_repo"] = base_repo
    manifest["base_revision"] = base_revision
    manifest["rows_path"] = str(rows_with_text_path(args.substrate))
    manifest["capture_rate"] = capture_rate
    manifest["g0b_answer_capture_pass"] = capture_rate >= 0.90

    if args.substrate == "raw_base":
        # G4 requires the anchor arm to record which raw-base pool it ran
        # on (AMENDMENT.md G4 block). raw_base_anchor_pool() was already
        # called (and hard-failed on any mismatch) inside joined_rows(); the
        # SAME provenance is recomputed here (cheap: one file read + one
        # hash) so it lands in this substrate's own manifest.json rather
        # than only living in an in-memory value from joined_rows().
        pool = raw_base_anchor_pool()
        manifest["raw_base_anchor_pool_provenance"] = {
            "pool_source": pool["pool_source"], "pool_path": pool["pool_path"],
            "pool_sha256": pool["pool_sha256"], "n_confab": pool["n_confab"],
            "pool_identity_note": pool["pool_identity_note"],
        }
        print(f"[extract:raw_base] anchor pool provenance: {pool['pool_source']} "
              f"({pool['n_confab']} confab rows, sha256={pool['pool_sha256'][:12]}...)", flush=True)

    # BLOCKER #9: standalone seam-continuity check inside this stage's
    # window, reusing the model/tokenizer already loaded above (substrate
    # loaded once). Cache-condition invariance, not adjacent-layer
    # comparison -- see run_seam_check()'s docstring.
    seam = run_seam_check(model, tokenizer, rows, cell)
    manifest.update(seam)
    print(f"[extract:{args.substrate}] G0b seam continuity: min_cos="
          f"{seam['g0b_seam_continuity_min_cos']} over {seam['g0b_seam_continuity_n_pairs_compared']} "
          f"(row, hidden-state) pairs across {seam['g0b_seam_continuity_n_rows_checked']} rows "
          f"-> pass={seam['g0b_seam_continuity_pass']}", flush=True)

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0 if (manifest["g0b_answer_capture_pass"] and seam["g0b_seam_continuity_pass"]) else 1


def _render_fn():
    from render_sweep import render
    return render


def _content_end_fn():
    from render_sweep import content_end_fn
    return content_end_fn


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--max-new-tokens", type=int, default=8,
                     help="anchor position is prompt_len-1, independent of the "
                          "completion; kept small purely so extract_rows' internal "
                          "content_end_fn / answered check has something to read")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
