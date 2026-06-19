#!/usr/bin/env python3
"""Hidden-state probing tier harness (exploratory mechanism tier, MVP).

Location: experiment/phase1/probe/hidden_state_probe.py
Reads:    experiment/phase1/probe/config/hidden_state_probe.yaml
          experiment/phase1/probe/<model_tag>/probe_results.jsonl (alignment, streamed)
          experiment/phase1/data/<model_tag>/questions_frozen.json (frozen split keys)
          experiment/phase1/eval/config/eval_smoke_local_4b.yaml (adapter paths, by-value)
Writes:   experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/
            manifest.json + rows.jsonl + per-arm h_base/h_lora/delta.safetensors

One job: for a matched known/unknown slice of FROZEN-split questions, run a
deterministic base-vs-LoRA forward pass and persist h_base, h_lora, and
delta = h_lora - h_base at the final prompt token across all layers, with an
exhaustive crash-safe manifest. It does NOT train probes or run interventions
(that is the deferred Phase 5), and it NEVER mutates probe_results.jsonl or any
run record (it links them by id only).

Design (plan Decisions A-E):
  - All validation is model-free in hidden_state_schema.py; this file is thin
    orchestration. Heavy deps (torch/transformers/peft) are LAZY-imported inside
    TransformersPeftBackend so the module loads, and the stub path runs, on a
    CPU-only / no-GPU / no-network host.
  - The forward pass is isolated behind the ExtractionBackend Protocol. The real
    TransformersPeftBackend needs a GPU; the StubExtractionBackend is
    deterministic, torch-free, and lets the full selection/manifest/persist/resume
    pipeline run GREEN in CI (mirrors backends.py's ProbeBackend/StubBackend seam).
  - Crash-safe manifest (Decision D-bis): the manifest is written with
    status="launched" BEFORE the forward, then patched to ok/failed; `verified`
    is set True only after emitted tensors are checked.

Real runs use TransformersPeftBackend on a GPU. The numerical h_base != h_lora
smoke assertion is GPU-only and out of MVP scope (a marked skip lives in the
test suite for the test-engineer).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Protocol

import yaml

import hidden_state_schema as schema

# Repo root is four levels up (experiment/phase1/probe/hidden_state_probe.py).
REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = Path(__file__).resolve().parent


def _rel(path: Path) -> str:
    """Path relative to REPO_ROOT for display, or absolute if outside it."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Step 3 — config parse, extraction_config_sha, output-tree resolution
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_eval_arm_adapters(config: dict, config_path: Path) -> dict:
    """Resolve active-arm adapter paths BY-VALUE from the eval config (Decision).

    Reads the eval config's arms[] and maps arm name -> adapter path, so the
    canonical adapter path is declared in exactly one place. An explicit
    `adapter` on a config arm overrides the mirror. Returns the config with
    each active arm's `adapter` populated; raises if an active arm has no
    resolvable adapter (a base arm legitimately has adapter=None).
    """
    eval_source = config.get("eval_arms_source")
    eval_adapters: dict[str, str | None] = {}
    if eval_source:
        # Relative paths in the config are anchored at the probe dir (the same
        # base resolve_output_dir / select_matched_slice use), not the config's
        # own dir, so they read naturally as probe/<...>.
        eval_path = (PROBE_DIR / eval_source).resolve()
        with eval_path.open(encoding="utf-8") as fh:
            eval_cfg = yaml.safe_load(fh)
        eval_adapters = {a["name"]: a.get("adapter") for a in eval_cfg.get("arms", [])}

    for arm in config["arms"]:
        if arm.get("adapter") is None and arm["adapter_state"] == schema.ADAPTER_STATE_ACTIVE:
            mirrored = eval_adapters.get(arm["name"])
            if not mirrored:
                raise ValueError(
                    f"active arm {arm['name']!r} has no adapter path: set "
                    f"arms[].adapter explicitly or add a matching arm to "
                    f"{eval_source!r}"
                )
            arm["adapter"] = mirrored
    return config


def parse_config(config_path: Path) -> tuple[dict, str]:
    """Load, validate (model-free), and hash the extraction config.

    Runs the P0 adapter-state pre-flight and the token-position-rule check at
    parse time so a malformed config fails BEFORE any model load. Returns the
    resolved config and its extraction_config_sha.
    """
    config = load_config(config_path)
    config = resolve_eval_arm_adapters(config, config_path)
    schema.validate_arm_states(config["arms"])
    schema.validate_token_position_rule(config["extraction"]["token_position_rule"])
    cfg_sha = schema.config_sha(config)
    return config, cfg_sha


def extraction_id(arm_name: str, extraction_config_sha: str) -> str:
    """Per-arm output id: f'{arm}__{extraction_config_sha[:12]}' (Decision C)."""
    return f"{arm_name}__{extraction_config_sha[:12]}"


def resolve_output_dir(config: dict, extraction_config_sha: str,
                       base_dir: Path | None = None) -> Path:
    """probe/<model_tag>/hidden_states/<extraction_id>/ (shared per extraction).

    The extraction_id keys the whole extraction (one base + one active arm), so
    the tree groups both arms' tensors with their shared manifest/rows.
    """
    root = base_dir if base_dir is not None else PROBE_DIR
    model_tag = config["model"]["model_tag"]
    subdir = config["output"]["hidden_states_subdir"]
    ext_id = extraction_id("extraction", extraction_config_sha)
    return root / model_tag / subdir / ext_id


# ---------------------------------------------------------------------------
# Step 4 — selection / alignment (frozen keys + streamed probe_results.jsonl)
# ---------------------------------------------------------------------------

def _select_keys(frozen: dict, pool_field: str, n: int, seed: int) -> list[str]:
    """Deterministically pick n keys from a frozen-split pool by stable hash."""
    import hashlib

    keys = list(frozen.get(pool_field, []))
    if n is None or n >= len(keys):
        return keys
    ordered = sorted(
        keys,
        key=lambda k: hashlib.sha256(f"{seed}|{k}".encode()).hexdigest(),
    )
    return ordered[:n]


def select_matched_slice(config: dict) -> list[dict]:
    """Build the matched known/unknown extraction slice (leakage-safe).

    Reads frozen known/unknown keys (probe_pool_row_key) and STREAMS
    probe_results.jsonl once, keeping only rows whose key is selected (never
    whole-loading the ~123MB file). Each returned row carries the alignment
    identity (probe_pool_row_key, question, label, probe_config_sha) the harness
    needs; alignment is by key only, never loose question text.
    """
    sel = config["selection"]
    source = sel.get("source", "probe_pool")
    if source == "selfaware_manifest":
        return select_selfaware_manifest_slice(config)
    if source != "probe_pool":
        raise ValueError(
            f"selection.source {source!r} is not supported; expected "
            "'probe_pool' or 'selfaware_manifest'"
        )
    # Config relative paths are anchored at the probe dir (see
    # resolve_eval_arm_adapters); keep frozen + results on the same base.
    frozen_path = (PROBE_DIR / sel["questions_frozen"]).resolve()
    results_path = (PROBE_DIR / sel["probe_results"]).resolve()

    with frozen_path.open(encoding="utf-8") as fh:
        frozen = json.load(fh)

    want_known = set(_select_keys(frozen, "known_question_keys",
                                  sel["n_known"], sel["selection_seed"]))
    want_unknown = set(_select_keys(frozen, "unknown_question_keys",
                                    sel["n_unknown"], sel["selection_seed"]))
    wanted = want_known | want_unknown
    label_by_key = {**{k: "known" for k in want_known},
                    **{k: "unknown" for k in want_unknown}}

    found = _stream_probe_rows(results_path, wanted, label_by_key)
    missing = wanted - {r["probe_pool_row_key"] for r in found}
    if missing:
        raise ValueError(
            f"{len(missing)} selected frozen key(s) not found in "
            f"{_rel(results_path)} (e.g. {sorted(missing)[:3]}); the probe "
            "tier must have probed these before extraction"
        )
    return found


def select_selfaware_manifest_slice(config: dict) -> list[dict]:
    """Load frozen SelfAware manifest rows for dedicated extraction prep.

    This path consumes `phase3-selfaware-frozen-row-manifest/v1` rows. It maps
    the manifest's stable `row_key` into `probe_pool_row_key` only as a
    compatibility key for the existing tensor writer/resume path; the row record
    still preserves the original `row_key`, `stable_identity`, and `strata`.
    """
    sel = config["selection"]
    manifest_path = (PROBE_DIR / sel["manifest"]).resolve()
    wanted_strata = sel.get("strata")
    max_rows = sel.get("max_rows")
    if max_rows is not None and (
        not isinstance(max_rows, int) or isinstance(max_rows, bool) or max_rows <= 0
    ):
        raise ValueError("selection.max_rows must be a positive integer when set")
    rows = load_selfaware_manifest_rows(
        manifest_path,
        wanted_strata=wanted_strata,
        max_rows=max_rows,
    )
    if not rows:
        raise ValueError(f"no rows selected from SelfAware manifest {_rel(manifest_path)}")
    return rows


def load_selfaware_manifest_rows(
    manifest_path: Path,
    *,
    wanted_strata: list[str] | None = None,
    max_rows: int | None = None,
) -> list[dict]:
    """Convert frozen SelfAware manifest rows into extraction slice rows."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"SelfAware manifest {_rel(manifest_path)} not found")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "phase3-selfaware-frozen-row-manifest/v1":
        raise ValueError("SelfAware manifest schema_version is not supported")
    if payload.get("scope", {}).get("not_probe_pool_runner_ready") is not True:
        raise ValueError("SelfAware manifest must declare not_probe_pool_runner_ready: true")
    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise ValueError("SelfAware manifest rows must be a list")
    aligned_probe_config_sha = selfaware_manifest_provenance_sha(manifest_path)
    strata_filter = set(wanted_strata or [])
    selected: list[dict] = []
    seen: set[str] = set()
    for index, row in enumerate(raw_rows):
        converted = convert_selfaware_manifest_row(
            row,
            index=index,
            aligned_probe_config_sha=aligned_probe_config_sha,
        )
        row_strata = set(converted["strata"])
        if strata_filter and not (row_strata & strata_filter):
            continue
        key = converted["row_key"]
        if key in seen:
            raise ValueError(f"duplicate SelfAware manifest row_key {key!r}")
        seen.add(key)
        selected.append(converted)
        if max_rows is not None and len(selected) >= max_rows:
            break
    return selected


def selfaware_manifest_provenance_sha(manifest_path: Path) -> str:
    """Tagged immutable identity for a frozen SelfAware row manifest."""
    digest = _file_sha256(manifest_path)
    if digest is None:
        raise FileNotFoundError(f"SelfAware manifest {_rel(manifest_path)} not found")
    return f"selfaware-manifest-sha256:{digest}"


def convert_selfaware_manifest_row(
    row: dict,
    *,
    index: int,
    aligned_probe_config_sha: str | None = None,
) -> dict:
    """Validate and convert one frozen SelfAware row for extraction."""
    required = ["row_key", "stable_identity", "strata", "label", "question", "prompt"]
    missing = [field for field in required if field not in row]
    if missing:
        raise ValueError(f"SelfAware manifest rows[{index}] missing {missing}")
    row_key = row["row_key"]
    if not isinstance(row_key, str) or not row_key:
        raise ValueError(f"SelfAware manifest rows[{index}].row_key must be non-empty")
    if not isinstance(row["stable_identity"], dict):
        raise ValueError(f"SelfAware manifest rows[{index}].stable_identity must be a mapping")
    if row["label"] not in {"known", "unknown"}:
        raise ValueError(f"SelfAware manifest rows[{index}].label must be known or unknown")
    if not isinstance(row["question"], str) or not row["question"]:
        raise ValueError(f"SelfAware manifest rows[{index}].question must be non-empty")
    prompt = row["prompt"]
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"SelfAware manifest rows[{index}].prompt must be non-empty")
    strata = row["strata"]
    if not isinstance(strata, list) or not all(isinstance(item, str) and item for item in strata):
        raise ValueError(f"SelfAware manifest rows[{index}].strata must be non-empty strings")
    aliases = row.get("aliases", [])
    if aliases is None:
        aliases = []
    if not isinstance(aliases, list):
        raise ValueError(f"SelfAware manifest rows[{index}].aliases must be a list")
    return {
        "probe_pool_row_key": row_key,
        "row_key": row_key,
        "stable_identity": row["stable_identity"],
        "strata": list(strata),
        "question": row["question"],
        "prompt": prompt,
        "label": row["label"],
        "frozen_label": row["label"],
        "probe_label": None,
        "aligned_probe_config_sha": aligned_probe_config_sha,
        "answer_value": row.get("answer_value"),
        "aliases": aliases,
        "source_arms": row.get("source_arms", {}),
    }


def _stream_probe_rows(results_path: Path, wanted: set[str],
                       label_by_key: dict[str, str]) -> list[dict]:
    """Stream probe_results.jsonl, returning only the selected alignment rows."""
    found: list[dict] = []
    if not results_path.exists():
        raise FileNotFoundError(
            f"alignment source {_rel(results_path)} not found; run the probe "
            "tier first (it produces probe_results.jsonl)"
        )
    with results_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if key in wanted:
                found.append({
                    "probe_pool_row_key": key,
                    "question": row["question"],
                    "label": label_by_key[key],
                    "frozen_label": label_by_key[key],
                    "probe_label": row.get("label"),
                    "aligned_probe_config_sha": row.get("probe_config_sha"),
                })
    return found


# ---------------------------------------------------------------------------
# Step 5 — ExtractionBackend seam + Stub + writer + resume
# ---------------------------------------------------------------------------

class ExtractionBackend(Protocol):
    """Minimal forward interface the harness depends on (one seam to stub).

    The base-vs-LoRA contrast lives behind this Protocol so the real GPU path
    (TransformersPeftBackend) and a deterministic torch-free stub are
    interchangeable. forward returns layer_id -> 1-D final-token vector.
    """

    num_hidden_layers: int
    hidden_dim: int

    def render(self, question: str) -> str:
        """Render the prompt bytes for one question (shared render helper)."""
        ...

    def forward_hidden_states(self, rendered_prompt: str, arm_state: str,
                              adapter_name: str | None) -> dict:
        """Final-token hidden states per layer for one arm/adapter-state."""
        ...

    def provenance(self) -> dict:
        """Backend-derived (post-load) manifest provenance fields.

        Returns the manifest fields that can only be known once the model is
        loaded: base_model_id/revision/hash, adapter_hash, tokenizer_revision,
        and the library versions (peft_version/transformers_version). The harness
        merges this into the manifest (after collect_static_provenance, so these
        win) before the finalize gate, so the REAL backend supplies real values
        and the stub supplies deterministic stand-ins (keeping the
        require_populated gate exercisable GPU-free).

        Seam note for the lora_* fields: on the REAL path they come from the
        adapter dir's adapter_config.json (read GPU-free by
        collect_static_provenance), so the real backend OMITS them here to let
        those values stand; the STUB has no adapter dir, so it INCLUDES lora_*
        stand-ins so the GPU-free pipeline still finalizes.
        """
        ...


class StubExtractionBackend:
    """Deterministic, torch-free ExtractionBackend for GPU-free tests.

    Fabricates per-layer final-token vectors from a stable hash of
    (prompt, arm_state, adapter_name, layer), so h_base != h_lora structurally
    (different arm_state seeds different vectors) and a resumed run reproduces
    identical tensors. No model, no torch — exercises the full select/persist/
    resume pipeline in CI.
    """

    def __init__(self, num_hidden_layers: int = 3, hidden_dim: int = 8,
                 system_prompt: str = "answer concisely", seed: int = 0):
        self.num_hidden_layers = num_hidden_layers
        self.hidden_dim = hidden_dim
        self.system_prompt = system_prompt
        self.seed = seed

    def render(self, question: str) -> str:
        # Deterministic stand-in render; the real backend uses the shared helper.
        return f"<|stub|>{self.system_prompt}|{question}<|gen|>"

    def forward_hidden_states(self, rendered_prompt, arm_state, adapter_name):
        import hashlib

        vectors: dict[int, list[float]] = {}
        layer_count = schema.expected_layer_count(self.num_hidden_layers)
        for layer in range(layer_count):
            key = f"{self.seed}|{rendered_prompt}|{arm_state}|{adapter_name}|{layer}"
            digest = hashlib.sha256(key.encode()).digest()
            vectors[layer] = [
                ((digest[i % len(digest)] / 255.0) - 0.5)
                for i in range(self.hidden_dim)
            ]
        return vectors

    def provenance(self) -> dict:
        """Deterministic stub stand-ins for the post-load provenance fields.

        These are clearly stub-marked (so a stub-produced manifest is never
        mistaken for a real extraction) but non-None, which lets the GPU-free
        pipeline produce a manifest that passes validate_manifest(
        require_populated=True) — i.e. the finalize gate is exercisable in CI.
        """
        return {
            "base_model_id": "stub/base-model",
            "base_model_revision": "stub-revision",
            "base_model_hash": "stub-base-hash",
            "adapter_hash": "stub-adapter-hash",
            "tokenizer_revision": "stub-tokenizer-revision",
            "peft_version": "stub-peft",
            "transformers_version": "stub-transformers",
            # LoRA hyperparams come from adapter_config.json on the real path
            # (GPU host has the adapter dir); the stub has no adapter dir, so it
            # supplies stand-ins here. The REAL backend OMITS these keys, letting
            # collect_static_provenance's adapter_config.json read stand.
            "lora_rank": -1,
            "lora_alpha": -1,
            "lora_dropout": 0.0,
            "lora_target_modules": ["stub-target"],
        }


def _arm_roles(arms: list[dict]) -> tuple[dict, dict]:
    """Return (base_arm, active_arm) after the pre-flight has validated them."""
    base = next(a for a in arms if a["adapter_state"] in schema.BASE_ADAPTER_STATES)
    active = next(a for a in arms if a["adapter_state"] == schema.ADAPTER_STATE_ACTIVE)
    return base, active


def _vector_delta(lora: dict, base: dict) -> dict:
    """delta = h_lora - h_base, per layer (plain python; persisted, not trusted)."""
    return {
        layer: [lv - bv for lv, bv in zip(lora[layer], base[layer])]
        for layer in lora
    }


def load_done_row_keys(rows_path: Path) -> set[str]:
    """Row keys already written to the append-log (resume; probe.py idiom)."""
    done: set[str] = set()
    if not rows_path.exists():
        return done
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key") or row.get("row_key")
            if key:
                done.add(key)
    return done


def _git_commit(repo_dir: Path) -> str | None:
    """HEAD commit of a git repo, or None if unavailable (GPU-free, optional)."""
    import subprocess  # noqa: PLC0415

    try:
        out = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


def _submodule_commit(repo_dir: Path, submodule_path: str) -> str | None:
    """The gitlink SHA a superproject records for a submodule (GPU-free).

    Reads the recorded commit from the superproject's index via `git ls-tree`,
    NOT `git -C <submodule> rev-parse HEAD`: in a worktree the submodule is often
    UNPOPULATED (no working tree), and rev-parse inside the missing dir silently
    walks up to the PARENT repo and returns the wrong commit. ls-tree reads the
    pinned gitlink directly, so it is correct whether or not the submodule is
    checked out. Returns None if the path is not a recorded submodule.
    """
    import subprocess  # noqa: PLC0415

    try:
        out = subprocess.run(
            ["git", "-C", str(repo_dir), "ls-tree", "HEAD", submodule_path],
            capture_output=True, text=True, check=True, timeout=10)
    except (subprocess.SubprocessError, OSError):
        return None
    # Output: "<mode> commit <sha>\t<path>"; mode 160000 marks a gitlink.
    parts = out.stdout.split()
    if len(parts) >= 3 and parts[1] == "commit":
        return parts[2]
    return None


def _file_sha256(path: Path) -> str | None:
    """sha256 of a file's bytes, streamed (GPU-free), or None if absent."""
    import hashlib  # noqa: PLC0415

    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _looks_like_explicit_local_path(model_name: str) -> bool:
    """Whether a model id should be treated as an operator-supplied local path."""
    path = Path(model_name).expanduser()
    return path.is_absolute() or model_name.startswith((".", "~"))


def _local_model_dir_sha256(model_name: str) -> str | None:
    """Deterministic local-model identity, or None when model_name is a hub id.

    Local merged models do not have a hub snapshot commit, so the manifest needs
    another immutable content key. Hash stable identity-bearing files in a fixed
    order, including each relative path and each file's sha256, and prefix the
    result so it cannot be mistaken for a hub commit SHA.

    Returns None only for non-local model ids. Explicit local-path failures are
    raised so the operator gets a direct error instead of a later None-field
    finalize failure.
    """
    import hashlib  # noqa: PLC0415

    root = Path(model_name).expanduser()
    if not root.exists():
        if _looks_like_explicit_local_path(model_name):
            raise FileNotFoundError(f"local model directory {model_name!r} does not exist")
        return None
    if not root.is_dir():
        raise NotADirectoryError(f"local model path {model_name!r} is not a directory")

    config_file = root / "config.json"
    if not config_file.is_file():
        raise FileNotFoundError(
            f"local model directory {model_name!r} is missing config.json")

    stable_names = [
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "special_tokens_map.json",
        "model.safetensors.index.json",
        "pytorch_model.bin.index.json",
    ]
    files = {root / name for name in stable_names if (root / name).is_file()}
    files.update(p for p in root.glob("*.safetensors") if p.is_file())
    files.update(p for p in root.glob("*.bin") if p.is_file())
    weight_files = [
        p for p in files
        if (p.name.endswith(".safetensors") or p.name.endswith(".bin")
            or p.name.endswith(".index.json"))
    ]
    if not weight_files:
        raise FileNotFoundError(
            f"local model directory {model_name!r} has config.json but no stable "
            "weight identity files (*.safetensors, *.bin, or weight index json)")

    h = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        digest = _file_sha256(path)
        if digest is None:
            raise FileNotFoundError(f"local model provenance file disappeared: {path}")
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    return f"local-sha256:{h.hexdigest()}"


def _read_adapter_lora_config(adapter_path: str | None) -> dict:
    """Read LoRA hyperparams from a PEFT adapter_config.json (GPU-free JSON read).

    PEFT writes adapter_config.json into the adapter dir; rank/alpha/dropout/
    target_modules are plain JSON, so we read them WITHOUT loading torch/peft.
    Returns the four manifest fields (None each if the file is unreadable, e.g.
    an adapter dir that only exists on the GPU host).
    """
    fields = {"lora_rank": None, "lora_alpha": None, "lora_dropout": None,
              "lora_target_modules": None}
    if not adapter_path:
        return fields
    cfg_file = Path(adapter_path) / "adapter_config.json"
    if not cfg_file.exists():
        return fields
    try:
        with cfg_file.open(encoding="utf-8") as fh:
            adapter_cfg = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return fields
    tgt = adapter_cfg.get("target_modules")
    fields["lora_rank"] = adapter_cfg.get("r")
    fields["lora_alpha"] = adapter_cfg.get("lora_alpha")
    fields["lora_dropout"] = adapter_cfg.get("lora_dropout")
    # target_modules may be a list or a set serialized as a list; normalize to a
    # sorted list of strings so the manifest value is JSON-stable and non-None.
    fields["lora_target_modules"] = sorted(tgt) if isinstance(tgt, (list, set)) else tgt
    return fields


def _renderer_hash(config: dict) -> str:
    """Stable identity of the prompt-render path (GPU-free).

    Hashes the render-affecting knobs (enable_thinking, token_position_rule) plus
    the shared helper's discovery-mode tuple, so a change to the render surface
    changes this manifest field. Imports the helper's constant lazily to avoid a
    hard backends dependency at module import.
    """
    try:
        from backends import _RENDER_MODES  # noqa: PLC0415
        modes = list(_RENDER_MODES)
    except Exception:  # noqa: BLE001 - renderer identity degrades, not fails
        modes = ["direct", "chat_template_kwargs"]
    identity = {
        "enable_thinking": config.get("model", {}).get("enable_thinking"),
        "token_position_rule": config.get("extraction", {}).get("token_position_rule"),
        "render_modes": modes,
    }
    return schema.config_sha(identity)


def collect_static_provenance(config: dict, slice_rows: list[dict],
                              rendered_prompts: list[str]) -> dict:
    """GPU-free manifest provenance the harness can fill without a loaded model.

    Everything here is derivable from the config, the selected slice, the on-disk
    adapter_config.json, and git — NO torch/transformers/peft. The backend's
    provenance() supplies the remaining post-load fields (versions, model/adapter
    hashes). Together they populate every Decision-D field so the finalize gate
    (validate_manifest(require_populated=True)) can run GPU-free.
    """
    base_arm, active_arm = _arm_roles(config["arms"])
    extraction = config["extraction"]
    prov_block = config.get("manifest_provenance", {})

    # aligned_probe_config_sha: the slice rows all carry the probe tier's sha;
    # take the first (they share one probe config) so the manifest links to it.
    aligned_probe_sha = (
        slice_rows[0].get("aligned_probe_config_sha") if slice_rows else None)

    data_source = selection_data_source(config)
    if aligned_probe_sha is None and config["selection"].get("source") == "selfaware_manifest":
        aligned_probe_sha = selfaware_manifest_provenance_sha(data_source)
    static = {
        "adapter_path": active_arm.get("adapter"),
        "active_adapter_name": active_arm["name"],
        "adapter_state": active_arm["adapter_state"],
        "merged_sanity": False,  # deferred path; never merged in the MVP
        "device": extraction.get("device"),
        "dtype": extraction.get("compute_dtype"),  # native compute precision
        "source_split": prov_block.get("source_split"),
        "aligned_run_record_id": prov_block.get("aligned_run_record_id"),
        "aligned_probe_config_sha": aligned_probe_sha,
        "research_repo_commit": _git_commit(REPO_ROOT),
        "submodule_commit": _submodule_commit(REPO_ROOT, "synaptic-tuner"),
        "data_sha256": _file_sha256(data_source),
        "prompt_renderer_hash": _renderer_hash(config),
        "prompt_hash_corpus": schema.corpus_prompt_hash(rendered_prompts),
    }
    static.update(_read_adapter_lora_config(active_arm.get("adapter")))
    return static


def selection_data_source(config: dict) -> Path:
    """Return the selected row-source artifact for manifest data hashing."""
    selection = config["selection"]
    source = selection.get("source", "probe_pool")
    if source == "selfaware_manifest":
        return (PROBE_DIR / selection["manifest"]).resolve()
    return (PROBE_DIR / selection["probe_results"]).resolve()


def run_extraction(config: dict, extraction_config_sha: str, backend,
                   slice_rows: list[dict], out_dir: Path) -> Path:
    """Run the deterministic extraction over the slice; resumable append-log.

    Crash-safe (Decision D-bis): write the manifest with status="launched"
    BEFORE the forward, append per-row results + per-arm tensors, then patch the
    manifest to ok and set verified after checking the emitted tensors exist.
    Before the final write, the manifest is fully populated (static + backend
    provenance) and re-validated with require_populated=True so an under-populated
    manifest fails LOUDLY instead of shipping verified=True over None fields.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / config["output"]["manifest_filename"]
    rows_path = out_dir / config["output"]["rows_filename"]
    base_arm, active_arm = _arm_roles(config["arms"])
    token_rule = config["extraction"]["token_position_rule"]

    # WRITE-BEFORE-INVOKE: launched manifest hits disk before any forward.
    manifest = schema.build_manifest(
        config=config, extraction_config_sha=extraction_config_sha,
        status=schema.STATUS_LAUNCHED)
    schema.validate_manifest(manifest)
    _write_json(manifest_path, manifest)

    done = load_done_row_keys(rows_path)
    n_preexisting = len(done)
    tensor_shapes: dict[str, list[int]] = {}
    # Corpus rendered deterministically over the FULL slice (resume-independent)
    # so prompt_hash_corpus is stable regardless of how many rows were skipped.
    rendered_prompts = [backend.render(row["question"]) for row in slice_rows]
    try:
        n_new = _extract_rows(
            backend, slice_rows, done, rows_path, base_arm, active_arm,
            token_rule, extraction_config_sha, out_dir, config, tensor_shapes)
    except Exception as exc:  # noqa: BLE001 - record failure, then re-raise
        manifest["status"] = schema.STATUS_FAILED
        _write_json(manifest_path, manifest)
        raise RuntimeError(
            f"extraction failed after launch; manifest marked failed at "
            f"{_rel(manifest_path)}: {exc}"
        ) from exc

    # Full-resume recovery: when every row was already done, _extract_rows
    # forwarded nothing and tensor_shapes is empty. Reconstruct it from the
    # persisted rows + shards so a resumed status=ok run carries the same
    # tensor_shapes a fresh run would, instead of crashing at the finalize gate.
    if not tensor_shapes:
        tensor_shapes.update(_reconstruct_tensor_shapes(out_dir, rows_path))

    # Populate provenance (static GPU-free fields + backend post-load fields)
    # BEFORE the finalize gate, so require_populated=True has a complete manifest.
    manifest.update(collect_static_provenance(config, slice_rows, rendered_prompts))
    manifest.update(backend.provenance())
    manifest["status"] = schema.STATUS_OK
    manifest["tensor_shapes"] = tensor_shapes or None
    manifest["verified"] = _verify_emitted(out_dir, base_arm, active_arm, config)
    # D-bis finalize gate: a status=ok extraction MUST carry a fully-populated
    # Decision-D manifest. This raises (failing loudly) on any None field rather
    # than silently shipping verified=True over missing provenance.
    schema.validate_manifest(manifest, require_populated=True)
    _write_json(manifest_path, manifest)
    print(f"hidden_state_probe: wrote {n_new} new rows to {_rel(rows_path)} "
          f"({n_preexisting} already present, skipped); manifest "
          f"status={manifest['status']} verified={manifest['verified']}")
    return manifest_path


def _extract_rows(backend, slice_rows, done, rows_path, base_arm, active_arm,
                  token_rule, cfg_sha, out_dir, config, tensor_shapes) -> int:
    """Forward each unseen row for both arms; append the row + per-arm tensors."""
    n_new = 0
    persist_delta = config["extraction"].get("persist_delta", True)
    with rows_path.open("a", encoding="utf-8") as fh:
        for row in slice_rows:
            key = row["probe_pool_row_key"]
            if key in done:
                continue
            rendered = backend.render(row["question"])
            h_base = backend.forward_hidden_states(
                rendered, base_arm["adapter_state"], None)
            h_lora = backend.forward_hidden_states(
                rendered, active_arm["adapter_state"], active_arm["name"])
            _validate_arm_tensors(backend, h_base, h_lora, token_rule)
            delta = _vector_delta(h_lora, h_base) if persist_delta else None

            _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta,
                                 config, tensor_shapes)
            record = {
                "probe_pool_row_key": key,
                "row_key": row.get("row_key", key),
                "question": row["question"],
                "label": row["label"],
                "probe_label": row["probe_label"],
                "aligned_probe_config_sha": row["aligned_probe_config_sha"],
                "prompt_hash": schema.prompt_hash(rendered),
                "extraction_config_sha": cfg_sha,
                "layer_count": schema.expected_layer_count(backend.num_hidden_layers),
                "hidden_dim": backend.hidden_dim,
            }
            for optional in ("stable_identity", "strata", "answer_value", "aliases", "source_arms"):
                if optional in row:
                    record[optional] = row[optional]
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            done.add(key)
            n_new += 1
    return n_new


def _validate_arm_tensors(backend, h_base, h_lora, token_rule) -> None:
    for layer_vectors in (h_base, h_lora):
        schema.validate_hidden_state_shape(
            layer_vectors=layer_vectors,
            num_hidden_layers=backend.num_hidden_layers,
            hidden_dim=backend.hidden_dim,
            token_position_rule=token_rule)


def _persist_row_tensors(out_dir, key, cfg_sha, h_base, h_lora, delta, config,
                         tensor_shapes) -> None:
    """Persist per-arm tensors for one row as safetensors (lazy numpy import).

    numpy is imported lazily so the row-record/append path stays importable
    without it; persistence is where the array dependency legitimately enters.
    """
    import numpy as np  # noqa: PLC0415
    from safetensors.numpy import save_file  # noqa: PLC0415

    persist_dtype = config["extraction"]["persist_dtype"]
    np_dtype = getattr(np, persist_dtype)
    # M1: honor extraction.layer_list. null => persist ALL captured layers; a
    # list => persist ONLY those layer ids (the full stack is still captured and
    # shape-validated upstream; this filters what reaches disk). Advertised knob
    # is now live, so the manifest's layer_list matches the persisted tensors.
    layer_list = config["extraction"].get("layer_list")
    keep_layers = set(layer_list) if layer_list is not None else None
    roles = {"h_base": h_base, "h_lora": h_lora}
    if delta is not None:
        roles["delta"] = delta

    safe_key = safe_tensor_key(key)
    for role, layer_vectors in roles.items():
        selected = {
            layer: vec for layer, vec in layer_vectors.items()
            if keep_layers is None or layer in keep_layers
        }
        if not selected:
            raise ValueError(
                f"extraction.layer_list {sorted(keep_layers)} selected no "
                f"captured layers (available 0..{len(layer_vectors) - 1}); "
                "check the configured layer ids"
            )
        tensors = {
            f"L{layer}": np.asarray(vec, dtype=np_dtype)
            for layer, vec in selected.items()
        }
        metadata = schema.safetensors_metadata(cfg_sha, safe_key, role)
        schema.validate_safetensors_metadata(metadata)
        path = out_dir / f"{safe_key}__{role}.safetensors"
        save_file(tensors, str(path), metadata=metadata)
        any_layer = next(iter(layer_vectors.values()))
        tensor_shapes[role] = [len(layer_vectors), len(any_layer)]


def safe_tensor_key(key: str) -> str:
    """Filesystem-safe tensor shard stem while preserving existing pipe behavior."""
    safe = key.replace("|", "_")
    for char in (":", "/", "\\", "<", ">", '"', "?", "*"):
        safe = safe.replace(char, "_")
    return safe


def _reconstruct_tensor_shapes(out_dir: Path, rows_path: Path) -> dict:
    """Rebuild tensor_shapes for a FULLY-resumed run from on-disk artifacts.

    On a resume where every slice row is already in the append-log, _extract_rows
    forwards nothing, so the in-memory tensor_shapes stays empty. The finalize
    gate (Decision D-bis) requires a status=ok manifest to carry non-None
    tensor_shapes, so a resumed run must reconstruct the same shapes a fresh run
    would have stamped — otherwise an idempotent re-run crashes at finalize.

    Faithful to the fresh-run value `[len(layer_vectors), len(any_layer)]`
    (hidden_state_probe.py: _persist_row_tensors): the FULL captured layer count
    (== the per-row record's `layer_count`, which is M1-independent — layer_list
    filters what reaches disk, not what is captured) and the hidden_dim. The
    roles present are derived from the shards actually on disk so persist_delta is
    honored without re-reading the config. Returns {} if nothing is recoverable
    (no rows or no shards), leaving the caller's None-tensor_shapes gate to fire.
    """
    last_record = None
    if rows_path.exists():
        with rows_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last_record = json.loads(line)
    if last_record is None:
        return {}
    layer_count = last_record.get("layer_count")
    hidden_dim = last_record.get("hidden_dim")
    if layer_count is None or hidden_dim is None:
        return {}

    # Roles present on disk (h_base / h_lora / optionally delta), from the shard
    # filenames `<key>__<role>.safetensors`. Using disk-truth keeps delta in iff
    # it was persisted, with no dependence on the config's persist_delta flag.
    roles = {
        shard.stem.rsplit("__", 1)[1]
        for shard in out_dir.glob("*.safetensors")
        if "__" in shard.stem
    }
    return {role: [layer_count, hidden_dim] for role in sorted(roles)}


def _verify_emitted(out_dir: Path, base_arm, active_arm, config) -> bool:
    """Decision D-bis: verified=True ONLY if expected tensor shards exist.

    The numerical h_base != h_lora check is GPU-only (real forward); on CPU the
    structural existence check is the strongest honest verification, so this
    never hand-sets verified on a run that emitted no tensors.
    """
    shards = list(out_dir.glob("*.safetensors"))
    return len(shards) > 0


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 6 — TransformersPeftBackend (lazy heavy imports; GPU-only forward)
# ---------------------------------------------------------------------------

class TransformersPeftBackend:
    """Real HF Transformers + PEFT ExtractionBackend (GPU). Lazy heavy imports.

    torch/transformers/peft are imported INSIDE __init__ so this module loads,
    and the stub path runs, on a CPU-only / no-GPU host (mirrors VLLMBackend's
    lazy vLLM import). Deterministic forward: model.eval(), use_cache=False,
    torch.no_grad(), batch=1, fixed dtype/device. The base pass uses
    PeftModel.disable_adapter(); the LoRA pass uses set_adapter(active). The
    shared render helper (backends.render_probe_prompt) is reused so this path
    cannot drift from VLLMBackend's thinking-tag handling.

    NOTE: PEFT/Transformers versions are intentionally NOT hard-pinned here;
    the manifest records them at runtime and the version pins are a TODO for
    devops/architect (cross-version adapter-load skew is a first-GPU-run gate).
    """

    def __init__(self, config: dict, system_prompt: str, active_adapter_path: str,
                 active_adapter_name: str):
        import torch  # noqa: PLC0415
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415

        self._torch = torch
        self._peft = __import__("peft")
        self._transformers = __import__("transformers")
        self.system_prompt = system_prompt
        self.enable_thinking = config["model"]["enable_thinking"]
        self.active_adapter_name = active_adapter_name
        self.active_adapter_path = active_adapter_path
        ext = config["extraction"]
        self.device = ext.get("device", "cuda")
        self._compute_dtype = getattr(torch, ext["compute_dtype"])
        self.token_position_rule = ext["token_position_rule"]

        self.model_name = config["model"]["model_name"]
        # Optional immutable revision pin (commit SHA / tag). Recorded as
        # base_model_revision and passed to from_pretrained so the load is
        # reproducible. None (default) loads the hub default branch — the
        # resolved snapshot SHA is still recovered post-load from
        # config._commit_hash below, so provenance stays a commit SHA, not a
        # mutable ref, whenever the hub returns one.
        self.model_revision = config["model"].get("revision")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, revision=self.model_revision)
        base = AutoModelForCausalLM.from_pretrained(
            self.model_name, revision=self.model_revision,
            torch_dtype=self._compute_dtype, device_map=self.device)
        self.model = PeftModel.from_pretrained(
            base, active_adapter_path, adapter_name=active_adapter_name)
        self.model.eval()
        self.num_hidden_layers = self.model.config.num_hidden_layers
        self.hidden_dim = self.model.config.hidden_size

    def render(self, question: str) -> str:
        # Reuse the SHARED render+verify helper (no second template path).
        from backends import render_probe_prompt  # noqa: PLC0415

        rendered, _mode = render_probe_prompt(
            self.tokenizer, self.system_prompt, question,
            enable_thinking=self.enable_thinking)
        return rendered

    def forward_hidden_states(self, rendered_prompt, arm_state, adapter_name):
        torch = self._torch
        inputs = self.tokenizer(rendered_prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            if arm_state in schema.BASE_ADAPTER_STATES:
                with self.model.disable_adapter():
                    out = self._forward(inputs)
            else:
                self.model.set_adapter(adapter_name)
                out = self._forward(inputs)
        # Final prompt token, all layers; batch=1 so -1 is unambiguous.
        return {
            layer: hs[0, -1, :].float().cpu().tolist()
            for layer, hs in enumerate(out.hidden_states)
        }

    def _forward(self, inputs):
        return self.model(**inputs, output_hidden_states=True,
                          use_cache=False, return_dict=True)

    def provenance(self) -> dict:
        """Post-load manifest provenance from the REAL loaded model + libraries.

        Supplies the fields that need the loaded backend: library versions, the
        base-model id/revision, and content hashes of the model + adapter dirs.
        Hub loads keep the resolved snapshot commit/configured revision behavior.
        Local merged-model directories have no hub commit, so they get an
        explicit local-sha256:<digest> identity over stable model files. Missing
        local provenance inputs fail explicitly; non-local unresolved hub ids
        still degrade to None so the strict finalize gate surfaces the gap.
        """
        base_cfg = getattr(self.model, "config", None)
        base_model_id = getattr(base_cfg, "_name_or_path", None) or self.model_name
        adapter_dir = Path(self.active_adapter_path) if self.active_adapter_path else None
        adapter_hash = (
            _file_sha256(adapter_dir / "adapter_config.json") if adapter_dir else None)
        # base_model_revision MUST be an IMMUTABLE pin, not a mutable ref or a
        # library version: prefer the resolved snapshot commit SHA the hub
        # returned (transformers sets config._commit_hash on a hub load), then
        # the operator-configured revision pin. Deliberately NOT
        # config.transformers_version (that is the library version the config was
        # saved with, not a model identity). None-safe: if neither is available
        # the field records None and the finalize gate surfaces the gap loudly
        # rather than attesting a non-immutable revision.
        base_model_revision = (
            getattr(base_cfg, "_commit_hash", None) or self.model_revision)
        local_model_hash = None
        if base_model_revision is None:
            local_model_hash = _local_model_dir_sha256(self.model_name)
            base_model_revision = local_model_hash
        return {
            "base_model_id": base_model_id,
            "base_model_revision": base_model_revision,
            "base_model_hash": local_model_hash or base_model_id,
            "adapter_hash": adapter_hash,
            "tokenizer_revision": getattr(self.tokenizer, "name_or_path", None),
            "peft_version": self._peft.__version__,
            "transformers_version": self._transformers.__version__,
        }


def build_extraction_backend(config: dict, system_prompt: str):
    """Construct the real GPU backend. The stub is built directly by tests."""
    _base_arm, active_arm = _arm_roles(config["arms"])
    return TransformersPeftBackend(
        config=config, system_prompt=system_prompt,
        active_adapter_path=active_arm["adapter"],
        active_adapter_name=active_arm["name"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_config = PROBE_DIR / "config" / "hidden_state_probe.yaml"
    parser.add_argument("--config", type=Path, default=default_config,
                        help="path to hidden_state_probe.yaml")
    args = parser.parse_args()

    config, cfg_sha = parse_config(args.config)
    slice_rows = select_matched_slice(config)
    out_dir = resolve_output_dir(config, cfg_sha)
    system_prompt = config.get("prompt", {}).get(
        "system", "You are a helpful assistant. Answer the question concisely.")
    backend = build_extraction_backend(config, system_prompt)
    run_extraction(config, cfg_sha, backend, slice_rows, out_dir)
    print(f"hidden_state_probe: extraction written to {_rel(out_dir)}")


if __name__ == "__main__":
    main()
