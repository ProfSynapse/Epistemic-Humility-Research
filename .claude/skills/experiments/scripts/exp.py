#!/usr/bin/env python3
"""Experiments lifecycle CLI for the experiments-first layout.

One self-contained directory per evidence-producing experiment lives under the
repo-root ``experiments/`` tree. Each directory holds a signed ``AMENDMENT.md``
(prose), a thin machine-readable ``experiment.yaml`` manifest (the single source
of truth for machine state), the instrument configs, a ``NOTEBOOK.md`` running
log, an untracked ``analysis/`` scratch dir, and a gitignored ``directions/``
data dir. The registry files under ``experiments/`` are GENERATED from the
manifests and must never be hand-edited.

This module is stdlib + PyYAML only, deterministic (no timestamps in any
generated output), and is exercised both through ``bin/exp`` and directly in
tests. Every core function takes an explicit repo ``root`` so tests can drive it
against a temporary tree.

Subcommands: new, sign, repin, list, show, resolve, validate, regen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

EXPERIMENTS_DIRNAME = "experiments"
MANIFEST_NAME = "experiment.yaml"
REGISTRY_MD_NAME = "REGISTRY.md"
REGISTRY_JSON_NAME = "registry.json"

# Reserved directory names under experiments/ that are never themselves an
# experiment: common/ is the shared cross-experiment code home (graders, renders,
# promoted directions). They carry no manifest and are excluded from validation,
# the manifest scan, and the registry.
RESERVED_DIRNAMES = frozenset({"common"})
_SKIP_DIRNAMES = frozenset({"__pycache__"}) | RESERVED_DIRNAMES

TYPES = (
    "steer-cell",
    "training-run",
    "eval",
    "probe-fit",
    "lab-diagnostic",
    "historical-amendment",
)
STATUSES = ("draft", "signed", "running", "resolved", "null-result", "falsified", "historical")
# Statuses at or beyond signing: pins are expected to exist and still match.
SIGNED_PLUS = frozenset({"signed", "running", "resolved", "null-result", "falsified"})
# Terminal statuses that must carry a verdict.
RESOLVED_STATES = frozenset({"resolved", "null-result", "falsified", "historical"})
# Statuses whose pins must exist and still match: signed+ plus migrated
# historical-amendment records, which carry pins from their original run but
# are not caught by SIGNED_PLUS.
PIN_CHECK_STATUSES = SIGNED_PLUS | {"historical"}

# Statuses that assert a finished result -- and therefore a written Outcome.
TERMINAL_STATUSES = frozenset({"resolved", "null-result", "falsified"})

# Persistence declaration modes for instrument.modules (see
# _module_persistence_problems). A killed run that buffered results in memory
# and wrote output only at the end loses the whole run; every module a signed
# instrument executes must say up front how it survives a kill.
PERSISTENCE_MODES = ("incremental", "short-run")

# Cutoff date (UTC, ISO date) for the structural text-capture requirement: an
# experiment whose created_at is on/after this date must declare
# `text_capture` (see _text_capture_problems). Experiments predating this
# field, or created before the cutoff, are exempt so the pre-existing
# registry never starts failing validate retroactively.
TEXT_CAPTURE_REQUIRED_FROM = "2026-08-26"
# Literal accepted values; `textless: <non-empty reason>` is the third,
# free-text-suffixed option (see _text_capture_problems).
TEXT_CAPTURE_LITERAL_VALUES = ("enabled", "not-applicable")

GENERATED_HEADER = "GENERATED - do not edit; run bin/exp regen and stage the result"

# GitHub project the pr field links into (used only for REGISTRY.md rendering).
_GH_REPO = "ProfSynapse/Epistemic-Humility-Research"


class ExpError(Exception):
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
    raise ExpError(f"no git repo root found above {here}")


def experiments_dir(root: Path) -> Path:
    return root / EXPERIMENTS_DIRNAME


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "experiment"


# --- manifest IO -------------------------------------------------------------

def load_manifest(manifest_path: Path) -> dict:
    """Parse one manifest, returning a dict. Raises ExpError on unreadable YAML."""
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem dependent
        raise ExpError(f"{manifest_path}: cannot read ({exc})") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ExpError(f"{manifest_path}: invalid YAML ({exc})") from exc
    if not isinstance(data, dict):
        raise ExpError(f"{manifest_path}: manifest must be a YAML mapping")
    return data


def manifest_path_for(root: Path, slug: str) -> Path:
    return experiments_dir(root) / slug / MANIFEST_NAME


def iter_manifests(root: Path) -> list[tuple[str, Path, dict]]:
    """Every experiment dir's (slug, manifest_path, manifest) sorted by slug.

    Directories without a manifest are skipped silently so partially staged trees
    do not crash read-only commands; ``validate`` reports missing manifests.
    """
    base = experiments_dir(root)
    if not base.is_dir():
        return []
    out: list[tuple[str, Path, dict]] = []
    for child in sorted(base.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name in _SKIP_DIRNAMES:
            continue
        mpath = child / MANIFEST_NAME
        if not mpath.is_file():
            continue
        out.append((child.name, mpath, load_manifest(mpath)))
    return out


def _dump_manifest(manifest_path: Path, data: dict) -> None:
    """Write a manifest with stable key order and no timestamps."""
    manifest_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


# --- templates ---------------------------------------------------------------

def _manifest_template(slug: str, exp_type: str, title: str | None = None) -> dict:
    return {
        "slug": slug,
        "title": title or slug,
        "type": exp_type,
        "status": "draft",
        "registered": True,
        "created_at": now_utc(),
        "question": "",
        "prediction": "",
        "falsifier": "",
        "text_capture": "enabled",
        "checkpoint": {"repo": "", "revision": ""},
        "instrument": {
            "configs": [],
            "modules": [],
            "pins": {},
            "persistence": {},
        },
        "inputs": [],
        "verdict": "",
        "kg": [],
    }


_AMENDMENT_TEMPLATE = """# {title}

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`{manifest}` and is never duplicated here.

## Motivation and posture

Why this experiment exists, what prior result or gap it follows from, and whether
it is headline or exploratory evidence.

## Design

Substrate, signal, rendering, arms, and controls. Name the instrument config
files that `exp sign` will pin.

## Prediction

One sentence, stated before the run. Copy it into `prediction:` in the manifest.

## Falsifier

The concrete result that would falsify the prediction. Copy it into
`falsifier:` in the manifest.

## Gates

The pre-stated pass/fail thresholds. Derive them from the expected effect size
and its uncertainty; do not round to a convenient default.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
"""


_NOTEBOOK_TEMPLATE = """# {title} notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `{manifest}`.

## Entries

- (add dated entries as the experiment progresses)
"""


_GITIGNORE_TEMPLATE = """# Fitted directions and other large local data for this experiment.
directions/
# Local analysis scratch; keep untracked, promote real outputs deliberately.
analysis/
"""


_CELL_TEMPLATE = """# TODO: replace this placeholder with the pinned experiment instrument.
# Keep this file in the experiment directory unless the runner skill for this
# experiment type requires a different config layout.
#
# Before signing:
# - fill the actual runner/tuner config
# - list this file under experiment.yaml instrument.configs
# - run `bin/exp sign <slug>` to pin the final bytes
"""


_GATES_TEMPLATE = """# TODO: replace this placeholder with pre-stated gates.
# Gates must be fixed before launch and should define the pass/fail thresholds
# and falsifier boundary used by the amendment.
"""


# --- validation --------------------------------------------------------------

def _module_persistence_problems(instrument: dict) -> list[str]:
    """Return human-readable problems with instrument.modules persistence
    declarations (empty = every module is covered).

    Each entry in ``instrument.modules`` must have a matching key in the
    parallel ``instrument.persistence`` mapping (keyed by the same module
    relpath, the same shape as ``instrument.pins``) declaring either:

    - ``persistence: incremental`` with a non-empty ``checkpoint_path``, or
    - ``persistence: short-run`` with a numeric ``measured_smoke_wall_clock_s``.

    Modules are the bespoke harness scripts a cell runs (extraction, grading,
    analysis passes); a config-only instrument (``instrument.modules: []``)
    has nothing to declare. Callers decide whether a problem is a hard error
    or a warning based on the manifest's status (see _validate_manifest and
    cmd_sign).
    """
    modules = instrument.get("modules") or []
    persistence = instrument.get("persistence") or {}
    if not isinstance(persistence, dict):
        return ["instrument.persistence must be a mapping keyed by module relpath"]
    problems: list[str] = []
    for rel in modules:
        rel = str(rel)
        entry = persistence.get(rel)
        if entry is None:
            problems.append(
                f"module {rel!r} has no persistence declaration (add "
                f"instrument.persistence.{rel!r} with persistence: "
                "incremental|short-run)"
            )
            continue
        if not isinstance(entry, dict):
            problems.append(f"instrument.persistence[{rel!r}] must be a mapping")
            continue
        mode = entry.get("persistence")
        if mode not in PERSISTENCE_MODES:
            problems.append(
                f"instrument.persistence[{rel!r}].persistence must be one of "
                f"{', '.join(PERSISTENCE_MODES)}, got {mode!r}"
            )
            continue
        if mode == "incremental":
            checkpoint_path = entry.get("checkpoint_path")
            if not (isinstance(checkpoint_path, str) and checkpoint_path.strip()):
                problems.append(
                    f"instrument.persistence[{rel!r}]: checkpoint_path must be a "
                    "non-empty string for persistence: incremental"
                )
        else:  # short-run
            wall_clock = entry.get("measured_smoke_wall_clock_s")
            if not isinstance(wall_clock, (int, float)) or isinstance(wall_clock, bool):
                problems.append(
                    f"instrument.persistence[{rel!r}]: measured_smoke_wall_clock_s must "
                    "be a number for persistence: short-run"
                )
    return problems


def _stale_gate_status_problems(exp_dir: Path, data: dict) -> list[str]:
    """Flag a signed-or-later experiment whose gates.yaml still reads as a draft.

    Returns human-readable problems (empty = ok). Checked only at `signed` and
    beyond: a draft experiment SHOULD carry `status: proposed` in its gates file.
    """
    if data.get("status") not in SIGNED_PLUS:
        return []
    gates_path = exp_dir / "gates.yaml"
    if not gates_path.is_file():
        return []
    try:
        gates = yaml.safe_load(gates_path.read_text(encoding="utf-8"))
    except Exception:
        return []  # malformed gates files are another check's problem
    if not isinstance(gates, dict):
        return []

    problems: list[str] = []
    if gates.get("status") == "proposed":
        problems.append(
            "gates.yaml declares `status: proposed` but the experiment is "
            f"{data.get('status')!r}; the pinned thresholds are binding. Correct "
            "the gates file via `bin/exp repin` (pre-run only) or a governed "
            "revision -- never by editing a pinned file in place."
        )
    for field in ("adjudicated_by", "adjudicated_date"):
        if field in gates and gates.get(field) is None:
            problems.append(
                f"gates.yaml leaves {field} null on a {data.get('status')!r} "
                "experiment; record who signed the thresholds and when."
            )
    return problems


_HEADER_DRAFT_WORD_RE = re.compile(r"\bdraft\b", re.IGNORECASE)
_HEADER_DRAFT_PHRASES = ("not signed", "no gpu work has run")


def _amendment_header_status_line(exp_dir: Path) -> str | None:
    """Return AMENDMENT.md's header status-assertion line, or None if absent.

    Checks the two conventions used across amendments: a prose ``Status:``
    line (optionally bold-marked, e.g. ``**Status:**``) within the first ~15
    lines, or a YAML frontmatter ``status:`` field. Returns the raw text to
    check for draft-claiming language; None means the header makes no
    explicit status claim, so there is nothing to contradict.
    """
    amend_path = exp_dir / "AMENDMENT.md"
    if not amend_path.is_file():
        return None
    try:
        lines = amend_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None

    if lines and lines[0].strip() == "---":
        for line in lines[1:15]:
            if line.strip() == "---":
                break
            m = re.match(r"^\s*status:\s*(.+?)\s*$", line, re.IGNORECASE)
            if m:
                return f"status: {m.group(1)}"
        return None

    for line in lines[:15]:
        if re.match(r"^\s*\*{0,2}status:", line, re.IGNORECASE):
            return line
    return None


def _stale_amendment_header_problems(exp_dir: Path, data: dict) -> list[str]:
    """Flag a signed-or-later experiment whose AMENDMENT.md header still
    reads as an unsigned draft.

    Returns human-readable problems (empty = ok). Checked only at `signed`
    and beyond, mirroring `_stale_gate_status_problems` above: a genuine
    draft correctly has a draft header, so drafts are never flagged. Only
    fires on a confident contradiction -- the header's own status-assertion
    line (see `_amendment_header_status_line`) containing the standalone
    word "draft", or the phrase "not signed" or "no gpu work has run" -- so
    a corrected header that narrates its own past draft/signing history in
    later prose (the exact convention this check exists to make routine,
    e.g. "this header was stale boilerplate reading 'draft' until <date>;
    corrected to match the machine state") is never flagged, since that
    narration lives outside the single status-assertion line. Ambiguous
    prose using neither literal marker is intentionally left unflagged.
    Warning-only and deliberately NOT auto-repaired, matching
    `_stale_gate_status_problems`'s severity: this is a bookkeeping
    contradiction between a human-authored header and the machine state, not
    a data-integrity fault, so it should not block a commit. See the two
    header-drift cases (`j-space-cross-family-layer-contrast`,
    `qwen3-4b-family-atlas`) and the wider sweep fixed 2026-08-11, and the
    `gemma-4-e4b-family-atlas/AMENDMENT.md` 2026-07-20 header correction
    that first established the fix pattern this check guards.
    """
    if data.get("status") not in SIGNED_PLUS:
        return []
    status_line = _amendment_header_status_line(exp_dir)
    if status_line is None:
        return []
    sl = status_line.lower()
    if _HEADER_DRAFT_WORD_RE.search(sl) or any(p in sl for p in _HEADER_DRAFT_PHRASES):
        return [
            f"AMENDMENT.md header still reads as an unsigned draft "
            f"({status_line.strip()!r}) but experiment.yaml status is "
            f"{data.get('status')!r}; correct the header to state the true "
            "status (see gemma-4-e4b-family-atlas/AMENDMENT.md's 2026-07-20 "
            "header correction for the pattern)."
        ]
    return []


_OUTCOME_PLACEHOLDER_RE = re.compile(r"filled at resolve", re.IGNORECASE)


def _unfilled_outcome_problems(exp_dir: Path, data: dict) -> list[str]:
    """Flag a terminal-status experiment whose AMENDMENT.md ``## Outcome``
    section is still the scaffold placeholder (or empty).

    Returns human-readable problems (empty = ok). Checked only at the
    terminal statuses (resolved / null-result / falsified): a terminal
    status in experiment.yaml implies a written Outcome in the governed
    doc, since the amendment is the sole citable source for the result.
    ``historical`` (migrated legacy) cells are exempt -- they predate the
    scaffold convention. Only the body of each exactly-``## Outcome``
    section is inspected, so header prose narrating a past backfill (e.g.
    'carried the unfilled placeholder text ("Filled at resolve...") -- was
    backfilled <date>') is never flagged, and a filled ``### Outcome``
    subsection elsewhere does not mask a still-unfilled trailing
    ``## Outcome`` (the qwen35-4b-midband-heldout shape). Warning-only and
    NOT auto-repaired, matching the two sibling drift checks above:
    writing an Outcome requires human transcription from the cell's own
    committed artifacts and notebook adjudication, never automation. See
    the four-cell Outcome backfill of 2026-08-11 for the fix pattern.
    """
    if data.get("status") not in TERMINAL_STATUSES:
        return []
    amend_path = exp_dir / "AMENDMENT.md"
    if not amend_path.is_file():
        return []
    try:
        lines = amend_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    bodies: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if re.match(r"^##\s+Outcome\s*$", line):
            current = []
            bodies.append(current)
        elif re.match(r"^##\s", line):
            current = None
        elif current is not None:
            current.append(line)

    for body in bodies:
        body_text = "\n".join(body).strip()
        if not body_text or _OUTCOME_PLACEHOLDER_RE.search(body_text):
            return [
                "AMENDMENT.md `## Outcome` is still the unfilled scaffold "
                "placeholder (or empty) but experiment.yaml status is "
                f"{data.get('status')!r}; a terminal status implies a "
                "written Outcome. Backfill it from this cell's own "
                "committed artifacts and NOTEBOOK.md adjudication (see the "
                "four-cell backfill of 2026-08-11 for the pattern), never "
                "from downstream summaries."
            ]
    return []


def _parse_created_at(value: object) -> "object | None":
    """Best-effort parse of a manifest's created_at into an aware datetime.

    Returns None for a missing/blank/unparseable value -- callers treat that
    as "predates the field" rather than raising, so a malformed date is
    conservatively exempted rather than blocking an unrelated commit.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    from datetime import datetime, timezone

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _text_capture_problems(data: dict) -> list[str]:
    """Return hard-error problems for a missing/invalid `text_capture`.

    Structural enforcement of the data-exhaust build-time rule
    (`.skills/data-exhaust/SKILL.md`): a generation harness must persist
    per-row text unless the experiment explicitly declares otherwise.
    Enforced only for experiments whose `created_at` is on/after
    TEXT_CAPTURE_REQUIRED_FROM -- an experiment with no `created_at`
    (predates that manifest field) or one before the cutoff is exempt, so
    the pre-existing registry never starts failing validate retroactively.
    `bin/exp new` scaffolds `text_capture: enabled` by default, so a
    normally-scaffolded new experiment satisfies this with no extra step;
    the sanctioned opt-outs are `not-applicable` (no generation happens at
    all, e.g. a pure analysis/probe-fit pass) and `textless: <non-empty
    reason>` (generation happens but text capture is deliberately,
    auditably disabled -- see `experiments/common/runlog_contract.py`,
    whose `open_generation_runlog` folds that same reason into the run
    log's own meta fingerprint). This is a hard error, not a warning: unlike
    the persistence/header/outcome checks above, there is no legacy cohort
    to protect once an experiment is new enough to be in scope.
    """
    created_at = _parse_created_at(data.get("created_at"))
    if created_at is None:
        return []
    from datetime import datetime, timezone

    cutoff = datetime.fromisoformat(TEXT_CAPTURE_REQUIRED_FROM).replace(tzinfo=timezone.utc)
    if created_at < cutoff:
        return []

    value = data.get("text_capture")
    if not (isinstance(value, str) and value.strip()):
        return [
            "text_capture is required for experiments created on/after "
            f"{TEXT_CAPTURE_REQUIRED_FROM} (see .skills/data-exhaust/SKILL.md's "
            "build-time requirement and experiments/common/runlog_contract.py); "
            "set it to 'enabled', 'not-applicable', or 'textless: <reason>'"
        ]
    v = value.strip()
    if v in TEXT_CAPTURE_LITERAL_VALUES:
        return []
    if v.startswith("textless:") and v[len("textless:") :].strip():
        return []
    return [
        f"text_capture value {value!r} is invalid -- must be 'enabled', "
        "'not-applicable', or 'textless: <non-empty reason>' (see "
        ".skills/data-exhaust/SKILL.md's build-time requirement and "
        "experiments/common/runlog_contract.py)"
    ]


def _is_untracked_data_input(rel: str) -> bool:
    """True when an input path lives under an experiment's gitignored data dir.

    Each experiment carries an untracked ``analysis/`` scratch dir and a
    gitignored ``directions/`` data dir (see the module docstring). Inputs that
    point into either are run-materialized data: present in the canonical
    checkout and sha256-verified by SC0 staging at run time, but legitimately
    absent in a fresh linked worktree or a clean clone. Their absence must not
    block a commit that does not even touch that experiment. Tracked locations
    such as ``analysis-committed/`` are NOT matched and stay strictly enforced.
    """
    parts = Path(rel).parts
    return (
        len(parts) >= 4
        and parts[0] == EXPERIMENTS_DIRNAME
        and parts[2] in ("analysis", "directions")
    )


def _validate_manifest(root: Path, slug: str, mpath: Path, data: dict) -> list[str]:
    """Return a list of human-readable problems for one manifest (empty = ok)."""
    problems: list[str] = []

    def err(msg: str) -> None:
        problems.append(f"{mpath}: {msg}")

    # slug matches dir name
    declared_slug = data.get("slug")
    if declared_slug != slug:
        err(f"slug {declared_slug!r} does not match directory name {slug!r}")

    exp_type = data.get("type")
    if exp_type not in TYPES:
        err(f"type {exp_type!r} not one of {', '.join(TYPES)}")

    status = data.get("status")
    if status not in STATUSES:
        err(f"status {status!r} not one of {', '.join(STATUSES)}")

    registered = data.get("registered")
    if not isinstance(registered, bool):
        err("registered must be a boolean (true|false)")
        registered = True  # assume registered so downstream checks still run

    question = data.get("question")
    if not (isinstance(question, str) and question.strip()):
        err("question must be a non-empty string")

    instrument = data.get("instrument")
    if not isinstance(instrument, dict):
        err("instrument must be a mapping with configs/pins")
        return problems
    configs = instrument.get("configs", [])
    modules = instrument.get("modules", []) or []
    pins = instrument.get("pins", {})
    if not isinstance(configs, list):
        err("instrument.configs must be a list")
        configs = []
    if not isinstance(modules, list):
        err("instrument.modules must be a list")
        modules = []
    if not isinstance(pins, dict):
        err("instrument.pins must be a mapping")
        pins = {}

    repins = instrument.get("repins", []) or []
    if not isinstance(repins, list):
        err("instrument.repins must be a list")
        repins = []

    # Persistence declarations (kill-resume safety): required per module, but
    # `validate` only ever WARNS about a missing one, at every status,
    # including draft. The hard-enforcement point is `cmd_sign`, which
    # refuses to pin an instrument missing one; that is the mandatory gate
    # every new experiment already passes before it can run. Warning-only in
    # validate means a stale draft that predates this field (or was run
    # informally without ever going through `exp sign`, e.g. a Tier-2
    # exploratory cell) never starts failing validate retroactively; nothing
    # here can move a manifest's goalposts after the fact.
    for p in _module_persistence_problems(instrument):
        print(f"exp validate: warning: {slug}: {p}", file=sys.stderr)

    # A signed experiment whose gates.yaml still declares itself `proposed` (or
    # leaves the sign-time adjudication fields null) reads as unsettled to anyone
    # who opens the gates file directly, even though the hash pin in this
    # manifest is what actually binds. That ambiguity is dangerous in exactly one
    # direction: it invites a reader to treat a frozen threshold as still
    # negotiable at adjudication time. Warning-only, and deliberately NOT
    # auto-repaired -- the file is hash-pinned, so any byte change must go
    # through `bin/exp repin` (pre-run) or a governed revision, never a silent
    # rewrite. See the grpo-three-seed-confirmatory NOTEBOOK entry of 2026-08-05.
    for p in _stale_gate_status_problems(mpath.parent, data):
        print(f"exp validate: warning: {slug}: {p}", file=sys.stderr)

    # A signed-or-later experiment whose AMENDMENT.md header still asserts
    # "draft (not signed)" reads as unlaunched/unsigned to anyone opening the
    # governed doc directly, even though the machine state has moved on --
    # exactly the drift found and fixed across 19 amendments 2026-08-11 (see
    # _stale_amendment_header_problems). Warning-only for the same reason as
    # the gates-status check above: bookkeeping drift, not a data-integrity
    # fault, and not auto-repaired since the fix requires human judgment
    # about which surrounding prose is now stale.
    for p in _stale_amendment_header_problems(mpath.parent, data):
        print(f"exp validate: warning: {slug}: {p}", file=sys.stderr)

    # A terminal-status experiment whose `## Outcome` still reads "Filled
    # at resolve..." presents no written result in the governed doc -- the
    # defect class found on four cells 2026-08-11. Warning-only: the fix is
    # human transcription, not automation (see _unfilled_outcome_problems).
    for p in _unfilled_outcome_problems(mpath.parent, data):
        print(f"exp validate: warning: {slug}: {p}", file=sys.stderr)

    # Structural text-capture guard (hard error, not warning-only): an
    # experiment new enough to be in scope must declare text_capture. See
    # _text_capture_problems.
    for p in _text_capture_problems(data):
        err(p)

    inputs = data.get("inputs", []) or []
    if not isinstance(inputs, list):
        err("inputs must be a list")
        inputs = []

    kg = data.get("kg", []) or []
    if not isinstance(kg, list):
        err("kg must be a list")
        kg = []

    # Claim requirements: only for registered experiments past draft.
    if registered and status in SIGNED_PLUS:
        for field in ("prediction", "falsifier"):
            val = data.get(field)
            if not (isinstance(val, str) and val.strip()):
                err(f"{field} must be non-empty for a registered {status} experiment")
    if registered and status in RESOLVED_STATES:
        verdict = data.get("verdict")
        if not (isinstance(verdict, str) and verdict.strip()):
            err(f"verdict must be non-empty for a {status} experiment")

    exp_dir = mpath.parent

    # Pins: signed+ experiments must have pinned every config, and every pinned
    # file must still exist and hash to its recorded value. Historical-amendment
    # records are not required to have pinned every config/module (some were
    # migrated with partial pin coverage), but any pin they do carry must still
    # match, so they get the drift check without the completeness check.
    if status in SIGNED_PLUS:
        pin_targets = [str(c) for c in configs] + [str(m) for m in modules]
        for rel in pin_targets:
            if rel not in pins:
                err(f"config/module {rel!r} is not pinned (run exp sign)")
    if status in PIN_CHECK_STATUSES:
        for rel, recorded in pins.items():
            fpath = exp_dir / rel
            if not fpath.is_file():
                err(f"pinned file missing: {rel}")
                continue
            actual = _sha256(fpath)
            if actual != recorded:
                err(f"pin drift: {rel} hashes {actual[:12]}..., pinned {str(recorded)[:12]}...")

    # Repins audit trail: each entry must carry its required fields, and the LAST
    # repin entry per file must agree with the file's current pin (a repin that no
    # longer matches the live pin is a stale/tampered audit record). Earlier
    # entries for the same file are historical and are not expected to match.
    last_new: dict[str, str] = {}
    for i, entry in enumerate(repins):
        if not isinstance(entry, dict):
            err(f"instrument.repins[{i}] must be a mapping")
            continue
        for key in ("file", "old_sha256", "new_sha256", "date", "reason"):
            val = entry.get(key)
            if not (isinstance(val, str) and val.strip()):
                err(f"instrument.repins[{i}] missing/empty required field {key!r}")
        rel = entry.get("file")
        new = entry.get("new_sha256")
        if isinstance(rel, str) and isinstance(new, str):
            last_new[rel] = new  # append-only order => ends as the LAST entry per file
    for rel, new in last_new.items():
        if rel not in pins:
            err(f"repinned file {rel!r} has no current pin")
        elif pins[rel] != new:
            err(
                f"repins/pins mismatch for {rel}: last repin new_sha256 "
                f"{new[:12]}... does not match pin {str(pins[rel])[:12]}..."
            )

    # Inputs: repo-relative paths that must exist. Inputs under an experiment's
    # gitignored data dirs (``analysis/`` scratch, ``directions/`` data) are
    # run-materialized: present in the canonical checkout and sha256-verified by
    # SC0 staging at run time, but legitimately absent in a fresh linked worktree
    # or clean clone. A missing one is a non-fatal warning (to stderr) rather
    # than a commit-blocking error, so a commit that does not touch that
    # experiment is never blocked by data it never needed. Tracked inputs
    # (configs, analysis-committed manifests, dataset cards) must still exist.
    for rel in inputs:
        ipath = root / str(rel)
        if ipath.exists():
            continue
        if _is_untracked_data_input(str(rel)):
            print(
                f"exp validate: warning: {slug}: gitignored data input absent "
                f"(ok in a worktree/clean clone; sha-staged at run time): {rel}",
                file=sys.stderr,
            )
            continue
        err(f"input path does not exist: {rel}")

    # KG ids must resolve to real library nodes.
    if kg:
        known = _scan_kg_ids(root)
        for node_id in kg:
            if str(node_id) not in known:
                err(f"kg id does not resolve to a library node: {node_id}")

    return problems


def _parse_frontmatter_id(path: Path) -> str | None:
    """Best-effort read of a leading ``id:`` from a markdown frontmatter block."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:  # pragma: no cover
        return None
    if not text.startswith("---"):
        return None
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return None
    for line in text[3:end].split("\n"):
        stripped = line.strip()
        if stripped.startswith("id:"):
            value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def _scan_kg_ids(root: Path) -> set[str]:
    """Collect resolvable KG node ids from library/ (frontmatter id, else stem).

    Mirrors the id-scan posture of the kg-ingest inventory: concept atoms and
    mechanisms carry an ``id:`` in frontmatter (fallback to the file stem), and
    paper notes resolve by stem.
    """
    ids: set[str] = set()
    library = root / "library"
    if not library.is_dir():
        return ids
    for md in library.rglob("*.md"):
        ids.add(md.stem)
        fm_id = _parse_frontmatter_id(md)
        if fm_id:
            ids.add(fm_id)
    return ids


def validate(root: Path) -> int:
    """Validate every manifest under experiments/. Returns process exit code."""
    base = experiments_dir(root)
    problems: list[str] = []

    if base.is_dir():
        # Surface experiment dirs that lack a manifest entirely.
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if not child.is_dir():
                continue
            if child.name in _SKIP_DIRNAMES:
                continue
            if not (child / MANIFEST_NAME).is_file():
                problems.append(f"{child}: missing {MANIFEST_NAME}")
        for slug, mpath, data in iter_manifests(root):
            problems.extend(_validate_manifest(root, slug, mpath, data))

    if problems:
        print("exp validate: FAILED")
        for line in problems:
            print(f"  - {line}")
        return 1
    count = len(iter_manifests(root))
    print(f"exp validate: OK ({count} experiment(s))")
    return 0


# --- registry generation -----------------------------------------------------

def _pr_cell(pr: object) -> str:
    if pr in (None, "", 0):
        return ""
    return f"[#{pr}](https://github.com/{_GH_REPO}/pull/{pr})"


def render_registry_md(root: Path) -> str:
    lines = [
        f"<!-- {GENERATED_HEADER} -->",
        "",
        "# Experiments registry",
        "",
        "| slug | type | status | PR | question | verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for slug, _mpath, data in iter_manifests(root):
        question = str(data.get("question", "") or "").replace("|", "\\|").strip()
        verdict = str(data.get("verdict", "") or "").replace("|", "\\|").strip()
        # registered:false rows stay in the inventory but are marked so they are
        # never read as a claim.
        if data.get("registered") is False:
            question = f"teaching artifact: {question}".strip()
        row = [
            slug,
            str(data.get("type", "") or ""),
            str(data.get("status", "") or ""),
            _pr_cell(data.get("pr")),
            question,
            verdict,
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def render_registry_json(root: Path) -> str:
    payload = {
        "_generated": GENERATED_HEADER,
        "experiments": [data for _slug, _mpath, data in iter_manifests(root)],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def regen(root: Path, *, check: bool = False) -> int:
    base = experiments_dir(root)
    md_text = render_registry_md(root)
    json_text = render_registry_json(root)
    md_path = base / REGISTRY_MD_NAME
    json_path = base / REGISTRY_JSON_NAME

    if check:
        stale: list[str] = []
        for path, expected in ((md_path, md_text), (json_path, json_text)):
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != expected:
                stale.append(str(path.relative_to(root)))
        if stale:
            print("exp regen --check: STALE registry files: " + ", ".join(stale))
            print("  run `bin/exp regen` and stage the result")
            return 1
        print("exp regen --check: registry up to date")
        return 0

    base.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_text, encoding="utf-8")
    json_path.write_text(json_text, encoding="utf-8")
    print(f"exp regen: wrote {md_path.relative_to(root)} and {json_path.relative_to(root)}")
    return 0


# --- subcommands: new / sign / list / show / resolve -------------------------

def cmd_new(root: Path, slug: str | None, exp_type: str, title: str | None = None) -> int:
    if exp_type not in TYPES:
        raise ExpError(f"type {exp_type!r} not one of {', '.join(TYPES)}")
    if not slug:
        if not title:
            raise ExpError("provide a slug or --title")
        slug = slugify(title)
    if not slug or not all(c.islower() or c.isdigit() or c == "-" for c in slug) or slug[0] == "-":
        raise ExpError(
            f"slug {slug!r} must be kebab-case (lowercase letters, digits, hyphens; "
            "not starting with a hyphen)"
        )
    title = title or slug
    exp_dir = experiments_dir(root) / slug
    if exp_dir.exists():
        raise ExpError(f"experiment already exists: {exp_dir}")

    exp_dir.mkdir(parents=True)
    _dump_manifest(exp_dir / MANIFEST_NAME, _manifest_template(slug, exp_type, title))
    (exp_dir / "AMENDMENT.md").write_text(
        _AMENDMENT_TEMPLATE.format(title=title, slug=slug, manifest=MANIFEST_NAME), encoding="utf-8"
    )
    (exp_dir / "NOTEBOOK.md").write_text(
        _NOTEBOOK_TEMPLATE.format(title=title, slug=slug, manifest=MANIFEST_NAME), encoding="utf-8"
    )
    (exp_dir / ".gitignore").write_text(_GITIGNORE_TEMPLATE, encoding="utf-8")
    (exp_dir / "cell.yaml").write_text(_CELL_TEMPLATE, encoding="utf-8")
    (exp_dir / "gates.yaml").write_text(_GATES_TEMPLATE, encoding="utf-8")

    print(f"exp new: scaffolded {exp_dir.relative_to(root)} (type={exp_type}, status=draft)")
    print("  created: experiment.yaml, AMENDMENT.md, NOTEBOOK.md, cell.yaml, gates.yaml, .gitignore")
    print("  next: fill question/prediction/falsifier + instrument.configs, then `bin/exp sign`")
    return 0


def _has_surface_block(path: Path) -> bool:
    """True if a config file parses to a mapping with a top-level surface: block."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return False
    return isinstance(data, dict) and isinstance(data.get("surface"), dict)


def cmd_sign(root: Path, slug: str) -> int:
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)

    if data.get("status") != "draft":
        raise ExpError(
            f"{slug}: status is {data.get('status')!r}; only a draft experiment can be signed"
        )
    for field in ("prediction", "falsifier"):
        val = data.get(field)
        if not (isinstance(val, str) and val.strip()):
            raise ExpError(f"{slug}: {field} must be filled before signing")

    exp_dir = mpath.parent
    instrument = data.setdefault("instrument", {})
    configs = list(instrument.get("configs", []) or [])
    modules = list(instrument.get("modules", []) or [])
    pin_targets = [str(c) for c in configs] + [str(m) for m in modules]
    if not pin_targets:
        raise ExpError(
            f"{slug}: instrument.configs is empty; list the instrument files before signing"
        )

    # GENERATION-ENGINE GATE (PI ruling 2026-08-13, enforced): vLLM is the
    # forced default for every generation-bearing cell. A draft can only be
    # signed if instrument.engine declares vllm with a pinned version, OR
    # instrument.engine_exception claims one of the two named exceptions
    # with a reason. See experiment-runner reference/batched-generation.md.
    GENERATION_BEARING_TYPES = {"steer-cell", "training-run", "eval", "probe-fit"}
    if data.get("type") in GENERATION_BEARING_TYPES:
        engine = instrument.get("engine")
        exception = instrument.get("engine_exception")
        engine_ok = (
            isinstance(engine, dict)
            and str(engine.get("name", "")).lower() == "vllm"
            and str(engine.get("version", "")).strip() not in ("", "unpinned")
        )
        exception_ok = (
            isinstance(exception, dict)
            and exception.get("kind") in ("parity-locked", "intervention")
            and isinstance(exception.get("reason"), str)
            and exception["reason"].strip()
        )
        if not (engine_ok or exception_ok):
            raise ExpError(
                f"{slug}: generation-engine gate (PI ruling 2026-08-13): "
                "declare instrument.engine {name: vllm, version: <pinned>} "
                "or instrument.engine_exception {kind: parity-locked|"
                "intervention, reason: <why>} before signing. vLLM is the "
                "forced default for generation-bearing cells; see "
                "experiment-runner reference/batched-generation.md."
            )

    persistence_problems = _module_persistence_problems(instrument)
    if persistence_problems:
        raise ExpError(
            f"{slug}: instrument.modules has missing/invalid persistence "
            "declarations; a signed instrument must state up front how each "
            "module survives a kill (see the experiments SKILL.md persistence "
            "section):\n  - " + "\n  - ".join(persistence_problems)
        )

    pins: dict[str, str] = {}
    steer_cells: list[str] = []
    for rel in pin_targets:
        fpath = exp_dir / rel
        if not fpath.is_file():
            raise ExpError(f"{slug}: cannot pin missing file {rel}")
        pins[rel] = _sha256(fpath)
        if _has_surface_block(fpath):
            steer_cells.append(rel)

    instrument["pins"] = pins
    data["status"] = "signed"
    _dump_manifest(mpath, data)

    print(f"exp sign: {slug} signed; pinned {len(pins)} file(s)")
    for rel, sha in pins.items():
        print(f"  {rel}: {sha}")
    for rel in steer_cells:
        print(
            f"  reminder: {rel} is a tuner steer cell. The pin above is a file-integrity "
            "hash of the YAML bytes, not the value surface.expected_config_sha checks "
            "(that compares against compute_config_sha over the parsed config, a "
            "different hash). To set expected_config_sha: run the cell once with it "
            "unset, copy the config_sha the tuner prints on completion "
            '("Steer cell complete. Output ..., config_sha <X>"), and hand-fill that value.'
        )
    return 0


def cmd_repin(root: Path, slug: str, relpaths: list[str], reason: str) -> int:
    """Repair pinned instrument files on a signed-but-unlaunched experiment.

    A signed experiment whose instrument has a build-environment or harness
    defect (discovered before any run artifact exists) has no honest way to move
    its pins otherwise: ``sign`` refuses non-drafts. ``repin`` re-hashes the named
    file(s), updates ``instrument.pins``, and appends an append-only audit entry
    per file to ``instrument.repins``. It hard-refuses anything that would be
    goalpost movement: only a ``signed`` experiment with no verdict, only files
    that are already pinned and whose bytes actually changed, and only when every
    OTHER pinned file still matches (so an intended repair never silently absorbs
    unrelated drift).
    """
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)

    status = data.get("status")
    if status != "signed":
        if status == "draft":
            raise ExpError(
                f"{slug}: status is 'draft'; nothing is pinned yet, edit the "
                "instrument freely and run `bin/exp sign`"
            )
        if status in RESOLVED_STATES:
            raise ExpError(
                f"{slug}: status is {status!r}; results exist, a repin after "
                "resolution is goalpost movement"
            )
        raise ExpError(
            f"{slug}: status is {status!r}; only a signed experiment can be "
            "repinned (repin repairs the instrument before any run artifact exists)"
        )

    verdict = data.get("verdict")
    if isinstance(verdict, str) and verdict.strip():
        raise ExpError(
            f"{slug}: a verdict is already recorded; never repin a resolved experiment"
        )

    if not (isinstance(reason, str) and reason.strip()):
        raise ExpError("--reason must be a non-empty explanation for the repin")
    reason = reason.strip()

    if not relpaths:
        raise ExpError("name at least one pinned file to repin")

    instrument = data.get("instrument")
    if not isinstance(instrument, dict):
        raise ExpError(f"{slug}: manifest has no instrument block to repin")
    pins = instrument.get("pins")
    if not isinstance(pins, dict) or not pins:
        raise ExpError(f"{slug}: no pins recorded; sign the experiment first")

    exp_dir = mpath.parent
    # De-duplicate the named files while preserving the order given.
    named = list(dict.fromkeys(str(r) for r in relpaths))

    # Every named file must already be pinned: repin repairs an existing pin, it
    # never introduces a new one (that is what signing is for).
    not_pinned = [r for r in named if r not in pins]
    if not_pinned:
        raise ExpError(
            f"{slug}: not in instrument.pins, so cannot be repinned "
            f"(repin repairs an existing pin only): {', '.join(not_pinned)}"
        )

    # Named files must exist on disk so we can re-hash them.
    missing = [r for r in named if not (exp_dir / r).is_file()]
    if missing:
        raise ExpError(f"{slug}: named file(s) missing on disk: {', '.join(missing)}")

    # No-op refusal: the current bytes must actually differ from the recorded pin.
    new_hashes = {r: _sha256(exp_dir / r) for r in named}
    noop = [r for r in named if new_hashes[r] == pins[r]]
    if noop:
        raise ExpError(
            f"{slug}: current bytes already match the pin, nothing to repin: "
            f"{', '.join(noop)}"
        )

    # Unrelated-drift refusal: every pinned file NOT named must still match, so a
    # targeted repair can never quietly launder drift in a sibling instrument file.
    drifted: list[str] = []
    for rel, recorded in pins.items():
        if rel in named:
            continue
        fpath = exp_dir / rel
        if not fpath.is_file():
            drifted.append(f"{rel} (missing)")
        elif _sha256(fpath) != recorded:
            drifted.append(rel)
    if drifted:
        raise ExpError(
            f"{slug}: other pinned file(s) have drifted; repin the intended files "
            f"only and investigate the rest: {', '.join(sorted(drifted))}"
        )

    # Effect: update the pins and append one audit entry per file. The repins list
    # is append-only; prior entries are never removed or edited.
    repins = instrument.get("repins")
    if not isinstance(repins, list):
        repins = []
    date = now_utc()
    old_hashes = {r: pins[r] for r in named}
    for rel in named:
        pins[rel] = new_hashes[rel]
        repins.append(
            {
                "file": rel,
                "old_sha256": old_hashes[rel],
                "new_sha256": new_hashes[rel],
                "date": date,
                "reason": reason,
            }
        )
    instrument["pins"] = pins
    instrument["repins"] = repins
    _dump_manifest(mpath, data)

    print(f"exp repin: {slug} repinned {len(named)} file(s)")
    for rel in named:
        print(f"  {rel}: {old_hashes[rel][:12]}... -> {new_hashes[rel]}")
    print(f"  reason: {reason}")
    print("  recorded in instrument.repins (audit trail); run `bin/exp validate` to confirm")
    return 0


def cmd_list(root: Path, status: str | None, exp_type: str | None) -> int:
    rows = []
    for slug, _mpath, data in iter_manifests(root):
        if status and data.get("status") != status:
            continue
        if exp_type and data.get("type") != exp_type:
            continue
        rows.append(
            (slug, str(data.get("type", "")), str(data.get("status", "")),
             str(data.get("question", "") or ""))
        )
    if not rows:
        print("(no experiments)")
        return 0
    widths = [max(len(r[i]) for r in ([("slug", "type", "status", "question")] + rows))
              for i in range(4)]
    header = ("slug", "type", "status", "question")
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(header)))
    print("  ".join("-" * widths[i] for i in range(4)))
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in range(4)))
    return 0


def cmd_show(root: Path, slug: str) -> int:
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)
    exp_dir = mpath.parent
    print(f"# {slug}")
    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip())
    print("\n# resolved paths")
    print(f"  dir: {exp_dir}")
    print(f"  manifest: {mpath}")
    for rel in (data.get("instrument", {}) or {}).get("configs", []) or []:
        target = exp_dir / str(rel)
        mark = "ok" if target.is_file() else "MISSING"
        print(f"  config: {target} [{mark}]")
    repins = (data.get("instrument", {}) or {}).get("repins", []) or []
    if repins:
        print("\n# instrument repins (append-only audit trail)")
        for entry in repins:
            print(
                f"  {entry.get('file')}: {str(entry.get('old_sha256'))[:12]}... -> "
                f"{str(entry.get('new_sha256'))[:12]}...  ({entry.get('date')})"
            )
            print(f"    reason: {entry.get('reason')}")
    return 0


def cmd_resolve(root: Path, slug: str, verdict: str, status: str) -> int:
    if status not in RESOLVED_STATES:
        raise ExpError(f"resolve status must be one of {', '.join(sorted(RESOLVED_STATES))}")
    if not verdict.strip():
        raise ExpError("verdict must be a non-empty sentence")
    mpath = manifest_path_for(root, slug)
    if not mpath.is_file():
        raise ExpError(f"no manifest at {mpath}")
    data = load_manifest(mpath)
    data["status"] = status
    data["verdict"] = verdict.strip()
    _dump_manifest(mpath, data)

    print(f"exp resolve: {slug} -> {status}")
    print(f"  verdict: {verdict.strip()}")
    print("  kg-ingest checklist:")
    print("    1. ingest the result as typed KG nodes (claim/mechanism/evidence) via the kg-ingest skill")
    print("    2. record the returned node ids in the manifest `kg:` list")
    print("    3. run `bin/exp validate` to confirm the kg ids resolve")
    print("    4. run `bin/exp regen` and stage the updated registry")
    return 0


# --- argparse / main ---------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exp", description="Experiments lifecycle CLI (draft -> sign -> run -> resolve)."
    )
    parser.add_argument(
        "--root", default=None,
        help="repo root (default: discovered by walking up to the git root).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="scaffold a new experiment directory")
    p_new.add_argument("slug", nargs="?", help="experiment slug; defaults to slugified --title")
    p_new.add_argument("--title", help="human title for AMENDMENT.md / NOTEBOOK.md; also used to derive slug if omitted")
    p_new.add_argument("--type", required=True, choices=TYPES, dest="exp_type")

    p_sign = sub.add_parser("sign", help="pin instrument configs and flip draft->signed")
    p_sign.add_argument("slug")

    p_repin = sub.add_parser(
        "repin",
        help="repair pinned instrument file(s) on a signed experiment (audited, pre-run only)",
    )
    p_repin.add_argument("slug")
    p_repin.add_argument(
        "relpaths", nargs="+", metavar="relpath",
        help="experiment-relative pinned file(s) to re-hash",
    )
    p_repin.add_argument(
        "--reason", required=True,
        help="why the repin is needed; recorded in the instrument.repins audit trail",
    )

    p_list = sub.add_parser("list", help="table of all experiments")
    p_list.add_argument("--status", choices=STATUSES, default=None)
    p_list.add_argument("--type", choices=TYPES, default=None, dest="exp_type")

    p_show = sub.add_parser("show", help="pretty-print one manifest and resolved paths")
    p_show.add_argument("slug")

    p_resolve = sub.add_parser("resolve", help="stamp a verdict and flip to a terminal status")
    p_resolve.add_argument("slug")
    p_resolve.add_argument("--verdict", required=True)
    p_resolve.add_argument(
        "--status", default="resolved", choices=sorted(RESOLVED_STATES),
        help="terminal status (default: resolved)",
    )

    sub.add_parser("validate", help="validate every manifest under experiments/")

    p_regen = sub.add_parser("regen", help="regenerate the registry files")
    p_regen.add_argument("--check", action="store_true",
                         help="fail if the committed registry is stale")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve() if args.root else find_repo_root()
        if args.command == "new":
            return cmd_new(root, args.slug, args.exp_type, title=args.title)
        if args.command == "sign":
            return cmd_sign(root, args.slug)
        if args.command == "repin":
            return cmd_repin(root, args.slug, args.relpaths, args.reason)
        if args.command == "list":
            return cmd_list(root, args.status, args.exp_type)
        if args.command == "show":
            return cmd_show(root, args.slug)
        if args.command == "resolve":
            return cmd_resolve(root, args.slug, args.verdict, args.status)
        if args.command == "validate":
            return validate(root)
        if args.command == "regen":
            return regen(root, check=args.check)
    except ExpError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown command {args.command!r}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
