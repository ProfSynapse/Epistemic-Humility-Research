#!/usr/bin/env python3
"""GPU-free provenance primitives for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). These are the leaf helpers
that derive manifest provenance from git, on-disk files/dirs, the adapter
config.json, and the renderer identity — all WITHOUT torch/transformers/peft and
WITHOUT PROBE_DIR. The orchestrating collect_static_provenance + selection_data_source
stay in the facade because they read PROBE_DIR (the monkeypatch seam).
"""

from __future__ import annotations

import json
from pathlib import Path

import hidden_state_schema as schema


def _git_commit(repo_dir: Path) -> str | None:
    """HEAD commit of a git repo, or None if unavailable (GPU-free, optional)."""
    import subprocess  # noqa: PLC0415

    try:
        out = subprocess.run(
            ["git", "-c", f"safe.directory={repo_dir}", "-C", str(repo_dir), "rev-parse", "HEAD"],
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
            [
                "git",
                "-c",
                f"safe.directory={repo_dir}",
                "-C",
                str(repo_dir),
                "ls-tree",
                "HEAD",
                submodule_path,
            ],
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
