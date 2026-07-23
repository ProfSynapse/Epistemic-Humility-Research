#!/usr/bin/env python3
"""SC1 GPU preflight for susceptibility-as-probe (M2) -- Decision record
item 7 / gates.yaml `SC1_capture_integrity` standing directive: an 8-row
capture smoke and an 8-row elicitation smoke, manifest-checked, MUST pass
before either full pass runs. Writes the code-enforced pass marker
`analysis/preflight/PASS.json` that `capture.py`/`elicit.py` refuse to run
the full population without.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import capture as capture_mod  # noqa: E402
import elicit as elicit_mod  # noqa: E402
import population as population_mod  # noqa: E402

PREFLIGHT_DIR = config.EXPERIMENT_DIR / "analysis" / "preflight"


def run_capture_smoke() -> dict:
    out_dir = PREFLIGHT_DIR / "capture_smoke"
    rows = population_mod.build_population()[: config.PREFLIGHT_CAPTURE_SMOKE_ROWS]

    cap_rows, template_sha256 = capture_mod.render_rows(rows)
    capture_mod.run_capture(cap_rows, out_dir, batch_size=config.PREFLIGHT_CAPTURE_SMOKE_ROWS)
    integrity = capture_mod.verify_capture_integrity(cap_rows, out_dir)
    scores = capture_mod.compute_readout_scores(cap_rows, out_dir)

    # Explicit layer_index / hs_index / anchor-position / fp32-persist checks
    # (cell.yaml `channels.readout.direction.layer_index: 19`, `hs_index: 20`).
    import torch
    from safetensors.torch import load_file

    index = common.load_jsonl(out_dir / "capture" / "capture.jsonl")
    dtype_checks = []
    for rec in index:
        tensors = load_file(str(out_dir / "capture" / rec["file"]))
        key = f"anchor__L{config.READOUT_HS_INDEX}"
        t = tensors[key]
        dtype_checks.append(t.dtype == torch.float32)

    checks = {
        "n_smoke_rows": len(rows),
        "n_captured": integrity["n_captured"],
        "zero_silent_drops": integrity["zero_silent_drops"],
        "all_positions_match_len_minus_1": integrity["all_positions_match"],
        "all_layer_shapes_match": integrity["all_layer_shapes_match"],
        "hs_index_requested": config.READOUT_HS_INDEX,
        "layer_index_derived": config.READOUT_HS_INDEX - 1,
        "layer_index_matches_cell_yaml_19": (config.READOUT_HS_INDEX - 1) == 19,
        "all_tensors_persisted_fp32": all(dtype_checks) and len(dtype_checks) == len(rows),
        "n_readout_scores_computed": len(scores),
        "readout_scores_finite": all(_is_finite(v) for v in scores.values()),
    }
    checks["pass"] = all([
        checks["zero_silent_drops"], checks["all_positions_match_len_minus_1"],
        checks["all_layer_shapes_match"], checks["layer_index_matches_cell_yaml_19"],
        checks["all_tensors_persisted_fp32"], checks["n_readout_scores_computed"] == len(rows),
        checks["readout_scores_finite"],
    ])
    common.write_json(out_dir / "smoke_check.json", checks)
    return checks


def _is_finite(x: float) -> bool:
    import math
    return math.isfinite(x)


def _live_cell_yaml_template_suffix() -> str:
    cfg = yaml.safe_load(config.CELL_YAML_PATH.read_text(encoding="utf-8"))
    return cfg["channels"]["verbalized_confidence"]["template_user_suffix"]


def run_elicitation_smoke() -> dict:
    out_dir = PREFLIGHT_DIR / "elicit_smoke"
    rows = population_mod.build_population()[: config.PREFLIGHT_ELICITATION_SMOKE_ROWS]

    prompt_rows, template_sha256 = elicit_mod.render_rows(rows)
    elicit_mod.run_generate(prompt_rows, out_dir, batch_size=config.PREFLIGHT_ELICITATION_SMOKE_ROWS)

    completions = common.load_jsonl(out_dir / "generate" / "completions.jsonl")
    completions_by_id = {c["id"]: c for c in completions}
    expected_ids = {r["id"] for r in prompt_rows}

    live_suffix = _live_cell_yaml_template_suffix().strip()
    pinned_suffix = config.CONFIDENCE_TEMPLATE_USER_SUFFIX.strip()
    # cell.yaml uses a YAML block scalar (">-"); normalize internal whitespace
    # runs to single spaces before comparing so line-wrap folding doesn't
    # register as a false mismatch.
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    template_matches_cell_yaml = norm(live_suffix) == norm(pinned_suffix)

    parsed = []
    n_parsed = 0
    for row_key in sorted(expected_ids):
        comp = completions_by_id.get(row_key)
        if comp is None:
            parsed.append({"row_key": row_key, "confidence": None, "reason": "missing_completion"})
            continue
        value, reason = elicit_mod.parse_confidence(comp["completion_text"])
        if value is not None:
            n_parsed += 1
        parsed.append({"row_key": row_key, "confidence": value, "reason": reason, "completion_text": comp["completion_text"]})

    checks = {
        "n_smoke_rows": len(rows),
        "n_completions_captured": len(completions_by_id),
        "zero_missing_completions": len(expected_ids - set(completions_by_id.keys())) == 0,
        "template_matches_cell_yaml": template_matches_cell_yaml,
        "n_parsed": n_parsed,
        "parse_examples": parsed,
        "at_least_one_parseable": n_parsed >= 1,
    }
    checks["pass"] = bool(
        checks["zero_missing_completions"] and checks["template_matches_cell_yaml"] and checks["at_least_one_parseable"]
    )
    common.write_json(out_dir / "smoke_check.json", checks)
    return checks


def main() -> int:
    hashes = config.verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"preflight FAIL: cell.yaml/gates.yaml sha256 mismatch: {hashes}")

    capture_checks = run_capture_smoke()
    elicit_checks = run_elicitation_smoke()

    overall_pass = bool(capture_checks["pass"] and elicit_checks["pass"])
    marker = {
        "pass": overall_pass,
        "capture_smoke": capture_checks,
        "elicitation_smoke": {k: v for k, v in elicit_checks.items() if k != "parse_examples"},
    }
    common.write_json(PREFLIGHT_DIR / "PASS.json", marker)
    print(json.dumps({"capture_smoke_pass": capture_checks["pass"], "elicitation_smoke_pass": elicit_checks["pass"], "overall_pass": overall_pass}, indent=2), flush=True)
    print(json.dumps(capture_checks, indent=2), flush=True)
    print(json.dumps({k: v for k, v in elicit_checks.items() if k != "parse_examples"}, indent=2), flush=True)
    for p in elicit_checks["parse_examples"][:3]:
        print(f"  sample: {p}", flush=True)

    if not overall_pass:
        raise SystemExit(f"preflight FAILED: capture_pass={capture_checks['pass']} elicitation_pass={elicit_checks['pass']}; PASS marker written with pass=False, full runs remain blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
