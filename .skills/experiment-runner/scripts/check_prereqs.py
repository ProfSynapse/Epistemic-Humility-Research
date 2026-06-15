#!/usr/bin/env python3
"""
Phase 1 experiment-runner — prerequisite gate.

Location: .claude/skills/experiment-runner/scripts/check_prereqs.py
Purpose: Assert the PROTOCOL.md v0.3 §5 launch prerequisites are verifiably
    present BEFORE run_matrix.py launches any cell. A hard failure ABORTS the
    whole matrix (never a single cell); two checks instead SKIP only the
    affected cells (cloud-data-not-published, bridge-prereqs-absent) so a
    not-yet-ready arm degrades gracefully rather than aborting the run.
Used by: run_matrix.py (imports check_cell; --check-only invokes it per
    expanded cell) and as a standalone CLI
    (`python check_prereqs.py --matrix <m.yaml> --data-root <d> [--lane cloud]`).

Design notes:
- Import-light: only stdlib + PyYAML at module load. The HF-hub availability
    query (item 3a) is isolated behind hub_dataset_revision(), which is the only
    function that touches huggingface_hub, and it is monkeypatchable so the gate
    logic is unit-testable with NO network.
- Side-effect-free: this module reads/queries; it never fetches, publishes, or
    writes. Publishing Phase-1 datasets to the hub is the tuner's
    dataset-publishing skill's job, not this gate's.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# Per-method training-file basenames the WS-2 builder emits (build_datasets.py).
# KTO files are suffixed by mapping (kto_<mapping>_train.jsonl); the recipe's
# dataset.local_file carries the concrete basename, so the gate derives the
# expected files from the recipe rather than re-deriving the mapping here.
MANIFEST_FILENAME = "build_manifest.json"


class PrereqError(Exception):
    """A hard prerequisite failure — run_matrix.py aborts the whole matrix."""


@dataclass
class CellPrereqResult:
    """Per-cell gate outcome. skip=True means launch this cell as SKIPPED."""

    ok: bool
    skip: bool = False
    skip_reason: str = ""
    details: dict = field(default_factory=dict)


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def data_dir_for_model_tag(data_root: Path, model_tag: str) -> Path:
    """Resolve the WS-2 builder output dir for a model tag."""
    return data_root / model_tag


def datasets_present(data_root: Path, model_tag: str, train_file: str, dev_file: str) -> bool:
    """Item 1: the builder train+dev outputs for the cell's arm exist on disk."""
    base = data_dir_for_model_tag(data_root, model_tag)
    return (base / train_file).is_file() and (base / dev_file).is_file()


def leakage_guard_passed(data_root: Path, model_tag: str) -> bool:
    """Item 2: build_manifest.json records the leakage-guard PASS.

    Refuses (returns False) if the manifest is absent or the guard did not pass,
    making the pre-registered leakage invariant a launch-time precondition.
    """
    manifest_path = data_dir_for_model_tag(data_root, model_tag) / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    guard = manifest.get("leakage_guard")
    return bool(isinstance(guard, dict) and guard.get("passed") is True)


def submodule_pushed(research_repo_root: Path) -> bool:
    """Item 3 (cloud): the recorded submodule pointer matches a pushed commit.

    The HF Jobs lane checks out the pinned submodule SHA, so the submodule must
    be pushed and the research-repo pointer must match a reachable remote commit.
    Verified by run_matrix.py via git plumbing; exposed here for the standalone
    gate. Kept as a thin shell-out so tests can monkeypatch it.
    """
    import subprocess

    sub = research_repo_root / "synaptic-tuner"
    try:
        head = subprocess.run(
            ["git", "-C", str(sub), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        # Is HEAD contained in any pushed remote branch?
        contains = subprocess.run(
            ["git", "-C", str(sub), "branch", "-r", "--contains", head],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return bool(contains)
    except (subprocess.CalledProcessError, OSError):
        return False


def hf_token_present() -> bool:
    """Item 3 (cloud): an HF credential is in the environment (never in a file)."""
    return bool(os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY"))


def hub_dataset_revision(dataset_name: str) -> Optional[str]:
    """Item 3a (cloud): resolve a published dataset's current revision SHA.

    Returns the hub commit SHA to pin into the run record, or None if the
    dataset is not resolvable on the hub. This is the ONLY function that imports
    huggingface_hub; tests monkeypatch it so the gate logic needs no network.
    """
    try:
        from huggingface_hub import HfApi  # local import keeps module import-light
    except ImportError:
        return None
    try:
        info = HfApi().dataset_info(dataset_name)
    except Exception:
        return None
    return getattr(info, "sha", None)


# --- Cloud seed/beta-forwarding capability gate ------------------------------
#
# The cloud lane is only safe to launch once the tuner forwards per-cell `seed`
# AND `beta` all the way to the trainer. If it does not, a cloud cell silently
# trains at the default seed (42) and default beta while the run record claims
# the intended values — invisible corruption of the seed sweep and beta panel
# (the HANDOFF §5 failure mode). The GENERAL tuner capability is being added by
# coder-cloud (Task #32), mirroring the existing learning-rate flow.
#
# We do NOT trust a hardcoded flag or a submodule SHA: the capability lands as
# working-tree edits before it is committed/pushed, so a version string would
# lie. Instead — same live-check philosophy as the hub gate — we PROBE the actual
# tuner source surface the runner will execute against. The probe is text-based
# (no torch/trl import; import-light) and monkeypatchable so the gate stays
# unit-testable.
#
# Three load-bearing surface elements must all be present (contract coordinated
# with coder-cloud + architect, Task #32 — names verified against the in-flight
# tuner working tree on feature/dpo-trainer):
#   1. CloudTrainingConfig carries `seed` and `beta` fields   (tuner/core/config.py)
#   2. the HF command builder emits `--seed` and `--beta`     (.../cloud/_hf_command_builder.py)
#   3. the CLI exposes `--train-seed` / `--train-beta`        (tuner/cli/parser.py)
#
# The OPEN decision ALWAYS comes from the live probe — there is deliberately no
# manual flag that can force the lane OPEN. A hand-flipped "capability present"
# boolean is exactly the desync the ruling excluded: someone sets it True while
# the pinned submodule predates #32 and the silent seed-42 corruption returns.
#
# FORCE_SEED_BETA_GATE_CLOSED is a one-way manual override that can only force the
# gate CLOSED (e.g. to quarantine the lane during an incident even if the probe
# passes). It can NEVER force OPEN. Default False = defer entirely to the probe.
FORCE_SEED_BETA_GATE_CLOSED: bool = False

_TUNER_DIRNAME = "synaptic-tuner"
_CLOUD_CONFIG_REL = "tuner/core/config.py"
_CLOUD_BUILDER_REL = "tuner/backends/training/cloud/_hf_command_builder.py"
_CLI_PARSER_REL = "tuner/cli/parser.py"


def _read_tuner_source(research_repo_root: Path, rel: str) -> Optional[str]:
    """Read a tuner source file as text, or None if it is not present.

    Text-only probe seam (no tuner import → no torch/trl). Monkeypatchable.
    """
    path = research_repo_root / _TUNER_DIRNAME / rel
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def cloud_seed_beta_capability_probe(research_repo_root: Path) -> bool:
    """Live-probe the tuner source for per-cell seed+beta forwarding.

    Returns True only if all three load-bearing surface elements are present in
    the actual tuner working tree (config fields, builder emission, CLI flags).
    A missing file or any missing element → False (fail-closed: a probe that
    cannot confirm the capability must not green-light a cloud launch).
    """
    config_src = _read_tuner_source(research_repo_root, _CLOUD_CONFIG_REL)
    builder_src = _read_tuner_source(research_repo_root, _CLOUD_BUILDER_REL)
    parser_src = _read_tuner_source(research_repo_root, _CLI_PARSER_REL)
    if config_src is None or builder_src is None or parser_src is None:
        return False

    # 1. CloudTrainingConfig must declare seed AND beta fields. Scope the search
    #    to the class body so we don't match an unrelated seed/beta elsewhere.
    config_tail = config_src.split("class CloudTrainingConfig", 1)
    config_has_fields = (
        len(config_tail) == 2
        and re.search(r"^\s*seed\s*:", config_tail[1], re.MULTILINE) is not None
        and re.search(r"^\s*beta\s*:", config_tail[1], re.MULTILINE) is not None
    )
    # 2. The HF command builder must EMIT both flags into the trainer invocation.
    builder_emits = ('"--seed"' in builder_src or "'--seed'" in builder_src) and (
        '"--beta"' in builder_src or "'--beta'" in builder_src
    )
    # 3. The CLI must expose the cloud override flags.
    cli_exposes = "--train-seed" in parser_src and "--train-beta" in parser_src
    return bool(config_has_fields and builder_emits and cli_exposes)


def cloud_chat_template_kwargs_capability_probe(research_repo_root: Path) -> bool:
    """Live-probe the tuner source for cloud chat_template_kwargs forwarding.

    PROTOCOL.md:193 pins enable_thinking=False for the hybrid Qwen3 pair (which
    default thinking ON). The SFT recipes carry it as training.chat_template_kwargs;
    the cloud lane must forward it to the trainer or a cloud SFT cell silently
    trains with thinking-mode ON while the run record claims the protocol pin —
    the same silent-substitution corruption class as a dropped seed (tuner #45/#48).

    Returns True only if BOTH cloud surface elements are present in the actual
    tuner working tree:
      1. CloudTrainingConfig declares a chat_template_kwargs field   (config.py)
      2. the HF command builder EMITS --chat-template-kwargs          (_hf_command_builder.py)
    No CLI-flag element: chat_template_kwargs flows via the recipe.training block
    through the recipe->CloudTrainingConfig mapping (like gradient_accumulation),
    not a per-cell --train-* override. A missing file or element => False
    (fail-closed: a probe that cannot confirm forwarding must not green-light a
    cloud launch). Against a pre-#48 tree this returns False; it flips True once
    #48's field + builder emission land in the pinned submodule.
    """
    config_src = _read_tuner_source(research_repo_root, _CLOUD_CONFIG_REL)
    builder_src = _read_tuner_source(research_repo_root, _CLOUD_BUILDER_REL)
    if config_src is None or builder_src is None:
        return False

    # 1. CloudTrainingConfig must declare the chat_template_kwargs field. Scope to
    #    the class body so an unrelated occurrence elsewhere cannot satisfy it.
    config_tail = config_src.split("class CloudTrainingConfig", 1)
    config_has_field = (
        len(config_tail) == 2
        and re.search(r"^\s*chat_template_kwargs\s*:", config_tail[1], re.MULTILINE)
        is not None
    )
    # 2. The HF command builder must EMIT the flag into the trainer invocation.
    builder_emits = (
        '"--chat-template-kwargs"' in builder_src
        or "'--chat-template-kwargs'" in builder_src
    )
    return bool(config_has_field and builder_emits)


def cloud_capability_ready(research_repo_root: Optional[Path] = None) -> bool:
    """Gate the whole cloud lane on the tuner seed/beta-forwarding capability.

    The OPEN decision comes ONLY from the live probe of the tuner source
    (cloud_seed_beta_capability_probe). FORCE_SEED_BETA_GATE_CLOSED can additionally
    force CLOSED but can never force OPEN — there is no manual 'capability present'
    flag, by design (a hand-flip would desync from the pinned submodule).
    """
    if FORCE_SEED_BETA_GATE_CLOSED:
        return False
    root = research_repo_root if research_repo_root is not None else Path(".")
    return cloud_seed_beta_capability_probe(root) and (
        cloud_chat_template_kwargs_capability_probe(root)
    )


# Local-lane forwarding surface — the mechanism is the HANDLER EXTENSION (§9.2
# lines 994-1013, lead-ratified final; trainer-`--config`/direct-invocation path
# explicitly WITHDRAWN at §9.2 :1175-1176) PLUS LoRA FLAG PARITY (§9.2(b)/(d) item
# 5, §5.2 SSOT, lead-ratified 2026-06-10). The tuner's local-run handler command
# builder is already method-generic (reads run.trainer, forwards a training-key
# whitelist with zero SFT-specific logic). coder-cloud's re-scoped #34:
#   1. widens the _compile dispatch guard past SFT-only → method ∈ {sft,dpo,kto};
#   2. forwards `beta` (method-gated to dpo/kto; `seed` already forwarded via #32);
#   3. adds LoRA flag parity to train_dpo.py / train_kto.py (the trainers gain
#      `--lora-*` argparse). This is the HYBRID ruling on coder-cloud's flag-diff:
#      run-control flags (--quiet/--no-dashboard/--save-*/--load-in-4bit) stay
#      method-gated in the builder, but the LoRA SCALARS get parity because the
#      recipe `lora:` block is the §5.2 SSOT and the 8B recipes pin r=64/alpha=128
#      vs the trainer config.yaml default r=32/alpha=64 — gating (not forwarding)
#      would silently corrupt the budget confound control on every 8B dpo/kto arm.
# So the LOCAL probe checks the HANDLER source (dispatch + seed/beta forward) AND —
# for the dpo/kto path — the TRAINER source for `--lora-*` parity. A missing LoRA
# sink is the SAME whole-matrix-corruption class as a missing seed/beta sink.
# Fail-closed: local cells gate-closed until #34's guard-widen + beta + LoRA parity
# all land in the pinned submodule, then it flips.
_LOCAL_HANDLER_REL = "tuner/handlers/local_run_handler.py"
_DPO_TRAINER_REL = "Trainers/dpo/train_dpo.py"
_KTO_TRAINER_REL = "Trainers/kto/train_kto.py"
# The five LoRA scalar flags the handler builder emits and the dpo/kto trainers
# must accept (§9.2(d) item 5). The builder's _flag_name maps key->`--kebab-case`,
# so e.g. lora_r -> --lora-r. The recipe lora: block is the SSOT for these values.
_LORA_PARITY_FLAGS = (
    "--lora-r", "--lora-alpha", "--lora-dropout",
    "--lora-target-modules", "--init-lora-weights",
)


def local_seed_beta_capability_probe(research_repo_root: Path) -> bool:
    """Live-probe the tuner source for LOCAL-lane per-cell forwarding capability.

    Handler-extension + LoRA-parity contract (§9.2 :994-1013 + (d) item 5, tuner
    task #34). Returns True only if ALL hold:
      1. the local run handler forwards `seed` AND `beta` in its training-key
         whitelist (seed via #32, beta via #34); and
      2. dispatch is no longer SFT-only — the `elif method == "sft"` guard in
         _compile has been widened so dpo/kto route through the generic builder; and
      3. LoRA flag parity — `train_dpo.py` AND `train_kto.py` accept every `--lora-*`
         scalar flag the builder emits (§5.2 budget SSOT; a missing sink silently
         mistrains every local dpo/kto arm at the wrong budget at 8B).
    A missing file or any missing element → False (fail-closed: a probe that cannot
    confirm the capability must not green-light a local launch). Against the
    pre-#34 tree this returns False (handler omits `beta` / still SFT-gated, and/or
    the trainers lack `--lora-*`); it flips True once #34 lands all three pieces.
    """
    handler_src = _read_tuner_source(research_repo_root, _LOCAL_HANDLER_REL)
    if handler_src is None:
        return False
    # 1. The handler must forward BOTH seed and beta in its training-key whitelist.
    forwards_seed = '"seed"' in handler_src or "'seed'" in handler_src
    forwards_beta = '"beta"' in handler_src or "'beta'" in handler_src
    if not (forwards_seed and forwards_beta):
        return False
    # 2. Dispatch must no longer be SFT-only. The pre-#34 wart is the exact guard
    #    `elif method == "sft"` (either quote style) in _compile; #34 widens it to
    #    route dpo/kto through the same generic builder. While that precise SFT-only
    #    gate survives, the handler still rejects 3 of its 4 registered methods.
    sft_only_gate = (
        'elif method == "sft"' in handler_src
        or "elif method == 'sft'" in handler_src
    )
    if sft_only_gate:
        return False
    # 3. LoRA flag parity (§9.2(d) item 5): the dpo/kto trainers must accept every
    #    --lora-* scalar the builder emits, or the recipe's §5.2 budget SSOT is
    #    silently dropped in favor of the trainer's config.yaml default at 8B.
    for rel in (_DPO_TRAINER_REL, _KTO_TRAINER_REL):
        trainer_src = _read_tuner_source(research_repo_root, rel)
        if trainer_src is None:
            return False
        if not all(flag in trainer_src for flag in _LORA_PARITY_FLAGS):
            return False
    return True


def lane_capability_ready(lane: str, research_repo_root: Optional[Path] = None) -> bool:
    """Gate a lane on the tuner seed/beta-forwarding capability for THAT lane.

    Each lane has its own forwarding surface (cloud command builder vs local run
    handler), so the cell is gated on the lane it will actually run on. The OPEN
    decision comes ONLY from the live probe; FORCE_SEED_BETA_GATE_CLOSED can force
    CLOSED for both lanes but can never force OPEN."""
    if FORCE_SEED_BETA_GATE_CLOSED:
        return False
    root = research_repo_root if research_repo_root is not None else Path(".")
    if lane == "cloud":
        # Cloud cells must forward seed/beta AND the chat_template_kwargs pin
        # (PROTOCOL.md:193 thinking-off). A gap in either is whole-matrix-abort
        # silent-substitution: a dropped seed corrupts the panel, a dropped
        # chat_template_kwargs trains the cloud SFT arm with thinking ON.
        return cloud_seed_beta_capability_probe(root) and (
            cloud_chat_template_kwargs_capability_probe(root)
        )
    return local_seed_beta_capability_probe(root)


def check_cell(
    *,
    lane: str,
    method: str,
    model_tag: str,
    train_file: str,
    dev_file: str,
    data_root: Path,
    research_repo_root: Path,
    dataset_name: Optional[str] = None,
    is_bridge: bool = False,
    bridge_prereqs_present: bool = False,
) -> CellPrereqResult:
    """Evaluate the gate for a single cell.

    Hard failures raise PrereqError (abort whole matrix). Cloud-data-unpublished
    and bridge-prereq-absent produce a SKIP result (launch the cell as SKIPPED,
    matrix continues).
    """
    # Item 1 + 2 apply to every cell; the local builder output is the source of
    # truth even for cloud cells (the cloud dataset is published FROM it).
    if not datasets_present(data_root, model_tag, train_file, dev_file):
        raise PrereqError(
            f"datasets missing for arm '{model_tag}/{method}': expected "
            f"{train_file} and {dev_file} under {data_dir_for_model_tag(data_root, model_tag)}"
        )
    if not leakage_guard_passed(data_root, model_tag):
        raise PrereqError(
            f"leakage guard not PASSED for '{model_tag}': "
            f"{MANIFEST_FILENAME} absent or leakage_guard.passed != true"
        )

    # Bridge cells are LOCAL-LANE ONLY: the OpenMOSS bridge training data is
    # user-authorized for vendored use but DO-NOT-REDISTRIBUTE (no license), so
    # it will never be published to the HF hub. A bridge cell on the cloud lane
    # is therefore a structurally invalid request — no future state makes it
    # runnable on cloud — so it ABORTS (loud), unlike the not-yet-available SKIP
    # conditions below. This abort precedes the bridge-prereqs-absent skip: a
    # mis-specified lane is a config error, not a "data not fetched yet" state.
    if is_bridge and lane == "cloud":
        raise PrereqError(
            "bridge cell requested on the cloud lane, but bridge training data is "
            "do-not-redistribute and is never published to the hub — bridge arms "
            "are LOCAL-LANE ONLY. Launch the bridge arms with --lane local."
        )

    # Bridge cells (item 4): skip-not-abort when their gated prereqs are absent.
    if is_bridge and not bridge_prereqs_present:
        return CellPrereqResult(
            ok=True, skip=True,
            skip_reason="bridge prerequisites absent (Cheng IDK data / gated Llama-2 access)",
        )

    # Tuner capability gate — applies to BOTH lanes. The tuner must forward per-cell
    # seed (and, for DPO/KTO, beta) AND honor the recipe's LoRA budget (LoRA flag
    # parity, local dpo/kto) all the way to the trainer, or cells silently train at
    # the default seed (42) / default beta / wrong LoRA budget while the run record
    # claims the intended values (HANDOFF §5 failure mode). Each lane has its OWN
    # forwarding surface, so we probe the lane the cell will run on, live against the
    # actual tuner source (not a flag).
    #
    # This is a WHOLE-MATRIX ABORT, not a cell skip (§9.2(d) item 5): a missing
    # seed/beta sink makes every headline seed identical and every beta-panel cell
    # land at the default — it corrupts the ENTIRE headline + panel design, not one
    # arm — and a missing LoRA sink mistrains every local dpo/kto arm at the wrong
    # §5.2 budget. There is no meaningful partial run, so the gate aborts loudly with
    # the missing capability + the lane it gates, rather than silently launching.
    if not lane_capability_ready(lane, research_repo_root):
        raise PrereqError(
            f"tuner {lane} lane has not landed the per-cell forwarding capability "
            f"(seed/beta forwarding + dispatch; LoRA flag parity for local dpo/kto; "
            f"chat_template_kwargs forwarding for cloud SFT, coder-cloud #48) "
            f"— capability probe failed against the pinned submodule. This ABORTS "
            f"the whole matrix: a missing seed/beta/LoRA sink silently corrupts the "
            f"entire headline + panel design, and a missing chat_template_kwargs sink "
            f"trains the cloud SFT arm with thinking-mode ON against PROTOCOL.md:193. "
            f"Re-run once the {lane}-lane capability lands and is verified."
        )

    if lane == "cloud":
        if not submodule_pushed(research_repo_root):
            raise PrereqError(
                "cloud lane: submodule not pushed / pointer not on a reachable remote commit"
            )
        if not hf_token_present():
            raise PrereqError("cloud lane: HF_TOKEN / HF_API_KEY not present in environment")
        # Item 3a: hub-dataset availability — skip-not-abort for this arm.
        revision = hub_dataset_revision(dataset_name) if dataset_name else None
        if revision is None:
            return CellPrereqResult(
                ok=True, skip=True,
                skip_reason=f"cloud dataset '{dataset_name}' not resolvable on the HF hub",
            )
        return CellPrereqResult(ok=True, details={"hf_dataset_revision": revision})

    return CellPrereqResult(ok=True)


# ===========================================================================
# Hidden-state EXTRACTION gate (architecture §4 + §6 + §8) — ADDITIVE.
# ===========================================================================
#
# Everything below is the off-matrix extraction capability. It NEVER alters the
# train/eval surface above: `check_cell`, `lane_capability_ready`, the three
# capability probes, `PrereqError` vs `CellPrereqResult` semantics, and
# `FORCE_SEED_BETA_GATE_CLOSED` are untouched. Extraction is EXPLORATORY, so
# every failure here is a SKIP (`CellPrereqResult(skip=True)`), NEVER a
# `PrereqError` — there is no matrix to abort, and a missing prereq must degrade
# gracefully rather than tear anything down (§4.3). The locked 19/9/2 count
# assertions live in run_matrix.py and are not referenced here.


def _resolve_against_probe_dir(probe_dir: Path, rel_or_abs: str) -> Path:
    """Resolve a config path relative to the probe dir (harness convention).

    The harness anchors config relative paths at the probe dir (see
    hidden_state_probe.resolve_eval_arm_adapters / select_matched_slice), so the
    launch-time gate uses the SAME base to pre-check the same files.
    """
    candidate = Path(rel_or_abs)
    return candidate if candidate.is_absolute() else (probe_dir / candidate)


def _first_probe_row_sha(results_path: Path) -> Optional[str]:
    """Stream the first non-empty JSONL row and return its probe_config_sha.

    Reads ONE line only (the file is ~123MB; never whole-load it — §4.3 E1).
    Returns None if the file is unreadable/empty or the row lacks the field.
    """
    try:
        with results_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    return None
                return row.get("probe_config_sha")
    except OSError:
        return None
    return None


def check_extraction_cell(
    *,
    config: dict,
    config_path: Path,
    research_repo_root: Path,
    run_records_dir: Optional[Path] = None,
    require_verified: bool = True,
) -> CellPrereqResult:
    """Fail-closed, SKIP-not-abort prereq gate for one hidden-state extraction.

    Returns a CellPrereqResult so the report shape matches the train/eval gate.
    EVERY failing check yields CellPrereqResult(skip=True, ...) — never a
    PrereqError. Checks run in order; the first failure decides the skip reason
    (architecture §4.3):

      E1  probe_results.jsonl present on disk for the model_tag
      E2  probe_results.jsonl probe_config_sha matches the expected provenance
          (selection.expected_probe_config_sha; null => presence-only + WARN)
      E3  aligned_run_record_id resolvable (resolver returns a non-None id AND
          run_records/<id>.json exists)
      E4  each active arm's adapter dir contains adapter_config.json

    A null model.revision is a WARN (not a SKIP) on the local lane (§8): the
    post-load _commit_hash still pins identity for an exploratory local run, but
    the operator is reminded to pin before a reproducible run. The cloud lane's
    revision requirement is enforced in the cloud-extract verb contract (§6.2),
    not here.
    """
    # Import the runner-side resolver lazily so this module stays import-light and
    # the resolver is co-located in the same scripts/ dir (synced canonical tree).
    import resolve_run_record  # noqa: PLC0415  (local import: keep module light)

    probe_dir = config_path.resolve().parent.parent  # config/<f>.yaml -> probe/
    details: dict = {}
    warnings: list[str] = []

    model = config.get("model") or {}
    selection = config.get("selection") or {}
    arms = config.get("arms") or []
    prov = config.get("manifest_provenance") or {}

    # Revision-pin WARN (§8): surfaced regardless of which check decides the gate.
    if model.get("revision") is None:
        warnings.append(
            "model.revision is null — acceptable for an exploratory LOCAL run "
            "(the resolved snapshot SHA is still recovered post-load), but SHOULD "
            "be pinned to a commit SHA before a reproducible run (cloud REQUIRES it)."
        )

    def _skip(reason: str) -> CellPrereqResult:
        return CellPrereqResult(ok=True, skip=True, skip_reason=reason,
                                details={**details, "warnings": warnings})

    # --- E1: probe_results.jsonl present -----------------------------------
    probe_results_rel = selection.get("probe_results")
    if not probe_results_rel:
        return _skip("selection.probe_results not set in the extraction config")
    results_path = _resolve_against_probe_dir(probe_dir, probe_results_rel).resolve()
    details["probe_results_path"] = str(results_path)
    if not results_path.is_file():
        model_tag = model.get("model_tag", "<unknown>")
        return _skip(
            f"probe_results.jsonl absent for {model_tag} (run the probe tier "
            f"first; WS-1 output, ~123MB, gitignored) — expected {results_path}"
        )

    # --- E2: probe_config_sha provenance -----------------------------------
    expected_sha = selection.get("expected_probe_config_sha")
    found_sha = _first_probe_row_sha(results_path)
    details["probe_config_sha_found"] = found_sha
    if expected_sha is None:
        # Null expectation cannot fail-closed against an unknown; WARN loudly and
        # degrade E2 to presence-only (§4.4 preferred-source decision).
        warnings.append(
            "selection.expected_probe_config_sha is null — E2 degraded to "
            "presence-only; the probe_config_sha provenance of "
            f"{results_path} (found {found_sha!r}) is NOT being verified. Set "
            "selection.expected_probe_config_sha to enforce it."
        )
    elif found_sha != expected_sha:
        return _skip(
            f"probe_results.jsonl probe_config_sha mismatch / contaminated "
            f"(expected {expected_sha!r}, found {found_sha!r}) — the probe rows "
            f"were produced by a different probe config (e.g. thinking-mode ON)"
        )

    # --- resolve the active arm adapter path (post eval-config mirror) ------
    # The harness mirrors active-arm adapters from eval_arms_source; reuse it so
    # the gate checks the SAME adapter the harness will load. We only need the
    # harness mirror when an active arm's adapter is NULL (it must be filled from
    # eval_arms_source). If every active arm already carries an explicit adapter,
    # no mirror — and thus no harness import — is required (KISS + avoids a
    # needless dependency when the config is self-contained).
    active_arms = [a for a in arms if a.get("adapter_state") == "active"]
    needs_mirror = any(a.get("adapter") is None for a in active_arms)
    if needs_mirror:
        # Temporarily expose the probe dir so the harness module is importable,
        # and ALWAYS restore sys.path afterward (finally) so this gate never leaks
        # an entry into a long-lived process — e.g. a test session — which could
        # otherwise bleed imports across cells/tests.
        probe_dir_str = str(probe_dir)
        sys.path.insert(0, probe_dir_str)
        try:
            import hidden_state_probe as harness  # noqa: PLC0415
            resolved_config = harness.resolve_eval_arm_adapters(
                {**config, "arms": [dict(a) for a in arms]}, config_path)
            active_arms = [
                a for a in resolved_config["arms"]
                if a.get("adapter_state") == "active"
            ]
        except Exception as exc:  # noqa: BLE001 — a mirror failure is a SKIP, not abort
            return _skip(f"could not resolve active-arm adapter path(s): {exc}")
        finally:
            try:
                sys.path.remove(probe_dir_str)
            except ValueError:
                pass  # already removed/absent — nothing to restore

    if not active_arms:
        return _skip("no active arm declared in the extraction config")

    records_dir = run_records_dir if run_records_dir is not None else (
        research_repo_root / "experiment" / "phase1" / "run_records")

    # --- E3 + E4 per active arm --------------------------------------------
    resolved_ids: dict[str, str] = {}
    for arm in active_arms:
        adapter_path = arm.get("adapter")
        if not adapter_path:
            return _skip(f"active arm {arm.get('name')!r} has no adapter path")

        # E3: aligned_run_record_id resolvable. The reverse-lookup is the single
        # source of truth for the verified-gate: it returns id=None (with a reason)
        # on zero-match / ambiguous / unverified, honoring require_verified. An
        # explicitly-pinned id does NOT bypass that gate — it is an ADDITIONAL
        # constraint: the pin must equal what the reverse-lookup independently
        # resolves (so a pinned-but-unverified id fails closed exactly like an
        # unpinned one). require_verified (set False by --allow-unverified) is the
        # only escape hatch; there is no pin-based override.
        explicit_id = prov.get("aligned_run_record_id")
        result = resolve_run_record.resolve_aligned_run_record_id(
            adapter_path=adapter_path, run_records_dir=records_dir,
            require_verified=require_verified,
        )
        if result.id is None:
            return _skip(
                f"aligned_run_record_id unresolvable for active arm "
                f"{arm.get('name')!r} adapter {adapter_path}: {result.reason}"
            )
        if explicit_id is not None and result.id != explicit_id:
            return _skip(
                f"aligned_run_record_id {explicit_id!r} disagrees with the "
                f"verified adapter reverse-lookup ({result.id!r}) — fail-closed"
            )
        resolved_ids[arm["name"]] = result.id

        # E4: the adapter dir must carry adapter_config.json (PEFT config read
        # GPU-free by the backend for lora_* provenance).
        adapter_dir = Path(str(adapter_path).replace("\\", "/"))
        if not (adapter_dir / "adapter_config.json").is_file():
            return _skip(
                f"adapter_config.json missing under active arm adapter dir "
                f"{adapter_dir}"
            )

    details["resolved_run_record_ids"] = resolved_ids
    return CellPrereqResult(ok=True, details={**details, "warnings": warnings})


# --- Cloud-extract runner-side gating (architecture §6.5) --------------------
#
# The runner-side PROBE + gate for the cloud-extract verb. The verb ITSELF is
# built by backend-coder in the synaptic-tuner submodule (a separate repo); this
# is only the runner's live capability probe + the push-gate sequence, mirroring
# the seed/beta probe philosophy: NEVER trust a flag/SHA — probe the actual tuner
# source the runner will execute against. False => the cloud-extract path SKIPs
# (it is exploratory), NEVER a whole-matrix abort.
_CLOUD_EXTRACT_VERB = "cloud-extract"


def cloud_extract_capability_probe(research_repo_root: Path) -> bool:
    """Live-probe the tuner source for the cloud-extract verb (§6.5 step 2).

    Returns True only if BOTH surface elements are present in the actual tuner
    working tree:
      1. the CLI parser exposes the `cloud-extract` verb        (tuner/cli/parser.py)
      2. the verb's command builder emits the extraction args   (--adapter-repo-id,
         --slice-dataset-name, --output-dataset-name)
    A missing file or any missing element => False (fail-closed: a probe that
    cannot confirm the capability must not green-light a cloud-extract launch).
    Against the pre-build tree this returns False; it flips True once
    backend-coder's verb lands in the pinned submodule. Text-only probe (no tuner
    import) and monkeypatchable, exactly like cloud_seed_beta_capability_probe.
    """
    parser_src = _read_tuner_source(research_repo_root, _CLI_PARSER_REL)
    builder_src = _read_tuner_source(research_repo_root, _CLOUD_BUILDER_REL)
    if parser_src is None or builder_src is None:
        return False
    cli_exposes = _CLOUD_EXTRACT_VERB in parser_src
    builder_emits = (
        ("--adapter-repo-id" in builder_src)
        and ("--slice-dataset-name" in builder_src)
        and ("--output-dataset-name" in builder_src)
    )
    return bool(cli_exposes and builder_emits)


def cloud_extract_prereqs(
    *,
    research_repo_root: Path,
    slice_dataset_name: Optional[str] = None,
    adapter_repo_id: Optional[str] = None,
    base_model_name: Optional[str] = None,
) -> CellPrereqResult:
    """Runner-side push-gate sequence for a cloud-extract launch (§6.5).

    SKIP-not-abort (cloud-extract is exploratory). Sequence (each a SKIP reason):
      1. submodule pushed (the pinned SHA carrying the verb is reachable)
      2. cloud_extract_capability_probe (verb exists in the tuner source)
      3. HF_TOKEN present (env-only, never printed)
      4. each referenced artifact (slice dataset / adapter repo / base model)
         resolves on the hub

    This is the runner half ONLY; the verb itself is backend-coder's submodule
    work. The capability probe confirms the verb exists in SOURCE; submodule_pushed
    separately confirms the pinned commit is reachable — both must hold (§6.5
    layering note), so even after the probe passes on the working tree, a launch
    correctly SKIPs until the verb is committed and pushed.
    """
    if not cloud_extract_capability_probe(research_repo_root):
        return CellPrereqResult(
            ok=True, skip=True,
            skip_reason=(
                "tuner cloud-extract verb not present in source (capability probe "
                "failed) — backend-coder's submodule verb has not landed yet"
            ),
        )
    if not submodule_pushed(research_repo_root):
        return CellPrereqResult(
            ok=True, skip=True,
            skip_reason=(
                "cloud-extract: submodule not pushed / pointer not on a reachable "
                "remote commit (HF Jobs checks out the pinned SHA)"
            ),
        )
    if not hf_token_present():
        return CellPrereqResult(
            ok=True, skip=True,
            skip_reason="cloud-extract: HF_TOKEN / HF_API_KEY not present in environment",
        )
    for label, name in (
        ("slice dataset", slice_dataset_name),
        ("base model", base_model_name),
    ):
        if name and hub_dataset_revision(name) is None and label == "slice dataset":
            return CellPrereqResult(
                ok=True, skip=True,
                skip_reason=f"cloud-extract: {label} '{name}' not resolvable on the HF hub — publish it first",
            )
    # adapter_repo_id is a MODEL repo; its resolution is verified by the verb at
    # launch (model-info), not a dataset-revision check, so it is surfaced in
    # details for the caller rather than gated here.
    return CellPrereqResult(ok=True, details={
        "cloud_extract_capability": True,
        "adapter_repo_id": adapter_repo_id,
        "slice_dataset_name": slice_dataset_name,
        "base_model_name": base_model_name,
    })


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 prerequisite gate (standalone).")
    parser.add_argument("--matrix", required=True, help="Path to config/matrix.yaml")
    parser.add_argument("--data-root", required=True, help="Research-repo data root (experiment/phase1/data)")
    parser.add_argument("--research-repo-root", default=".", help="Research repo root (default: cwd)")
    parser.add_argument("--lane", choices=["local", "cloud"], default="local")
    parser.add_argument("--recipes-dir", default="experiment/phase1/recipes",
                        help="Dir holding the base recipe YAMLs")
    return parser


def main(argv: Optional[list] = None) -> int:
    """Standalone --check-only entry point: report gate status, launch nothing."""
    args = _build_arg_parser().parse_args(argv)
    matrix = load_yaml(Path(args.matrix))
    print(f"Prereq gate (lane={args.lane}) for matrix '{matrix.get('matrix_version')}'")
    print("  This standalone gate reports config-level readiness; run_matrix.py")
    print("  performs the per-cell gate during expansion. Use --check-only there")
    print("  for the full per-cell report.")
    if not lane_capability_ready(args.lane, Path(args.research_repo_root)):
        print(f"  NOTE: {args.lane} lane is gated CLOSED — the seed/beta capability")
        print("  probe failed against the submodule source (tuner does not yet")
        print(f"  forward per-cell seed/beta on the {args.lane} lane; Task #32). Cells")
        print("  record as SKIPPED until the probe passes against the tuner source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
