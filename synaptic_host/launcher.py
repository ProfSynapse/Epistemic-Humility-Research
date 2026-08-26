"""Exact isolated Modal launcher owned by the consuming project."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Sequence

_MARKER = "SYNAPTIC_MODAL_LAUNCHER_V1"


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def launcher_python(project_root: Path) -> Path:
    root = project_root / ".synaptic" / "cache" / "modal-launcher-v1"
    windows = root / "Scripts" / "python.exe"
    return windows if os.name == "nt" else root / "bin" / "python"


def ensure_and_reexec(
    *, project_root: Path, engine_root: Path, argv: Sequence[str]
) -> int | None:
    """Run provider commands in the exact locked SDK; return child status."""
    if os.environ.get(_MARKER) == "1":
        import modal

        if modal.__version__ != "1.5.4":
            raise RuntimeError("isolated Modal launcher version mismatch")
        return None
    requirements = engine_root / "requirements" / "modal-launcher-v1.lock"
    expected = _digest(requirements)
    python = launcher_python(project_root)
    stamp = python.parent.parent / ".synaptic-lock-sha256"
    ready = (
        python.is_file() and stamp.is_file()
        and stamp.read_text(encoding="ascii").strip() == expected
    )
    if not ready:
        root = python.parent.parent
        if root.exists():
            raise RuntimeError(
                "isolated Modal launcher exists with an incomplete or stale lock; "
                "remove only .synaptic/cache/modal-launcher-v1 and retry"
            )
        root.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True, clear=False, symlinks=False).create(root)
        subprocess.run(
            [
                str(python), "-m", "pip", "install", "--disable-pip-version-check",
                "--require-hashes", "--only-binary=:all:", "-r", str(requirements),
            ],
            check=True, cwd=project_root,
        )
        stamp.write_text(expected + "\n", encoding="ascii")
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
