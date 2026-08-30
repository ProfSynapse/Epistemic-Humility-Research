"""Exact isolated Modal launcher owned by the consuming project."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
import urllib.request
from pathlib import Path
from typing import Sequence

_MARKER = "SYNAPTIC_MODAL_LAUNCHER_V1"
_INGRESS_DIGEST = "SYNAPTIC_TRAINING_INGRESS_DIGEST_V1"
_CONTRACT_IDENTITY_DIGEST = "SYNAPTIC_TRAINING_CONTRACT_IDENTITY_DIGEST_V1"
_RUNTIME_PROOF_DIGEST = "SYNAPTIC_MODAL_RUNTIME_PROOF_DIGEST_V1"
_PROOF_SCHEMA = "synaptic-modal-launcher-runtime-proof/v1"
_PYTHON_VERSION = "3.11.15"
_UV_VERSION = "0.12.0"
_UV_ARCHIVE = "uv-x86_64-unknown-linux-gnu.tar.gz"
_UV_ARCHIVE_SHA256 = "eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9"
_UV_URL = f"https://github.com/astral-sh/uv/releases/download/{_UV_VERSION}/{_UV_ARCHIVE}"
_MAX_UV_ARCHIVE_BYTES = 64 * 1024 * 1024
_PROOF_FILE = ".synaptic-runtime-proof.json"
_ALLOWED_CHILD_ENV = (
    "HOME", "LANG", "LC_ALL", "PATH", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR",
)
_MODAL_CREDENTIAL_ENV = ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET")
_FIXED_BOOTSTRAP = """import os,runpy,sys
project_root,engine_root=sys.argv[1:3]
if not os.path.isabs(project_root) or not os.path.isabs(engine_root): raise SystemExit(4)
project_root=os.path.realpath(project_root); engine_root=os.path.realpath(engine_root)
if not os.path.isdir(project_root) or not os.path.isdir(engine_root): raise SystemExit(4)
sys.path[:0]=[project_root,engine_root]
sys.argv=['synaptic_host',*sys.argv[3:]]
runpy.run_module('synaptic_host',run_name='__main__')
"""


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


def _contained_relative(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if (
        not relative or relative.startswith("/") or "\\" in relative
        or any(part in {"", ".", "..", "~"} for part in relative.split("/"))
        or len(relative.encode("utf-8")) > 4096
    ):
        raise RuntimeError("runtime proof path is invalid")
    return relative


def _stable_regular_bytes(path: Path, maximum: int = 1024 * 1024) -> bytes:
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise RuntimeError("runtime proof member is invalid")
    if before.st_size > maximum:
        raise RuntimeError("runtime proof member is invalid")
    payload = path.read_bytes()
    after = path.lstat()
    identity = lambda value: (
        value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns
    )
    if identity(before) != identity(after) or len(payload) != before.st_size:
        raise RuntimeError("runtime proof member changed")
    return payload


def _validated_child_environment_value(value: object) -> str | None:
    if type(value) is not str:
        return None
    try:
        encoded = value.encode("utf-8")
        snapshot = encoded.decode("utf-8")
    except UnicodeError:
        return None
    if (
        not encoded or len(encoded) > 4096
        or any(
            unicodedata.category(character).startswith("C")
            for character in snapshot
        )
    ):
        return None
    return snapshot


def _launcher_chain(
    launcher: Path, venv_root: Path, managed_root: Path,
) -> tuple[list[dict[str, object]], Path]:
    current = launcher
    seen: set[str] = set()
    entries: list[dict[str, object]] = []
    total_text = 0
    for index in range(8):
        observed = current.lstat()
        if not stat.S_ISLNK(observed.st_mode):
            if index == 0:
                raise RuntimeError("launcher Python must be a managed symlink")
            if not stat.S_ISREG(observed.st_mode):
                raise RuntimeError("launcher Python target is invalid")
            return entries, current
        key = os.path.normcase(str(current.absolute()))
        if key in seen:
            raise RuntimeError("launcher Python symlink cycle")
        seen.add(key)
        link_text = os.readlink(current)
        encoded = link_text.encode("utf-8")
        total_text += len(encoded)
        if total_text > 4096 or not encoded:
            raise RuntimeError("launcher Python link text is invalid")
        target = Path(link_text)
        if not target.is_absolute():
            target = current.parent / target
        target = Path(os.path.abspath(os.path.normpath(target)))
        target.relative_to(managed_root)
        if index == 0:
            location_kind = "venv"
            relative = _contained_relative(current, venv_root)
        else:
            location_kind = "managed"
            relative = _contained_relative(current, managed_root)
        entries.append({
            "index": index,
            "link_location_kind": location_kind,
            "link_relative_path": relative,
            "link_text_sha256": hashlib.sha256(encoded).hexdigest(),
            "resolved_target_kind": "managed",
            "resolved_target_relative_path": _contained_relative(target, managed_root),
        })
        current = target
    raise RuntimeError("launcher Python symlink chain is too long")


def _python_identity(python: Path) -> dict[str, str]:
    completed = subprocess.run(
        [str(python), "-I", "-c", (
            "import json,platform,sys;print(json.dumps({"
            "'python_version':platform.python_version(),"
            "'prefix':sys.prefix,'base_prefix':sys.base_prefix},sort_keys=True))"
        )],
        check=True, capture_output=True, text=True,
        env={},
    )
    value = json.loads(completed.stdout)
    if type(value) is not dict or set(value) != {"python_version", "prefix", "base_prefix"}:
        raise RuntimeError("launcher Python identity is invalid")
    if any(type(item) is not str for item in value.values()):
        raise RuntimeError("launcher Python identity is invalid")
    return value


def _uv_reported_version(uv: Path) -> str:
    completed = subprocess.run(
        [str(uv), "--version"], check=True, capture_output=True, text=False, env={}
    )
    expected = f"uv {_UV_VERSION}".encode("ascii")
    expected_target = expected + b" (x86_64-unknown-linux-gnu)"
    if type(completed.stdout) is not bytes or completed.stdout not in {
        expected,
        expected + b"\n",
        expected_target,
        expected_target + b"\n",
    }:
        raise RuntimeError("pinned uv executable version mismatch")
    return _UV_VERSION


def _proof_digest(body: dict[str, object]) -> str:
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(_PROOF_SCHEMA.encode("ascii") + b"\0" + canonical).hexdigest()


def _closed_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if type(key) is not str or key in value:
            raise RuntimeError("stored runtime proof is invalid")
        value[key] = item
    return value


def _reject_json_constant(_value: str) -> object:
    raise RuntimeError("stored runtime proof is invalid")


def _compute_runtime_proof(
    *, project_root: Path, engine_root: Path, venv_root: Path | None = None,
    uv_binary: Path | None = None,
) -> dict[str, object]:
    venv = (venv_root or launcher_python(project_root).parent.parent).absolute()
    managed = (_cache_root(project_root) / "uv-python-v1").absolute()
    requirements = engine_root / "requirements/modal-launcher-v1.lock"
    requirements_bytes = _stable_regular_bytes(requirements)
    stamp_bytes = _stable_regular_bytes(venv / ".synaptic-lock-sha256", 1024)
    lock_stamp = stamp_bytes.decode("ascii").strip()
    if lock_stamp != _runtime_stamp(requirements):
        raise RuntimeError("launcher runtime stamp mismatch")
    uv = (uv_binary or _uv_binary(project_root)).absolute()
    uv_bytes = _stable_regular_bytes(uv, _MAX_UV_ARCHIVE_BYTES)
    archive_stamp = _stable_regular_bytes(uv.parent / ".archive-sha256", 1024)
    if archive_stamp.decode("ascii").strip() != _UV_ARCHIVE_SHA256:
        raise RuntimeError("pinned uv archive identity mismatch")
    uv_version = _uv_reported_version(uv)
    chain, final_target = _launcher_chain(venv / "bin/python", venv, managed)
    final_bytes = _stable_regular_bytes(final_target, _MAX_UV_ARCHIVE_BYTES)
    final_stat = final_target.lstat()
    mode = stat.S_IMODE(final_stat.st_mode)
    if mode & 0o111 == 0:
        raise RuntimeError("launcher Python target is not executable")
    pyvenv = _stable_regular_bytes(venv / "pyvenv.cfg", 64 * 1024)
    identity = _python_identity(venv / "bin/python")
    if identity["python_version"] != _PYTHON_VERSION:
        raise RuntimeError("launcher Python version mismatch")
    prefix = Path(identity["prefix"]).absolute()
    base_prefix = Path(identity["base_prefix"]).absolute()
    if prefix != venv:
        raise RuntimeError("launcher Python prefix mismatch")
    base_relative = _contained_relative(base_prefix, managed)
    body: dict[str, object] = {
        "schema_version": _PROOF_SCHEMA,
        "lock_stamp": lock_stamp,
        "requirements_lock_sha256": hashlib.sha256(requirements_bytes).hexdigest(),
        "uv_version": uv_version,
        "uv_archive_sha256": _UV_ARCHIVE_SHA256,
        "uv_executable_sha256": hashlib.sha256(uv_bytes).hexdigest(),
        "python_version": _PYTHON_VERSION,
        "launcher_relative_path": "bin/python",
        "launcher_chain": chain,
        "final_target_relative_path": _contained_relative(final_target, managed),
        "final_target_sha256": hashlib.sha256(final_bytes).hexdigest(),
        "final_target_size": len(final_bytes),
        "final_target_mode": mode,
        "pyvenv_cfg_sha256": hashlib.sha256(pyvenv).hexdigest(),
        "sys_prefix_relative_path": ".",
        "base_prefix_relative_path": base_relative,
    }
    return body


def _runtime_proof(project_root: Path, engine_root: Path) -> tuple[dict[str, object], str]:
    body = _compute_runtime_proof(project_root=project_root, engine_root=engine_root)
    digest = _proof_digest(body)
    stored = json.loads(
        _stable_regular_bytes(
            launcher_python(project_root).parent.parent / _PROOF_FILE
        ).decode("utf-8", errors="strict"),
        object_pairs_hook=_closed_json_object,
        parse_constant=_reject_json_constant,
    )
    if type(stored) is not dict or set(stored) != {*body, "proof_digest"}:
        raise RuntimeError("stored runtime proof is invalid")
    expected = {**body, "proof_digest": digest}
    if json.dumps(
        stored, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ) != json.dumps(
        expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ):
        raise RuntimeError("stored runtime proof mismatch")
    return body, digest


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
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        python = build / "bin" / "python"
        subprocess.run(
            [
                str(uv), "pip", "install", "--python", str(python),
                "--require-hashes", "--only-binary", ":all:",
                "-r", str(requirements),
            ],
            check=True, cwd=project_root, env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
        proof_body = _compute_runtime_proof(
            project_root=project_root, engine_root=requirements.parents[1],
            venv_root=build, uv_binary=uv,
        )
        proof_digest = _proof_digest(proof_body)
        (build / _PROOF_FILE).write_text(
            json.dumps(
                {**proof_body, "proof_digest": proof_digest},
                sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                allow_nan=False,
            ) + "\n",
            encoding="utf-8",
        )
        os.replace(build, root)
    except BaseException:
        shutil.rmtree(build, ignore_errors=True)
        raise


def ensure_and_reexec(
    *, project_root: Path, engine_root: Path, argv: Sequence[str],
    ingress_digest: str, contract_identity_digest: str,
) -> int | None:
    """Enter or validate the exact locked interpreter for one ingress digest."""
    digests = (ingress_digest, contract_identity_digest)
    if any(
        type(value) is not str or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        for value in digests
    ):
        raise RuntimeError("training ingress digest is invalid")
    project_root = project_root.resolve(strict=True)
    engine_root = engine_root.resolve(strict=True)
    requirements = engine_root / "requirements" / "modal-launcher-v1.lock"
    python = launcher_python(project_root)
    marker = os.environ.get(_MARKER)
    if marker is not None:
        if (
            marker != "1"
            or os.environ.get(_INGRESS_DIGEST) != ingress_digest
            or os.environ.get(_CONTRACT_IDENTITY_DIGEST) != contract_identity_digest
        ):
            raise RuntimeError("isolated launcher authority mismatch")
        _body, proof_digest = _runtime_proof(project_root, engine_root)
        if os.environ.get(_RUNTIME_PROOF_DIGEST) != proof_digest:
            raise RuntimeError("isolated launcher runtime proof mismatch")
        if Path(sys.executable).resolve(strict=True) != python.resolve(strict=True):
            raise RuntimeError("isolated Modal launcher interpreter mismatch") from None
        return None
    try:
        _body, proof_digest = _runtime_proof(project_root, engine_root)
    except BaseException:
        _build_runtime(
            project_root=project_root, requirements=requirements,
            expected=_runtime_stamp(requirements),
        )
        _body, proof_digest = _runtime_proof(project_root, engine_root)
    environment: dict[str, str] = {}
    for name in _ALLOWED_CHILD_ENV:
        value = os.environ.get(name)
        if value is None:
            continue
        snapshot = _validated_child_environment_value(value)
        if snapshot is None:
            raise RuntimeError("child environment value is invalid")
        environment[name] = snapshot
    modal_credentials: dict[str, str] = {}
    for name in _MODAL_CREDENTIAL_ENV:
        value = os.environ.get(name)
        snapshot = _validated_child_environment_value(value)
        if snapshot is None:
            modal_credentials.clear()
            break
        modal_credentials[name] = snapshot
    if len(modal_credentials) == len(_MODAL_CREDENTIAL_ENV):
        environment.update(modal_credentials)
    environment[_MARKER] = "1"
    environment[_INGRESS_DIGEST] = ingress_digest
    environment[_CONTRACT_IDENTITY_DIGEST] = contract_identity_digest
    environment[_RUNTIME_PROOF_DIGEST] = proof_digest
    _final_body, final_proof_digest = _runtime_proof(project_root, engine_root)
    if final_proof_digest != proof_digest:
        raise RuntimeError("launcher runtime proof changed before spawn")
    completed = subprocess.run(
        [
            str(python), "-I", "-c", _FIXED_BOOTSTRAP,
            str(project_root), str(engine_root), *argv,
        ],
        cwd=project_root, env=environment, check=False,
    )
    return completed.returncode
