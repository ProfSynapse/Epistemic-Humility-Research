from __future__ import annotations

from hashlib import sha256
import json
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Full, Queue
import re
import subprocess
from threading import Event, Thread
import time

from tuner.execution.providers.docker_provider_v1.model import DockerLabelsV1

from synaptic_host.bundle_io_v1.model import digest_v1

from .model import (
    DockerCLICommandV1,
    DockerCLIEnvironmentV1,
    DockerCLIOutcomeV1,
    DockerCLIPolicyV1,
    DockerCLIResultV1,
    DockerCLIVerbV1,
    DockerLocalEndpointDescriptorV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
)
from .ports import DockerPopenFactoryPortV1
from .control_contract import (
    docker_arguments_projection_digest_v1,
    docker_device_requests_projection_digest_v1, docker_safe_unc_v1,
)
from .control_model import (
    OWNED_LABEL_NAMES_V1, OWNED_LABEL_PREFIX_V1,
    DockerContainerInspectProjectionV1, DockerContainerInspectResultV1,
    DockerCreateExecutionProjectionV1, DockerCreateExecutionResultV1,
    DockerStartExecutionResultV1,
    DockerContainerStateV1, DockerContainerStatusV1,
    DockerEnvironmentEntryProjectionV1, DockerEnvironmentProjectionV1,
    DockerExactNameInventoryResultV1, DockerExactNameInventoryV1,
    DockerImageInspectProjectionV1, DockerImageInspectResultV1,
    DockerLabelProjectionV1, DockerMountProjectionV1,
    DockerTypedResultKindV1, docker_typed_request_digest_v1,
    docker_create_execution_request_digest_v1,
    docker_start_execution_request_digest_v1,
)


_READ_SIZE = 65_536
_EVENT_QUEUE_DEPTH = 4
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SHA256_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CONTAINER_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}\Z")
_MAX_JSON_DEPTH = 16
_MAX_JSON_NODES = 8192
_MAX_JSON_ITEMS = 1024
_MAX_JSON_STRING_BYTES = 65_536
_MAX_INVENTORY = 64
_STARTED_AT = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z\Z"
)


def _validate_start_command(command, expected_container_ref):
    if (
        type(command) is not DockerCLICommandV1
        or command.verb is not DockerCLIVerbV1.START
        or type(expected_container_ref) is not str
        or _HEX64.fullmatch(expected_container_ref) is None
    ):
        raise ValueError
    rebuilt = DockerCLICommandV1(
        command.verb, tuple(command.arguments), command.command_digest
    )
    if rebuilt.arguments != (expected_container_ref,):
        raise ValueError


def _validate_create_command(command, expected_container_name):
    if (
        type(command) is not DockerCLICommandV1
        or command.verb is not DockerCLIVerbV1.CREATE
        or type(expected_container_name) is not str
        or _CONTAINER_NAME.fullmatch(expected_container_name) is None
    ):
        raise ValueError
    command = DockerCLICommandV1(
        command.verb, tuple(command.arguments), command.command_digest
    )
    arguments = command.arguments
    prefix = (
        "--name", expected_container_name, "--pull", "never",
        "--network", "none", "--cpus",
    )
    if arguments[:7] != prefix or len(arguments) > 256:
        raise ValueError
    index = 7
    cpu = arguments[index]
    index += 1
    if (
        not cpu.isascii() or not cpu.isdigit()
        or str(int(cpu)) != cpu or not 1 <= int(cpu) <= 256
    ):
        raise ValueError
    if arguments[index:index + 1] != ("--memory",):
        raise ValueError
    index += 1
    memory = arguments[index]
    index += 1
    if (
        not memory.isascii() or not memory.isdigit()
        or str(int(memory)) != memory or not 1 <= int(memory) <= 2**50
    ):
        raise ValueError
    if arguments[index:index + 1] == ("--gpus",):
        if arguments[index:index + 2] != (
            "--gpus", "driver=nvidia,device=0"
        ):
            raise ValueError
        index += 2
    label_values = []
    for label_name in OWNED_LABEL_NAMES_V1:
        if arguments[index:index + 1] != ("--label",):
            raise ValueError
        index += 1
        label = arguments[index]
        index += 1
        expected_prefix = OWNED_LABEL_PREFIX_V1 + label_name + "="
        if not label.startswith(expected_prefix) or len(label) == len(expected_prefix):
            raise ValueError
        label_values.append(label[len(expected_prefix):])
    labels = DockerLabelsV1(*label_values[:13])
    if (
        labels.effect_kind != "submit"
        or labels.container_name != expected_container_name
        or label_values[13] != labels.digest
        or label_values[14] != "1"
    ):
        raise ValueError
    expected_mounts = (
        ("/source", False, 4), ("/artifacts", True, 3),
    )
    mount_sources = []
    for destination, read_write, component_count in expected_mounts:
        if arguments[index:index + 1] != ("--mount",):
            raise ValueError
        index += 1
        mount = arguments[index]
        index += 1
        components = mount.split(",")
        expected = ["type=bind", None, f"destination={destination}"]
        if not read_write:
            expected.append("readonly")
        if len(components) != component_count or components[0] != expected[0]:
            raise ValueError
        if not components[1].startswith("source="):
            raise ValueError
        mount_sources.append(docker_safe_unc_v1(
            components[1][len("source="):]
        ))
        if components[2:] != expected[2:]:
            raise ValueError
    if mount_sources[0] == mount_sources[1]:
        raise ValueError
    env_keys = []
    while index < len(arguments) and arguments[index] == "--env":
        if len(env_keys) >= 64 or index + 1 >= len(arguments):
            raise ValueError
        index += 1
        token = arguments[index]
        index += 1
        if "=" not in token or len(token.encode("utf-8")) > 4096:
            raise ValueError
        key, _ = token.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError
        env_keys.append(key)
    if env_keys != sorted(env_keys) or len(env_keys) != len(set(env_keys)):
        raise ValueError
    if index >= len(arguments) or _SHA256_ID.fullmatch(arguments[index]) is None:
        raise ValueError
    index += 1
    workload_count = len(arguments) - index
    if (
        not 1 <= workload_count <= 64
        or sum(len(value.encode("utf-8")) for value in arguments[index:])
        > 32_768
    ):
        raise ValueError


def _parse_create_ref(raw):
    if type(raw) is not bytes:
        raise ValueError
    value = raw[:-1] if raw.endswith(b"\n") else raw
    if len(value) != 64 or _HEX64.fullmatch(value.decode("ascii")) is None:
        raise ValueError
    return value.decode("ascii")


def _error(code: DockerPlatformCodeV1) -> DockerPlatformErrorV1:
    return DockerPlatformErrorV1(code)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _validate_json_tree(value) -> None:
    nodes = 0

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        if depth > _MAX_JSON_DEPTH or nodes > _MAX_JSON_NODES:
            raise ValueError
        if item is None or type(item) in (bool, int, float):
            return
        if type(item) is str:
            if len(item.encode("utf-8")) > _MAX_JSON_STRING_BYTES:
                raise ValueError
            return
        if type(item) is list:
            if len(item) > _MAX_JSON_ITEMS:
                raise ValueError
            for child in item:
                visit(child, depth + 1)
            return
        if type(item) is dict:
            if len(item) > _MAX_JSON_ITEMS:
                raise ValueError
            for key, child in item.items():
                if type(key) is not str or len(key.encode("utf-8")) > 256:
                    raise ValueError
                visit(child, depth + 1)
            return
        raise ValueError

    visit(value, 0)


def _parse_inspect(raw: bytes | None) -> dict:
    if type(raw) is not bytes:
        raise ValueError
    text = raw.decode("utf-8", errors="strict")
    value = json.loads(
        text, object_pairs_hook=_pairs,
        parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
    )
    _validate_json_tree(value)
    if type(value) is not list or len(value) != 1 or type(value[0]) is not dict:
        raise ValueError
    return value[0]


def _parse_inventory(raw: bytes | None, *, container_name, query,
                     request_digest, command_digest) -> DockerExactNameInventoryV1:
    if type(raw) is not bytes:
        raise ValueError
    text = raw.decode("utf-8", errors="strict")
    if text == "":
        refs = ()
    else:
        if text.endswith("\n"):
            text = text[:-1]
        lines = text.split("\n")
        if not lines or len(lines) > _MAX_INVENTORY:
            raise ValueError
        refs = tuple(lines)
        if any(_HEX64.fullmatch(value) is None for value in refs):
            raise ValueError
        if len(set(refs)) != len(refs):
            raise ValueError
        refs = tuple(sorted(refs))
    return DockerExactNameInventoryV1.build(
        container_name, query, request_digest, command_digest, refs
    )


def _required_dict(value: dict, key: str) -> dict:
    child = value.get(key)
    if type(child) is not dict:
        raise ValueError
    return child


def _required_str(value: dict, key: str, pattern=None) -> str:
    child = value.get(key)
    if type(child) is not str or not child or len(child.encode("utf-8")) > 4096:
        raise ValueError
    if pattern is not None and pattern.fullmatch(child) is None:
        raise ValueError
    return child


def _required_int(value: dict, key: str, *, minimum=0, maximum=2**63 - 1) -> int:
    child = value.get(key)
    if type(child) is not int or not minimum <= child <= maximum:
        raise ValueError
    return child


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _device_requests_digest(host: dict) -> str:
    raw = host.get("DeviceRequests")
    if raw is None or raw == []:
        return docker_device_requests_projection_digest_v1(())
    if type(raw) is not list or len(raw) != 1:
        raise ValueError
    projected = []
    required = {"Driver", "Count", "DeviceIDs", "Capabilities", "Options"}
    for item in raw:
        if type(item) is not dict or set(item) != required:
            raise ValueError
        driver = item["Driver"]
        count = item["Count"]
        device_ids = item["DeviceIDs"]
        capabilities = item["Capabilities"]
        options = item["Options"]
        if (
            type(driver) is not str
            or type(count) is not int
            or type(device_ids) is not list
            or type(capabilities) is not list
            or type(options) is not dict
            or any(type(group) is not list for group in capabilities)
            or any(
                type(key) is not str or type(value) is not str
                for key, value in options.items()
            )
        ):
            raise ValueError
        if (
            driver != "nvidia"
            or count != 0
            or device_ids != ["0"]
            or capabilities != [["gpu"]]
            or options != {}
        ):
            raise ValueError
        projected.append((
            driver,
            count,
            tuple(device_ids),
            tuple(tuple(group) for group in capabilities),
            tuple(sorted(options.items())),
        ))
    return docker_device_requests_projection_digest_v1(tuple(projected))


def _project_container(record: dict, expected_ref: str, request_digest: str,
                       command_digest: str) -> DockerContainerInspectProjectionV1:
    container_ref = _required_str(record, "Id", _HEX64)
    if container_ref != expected_ref:
        raise ValueError
    raw_name = _required_str(record, "Name")
    if not raw_name.startswith("/") or _CONTAINER_NAME.fullmatch(raw_name[1:]) is None:
        raise ValueError
    image_digest = _required_str(record, "Image", _SHA256_ID)
    config = _required_dict(record, "Config")
    labels = config.get("Labels")
    if type(labels) is not dict:
        raise ValueError
    expected_names = set(OWNED_LABEL_NAMES_V1)
    owned = {}
    for key, value in labels.items():
        if key.startswith(OWNED_LABEL_PREFIX_V1):
            name = key[len(OWNED_LABEL_PREFIX_V1):]
            if name not in expected_names or type(value) is not str:
                raise ValueError
            owned[name] = value
    if set(owned) != expected_names or owned["schema-version"] != "1":
        raise ValueError
    if _SHA256_ID.fullmatch("sha256:" + owned["labels-digest"]) is None:
        raise ValueError
    owned_projection = tuple(
        DockerLabelProjectionV1.build(name, _digest_text(owned[name]))
        for name in OWNED_LABEL_NAMES_V1
    )

    environment = config.get("Env")
    if environment is None:
        environment = []
    if type(environment) is not list or len(environment) > 256:
        raise ValueError
    env_projection = []
    seen_env = set()
    for entry in environment:
        if type(entry) is not str or "=" not in entry:
            raise ValueError
        key, value = entry.split("=", 1)
        if not key or key in seen_env:
            raise ValueError
        seen_env.add(key)
        env_projection.append(DockerEnvironmentEntryProjectionV1.build(
            _digest_text(key), _digest_text(value)
        ))

    arguments = config.get("Cmd")
    if arguments is None:
        arguments = []
    if type(arguments) is not list or len(arguments) > 256 or any(type(x) is not str for x in arguments):
        raise ValueError
    host = _required_dict(record, "HostConfig")
    network_mode = _required_str(host, "NetworkMode")
    nano_cpus = _required_int(host, "NanoCpus")
    memory_bytes = _required_int(host, "Memory")
    device_requests_digest = _device_requests_digest(host)

    raw_mounts = record.get("Mounts")
    if type(raw_mounts) is not list or len(raw_mounts) > 64:
        raise ValueError
    mounts = []
    destinations = set()
    for raw_mount in raw_mounts:
        if type(raw_mount) is not dict:
            raise ValueError
        mount_type = _required_str(raw_mount, "Type")
        if mount_type not in ("bind", "volume", "tmpfs"):
            raise ValueError
        source = _required_str(raw_mount, "Source")
        destination = _required_str(raw_mount, "Destination")
        read_write = raw_mount.get("RW")
        if type(read_write) is not bool:
            raise ValueError
        destination_digest = _digest_text(destination)
        if destination_digest in destinations:
            raise ValueError
        destinations.add(destination_digest)
        mounts.append(DockerMountProjectionV1.build(
            mount_type, _digest_text(source), destination_digest, read_write
        ))

    raw_state = _required_dict(record, "State")
    status = DockerContainerStatusV1(_required_str(raw_state, "Status"))
    running = raw_state.get("Running")
    if type(running) is not bool:
        raise ValueError
    exit_code = _required_int(raw_state, "ExitCode", minimum=-(2**31), maximum=2**31 - 1)
    started_at = _required_str(raw_state, "StartedAt")
    if _STARTED_AT.fullmatch(started_at) is None:
        raise ValueError
    if started_at == "0001-01-01T00:00:00Z":
        started = False
    else:
        timestamp = started_at[:-1]
        if "." in timestamp:
            whole, fraction = timestamp.rsplit(".", 1)
            timestamp = f"{whole}.{fraction[:6].ljust(6, '0')}"
        datetime.fromisoformat(timestamp + "+00:00")
        started = True
    restart_count = _required_int(record, "RestartCount", maximum=2**31 - 1)
    state = DockerContainerStateV1.build(
        status, running, exit_code, started, restart_count
    )

    return DockerContainerInspectProjectionV1.build(
        container_ref=container_ref, container_name=raw_name[1:],
        image_digest=image_digest, owned_labels=owned_projection,
        request_digest=request_digest, command_digest=command_digest,
        network_mode=network_mode, nano_cpus=nano_cpus,
        memory_bytes=memory_bytes, mounts=tuple(mounts), state=state,
        environment=DockerEnvironmentProjectionV1.build(env_projection),
        argument_count=len(arguments),
        arguments_digest=docker_arguments_projection_digest_v1(arguments),
        device_requests_digest=device_requests_digest,
    )


@dataclass(frozen=True, slots=True)
class DockerBoundedProcessResultV1:
    exit_code: int
    stdout: bytes | None
    stdout_size: int
    stdout_digest: str
    stderr_size: int
    stderr_digest: str


class DockerCLIRunnerV1:
    def __init__(
        self, policy: DockerCLIPolicyV1, *,
        popen_factory: DockerPopenFactoryPortV1 = subprocess.Popen,
        monotonic=time.monotonic,
        thread_factory=Thread,
    ) -> None:
        try:
            if type(policy) is not DockerCLIPolicyV1:
                raise ValueError
            environment = DockerCLIEnvironmentV1(
                tuple((key, value) for key, value in policy.environment.entries),
                policy.environment.environment_digest,
            )
            endpoint = DockerLocalEndpointDescriptorV1.build(
                policy.endpoint.source_context_ref, policy.endpoint.host,
                policy.endpoint.tls,
            )
            self._policy = DockerCLIPolicyV1(
                policy.executable, endpoint, environment,
                policy.timeout_ms, policy.terminate_grace_ms,
                policy.stdout_limit, policy.stderr_limit,
                policy.combined_limit, policy.policy_digest,
            )
            self._popen = popen_factory
            self._monotonic = monotonic
            self._thread_factory = thread_factory
        except DockerPlatformErrorV1 as error:
            raise _error(error.code) from None
        except BaseException:
            raise _error(DockerPlatformCodeV1.POLICY_INVALID) from None

    @staticmethod
    def _snapshot_command(value) -> DockerCLICommandV1:
        try:
            if type(value) is not DockerCLICommandV1:
                raise ValueError
            rebuilt = DockerCLICommandV1(
                value.verb, tuple(value.arguments), value.command_digest
            )
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except DockerPlatformErrorV1 as error:
            raise _error(error.code) from None
        except BaseException:
            raise _error(DockerPlatformCodeV1.COMMAND_INVALID) from None

    @staticmethod
    def _drain(name, stream, events: Queue, stopped: Event) -> None:
        def emit(kind, payload) -> bool:
            while not stopped.is_set():
                try:
                    events.put((name, kind, payload), timeout=0.05)
                    return True
                except Full:
                    continue
            return False

        try:
            while not stopped.is_set():
                chunk = stream.read(_READ_SIZE)
                if type(chunk) is not bytes or len(chunk) > _READ_SIZE:
                    emit("error", None)
                    return
                if not chunk:
                    emit("eof", None)
                    return
                if not emit("data", chunk):
                    return
        except BaseException:
            emit("error", None)

    @staticmethod
    def _close_pass(streams, closed: list[bool]) -> None:
        for index, stream in enumerate(streams):
            if closed[index]:
                continue
            try:
                if stream is not None:
                    stream.close()
                    closed[index] = True
            except BaseException:
                continue

    @staticmethod
    def _join_pass(readers, timeout: float) -> bool:
        certain = True
        for reader in readers:
            try:
                if reader.is_alive():
                    reader.join(timeout)
                if reader.is_alive():
                    certain = False
            except BaseException:
                certain = False
        return certain

    def _cleanup(
        self, *, process, streams, readers, stopped: Event,
        already_reaped: bool,
    ) -> bool:
        grace = self._policy.terminate_grace_ms / 1000
        certain = True
        try:
            stopped.set()
        except BaseException:
            certain = False

        process_certain = already_reaped
        if not already_reaped:
            terminate_ok = False
            first_reap_ok = False
            try:
                process.terminate()
                terminate_ok = True
            except BaseException:
                pass
            try:
                first_exit = process.wait(timeout=grace)
                first_reap_ok = type(first_exit) is int
            except BaseException:
                pass
            if terminate_ok and first_reap_ok:
                process_certain = True
            else:
                kill_ok = False
                final_reap_ok = False
                try:
                    process.kill()
                    kill_ok = True
                except BaseException:
                    pass
                try:
                    final_exit = process.wait(timeout=grace)
                    final_reap_ok = type(final_exit) is int
                except BaseException:
                    pass
                process_certain = kill_ok and final_reap_ok

        closed = [False, False]
        self._close_pass(streams, closed)
        first_join_ok = self._join_pass(readers, grace)
        self._close_pass(streams, closed)
        second_join_ok = self._join_pass(readers, grace)
        return (
            certain
            and process_certain
            and all(closed)
            and first_join_ok
            and second_join_ok
        )

    def _execute_argv(
        self, argv: tuple[str, ...], environment: dict[str, str], *,
        capture_stdout: bool,
    ) -> "DockerBoundedProcessResultV1":
        policy = self._policy
        try:
            events: Queue = Queue(maxsize=_EVENT_QUEUE_DEPTH)
            stopped = Event()
        except BaseException:
            raise _error(DockerPlatformCodeV1.IO_INDETERMINATE) from None
        try:
            process = self._popen(
                argv, shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=environment, text=False, close_fds=True,
            )
        except BaseException:
            raise _error(DockerPlatformCodeV1.SPAWN_INDETERMINATE) from None
        streams = (None, None)
        readers: list[object] = []
        reaped = False
        trigger: DockerPlatformCodeV1 | None = None
        result: DockerBoundedProcessResultV1 | None = None
        try:
            streams = (process.stdout, process.stderr)
            if any(stream is None for stream in streams):
                trigger = DockerPlatformCodeV1.IO_INDETERMINATE

            if trigger is None:
                for name, stream in zip(("stdout", "stderr"), streams, strict=True):
                    reader = self._thread_factory(
                        target=self._drain,
                        args=(name, stream, events, stopped),
                        daemon=True,
                    )
                    readers.append(reader)
                    reader.start()

            hashes = {"stdout": sha256(), "stderr": sha256()}
            captured = bytearray() if capture_stdout else None
            sizes = {"stdout": 0, "stderr": 0}
            limits = {"stdout": policy.stdout_limit, "stderr": policy.stderr_limit}
            ended: set[str] = set()
            deadline = self._monotonic() + policy.timeout_ms / 1000
            while trigger is None and len(ended) != 2:
                remaining = deadline - self._monotonic()
                if remaining <= 0:
                    trigger = DockerPlatformCodeV1.TIMEOUT
                    break
                try:
                    name, kind, payload = events.get(timeout=min(remaining, 0.05))
                except Empty:
                    continue
                if kind == "error":
                    trigger = DockerPlatformCodeV1.IO_INDETERMINATE
                elif kind == "eof":
                    ended.add(name)
                else:
                    new_size = sizes[name] + len(payload)
                    other = "stderr" if name == "stdout" else "stdout"
                    if (
                        new_size > limits[name]
                        or new_size + sizes[other] > policy.combined_limit
                    ):
                        trigger = DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED
                    else:
                        sizes[name] = new_size
                        hashes[name].update(payload)
                        if name == "stdout" and captured is not None:
                            captured.extend(payload)

            exit_code = None
            if trigger is None:
                remaining = deadline - self._monotonic()
                if remaining <= 0:
                    trigger = DockerPlatformCodeV1.TIMEOUT
                else:
                    try:
                        exit_code = process.wait(timeout=remaining)
                    except (subprocess.TimeoutExpired, TimeoutError):
                        trigger = DockerPlatformCodeV1.TIMEOUT
                    except BaseException:
                        trigger = DockerPlatformCodeV1.IO_INDETERMINATE
                    if trigger is None:
                        if type(exit_code) is not int:
                            trigger = DockerPlatformCodeV1.IO_INDETERMINATE
                        else:
                            reaped = True

            if trigger is None:
                if not self._join_pass(readers, policy.terminate_grace_ms / 1000):
                    trigger = DockerPlatformCodeV1.IO_INDETERMINATE
                normal_closed = [False, False]
                self._close_pass(streams, normal_closed)
                if not all(normal_closed):
                    trigger = DockerPlatformCodeV1.IO_INDETERMINATE

            if trigger is None:
                stdout_digest = hashes["stdout"].hexdigest()
                stderr_digest = hashes["stderr"].hexdigest()
                result = DockerBoundedProcessResultV1(
                    exit_code, bytes(captured) if captured is not None else None,
                    sizes["stdout"], stdout_digest, sizes["stderr"], stderr_digest,
                )
        except DockerPlatformErrorV1 as error:
            trigger = error.code
        except BaseException:
            trigger = DockerPlatformCodeV1.IO_INDETERMINATE

        if trigger is None and type(result) is not DockerBoundedProcessResultV1:
            trigger = DockerPlatformCodeV1.IO_INDETERMINATE
        if trigger is not None:
            certain = self._cleanup(
                process=process, streams=streams, readers=readers,
                stopped=stopped, already_reaped=reaped,
            )
            code = trigger if certain else DockerPlatformCodeV1.TERMINATION_INDETERMINATE
            raise _error(code) from None
        return result

    def _execute(
        self, command: DockerCLICommandV1, *, capture_stdout: bool,
    ) -> tuple[DockerCLIResultV1, bytes | None]:
        command = self._snapshot_command(command)
        policy = self._policy
        raw = self._execute_argv(
            (policy.executable, "--host", policy.endpoint.host,
             command.verb.value, *command.arguments),
            {key: value for key, value in policy.environment.entries},
            capture_stdout=capture_stdout,
        )
        outcome = (DockerCLIOutcomeV1.SUCCESS if raw.exit_code == 0
                   else DockerCLIOutcomeV1.NONZERO_EXIT)
        body = {
            "command_digest": command.command_digest, "exit_code": raw.exit_code,
            "outcome": outcome.value, "policy_digest": policy.policy_digest,
            "schema_version": "synaptic-host-docker-cli-result/v1",
            "stderr_digest": raw.stderr_digest, "stderr_size": raw.stderr_size,
            "stdout_digest": raw.stdout_digest, "stdout_size": raw.stdout_size,
        }
        result = DockerCLIResultV1(
            command.command_digest, policy.policy_digest, outcome, raw.exit_code,
            raw.stdout_size, raw.stdout_digest, raw.stderr_size,
            raw.stderr_digest, digest_v1(body),
        )
        return result, raw.stdout

    def run(self, command: DockerCLICommandV1) -> DockerCLIResultV1:
        result, _ = self._execute(command, capture_stdout=False)
        return result

    def create_container(
        self, command: DockerCLICommandV1, expected_container_name: str,
    ) -> DockerCreateExecutionResultV1:
        try:
            _validate_create_command(command, expected_container_name)
            request_digest = docker_create_execution_request_digest_v1(
                expected_container_name, command.command_digest
            )
            evidence, raw = self._execute(command, capture_stdout=True)
            projection = None
            if evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                projection = DockerCreateExecutionProjectionV1.build(
                    _parse_create_ref(raw), request_digest,
                    command.command_digest,
                )
            return DockerCreateExecutionResultV1.build(
                expected_container_name, request_digest,
                command.command_digest, evidence, projection,
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            raise _error(DockerPlatformCodeV1.OUTPUT_INVALID) from None

    def start_container(
        self, command: DockerCLICommandV1, expected_container_ref: str,
    ) -> DockerStartExecutionResultV1:
        try:
            _validate_start_command(command, expected_container_ref)
            request_digest = docker_start_execution_request_digest_v1(
                expected_container_ref, command.command_digest
            )
            evidence, _ = self._execute(command, capture_stdout=False)
            return DockerStartExecutionResultV1.build(
                expected_container_ref, request_digest, command, evidence
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            raise _error(DockerPlatformCodeV1.OUTPUT_INVALID) from None

    def inventory_exact_name(
        self, container_name: str,
    ) -> DockerExactNameInventoryResultV1:
        try:
            if type(container_name) is not str or _CONTAINER_NAME.fullmatch(container_name) is None:
                raise ValueError
            query = f"name=^/{container_name}$"
            command = DockerCLICommandV1.build(
                DockerCLIVerbV1.PS,
                ("--all", "--quiet", "--no-trunc", "--filter",
                 query),
            )
            request_digest = docker_typed_request_digest_v1(
                DockerTypedResultKindV1.EXACT_NAME_INVENTORY,
                container_name, command.command_digest,
            )
            evidence, raw = self._execute(command, capture_stdout=True)
            projection = None
            if evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                projection = _parse_inventory(
                    raw, container_name=container_name, query=query,
                    request_digest=request_digest,
                    command_digest=command.command_digest,
                )
            return DockerExactNameInventoryResultV1.build(
                container_name, request_digest, command,
                evidence, projection
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            raise _error(DockerPlatformCodeV1.OUTPUT_INVALID) from None

    def inspect_image(self, image_digest: str) -> DockerImageInspectResultV1:
        try:
            if type(image_digest) is not str or _SHA256_ID.fullmatch(image_digest) is None:
                raise ValueError
            command = DockerCLICommandV1.build(
                DockerCLIVerbV1.INSPECT, ("--type", "image", image_digest)
            )
            request_digest = docker_typed_request_digest_v1(
                DockerTypedResultKindV1.IMAGE_INSPECT,
                image_digest, command.command_digest,
            )
            evidence, raw = self._execute(command, capture_stdout=True)
            projection = None
            if evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                record = _parse_inspect(raw)
                actual = _required_str(record, "Id", _SHA256_ID)
                if actual != image_digest:
                    raise ValueError
                projection = DockerImageInspectProjectionV1.build(
                    actual, request_digest, command.command_digest
                )
            return DockerImageInspectResultV1.build(
                image_digest, request_digest, command,
                evidence, projection
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            raise _error(DockerPlatformCodeV1.OUTPUT_INVALID) from None

    def inspect_container(
        self, container_ref: str,
    ) -> DockerContainerInspectResultV1:
        try:
            if type(container_ref) is not str or _HEX64.fullmatch(container_ref) is None:
                raise ValueError
            command = DockerCLICommandV1.build(
                DockerCLIVerbV1.INSPECT, ("--type", "container", container_ref)
            )
            request_digest = docker_typed_request_digest_v1(
                DockerTypedResultKindV1.CONTAINER_INSPECT,
                container_ref, command.command_digest,
            )
            evidence, raw = self._execute(command, capture_stdout=True)
            projection = None
            if evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                projection = _project_container(
                    _parse_inspect(raw), container_ref,
                    request_digest, command.command_digest,
                )
            return DockerContainerInspectResultV1.build(
                container_ref, request_digest, command,
                evidence, projection
            )
        except DockerPlatformErrorV1:
            raise
        except BaseException:
            raise _error(DockerPlatformCodeV1.OUTPUT_INVALID) from None

@dataclass(frozen=True, slots=True)
class _DockerProcessBoundsV1:
    timeout_ms: int
    terminate_grace_ms: int
    stdout_limit: int
    stderr_limit: int
    combined_limit: int


class DockerBoundedProcessRunnerV1(DockerCLIRunnerV1):
    def __init__(
        self, *, timeout_ms: int, terminate_grace_ms: int,
        stdout_limit: int, stderr_limit: int, combined_limit: int,
        popen_factory: DockerPopenFactoryPortV1 = subprocess.Popen,
        monotonic=time.monotonic, thread_factory=Thread,
    ) -> None:
        self._policy = _DockerProcessBoundsV1(
            timeout_ms, terminate_grace_ms, stdout_limit, stderr_limit,
            combined_limit,
        )
        self._popen = popen_factory
        self._monotonic = monotonic
        self._thread_factory = thread_factory

    def execute(self, argv, environment, *, capture_stdout):
        return self._execute_argv(argv, environment, capture_stdout=capture_stdout)


__all__: tuple[str, ...] = ()
