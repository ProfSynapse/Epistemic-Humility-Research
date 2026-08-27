#!/usr/bin/env python3
"""Task-backlog lifecycle CLI for the Epistemic-Humility-Research repo.

One markdown file per task lives under ``backlog/tasks`` (active),
``backlog/drafts`` (draft), or ``backlog/completed`` (done, archived). Each file
is a YAML frontmatter block (the machine state) followed by three body
sections: ``## Description``, ``## Acceptance Criteria``, ``## Work Log``. IDs
are random 6-hex strings minted ONLY by this CLI (``new``), so parallel
worktrees never collide on merge.

This module is stdlib + PyYAML only, deterministic, and exercised both through
``bin/task`` and directly in tests. Every core function takes an explicit repo
``root`` so tests can drive it against a temporary tree.

Subcommands: new, list, show, claim, release, review, done, validate.

Tasks point at experiments (via the optional ``experiment:`` field); they never
duplicate an experiment's own lifecycle, which stays governed by ``bin/exp`` and
its ``experiments/<slug>/AMENDMENT.md``. ``validate`` enforces the rot-killer
cross-check: a task that is still open (draft/todo/in-progress/in-review) but
bound to an experiment that has reached a terminal status is a backlog rot and
fails validation until the task is closed.
"""

from __future__ import annotations

import argparse
import re
import secrets
import sys
from datetime import date
from pathlib import Path

import yaml

BACKLOG_DIRNAME = "backlog"
TASK_DIRS = ("tasks", "drafts", "completed")

STATUSES = ("draft", "todo", "in-progress", "in-review", "done")
TIERS = ("A", "L", "P")
PRIORITIES = ("high", "medium", "low")
PRIORITY_ORDER = {p: i for i, p in enumerate(PRIORITIES)}

# Task statuses that count as "still open" for the rot-killer cross-check.
OPEN_TASK_STATUSES = frozenset({"draft", "todo", "in-progress", "in-review"})

# Experiment statuses (read from experiments/<slug>/experiment.yaml's `status:`)
# that mean the bound experiment is closed out. `shelved` is not currently a
# value exp.py's own STATUSES enum accepts, but is included here for forward
# compatibility with the legacy shelved vocabulary (see TODO.md's amendment
# index) should it ever be reintroduced as a manifest status.
TERMINAL_EXPERIMENT_STATUSES = frozenset(
    {"resolved", "null-result", "falsified", "historical", "shelved"}
)

ID_RE = re.compile(r"^task-[0-9a-f]{6}$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)

# Stable key order for every frontmatter dump.
FRONTMATTER_FIELDS = (
    "id",
    "title",
    "status",
    "assignee",
    "tier",
    "priority",
    "experiment",
    "component",
    "depends_on",
    "files",
    "new_files",
    "blocker",
    "created_date",
    "updated_date",
)
_DEFAULT_FOR = {
    "assignee": [],
    "experiment": "",
    "component": "",
    "depends_on": [],
    "files": [],
    "new_files": [],
    "blocker": "",
}

BODY_TEMPLATE = """## Description


## Acceptance Criteria
- [ ]

## Work Log
"""


class TaskError(Exception):
    """A user-facing error; the CLI prints the message and exits non-zero."""


# --- repo / path discovery ---------------------------------------------------


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (or cwd) until a dir holds a ``.git`` entry.

    Worktrees keep a ``.git`` file rather than a directory, so we accept either.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    raise TaskError(f"no git repo root found above {here}")


def backlog_dir(root: Path) -> Path:
    return root / BACKLOG_DIRNAME


def today() -> str:
    return date.today().isoformat()


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:40].strip("-")
    return slug or "task"


def mint_id(existing_ids: set[str]) -> str:
    while True:
        candidate = f"task-{secrets.token_hex(3)}"
        if candidate not in existing_ids:
            return candidate


# --- frontmatter IO ------------------------------------------------------


def _split(text: str, path: Path) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise TaskError(f"{path}: malformed task file (missing YAML frontmatter)")
    fm_text, body = m.group(1), m.group(2)
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        raise TaskError(f"{path}: invalid frontmatter YAML ({exc})") from exc
    if not isinstance(data, dict):
        raise TaskError(f"{path}: frontmatter is not a mapping")
    return data, body


def _render(data: dict, body: str) -> str:
    ordered = {k: data.get(k, _DEFAULT_FOR.get(k, "")) for k in FRONTMATTER_FIELDS}
    fm_text = yaml.safe_dump(
        ordered, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    return f"---\n{fm_text}---\n{body}"


def load_task(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data, body = _split(text, path)
    data["_path"] = path
    data["_body"] = body
    return data


def write_task(path: Path, data: dict, body: str) -> None:
    path.write_text(_render(data, body), encoding="utf-8")


def iter_tasks(root: Path) -> list[dict]:
    """Every task across tasks/drafts/completed, sorted by (dir, filename)."""
    out: list[dict] = []
    base = backlog_dir(root)
    for d in TASK_DIRS:
        abs_dir = base / d
        if not abs_dir.is_dir():
            continue
        for f in sorted(abs_dir.glob("task-*.md")):
            t = load_task(f)
            t["_dir"] = d
            out.append(t)
    return out


def find_task(root: Path, task_id: str) -> dict:
    for t in iter_tasks(root):
        if t.get("id") == task_id:
            return t
    raise TaskError(f"no task with id {task_id}")


# --- validation ------------------------------------------------------------


def _experiment_status(root: Path, slug: str) -> str | None:
    manifest = root / "experiments" / slug / "experiment.yaml"
    if not manifest.is_file():
        return None
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    return status if isinstance(status, str) else None


def _validate_one(root: Path, t: dict, all_ids: set[str]) -> list[str]:
    errors: list[str] = []
    tid = t.get("id") or f"<{Path(t['_path']).name}>"

    def err(msg: str) -> None:
        errors.append(f"{tid}: {msg}")

    if not ID_RE.match(str(t.get("id") or "")):
        err(f"invalid id {t.get('id')!r} (want task-<6hex>)")
    if t.get("status") not in STATUSES:
        err(f"invalid status {t.get('status')!r} (want one of {STATUSES})")
    if t.get("tier") not in TIERS:
        err(f"invalid tier {t.get('tier')!r} (want one of {TIERS})")
    if t.get("priority") not in PRIORITIES:
        err(f"invalid priority {t.get('priority')!r} (want one of {PRIORITIES})")

    for dep in t.get("depends_on") or []:
        if dep not in all_ids:
            err(f"unknown depends_on {dep!r}")

    for f in t.get("files") or []:
        if not (root / f).exists():
            err(f"files: {f!r} does not exist")

    component = t.get("component") or ""
    if component and component != "." and not (root / component).exists():
        err(f"component {component!r} does not exist")

    experiment = t.get("experiment") or ""
    if experiment:
        exp_dir = root / "experiments" / experiment
        manifest = exp_dir / "experiment.yaml"
        if not exp_dir.is_dir():
            err(f"experiment {experiment!r} does not exist under experiments/")
        elif not manifest.is_file():
            err(f"experiment {experiment!r} has no experiment.yaml")
        else:
            exp_status = _experiment_status(root, experiment)
            if (
                t.get("status") in OPEN_TASK_STATUSES
                and exp_status in TERMINAL_EXPERIMENT_STATUSES
            ):
                err(
                    f"bound experiment {experiment!r} is terminal "
                    f"({exp_status}) but task is still {t.get('status')!r} -- "
                    f"close it (`bin/task done {tid}` or `bin/task release "
                    f"{tid}`)"
                )

    return errors


def _find_cycle(depends_map: dict[str, list[str]]) -> list[str] | None:
    """DFS cycle search over the depends_on graph; returns the cycle path."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in depends_map}
    stack_path: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GRAY
        stack_path.append(node)
        for nxt in depends_map.get(node, []):
            if nxt not in color:
                continue  # unknown id; reported separately by _validate_one
            if color[nxt] == GRAY:
                idx = stack_path.index(nxt)
                return stack_path[idx:] + [nxt]
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack_path.pop()
        color[node] = BLACK
        return None

    for node in list(depends_map):
        if color[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def validate_all(root: Path) -> list[str]:
    errors: list[str] = []
    tasks = iter_tasks(root)

    seen: dict[str, list[Path]] = {}
    depends_map: dict[str, list[str]] = {}
    for t in tasks:
        tid = t.get("id")
        seen.setdefault(tid, []).append(t["_path"])
        depends_map[tid] = list(t.get("depends_on") or [])

    all_ids = set(seen)
    for tid, paths in seen.items():
        if len(paths) > 1:
            errors.append(
                f"duplicate id {tid}: " + ", ".join(str(p) for p in paths)
            )

    for t in tasks:
        errors.extend(_validate_one(root, t, all_ids))

    cycle = _find_cycle(depends_map)
    if cycle:
        errors.append("depends_on cycle: " + " -> ".join(cycle))

    return errors


def _unmet_deps(t: dict, by_id: dict[str, dict]) -> list[str]:
    return [
        d for d in (t.get("depends_on") or []) if by_id.get(d, {}).get("status") != "done"
    ]


def _revalidate_and_report(root: Path, message: str) -> int:
    errors = validate_all(root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 2
    print(message)
    return 0


# --- commands ----------------------------------------------------------------


def cmd_new(
    root: Path,
    title: str,
    *,
    tier: str,
    priority: str,
    assignee: list[str] | None = None,
    experiment: str | None = None,
    component: str | None = None,
    depends_on: list[str] | None = None,
    files: list[str] | None = None,
    new_files: list[str] | None = None,
    blocker: str | None = None,
    draft: bool = False,
) -> int:
    existing_ids = {t["id"] for t in iter_tasks(root)}
    task_id = mint_id(existing_ids)
    slug = slugify(title)
    dirname = "drafts" if draft else "tasks"
    status = "draft" if draft else "todo"
    dest_dir = backlog_dir(root) / dirname
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{task_id}-{slug}.md"

    data = {
        "id": task_id,
        "title": title,
        "status": status,
        "assignee": assignee or [],
        "tier": tier,
        "priority": priority,
        "experiment": experiment or "",
        "component": component or "",
        "depends_on": depends_on or [],
        "files": files or [],
        "new_files": new_files or [],
        "blocker": blocker or "",
        "created_date": today(),
        "updated_date": today(),
    }
    write_task(path, data, BODY_TEMPLATE)

    errors = validate_all(root)
    if errors:
        path.unlink(missing_ok=True)
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"created {path.relative_to(root)}")
    return 0


def cmd_list(root: Path) -> int:
    tasks = iter_tasks(root)
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        blocked = ""
        if t.get("status") != "done":
            unmet = _unmet_deps(t, by_id)
            if unmet:
                blocked = f"  [blocked by: {', '.join(unmet)}]"
        assignees = ",".join(t.get("assignee") or [])
        print(
            f"{t['id']}  {str(t.get('status') or ''):<11} "
            f"{assignees:<12} {t.get('title') or ''}{blocked}"
        )
    return 0


def cmd_show(root: Path, task_id: str) -> int:
    t = find_task(root, task_id)
    by_id = {x["id"]: x for x in iter_tasks(root)}

    print(f"# {t['id']} -- {t.get('title', '')}")
    assignee = ", ".join(t.get("assignee") or [])
    print(f"status: {t.get('status')}" + (f"  assignee: {assignee}" if assignee else ""))
    print(f"tier: {t.get('tier')}  priority: {t.get('priority')}")
    if t.get("experiment"):
        exp_status = _experiment_status(root, t["experiment"])
        print(f"experiment: {t['experiment']} (status: {exp_status or 'unknown'})")
    if t.get("component"):
        print(f"component: {t['component']}")
    if t.get("blocker"):
        print(f"blocker: {t['blocker']}")
    for d in t.get("depends_on") or []:
        dep = by_id.get(d)
        status = dep["status"] if dep else "?"
        flag = "  [unfinished]" if (not dep or dep.get("status") != "done") else ""
        print(f"depends on: {d} ({status}){flag}")
    if t.get("files"):
        print("existing files in scope:")
        for f in t["files"]:
            flag = "" if (root / f).exists() else "  [MISSING]"
            print(f"  {f}{flag}")
    if t.get("new_files"):
        print("planned files:")
        for f in t["new_files"]:
            already = (not f.endswith("/")) and (root / f).exists()
            flag = "  [already exists -- move to files:]" if already else ""
            print(f"  {f}{flag}")
    print()
    print((t.get("_body") or "").strip())
    return 0


def cmd_claim(root: Path, task_id: str, who: str) -> int:
    t = find_task(root, task_id)
    if t.get("status") == "done":
        print(f"error: {task_id} is done", file=sys.stderr)
        return 2
    assignees = t.get("assignee") or []
    if assignees and who not in assignees:
        print(
            f"error: {task_id} is already claimed by {', '.join(assignees)} "
            "-- release it first or hand it off",
            file=sys.stderr,
        )
        return 2

    by_id = {x["id"]: x for x in iter_tasks(root)}
    unmet = _unmet_deps(t, by_id)
    if unmet:
        print(f"warning: {task_id} is blocked by unfinished {', '.join(unmet)}", file=sys.stderr)

    t["status"] = "in-progress"
    t["assignee"] = [who]
    t["updated_date"] = today()
    write_task(t["_path"], t, t["_body"])
    return _revalidate_and_report(root, f"{task_id} claimed by {who} (in-progress)")


def cmd_release(root: Path, task_id: str) -> int:
    t = find_task(root, task_id)
    t["status"] = "todo"
    t["assignee"] = []
    t["updated_date"] = today()
    write_task(t["_path"], t, t["_body"])
    return _revalidate_and_report(root, f"{task_id} released (todo, unassigned)")


def cmd_review(root: Path, task_id: str) -> int:
    t = find_task(root, task_id)
    t["status"] = "in-review"
    t["updated_date"] = today()
    write_task(t["_path"], t, t["_body"])
    return _revalidate_and_report(root, f"{task_id} -> in-review")


def cmd_done(root: Path, task_id: str) -> int:
    t = find_task(root, task_id)
    t["status"] = "done"
    t["updated_date"] = today()
    write_task(t["_path"], t, t["_body"])
    dest_dir = backlog_dir(root) / "completed"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / t["_path"].name
    t["_path"].rename(dest)
    return _revalidate_and_report(root, f"{task_id} -> done, archived to backlog/completed/")


def cmd_validate(root: Path) -> int:
    errors = validate_all(root)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print(f"validate: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"validate: OK -- {len(iter_tasks(root))} task(s)")
    return 0


# --- CLI -----------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task", description="Task-backlog lifecycle CLI (draft/todo -> in-progress -> in-review -> done)."
    )
    parser.add_argument(
        "--root", default=None,
        help="repo root (default: discovered by walking up to the git root).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="mint a task id and write a new task file")
    p_new.add_argument("title")
    p_new.add_argument("--tier", required=True, choices=TIERS)
    p_new.add_argument("--priority", default="medium", choices=PRIORITIES)
    p_new.add_argument("--assignee", action="append", default=[])
    p_new.add_argument("--experiment", default=None)
    p_new.add_argument("--component", default=None)
    p_new.add_argument("--depends-on", dest="depends_on", action="append", default=[])
    p_new.add_argument("--file", dest="files", action="append", default=[])
    p_new.add_argument("--new-file", dest="new_files", action="append", default=[])
    p_new.add_argument("--blocker", default=None)
    p_new.add_argument("--draft", action="store_true", help="write to backlog/drafts/ with status draft")

    sub.add_parser("list", help="table of all tasks, blocked ones flagged")

    p_show = sub.add_parser("show", help="full working context for one task")
    p_show.add_argument("id")

    p_claim = sub.add_parser("claim", help="check out: draft/todo -> in-progress")
    p_claim.add_argument("id")
    p_claim.add_argument("--as", dest="who", default="@agent", help="assignee handle")

    p_release = sub.add_parser("release", help="check in unfinished: -> todo, unassigned")
    p_release.add_argument("id")

    p_review = sub.add_parser("review", help="-> in-review (PR open)")
    p_review.add_argument("id")

    p_done = sub.add_parser("done", help="-> done, archived to backlog/completed/")
    p_done.add_argument("id")

    sub.add_parser("validate", help="validate every task under backlog/")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve() if args.root else find_repo_root()
        if args.command == "new":
            return cmd_new(
                root,
                args.title,
                tier=args.tier,
                priority=args.priority,
                assignee=args.assignee,
                experiment=args.experiment,
                component=args.component,
                depends_on=args.depends_on,
                files=args.files,
                new_files=args.new_files,
                blocker=args.blocker,
                draft=args.draft,
            )
        if args.command == "list":
            return cmd_list(root)
        if args.command == "show":
            return cmd_show(root, args.id)
        if args.command == "claim":
            return cmd_claim(root, args.id, args.who)
        if args.command == "release":
            return cmd_release(root, args.id)
        if args.command == "review":
            return cmd_review(root, args.id)
        if args.command == "done":
            return cmd_done(root, args.id)
        if args.command == "validate":
            return cmd_validate(root)
    except TaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.command!r}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
