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


def shallow_ladder_hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    """The DESCRIPTIVE shallow ladder (arms D1-D4), registered in gates.yaml
    `descriptive_shallow_ladder` and cell.yaml `arms`.

    Deliberately a SEPARATE key from midband_candidates_hs rather than an
    extension of it. Two reasons, both load-bearing:

    1. These sites are not midband. gemma4-e4b's shallow ladder sits at relative
       depth 0.357-0.548; "midband" for this family means 0.810-1.000. Folding
       them into midband_candidates_hs would mislabel them at every call site.
    2. midband_candidates_hs has other consumers (hs_indices(), the A-arms, the
       parent's profile stage). Extending it would silently change the site set
       those consumers sweep, which is exactly the kind of quiet scope change a
       pre-registration is supposed to prevent.

    Site sets are resolved from config, never from the command line, so the
    registered ladder is hash-pinned at `bin/exp sign` along with the rest of
    families/<family>.yaml.
    """
    values = family_cfg.get("band_selection", {}).get("shallow_ladder_hs")
    if not values:
        raise ValueError(
            f"{family_cfg.get('family')}: shallow_ladder_hs not present in "
            "band_selection -- this family has no registered shallow ladder. "
            "Only gemma4-e4b defines one (experiments/"
            "gemma4-e4b-kv-seam-quarantine/gates.yaml descriptive_shallow_ladder)."
        )
    return list(values)


def seam_pair_hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    """The two sites straddling the KV donor seam: A3 (hs22) and A5 (hs24).

    Added 2026-07-25, after G0-ALIN Part 1 resolved A3 to hs22 and A5 to hs24
    (AMENDMENT.md "Part 1 RESULT"). Before this, both arms named sites that NO
    site set contained, so `build_directions.py` / `gate_fit.py` /
    `calibrate_dose.py` -- all of which select sites through `--site-set` --
    could not address them at all. The two arms carrying this experiment's
    registered non-gating expectation had no path to a direction, a tau or a
    dose. Found by the 2026-07-25 smoke run; see NOTEBOOK.md.

    ONE set covering BOTH sites, deliberately, rather than one set per arm.
    A3-vs-A5 is a contrast, and it is read as one: any difference in HOW the
    two directions or thresholds were fit lands squarely on the comparison the
    experiment is registered to make. A single invocation of each fitting stage
    over both sites makes "identical code path" structural rather than something
    to be checked afterwards.

    Deliberately NOT an extension of shallow_ladder_hs, for the same two reasons
    that key gives for not extending midband_candidates_hs, plus one specific to
    this pair: shallow_ladder's registered story is the donor-REACHABLE band
    (gates.yaml `descriptive_shallow_ladder`), and hs24 is the quarantined site.
    Folding it in would put a site inside a set whose definition excludes it,
    and would make D1-D4's already-committed roll-ups stale.
    """
    values = family_cfg.get("band_selection", {}).get("seam_pair_hs")
    if not values:
        raise ValueError(
            f"{family_cfg.get('family')}: seam_pair_hs not present in "
            "band_selection -- the A3/A5 sites are resolved by G0-ALIN Part 1 "
            "and must be registered in families/<family>.yaml before the arms "
            "can be fit. Only gemma4-e4b defines this pair."
        )
    return list(values)


def pocket_hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    """The pocket ladder: E1 (hs25), E2 (hs26), E3 (hs27), registered for
    gemma4-e4b-pocket-ladder's own arms table.

    Sites are FIXED by registration (rd 0.595/0.619/0.643, the top of the
    cross-family operating range rd 0.375-0.639), not selected by any
    site-property measurement -- there is no A_lin resolution step for this
    set the way there is for seam_pair. All three sites are quarantined by the
    same donor-reachability construction as seam_pair's hs24 and midband's
    hs34/hs38/hs42: none of them is donor-reachable.

    Deliberately NOT an extension of seam_pair_hs or shallow_ladder_hs, for the
    same reasons those two keys give for not extending each other: each site
    set has its own registered story (seam_pair is a fixed A3/A5 contrast pair,
    shallow_ladder is the donor-reachable band) and folding a new band into an
    existing key would silently change what its existing consumers sweep.
    """
    values = family_cfg.get("band_selection", {}).get("pocket_hs")
    if not values:
        raise ValueError(
            f"{family_cfg.get('family')}: pocket_hs not present in "
            "band_selection -- the E1/E2/E3 sites are fixed by registration "
            "and must be listed in families/<family>.yaml before the arms can "
            "be fit. Only gemma4-e4b defines this ladder."
        )
    return list(values)


#: Named site sets selectable with `--site-set`. Adding a set here is an
#: instrument change and must be registered in gates.yaml before it is run.
SITE_SETS: dict[str, Any] = {
    "midband": midband_hs_indices,
    "shallow_ladder": shallow_ladder_hs_indices,
    "seam_pair": seam_pair_hs_indices,
    "pocket": pocket_hs_indices,
}


#: The site set whose artifacts keep the historical un-suffixed filenames.
DEFAULT_SITE_SET = "midband"


def site_set_artifact(name: str, site_set: str) -> str:
    """Filename for a per-site-set roll-up artifact.

    The three roll-ups (build_manifest_layers, gate_fit_layers,
    dose_calibration_summary) are written to ONE path per family. Without
    scoping, running a second site set would overwrite the first's file with a
    report containing only the second's layers -- silently destroying the
    A-arms' frozen directions/gates rather than merging with them.

    `midband` keeps the historical un-suffixed names byte-for-byte, so every
    already-committed artifact and every existing caller is untouched. Any
    other site set gets `<stem>.<site_set>.<ext>`.
    """
    if site_set == DEFAULT_SITE_SET:
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        return f"{name}.{site_set}"
    return f"{stem}.{site_set}.{ext}"


def resolve_site_set(family_cfg: dict[str, Any], name: str) -> list[int]:
    """Resolve a named site set for this family. Raises on an unknown name
    rather than falling back, so a typo can never silently sweep the wrong
    band."""
    try:
        resolver = SITE_SETS[name]
    except KeyError:
        raise ValueError(
            f"unknown --site-set {name!r}; registered sets are "
            f"{sorted(SITE_SETS)}"
        ) from None
    return resolver(family_cfg)


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


# Full set of doubt-snap artifacts a REUSED-POOL family consumes + integrity-
# checks (pool/split manifests AND the frozen late-site direction/gate).
_ALL_REUSE_ARTIFACTS = (
    "split_manifest", "build_manifest", "c_hat", "u_d",
    "random_direction", "gate_fit", "dose_fit", "g0_prep_summary",
)
# The frozen late-site OPERATING POINT only: direction (c_hat/u_d), its build
# standardization (build_manifest: mu_d/sigma_d/mu_c/sigma_c), the random-
# direction control, and the frozen gate (gate_fit: tau). A fresh-mine family
# consumes ONLY these; it mines its own pool/split (qwen35-4b-midband-heldout
# frozen-direction-on-fresh-rows pattern).
_LATE_SITE_ARTIFACTS = ("build_manifest", "c_hat", "u_d", "random_direction", "gate_fit")


def pool_provenance(family_cfg: dict[str, Any]) -> str:
    """How this family obtains its eval pool + FIT/HELD-OUT split. Default
    'reused' (materialize_reused_rows.py copies the doubt-snap split verbatim).
    'fresh_mine' (gemma4-e4b, lead-authorized 2026-07-23): the doubt-snap row
    text is absent from the Modal volume, so the pool/split are mined fresh here
    (mine_eval_pool.py + split_fit_heldout.py) on this family's own checkpoint;
    reuse provenance for the pool is LOST. The frozen late-site direction/gate
    are still reused verbatim regardless (see integrity_artifact_names)."""
    rb = reuse_block(family_cfg)
    return (rb or {}).get("pool_provenance", "reused")


def is_fresh_mine(family_cfg: dict[str, Any]) -> bool:
    return pool_provenance(family_cfg) == "fresh_mine"


def integrity_artifact_names(family_cfg: dict[str, Any]) -> tuple[str, ...]:
    """Which pinned reuse artifacts G0 hash-verifies for this family. Reused-pool
    families verify the pool/split manifests AND the frozen late-site
    direction/gate. Fresh-mine families (gemma) verify ONLY the frozen late-site
    direction/gate they actually consume -- they mine their own pool/split, so
    the doubt-snap pool manifests are neither consumed nor integrity-checked."""
    if is_fresh_mine(family_cfg):
        return _LATE_SITE_ARTIFACTS
    return _ALL_REUSE_ARTIFACTS


def hs_indices(family_cfg: dict[str, Any]) -> list[int]:
    """Full candidate layer set for this family: midband candidates plus the
    late reference, in the same order convention as the predecessor's
    HS_INDICES (midband first, late reference last)."""
    return midband_hs_indices(family_cfg) + [late_reference_hs(family_cfg)]
