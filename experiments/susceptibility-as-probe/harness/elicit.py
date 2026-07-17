#!/usr/bin/env python3
"""SC2 elicitation: one greedy verbalized-confidence pass per row for
susceptibility-as-probe (M2).

GPU. Renders each row via `render_confidence.py` (baseline system prompt +
question + the registered CONFIDENCE-first-line suffix, Decision record item
2), invokes synaptic-tuner's `batch-generate` (engine hf-batched, greedy
i.e. `do_sample=False`, resume-safe), and parses the completion per the
registered rule: first regex match of `CONFIDENCE` followed by an integer
within the first two output lines; values above 100 are invalid
(unparseable). No max_new_tokens value is registered in cell.yaml for this
channel (only "one greedy pass per row" is specified); this harness uses 64
new tokens as an implementation choice -- generously long enough to contain
the mandated first-line CONFIDENCE marker plus the start of an answer, but
not itself a locked spec value. Flagged as such in the run report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import population as population_mod  # noqa: E402

REPO_ROOT = config.REPO_ROOT
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"

ELICIT_MAX_NEW_TOKENS = 64  # implementation choice; NOT a registered constant (see module docstring)

_CONFIDENCE_RE = re.compile(r"CONFIDENCE\s+(\d+)")


def parse_confidence(completion_text: str) -> tuple[Optional[int], str]:
    """Returns (value_or_None, reason). Registered parse rule: first regex
    match of CONFIDENCE followed by an integer within the first two output
    lines; values above 100 invalid."""
    lines = (completion_text or "").split("\n")
    scope = "\n".join(lines[: config.CONFIDENCE_PARSE_LINES])
    m = _CONFIDENCE_RE.search(scope)
    if not m:
        return None, "no_regex_match_in_first_two_lines"
    value = int(m.group(1))
    if value > config.CONFIDENCE_MAX_VALID:
        return None, f"value_above_100 ({value})"
    return value, "ok"


def _sh(cmd: list[str]) -> None:
    print(f"[m2-elicit] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def render_rows(rows: list[dict[str, Any]]) -> str:
    os.environ["M2_ELICIT_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M2_ELICIT_RENDER_REVISION"] = config.MODEL_REVISION
    import render_confidence  # noqa: E402

    prompt_rows: list[dict[str, Any]] = []
    for row in rows:
        prompt = render_confidence.render(row)
        prompt_rows.append({"id": row["row_key"], "prompt": prompt, "role": row["role"]})
    template_sha256 = common.sha256_of_bytes(
        (render_confidence.BASELINE_SYSTEM_PROMPT + "\n" + render_confidence.CONFIDENCE_TEMPLATE_USER_SUFFIX).encode("utf-8")
    )
    return prompt_rows, template_sha256


def run_generate(prompt_rows: list[dict[str, Any]], out_dir: Path, batch_size: int) -> None:
    prompts_in = out_dir / "elicit_prompts.jsonl"
    common.write_jsonl(prompts_in, prompt_rows)
    _sh([
        sys.executable, str(TUNER), "batch-generate",
        "--prompts", str(prompts_in),
        "--model", config.MODEL_REPO,
        "--model-revision", config.MODEL_REVISION,
        "--out-dir", str(out_dir / "generate"),
        "--engine", config.READOUT_ENGINE,
        "--max-new-tokens", str(ELICIT_MAX_NEW_TOKENS),
        "--batch-size", str(batch_size),
        "--resume",
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--rows", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=config.READOUT_BATCH_SIZE)
    args = ap.parse_args()

    hashes = config.verify_pinned_hashes()
    if not all(hashes.values()):
        raise SystemExit(f"elicit FAIL: cell.yaml/gates.yaml sha256 mismatch: {hashes}")

    if args.rows is None:
        marker_path = config.EXPERIMENT_DIR / config.PREFLIGHT_PASS_MARKER
        if not marker_path.is_file():
            raise SystemExit(
                f"elicit FAIL: full elicitation pass requested (--rows omitted) but "
                f"no preflight PASS marker at {marker_path}; run preflight.py first "
                f"(Decision record item 7 / SC1 mandatory GPU preflight)."
            )
        marker = common.load_json(marker_path)
        if not marker.get("pass"):
            raise SystemExit(f"elicit FAIL: preflight PASS marker at {marker_path} records pass=False; refusing full run: {marker}")

    rows = population_mod.build_population()
    if args.rows is not None:
        rows = rows[: args.rows]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_rows, template_sha256 = render_rows(rows)
    run_generate(prompt_rows, out_dir, args.batch_size)

    completions = common.load_jsonl(out_dir / "generate" / "completions.jsonl")
    completions_by_id = {c["id"]: c for c in completions}

    expected_ids = {r["id"] for r in prompt_rows}
    captured_ids = set(completions_by_id.keys())
    missing = sorted(expected_ids - captured_ids)

    role_by_key = {r["row_key"]: r["role"] for r in rows}
    scored_rows: list[dict[str, Any]] = []
    n_parsed = 0
    for row_key in sorted(expected_ids):
        comp = completions_by_id.get(row_key)
        if comp is None:
            scored_rows.append({"row_key": row_key, "role": role_by_key[row_key], "confidence": None, "parse_reason": "missing_completion"})
            continue
        value, reason = parse_confidence(comp["completion_text"])
        if value is not None:
            n_parsed += 1
        scored_rows.append({
            "row_key": row_key, "role": role_by_key[row_key], "confidence": value,
            "parse_reason": reason, "finish_reason": comp.get("finish_reason"),
        })
    common.write_jsonl(out_dir / "confidence_scores.jsonl", scored_rows)

    parse_rate = n_parsed / len(expected_ids) if expected_ids else 0.0
    manifest = {
        "model": config.MODEL_REPO, "revision": config.MODEL_REVISION,
        "engine": config.READOUT_ENGINE, "do_sample": False, "decode": "greedy",
        "max_new_tokens": ELICIT_MAX_NEW_TOKENS,
        "max_new_tokens_is_registered_constant": False,
        "batch_size": args.batch_size,
        "template_sha256": template_sha256,
        "template_user_suffix": config.CONFIDENCE_TEMPLATE_USER_SUFFIX,
        "parse_rule": "first regex match of CONFIDENCE followed by an integer within the first two output lines; values above 100 invalid",
        "n_rows_requested": len(expected_ids),
        "n_completions_captured": len(captured_ids),
        "n_missing_completions": len(missing), "missing_sample": missing[:10],
        "n_parsed": n_parsed, "parse_rate": parse_rate,
        "parse_rate_floor": config.SC2_CONFIDENCE_PARSE_RATE_FLOOR,
        "parse_rate_pass": parse_rate >= config.SC2_CONFIDENCE_PARSE_RATE_FLOOR,
    }
    common.write_json(out_dir / "elicitation_manifest.json", manifest)
    print(json.dumps(manifest, indent=2), flush=True)

    if missing:
        raise SystemExit(f"elicit FAIL: {len(missing)} rows missing a completion (zero-silent-drops violated): {missing[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
