"""Exact isolated Modal launcher owned by the consuming project."""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Sequence

_MARKER = "SYNAPTIC_MODAL_LAUNCHER_V1"
_MODAL_VERSION = "1.5.4"
_PYTHON_VERSION = "3.11.15"
_UV_VERSION = "0.12.0"
_UV_ARCHIVE = "uv-x86_64-unknown-linux-gnu.tar.gz"
_UV_ARCHIVE_SHA256 = "eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9"
_UV_URL = f"https://github.com/astral-sh/uv/releases/download/{_UV_VERSION}/{_UV_ARCHIVE}"
_MAX_UV_ARCHIVE_BYTES = 64 * 1024 * 1024


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _cache_root(project_root: Path) -> Path:
    return project_root / ".synaptic" / "cache"


def launcher_python(project_root: Path) -> Path:
    return _cache_root(project_root) / "modal-launcher-v1" / "bin" / "python"


def _runtime_stamp(requirements: Path) -> str:
    payload = "\0".join((_digest(requirements), _UV_VERSION, _PYTHON_VERSION))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "synaptic-host-launcher-v1"})
    size = 0
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as stream:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > _MAX_UV_ARCHIVE_BYTES:
                    raise RuntimeError("pinned uv archive exceeded its size bound")
                stream.write(chunk)


def _uv_binary(project_root: Path) -> Path:
    if platform.system() != "Linux" or platform.machine().lower() not in {
        "x86_64", "amd64",
    }:
        raise RuntimeError("Modal launcher v1 requires Linux x86_64")
    root = _cache_root(project_root) / "tools" / f"uv-{_UV_VERSION}"
    binary = root / "uv"
    stamp = root / ".archive-sha256"
    if (
        binary.is_file()
        and stamp.is_file()
        and stamp.read_text(encoding="ascii").strip() == _UV_ARCHIVE_SHA256
    ):
        return binary
    if root.exists():
        raise RuntimeError(
            f"pinned uv bootstrap is incomplete; remove only {root} and retry"
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=root.parent, prefix=f".uv-{_UV_VERSION}-build-"
    ) as temporary:
        temporary_root = Path(temporary)
        archive = temporary_root / _UV_ARCHIVE
        payload = temporary_root / "payload"
        payload.mkdir()
        _download(_UV_URL, archive)
        if _digest(archive) != _UV_ARCHIVE_SHA256:
            raise RuntimeError("pinned uv archive digest mismatch")
        expected_member = "uv-x86_64-unknown-linux-gnu/uv"
        with tarfile.open(archive, mode="r:gz") as bundle:
            members = [item for item in bundle.getmembers() if item.name == expected_member]
            if len(members) != 1 or not members[0].isfile():
                raise RuntimeError("pinned uv archive did not contain the exact binary")
            source = bundle.extractfile(members[0])
            if source is None:
                raise RuntimeError("pinned uv binary could not be read")
            with source, (payload / "uv").open("wb") as destination:
                shutil.copyfileobj(source, destination)
        (payload / "uv").chmod(0o755)
        (payload / ".archive-sha256").write_text(
            _UV_ARCHIVE_SHA256 + "\n", encoding="ascii"
        )
        os.replace(payload, root)
    return binary


def _uv_environment(project_root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    cache = _cache_root(project_root)
    environment.update({
        "UV_CACHE_DIR": str(cache / "uv-cache-v1"),
        "UV_LINK_MODE": "copy",
        "UV_NO_PROGRESS": "1",
        "UV_PYTHON_INSTALL_DIR": str(cache / "uv-python-v1"),
        "UV_PYTHON_PREFERENCE": "only-managed",
    })
    return environment


def _build_runtime(*, project_root: Path, requirements: Path, expected: str) -> None:
    root = launcher_python(project_root).parent.parent
    if root.exists():
        raise RuntimeError(
            "isolated Modal launcher exists with an incomplete or stale lock; "
            "remove only .synaptic/cache/modal-launcher-v1 and retry"
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    build = Path(tempfile.mkdtemp(dir=root.parent, prefix=".modal-launcher-v1-build-"))
    try:
        uv = _uv_binary(project_root)
        environment = _uv_environment(project_root)
        subprocess.run(
            [
                str(uv), "venv", "--python", _PYTHON_VERSION,
                str(build),
            ],
            check=True, cwd=project_root, env=environment,
        )
        python = build / "bin" / "python"
        subprocess.run(
            [
                str(uv), "pip", "install", "--python", str(python),
                "--require-hashes", "--only-binary", ":all:",
                "-r", str(requirements),
            ],
            check=True, cwd=project_root, env=environment,
        )
        observed = subprocess.run(
            [str(python), "-c", "import platform;print(platform.python_version())"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        if observed != _PYTHON_VERSION:
            raise RuntimeError("isolated Modal launcher Python version mismatch")
        (build / ".synaptic-lock-sha256").write_text(
            expected + "\n", encoding="ascii"
        )
        os.replace(build, root)
    except BaseException:
        shutil.rmtree(build, ignore_errors=True)
        raise


def ensure_and_reexec(
    *, project_root: Path, engine_root: Path, argv: Sequence[str]
) -> int | None:
    """Run provider commands in the exact locked SDK; return child status."""
    if os.environ.get(_MARKER) == "1":
        import modal

        if modal.__version__ != _MODAL_VERSION:
            raise RuntimeError("isolated Modal launcher version mismatch")
        if platform.python_version() != _PYTHON_VERSION:
            raise RuntimeError("isolated Modal launcher Python version mismatch")
        return None
    requirements = engine_root / "requirements" / "modal-launcher-v1.lock"
    expected = _runtime_stamp(requirements)
    python = launcher_python(project_root)
    stamp = python.parent.parent / ".synaptic-lock-sha256"
    ready = (
        python.is_file() and stamp.is_file()
        and stamp.read_text(encoding="ascii").strip() == expected
    )
    if not ready:
        _build_runtime(
            project_root=project_root, requirements=requirements, expected=expected
        )
    environment = dict(os.environ)
    environment[_MARKER] = "1"
    existing = environment.get("PYTHONPATH", "")
    roots = os.pathsep.join((str(project_root), str(engine_root)))
    environment["PYTHONPATH"] = roots if not existing else roots + os.pathsep + existing
    completed = subprocess.run(
        [str(python), "-m", "synaptic_host", *argv],
        cwd=project_root, env=environment, check=False,
    )
    return completed.returncode
