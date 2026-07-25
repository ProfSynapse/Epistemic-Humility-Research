#!/usr/bin/env python3
"""Extract prompt-anchor activations for one family's eval pool, at that
family's own resolved candidate layers.

Ported from `j-space-layer-contrast-replication-qwen3-4b/extract_fresh_anchor.py`
and `j-space-midband-write-sweep-qwen3-4b/extract_layer_sweep_anchor.py`,
generalized to read the checkpoint and candidate hs_indices from a family
config instead of hardcoding `unsloth/Qwen3-4B` and `HS_INDICES = [23, 26,
29, 34]`. Requires `jlens_profile.py --family <slug>` to have already
resolved that family's `band_selection` (midband_candidates_hs +
late_reference_hs) -- this script refuses to run on an unresolved family
rather than silently falling back to Qwen3-4B's own layer set.

Writes private per-row anchor safetensors + a JSON manifest under
`analysis/<family>/`. Does not commit question text or activations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import (  # noqa: E402
    FAMILY_SLUGS, SITE_SETS, hs_indices, late_reference_hs, load_family,
    resolve_site_set,
)
import kv_seam_patch as kv  # noqa: E402
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


FLUSH_EVERY = 50  # rows between durable safetensors+manifest flushes (kill-resume safety)


def run(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file, load_file

    family = args.family
    cfg = load_family(family)
    # raises if band_selection not yet resolved. The late reference is appended
    # for every site set, matching hs_indices()'s midband-first/late-last order.
    if args.site_set == "midband":
        hs_list = hs_indices(cfg)
    else:
        hs_list = resolve_site_set(cfg, args.site_set) + [late_reference_hs(cfg)]

    def cn(name: str) -> str:
        return kv.condition_artifact(name, args.kv_sharing)

    rows_path = Path(args.rows or (HERE / "analysis" / family / "eval_rows.jsonl"))
    out_path = Path(args.out or (HERE / "analysis" / family / cn("anchor_extract.safetensors")))
    manifest_path = Path(args.manifest
                         or (HERE / "analysis" / family / cn("anchor_extract_manifest.json")))
    # The ON default paths are staged SYMLINKS to the parent experiment's clean
    # use_cache=True extract -- the sole surviving copy, 341.7 MB, not in
    # version control. Writing through them would destroy it. The OFF condition
    # writes its own `.kv_off.` names and is unaffected, but the guard is
    # unconditional: an explicit --out could point anywhere.
    kv.refuse_to_write_through_symlink(out_path)
    kv.refuse_to_write_through_symlink(manifest_path)
    rows = load_jsonl(rows_path)
    if not rows:
        print(f"[extract-anchor:{family}] ERROR: no rows in {rows_path}", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows_sha = sha256_file(rows_path)

    # Kill-resume: this is a per-row GPU forward loop that previously buffered
    # ALL rows in memory and wrote the safetensors + manifest only at the end,
    # so a kill lost the whole extraction. It now flushes durably every
    # FLUSH_EVERY rows and RESUMES from the last flush. Resume reuses an existing
    # partial extraction only when its fingerprint (rows_sha256 + candidate hs
    # set) matches; --fresh forces a clean restart. See experiment.yaml
    # instrument.persistence and experiments/common/README-runlog.md.
    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    done_keys: set[str] = set()
    if not args.fresh and out_path.is_file() and manifest_path.is_file():
        prev = json.loads(manifest_path.read_text())
        # forward_use_cache is part of the fingerprint: a pre-fix extraction
        # (use_cache=False, or a manifest predating the field) must NEVER be
        # resumed into a post-fix run, or the artifact silently interleaves
        # corrupt and correct rows with nothing on disk to tell them apart.
        # kv_sharing joins the fingerprint for the same reason: the two
        # conditions produce different activations at the SAME keys, so
        # resuming across conditions would interleave them invisibly.
        if (prev.get("rows_sha256") == rows_sha
                and prev.get("hidden_states_indices") == hs_list
                and prev.get("forward_use_cache") is True
                and prev.get("kv_sharing", "on") == args.kv_sharing):
            tensors = dict(load_file(str(out_path)))
            row_meta = list(prev.get("rows", []))
            done_keys = {rm["row_key"] for rm in row_meta}
            print(f"[extract-anchor:{family}] resume: {len(done_keys)} rows already "
                  f"extracted, {len(rows) - len(done_keys)} remaining", flush=True)
        else:
            print(f"[extract-anchor:{family}] existing extract has a different "
                  f"fingerprint (rows/layers changed); starting fresh", flush=True)

    print(f"[extract-anchor:{family}] loading {cfg['checkpoint']['repo']} bf16, "
          f"hs_indices={hs_list}", flush=True)
    model, tokenizer, hidden_size, n_layers = ml.load_model_and_tokenizer(family)
    device = next(model.parameters()).device
    param_dtype = next(model.parameters()).dtype
    assert max(hs_list) <= n_layers, (
        f"requested hs={hs_list} requires >= {max(hs_list)} hidden layers, got {n_layers}"
    )

    # CALLER CONTRACT (cell.yaml `cache_contract`), applied here even though this
    # stage uses a plain forward rather than generate(): a fresh full-length
    # cache is passed in BOTH conditions. Under OFF it is required -- the shared
    # blocks index a cache transformers builds 24 entries long and raise
    # IndexError without it. Under ON it is a verified no-op (preflight check 4)
    # and is passed anyway so the two extracts differ in the sharing flag alone,
    # not in how the cache was constructed.
    kv_ctx, cache_factory = pl.kv_condition_context(family, model, args.kv_sharing)
    n_forwards = 0
    n_caches_built = 0

    def write_manifest(complete: bool) -> dict:
        manifest = {
            "stage": "j_space_cross_family_layer_contrast_anchor_extract",
            "family": family, "base_model": cfg["checkpoint"]["repo"],
            "substrate": "bf16", "torch_dtype": str(param_dtype),
            "hidden_size": hidden_size, "n_hidden_layers": n_layers,
            "layer_labels": [f"hs{h}" for h in hs_list],
            "hidden_states_indices": hs_list, "anchor_position": "prompt_len-1",
            "site_set": args.site_set,
            # The KV-sharing condition these activations were produced under.
            # Downstream fit stages refuse to consume an extract whose condition
            # differs from theirs (cell.yaml readouts.refit_policy).
            "kv_sharing": args.kv_sharing,
            "cache_contract": {
                "full_length_cache_passed": cache_factory is not None,
                "builder": "kv_seam_patch.build_full_length_cache",
                "freshness": "per forward",
                "n_forwards": n_forwards, "n_caches_built": n_caches_built,
            },
            # Provenance: any artifact WITHOUT this field set True predates the
            # 2026-07-24 KV-seam fix and is invalid on KV-sharing models.
            "forward_use_cache": True,
            "rows_path": str(rows_path), "rows_sha256": rows_sha,
            "out_path": str(out_path), "n_rows_extracted": len(row_meta),
            "n_rows_total": len(rows), "complete": complete,
            "runtime_sec": round(time.time() - t0, 1), "rows": row_meta,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    t0 = time.time()
    since_flush = 0
    with kv_ctx:
        for idx, row in enumerate(rows, start=1):
            if row["row_key"] in done_keys:
                continue
            rendered = ml.render(family, tokenizer, row)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            fwd_kwargs = {}
            if cache_factory is not None:
                # Fresh per row -- a Cache is stateful and reuse would leak the
                # previous row's K/V into this one's donor reads.
                fwd_kwargs["past_key_values"] = cache_factory()
                n_caches_built += 1
            n_forwards += 1
            with torch.no_grad():
                # use_cache MUST be True. On models that share K/V across layers
                # this is not a performance knob, it is a correctness
                # requirement. gemma-4-E4B blocks 24-41 read donor K/V from
                # blocks 22/23 THROUGH the cache object; with use_cache=False
                # those blocks are starved and every hidden state from hs25 up is
                # garbage (hs00-hs24 stay bit-identical, hs25-hs42 cos 0.732 ->
                # 0.075 vs the correct values), while `.generate()` -- which
                # defaults use_cache=True -- is fine. That silently invalidated
                # the entire first gemma extraction. llama / mistral / qwen are
                # unaffected (min cos 1.000000 either way), which is exactly why
                # this went unnoticed: CPU and GPU agreed at cos 0.998-0.9998
                # because BOTH ran the broken path -- that agreement is VACUOUS
                # as evidence of faithfulness.
                # This experiment is ABOUT the KV-sharing seam, so a starved-seam
                # forward would confound the very thing it measures.
                # See j-space-cross-family-layer-contrast AMENDMENT.md,
                # "Registered-instrument defects found at resolve", Defect 3.
                #
                # Note this is orthogonal to --kv-sharing: use_cache=True is how
                # the donor K/V reaches the shared blocks AT ALL, in both
                # conditions. The OFF condition severs the seam at the block
                # level (kv_seam_patch), not by starving the cache.
                out = model(**enc, output_hidden_states=True, use_cache=True,
                            **fwd_kwargs)
            hs = out.hidden_states
            safe = sanitize_key(row["row_key"])
            for hs_index in hs_list:
                tensors[f"hs{hs_index}__{safe}"] = (
                    hs[hs_index][0, prompt_len - 1, :].float().cpu().contiguous()
                )
            row_meta.append({
                "row_key": row["row_key"], "role": row["role"],
                "category_canon": row.get("category_canon"), "prompt_len": prompt_len,
            })
            since_flush += 1
            if since_flush >= FLUSH_EVERY:
                save_file(tensors, str(out_path))  # durable checkpoint
                write_manifest(complete=False)
                since_flush = 0
            if idx % 50 == 0 or idx == len(rows):
                print(f"[extract-anchor:{family}] {idx}/{len(rows)} "
                      f"(extracted {len(row_meta)})", flush=True)

    save_file(tensors, str(out_path))
    manifest = write_manifest(complete=True)
    print(json.dumps({k: manifest[k] for k in ("stage", "family", "n_rows_extracted",
                                                "runtime_sec")}, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--site-set", default="midband", choices=sorted(SITE_SETS),
                    help="named site set from families/<family>.yaml "
                         "band_selection; the late reference is always appended. "
                         "Default 'midband' preserves the pre-existing behaviour "
                         "exactly.")
    ap.add_argument("--kv-sharing", default=kv.DEFAULT_KV_SHARING,
                    choices=list(kv.KV_SHARING_CHOICES),
                    help="KV-sharing condition to extract UNDER. 'off' produces "
                         "the OFF activation cache that does not otherwise exist "
                         "anywhere -- the OFF model has never been run -- and "
                         "feeds both the OFF direction fits and G0-ALIN Part 2 "
                         "(cell.yaml pipeline_stages). A fresh full-length cache "
                         "is passed on every forward in BOTH conditions, per the "
                         "cache contract. Writes condition-scoped defaults; 'on' "
                         "keeps the historical filenames unchanged.")
    ap.add_argument("--rows", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--fresh", action="store_true",
                    help="Ignore any existing partial extraction and restart from row 0 "
                         "(default: resume from the last durable flush if the fingerprint matches).")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
