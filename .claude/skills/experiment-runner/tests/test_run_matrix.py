#!/usr/bin/env python3
"""CODE-phase smoke tests for the WS-5 experiment runner.

Scope (smoke, not exhaustive TEST-phase coverage): does the matrix expand to the
pre-registered counts, does a count typo ABORT, does the prereq gate fail/skip in
the right modes, does recipe materialization apply the right single override and
rewrite the staged dataset path, and does the run record carry the data block +
dual SHAs? NO network, NO model downloads, NO training launches — the hub query
and git plumbing are monkeypatched / fixtured.

Run:
    python -m pytest .claude/skills/experiment-runner/tests/test_run_matrix.py -q
"""

import copy
import json
from pathlib import Path

import pytest
import yaml

import check_prereqs as cp
import run_matrix as rm


# ---------------------------------------------------------------------------
# Fixtures — a tiny but PROTOCOL-shaped matrix + a stub recipe.
# ---------------------------------------------------------------------------


def _full_matrix():
    """The real matrix.yaml — the expansion must match the locked counts."""
    matrix_path = Path(rm.__file__).resolve().parent.parent / "config" / "matrix.yaml"
    return yaml.safe_load(matrix_path.read_text())


def _stub_recipe(method="dpo", model_tag="qwen3-4b-instruct", lr=5.0e-6):
    train = f"{'dpo' if method == 'dpo' else method}_train.jsonl"
    return {
        "name": f"eh-stub-{method}",
        "method": method,
        "target": "local",
        "model": {"name": "unsloth/Qwen3-4B-Instruct-bnb-4bit"},
        "dataset": {"local_file": f"experiment/phase1/data/{model_tag}/{train}"},
        "training": {"learning_rate": lr, "num_epochs": 1},
        "run": {"command": ["legacy run.command that must be stripped"],
                "workdir": "{tuner_root}"},
        "artifacts": {"output_root": "x/{name}"},
    }


# ---------------------------------------------------------------------------
# Matrix expansion + count assertions.
# ---------------------------------------------------------------------------


def test_matrix_expands_to_locked_counts():
    cells = rm.expand_matrix(_full_matrix())
    assert len(cells) == 30  # 19 @ 4B + 9 @ 8B + 2 bridge
    by_size = {}
    for c in cells:
        by_size.setdefault(c.coordinate.size, 0)
        by_size[c.coordinate.size] += 1
    assert by_size["4b"] == rm.EXPECTED_COUNT_4B == 19
    assert by_size["8b"] == rm.EXPECTED_COUNT_8B == 9
    assert by_size["bridge"] == rm.EXPECTED_COUNT_BRIDGE == 2


def test_4b_block_breakdown():
    cells = rm.expand_4b(_full_matrix())
    kinds = {}
    for c in cells:
        kinds.setdefault(c.coordinate.cell_type, 0)
        kinds[c.coordinate.cell_type] += 1
    assert kinds["headline"] == 9   # 3 arms x 3 seeds
    assert kinds["lr_panel"] == 6   # 3 arms x 2 multipliers
    assert kinds["beta_panel"] == 4  # 2 arms (dpo, kto) x 2 betas


def test_count_assertion_aborts_on_extra_arm():
    """A matrix typo that changes a count must ABORT, not silently expand."""
    bad = copy.deepcopy(_full_matrix())
    bad["arms_4b"].append({"recipe": "rogue", "method": "sft", "has_beta": False})
    with pytest.raises(rm.MatrixError):
        rm.expand_4b(bad)


def test_count_assertion_aborts_on_missing_seed():
    bad = copy.deepcopy(_full_matrix())
    bad["seeds_headline"] = [1, 2]  # 2 seeds -> 4B count drifts below 19
    with pytest.raises(rm.MatrixError):
        rm.expand_4b(bad)


def test_beta_panel_skips_sft():
    """SFT has has_beta=false, so it gets no beta-panel cells."""
    cells = rm.expand_4b(_full_matrix())
    beta_arms = {c.method for c in cells if c.coordinate.cell_type == "beta_panel"}
    assert beta_arms == {"dpo", "kto"}
    assert "sft" not in beta_arms


# ---------------------------------------------------------------------------
# Recipe materialization.
# ---------------------------------------------------------------------------


def test_materialize_sft_sets_seed_and_strips_run_command():
    """SFT stays native through the handler — its legacy run.command/workdir are
    stripped and NO command is injected (the handler builds it)."""
    base = _stub_recipe(method="sft")
    cell = rm.Cell(rm.Coordinate("sft", "4b", "headline", 2), "eh-stub-sft", "sft")
    out = rm.materialize_recipe(base, cell, "local")
    assert out["training"]["seed"] == 2
    # Declarative: the legacy run.command/workdir must be stripped, none injected.
    assert "command" not in out.get("run", {})
    assert "workdir" not in out.get("run", {})
    # The base recipe is untouched (deep copy).
    assert "command" in base["run"]


def test_materialize_local_dpo_stays_declarative():
    """Local DPO route through the NATIVE handler (arch §9.2, re-ruled): the
    handler builds the trainer command from run.trainer + the training block, so
    materialize_recipe injects NO run.command — the materialized recipe is purely
    declarative. seed/beta live in the training block, not a command string."""
    base = _stub_recipe(method="dpo")
    base["training"]["beta"] = 0.1
    cell = rm.Cell(rm.Coordinate("dpo", "4b", "headline", 3), "eh-stub-dpo", "dpo")
    out = rm.materialize_recipe(base, cell, "local")
    assert "command" not in out.get("run", {})
    assert "workdir" not in out.get("run", {})
    # The overrides land in the declarative training block, for the handler to read.
    assert out["training"]["seed"] == 3
    assert out["training"]["beta"] == 0.1


def test_materialize_local_kto_stays_declarative_with_seed_zero():
    """seed=0 is carried in the training block (no injected command); the handler
    forwards it with is-not-None semantics."""
    base = _stub_recipe(method="kto")
    cell = rm.Cell(rm.Coordinate("kto", "4b", "headline", 0), "eh-stub-kto", "kto")
    out = rm.materialize_recipe(base, cell, "local")
    assert "command" not in out.get("run", {})
    assert out["training"]["seed"] == 0


def test_materialize_local_sft_does_not_inject_command():
    """SFT on the local lane stays declarative too — no injected command."""
    base = _stub_recipe(method="sft")
    cell = rm.Cell(rm.Coordinate("sft", "4b", "headline", 1), "eh-stub-sft", "sft")
    out = rm.materialize_recipe(base, cell, "local")
    assert "command" not in out.get("run", {})


def test_materialize_cloud_dpo_does_not_inject_command():
    """Cloud DPO cells go through the cloud command builder — no injected
    run.command. (No lane injects: both drive the tuner declaratively.)"""
    base = _stub_recipe(method="dpo")
    cell = rm.Cell(rm.Coordinate("dpo", "8b", "confirm", 1), "eh-stub-dpo", "dpo")
    out = rm.materialize_recipe(base, cell, "cloud")
    assert "command" not in out.get("run", {})


def test_materialize_lr_is_per_arm_relative():
    """The LR override scales the recipe's OWN default LR, not a hardcoded value."""
    base = _stub_recipe(lr=5.0e-6)  # DPO default
    cell = rm.Cell(rm.Coordinate("dpo", "4b", "lr_panel", 1, ("learning_rate", 3.0)),
                   "eh-stub-dpo", "dpo")
    out = rm.materialize_recipe(base, cell)
    assert out["training"]["learning_rate"] == pytest.approx(5.0e-6 * 3.0)


def test_materialize_beta_override():
    base = _stub_recipe(method="kto")
    cell = rm.Cell(rm.Coordinate("kto", "4b", "beta_panel", 1, ("beta", 0.05)),
                   "eh-stub-kto", "kto")
    out = rm.materialize_recipe(base, cell)
    assert out["training"]["beta"] == 0.05


def test_run_id_is_deterministic_and_unique():
    cells = rm.expand_matrix(_full_matrix())
    ids = [c.coordinate.run_id() for c in cells]
    assert len(ids) == len(set(ids)), "run ids must be unique"


# ---------------------------------------------------------------------------
# Data staging (local lane) — path rewrite + sha.
# ---------------------------------------------------------------------------


def test_stage_local_data_rewrites_to_tuner_relative_path(tmp_path):
    data_root = tmp_path / "data"
    model_dir = data_root / "qwen3-4b-instruct"
    model_dir.mkdir(parents=True)
    (model_dir / "dpo_train.jsonl").write_text('{"a": 1}\n')
    (model_dir / "dpo_dev.jsonl").write_text('{"b": 2}\n')
    tuner_root = tmp_path / "synaptic-tuner"
    block = rm.stage_local_data(
        data_root=data_root, model_tag="qwen3-4b-instruct",
        train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
        tuner_root=tuner_root, run_id="dpo__4b__headline__seed1")
    # Staged path is tuner-repo-relative and under the already-gitignored scratch.
    assert block["staged_data_file"].startswith("scratch/eh_staging/")
    assert (tuner_root / block["staged_data_file"]).is_file()
    assert len(block["data_sha256"]) == 64


# ---------------------------------------------------------------------------
# Prereq gate — failure + skip modes.
# ---------------------------------------------------------------------------


def _write_manifest(data_root: Path, model_tag: str, passed: bool):
    base = data_root / model_tag
    base.mkdir(parents=True, exist_ok=True)
    (base / cp.MANIFEST_FILENAME).write_text(
        json.dumps({"leakage_guard": {"passed": passed}}))


def _write_data(data_root: Path, model_tag: str, train: str, dev: str):
    base = data_root / model_tag
    base.mkdir(parents=True, exist_ok=True)
    (base / train).write_text("{}\n")
    (base / dev).write_text("{}\n")


def test_gate_aborts_on_missing_datasets(tmp_path):
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    with pytest.raises(cp.PrereqError):
        cp.check_cell(lane="local", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path)


def test_gate_aborts_on_leakage_guard_absent(tmp_path):
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    # No manifest written -> leakage guard cannot be confirmed -> abort.
    with pytest.raises(cp.PrereqError):
        cp.check_cell(lane="local", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path)


def test_gate_aborts_on_leakage_guard_failed(tmp_path):
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=False)
    with pytest.raises(cp.PrereqError):
        cp.check_cell(lane="local", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path)


def _write_local_capability_tree(root, *, handler_seed=True, handler_beta=True,
                                 sft_only_gate=False, trainer_lora=True):
    """Build a fake tuner tree with the HANDLER-EXTENSION + LoRA-PARITY LOCAL-lane
    forwarding surface (§9.2 :994-1013 + (d) item 5, lead-ratified final; tuner #34).
    The handler forwards `seed` AND `beta` and — once #34 lands — no longer gates
    dispatch to SFT only; the dpo/kto trainers accept every `--lora-*` scalar flag.
    Toggle sft_only_gate=True to model the pre-#34 dispatch wart, handler_beta=False
    / handler_seed=False to drop a handler forward, and trainer_lora=False to drop
    the trainer LoRA-parity surface — each must keep the probe closed."""
    tuner = root / "synaptic-tuner"
    handlers = tuner / "tuner" / "handlers"
    handlers.mkdir(parents=True, exist_ok=True)
    body = "def _build_sft_command(self, cfg, variables):\n    command = []\n"
    if handler_seed:
        body += '    _append_flag(command, "seed", training_cfg.get("seed"))\n'
    if handler_beta:
        body += '    _append_flag(command, "beta", training_cfg.get("beta"))\n'
    body += "\ndef _compile(self, config_path, cfg):\n"
    if sft_only_gate:
        # The artificial pre-#34 limit: dispatch is gated to sft only.
        body += '    elif method == "sft":\n        command = self._build_sft_command(cfg, variables)\n'
    else:
        # #34 widened the guard to route all registered methods.
        body += '    elif method in ("sft", "dpo", "kto"):\n        command = self._build_sft_command(cfg, variables)\n'
    (handlers / "local_run_handler.py").write_text(body)
    # LoRA flag parity (§9.2(d) item 5): dpo/kto trainers must accept every --lora-*
    # scalar the builder emits, or the recipe's §5.2 budget SSOT is silently dropped.
    lora_flags = ("--lora-r", "--lora-alpha", "--lora-dropout",
                  "--lora-target-modules", "--init-lora-weights")
    for method in ("dpo", "kto"):
        td = tuner / "Trainers" / method
        td.mkdir(parents=True, exist_ok=True)
        tbody = "def build_parser(p):\n    p.add_argument('--seed', type=int)\n"
        if trainer_lora:
            for flag in lora_flags:
                tbody += f"    p.add_argument('{flag}')\n"
        (td / f"train_{method}.py").write_text(tbody)


def test_gate_passes_local_when_data_guard_and_capability_ok(tmp_path):
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    _write_local_capability_tree(tmp_path)  # per-method local surface present
    res = cp.check_cell(lane="local", method="dpo", model_tag="qwen3-4b-instruct",
                        train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                        data_root=tmp_path, research_repo_root=tmp_path)
    assert res.ok and not res.skip


def test_gate_aborts_local_when_capability_not_landed(tmp_path):
    """The tuner-capability gate is a WHOLE-MATRIX ABORT, not a cell skip (§9.2(d)
    item 5): a missing seed/beta/LoRA sink corrupts the entire headline+panel design,
    not one arm. No local forwarding surface → probe False → PrereqError (abort)."""
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    # No tuner tree → local probe fails closed → whole-matrix abort.
    with pytest.raises(cp.PrereqError, match="ABORTS the whole matrix"):
        cp.check_cell(lane="local", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path)


def test_local_probe_false_when_handler_omits_beta(tmp_path):
    """Handler-extension contract (tuner #34): the handler must forward BOTH seed
    and beta. With beta absent — the pre-#34 state — the probe fails closed even
    though seed is forwarded and dispatch is widened."""
    _write_local_capability_tree(tmp_path, handler_beta=False)
    assert cp.local_seed_beta_capability_probe(tmp_path) is False


def test_local_probe_false_when_handler_omits_seed(tmp_path):
    _write_local_capability_tree(tmp_path, handler_seed=False)
    assert cp.local_seed_beta_capability_probe(tmp_path) is False


def test_local_probe_false_when_dispatch_still_sft_only(tmp_path):
    """The pre-#34 wart is the `elif method == "sft"` dispatch gate. While it
    survives, local-run rejects dpo/kto, so the probe must stay closed even if the
    handler already forwards seed+beta."""
    _write_local_capability_tree(tmp_path, sft_only_gate=True)
    assert cp.local_seed_beta_capability_probe(tmp_path) is False


def test_local_probe_false_when_trainer_lora_parity_missing(tmp_path):
    """LoRA flag parity (§9.2(d) item 5): even with the handler fully extended, the
    probe must stay closed until train_dpo.py/train_kto.py accept every --lora-*
    scalar — a missing LoRA sink silently mistrains every local dpo/kto arm at the
    wrong §5.2 budget (whole-matrix-corruption class)."""
    _write_local_capability_tree(tmp_path, trainer_lora=False)
    assert cp.local_seed_beta_capability_probe(tmp_path) is False


def test_local_probe_true_when_handler_extended_and_lora_parity(tmp_path):
    """Post-#34: handler forwards seed+beta, dispatch widened past SFT-only, AND the
    dpo/kto trainers carry --lora-* parity."""
    _write_local_capability_tree(tmp_path)
    assert cp.local_seed_beta_capability_probe(tmp_path) is True


def test_gate_skips_bridge_when_prereqs_absent(tmp_path):
    _write_data(tmp_path, "bridge_llama2_7b_chat", "sft_train.jsonl", "sft_dev.jsonl")
    _write_manifest(tmp_path, "bridge_llama2_7b_chat", passed=True)
    res = cp.check_cell(lane="local", method="sft", model_tag="bridge_llama2_7b_chat",
                        train_file="sft_train.jsonl", dev_file="sft_dev.jsonl",
                        data_root=tmp_path, research_repo_root=tmp_path,
                        is_bridge=True, bridge_prereqs_present=False)
    assert res.ok and res.skip and "bridge" in res.skip_reason.lower()


def test_gate_aborts_cloud_when_capability_missing(tmp_path):
    """The tuner-capability gate ABORTS the whole matrix on both lanes (§9.2(d)
    item 5) — a missing seed/beta sink corrupts the entire seed sweep + beta panel,
    so a partial cloud run is meaningless. No cloud capability surface → abort."""
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    with pytest.raises(cp.PrereqError, match="ABORTS the whole matrix"):
        cp.check_cell(lane="cloud", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path,
                      dataset_name="org/eh-phase1-qwen3-4b-dpo")


def test_gate_cloud_skips_when_dataset_not_on_hub(tmp_path, monkeypatch):
    """With the capability surface present (probe True), an unpublished arm still
    SKIPs (item 3a). OPEN comes from the probe, never a forced flag."""
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    _write_tuner_capability_tree(tmp_path)  # cloud capability surface present
    monkeypatch.setattr(cp, "submodule_pushed", lambda root: True)
    monkeypatch.setattr(cp, "hf_token_present", lambda: True)
    monkeypatch.setattr(cp, "hub_dataset_revision", lambda name: None)  # not on hub
    res = cp.check_cell(lane="cloud", method="dpo", model_tag="qwen3-4b-instruct",
                        train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                        data_root=tmp_path, research_repo_root=tmp_path,
                        dataset_name="org/eh-phase1-qwen3-4b-dpo")
    assert res.ok and res.skip and "hub" in res.skip_reason.lower()


def test_gate_cloud_passes_and_pins_revision_when_published(tmp_path, monkeypatch):
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    _write_tuner_capability_tree(tmp_path)  # cloud capability surface present
    monkeypatch.setattr(cp, "submodule_pushed", lambda root: True)
    monkeypatch.setattr(cp, "hf_token_present", lambda: True)
    monkeypatch.setattr(cp, "hub_dataset_revision", lambda name: "abc123")
    res = cp.check_cell(lane="cloud", method="dpo", model_tag="qwen3-4b-instruct",
                        train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                        data_root=tmp_path, research_repo_root=tmp_path,
                        dataset_name="org/eh-phase1-qwen3-4b-dpo")
    assert res.ok and not res.skip
    assert res.details["hf_dataset_revision"] == "abc123"


def test_gate_aborts_bridge_on_cloud_lane(tmp_path):
    """Bridge cells are LOCAL-LANE ONLY (do-not-redistribute data): a bridge cell
    on the cloud lane ABORTS, it does not skip — it can never become runnable."""
    _write_data(tmp_path, "bridge_llama2_7b_chat", "sft_train.jsonl", "sft_dev.jsonl")
    _write_manifest(tmp_path, "bridge_llama2_7b_chat", passed=True)
    with pytest.raises(cp.PrereqError, match="LOCAL-LANE ONLY"):
        cp.check_cell(lane="cloud", method="sft", model_tag="bridge_llama2_7b_chat",
                      train_file="sft_train.jsonl", dev_file="sft_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path,
                      is_bridge=True, bridge_prereqs_present=True,
                      dataset_name="org/should-never-be-queried")


def test_select_invocation_rejects_bridge_on_cloud():
    """The dispatcher also refuses a bridge cell on the cloud lane (defense in
    depth: enforced at both the gate and the invocation builder)."""
    cell = rm.Cell(rm.Coordinate("sft", "bridge", "bridge", 1),
                   "eh-bridge-llama2-7b-chat-sft", "sft")
    recipe = _stub_recipe(method="sft", model_tag="bridge_llama2_7b_chat")
    with pytest.raises(rm.MatrixError, match="LOCAL-LANE ONLY"):
        rm.select_invocation(cell, "cloud",
                             materialized_recipe_path=Path("x.yaml"),
                             dataset_name=None, recipe=recipe)


def test_select_invocation_bridge_local_uses_local_run():
    """A bridge cell on the local lane dispatches to the local-run invocation
    (bridge arms are SFT/DPO; the SFT bridge routes through native local-run)."""
    cell = rm.Cell(rm.Coordinate("sft", "bridge", "bridge", 1),
                   "eh-bridge-llama2-7b-chat-sft", "sft")
    recipe = _stub_recipe(method="sft", model_tag="bridge_llama2_7b_chat")
    inv = rm.select_invocation(cell, "local",
                               materialized_recipe_path=Path("staged/x.yaml"),
                               dataset_name=None, recipe=recipe)
    assert inv[:3] == ["python", "tuner.py", "local-run"]


def test_local_invocation_is_uniform_local_run_for_all_methods():
    """Handler-extension: every method dispatches through the SAME native local-run
    verb with the declarative materialized recipe — no per-method branching, no
    trainer command synthesis."""
    inv = rm.local_invocation(Path("staged/x.yaml"))
    assert inv == ["python", "tuner.py", "local-run",
                   "--job-config", "staged/x.yaml", "--yes"]


def test_select_invocation_local_dpo_kto_use_local_run_no_trainer_argv():
    """select_invocation routes local DPO and KTO cells through native local-run
    (the handler dispatches them from run.method/run.trainer — NO direct trainer
    call). Structurally pins correction 3a: no `train_*.py` argv survives anywhere
    in a local invocation for any method."""
    for method in ("dpo", "kto", "sft"):
        cell = rm.Cell(rm.Coordinate(method, "4b", "headline", 2),
                       f"eh-stub-{method}", method)
        recipe = _stub_recipe(method=method)
        inv = rm.select_invocation(cell, "local",
                                   materialized_recipe_path=Path(f"staged/{method}.yaml"),
                                   dataset_name=None, recipe=recipe)
        assert inv[:3] == ["python", "tuner.py", "local-run"]
        assert "--job-config" in inv and f"staged/{method}.yaml" in inv
        # No direct-trainer argv leaked into the invocation for ANY method.
        assert not any(tok.startswith("train_") and tok.endswith(".py") for tok in inv)
        assert "--config" not in inv


def test_materialize_sets_run_method_and_trainer_per_method():
    """The materialized recipe is a complete self-describing job-config: run.method
    routes the handler's widened dispatch and run.trainer points at the per-method
    trainer script (the handler defaults run.trainer to the SFT path, so DPO/KTO
    MUST carry the right one)."""
    for method, recipe_name in (("dpo", "eh-stub-dpo"), ("kto", "eh-stub-kto"),
                                ("sft", "eh-stub-sft")):
        base = _stub_recipe(method=method)
        cell = rm.Cell(rm.Coordinate(method, "4b", "headline", 1), recipe_name, method)
        out = rm.materialize_recipe(base, cell, "local")
        assert out["run"]["method"] == method
        assert out["run"]["trainer"] == f"Trainers/{method}/train_{method}.py"
        # Still purely declarative — no synthesized command.
        assert "command" not in out["run"]


_SFT_TRAINER_DEFAULT = "Trainers/sft/train_sft.py"


def test_materialize_pins_dpo_kto_trainer_not_sft_default_even_without_run_block():
    """Structural pin for the silent-substitution hazard: the handler defaults
    run.trainer to the SFT trainer when a recipe omits it, which would make a DPO/KTO
    cell run the SFT trainer. materialize_recipe must set the per-method trainer even
    when the BASE recipe carries NO `run:` block at all (the exact state of the
    committed local-4B dpo/kto recipes). Assert-NOT-default for dpo/kto."""
    for method in ("dpo", "kto"):
        base = _stub_recipe(method=method)
        base.pop("run", None)  # committed dpo/kto recipes have no run: block
        assert "run" not in base
        cell = rm.Cell(rm.Coordinate(method, "4b", "headline", 1), f"eh-stub-{method}", method)
        out = rm.materialize_recipe(base, cell, "local")
        assert out["run"]["trainer"] != _SFT_TRAINER_DEFAULT  # not the silent default
        assert out["run"]["trainer"] == f"Trainers/{method}/train_{method}.py"
        assert out["run"]["method"] == method


def test_expander_aborts_bridge_on_cloud_lane():
    """Expansion-time belt-and-suspenders: a bridge cell with --lane cloud is a
    config error that aborts loudly (license containment)."""
    cells = rm.expand_matrix(_full_matrix())
    with pytest.raises(rm.MatrixError, match="LOCAL-LANE ONLY"):
        rm.assert_bridge_lane_safety(cells, "cloud")
    # Local lane: no abort (bridge cells are fine on local).
    rm.assert_bridge_lane_safety(cells, "local")


def test_dry_run_cloud_lane_aborts_when_bridge_present(monkeypatch, capsys):
    """The full --dry-run path aborts on cloud lane because the matrix carries
    bridge cells (the expander guard fires before any per-cell work)."""
    with pytest.raises(rm.MatrixError, match="LOCAL-LANE ONLY"):
        rm.main(["--dry-run", "--lane", "cloud"])


def test_bridge_recipes_declare_target_local():
    """Both bridge recipes must carry target: local (not 'both') — the license
    containment is also declared in the recipe, not only enforced by the runner."""
    # scripts/run_matrix.py → .../.claude/skills/experiment-runner/scripts;
    # the repo root is the parent of the .claude dir.
    skill_dir = Path(rm.__file__).resolve().parent.parent  # experiment-runner
    repo_root = skill_dir.parent.parent.parent  # skills → .claude → repo root
    recipes_dir = repo_root / "experiment" / "phase1" / "recipes"
    for name in ("eh_bridge_llama2_7b_chat_sft", "eh_bridge_llama2_7b_chat_dpo"):
        recipe = yaml.safe_load((recipes_dir / f"{name}.yaml").read_text())
        assert recipe["target"] == "local", f"{name} must be target: local"


# ---------------------------------------------------------------------------
# Cloud capability probe — live-check the tuner source surface, not a flag.
# ---------------------------------------------------------------------------


def _write_tuner_capability_tree(root, *, config=True, builder=True, parser=True):
    """Build a fake synaptic-tuner tree with controllable surface presence.

    Each element mirrors the real seed/beta-forwarding contract: a
    CloudTrainingConfig with seed/beta fields, a builder emitting --seed/--beta,
    and the --train-seed/--train-beta CLI flags.
    """
    tuner = root / "synaptic-tuner"
    cfg = tuner / "tuner" / "core"
    bld = tuner / "tuner" / "backends" / "training" / "cloud"
    cli = tuner / "tuner" / "cli"
    for d in (cfg, bld, cli):
        d.mkdir(parents=True, exist_ok=True)
    cfg_body = "class CloudTrainingConfig(TrainingConfig):\n    learning_rate: float\n"
    if config:
        cfg_body += "    seed: Optional[int] = None\n    beta: Optional[float] = None\n"
    (cfg / "config.py").write_text(cfg_body)
    bld_body = 'def _build_training_command(self, config):\n    args = []\n'
    if builder:
        bld_body += '    args.extend(["--seed", str(config.seed)])\n'
        bld_body += '    args.extend(["--beta", str(config.beta)])\n'
    (bld / "_hf_command_builder.py").write_text(bld_body)
    cli_body = 'def build_parser(p):\n'
    if parser:
        cli_body += '    p.add_argument("--train-seed", type=int)\n'
        cli_body += '    p.add_argument("--train-beta", type=float)\n'
    else:
        cli_body += '    p.add_argument("--something-else")\n'
    (cli / "parser.py").write_text(cli_body)


def test_cloud_probe_true_when_full_surface_present(tmp_path):
    _write_tuner_capability_tree(tmp_path)
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is True


def test_cloud_probe_false_when_config_fields_absent(tmp_path):
    _write_tuner_capability_tree(tmp_path, config=False)
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is False


def test_cloud_probe_false_when_builder_does_not_emit(tmp_path):
    _write_tuner_capability_tree(tmp_path, builder=False)
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is False


def test_cloud_probe_false_when_cli_flags_absent(tmp_path):
    _write_tuner_capability_tree(tmp_path, parser=False)
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is False


def test_cloud_probe_fails_closed_when_tuner_absent(tmp_path):
    """No tuner tree at all → probe returns False (never green-light a launch)."""
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is False


def test_cloud_probe_false_against_pre32_baseline(tmp_path):
    """The 9b6ecc0 baseline (pre-#32): CloudTrainingConfig has no seed/beta and
    the builder emits neither flag → probe returns False (the ruling's required
    'False against current 9b6ecc0' check)."""
    tuner = tmp_path / "synaptic-tuner"
    cfg = tuner / "tuner" / "core"
    bld = tuner / "tuner" / "backends" / "training" / "cloud"
    cli = tuner / "tuner" / "cli"
    for d in (cfg, bld, cli):
        d.mkdir(parents=True, exist_ok=True)
    # Baseline config: learning_rate only, no seed/beta on CloudTrainingConfig.
    (cfg / "config.py").write_text(
        "class CloudTrainingConfig(TrainingConfig):\n    learning_rate: float\n")
    # Baseline builder: emits --learning-rate but not --seed / --beta.
    (bld / "_hf_command_builder.py").write_text(
        'def _build_training_command(self, config):\n'
        '    args = ["--learning-rate", str(config.learning_rate)]\n')
    # Baseline CLI: no --train-seed / --train-beta.
    (cli / "parser.py").write_text(
        'def build_parser(p):\n    p.add_argument("--train-lr", type=float)\n')
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is False


def test_cloud_probe_true_against_post32_surface(tmp_path):
    """A fixture mimicking the post-#32 surface returns True (ruling's paired
    check). Distinct from the baseline test above."""
    _write_tuner_capability_tree(tmp_path)
    assert cp.cloud_seed_beta_capability_probe(tmp_path) is True


def test_override_can_force_closed_but_never_open(tmp_path, monkeypatch):
    """FORCE_SEED_BETA_GATE_CLOSED is a ONE-WAY override: it can force CLOSED even
    when the probe would pass, but there is NO flag that can force OPEN — the OPEN
    decision always comes from the live probe. This is the ruling's anti-desync
    requirement (a hand-flipped True must not re-open the lane)."""
    # Full surface present → probe would pass → but forced CLOSED stays closed.
    _write_tuner_capability_tree(tmp_path)
    monkeypatch.setattr(cp, "FORCE_SEED_BETA_GATE_CLOSED", True)
    assert cp.cloud_capability_ready(tmp_path) is False
    # No surface + not forced closed → probe decides → still CLOSED (no flag can
    # force it open).
    monkeypatch.setattr(cp, "FORCE_SEED_BETA_GATE_CLOSED", False)
    assert cp.cloud_capability_ready(tmp_path / "empty") is False


def test_cloud_capability_default_uses_live_probe(tmp_path):
    """With no forced-closed override, the gate result IS the live probe."""
    _write_tuner_capability_tree(tmp_path)
    assert cp.cloud_capability_ready(tmp_path) is True
    _write_tuner_capability_tree(tmp_path, builder=False)
    assert cp.cloud_capability_ready(tmp_path) is False


def test_gate_cloud_cell_aborts_when_probe_fails(tmp_path):
    """check_cell ABORTS the whole matrix (not skip) when the cloud capability probe
    fails — the gate is keyed to the live probe, no flag forces it open (§9.2(d)
    item 5: a missing seed/beta sink corrupts the entire seed sweep + beta panel)."""
    _write_data(tmp_path, "qwen3-4b-instruct", "dpo_train.jsonl", "dpo_dev.jsonl")
    _write_manifest(tmp_path, "qwen3-4b-instruct", passed=True)
    # No tuner tree under tmp_path → probe fails → whole-matrix abort.
    with pytest.raises(cp.PrereqError, match="ABORTS the whole matrix"):
        cp.check_cell(lane="cloud", method="dpo", model_tag="qwen3-4b-instruct",
                      train_file="dpo_train.jsonl", dev_file="dpo_dev.jsonl",
                      data_root=tmp_path, research_repo_root=tmp_path,
                      dataset_name="org/eh-phase1-qwen3-4b-dpo")


# ---------------------------------------------------------------------------
# Run records — data block + dual SHAs.
# ---------------------------------------------------------------------------


def test_run_record_carries_data_block_and_dual_shas(monkeypatch):
    monkeypatch.setattr(rm, "git_head", lambda root: "deadbeef")
    base = _stub_recipe()
    cell = rm.Cell(rm.Coordinate("dpo", "4b", "headline", 1), "eh-stub-dpo", "dpo")
    materialized = rm.materialize_recipe(base, cell)
    text = yaml.safe_dump(materialized)
    data_block = {"source_data_file": "experiment/phase1/data/qwen3-4b-instruct/dpo_train.jsonl",
                  "staged_data_file": "scratch/eh_staging/x/dpo_train.jsonl",
                  "hf_dataset_name": None, "hf_dataset_revision": None}
    record = rm.build_run_record(
        cell=cell, recipe=materialized, materialized_text=text, lane="local",
        research_repo_root=Path("."), data_block=data_block, status="launched",
        tuner_invocation=["python", "tuner.py", "local-run"], prereq_details={})
    assert record["research_repo_commit"] == "deadbeef"
    assert record["submodule_commit"] == "deadbeef"
    assert record["data"]["staged_data_file"].startswith("scratch/eh_staging/")
    assert record["outcome"]["verified"] is False
    assert len(record["materialized_recipe_sha"]) == 64


def test_dry_run_main_does_not_launch(capsys):
    """--dry-run expands + asserts counts and returns 0 without launching."""
    rc = rm.main(["--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Count assertions PASSED" in out


def test_bare_main_refuses_to_launch(capsys):
    """A launch without --dry-run/--check-only is refused (no implicit cost)."""
    rc = rm.main([])
    assert rc == 1


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
