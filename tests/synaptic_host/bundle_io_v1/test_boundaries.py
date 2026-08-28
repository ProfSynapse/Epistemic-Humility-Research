from __future__ import annotations

import ast
from pathlib import Path


PACKAGE = Path(__file__).parents[3] / "synaptic_host" / "bundle_io_v1"


def test_package_has_empty_exports() -> None:
    namespace = {}
    exec((PACKAGE / "__init__.py").read_text(encoding="utf-8"), namespace)
    assert namespace["__all__"] == ()


def test_bundle_boundary_has_no_engine_provider_database_process_or_raw_fs_imports() -> None:
    forbidden = {
        "synaptic_tuner", "docker", "modal", "huggingface_hub", "runpod",
        "sqlite3", "subprocess",
    }
    combined = ""
    for path in PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        combined += source
        tree = ast.parse(source, filename=path.name)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden)
    for forbidden_name in (
        "LocalFilesystemV1", "RetainedDirectoryV1", "OpenFileV1",
        "PosixFilesystemPortV1", "absolute_root", "root_permit",
        "BundleNoncePortV1", "SecretsBundleNonceV1", "unlink_borrowed",
    ):
        assert forbidden_name not in combined


def test_bundle_has_no_nonce_or_posix_module() -> None:
    assert not (PACKAGE / "posix.py").exists()


def test_bundle_has_no_hardcoded_roles_locations_or_dataset_formats() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    for value in (
        "final_model", "tokenizer", "training_metrics", "dataset.jsonl",
        "huggingface", "modal", "runpod", "project://",
    ):
        assert value not in combined.casefold()
