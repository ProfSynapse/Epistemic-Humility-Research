"""Write synthetic ``mechinterp-capture/v2`` directories (as the engine would) for tests."""

import hashlib
import json
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe_key(key: str) -> str:
    import re

    if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", key):
        return key
    return "row-" + hashlib.sha256(key.encode()).hexdigest()


def write_capture(directory: Path, rows: list[dict], residual_fn, site_fn=None, *, hidden_state=20, blocks=(20, 21, 22),
                  complete=True) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for row in rows:
        key, name = row["row_key"], safe_key(row["row_key"])
        res = directory / f"{name}__anchor.safetensors"
        save_file({f"L{hidden_state}": residual_fn(row).astype(np.float32)[None, :]}, str(res))
        rec = {"row_key": key, "prompt_len": 10, "seq_total": 10, "content_end": 9, "answered": True, "answer_text": "",
               "capture_files": {"anchor": {"file": res.name, "sha256": _sha(res)}}, "hidden_dim": 2560, "n_hidden_states": 33,
               "captured_families": ["anchor"]}
        if site_fn is not None:
            sp = directory / f"{name}__anchor.sites.safetensors"
            save_file({f"L{b}.mlp.down_proj.input": site_fn(row, b).astype(np.float32)[None, :] for b in blocks}, str(sp))
            rec["site_captures"] = {"anchor": {"file": sp.name, "sha256": _sha(sp), "positions": [9]}}
        records.append(rec)
    manifest = {"schema_version": "mechinterp-capture/v2", "complete": complete, "n_rows": len(rows), "n_answered": len(rows),
                "forward_only": True, "rows": records}
    (directory / "manifest.json").write_text(json.dumps(manifest))
    return manifest
