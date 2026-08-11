#!/usr/bin/env python3
"""GG0-GG7 fail-closed gate adjudication for flavor-atlas-gemma-pt-confirmatory
(AMENDMENT.md "Gates", gates.yaml). Consumes manifests/results already on
disk; issues no GPU verb and reads no weights itself.

Decision order matches gates.yaml: gg0..gg4 gate G1-G4 (P1/P2/P3, F1/F2/F4);
gg5 gates only the secondary (P4/F3); gg6 gates containment; gg7 is the
final adjudication, which only runs once every required gate has passed
(fail-closed: ANY prerequisite gate failure makes the dependent verdicts
`indeterminate`, never a silent pass or a downgraded-but-scored fail).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GateResult:
    name: str
    status: str  # "pass" | "fail" | "indeterminate"
    detail: str = ""
    checks: dict[str, Any] = field(default_factory=dict)


KUQ_CATEGORIES = [
    "ambiguous",
    "controversial",
    "counterfactual",
    "false assumption",
    "future unknown",
    "unsolved problem",
]


def load_yaml(path: Path) -> dict:
    import yaml
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def gg0_substrate_and_input_integrity(gates: dict, run_context: dict) -> GateResult:
    """run_context carries the resolved facts a real run would record:
    model_repo/revision, architecture facts, panel shas/counts, probe sha."""
    checks = gates["gg0_substrate_and_input_integrity"]["checks"]
    problems = []
    field_map = {
        "model_repo_must_equal": "model_repo",
        "model_revision_must_equal": "model_revision",
        "n_text_decoder_blocks_must_equal": "n_text_decoder_blocks",
        "n_hidden_states_must_equal": "n_hidden_states",
        "hidden_dim_must_equal": "hidden_dim",
        "kuq_panel_sha256_must_equal": "kuq_panel_sha256",
        "ambigqa_panel_sha256_must_equal": "ambigqa_panel_sha256",
        "selfaware_panel_sha256_must_equal": "selfaware_panel_sha256",
        "panels_manifest_sha256_must_equal": "panels_manifest_sha256",
        "probe_module_sha256_must_equal": "probe_module_sha256",
        "kuq_rows_must_equal": "kuq_rows",
        "kuq_known_must_equal": "kuq_known",
        "kuq_unknown_must_equal": "kuq_unknown",
        "ambigqa_rows_must_equal": "ambigqa_rows",
        "selfaware_rows_must_equal": "selfaware_rows",
    }
    for gate_key, ctx_key in field_map.items():
        expected = checks[gate_key]
        got = run_context.get(ctx_key)
        if got != expected:
            problems.append(f"{ctx_key}: got {got!r}, expected {expected!r}")
    if run_context.get("adapter_present", False):
        problems.append("adapter is present; must be absent")
    got_flavors = run_context.get("kuq_flavor_counts", {})
    for cat, expected in checks["kuq_flavor_counts_must_equal"].items():
        if got_flavors.get(cat) != expected:
            problems.append(f"kuq flavor '{cat}': got {got_flavors.get(cat)!r}, expected {expected!r}")
    status = "pass" if not problems else "fail"
    return GateResult("gg0", status, "; ".join(problems), {"problems": problems})


def gg1_kv_seam_admissibility(gates: dict, extraction_manifests: list[dict],
                               paired_smoke_outcome: str | None) -> GateResult:
    checks = gates["gg1_kv_seam_admissibility"]["checks"]
    problems = []
    for m in extraction_manifests:
        if m.get("forward_use_cache") is not True:
            problems.append(f"manifest for {m.get('render', '?')} missing forward_use_cache=true")
    admissible = set(checks["paired_smoke_admissible_outcomes"])
    if paired_smoke_outcome is None:
        return GateResult("gg1", "indeterminate", "GG1 live paired smoke not yet run", {})
    if paired_smoke_outcome == checks["paired_smoke_halt_outcome"]:
        return GateResult("gg1", "indeterminate",
                           f"paired smoke outcome '{paired_smoke_outcome}' is the halt outcome", {})
    if paired_smoke_outcome not in admissible:
        return GateResult("gg1", "indeterminate",
                           f"paired smoke outcome '{paired_smoke_outcome}' unrecognized", {})
    if problems:
        return GateResult("gg1", "fail", "; ".join(problems), {"problems": problems})
    return GateResult("gg1", "pass", f"paired smoke outcome: {paired_smoke_outcome}", {})


def gg2_capture_completeness(gates: dict, extraction_manifests: dict[str, dict]) -> GateResult:
    checks = gates["gg2_capture_completeness"]["checks"]
    expected_rows = {
        "kuq": checks["kuq_rows_extracted_must_equal"],
        "ambigqa": checks["ambigqa_rows_extracted_must_equal"],
        "selfaware": checks["selfaware_rows_extracted_must_equal"],
        "control": checks["dual_render_rows_extracted_must_equal"],
    }
    problems = []
    for name, expected in expected_rows.items():
        m = extraction_manifests.get(name)
        if m is None:
            problems.append(f"missing extraction manifest for '{name}'")
            continue
        if m.get("n_rows_extracted") != expected:
            problems.append(f"'{name}' n_rows_extracted={m.get('n_rows_extracted')}, expected {expected}")
        if m.get("complete") is not True:
            problems.append(f"'{name}' complete flag is not true")
        if m.get("n_hidden_states") != checks["n_hidden_states_present_must_equal"]:
            problems.append(f"'{name}' n_hidden_states={m.get('n_hidden_states')}, expected 43")
        if m.get("anchor_position") != checks["anchor_position_must_equal"]:
            problems.append(f"'{name}' anchor_position={m.get('anchor_position')!r}")
        if m.get("hidden_size") != checks["hidden_dim_must_equal"]:
            problems.append(f"'{name}' hidden_size={m.get('hidden_size')}, expected 2560")
    status = "pass" if not problems else "fail"
    return GateResult("gg2", status, "; ".join(problems), {"problems": problems})


def gg3_runtime_provenance(gates: dict, run_context: dict) -> GateResult:
    checks = gates["gg3_runtime_provenance"]["checks"]
    problems = []
    if checks.get("image_digest_must_equal_manifest_runtime_image_digest") and (
        run_context.get("runtime_image_digest") != run_context.get("manifest_runtime_image_digest")
    ):
        problems.append("runtime image digest does not match manifest-pinned digest")
    if checks.get("provenance_json_line_must_appear_in_each_run_log") and not run_context.get(
        "provenance_lines_present", False
    ):
        problems.append("provenance JSON line missing from a run log")
    status = "pass" if not problems else "fail"
    return GateResult("gg3", status, "; ".join(problems), {"problems": problems})


def gg4_hidden_state_0_sanity(gates: dict, hs0_aurocs: dict[str, float]) -> GateResult:
    checks = gates["gg4_hidden_state_0_sanity"]["checks"]
    ceiling = checks["hs0_auroc_must_be_at_most"]
    problems = [f"{name}: hs0 auroc {auc:.4f} > {ceiling}" for name, auc in hs0_aurocs.items() if auc > ceiling]
    status = "pass" if not problems else "fail"
    return GateResult("gg4", status, "; ".join(problems), {"problems": problems, "ceiling": ceiling})


def gg5_residualization_controls(gates: dict, treatment_r2: dict[str, float], permuted_r2_p95: float,
                                  permutation_passing: int, planted: dict) -> GateResult:
    checks = gates["gg5_residualization_controls"]["checks"]
    problems = []
    for layer_name, r2 in treatment_r2.items():
        if r2 < checks["min_activation_oof_r2_at_each_primary_layer"]:
            problems.append(f"{layer_name}: oof_r2 {r2:.4f} below floor")
        if r2 < permuted_r2_p95 + checks["min_above_permutation_quantile"]:
            problems.append(f"{layer_name}: oof_r2 {r2:.4f} not >= {checks['min_above_permutation_quantile']} above permutation p95 {permuted_r2_p95:.4f}")
    if permutation_passing < checks["min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90"]:
        problems.append(f"permutation negative control: {permutation_passing} passing, need >= "
                         f"{checks['min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90']}")
    if not planted.get("planted_pass"):
        problems.append(f"planted control raw AUROC {planted.get('planted_pooled_auroc')} below "
                         f"{checks['planted_pooled_auroc_must_reach_at_least']}")
    if not planted.get("residualized_pass"):
        problems.append(f"planted control residualized AUROC {planted.get('residualized_planted_pooled_auroc')} above "
                         f"{checks['residualized_planted_pooled_auroc_must_be_at_most']}")
    status = "pass" if not problems else "fail"
    return GateResult("gg5", status, "; ".join(problems), {"problems": problems})


def gg6_containment(gates: dict, committed_json: dict, private_texts: set[str]) -> GateResult:
    problems = []
    blob = json.dumps(committed_json)
    for text in private_texts:
        if text and text in blob:
            problems.append(f"prohibited text found in committed JSON: {text!r}")
    for prohibited_key in ("question", "row_level_matrix", "prediction", "activation"):
        if prohibited_key in blob.lower():
            problems.append(f"prohibited key-like substring '{prohibited_key}' found in committed JSON")
    status = "pass" if not problems else "fail"
    return GateResult("gg6", status, "; ".join(problems), {"problems": problems})


def adjudicate_p1_f1(gates: dict, dual_leg_decision: dict[str, dict]) -> dict:
    """P1/F1 (Clause A): all 6 flavors at or above 0.90 at BOTH legs."""
    floor = gates["g_bands"]["p1_replication_floor_heldout_auroc"]
    per_flavor = {}
    all_pass = True
    any_below = False
    for cat in KUQ_CATEGORIES:
        dl = dual_leg_decision[cat]
        a = dl["leg_a"]["auroc"]
        b = dl["leg_b"]["auroc"]
        passes = a >= floor and b >= floor
        per_flavor[cat] = {"leg_a": a, "leg_b": b, "pass": passes}
        if not passes:
            all_pass = False
        if a < floor or b < floor:
            any_below = True
    verdict = "P1_SUPPORTED" if all_pass else ("F1_FALSIFIED" if any_below else "AMBIGUOUS")
    return {"per_flavor": per_flavor, "floor": floor, "verdict": verdict}


def adjudicate_p2_f2(gates: dict, ambigqa_curve: list[float]) -> dict:
    ceiling = gates["g_bands"]["p2_ambigqa_ceiling_all_43_hidden_states"]
    f2_floor = 0.90
    max_val = max(ambigqa_curve)
    max_layer = int(max(range(len(ambigqa_curve)), key=lambda i: ambigqa_curve[i]))
    if max_val <= ceiling:
        verdict = "P2_SUPPORTED"
    elif max_val >= f2_floor:
        verdict = "F2_FALSIFIED"
    else:
        verdict = "AMBIGUOUS"
    return {"max_auroc": max_val, "max_layer": max_layer, "ceiling": ceiling, "verdict": verdict}


def adjudicate_p3_f4(gates: dict, transfer_matrix: dict[str, dict[str, float]]) -> dict:
    overt_floor = gates["g_bands"]["p3_transfer_offdiagonal_floor_among_seven_overt"]
    ambigqa_ceiling = gates["g_bands"]["p3_transfer_ambigqa_ceiling_either_direction"]
    overt_sources = KUQ_CATEGORIES + ["selfaware"]
    problems = []
    for src, row in transfer_matrix.items():
        for tgt, val in row.items():
            if src in overt_sources and tgt in overt_sources:
                if val < overt_floor:
                    problems.append(f"{src}->{tgt}: {val} < {overt_floor}")
            elif src == "ambigqa" or tgt == "ambigqa":
                if val > ambigqa_ceiling:
                    problems.append(f"{src}->{tgt}: {val} > {ambigqa_ceiling}")
    verdict = "P3_SUPPORTED" if not problems else "F4_FALSIFIED"
    return {"problems": problems, "verdict": verdict}


def adjudicate(gates: dict, gate_results: list[GateResult], readouts: dict) -> dict:
    """GG7: only adjudicate P/F once every prerequisite gate has passed.
    Fail-closed: any non-pass prerequisite gate makes the dependent
    verdict(s) indeterminate, never silently skipped."""
    by_name = {g.name: g for g in gate_results}
    core_gates = ["gg0", "gg1", "gg2", "gg3", "gg4"]
    core_ok = all(by_name[g].status == "pass" for g in core_gates if g in by_name)

    out: dict[str, Any] = {"gate_results": {g.name: {"status": g.status, "detail": g.detail} for g in gate_results}}

    if not core_ok:
        out["p1_f1"] = {"verdict": "INDETERMINATE", "reason": "one or more of GG0-GG4 did not pass"}
        out["p2_f2"] = {"verdict": "INDETERMINATE", "reason": "one or more of GG0-GG4 did not pass"}
        out["p3_f4"] = {"verdict": "INDETERMINATE", "reason": "one or more of GG0-GG4 did not pass"}
    else:
        if "dual_leg_decision" in readouts:
            out["p1_f1"] = adjudicate_p1_f1(gates, readouts["dual_leg_decision"])
        if "ambigqa_curve" in readouts:
            out["p2_f2"] = adjudicate_p2_f2(gates, readouts["ambigqa_curve"])
        if "transfer_matrix" in readouts:
            out["p3_f4"] = adjudicate_p3_f4(gates, readouts["transfer_matrix"])

    gg5 = by_name.get("gg5")
    if gg5 is None or gg5.status != "pass":
        out["p4_f3"] = {"verdict": "INDETERMINATE", "reason": "GG5 did not pass or was not run"}
    elif not core_ok:
        out["p4_f3"] = {"verdict": "INDETERMINATE", "reason": "core gates GG0-GG4 did not pass"}
    elif "residualized_dual_leg_decision" in readouts:
        out["p4_f3"] = adjudicate_p1_f1(gates, readouts["residualized_dual_leg_decision"])

    return out
