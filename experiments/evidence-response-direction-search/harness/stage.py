#!/usr/bin/env python3
"""SC0 staging for evidence-response-direction-search (M4c). Step 1 of the
execution sequence. Verifies and hash-pins every reused input BEFORE any fit
touches them: the three M4-WK channel-1 capture arms, `test_population.json`,
`c_hat_worldknown.json`, KUQ `c_hat.json`, and the KUQ doubt-snap anchor
extract + fit-rows sidecar. Writes `analysis-committed/staging_manifest.json`.

CPU only. No model. No generation/question/answer text is read into any
committed field (row ids, roles, and hashes only).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

from safetensors import safe_open  # noqa: E402

COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"


def _stage_arm(arm: str) -> dict:
    arm_dir = config.CAPTURE_SOURCE_DIR / arm
    capture_jsonl = arm_dir / "capture" / "capture.jsonl"
    if not capture_jsonl.is_file():
        raise SystemExit(f"stage FAIL: missing {capture_jsonl}")
    rows = common.load_jsonl(capture_jsonl)
    if len(rows) != config.N_ROWS_PER_ARM:
        raise SystemExit(f"stage FAIL: {arm} has {len(rows)} rows, expected {config.N_ROWS_PER_ARM}")

    role_counts: dict[str, int] = {}
    per_row = []
    for r in rows:
        role = r["role"]
        role_counts[role] = role_counts.get(role, 0) + 1
        tensor_path = arm_dir / "capture" / r["file"]
        if not tensor_path.is_file():
            raise SystemExit(f"stage FAIL: {arm} row {r['id']}: missing tensor file {tensor_path}")
        with safe_open(str(tensor_path), framework="numpy") as f:
            keys = list(f.keys())
            if keys != [config.ANCHOR_TENSOR_KEY]:
                raise SystemExit(f"stage FAIL: {arm} row {r['id']}: tensor keys {keys} != [{config.ANCHOR_TENSOR_KEY!r}]")
            vec = f.get_tensor(config.ANCHOR_TENSOR_KEY)
            if vec.shape != (config.HIDDEN_DIM,):
                raise SystemExit(f"stage FAIL: {arm} row {r['id']}: anchor shape {vec.shape} != ({config.HIDDEN_DIM},)")
        file_sha256 = common.sha256_of_file(tensor_path)
        per_row.append({"id": r["id"], "file": r["file"], "role": role, "sha256": file_sha256})

    if role_counts != config.ROLE_COMPOSITION_EXPECTED:
        raise SystemExit(f"stage FAIL: {arm} role composition {role_counts} != {config.ROLE_COMPOSITION_EXPECTED}")

    row_order = [r["id"] for r in rows]
    row_order_sha256 = common.sha256_of_bytes(
        __import__("json").dumps(row_order, sort_keys=False).encode("utf-8")
    )
    file_manifest_sha256 = common.sha256_of_bytes(
        __import__("json").dumps(sorted(per_row, key=lambda x: x["id"]), sort_keys=True).encode("utf-8")
    )
    return {
        "arm": arm,
        "n_rows": len(rows),
        "role_counts": role_counts,
        "row_order_sha256": row_order_sha256,
        "file_manifest_sha256": file_manifest_sha256,
        "per_row": per_row,
        "row_ids_set": sorted(row_order),
    }


def main() -> int:
    config.assert_pinned_hashes()

    arm_manifests = {}
    for arm in config.ARMS:
        print(f"[stage] staging arm {arm}...", flush=True)
        arm_manifests[arm] = _stage_arm(arm)
        print(f"[stage] {arm}: n_rows={arm_manifests[arm]['n_rows']} roles={arm_manifests[arm]['role_counts']}", flush=True)

    # Single-regime attestation: identical row_key SET across all three arms
    # (M4-WK's own row_order_sha256 differs across arms at the JSONL-write
    # level -- an artifact of their capture pipeline's internal composition
    # order vs write order -- but the row_key SET, which is what this harness
    # actually indexes on, must be identical; verified directly here rather
    # than assumed from their manifest).
    id_sets = {arm: set(m["row_ids_set"]) for arm, m in arm_manifests.items()}
    arms_list = list(config.ARMS)
    base_set = id_sets[arms_list[0]]
    for arm in arms_list[1:]:
        if id_sets[arm] != base_set:
            raise SystemExit(f"stage FAIL: row_key set mismatch between {arms_list[0]} and {arm}")
    print(f"[stage] single-regime attestation PASS: identical {len(base_set)}-row_key set across all 3 arms", flush=True)

    # test_population.json: byte-verify + role composition cross-check
    if not config.TEST_POPULATION_PATH.is_file():
        raise SystemExit(f"stage FAIL: missing {config.TEST_POPULATION_PATH}")
    test_pop_sha256 = common.sha256_of_file(config.TEST_POPULATION_PATH)
    if test_pop_sha256 != config.TEST_POPULATION_SHA256_PINNED:
        raise SystemExit(f"stage FAIL: test_population.json sha256 {test_pop_sha256} != pinned {config.TEST_POPULATION_SHA256_PINNED}")
    test_pop = common.load_json(config.TEST_POPULATION_PATH)
    tp_counts = test_pop["counts"]
    expected_short = {"confab": 400, "correct": 360, "refused": 241}
    if tp_counts != expected_short:
        raise SystemExit(f"stage FAIL: test_population.json counts {tp_counts} != {expected_short}")
    role_key_map = {"confab": config.ROLE_CONFAB, "correct": config.ROLE_CORRECT, "refused": config.ROLE_REFUSED}
    for short, long_role in role_key_map.items():
        tp_ids = set(test_pop["row_keys"][short])
        capture_ids = {r["id"] for r in arm_manifests[config.ARMS[0]]["per_row"] if r["role"] == long_role}
        if tp_ids != capture_ids:
            raise SystemExit(f"stage FAIL: test_population.json[{short}] row_keys != capture role={long_role} ids (n_pop={len(tp_ids)}, n_capture={len(capture_ids)})")
    print("[stage] test_population.json byte-verified + role composition cross-checked against captures", flush=True)

    # c_hat_worldknown.json: byte-verify
    c_hat_wk_sha256 = common.sha256_of_file(config.C_HAT_WORLDKNOWN_PATH)
    if c_hat_wk_sha256 != config.C_HAT_WORLDKNOWN_SHA256_PINNED:
        raise SystemExit(f"stage FAIL: c_hat_worldknown.json sha256 {c_hat_wk_sha256} != pinned {config.C_HAT_WORLDKNOWN_SHA256_PINNED}")
    print(f"[stage] c_hat_worldknown.json byte-verified: {c_hat_wk_sha256}", flush=True)

    # KUQ c_hat.json: byte-verify
    kuq_chat_sha256 = common.sha256_of_file(config.KUQ_CHAT_PATH)
    if kuq_chat_sha256 != config.KUQ_CHAT_SHA256_PINNED:
        raise SystemExit(f"stage FAIL: KUQ c_hat.json sha256 {kuq_chat_sha256} != pinned {config.KUQ_CHAT_SHA256_PINNED}")
    print(f"[stage] KUQ c_hat.json byte-verified: {kuq_chat_sha256}", flush=True)

    # KUQ anchor_extract.safetensors + fit_rows_for_anchor.jsonl: presence +
    # measured sha256 (no numeric pin in cell.yaml/gates.yaml/AMENDMENT for
    # these two files beyond "verified present on disk"; recorded for
    # provenance, not asserted against a pre-registered value).
    if not config.KUQ_ANCHOR_EXTRACT_PATH.is_file():
        raise SystemExit(f"stage FAIL: missing {config.KUQ_ANCHOR_EXTRACT_PATH}")
    if not config.KUQ_FIT_ROWS_PATH.is_file():
        raise SystemExit(f"stage FAIL: missing {config.KUQ_FIT_ROWS_PATH}")
    if not config.KUQ_ANCHOR_MANIFEST_PATH.is_file():
        raise SystemExit(f"stage FAIL: missing {config.KUQ_ANCHOR_MANIFEST_PATH}")
    kuq_anchor_extract_sha256 = common.sha256_of_file(config.KUQ_ANCHOR_EXTRACT_PATH)
    kuq_fit_rows_sha256 = common.sha256_of_file(config.KUQ_FIT_ROWS_PATH)
    print(f"[stage] KUQ anchor_extract.safetensors staged: {kuq_anchor_extract_sha256}", flush=True)
    print(f"[stage] KUQ fit_rows_for_anchor.jsonl staged: {kuq_fit_rows_sha256}", flush=True)

    manifest = {
        "config_hashes_verified": config.verify_pinned_hashes(),
        "capture_arms": {
            arm: {
                "n_rows": m["n_rows"],
                "role_counts": m["role_counts"],
                "row_order_sha256": m["row_order_sha256"],
                "file_manifest_sha256": m["file_manifest_sha256"],
                "per_row": m["per_row"],
            }
            for arm, m in arm_manifests.items()
        },
        "single_regime_attestation": {
            "identical_row_key_set_across_arms": True,
            "n_row_keys": len(base_set),
            "note": "M4-WK's own per-arm row_order_sha256 (capture_manifest.json) reflects internal batch-composition order, not JSONL write order; this harness verifies row_key SET identity directly instead of reproducing that hash.",
        },
        "test_population": {
            "path": str(config.TEST_POPULATION_PATH),
            "sha256": test_pop_sha256,
            "matches_pin": True,
            "counts": tp_counts,
            "role_composition_cross_checked_against_captures": True,
        },
        "c_hat_worldknown": {
            "path": str(config.C_HAT_WORLDKNOWN_PATH),
            "sha256": c_hat_wk_sha256,
            "matches_pin": True,
        },
        "kuq_c_hat": {
            "path": str(config.KUQ_CHAT_PATH),
            "sha256": kuq_chat_sha256,
            "matches_pin": True,
        },
        "kuq_anchor_extract": {
            "safetensors_path": str(config.KUQ_ANCHOR_EXTRACT_PATH),
            "safetensors_sha256": kuq_anchor_extract_sha256,
            "fit_rows_path": str(config.KUQ_FIT_ROWS_PATH),
            "fit_rows_sha256": kuq_fit_rows_sha256,
            "manifest_path": str(config.KUQ_ANCHOR_MANIFEST_PATH),
            "note": "no numeric sha256 pin registered in cell.yaml/gates.yaml/AMENDMENT for these two files beyond presence-on-disk; hashes recorded for provenance.",
        },
        "detector_stack": {
            "applicable": False,
            "note": "gates.yaml SC2 states rungs (a), (c), and the KUQ transfer readout need no grading; all role labels (confab/correct/refused, known_correct_answered) are reused verbatim from M4-WK's and doubt-snap's already-graded artifacts. No detector/grader code is invoked by this CPU-rung harness, so no detector-stack hash applies here.",
        },
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    common.write_json(COMMITTED / "staging_manifest.json", manifest)
    print(f"[stage] wrote {COMMITTED / 'staging_manifest.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
