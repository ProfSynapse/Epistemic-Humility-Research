from pathlib import Path


def test_host_docker_package_keeps_empty_exports_and_forbidden_boundaries():
    root = Path(__file__).parents[3] / "synaptic_host" / "docker_v1"
    init_text = (root / "__init__.py").read_text(encoding="utf-8")
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(root.glob("*.py"))
    ).lower()
    assert "__all__: tuple[str, ...] = ()" in init_text
    for forbidden in (
        "import sqlite", "from sqlite", "import subprocess", "from subprocess",
        "docker.from_env", "import requests", "from requests", "os.system",
        "shell=true", "hf_token", "runpod_api_key", "modal_token",
    ):
        assert forbidden not in combined
