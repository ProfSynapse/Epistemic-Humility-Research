#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier): label-path vs extraction-path render identity.

Compares check_vllm.json (EH render through vLLM's tokenizer, vLLM's own
prompt_token_ids) with check_runner_render.json (Stage 0 extraction render in
the runner image, tokenizer(prompt) ids) row by row: prompt bytes (sha256) and
prompt token ids must be identical on all 20 smoke rows.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    a = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    b = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    ra, rb = {r["i"]: r for r in a["rows"]}, {r["i"]: r for r in b["rows"]}
    bytes_diff = [i for i in ra if ra[i]["prompt_sha256"] != rb[i]["prompt_sha256"]]
    ids_diff = [i for i in ra if ra[i]["prompt_token_ids"] != rb[i]["prompt_token_ids"]]
    res = {"check": "render_identity", "n_rows": len(ra), "same_row_set": set(ra) == set(rb),
           "prompt_bytes_mismatch_rows": bytes_diff, "prompt_token_id_mismatch_rows": ids_diff,
           "label_side": {"vllm": a.get("vllm_version")}, "extract_side": {"transformers": b.get("transformers")},
           "pass": set(ra) == set(rb) and not bytes_diff and not ids_diff}
    Path(sys.argv[3]).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
