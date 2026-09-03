"""tests/synaptic_host/test_cause_line.py

The shared cause-line renderer (architecture sections 20.11, 22.14, 24.4).

B-15 presented as INTERNAL_FAILURE exit 4 with an all-null envelope and an
EMPTY stderr, so the operator was told a run failed and nothing whatever about
where.  Ruling two refuses to widen the result envelope -- it is rebuilt
field-for-field and equality-checked at two sites and it is the contract the
driver parses -- and reports the cause on stderr instead, reusing the
mechanism 20.11 already ruled for admission.

The renderer had to move out of `docker_training.py` first: that module
imports the engine at module scope, so `cli.py` cannot import from it, least
of all to report that importing it failed.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from synaptic_host import cause_line, cli
from synaptic_host.cli import TrainingRunCommandCodeV2


_RELEASE_ROOT = Path(cli.__file__).resolve().parents[1]
_ENGINE_ROOT = _RELEASE_ROOT / "synaptic-tuner"

_LAYOUT_PRESENT = pytest.mark.skipif(
    not _ENGINE_ROOT.is_dir(),
    reason="needs the release-shaped layout (synaptic-tuner beside synaptic_host)",
)


def _scrubbed_env() -> dict[str, str]:
    """The operator environment run 9 used: no PYTHONPATH, no credentials."""

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    for name in list(env):
        upper = name.upper()
        if any(mark in upper for mark in ("SECRET", "PASSWORD", "CREDENTIAL")):
            del env[name]
        elif upper.endswith("_KEY") or "API_KEY" in upper:
            del env[name]
    return env


def test_the_renderer_imports_nothing_from_the_engine_or_docker_training() -> None:
    """Section 24.4 item 1.  The reason the module exists at all.

    `cli.py` must be able to import the renderer on the path where importing
    the engine has just failed.  If the renderer reached for the engine, or
    for `docker_training` which imports the engine at module scope, the
    diagnostic would die of the very fault it reports.
    """

    source = Path(cause_line.__file__).read_text(encoding="utf-8")
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    for name in imported:
        head = name.split(".")[0]
        assert head not in ("synaptic_tuner", "tuner"), name
        assert "docker_training" not in name, name


def test_cause_line_names_the_missing_module_for_a_module_not_found_error(
    capsys,
) -> None:
    """Section 24.4 item 2.  The authored, useful identity for an import fault.

    CPython produces `.name` as a dotted identifier, never a path and never
    operator text, so it passes the same test the class name passes.  It is
    also the field that separates B-15's real cut from the shallower failure a
    bare import produces: `tuner` against `synaptic_tuner`.
    """

    try:
        raise ModuleNotFoundError("No module named 'tuner'", name="tuner")
    except ModuleNotFoundError as error:
        cause_line.report_cause_line_v1(
            error, TrainingRunCommandCodeV2.INTERNAL_FAILURE,
        )

    line = capsys.readouterr().err.strip()
    assert line.startswith("synaptic-host: INTERNAL_FAILURE ModuleNotFoundError")
    assert "'tuner'" in line
    # The exception's own text is still excluded entirely, exactly as 20.11
    # ruled; only the class and the dotted name survive.
    assert "No module named" not in line


def test_cause_line_adds_no_module_clause_for_other_exceptions(capsys) -> None:
    """The clause is added when, and ONLY when, the exception carries one.

    Without this the module clause could be satisfied by a renderer that
    always appended something, and the negative case is what makes the
    positive one mean anything.
    """

    try:
        raise ValueError("plain")
    except ValueError as error:
        cause_line.report_cause_line_v1(
            error, TrainingRunCommandCodeV2.INTERNAL_FAILURE,
        )

    line = capsys.readouterr().err.strip()
    assert line.startswith("synaptic-host: INTERNAL_FAILURE ValueError at ")
    assert "'" not in line


def test_cause_line_carries_no_text_no_path_and_no_traceback(capsys) -> None:
    """20.11's exclusions, unchanged by the move."""

    secret_shaped = "AKIA" + "Z" * 36
    absolute = "C:\\Users\\operator\\project\\.synaptic\\state"
    try:
        raise ModuleNotFoundError(
            "{} rejected {}".format(absolute, secret_shaped), name="tuner",
        )
    except ModuleNotFoundError as error:
        cause_line.report_cause_line_v1(
            error, TrainingRunCommandCodeV2.INTERNAL_FAILURE,
        )

    line = capsys.readouterr().err.strip()
    assert secret_shaped not in line
    assert absolute not in line and "operator" not in line
    assert "Traceback" not in line
    assert len(line) <= cause_line._CAUSE_LINE_LIMIT


def test_the_package_anchor_is_the_package_not_this_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Counter-test for the anchor.  The lead's ruling on the renderer move.

    `_innermost_package_frame` renders frames relative to a package root.  If
    that root were derived from the renderer module's own `__file__`, moving
    the module into a subpackage would put every real frame outside the anchor
    and silently degrade both call sites to "<unknown>" with nothing failing.
    So the anchor is asserted to be the package directory, and then sabotaged:
    pointed somewhere no frame can be relative to, the frame must go
    "<unknown>".  A renderer that reported a frame either way would not be
    measuring the anchor at all.
    """

    assert cause_line._package_root() == Path(cli.__file__).resolve().parent

    # An exception whose deepest frame genuinely lies inside the package.
    original = cause_line._ROOT_PACKAGE
    try:
        cause_line._ROOT_PACKAGE = "a_package_that_is_not_imported"
        try:
            cause_line._package_root()
        except RuntimeError as error:
            in_package = error
    finally:
        cause_line._ROOT_PACKAGE = original

    rendered = cause_line._innermost_package_frame(in_package)
    assert "synaptic_host/cause_line.py:" in rendered
    assert rendered.endswith(" in _package_root")

    # Sabotage the anchor.  Every real frame now falls outside it, so the
    # renderer must say so rather than invent a location.  A renderer that
    # reported a frame either way would not be measuring the anchor at all.
    monkeypatch.setattr(
        cause_line, "_package_root", lambda: Path("/nowhere/at/all"),
    )
    assert cause_line._innermost_package_frame(in_package) == "<unknown>"


@_LAYOUT_PRESENT
def test_dispatch_reports_the_import_failure_and_leaves_the_envelope_alone(
) -> None:
    """P3 of section 24.5, at the real site: `cli.py`'s bare catch.

    An `ImportError` is injected at the `:973` import site, which is the fault
    B-15 actually produced.  Two things are asserted together because ruling
    two is exactly that pair: the stderr names the class and the missing
    module, AND the envelope is untouched -- no new field, and the bare
    `_failure` at the catch still returns the null-shaped result the schema
    already had.  24.5's P2 is satisfied at the cuts whose code path already
    carries the four refs; this cut is not one of them, and that is recorded
    rather than fixed, because ruling two forbids widening and filling the
    four names here would mean binding them above the `try`.

    In a CHILD process, and that is not incidental.  `_ENGINE_CONTRACT_CACHE`
    is process-global and the suite's earlier tests populate it against their
    own temporary engine roots, so an in-process version of this test passes
    alone and fails in the suite -- it would be measuring test order, not the
    Host.
    """

    harness = textwrap.dedent(
        """
        import sys
        from pathlib import Path

        root = Path.cwd()
        engine = root / "synaptic-tuner"
        sys.path.insert(0, str(root))

        from synaptic_host import cli

        prepared = cli.prepare_training_run_ingress_v1(
            ["training", "run", "--provider", "docker",
             "--config", "project://training/smokes/docker-sft.json",
             "--destination", "local-default"],
            project_root=root, engine_root=engine,
        )
        assert type(prepared) is cli.TrainingRunIngressV1, "ingress refused"

        real_import = cli.importlib.import_module

        def refuse(name, *args, **kwargs):
            if name == "synaptic_host.docker_training":
                raise ModuleNotFoundError(
                    "No module named 'tuner'", name="tuner",
                )
            return real_import(name, *args, **kwargs)

        cli.importlib.import_module = refuse

        result = cli.dispatch_validated_training_run_v1(
            prepared, isolated_child_authority=None,
            project_root=root, engine_root=engine,
        )

        assert result.code is cli.TrainingRunCommandCodeV2.INTERNAL_FAILURE
        assert result.provider_ref is None
        assert result.config_ref is None
        assert result.destination_ref is None
        assert result.input_digest is None
        print("DISPATCH-OK")
        """
    )

    completed = subprocess.run(
        [sys.executable, "-c", harness],
        cwd=str(_RELEASE_ROOT),
        env=_scrubbed_env(),
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert "DISPATCH-OK" in completed.stdout, (
        "stdout={!r} stderr={!r}".format(
            completed.stdout[-400:], completed.stderr[-800:],
        )
    )

    line = completed.stderr.strip().splitlines()[-1]
    assert line.startswith("synaptic-host: INTERNAL_FAILURE ModuleNotFoundError")
    assert "'tuner'" in line
    assert "Traceback" not in completed.stderr
    assert str(_RELEASE_ROOT) not in completed.stderr
