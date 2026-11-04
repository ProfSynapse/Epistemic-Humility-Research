"""Small shared helpers: hashing, atomic writes, JSONL, intervals."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


class HarnessError(RuntimeError):
    """A refusal or stop condition. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, chunk: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_sha256(obj: Any) -> str:
    return sha256_bytes(canonical_json(obj).encode("utf-8"))


def atomic_write_bytes(path: str | Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def atomic_write_text(path: str | Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def write_json(path: str | Path, obj: Any) -> str:
    """Write stable pretty JSON atomically and return its sha256."""
    data = (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    atomic_write_bytes(path, data)
    return sha256_bytes(data)


def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def write_yaml(path: str | Path, obj: Any) -> str:
    data = yaml.safe_dump(obj, sort_keys=False, default_flow_style=False).encode("utf-8")
    atomic_write_bytes(path, data)
    return sha256_bytes(data)


def read_jsonl(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iter_jsonl(path: str | Path) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if line:
                yield json.loads(line)


def count_jsonl(path: str | Path) -> int:
    path = Path(path)
    if not path.exists():
        return 0
    n = 0
    with open(path, "rb") as stream:
        for line in stream:
            if line.strip():
                n += 1
    return n


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> str:
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    atomic_write_bytes(path, data)
    return sha256_bytes(data)


def append_jsonl(path: str | Path, record: dict) -> None:
    """Durable append (flush + fsync) of one JSON record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "ab") as stream:
        stream.write((json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())


_Z95 = 1.959963984540054


def wilson(successes: int, n: int, z: float = _Z95) -> dict:
    """Wilson score interval (same formula as the frozen RR gates_lib)."""
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))) / denom
    return {"n": n, "successes": successes, "rate": phat,
            "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)]}


def rate(records: list[dict], field: str) -> dict:
    return wilson(sum(1 for r in records if bool(r.get(field))), len(records))
