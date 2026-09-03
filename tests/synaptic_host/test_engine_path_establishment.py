"""tests/synaptic_host/test_engine_path_establishment.py

B-15 (architecture section 24.3, 24.5 P1/P3/P4, 24.6).  The Host never put the
engine root on `sys.path` for provider `docker`: `cli.py:743-750` inserts the
root for the contract loader and deletes it again, and the docker branch below
`:972` re-imports the engine at `docker_training.py:18` with nothing to resolve
it.  Runs 1 to 8 only passed because the operator's wrapper exported
`PYTHONPATH`; run 9 used the documented invocation and died at cut 1.

These tests pin the ruled establishment: appended (never inserted at 0),
idempotent, kept for the process lifetime, and placed after the bound-root
equality check so the process never gains an import root that was not already
proven to be the bound one.

The acceptance test runs in a CHILD process because no in-process test can
reach this bound: the parent pytest already carries whatever `sys.path` the
developer's environment gave it (standing rule 21.2).
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from synaptic_host import cli


# The release-shaped layout is the checkout itself: a project root holding
# `synaptic_host/` with `synaptic-tuner/` beside it, which is exactly what
# `__main__.py:19-20` derives the two roots from.
_RELEASE_ROOT = Path(cli.__file__).resolve().parents[1]
_ENGINE_ROOT = _RELEASE_ROOT / "synaptic-tuner"

_LAYOUT_PRESENT = pytest.mark.skipif(
    not _ENGINE_ROOT.is_dir(),
    reason="needs the release-shaped layout (synaptic-tuner beside synaptic_host)",
)


def _scrubbed_env() -> dict[str, str]:
    """The operator environment run 9 used: no PYTHONPATH, no credentials.

    `PYTHONPATH` is REMOVED rather than set empty; an empty value is still a
    value and CPython treats it as a single empty path entry, which is not the
    shape the documented invocation has.  Credential-shaped keys are dropped
    because the child has no use for them and a fixture should not hand a
    subprocess secrets it does not need.
    """

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    for name in list(env):
        upper = name.upper()
        if any(mark in upper for mark in ("SECRET", "PASSWORD", "CREDENTIAL")):
            del env[name]
        elif upper.endswith("_KEY") or "API_KEY" in upper:
            del env[name]
    return env


def _run_child(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(cwd),
        env=_scrubbed_env(),
        capture_output=True,
        text=True,
        timeout=300,
    )


@_LAYOUT_PRESENT
def test_documented_invocation_gets_past_the_docker_training_import() -> None:
    """P1, the acceptance test.  Section 24.5.

    This runs the WHOLE documented invocation, not `import
    synaptic_host.docker_training`, and that distinction is the trap section
    24.5 names.  A bare import in a fresh process fails on `synaptic_tuner`
    (log 13 arm A).  The real run fails on `tuner` four frames deeper (log 12),
    because ingress preparation has already made `synaptic_tuner` resident in
    `sys.modules` by the time cut 1 runs, so only a genuinely top-level name
    still consults `sys.path`.  A fixture that stopped at the bare import would
    green a fix that leaves the real failure standing.
    """

    completed = _run_child(
        [
            "-m", "synaptic_host", "training", "run",
            "--provider", "docker",
            "--config", "project://training/smokes/docker-sft.json",
            "--destination", "local-default",
        ],
        cwd=_RELEASE_ROOT,
    )

    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert lines, "the child wrote no result JSON at all"
    envelope = json.loads(lines[-1])

    # Before the establishment this is INTERNAL_FAILURE exit 4 with an
    # all-null envelope and an empty stderr, which is precisely how B-15
    # presented in run 9.  Getting past `cli.py:973` means the import
    # resolved; the run may still fail later for want of a daemon, and any
    # such failure carries a different code.
    assert envelope["code"] != "INTERNAL_FAILURE", (
        "cut 1 still dies at the docker_training import; "
        "stderr={!r}".format(completed.stderr[-400:])
    )
    # The engine name that B-15 actually failed on must not appear as an
    # unresolved import anywhere in the child's diagnostics.
    assert "No module named 'tuner'" not in completed.stderr
    assert "No module named 'synaptic_tuner'" not in completed.stderr


def test_engine_root_is_appended_last_and_never_duplicated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P3.  Appended, idempotent, and never at position 0.

    Section 24.3 rules append over insert and says plainly that this is not a
    style preference: the release root and the engine root both carry `docs/`,
    `scripts/` and `tests/`, and the engine's `Tools/` is the project's
    `tools/` on a case-insensitive Windows filesystem.  Giving the engine
    precedence would let it shadow project modules by name.
    """

    engine = tmp_path / "synaptic-tuner"
    engine.mkdir()
    sentinel = "/sentinel-root-that-must-stay-first"
    monkeypatch.setattr(sys, "path", [sentinel, "/somewhere/else"])

    cli._establish_engine_import_root(engine)
    assert sys.path[-1] == str(engine)
    assert sys.path[0] == sentinel, "the engine root must never take precedence"

    # Repeated dispatches share one process; the entry is established once.
    cli._establish_engine_import_root(engine)
    cli._establish_engine_import_root(engine)
    assert sys.path.count(str(engine)) == 1


def test_the_establishment_sits_between_the_bound_root_check_and_the_import(
) -> None:
    """The establishment's POSITION is the ruling, not merely its presence.

    Section 24.3's first and load-bearing reason is that the point is
    DOWNSTREAM of validation: `:955-972` refuses with BOOTSTRAP_UNAVAILABLE
    unless the supplied roots equal the roots bound at module scope, so
    establishing the path after that check means the process never gains an
    import root that was not already proven to be the bound one.  A call that
    still ran, but ran above the check, would satisfy every behavioural
    assertion here and quietly discard that property, so the order is pinned
    rather than the effect alone.
    """

    source = textwrap.dedent(
        inspect.getsource(cli.dispatch_validated_training_run_v1)
    )
    tree = ast.parse(source).body[0]

    establishments = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "_establish_engine_import_root"
    ]
    assert len(establishments) == 1

    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", None) == "import_module"
        and any(
            isinstance(arg, ast.Constant)
            and arg.value == "synaptic_host.docker_training"
            for arg in node.args
        )
    ]
    assert len(imports) == 1

    comparisons = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        and any(
            isinstance(operand, ast.Name)
            and operand.id in ("bound_project_root", "bound_engine_root")
            for operand in [node.left, *node.comparators]
        )
    ]
    assert comparisons, "the bound-root equality check has moved or gone"

    assert max(node.lineno for node in comparisons) < establishments[0].lineno
    assert establishments[0].lineno < imports[0].lineno


@_LAYOUT_PRESENT
def test_contract_loader_is_unaffected_with_the_engine_root_already_appended(
) -> None:
    """P4.  The regression this fix could plausibly cause.  Section 24.6 row 1.

    `cli.py:743-750` is do-not-touch, and the ruling's claim is that the
    appended entry is idempotent with it: adding a path entry imports nothing,
    so the `:738-742` refusal that no `synaptic_tuner` may be resident still
    holds, and if `:743` inserts the same string at position 0 the `finally` at
    `:749-750` deletes that position-0 copy while the appended entry survives.

    This runs in a child so the process-global `_ENGINE_CONTRACT_CACHE` starts
    empty, which is the only state in which the `:743` branch is taken at all.
    """

    harness = textwrap.dedent(
        """
        import sys
        from pathlib import Path

        root = Path.cwd()
        engine = root / "synaptic-tuner"
        sys.path.insert(0, str(root))
        # The ruled establishment, already in place before the loader runs.
        sys.path.append(str(engine))

        from synaptic_host import cli

        prepared = cli.prepare_training_run_ingress_v1(
            ["training", "run", "--provider", "docker",
             "--config", "project://training/smokes/docker-sft.json",
             "--destination", "local-default"],
            project_root=root, engine_root=engine,
        )
        assert type(prepared) is cli.TrainingRunIngressV1, "ingress refused"

        cached = cli._ENGINE_CONTRACT_CACHE
        assert cached is not None, "the contract loader never populated"
        assert cached[0] == engine.resolve(strict=True)

        # The appended entry survives the loader's insert/delete window, is
        # still last, and the position-0 copy the window makes is gone.
        assert sys.path.count(str(engine)) == 1
        assert sys.path[-1] == str(engine)
        print("P4-OK")
        """
    )

    completed = _run_child(["-c", harness], cwd=_RELEASE_ROOT)
    assert "P4-OK" in completed.stdout, (
        "stdout={!r} stderr={!r}".format(
            completed.stdout[-400:], completed.stderr[-800:],
        )
    )
