"""The source-pinned CLI boundary for operations absent from API v1.

Calling a CLI is not a public Python API import. No runtime source paths are
added to Python's import path, and no host authority flags are inserted.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .engine_identity import inspect_engine


_MECHINTERP = frozenset({"run", "list-configs", "extract", "probe-fit", "steer", "dose-calibrate", "score-gates", "weights-inspect", "weights-patch"})
_BATCH = frozenset({"batch-generate", "batch-capture"})
_RESERVED = frozenset({"--project-root", "--manifest", "--base-dir", "--env-file"})


class EngineCLI:
    def __init__(self, project_root: Path, *, plugin_roots=()):
        self.project_root = Path(project_root).resolve()
        self.identity = inspect_engine(self.project_root)
        if not self.identity["wheel_pin_verified"]:
            raise ValueError("the experimental CLI requires a reviewed engine.wheel_sha256 pin")
        cli_requirement = self.identity["cli_requires"]
        if not isinstance(cli_requirement, str) or not cli_requirement.startswith("==") or "*" in cli_requirement:
            raise ValueError("the nonstable CLI requires an exact engine version pin")
        if not SpecifierSet(cli_requirement).contains(Version(self.identity["version"]), prereleases=True):
            raise ValueError("installed engine does not satisfy the CLI pin")
        self.plugin_roots = tuple(Path(p).resolve() for p in plugin_roots)
        if any(not p.is_relative_to(self.project_root) for p in self.plugin_roots):
            raise ValueError("project plug-in roots must belong to the host project")
        for root in (self.project_root, *self.plugin_roots):
            for name in ("tuner", "synaptic_tuner", "MechInterp", "shared", "Trainers", "Evaluator", "SynthChat", "schemas", "engine_host"):
                if (root / name).exists() or (root / (name + ".py")).exists():
                    raise ValueError("a project plug-in root shadows an installed package")

    def command(self, operation: str, arguments=()) -> list[str]:
        arguments = list(arguments)
        if operation == "mechinterp":
            if not arguments or arguments[0] not in _MECHINTERP:
                raise ValueError("unsupported mechinterp operation")
        elif operation not in _BATCH | {"project", "capabilities"}:
            raise ValueError("use public APIs for this operation")
        if any(a.startswith("--") and any(flag.startswith(a.split("=", 1)[0])
                                          for flag in _RESERVED) for a in arguments):
            raise ValueError("project selection belongs to the host boundary")
        return [sys.executable, "-m", "tuner", operation, *arguments,
                "--project-root", str(self.project_root),
                "--manifest", str(self.project_root / "synaptic.yaml")]

    def run(self, operation: str, arguments=(), *, timeout=None, stdout=None, stderr=None,
            guard_parent=False, pass_fds=()):
        environment = os.environ.copy()
        if environment.get("EHR_HOST_CONFIG"):
            from .storage import configure_storage
            environment.update(configure_storage(self.project_root, Path(environment["EHR_HOST_CONFIG"])))
        # Only project plug-ins are added. Never inherit a path to engine internals.
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
        environment["PATH"] = os.pathsep.join((str(Path(sys.executable).parent), environment.get("PATH", "")))
        if self.plugin_roots:
            environment["PYTHONPATH"] = os.pathsep.join(map(str, self.plugin_roots))
        command = self.command(operation, arguments)
        if guard_parent:
            if not sys.platform.startswith("linux"):
                raise ValueError("guarded GPU CLI execution requires the qualified Linux host")
            command = [sys.executable, "-m", "engine_host.exec_guard", str(os.getpid()), "--", *command]
        return subprocess.run(command, cwd=self.project_root, env=environment, check=True,
                              timeout=timeout, stdout=stdout, stderr=stderr, pass_fds=tuple(pass_fds))

    def plan_pipeline(self, config: str):
        return self.run("mechinterp", ["run", "--config", config, "--provider", "local", "--dry-run", "--json"])
