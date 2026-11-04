"""Config-first access to cell.yaml / gates.yaml plus artifact layout.

Nothing numeric is hardcoded here: every constant is read from the locked
cell.yaml / gates.yaml at call time and their sha256 values are stamped into
each manifest, so a post-hoc edit cannot go unnoticed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import EXPERIMENT_SLUG
from .util import HarnessError, sha256_file

EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
CELL_SCHEMA = "ehr-native-weight-edit/v1"
GATES_SCHEMA = "ehr-native-weight-edit-gates/v1"
ROLES = ("confab", "known_correct", "unknown_refused")
# Source-file spellings seen on the desktop (metadata read, 2026-11-03).
SOURCE_ROLE_SPELLING = {
    "confab": "confab",
    "known_correct_answered": "known_correct",
    "unknown_refused": "unknown_refused",
}


def find_project_root(start: Path | None = None) -> Path:
    here = Path(start or EXPERIMENT_DIR).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "synaptic.yaml").is_file():
            return candidate
    raise HarnessError("PROJECT_ROOT", f"no synaptic.yaml above {here}")


@dataclass(frozen=True)
class Cell:
    """Parsed locked configuration."""

    cell: dict
    gates: dict
    cell_sha256: str
    gates_sha256: str
    directory: Path

    @classmethod
    def load(cls, directory: Path | None = None) -> "Cell":
        directory = Path(directory or EXPERIMENT_DIR).resolve()
        cell_path, gates_path = directory / "cell.yaml", directory / "gates.yaml"
        cell = yaml.safe_load(cell_path.read_text(encoding="utf-8"))
        gates = yaml.safe_load(gates_path.read_text(encoding="utf-8"))
        if cell.get("schema_version") != CELL_SCHEMA:
            raise HarnessError("CELL_SCHEMA", f"cell.yaml schema must be {CELL_SCHEMA}")
        if gates.get("schema_version") != GATES_SCHEMA:
            raise HarnessError("GATES_SCHEMA", f"gates.yaml schema must be {GATES_SCHEMA}")
        return cls(cell, gates, sha256_file(cell_path), sha256_file(gates_path), directory)

    # -- derived constants -------------------------------------------------
    @property
    def slug(self) -> str:
        return self.cell["slug"]

    @property
    def revision(self) -> str:
        return self.cell["model"]["revision"]

    @property
    def controller_strength(self) -> float:
        """Absolute c_hat coordinate expressed as erase_write gain (target / sigma_c)."""
        w = self.cell["writer"]
        return float(w["reference_target"]) / float(w["sigma_c"])

    def clamp_setpoint(self, kind: str) -> float:
        """Absolute u_d coordinate: known -> mu_d + z*sigma_d, unknown -> mu_d - z*sigma_d."""
        s, z = self.cell["sensor"], float(self.cell["controls"]["clamp_z"])
        if kind == "known":
            return float(s["mu_d"]) + z * float(s["sigma_d"])
        if kind == "unknown":
            return float(s["mu_d"]) - z * float(s["sigma_d"])
        raise HarnessError("CLAMP_KIND", f"unknown clamp kind {kind!r}")

    def fire(self, proj_d: float) -> dict:
        """Frozen sensor rule: fire iff -clip((proj-mu)/sigma, -2, 2) >= tau."""
        s = self.cell["sensor"]
        z = max(-2.0, min(2.0, (float(proj_d) - float(s["mu_d"])) / float(s["sigma_d"])))
        score = -z
        return {"proj_d": float(proj_d), "z_d": z, "score_neg_z_d": score,
                "fire": bool(score >= float(s["tau"])), "tau": float(s["tau"])}

    def stamp(self) -> dict:
        return {"cell_sha256": self.cell_sha256, "gates_sha256": self.gates_sha256,
                "engine_wheel_sha256": self.cell["engine"]["wheel_sha256"],
                "engine_source_commit": self.cell["engine"]["source_commit"]}


class Layout:
    """Artifact paths. Logical names -> ``artifact://`` refs and local files.

    Everything lives under ``.synaptic/artifacts/<slug>``; a path that would
    escape (``..``, absolute, symlink) is refused.  ``tag`` selects an isolated
    smoke area so smokes never share outputs with the real run.
    """

    def __init__(self, project_root: Path, slug: str = EXPERIMENT_SLUG, *, tag: str | None = None):
        self.project_root = Path(project_root).resolve()
        manifest = yaml.safe_load((self.project_root / "synaptic.yaml").read_text(encoding="utf-8"))
        ref = manifest["paths"]["artifacts"]
        if not ref.startswith("project://"):
            raise HarnessError("LAYOUT", "paths.artifacts must be a project:// reference")
        self.artifacts_root = (self.project_root / ref[len("project://"):]).resolve()
        if not self.artifacts_root.is_relative_to(self.project_root):
            raise HarnessError("LAYOUT", "artifact root escapes the project")
        self.slug = slug
        self.tag = tag
        self.base_rel = slug
        self.run_rel = slug if tag is None else f"{slug}/smoke/{tag}"

    # ------------------------------------------------------------------
    def _check(self, rel: str) -> str:
        rel = rel.strip("/")
        parts = Path(rel).parts
        if not rel or any(p in ("..", "") for p in parts) or Path(rel).is_absolute():
            raise HarnessError("LAYOUT", f"unsafe artifact path {rel!r}")
        return rel

    def ref(self, rel: str, *, shared: bool = False) -> str:
        """``artifact://`` reference. ``shared`` paths ignore the smoke tag, except
        ``materialize/`` rows, which a smoke tree always keeps privately (truncated)."""
        local_rows = self.tag is not None and rel.startswith("materialize/")
        root = self.base_rel if (shared and not local_rows) or self.tag is None else self.run_rel
        return f"artifact://{root}/{self._check(rel)}"

    def local(self, rel: str, *, shared: bool = False) -> Path:
        return self.to_local(self.ref(rel, shared=shared))

    def to_local(self, ref: str) -> Path:
        if not ref.startswith("artifact://"):
            raise HarnessError("LAYOUT", f"not an artifact reference: {ref!r}")
        rel = ref[len("artifact://"):]
        path = (self.artifacts_root / rel)
        self._contained(path)
        return path

    def _contained(self, path: Path) -> None:
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(self.artifacts_root / self.slug):
            raise HarnessError("LAYOUT", f"{path} resolves outside the experiment artifact root")
        # Refuse symlinked ancestors inside the artifact root as well.
        probe = path
        while probe != self.artifacts_root and probe != probe.parent:
            if probe.is_symlink():
                raise HarnessError("LAYOUT", f"symlink in artifact path: {probe}")
            probe = probe.parent

    def experiment_ref(self, name: str) -> str:
        return f"project://experiments/{self.slug}/{name}"

    def project_local(self, ref: str) -> Path:
        if not ref.startswith("project://"):
            raise HarnessError("LAYOUT", f"not a project reference: {ref!r}")
        path = (self.project_root / ref[len("project://"):]).resolve()
        if not path.is_relative_to(self.project_root):
            raise HarnessError("LAYOUT", "project reference escapes the project")
        return path
