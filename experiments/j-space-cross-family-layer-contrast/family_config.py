"""Family config loader for the cross-family J-space layer contrast.

Each family's checkpoint, loader hardening, render/EOS contract, band
selection, dose calibration, and G3 floor live in one YAML file under
`families/`. Every other script in this experiment reads a family only
through this module -- no other script hardcodes a checkpoint string,
hidden_size, or layer index.

Band selection and dose calibration fields start as `null`/"not_yet_run" in
each family YAML (this is a DRAFT scaffold; no GPU work has run yet). The
profile/fit/calibrate stages are expected to REWRITE the family YAML in
place with their results before the next stage reads it -- this module's
`load_family` / `save_family` pair is the single read/write path so that
in-place update is auditable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
FAMILIES_DIR = HERE / "families"
# experiments/<slug>/ -> repo root, for resolving reuse.committed_dir which is
# recorded repo-relative (experiments/doubt-snap-.../analysis-committed/<cell>).
REPO_ROOT = HERE.parent.parent

FAMILY_SLUGS = ["llama-3.2-3b", "mistral-7b-v03", "qwen35-4b", "gemma4-e4b"]

# Amendment Z's risk order (lowest risk first): mirrors
# experiment/protocol/AMENDMENT-Z-cross-family-confirmatory.md "Run order".
RUN_ORDER = ["llama-3.2-3b", "mistral-7b-v03", "qwen35-4b", "gemma4-e4b"]


def family_config_path(family: str) -> Path:
    if family not in FAMILY_SLUGS:
        raise ValueError(f"unknown family {family!r}; expected one of {FAMILY_SLUGS}")
    return FAMILIES_DIR / f"{family}.yaml"


def load_family(family: str) -> dict[str, Any]:
    path = family_config_path(family)
    if not path.is_file():
        raise FileNotFoundError(f"family config not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data.get("family") != family:
        raise ValueError(
            f"{path}: family field {data.get('family')!r} does not match "
            f"requested family {family!r}"
        )
    return data


def save_family(family: str, data: dict[str, Any]) -> None:
    """Rewrite a family's YAML in place. Callers must load_family() first and
    mutate the returned dict rather than constructing a new one, so unrelated
    fields survive untouched."""
    path = family_config_path(family)
    if data.get("family") != family:
        raise ValueError(f"refusing to write {path} with family field {data.get('family')!r}")
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=88), encoding="utf-8")


def all_families_in_run_order() -> list[dict[str, Any]]:
    return [load_family(f) for f in RUN_ORDER]


def hs_to_block(hs_index: int) -> int:
    """HF hidden_states index -> 0-indexed decoder block, for direction JSON
    provenance. Identical convention across every family: HF's own
    output_hidden_states tuple always has index 0 = embeddings, index i =
    block i's output, for i in [1, num_hidden_layers]."""
    if hs_index < 1:
        raise ValueError(f"hidden_states index must be >=1, got {hs_index}")
    return hs_index - 1


def layer_dir_name(hs_index: int) -> str:
    return f"hs{hs_index}"


def midband_hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    values = family_cfg.get("band_selection", {}).get("midband_candidates_hs")
    if not values:
        raise ValueError(
            f"{family_cfg.get('family')}: midband_candidates_hs not yet resolved -- "
            "run jlens_profile.py for this family before requesting its layer set."
        )
    return list(values)


def late_reference_hs(family_cfg: dict[str, Any]) -> int:
    """The late reference site is DEFINED by the reused doubt-snap frozen late
    site (reuse.doubt_snap.late_site.hs_index = doubt-snap decoder block + 1),
    not re-localized by this experiment's J-lens. Falls back to the legacy
    band_selection.late_reference_hs only if no reuse block is present."""
    ls = late_site(family_cfg)
    if ls and ls.get("hs_index") is not None:
        return int(ls["hs_index"])
    value = family_cfg.get("band_selection", {}).get("late_reference_hs")
    if value is None:
        raise ValueError(
            f"{family_cfg.get('family')}: late_reference_hs not resolved -- no "
            "reuse.doubt_snap.late_site.hs_index and no band_selection fallback."
        )
    return int(value)


# --- reused doubt-snap artifacts (sign-time revision 2026-07-23) --------------

def reuse_block(family_cfg: dict[str, Any]) -> dict[str, Any] | None:
    """The `reuse.doubt_snap` block, or None if this family is not reusing a
    doubt-snap cell (e.g. a fallback-fresh-mine family)."""
    return (family_cfg.get("reuse") or {}).get("doubt_snap")


def late_site(family_cfg: dict[str, Any]) -> dict[str, Any] | None:
    rb = reuse_block(family_cfg)
    return rb.get("late_site") if rb else None


def is_late_reference(family_cfg: dict[str, Any], hs_index: int) -> bool:
    ls = late_site(family_cfg)
    if not ls or ls.get("hs_index") is None:
        return hs_index == family_cfg.get("band_selection", {}).get("late_reference_hs")
    return hs_index == int(ls["hs_index"])


def reuse_committed_dir(family_cfg: dict[str, Any]) -> Path | None:
    rb = reuse_block(family_cfg)
    if not rb or not rb.get("committed_dir"):
        return None
    return (REPO_ROOT / rb["committed_dir"]).resolve()


def reuse_artifact_path(family_cfg: dict[str, Any], name: str) -> Path | None:
    """Absolute path to a pinned reused doubt-snap artifact (e.g. 'c_hat',
    'u_d', 'gate_fit', 'build_manifest', 'split_manifest'), or None if the
    artifact is not recorded (e.g. gemma's absent dose_fit)."""
    rb = reuse_block(family_cfg)
    d = reuse_committed_dir(family_cfg)
    if not rb or d is None:
        return None
    art = (rb.get("artifacts") or {}).get(name)
    if not art or not art.get("path"):
        return None
    return d / art["path"]


def reuse_artifact_sha256(family_cfg: dict[str, Any], name: str) -> str | None:
    rb = reuse_block(family_cfg)
    if not rb:
        return None
    art = (rb.get("artifacts") or {}).get(name)
    return art.get("sha256") if art else None


def hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    """Full candidate layer set for this family: midband candidates plus the
    late reference, in the same order convention as the predecessor's
    HS_INDICES (midband first, late reference last)."""
    return midband_hs_indices(family_cfg) + [late_reference_hs(family_cfg)]
