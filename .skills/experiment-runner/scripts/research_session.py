#!/usr/bin/env python3
"""Create, append, and validate durable research-session memory notes.

Sessions are checked-in Markdown files under docs/sessions/ with YAML
frontmatter. The frontmatter is the structured source of truth; the Markdown body
keeps the same checkpoints readable for humans and Obsidian.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "research-session/v1"
SESSION_ROOT = Path("docs") / "sessions"
VALID_STATUS = {"active", "paused", "complete", "superseded"}
VALID_KINDS = {
    "planning",
    "gate",
    "launch",
    "observation",
    "decision",
    "result",
    "blocker",
    "handoff",
    "checkpoint",
    "recovery",
    "validation",
    "heartbeat",
    "interpretation",
    "amendment",
    "infrastructure",
}
SESSION_ID_RE = re.compile(r"^(?:[a-z0-9][a-z0-9_.-]*|\d{8}T\d{6}Z-[a-z0-9][a-z0-9_.-]*)$")
LEGACY_SESSION_FILENAME_RE = re.compile(r"^\d{4} - [a-z0-9][a-z0-9-]*\.md$")
TIMESTAMP_SESSION_FILENAME_RE = re.compile(r"^\d{8}T\d{6}Z-[a-z0-9][a-z0-9_.-]*\.md$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)


class SessionError(Exception):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_list(values: list[str] | None) -> list[str]:
    return [value for value in values or [] if value]


def slugify_title(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "session"


def filename_timestamp(value: str | None = None) -> str:
    """Return a compact UTC timestamp suitable for a filename."""
    stamp = value or now_utc()
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$", stamp)
    if not match:
        raise SessionError(f"timestamp must be UTC ISO-8601 like 2026-07-08T17:15:28Z: {stamp}")
    return "".join(match.groups()[:3]) + "T" + "".join(match.groups()[3:]) + "Z"


def default_session_id(title: str, *, timestamp: str | None = None) -> str:
    return f"{filename_timestamp(timestamp)}-{slugify_title(title)}"


def next_session_number(root: Path = Path(".")) -> str:
    session_dir = root / SESSION_ROOT
    highest = 0
    if session_dir.is_dir():
        for path in session_dir.glob("*.md"):
            match = re.match(r"^(\d{4}) - ", path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"{highest + 1:04d}"


def default_session_path(
    session_id: str,
    title: str | None = None,
    root: Path = Path("."),
    *,
    filename_mode: str = "timestamp",
    timestamp: str | None = None,
) -> Path:
    if filename_mode == "timestamp":
        if TIMESTAMP_SESSION_FILENAME_RE.match(f"{session_id}.md"):
            filename_stem = session_id
        else:
            filename_stem = f"{filename_timestamp(timestamp)}-{session_id}"
        return root / SESSION_ROOT / f"{filename_stem}.md"
    if filename_mode == "numbered":
        filename_title = slugify_title(title or session_id)
        return root / SESSION_ROOT / f"{next_session_number(root)} - {filename_title}.md"
    raise SessionError("filename_mode must be 'timestamp' or 'numbered'")


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise SessionError("session note must start with YAML frontmatter")
    frontmatter = yaml.safe_load(match.group("body")) or {}
    if not isinstance(frontmatter, dict):
        raise SessionError("session frontmatter must be a YAML mapping")
    return frontmatter, text[match.end() :]


def load_session(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise SessionError(f"session file does not exist: {path}")
    return split_frontmatter(path.read_text(encoding="utf-8"))


def render_frontmatter(data: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip() + "\n---\n"


def render_initial_body(data: dict[str, Any]) -> str:
    return (
        f"# {data['title']}\n\n"
        "## Question\n\n"
        f"{data['question']}\n\n"
        "## Trajectory Position\n\n"
        f"{data['trajectory'].get('current_position') or '_Not yet recorded._'}\n\n"
        "## Summary\n\n"
        "_No summary yet._\n\n"
        "## Checkpoints\n"
    )


def render_checkpoint(checkpoint: dict[str, Any]) -> str:
    lines = [
        "",
        f"### {checkpoint['id']} - {checkpoint['title']}",
        "",
        f"- at: `{checkpoint['at']}`",
        f"- kind: `{checkpoint['kind']}`",
        f"- summary: {checkpoint['summary']}",
    ]
    for key, label in (
        ("run_ids", "run ids"),
        ("evidence", "evidence"),
        ("commands", "commands"),
        ("decisions", "decisions"),
        ("next_steps", "next steps"),
    ):
        values = checkpoint.get(key) or []
        if values:
            lines.append(f"- {label}:")
            lines.extend(f"  - `{value}`" if key in {"evidence", "commands", "run_ids"} else f"  - {value}" for value in values)
    signals = checkpoint.get("signals") or {}
    if signals:
        lines.append("- signals:")
        for signal, values in signals.items():
            lines.append(f"  - {signal}:")
            lines.extend(f"    - `{value}`" for value in values)
    lines.append("")
    return "\n".join(lines)


def write_session(path: Path, data: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_frontmatter(data) + body.lstrip(), encoding="utf-8")


def create_session(
    path: Path,
    *,
    session_id: str,
    title: str,
    question: str,
    phase: str = "",
    status: str = "active",
    tags: list[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    if not SESSION_ID_RE.match(session_id):
        raise SessionError(
            "session_id must be lowercase alnum plus '.', '_', or '-' "
            "or a generated YYYYMMDDTHHMMSSZ-<title-slug> id"
        )
    if status not in VALID_STATUS:
        raise SessionError(f"invalid status {status!r}; expected one of {sorted(VALID_STATUS)}")
    if path.exists() and not overwrite:
        raise SessionError(f"session file already exists: {path}")
    timestamp = now_utc()
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "title": title,
        "status": status,
        "created_at": timestamp,
        "updated_at": timestamp,
        "question": question,
        "tags": normalize_list(tags),
        "run_ids": [],
        "trajectory": {
            "anchor": "experiment/protocol/research-trajectory.md",
            "current_position": "",
            "changed_by_session": "",
        },
        "checkpoints": [],
    }
    if phase:
        data["phase"] = phase
    write_session(path, data, render_initial_body(data))
    return data


def checkpoint_id(data: dict[str, Any], kind: str) -> str:
    return f"{len(data.get('checkpoints') or []) + 1:03d}-{kind}"


def append_checkpoint(
    path: Path,
    *,
    kind: str,
    title: str | None = None,
    summary: str,
    evidence: list[str] | None = None,
    run_ids: list[str] | None = None,
    commands: list[str] | None = None,
    decisions: list[str] | None = None,
    next_steps: list[str] | None = None,
    status: str | None = None,
    signals: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    if kind not in VALID_KINDS:
        raise SessionError(f"invalid checkpoint kind {kind!r}; expected one of {sorted(VALID_KINDS)}")
    data, body = load_session(path)
    errors = validate_session(data, path=path)
    if errors:
        raise SessionError("; ".join(errors))
    checkpoint = {
        "id": checkpoint_id(data, kind),
        "at": now_utc(),
        "kind": kind,
        "title": title or kind.replace("_", " ").title(),
        "summary": summary,
        "evidence": normalize_list(evidence),
        "run_ids": normalize_list(run_ids),
        "commands": normalize_list(commands),
        "decisions": normalize_list(decisions),
        "next_steps": normalize_list(next_steps),
        "signals": signals or {},
    }
    data.setdefault("checkpoints", []).append(checkpoint)
    data["run_ids"] = list(dict.fromkeys([*(data.get("run_ids") or []), *checkpoint["run_ids"]]))
    if status is not None:
        if status not in VALID_STATUS:
            raise SessionError(f"invalid status {status!r}; expected one of {sorted(VALID_STATUS)}")
        data["status"] = status
    data["updated_at"] = checkpoint["at"]
    write_session(path, data, body.rstrip() + render_checkpoint(checkpoint))
    return data


def validate_session(data: dict[str, Any], *, path: Path | None = None) -> list[str]:
    errors: list[str] = []
    location = f"{path}: " if path else ""
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{location}schema_version must be {SCHEMA_VERSION!r}")
    if (
        path is not None
        and path.parent.name == "sessions"
        and not (
            LEGACY_SESSION_FILENAME_RE.match(path.name)
            or TIMESTAMP_SESSION_FILENAME_RE.match(path.name)
        )
    ):
        errors.append(
            f"{location}filename must match 'YYYYMMDDTHHMMSSZ-session-id.md' "
            "or legacy '0001 - session-title.md'"
        )
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID_RE.match(session_id):
        errors.append(
            f"{location}session_id must be lowercase alnum plus '.', '_', or '-' "
            "or a generated YYYYMMDDTHHMMSSZ-<title-slug> id"
        )
    if not data.get("title"):
        errors.append(f"{location}title is required")
    if data.get("status") not in VALID_STATUS:
        errors.append(f"{location}status must be one of {sorted(VALID_STATUS)}")
    for key in ("created_at", "updated_at", "question"):
        if not data.get(key):
            errors.append(f"{location}{key} is required")
    trajectory = data.get("trajectory")
    if not isinstance(trajectory, dict) or not trajectory.get("anchor"):
        errors.append(f"{location}trajectory.anchor is required")
    checkpoints = data.get("checkpoints")
    if not isinstance(checkpoints, list):
        errors.append(f"{location}checkpoints must be a list")
        return errors
    seen_ids: set[str] = set()
    for idx, checkpoint in enumerate(checkpoints):
        prefix = f"{location}checkpoints[{idx}]"
        if not isinstance(checkpoint, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        cid = checkpoint.get("id")
        if not cid:
            errors.append(f"{prefix}.id is required")
        elif cid in seen_ids:
            errors.append(f"{prefix}.id duplicates {cid!r}")
        else:
            seen_ids.add(str(cid))
        if checkpoint.get("kind") not in VALID_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(VALID_KINDS)}")
        if not checkpoint.get("title"):
            errors.append(f"{prefix}.title is required")
        if not checkpoint.get("at"):
            errors.append(f"{prefix}.at is required")
        if not checkpoint.get("summary"):
            errors.append(f"{prefix}.summary is required")
        for list_key in ("evidence", "run_ids", "commands", "decisions", "next_steps"):
            if not isinstance(checkpoint.get(list_key, []), list):
                errors.append(f"{prefix}.{list_key} must be a list")
        if not isinstance(checkpoint.get("signals", {}), dict):
            errors.append(f"{prefix}.signals must be a mapping")
    return errors


def iter_session_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.glob("*.md") if item.name.upper() != "README.MD")
    raise SessionError(f"path does not exist: {path}")


def validate_path(path: Path) -> list[str]:
    errors: list[str] = []
    files = iter_session_files(path)
    seen_session_ids: dict[str, Path] = {}
    for session_file in files:
        data, _ = load_session(session_file)
        errors.extend(validate_session(data, path=session_file))
        session_id = data.get("session_id")
        if isinstance(session_id, str) and session_id:
            previous = seen_session_ids.get(session_id)
            if previous is not None:
                errors.append(
                    f"{session_file}: session_id {session_id!r} duplicates {previous}"
                )
            else:
                seen_session_ids[session_id] = session_file
    return errors


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage durable research-session memory notes.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="Create a new research session note.")
    init.add_argument(
        "--session-id",
        help="Durable session id. Defaults to YYYYMMDDTHHMMSSZ-<title-slug>.",
    )
    init.add_argument("--title", required=True)
    init.add_argument("--question", required=True)
    init.add_argument("--phase", default="", help=argparse.SUPPRESS)
    init.add_argument("--status", choices=sorted(VALID_STATUS), default="active")
    init.add_argument("--tag", action="append", default=[])
    init.add_argument(
        "--filename-mode",
        choices=["timestamp", "numbered"],
        default="timestamp",
        help="Default output filename style when --path is omitted (default: timestamp).",
    )
    init.add_argument("--path", help="Output path. Defaults to docs/sessions/<generated-session-id>.md.")
    init.add_argument("--overwrite", action="store_true")

    checkpoint = sub.add_parser("checkpoint", help="Append a checkpoint to a session.")
    checkpoint.add_argument("--session", required=True)
    checkpoint.add_argument("--kind", choices=sorted(VALID_KINDS), default="checkpoint")
    checkpoint.add_argument("--title", help="Human-readable checkpoint title.")
    checkpoint.add_argument("--summary", required=True)
    checkpoint.add_argument("--evidence", action="append", default=[])
    checkpoint.add_argument("--run-id", action="append", default=[])
    checkpoint.add_argument("--command", action="append", default=[])
    checkpoint.add_argument("--decision", action="append", default=[])
    checkpoint.add_argument("--next-step", action="append", default=[])
    checkpoint.add_argument("--status", choices=sorted(VALID_STATUS))

    validate = sub.add_parser("validate", help="Validate one session note or a directory.")
    validate.add_argument("path", nargs="?", default=str(SESSION_ROOT))
    validate.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.cmd == "init":
            session_id = args.session_id or default_session_id(args.title)
            path = Path(args.path) if args.path else default_session_path(
                session_id,
                args.title,
                filename_mode=args.filename_mode,
            )
            data = create_session(
                path,
                session_id=session_id,
                title=args.title,
                question=args.question,
                phase=args.phase,
                status=args.status,
                tags=args.tag,
                overwrite=args.overwrite,
            )
            print(json.dumps({"path": path.as_posix(), "session_id": data["session_id"]}, indent=2))
            return 0
        if args.cmd == "checkpoint":
            append_checkpoint(
                Path(args.session),
                kind=args.kind,
                title=args.title,
                summary=args.summary,
                evidence=args.evidence,
                run_ids=args.run_id,
                commands=args.command,
                decisions=args.decision,
                next_steps=args.next_step,
                status=args.status,
            )
            print(json.dumps({"path": args.session, "checkpoint": "appended"}, indent=2))
            return 0
        if args.cmd == "validate":
            errors = validate_path(Path(args.path))
            if args.json:
                print(json.dumps({"errors": errors}, indent=2))
            elif errors:
                print("Research session validation failed:")
                for error in errors:
                    print(f"- {error}")
            else:
                print("Research session validation passed.")
            return 1 if errors else 0
    except SessionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
