from pathlib import Path


def test_host_docker_package_keeps_empty_exports_and_forbidden_boundaries():
    root = Path(__file__).parents[3] / "synaptic_host" / "docker_v1"
    init_text = (root / "__init__.py").read_text(encoding="utf-8")
    files = {path.name: path.read_text(encoding="utf-8")
             for path in sorted(root.glob("*.py"))}
    combined = "\n".join(
        text for name, text in files.items() if name != "cli.py"
    ).lower()
    assert "__all__: tuple[str, ...] = ()" in init_text
    for forbidden in (
        "import sqlite", "from sqlite", "import subprocess", "from subprocess",
        "docker.from_env", "import requests", "from requests", "os.system",
        "shell=true", "hf_token", "runpod_api_key", "modal_token",
        "json.loads", "object_pairs_hook",
    ):
        assert forbidden not in combined
    cli = files["cli.py"].lower()
    assert "import subprocess" in cli
    assert "shell=false" in cli
    for forbidden in (
        "shell=true", "os.environ", "getenv(", "userprofile", "appdata",
        "docker_context", "docker_config", "hf_token", "runpod_api_key",
        "modal_token", "http_proxy", "https_proxy",
    ):
        assert forbidden not in cli
    ports = files["ports.py"]
    assert "DockerTypedCLIRunnerPortV1" in ports
    assert "bytes" not in ports.split("class DockerTypedCLIRunnerPortV1", 1)[1]
    control_model = files["control_model.py"]
    assert "raw_output" not in control_model and "state_error" not in control_model
    public_contract = files["control_contract.py"].lower()
    private_contract = files["control_private.py"].lower()
    assert "control_private" not in ports.lower()
    assert "sqlite" not in public_contract + private_contract
    assert "subprocess" not in public_contract + private_contract
    assert "docker.from_env" not in public_contract + private_contract
    assert "os.environ" not in public_contract + private_contract
    assert "__reduce__" in private_contract and "<redacted>" in private_contract
    control = files["control.py"].lower()
    assert "control_private" not in control
    for mutation_call in (".admit(", ".compare_and_swap("):
        assert mutation_call not in control
    for forbidden in ("sqlite", "subprocess", "docker.from_env", "os.environ"):
        assert forbidden not in control
