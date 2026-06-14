#!/usr/bin/env python3
"""Model-free validation + manifest builder for the hidden-state probing tier.

Location: experiment/phase1/probe/hidden_state_schema.py
Used by:  experiment/phase1/probe/hidden_state_probe.py
Tested by: experiment/phase1/probe/tests/test_hidden_state_probe.py

This module is the TESTABILITY KEYSTONE of the hidden-state extraction tier
(plan Decision B): it carries NO heavy dependency (no torch / transformers /
peft) so the entire validation + manifest surface can be exercised on a CPU,
GPU-free host. The harness (hidden_state_probe.py) does the model load + forward
behind a backend seam; everything that decides whether an extraction is VALID
lives here.

Responsibilities (single concern: "is this extraction well-formed?"):
  - adapter-state pre-flight (the GPU-free tier of the two-tier confound guard):
    reject any arm config that does not pair exactly one disabled/unloaded base
    arm with one active-adapter arm; reject both-arms-active (the silent
    adapter-active-vs-adapter-active confound that would invalidate every delta).
  - hidden-state tensor-shape validation: the per-layer stack must have length
    `num_hidden_layers + 1` (embeddings + N block outputs, verified against the
    Transformers contract), each layer a [hidden_dim] final-token vector.
  - token-position-rule validation (only the rules this MVP supports).
  - manifest field completeness (Decision D exhaustive manifest) + the crash-safe
    status lifecycle (Decision D-bis: launched -> ok/failed, verified gated).
  - safetensors persistence contract: keys/dtype shape that a round-trip must
    satisfy, asserted on plain numpy arrays so no torch is needed to test it.

Nothing here imports a model. A wrong shape, a missing manifest field, or a
both-active arm config fails HERE, at write time, not at Phase-5 load time.
"""

from __future__ import annotations

import hashlib
import json

# ---------------------------------------------------------------------------
# Enums / constants (the pinned vocabulary the config and manifest must use)
# ---------------------------------------------------------------------------

# Adapter state of one extraction arm. `disabled`/`unloaded` are the two valid
# base-pass forms (PeftModel.disable_adapter() context vs a base model with no
# adapter loaded); `active` is the LoRA pass. `merged` is reserved for the
# deferred merged-sanity path (plan Decision: keep the enum slot, do not build).
ADAPTER_STATE_DISABLED = "disabled"
ADAPTER_STATE_UNLOADED = "unloaded"
ADAPTER_STATE_ACTIVE = "active"
ADAPTER_STATE_MERGED = "merged"

BASE_ADAPTER_STATES = frozenset({ADAPTER_STATE_DISABLED, ADAPTER_STATE_UNLOADED})
VALID_ADAPTER_STATES = frozenset({
    ADAPTER_STATE_DISABLED, ADAPTER_STATE_UNLOADED,
    ADAPTER_STATE_ACTIVE, ADAPTER_STATE_MERGED,
})

# Token-position rules supported in the MVP. `final_prompt_token` is the spec
# default (the last prompt token's hidden state); others are future expansion.
TOKEN_POSITION_FINAL_PROMPT = "final_prompt_token"
VALID_TOKEN_POSITION_RULES = frozenset({TOKEN_POSITION_FINAL_PROMPT})

# Crash-safe manifest status lifecycle (Decision D-bis): WRITE-BEFORE-INVOKE
# stamps `launched`; the forward patches `ok` or `failed`. A `launched` manifest
# left on disk is a self-evident crashed/partial extraction.
STATUS_LAUNCHED = "launched"
STATUS_OK = "ok"
STATUS_FAILED = "failed"
VALID_STATUSES = frozenset({STATUS_LAUNCHED, STATUS_OK, STATUS_FAILED})

# Per-arm tensor file roles persisted as safetensors (plan Decision C). `delta`
# is persisted (tamper-evident, cheap downstream), not recomputed on read.
TENSOR_ROLES = ("h_base", "h_lora", "delta")

# Exhaustive manifest field set (plan Decision D). Field PRESENCE is asserted by
# validate_manifest; this is the single source of truth for "what provenance a
# hidden-state extraction must carry". Keep in lockstep with build_manifest.
REQUIRED_MANIFEST_FIELDS = frozenset({
    # model + adapter identity
    "base_model_id", "base_model_revision", "base_model_hash",
    "adapter_path", "adapter_hash", "active_adapter_name",
    "adapter_state", "merged_sanity",
    "lora_rank", "lora_alpha", "lora_dropout", "lora_target_modules",
    # render / determinism provenance
    "dtype", "device", "compute_dtype", "persist_dtype",
    "tokenizer_revision", "enable_thinking",
    "prompt_renderer_hash", "prompt_hash_corpus",
    # data + alignment provenance
    "source_split", "data_sha256", "layer_list", "token_position_rule",
    "tensor_shapes", "persistence_format",
    # code + config provenance (link-never-mutate run records)
    "research_repo_commit", "submodule_commit",
    "extraction_config_sha", "aligned_probe_config_sha", "aligned_run_record_id",
    "peft_version", "transformers_version",
    # crash-safe lifecycle (Decision D-bis)
    "status", "verified",
})


# ---------------------------------------------------------------------------
# Hash helpers (mirror probe.py config_sha idiom for cross-tier consistency)
# ---------------------------------------------------------------------------

def config_sha(config: dict) -> str:
    """Stable 16-hex hash of a config dict (probe.py `config_sha` idiom).

    Identical algorithm to the stochastic probe so an extraction_config_sha is
    computed the same way the probe_config_sha is, keeping the two tiers'
    provenance discipline consistent and comparable.
    """
    blob = json.dumps(config, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def prompt_hash(rendered_prompt: str) -> str:
    """Stable 16-hex hash of one rendered prompt's exact bytes.

    The per-row prompt identity: base and adapter passes MUST render the same
    bytes, so each arm stamps this and the harness asserts equality across arms.
    """
    return hashlib.sha256(rendered_prompt.encode("utf-8")).hexdigest()[:16]


def corpus_prompt_hash(rendered_prompts: list[str]) -> str:
    """Stable hash over an ordered list of rendered prompts (corpus identity)."""
    h = hashlib.sha256()
    for rendered in rendered_prompts:
        h.update(rendered.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Adapter-state pre-flight (P0; GPU-free tier of the two-tier confound guard)
# ---------------------------------------------------------------------------

def validate_arm_states(arms: list[dict]) -> None:
    """Reject any arm set that would silently confound the base-vs-LoRA delta.

    The single most dangerous failure for an attribution harness is comparing an
    adapter-ACTIVE pass to another adapter-ACTIVE pass (e.g. both arms forgot to
    disable). This pre-flight is the GPU-free half of the two-tier guard; the
    GPU-smoke `h_base != h_lora` assertion is the other half.

    Contract (raises ValueError with an actionable message on any breach):
      - exactly one base arm whose state is in {disabled, unloaded}
      - exactly one active arm whose state is `active`
      - no `merged` arm in the MVP (the slot exists but the path is deferred)
      - every arm has a non-empty `name` and a valid `adapter_state`
    """
    if not isinstance(arms, list) or not arms:
        raise ValueError("adapter-state pre-flight: `arms` must be a non-empty list")

    names: list[str] = []
    for idx, arm in enumerate(arms):
        name = arm.get("name")
        if not name or not isinstance(name, str):
            raise ValueError(
                f"adapter-state pre-flight: arm #{idx} is missing a non-empty "
                f"`name` (got {name!r})"
            )
        names.append(name)
        state = arm.get("adapter_state")
        if state not in VALID_ADAPTER_STATES:
            raise ValueError(
                f"adapter-state pre-flight: arm {name!r} has invalid "
                f"adapter_state {state!r}; expected one of "
                f"{sorted(VALID_ADAPTER_STATES)}"
            )
        if state == ADAPTER_STATE_MERGED:
            raise ValueError(
                f"adapter-state pre-flight: arm {name!r} requests the `merged` "
                "state, but the merged-sanity path is DEFERRED in the MVP "
                "(the enum slot is reserved; do not build it here)"
            )

    duplicate_names = {n for n in names if names.count(n) > 1}
    if duplicate_names:
        raise ValueError(
            f"adapter-state pre-flight: duplicate arm name(s) {sorted(duplicate_names)}; "
            "each arm name must be unique (it keys the per-arm output tree)"
        )

    base_arms = [a for a in arms if a["adapter_state"] in BASE_ADAPTER_STATES]
    active_arms = [a for a in arms if a["adapter_state"] == ADAPTER_STATE_ACTIVE]

    if len(base_arms) != 1:
        raise ValueError(
            "adapter-state pre-flight: expected EXACTLY ONE base arm "
            f"(adapter_state in {sorted(BASE_ADAPTER_STATES)}); found "
            f"{len(base_arms)}. The base pass anchors h_base; missing or "
            "duplicated it poisons every delta."
        )
    if len(active_arms) != 1:
        raise ValueError(
            "adapter-state pre-flight: expected EXACTLY ONE active arm "
            f"(adapter_state == {ADAPTER_STATE_ACTIVE!r}); found "
            f"{len(active_arms)}. Two active arms is the silent "
            "adapter-active-vs-adapter-active confound; aborting before any "
            "forward pass."
        )


# ---------------------------------------------------------------------------
# Tensor-shape + token-position validation (model-free)
# ---------------------------------------------------------------------------

def validate_token_position_rule(rule: str) -> None:
    """Reject any token-position rule the MVP does not implement."""
    if rule not in VALID_TOKEN_POSITION_RULES:
        raise ValueError(
            f"token-position rule {rule!r} is not supported in the MVP; "
            f"expected one of {sorted(VALID_TOKEN_POSITION_RULES)}"
        )


def expected_layer_count(num_hidden_layers: int) -> int:
    """Per the Transformers contract: hidden_states has length N+1.

    Index 0 is the embedding output; 1..N are the N block outputs. (The N+2
    form is Mamba-specific and must NOT be generalized here.)
    """
    return num_hidden_layers + 1


def validate_hidden_state_shape(
    *, layer_vectors: dict, num_hidden_layers: int, hidden_dim: int,
    token_position_rule: str,
) -> None:
    """Validate one arm's per-layer final-token hidden-state stack (no torch).

    `layer_vectors` maps layer_id (int, 0..N) -> a 1-D sequence of length
    hidden_dim (the final-token vector at that layer). Validated on plain
    sequences (list/tuple/numpy 1-D), so tests need no torch.

    Raises ValueError on: wrong layer count (!= N+1), a missing/extra layer id,
    or any layer vector whose length != hidden_dim. The token-position rule is
    validated too, since the shape contract is rule-specific (final-token =>
    one vector per layer; future windowed rules would carry a seq axis).
    """
    validate_token_position_rule(token_position_rule)

    want_count = expected_layer_count(num_hidden_layers)
    if len(layer_vectors) != want_count:
        raise ValueError(
            f"hidden-state layer count {len(layer_vectors)} != "
            f"num_hidden_layers + 1 = {want_count}. The Transformers "
            "output_hidden_states tuple must carry embeddings + every block "
            "output; a mismatch means the wrong layers were captured."
        )

    expected_ids = set(range(want_count))
    got_ids = set(layer_vectors.keys())
    if got_ids != expected_ids:
        missing = sorted(expected_ids - got_ids)
        extra = sorted(got_ids - expected_ids)
        raise ValueError(
            f"hidden-state layer ids mismatch; missing={missing} extra={extra}; "
            f"expected contiguous 0..{want_count - 1}"
        )

    for layer_id, vec in layer_vectors.items():
        length = _vector_length(vec)
        if length != hidden_dim:
            raise ValueError(
                f"hidden-state layer {layer_id} vector length {length} != "
                f"hidden_dim {hidden_dim}; a final-token vector must be 1-D of "
                "width hidden_dim"
            )


def _vector_length(vec) -> int:
    """Length of a 1-D vector (list/tuple or a 1-D numpy/array-like).

    Defensive: rejects scalars and multi-dim arrays so a [seq, hidden] tensor
    slipping in (the literal `-1` left-padding footgun) is caught as a shape
    error rather than silently length-matching.
    """
    shape = getattr(vec, "shape", None)
    if shape is not None:
        if len(shape) != 1:
            raise ValueError(
                f"expected a 1-D final-token vector, got shape {tuple(shape)}"
            )
        return int(shape[0])
    try:
        return len(vec)
    except TypeError as exc:  # scalar / non-sequence
        raise ValueError(f"expected a 1-D vector, got {type(vec).__name__}") from exc


# ---------------------------------------------------------------------------
# safetensors persistence contract (asserted on numpy, no torch)
# ---------------------------------------------------------------------------

def safetensors_metadata(extraction_config_sha: str, arm_name: str,
                         tensor_role: str) -> dict:
    """The string-only metadata block stored inside a safetensors file.

    safetensors metadata VALUES MUST be strings, so the rich manifest lives in
    a sidecar manifest.json and only a small string-keyed provenance stub goes
    in the tensor file (enough to detect a mismatched/misfiled shard).
    """
    if tensor_role not in TENSOR_ROLES:
        raise ValueError(
            f"tensor_role {tensor_role!r} not in {TENSOR_ROLES}"
        )
    return {
        "extraction_config_sha": str(extraction_config_sha),
        "arm_name": str(arm_name),
        "tensor_role": str(tensor_role),
    }


def validate_safetensors_metadata(metadata: dict) -> None:
    """All safetensors metadata values must be strings (round-trip contract)."""
    for key, value in metadata.items():
        if not isinstance(value, str):
            raise ValueError(
                f"safetensors metadata value for {key!r} is "
                f"{type(value).__name__}, must be str (safetensors stores only "
                "string metadata; keep rich fields in manifest.json)"
            )


# ---------------------------------------------------------------------------
# Manifest builder + validation (Decision D + D-bis)
# ---------------------------------------------------------------------------

def build_manifest(*, config: dict, extraction_config_sha: str,
                   status: str = STATUS_LAUNCHED) -> dict:
    """Assemble the Decision-D exhaustive manifest from a parsed config.

    Built with status=`launched` by default so the harness can WRITE-BEFORE-INVOKE
    (Decision D-bis): the manifest hits disk before the forward pass, then the
    harness patches `status`, `tensor_shapes`, and `verified` afterward. `verified`
    starts False and is set True ONLY by the harness after checking emitted
    tensors (never hand-set here).

    Pulls the exhaustive provenance from the config's `manifest_provenance`
    sub-block (config is the SSOT; the harness fills runtime-discovered fields
    like base_model_hash / tensor_shapes after load). Missing provenance values
    default to None so a partial config still yields a complete-keyed manifest
    that validate_manifest can check for population at finalize time.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"status {status!r} not in {sorted(VALID_STATUSES)}")

    prov = config.get("manifest_provenance", {})
    extraction = config.get("extraction", {})

    manifest = {field: prov.get(field) for field in REQUIRED_MANIFEST_FIELDS}
    # Fields the schema/harness owns rather than free-form provenance:
    manifest["extraction_config_sha"] = extraction_config_sha
    manifest["enable_thinking"] = config.get("model", {}).get("enable_thinking")
    manifest["layer_list"] = extraction.get("layer_list")
    manifest["token_position_rule"] = extraction.get("token_position_rule")
    manifest["compute_dtype"] = extraction.get("compute_dtype")
    manifest["persist_dtype"] = extraction.get("persist_dtype")
    manifest["persistence_format"] = extraction.get("persistence_format", "safetensors")
    manifest["status"] = status
    manifest["verified"] = False
    manifest["tensor_shapes"] = None  # patched post-forward
    return manifest


def validate_manifest(manifest: dict, *, require_populated: bool = False) -> None:
    """Assert the manifest carries the exact Decision-D field set.

    `require_populated=False` (default, write-before-invoke time): only field
    PRESENCE is asserted, since runtime fields (base_model_hash, tensor_shapes)
    are filled after the forward.

    `require_populated=True` (finalize time): also asserts the launch-critical
    provenance fields are non-None and the status/verified invariants hold
    (verified True only when status is ok). This is the gate that a `launched`
    or `failed` extraction can never be silently treated as verified.
    """
    missing = REQUIRED_MANIFEST_FIELDS - set(manifest.keys())
    if missing:
        raise ValueError(
            f"manifest missing required field(s): {sorted(missing)} "
            "(Decision D exhaustive-manifest contract)"
        )
    extra = set(manifest.keys()) - REQUIRED_MANIFEST_FIELDS
    if extra:
        raise ValueError(
            f"manifest has unexpected field(s): {sorted(extra)}; the manifest "
            "schema is closed (update REQUIRED_MANIFEST_FIELDS to extend it)"
        )

    status = manifest.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(f"manifest status {status!r} not in {sorted(VALID_STATUSES)}")

    verified = manifest.get("verified")
    if not isinstance(verified, bool):
        raise ValueError(f"manifest `verified` must be bool, got {verified!r}")
    if verified and status != STATUS_OK:
        raise ValueError(
            f"manifest `verified` is True but status is {status!r}; verified may "
            "only be set on a status=ok extraction (Decision D-bis)"
        )

    if require_populated:
        _assert_populated(manifest)


# Provenance fields that MUST be non-None for a finalized extraction. Excludes
# fields legitimately null in the MVP (merged_sanity is False not None; the
# deferred-merged path never populates a merged manifest).
_FINALIZE_REQUIRED_NON_NULL = frozenset(REQUIRED_MANIFEST_FIELDS - {
    "tensor_shapes",  # validated separately (must be populated when status ok)
    # layer_list is null by design when ALL layers are persisted (the common
    # case); null here is an intentional "all layers" sentinel, not missing
    # provenance, so it is exempt from the non-null finalize requirement.
    "layer_list",
})


def _assert_populated(manifest: dict) -> None:
    null_fields = sorted(
        f for f in _FINALIZE_REQUIRED_NON_NULL if manifest.get(f) is None
    )
    if null_fields:
        raise ValueError(
            f"finalize: manifest provenance field(s) still None: {null_fields}; "
            "every Decision-D field must be populated before an extraction is "
            "treated as complete"
        )
    if manifest.get("status") == STATUS_OK and manifest.get("tensor_shapes") is None:
        raise ValueError(
            "finalize: status is ok but tensor_shapes is None; the forward must "
            "patch tensor_shapes before marking an extraction ok"
        )
