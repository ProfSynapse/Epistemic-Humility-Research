"""Text-free public commitments; Git writes remain the lead's responsibility."""

import json
import subprocess

from .util import HarnessError, write_json


def public_path(layout, name):
    return layout.project_root / "experiments" / layout.slug / "analysis-committed" / name


def export(layout, name, document):
    path = public_path(layout, name)
    write_json(path, document)
    return path


def require_git(layout, name, expected):
    """Require these exact JSON bytes in a reachable commit, locally or fetched.

    An execution snapshot can fetch the lead's evidence commit without swapping
    its live source tree. A private append log or an untracked file is insufficient.
    """
    path = public_path(layout, name)
    if not path.is_file() or json.loads(path.read_text()) != expected:
        raise HarnessError("PUBLIC_COMMITMENT", f"public {name} is missing or differs from the private commitment")
    relative = path.relative_to(layout.project_root).as_posix()
    result = subprocess.run(["git", "-C", str(layout.project_root), "log", "--all", "--format=%H", "--", relative],
                            capture_output=True, text=True, check=False)
    if result.returncode == 0:
        for commit in result.stdout.splitlines():
            blob = subprocess.run(["git", "-C", str(layout.project_root), "show", f"{commit}:{relative}"],
                                  capture_output=True, check=False)
            if blob.returncode == 0 and blob.stdout == path.read_bytes():
                return commit
    raise HarnessError("PUBLIC_NOT_IN_GIT", f"commit {relative} before proceeding; the harness never commits it for you")
