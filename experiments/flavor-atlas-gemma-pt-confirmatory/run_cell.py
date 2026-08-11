#!/usr/bin/env python3
"""CPU-side orchestrator for flavor-atlas-gemma-pt-confirmatory
(AMENDMENT.md "Design", "Containment"; cell.yaml; gates.yaml).

Given GPU extractions that already exist on disk, runs the full registered
read-side chain in order:

  1. panel verify + reuse       (build_flavor_panels.py, subprocess)
  2. probe sweep, both legs     (flavor_probe_sweep.py, subprocess)
  3. residualization secondary  (surface_residualization.py, driven for
                                  real over the real panels/extractions --
                                  this module's first and only committed
                                  real-data caller; the module itself stays
                                  library-only)
  4. gate adjudication          (gate_adjudicator.py, over the real
                                  readouts from steps 1-3; this script is
                                  gate_adjudicator.py's first and only
                                  committed real-data caller)

and writes the counts-only committed output at
`analysis-committed/gemma_flavor_sweep.json` (AMENDMENT.md "Containment"):
AUROCs, class counts, best layers, full layer curves, the transfer matrix,
residualized curves, control summaries, gate records, input shas, and the
extraction manifests' `forward_use_cache` values. No question text, no
row-level surface matrix, no row-level prediction, and no activation ever
enters this file (GG6 refuses to write it otherwise).

This orchestrator NEVER runs a GPU verb and NEVER wraps or re-implements
`extract_anchor_gemma.py`. It only reads extraction manifests that already
exist on disk (read-only) and refuses to proceed if any is missing or
KV-seam-inadmissible (`forward_use_cache != true`). The live 32-row GG1
paired smoke (`kv_seam_paired_smoke.py --mode=live`) is a separate,
GPU-gated step; its outcome, if already run, is supplied via
`--paired-smoke-outcome`. Omitting it correctly leaves GG1 -- and by
fail-closed propagation, every P/F verdict -- INDETERMINATE.

--dry-run resolves every required input, prints the full execution plan,
executes nothing, writes nothing, and exits nonzero listing exactly what is
missing. Before any GPU capture exists, a nonzero --dry-run exit is the
CORRECT outcome, not a bug.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.resolve().parents[1]
GATES_PATH = HERE / "gates.yaml"
EXPERIMENT_YAML_PATH = HERE / "experiment.yaml"
ITEM26_DIR = REPO_ROOT / "experiments" / "ood-breadth-beyond-selfaware"
RAWBASE_PANELS_DIR = REPO_ROOT / "experiments" / "flavor-atlas-rawbase" / "analysis" / "panels"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ITEM26_DIR))

KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]

# g_bands.n_permutations (gates.yaml gg5_residualization_controls). Overridable
# via --n-permutations for a fast smoke; the registered default is 20.
N_PERMUTATIONS_DEFAULT = 20


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Plan resolution (--dry-run and the pre-flight check the real run shares)
# ---------------------------------------------------------------------------

def resolve_plan(args: argparse.Namespace) -> dict:
    """Resolve every input this cell needs. Read-only (stat/exists checks
    only); never executes a stage, never writes anything."""
    gates = load_yaml(GATES_PATH)
    checks = gates["gg0_substrate_and_input_integrity"]["checks"]

    source_panels = {
        "kuq": {
            "path": args.rawbase_panels_dir / "kuq_panel.jsonl",
            "expected_sha256": checks["kuq_panel_sha256_must_equal"],
        },
        "ambigqa": {
            "path": args.rawbase_panels_dir / "ambigqa_panel.jsonl",
            "expected_sha256": checks["ambigqa_panel_sha256_must_equal"],
        },
        "selfaware": {
            "path": args.rawbase_panels_dir / "selfaware_panel.jsonl",
            "expected_sha256": checks["selfaware_panel_sha256_must_equal"],
        },
    }
    for info in source_panels.values():
        info["exists"] = info["path"].is_file()

    extraction_dirs = {
        "kuq": args.extraction_root / "kuq",
        "ambigqa": args.extraction_root / "ambigqa",
        "selfaware": args.extraction_root / "selfaware",
        "control": args.control_extraction_dir,
    }
    extractions = {}
    for name, ext_dir in extraction_dirs.items():
        manifest_path = ext_dir / "manifest.json"
        extractions[name] = {
            "extraction_dir": ext_dir,
            "manifest_path": manifest_path,
            "exists": manifest_path.is_file(),
        }

    probe_module = ITEM26_DIR / "internal_panel_probe_gate.py"

    return {
        "source_panels": source_panels,
        "extractions": extractions,
        "probe_module": {"path": probe_module, "exists": probe_module.is_file()},
        "outputs": {
            "panels_dir": args.panels_dir,
            "probe_result": args.probe_out,
            "residualization_result": args.residualization_out,
            "committed_output": args.committed_out,
        },
    }


def missing_inputs(plan: dict) -> list[str]:
    missing = []
    for name, info in plan["source_panels"].items():
        if not info["exists"]:
            missing.append(f"source panel '{name}' missing: {info['path']}")
    for name, info in plan["extractions"].items():
        if not info["exists"]:
            missing.append(f"extraction manifest '{name}' missing: {info['manifest_path']}")
    if not plan["probe_module"]["exists"]:
        missing.append(f"pinned probe module missing: {plan['probe_module']['path']}")
    return missing


def _plan_json(plan: dict) -> dict:
    out: dict = {"source_panels": {}, "extractions": {}, "probe_module": {}, "outputs": {}}
    for name, info in plan["source_panels"].items():
        out["source_panels"][name] = {
            "path": str(info["path"]),
            "expected_sha256": info["expected_sha256"],
            "exists": info["exists"],
        }
    for name, info in plan["extractions"].items():
        out["extractions"][name] = {
            "manifest_path": str(info["manifest_path"]),
            "exists": info["exists"],
        }
    out["probe_module"] = {"path": str(plan["probe_module"]["path"]), "exists": plan["probe_module"]["exists"]}
    out["outputs"] = {k: str(v) for k, v in plan["outputs"].items()}
    return out


# ---------------------------------------------------------------------------
# Stage 0: read-only seam-admissibility + completeness check on GPU outputs
# that already exist. Never triggers extraction.
# ---------------------------------------------------------------------------

def require_seam_admissible(extractions: dict) -> list[dict]:
    manifests = []
    problems = []
    for name, info in extractions.items():
        manifest = json.loads(info["manifest_path"].read_text(encoding="utf-8"))
        manifest["_source"] = name
        manifests.append(manifest)
        if manifest.get("forward_use_cache") is not True:
            problems.append(f"extraction '{name}' manifest does not record forward_use_cache=true")
        if manifest.get("complete") is not True:
            problems.append(f"extraction '{name}' manifest complete flag is not true")
    if problems:
        raise SystemExit("GG1 STOP: " + "; ".join(problems))
    return manifests


# ---------------------------------------------------------------------------
# Stage 1: panel verify + reuse (subprocess of the exact committed command)
# ---------------------------------------------------------------------------

def run_panel_verify(args: argparse.Namespace) -> dict:
    cmd = [
        sys.executable, str(HERE / "build_flavor_panels.py"),
        "--source-dir", str(args.rawbase_panels_dir),
        "--panels-dir", str(args.panels_dir),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"panel verify failed (exit {proc.returncode})")
    return json.loads((args.panels_dir / "panels_manifest.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Stage 2: probe sweep, both legs, plus G6 (subprocess of the exact
# committed command). The dual-render control panel is recomputed
# deterministically from the just-verified kuq panel (render_gemma's fixed
# seed), so its row_keys line up with whatever the GPU control capture used.
# ---------------------------------------------------------------------------

def run_probe_sweep(args: argparse.Namespace) -> dict:
    import render_gemma as rg

    kuq_rows = load_jsonl(args.panels_dir / "kuq_panel.jsonl")
    subsample = rg.select_dual_render_subsample(kuq_rows)
    control_panel_path = args.panels_dir / "control_panel.jsonl"
    with control_panel_path.open("w", encoding="utf-8") as fh:
        for r in subsample:
            fh.write(json.dumps(r) + "\n")

    cmd = [
        sys.executable, str(HERE / "flavor_probe_sweep.py"),
        "--panels-dir", str(args.panels_dir),
        "--extraction-root", str(args.extraction_root),
        "--control-panel", str(control_panel_path),
        "--control-extraction-dir", str(args.control_extraction_dir),
        "--out", str(args.probe_out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"probe sweep failed (exit {proc.returncode})")
    return json.loads(args.probe_out.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Stage 3: residualization secondary, driven for real (surface_residualization.py
# is library-only; this is its first and only committed real-data caller).
# G5 residualizes exactly the cells G1/dual-leg already decided on: the
# selected layers are READ from probe_result, never re-derived here.
# ---------------------------------------------------------------------------

def run_residualization(args: argparse.Namespace, probe_result: dict) -> dict:
    import flavor_probe_sweep as fps
    import surface_residualization as sr

    kuq_rows = load_jsonl(args.panels_dir / "kuq_panel.jsonl")
    ambigqa_rows = load_jsonl(args.panels_dir / "ambigqa_panel.jsonl")
    selfaware_rows = load_jsonl(args.panels_dir / "selfaware_panel.jsonl")

    kuq_panel = fps.SourcePanel("kuq", kuq_rows, args.extraction_root / "kuq")

    # AMENDMENT.md G5: one unsupervised surface basis fit on the union of
    # the three panels' question strings, unlabeled.
    questions = (
        [r["question"] for r in kuq_rows]
        + [r["question"] for r in ambigqa_rows]
        + [r["question"] for r in selfaware_rows]
    )
    z_union = sr.build_surface_matrix(questions, seed=0)
    z_kuq = z_union[: len(kuq_rows)]

    dual_leg_raw = probe_result["dual_leg_decision"]

    treatment_r2: dict[str, float] = {}
    residualized_dual_leg: dict[str, dict] = {}

    for cat in KUQ_CATEGORIES:
        mask = fps.m1_flavor_mask(kuq_panel, cat)
        idx = np.where(mask)[0]
        y_sub = kuq_panel.y_known[idx]
        strata = [str(v) for v in y_sub]
        z_sub = z_kuq[idx]

        leg_a_layer = dual_leg_raw[cat]["leg_a"]["hidden_state"]
        leg_b_layer = dual_leg_raw[cat]["leg_b"]["selected_layer"]

        h_a = kuq_panel.matrix_at(leg_a_layer)[idx]
        residual_a, _yhat_a, _alphas_a = sr.crossfit_ridge(h_a, z_sub, strata, seed=0)
        r2_a = sr.activation_oof_r2(h_a, residual_a)
        auc_a = sr.residualized_probe_auroc(residual_a, y_sub)
        treatment_r2[f"{cat}_leg_a_hs{leg_a_layer}"] = round(r2_a, 4)

        h_b = kuq_panel.matrix_at(leg_b_layer)[idx]
        residual_b, _yhat_b, _alphas_b = sr.crossfit_ridge(h_b, z_sub, strata, seed=0)
        r2_b = sr.activation_oof_r2(h_b, residual_b)
        auc_b = sr.residualized_probe_auroc(residual_b, y_sub)
        treatment_r2[f"{cat}_leg_b_hs{leg_b_layer}"] = round(r2_b, 4)

        residualized_dual_leg[cat] = {
            "leg_a": {"hidden_state": leg_a_layer, "auroc": round(auc_a, 4), "oof_r2": round(r2_a, 4)},
            "leg_b": {"selected_layer": leg_b_layer, "auroc": round(auc_b, 4), "oof_r2": round(r2_b, 4)},
        }

    # Permutation negative control: gates.yaml gg5's pass condition is
    # counted PER REPETITION across all twelve primary cells (six flavors,
    # both legs), not per cell independently.
    rng = np.random.default_rng(0)
    permutation_passing = 0
    permuted_r2_values: list[float] = []
    for rep in range(args.n_permutations):
        rep_all_pass = True
        for cat in KUQ_CATEGORIES:
            mask = fps.m1_flavor_mask(kuq_panel, cat)
            idx = np.where(mask)[0]
            y_sub = kuq_panel.y_known[idx]
            strata = [str(v) for v in y_sub]
            z_sub = z_kuq[idx]
            perm = rng.permutation(len(z_sub))
            z_perm = z_sub[perm]
            for layer in (dual_leg_raw[cat]["leg_a"]["hidden_state"], dual_leg_raw[cat]["leg_b"]["selected_layer"]):
                h = kuq_panel.matrix_at(layer)[idx]
                residual, _yhat, _alphas = sr.crossfit_ridge(h, z_perm, strata, seed=rep)
                permuted_r2_values.append(sr.activation_oof_r2(h, residual))
                auc = sr.residualized_probe_auroc(residual, y_sub)
                if auc < 0.90:
                    rep_all_pass = False
        if rep_all_pass:
            permutation_passing += 1
    permuted_r2_p95 = float(np.percentile(permuted_r2_values, 95)) if permuted_r2_values else 0.0

    # Planted-channel positive control at hs0 (provably-null layer), pooled
    # all-unknowns mask.
    pooled_mask = fps.m1_flavor_mask(kuq_panel, None)
    pooled_idx = np.where(pooled_mask)[0]
    y_pooled = kuq_panel.y_known[pooled_idx]
    strata_pooled = [str(v) for v in y_pooled]
    z_pooled = z_kuq[pooled_idx]
    h0 = kuq_panel.matrix_at(0)[pooled_idx]
    planted = sr.planted_channel_positive_control(h0, z_pooled, strata_pooled, y_pooled, seed=0)

    return {
        "surface_basis": "prompt-text-shape-only (no source/panel/category/flavor/label), union of kuq+ambigqa+selfaware panels, unlabeled",
        "treatment_r2": treatment_r2,
        "permuted_r2_p95": round(permuted_r2_p95, 4),
        "permutation_passing": permutation_passing,
        "n_permutations": args.n_permutations,
        "planted": planted,
        "residualized_dual_leg_decision": residualized_dual_leg,
    }


# ---------------------------------------------------------------------------
# Stage 4: gate adjudication over the real readouts (gate_adjudicator.py is
# library-only; this is its first and only committed real-data caller).
# ---------------------------------------------------------------------------

def build_run_context(args: argparse.Namespace, extraction_manifests: list[dict],
                       panels_manifest: dict, probe_module_sha: str) -> dict:
    by_source = {m["_source"]: m for m in extraction_manifests}
    kuq_manifest = by_source["kuq"]
    return {
        "model_repo": kuq_manifest["model_repo"],
        "model_revision": kuq_manifest["revision"],
        "n_text_decoder_blocks": kuq_manifest["n_hidden_layers"],
        "n_hidden_states": kuq_manifest["n_hidden_states"],
        "hidden_dim": kuq_manifest["hidden_size"],
        # extract_anchor_gemma.py never loads a PEFT adapter; "no adapter" is
        # part of its fixed base_form string, not self-reported after the fact.
        "adapter_present": "no adapter" not in kuq_manifest.get("base_form", ""),
        "kuq_panel_sha256": panels_manifest["reused_from"]["kuq"]["sha256"],
        "ambigqa_panel_sha256": panels_manifest["reused_from"]["ambigqa"]["sha256"],
        "selfaware_panel_sha256": panels_manifest["reused_from"]["selfaware"]["sha256"],
        "panels_manifest_sha256": sha256_file(args.panels_dir / "panels_manifest.json"),
        "probe_module_sha256": probe_module_sha,
        "kuq_rows": panels_manifest["counts"]["kuq"]["n"],
        "kuq_known": panels_manifest["counts"]["kuq"]["by_label"].get("known", 0),
        "kuq_unknown": panels_manifest["counts"]["kuq"]["by_label"].get("unknown", 0),
        "ambigqa_rows": panels_manifest["counts"]["ambigqa"]["n"],
        "selfaware_rows": panels_manifest["counts"]["selfaware"]["n"],
        "kuq_flavor_counts": panels_manifest["counts"]["kuq"]["by_flavor"],
    }


def run_gate_adjudication(args: argparse.Namespace, gates: dict, extraction_manifests: list[dict],
                           run_context: dict, probe_result: dict, residualization_result: dict) -> dict:
    import gate_adjudicator as ga

    gg0 = ga.gg0_substrate_and_input_integrity(gates, run_context)
    gg1 = ga.gg1_kv_seam_admissibility(gates, extraction_manifests, args.paired_smoke_outcome)

    manifests_by_name = {m["_source"]: m for m in extraction_manifests}
    gg2 = ga.gg2_capture_completeness(gates, manifests_by_name)

    manifest_digest = load_yaml(EXPERIMENT_YAML_PATH)["instrument"]["runtime_image_digest"]
    gg3_context = {
        "runtime_image_digest": args.runtime_image_digest,
        "manifest_runtime_image_digest": manifest_digest,
        "provenance_lines_present": args.provenance_lines_present,
    }
    gg3 = ga.gg3_runtime_provenance(gates, gg3_context)

    hs0_aurocs = {cat: probe_result["g1_kuq"]["flavors"][cat]["auroc"][0] for cat in KUQ_CATEGORIES}
    hs0_aurocs["pooled"] = probe_result["g1_kuq"]["flavors"]["pooled_all_unknowns"]["auroc"][0]
    hs0_aurocs["selfaware"] = probe_result["g3_selfaware"]["auroc"][0]
    hs0_aurocs["ambigqa"] = probe_result["g2_ambigqa"]["auroc"][0]
    gg4 = ga.gg4_hidden_state_0_sanity(gates, hs0_aurocs)

    gg5 = ga.gg5_residualization_controls(
        gates,
        residualization_result["treatment_r2"],
        residualization_result["permuted_r2_p95"],
        residualization_result["permutation_passing"],
        residualization_result["planted"],
    )

    readouts = {
        "dual_leg_decision": probe_result["dual_leg_decision"],
        "ambigqa_curve": probe_result["g2_ambigqa"]["auroc"],
        "transfer_matrix": probe_result["g4_transfer_matrix"].get("matrix", {}),
        "residualized_dual_leg_decision": residualization_result["residualized_dual_leg_decision"],
    }

    return ga.adjudicate(gates, [gg0, gg1, gg2, gg3, gg4, gg5], readouts)


# ---------------------------------------------------------------------------
# Stage 5: assemble + write the counts-only committed output (GG6 refuses
# the write if containment fails).
# ---------------------------------------------------------------------------

def build_committed_output(run_context: dict, extraction_manifests: list[dict], probe_result: dict,
                            residualization_result: dict, adjudication: dict) -> dict:
    forward_use_cache_by_source = {m["_source"]: m.get("forward_use_cache") for m in extraction_manifests}
    return {
        "cell": "flavor-atlas-gemma-pt-confirmatory",
        "generated_at_utc": _utc_now_iso(),
        "input_shas": {
            "kuq_panel_sha256": run_context["kuq_panel_sha256"],
            "ambigqa_panel_sha256": run_context["ambigqa_panel_sha256"],
            "selfaware_panel_sha256": run_context["selfaware_panel_sha256"],
            "panels_manifest_sha256": run_context["panels_manifest_sha256"],
            "probe_module_sha256": run_context["probe_module_sha256"],
        },
        "extraction_forward_use_cache": forward_use_cache_by_source,
        "g1_kuq": probe_result["g1_kuq"],
        "g2_ambigqa": probe_result["g2_ambigqa"],
        "g3_selfaware": probe_result["g3_selfaware"],
        "g4_transfer_matrix": probe_result["g4_transfer_matrix"],
        "dual_leg_decision": probe_result["dual_leg_decision"],
        "g6_dual_render_control_chat_template": probe_result.get("g6_dual_render_control_chat_template"),
        "g5_residualization": {
            "surface_basis": residualization_result["surface_basis"],
            "treatment_r2": residualization_result["treatment_r2"],
            "permuted_r2_p95": residualization_result["permuted_r2_p95"],
            "permutation_passing": residualization_result["permutation_passing"],
            "n_permutations": residualization_result["n_permutations"],
            "planted": residualization_result["planted"],
            "residualized_dual_leg_decision": residualization_result["residualized_dual_leg_decision"],
        },
        "gate_adjudication": adjudication,
    }


def finalize_and_write(args: argparse.Namespace, committed: dict, gates: dict, private_texts: set[str]) -> dict:
    import gate_adjudicator as ga

    gg6 = ga.gg6_containment(gates, committed, private_texts)
    committed["gate_adjudication"]["gate_results"]["gg6"] = {"status": gg6.status, "detail": gg6.detail}
    if gg6.status != "pass":
        raise SystemExit(f"GG6 CONTAINMENT STOP: refusing to write committed output: {gg6.detail}")
    args.committed_out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.committed_out.with_suffix(args.committed_out.suffix + ".tmp")
    tmp.write_text(json.dumps(committed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(args.committed_out)
    return committed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rawbase-panels-dir", type=Path, default=RAWBASE_PANELS_DIR)
    ap.add_argument("--panels-dir", type=Path, default=HERE / "analysis" / "panels")
    ap.add_argument("--extraction-root", type=Path, default=HERE / "analysis" / "extraction")
    ap.add_argument("--control-extraction-dir", type=Path, default=HERE / "analysis" / "extraction" / "control")
    ap.add_argument("--probe-out", type=Path, default=HERE / "analysis" / "probe" / "gemma_flavor_atlas_result.json")
    ap.add_argument("--residualization-out", type=Path,
                     default=HERE / "analysis" / "residualization" / "gemma_flavor_residualized.json")
    ap.add_argument("--committed-out", type=Path, default=HERE / "analysis-committed" / "gemma_flavor_sweep.json")
    ap.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS_DEFAULT,
                     help="gg5 permutation negative control repetitions (registered default 20; "
                          "override only for a fast smoke, never for a real run)")
    ap.add_argument("--paired-smoke-outcome", default=None,
                     help="GG1 live 32-row paired smoke outcome from a real GPU run; omit to leave "
                          "GG1 -- and by fail-closed propagation, everything downstream -- indeterminate")
    ap.add_argument("--runtime-image-digest", default=None,
                     help="GG3: the image digest actually used for the GPU verbs; omit to leave GG3 indeterminate")
    ap.add_argument("--provenance-lines-present", action="store_true",
                     help="GG3: set only after confirming every GPU run log carries its provenance line")
    ap.add_argument("--dry-run", action="store_true",
                     help="resolve every input and print the plan; execute nothing, write nothing")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    plan = resolve_plan(args)

    if args.dry_run:
        print(json.dumps(_plan_json(plan), indent=2))
        missing = missing_inputs(plan)
        if missing:
            print("\nDRY-RUN: missing inputs, nothing executed, nothing written:", file=sys.stderr)
            for m in missing:
                print(f"  - {m}", file=sys.stderr)
            return 2
        print("\nDRY-RUN: all inputs resolved; nothing executed, nothing written.", file=sys.stderr)
        return 0

    missing = missing_inputs(plan)
    if missing:
        print("REFUSING TO RUN: missing inputs:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 2

    gates = load_yaml(GATES_PATH)

    extraction_manifests = require_seam_admissible(plan["extractions"])
    panels_manifest = run_panel_verify(args)
    probe_result = run_probe_sweep(args)
    residualization_result = run_residualization(args, probe_result)

    probe_module_sha = sha256_file(plan["probe_module"]["path"])
    run_context = build_run_context(args, extraction_manifests, panels_manifest, probe_module_sha)

    adjudication = run_gate_adjudication(
        args, gates, extraction_manifests, run_context, probe_result, residualization_result,
    )

    kuq_rows = load_jsonl(args.panels_dir / "kuq_panel.jsonl")
    ambigqa_rows = load_jsonl(args.panels_dir / "ambigqa_panel.jsonl")
    selfaware_rows = load_jsonl(args.panels_dir / "selfaware_panel.jsonl")
    private_texts = {r["question"] for r in kuq_rows + ambigqa_rows + selfaware_rows}

    committed = build_committed_output(run_context, extraction_manifests, probe_result,
                                        residualization_result, adjudication)
    finalize_and_write(args, committed, gates, private_texts)

    print(json.dumps({"status": "wrote committed output", "path": str(args.committed_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
