"""Fresh unpatched sensor read from hs20 anchor captures (frozen rule)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .capture import check_rows_covered, load_manifest, read_row
from .config import Cell
from .util import HarnessError, read_json


def load_direction_vector(path: Path, expected_sha: str | None = None, *, hidden_dim: int) -> np.ndarray:
    from .util import sha256_file

    if expected_sha is not None and sha256_file(path) != expected_sha:
        raise HarnessError("DIRECTION_HASH", f"{Path(path).name} differs from its promoted hash")
    doc = read_json(path)
    if doc.get("schema_version") != "mechinterp-direction/v1":
        raise HarnessError("DIRECTION_SCHEMA", f"{Path(path).name} is not mechinterp-direction/v1")
    vec = np.asarray(doc["vector"], dtype=np.float64)
    if vec.shape != (hidden_dim,):
        raise HarnessError("DIRECTION_SHAPE", f"{Path(path).name} has shape {vec.shape}")
    if abs(float(np.linalg.norm(vec)) - 1.0) > 1e-6:
        raise HarnessError("DIRECTION_NORM", f"{Path(path).name} is not unit norm")
    return vec


def direction_layer_report(path: Path) -> dict:
    """Report the JSON's layer field; here it is a DECODER BLOCK index even though
    the directory says hs20 (hidden-state index 20 = block 19 output)."""
    doc = read_json(path)
    return {"json_layer": doc.get("layer"), "convention": "decoder_block",
            "hs_index_in_provenance": doc.get("provenance", {}).get("hs_index")}


def fire_decisions(cell: Cell, capture_dir: Path, rows: list[dict], u_d: np.ndarray) -> list[dict]:
    """One decision per registered row from the fresh capture; fails closed on any gap."""
    manifest = load_manifest(capture_dir)
    check_rows_covered(manifest, [r["row_key"] for r in rows])
    record = {r["row_key"]: r for r in manifest["rows"]}
    hs = int(cell.cell["sensor"]["hidden_state"])
    out = []
    for row in rows:
        data = read_row(capture_dir, record[row["row_key"]], hidden_state=hs, sites=[])
        out.append({"row_key": row["row_key"], "role": row["role"],
                    **cell.fire(float(data["residual"] @ u_d))})
    return out
