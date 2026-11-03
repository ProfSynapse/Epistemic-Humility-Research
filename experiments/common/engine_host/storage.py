"""Host-owned storage selection; local GPU templates must opt into a host file."""

from pathlib import Path
import hashlib

import yaml


def load_host(path: Path) -> dict:
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != "ehr-desktop-host/v1":
        raise ValueError("ehr-desktop-host/v1 configuration required")
    return document


def configure_storage(project_root: Path, config_path: Path) -> dict[str, str]:
    """Fail before loading/downloading when the project or caches leave T7.

    This selects paths, not an OS sandbox. The launch must bind these same E:
    directories into its container; mounted volume identity is checked on host.
    """
    document = load_host(config_path)
    storage = document["storage"]
    mount = Path(storage["wsl_mount"]).resolve()
    root = Path(project_root).resolve()
    model_root = Path(storage["model_root"]).resolve()
    if not mount.is_dir() or not root.is_relative_to(mount) or not model_root.is_relative_to(mount):
        raise ValueError("project, models and checkpoints must use the selected T7 mount")
    cache = root / ".synaptic" / "cache"
    temporary = root / ".synaptic" / "tmp"
    for path in (cache / "huggingface" / "hub", cache / "torch", temporary,
                 root / ".synaptic" / "artifacts", root / ".synaptic" / "tracking"):
        if not path.resolve().is_relative_to(mount) or not path.resolve().is_relative_to(root):
            raise ValueError("a cache symlink leaves the selected T7 mount")
        path.mkdir(parents=True, exist_ok=True)
    return {"HF_HOME": str(cache / "huggingface"),
            "HF_HUB_CACHE": str(cache / "huggingface" / "hub"),
            "TORCH_HOME": str(cache / "torch"), "TMPDIR": str(temporary),
            "EHR_HOST_CONFIG": str(Path(config_path).resolve())}


def local_model(config_path: Path, repo: str, revision: str) -> str:
    """Reuse the configured snapshot when it matches; otherwise download to T7 cache."""
    document = load_host(config_path)
    base = document.get("base_model", {})
    if repo == base.get("repo") and revision == base.get("revision"):
        snapshot = Path(base["local_snapshot"]).resolve()
        mount = Path(document["storage"]["wsl_mount"]).resolve()
        if not snapshot.is_relative_to(mount) or not snapshot.is_dir():
            raise ValueError("configured local model snapshot is missing or outside T7")
        for name, expected in base.get("shard_sha256", {}).items():
            path = snapshot / name
            if Path(name).name != name or path.is_symlink() or not path.is_file():
                raise ValueError("configured model shard is missing or unsafe")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                raise ValueError("configured model shard hash mismatch")
        return str(snapshot)
    return repo
