from __future__ import annotations

import ast
from pathlib import Path

from synaptic_host.local_io_v1.model import LocalIOCodeV1


PACKAGE = Path(__file__).parents[3] / "synaptic_host" / "local_io_v1"


def test_package_has_no_public_convenience_exports() -> None:
    namespace: dict[str, object] = {}
    exec((PACKAGE / "__init__.py").read_text(encoding="utf-8"), namespace)
    assert namespace["__all__"] == ()


def test_local_io_boundary_has_no_engine_provider_database_or_process_imports() -> None:
    forbidden_roots = {
        "synaptic_tuner",
        "docker",
        "modal",
        "huggingface_hub",
        "runpod",
        "sqlite3",
        "subprocess",
    }
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden_roots), (path.name, imported & forbidden_roots)


def test_checked_in_storage_config_contains_no_credentials_or_absolute_paths() -> None:
    storage = Path(__file__).parents[3] / "training" / "storage.json"
    text = storage.read_text(encoding="utf-8")
    lowered = text.casefold()
    assert "token" not in lowered
    assert "password" not in lowered
    assert "secret" not in lowered
    assert '"location": "project://' in text


def test_no_artifact_roles_are_hard_coded_in_production_package() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    for legacy_role in ("final_model", "tokenizer", "training_metrics", "workload_record"):
        assert legacy_role not in combined


def test_architecture_error_vocabulary_contains_all_six_recovery_codes() -> None:
    assert {
        LocalIOCodeV1.ROOT_CHANGED.value,
        LocalIOCodeV1.ACCESS_MISMATCH.value,
        LocalIOCodeV1.PATH_CHANGED.value,
        LocalIOCodeV1.HARDLINK_UNSAFE.value,
        LocalIOCodeV1.JOURNAL_CONFLICT.value,
        LocalIOCodeV1.RECOVERY_REQUIRED.value,
    } == {
        "LOCAL_IO_ROOT_CHANGED",
        "LOCAL_IO_ACCESS_MISMATCH",
        "LOCAL_IO_PATH_CHANGED",
        "LOCAL_IO_HARDLINK_UNSAFE",
        "LOCAL_IO_JOURNAL_CONFLICT",
        "LOCAL_IO_RECOVERY_REQUIRED",
    }
