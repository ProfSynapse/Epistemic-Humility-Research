from hashlib import sha256
import json
from dataclasses import replace
from threading import Event
import traceback

import pytest

from synaptic_host.docker_v1.cli import DockerCLIRunnerV1
from synaptic_host.docker_v1.control_model import (
    OWNED_LABEL_NAMES_V1, OWNED_LABEL_PREFIX_V1,
    DockerImageInspectProjectionV1,
    DockerImageInspectResultV1,
    DockerTypedResultKindV1,
    docker_typed_request_digest_v1,
)
from synaptic_host.docker_v1.model import (
    MAX_DOCKER_ARG_BYTES_V1,
    MAX_DOCKER_ARGS_V1,
    MAX_DOCKER_COMBINED_BYTES_V1,
    MAX_DOCKER_STREAM_BYTES_V1,
    DockerCLICommandV1,
    DockerCLIEnvironmentV1,
    DockerCLIOutcomeV1,
    DockerCLIPolicyV1,
    DockerCLIVerbV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
)


class Stream:
    def __init__(self, chunks=(), *, error=False, close_error=False, gate=None,
                 close_unblocks=False):
        self.chunks = list(chunks)
        self.error = error
        self.close_error = close_error
        self.gate = gate
        self.close_unblocks = close_unblocks
        self.read_sizes = []
        self.closed = 0

    def read(self, size):
        self.read_sizes.append(size)
        if self.gate is not None:
            self.gate.wait(2)
        if self.error:
            raise RuntimeError("secret stream failure")
        return self.chunks.pop(0) if self.chunks else b""

    def close(self):
        self.closed += 1
        if self.close_unblocks and self.gate is not None:
            self.gate.set()
        if self.close_error:
            raise RuntimeError("secret close failure")


class Process:
    def __init__(self, stdout=(), stderr=(), *, exit_code=0,
                 stdout_stream=None, stderr_stream=None,
                 terminate_wait_fails=False, terminate_fails=False,
                 kill_fails=False, initial_wait_fails=False,
                 initial_wait_error=False, final_wait_fails=False,
                 termination_unblocks=True, first_reap_error=False):
        self.stdout = stdout_stream or Stream(stdout)
        self.stderr = stderr_stream or Stream(stderr)
        self.exit_code = exit_code
        self.terminate_wait_fails = terminate_wait_fails
        self.terminate_fails = terminate_fails
        self.kill_fails = kill_fails
        self.initial_wait_fails = initial_wait_fails
        self.initial_wait_error = initial_wait_error
        self.final_wait_fails = final_wait_fails
        self.termination_unblocks = termination_unblocks
        self.first_reap_error = first_reap_error
        self.terminated = 0
        self.killed = 0
        self.waits = []
        self._after_terminate = False
        self.events = []

    def poll(self):
        return self.exit_code

    def wait(self, timeout=None):
        self.events.append("wait")
        self.waits.append(timeout)
        if not self._after_terminate and self.initial_wait_error:
            raise RuntimeError("secret initial wait")
        if not self._after_terminate and self.initial_wait_fails:
            raise TimeoutError
        if self._after_terminate and self.terminate_wait_fails and not self.killed:
            raise TimeoutError
        if self._after_terminate and self.first_reap_error and not self.killed:
            raise RuntimeError("secret first reap")
        if self.killed and self.final_wait_fails:
            raise RuntimeError("secret final reap")
        return self.exit_code

    def terminate(self):
        self.events.append("terminate")
        self.terminated += 1
        self._after_terminate = True
        if self.terminate_fails:
            raise RuntimeError("secret terminate")
        if self.termination_unblocks:
            for stream in (self.stdout, self.stderr):
                if stream.gate is not None:
                    stream.gate.set()

    def kill(self):
        self.events.append("kill")
        self.killed += 1
        if self.kill_fails:
            raise RuntimeError("secret kill")
        if self.termination_unblocks:
            for stream in (self.stdout, self.stderr):
                if stream.gate is not None:
                    stream.gate.set()


class Factory:
    def __init__(self, process=None, *, error=False):
        self.process = process
        self.error = error
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if self.error:
            raise RuntimeError("secret executable path")
        return self.process


class ThreadFactory:
    def __init__(self, *, construct_fails=False, start_fails=False):
        self.construct_fails = construct_fails
        self.start_fails = start_fails
        self.created = []

    def __call__(self, **kwargs):
        if self.construct_fails:
            raise RuntimeError("secret thread construction")
        thread = StartControlledThread(start_fails=self.start_fails)
        self.created.append(thread)
        return thread


class StartControlledThread:
    def __init__(self, *, start_fails):
        self.start_fails = start_fails
        self.joins = []

    def start(self):
        if self.start_fails:
            raise RuntimeError("secret thread start")

    def is_alive(self):
        return False

    def join(self, timeout=None):
        self.joins.append(timeout)


class InspectionFailureThread:
    def __init__(self, *, failure):
        self.failure = failure

    def start(self):
        return None

    def is_alive(self):
        if self.failure == "is_alive":
            raise RuntimeError("secret is_alive failure")
        return True

    def join(self, timeout=None):
        raise RuntimeError("secret join failure")


class InspectionFailureThreadFactory:
    def __init__(self, failure):
        self.failure = failure

    def __call__(self, **kwargs):
        return InspectionFailureThread(failure=self.failure)


class RaisingClock:
    def __init__(self, good_reads):
        self.good_reads = good_reads
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls > self.good_reads:
            raise RuntimeError("secret clock")
        return 0.0


def _assert_closed_causal_error(caught, code):
    assert caught.value.code is code
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret" not in rendered


def _environment():
    return DockerCLIEnvironmentV1.build((
        ("SystemRoot", "C:\\Windows"),
        ("TEMP", "C:\\Temp"),
        ("TMP", "C:\\Temp"),
        ("WINDIR", "C:\\Windows"),
    ))


def _policy(**changes):
    values = {
        "executable": "C:\\Program Files\\Docker\\docker.exe",
        "context_ref": "desktop-linux",
        "environment": _environment(),
        "timeout_ms": 10_000,
        "terminate_grace_ms": 100,
        "stdout_limit": 1024,
        "stderr_limit": 1024,
        "combined_limit": 2048,
    }
    values.update(changes)
    return DockerCLIPolicyV1.build(**values)


def test_argv_context_shell_and_fresh_environment_are_exact():
    process = Process((b"ok",), (b"warning",))
    factory = Factory(process)
    command = DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT,
        ("name;echo secret", "$(not-executed)", "a&b"),
    )
    result = DockerCLIRunnerV1(_policy(), popen_factory=factory).run(command)
    argv, kwargs = factory.calls[0]
    assert argv == (
        "C:\\Program Files\\Docker\\docker.exe", "--context",
        "desktop-linux", "inspect", "name;echo secret",
        "$(not-executed)", "a&b",
    )
    assert kwargs["shell"] is False
    assert kwargs["env"] == dict(_environment().entries)
    assert set(kwargs["env"]) == {"SystemRoot", "WINDIR", "TEMP", "TMP"}
    assert result.outcome is DockerCLIOutcomeV1.SUCCESS
    assert result.stdout_digest == sha256(b"ok").hexdigest()
    assert result.stderr_digest == sha256(b"warning").hexdigest()


@pytest.mark.parametrize("verb", tuple(DockerCLIVerbV1))
def test_only_closed_typed_verbs_are_accepted(verb):
    command = DockerCLICommandV1.build(verb, ())
    assert command.verb is verb
    assert verb.value not in {"pull", "build", "restart"}


@pytest.mark.parametrize("token", ("", "x\x00y", "x\x1fy", "e\u0301"))
def test_invalid_argv_is_rejected_before_spawn(token):
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLICommandV1.build(DockerCLIVerbV1.PS, (token,))
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID


def test_command_builder_rejects_untyped_verb_without_leaking_details():
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLICommandV1.build("pull", ())
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID


def test_argument_byte_and_count_bounds_are_exact():
    maximum = "a" * MAX_DOCKER_ARG_BYTES_V1
    assert DockerCLICommandV1.build(
        DockerCLIVerbV1.PS, (maximum,)
    ).arguments == (maximum,)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLICommandV1.build(
            DockerCLIVerbV1.PS, (maximum + "a",)
        )
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID
    multibyte_maximum = "\u00e9" * (MAX_DOCKER_ARG_BYTES_V1 // 2)
    assert len(multibyte_maximum.encode("utf-8")) == MAX_DOCKER_ARG_BYTES_V1
    assert DockerCLICommandV1.build(
        DockerCLIVerbV1.PS, (multibyte_maximum,)
    ).arguments == (multibyte_maximum,)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLICommandV1.build(
            DockerCLIVerbV1.PS, (multibyte_maximum + "a",)
        )
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID
    arguments = ("x",) * MAX_DOCKER_ARGS_V1
    assert len(DockerCLICommandV1.build(
        DockerCLIVerbV1.PS, arguments
    ).arguments) == MAX_DOCKER_ARGS_V1
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLICommandV1.build(
            DockerCLIVerbV1.PS, arguments + ("x",)
        )
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID


def test_policy_rejects_nonabsolute_executable_and_all_extra_environment():
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _policy(executable="docker.exe")
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID

    mutable_pairs = [list(pair) for pair in _environment().entries]
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIEnvironmentV1.build(mutable_pairs)
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID

    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIPolicyV1.build(
            "C:\\Docker\\docker.exe", "desktop-linux", None
        )
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID
    for key in ("PATH", "HOME", "USERPROFILE", "APPDATA", "DOCKER_CONTEXT",
                "HF_TOKEN", "HTTP_PROXY"):
        entries = list(_environment().entries) + [(key, "secret")]
        with pytest.raises(DockerPlatformErrorV1) as caught:
            DockerCLIEnvironmentV1.build(tuple(entries))
        assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID
    invalid_paths = list(_environment().entries)
    invalid_paths[1] = ("TEMP", "relative-temp")
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIEnvironmentV1.build(tuple(invalid_paths))
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID


def test_hostile_environment_iterable_has_no_visible_causal_chain():
    class HostileEntries:
        def __iter__(self):
            raise RuntimeError("secret hostile iterable")

    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIEnvironmentV1.build(HostileEntries())
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.POLICY_INVALID)


def test_executable_and_each_environment_field_fail_causally_closed():
    tainted_executable = "secret-relative-docker.exe"
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _policy(executable=tainted_executable)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.POLICY_INVALID)

    valid = list(_environment().entries)
    for index, (key, _) in enumerate(valid):
        wrong_key = list(valid)
        wrong_key[index] = (f"secret-{key}", "C:\\Closed")
        with pytest.raises(DockerPlatformErrorV1) as caught:
            DockerCLIEnvironmentV1.build(tuple(wrong_key))
        _assert_closed_causal_error(caught, DockerPlatformCodeV1.POLICY_INVALID)

        wrong_path = list(valid)
        wrong_path[index] = (key, f"secret-relative-{key}")
        with pytest.raises(DockerPlatformErrorV1) as caught:
            DockerCLIEnvironmentV1.build(tuple(wrong_path))
        _assert_closed_causal_error(caught, DockerPlatformCodeV1.POLICY_INVALID)


@pytest.mark.parametrize(
    "value",
    (
        "C:relative", "\\\\server\\share", "C:/Temp", "C:\\Temp\\..\\Other",
        "C:\\Temp\\.\\Other", "C:\\Temp\\\\Other", "C:\\Temp\\",
        "C:\\Temp. ", "C:\\Te?mp", "C:\\e\u0301",
    ),
)
def test_environment_paths_must_be_canonical_absolute_drive_paths(value):
    entries = list(_environment().entries)
    entries[1] = ("TEMP", value)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIEnvironmentV1.build(tuple(entries))
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID


@pytest.mark.parametrize(
    "value",
    (
        "docker.exe", "\\\\server\\docker.exe", "C:/Docker/docker.exe",
        "C:\\Docker\\..\\docker.exe", "C:\\Docker\\", "C:\\Docker\\tool",
    ),
)
def test_executable_must_be_a_canonical_absolute_drive_exe(value):
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _policy(executable=value)
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID


@pytest.mark.parametrize(
    "value",
    (
        "c:\\Windows", "C:\\CON", "C:\\con.txt", "C:\\PRN.log",
        "C:\\AUX", "C:\\NUL.bin", "C:\\COM1", "C:\\com9.txt",
        "C:\\LPT1", "C:\\lpt9.txt", "C:\\Temp:stream",
        "C:\\CON .txt", "C:\\COM1 .log",
        "C:\\COM\u00b9", "C:\\com\u00b2.txt", "C:\\Com\u00b3. ",
        "C:\\LPT\u00b9", "C:\\lpt\u00b2.log", "C:\\Lpt\u00b3. ",
        "C:\\CONIN$", "C:\\conin$.txt", "C:\\ConIn$. ",
        "C:\\CONOUT$", "C:\\conout$.txt", "C:\\ConOut$. ",
        "\\\\?\\C:\\Windows", "\\\\.\\C:\\Windows",
    ),
)
def test_environment_rejects_noncanonical_drive_reserved_and_device_paths(value):
    entries = list(_environment().entries)
    entries[0] = ("SystemRoot", value)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIEnvironmentV1.build(tuple(entries))
    assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID


@pytest.mark.parametrize(
    "value",
    (
        "C:\\COM0", "C:\\COM10.txt", "C:\\COM\u2074",
        "C:\\LPT0", "C:\\LPT10.txt", "C:\\LPT\u2074",
        "C:\\CONIN", "C:\\CONOUT", "C:\\CONINX$", "C:\\CONOUTX$",
    ),
)
def test_windows_reserved_alias_neighbors_remain_valid(value):
    entries = list(_environment().entries)
    entries[0] = ("SystemRoot", value)
    result = DockerCLIEnvironmentV1.build(tuple(entries))
    assert result.entries[0] == ("SystemRoot", value)


def test_policy_numeric_bounds_are_exact():
    assert _policy(timeout_ms=1).timeout_ms == 1
    assert _policy(timeout_ms=3_600_000).timeout_ms == 3_600_000
    assert _policy(terminate_grace_ms=1).terminate_grace_ms == 1
    assert _policy(terminate_grace_ms=60_000).terminate_grace_ms == 60_000
    assert _policy(
        stdout_limit=MAX_DOCKER_STREAM_BYTES_V1,
        stderr_limit=1,
        combined_limit=MAX_DOCKER_COMBINED_BYTES_V1,
    ).stdout_limit == MAX_DOCKER_STREAM_BYTES_V1
    assert _policy(
        stdout_limit=1, stderr_limit=1, combined_limit=1
    ).combined_limit == 1
    for changes in (
        {"timeout_ms": 0}, {"timeout_ms": 3_600_001},
        {"terminate_grace_ms": 0}, {"terminate_grace_ms": 60_001},
        {"stdout_limit": 0},
        {"stdout_limit": MAX_DOCKER_STREAM_BYTES_V1 + 1},
        {"stderr_limit": 0},
        {"stderr_limit": MAX_DOCKER_STREAM_BYTES_V1 + 1},
        {"combined_limit": 0},
        {"combined_limit": MAX_DOCKER_COMBINED_BYTES_V1 + 1},
        {"stdout_limit": 1024, "stderr_limit": 1, "combined_limit": 1023},
    ):
        with pytest.raises(DockerPlatformErrorV1) as caught:
            _policy(**changes)
        assert caught.value.code is DockerPlatformCodeV1.POLICY_INVALID


def test_both_streams_are_drained_in_bounded_chunks_without_raw_output_evidence():
    stdout = (b"a" * 50,) * 16
    stderr = (b"b" * 40,) * 16
    process = Process(stdout, stderr, exit_code=7)
    result = DockerCLIRunnerV1(
        _policy(), popen_factory=Factory(process)
    ).run(DockerCLICommandV1.build(DockerCLIVerbV1.LOGS, ("container",)))
    assert result.outcome is DockerCLIOutcomeV1.NONZERO_EXIT
    assert result.exit_code == 7
    assert result.stdout_size == 800 and result.stderr_size == 640
    assert all(size == 65_536 for size in process.stdout.read_sizes)
    assert all(size == 65_536 for size in process.stderr.read_sizes)
    assert "aaaa" not in repr(result) and "bbbb" not in repr(result)
    assert process.stdout.closed == process.stderr.closed == 1


@pytest.mark.parametrize(
    "stdout,stderr,code",
    (
        ((b"a" * 513, b"a" * 512), (), DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED),
        ((), (b"b" * 1025,), DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED),
        ((b"a",), (), DockerPlatformCodeV1.IO_INDETERMINATE),
    ),
)
def test_overflow_and_stream_errors_are_closed(stdout, stderr, code):
    stdout_stream = Stream(stdout, error=(code is DockerPlatformCodeV1.IO_INDETERMINATE))
    process = Process(stdout_stream=stdout_stream, stderr_stream=Stream(stderr))
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is code
    assert "secret" not in str(caught.value)
    assert process.terminated == 1


@pytest.mark.parametrize("failing_name", ("stdout", "stderr"))
def test_each_reader_exception_is_closed_and_causally_suppressed(failing_name):
    streams = {
        "stdout": Stream(error=failing_name == "stdout"),
        "stderr": Stream(error=failing_name == "stderr"),
    }
    process = Process(
        stdout_stream=streams["stdout"], stderr_stream=streams["stderr"]
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.IO_INDETERMINATE)
    assert process.events == ["terminate", "wait"]


class AdvancingClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 1.0
        return self.value


def test_timeout_terminates_and_reaps_both_readers():
    gate = Event()
    process = Process(
        stdout_stream=Stream(gate=gate), stderr_stream=Stream(gate=gate)
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(timeout_ms=1), popen_factory=Factory(process),
            monotonic=AdvancingClock(),
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
    assert caught.value.code is DockerPlatformCodeV1.TIMEOUT
    assert process.terminated == 1
    assert process.stdout.closed == process.stderr.closed == 1


def test_timeout_after_both_streams_close_is_classified_and_reaped():
    process = Process(initial_wait_fails=True)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.VERSION)
        )
    assert caught.value.code is DockerPlatformCodeV1.TIMEOUT
    assert process.terminated == 1
    assert process.stdout.closed == process.stderr.closed == 1


def test_generic_initial_wait_error_is_io_and_then_cleanly_reaped():
    process = Process(initial_wait_error=True)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.VERSION)
        )
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.IO_INDETERMINATE)
    assert process.events == ["wait", "terminate", "wait"]


@pytest.mark.parametrize(
    "thread_factory",
    (
        ThreadFactory(construct_fails=True),
        ThreadFactory(start_fails=True),
    ),
)
def test_thread_construction_and_start_failures_cannot_escape_or_leak(
    thread_factory,
):
    process = Process()
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(), popen_factory=Factory(process),
            thread_factory=thread_factory,
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.IO_INDETERMINATE)
    assert process.events == ["terminate", "wait"]
    assert process.stdout.closed == process.stderr.closed == 1
    assert all(not thread.is_alive() for thread in thread_factory.created)


@pytest.mark.parametrize("good_reads", (0, 1))
def test_clock_failures_after_spawn_are_cleaned_without_raw_escape(good_reads):
    process = Process()
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(), popen_factory=Factory(process),
            monotonic=RaisingClock(good_reads),
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.IO_INDETERMINATE)
    assert process.events == ["terminate", "wait"]


@pytest.mark.parametrize("failure", ("join", "is_alive"))
def test_reader_join_and_liveness_exceptions_fail_closed(failure):
    process = Process()
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(timeout_ms=1), popen_factory=Factory(process),
            monotonic=AdvancingClock(),
            thread_factory=InspectionFailureThreadFactory(failure),
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
    _assert_closed_causal_error(
        caught, DockerPlatformCodeV1.TERMINATION_INDETERMINATE
    )


def test_close_unblocks_readers_before_bounded_joins():
    gate = Event()
    process = Process(
        stdout_stream=Stream(gate=gate, close_unblocks=True),
        stderr_stream=Stream(gate=gate, close_unblocks=True),
        termination_unblocks=False,
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(timeout_ms=1), popen_factory=Factory(process),
            monotonic=AdvancingClock(),
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
    assert caught.value.code is DockerPlatformCodeV1.TIMEOUT
    assert process.stdout.closed == process.stderr.closed == 1


def test_permanently_blocked_reader_makes_cleanup_indeterminate():
    gate = Event()
    process = Process(
        stdout_stream=Stream(gate=gate), stderr_stream=Stream(gate=gate),
        termination_unblocks=False,
    )
    try:
        with pytest.raises(DockerPlatformErrorV1) as caught:
            DockerCLIRunnerV1(
                _policy(timeout_ms=1, terminate_grace_ms=1),
                popen_factory=Factory(process), monotonic=AdvancingClock(),
            ).run(DockerCLICommandV1.build(DockerCLIVerbV1.VERSION))
        assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE
    finally:
        gate.set()


@pytest.mark.parametrize("trigger", ("timeout", "overflow"))
def test_close_uncertainty_dominates_timeout_and_overflow(trigger):
    if trigger == "timeout":
        gate = Event()
        process = Process(
            stdout_stream=Stream(gate=gate, close_error=True),
            stderr_stream=Stream(gate=gate),
        )
        runner = DockerCLIRunnerV1(
            _policy(timeout_ms=1), popen_factory=Factory(process),
            monotonic=AdvancingClock(),
        )
    else:
        process = Process(
            stdout_stream=Stream((b"x" * 1025,), close_error=True),
            stderr_stream=Stream(),
        )
        runner = DockerCLIRunnerV1(
            _policy(), popen_factory=Factory(process)
        )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.run(DockerCLICommandV1.build(DockerCLIVerbV1.PS))
    assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE


def test_terminate_timeout_escalates_to_kill_and_cleanup_uncertainty_dominates():
    process = Process((b"x" * 1025,), (), terminate_wait_fails=True)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED
    assert process.terminated == 1 and process.killed == 1
    assert process.events == ["terminate", "wait", "kill", "wait"]

    first_reap_broken = Process(
        (b"x" * 1025,), (), first_reap_error=True
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(), popen_factory=Factory(first_reap_broken)
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.PS))
    assert caught.value.code is DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED
    assert first_reap_broken.events == ["terminate", "wait", "kill", "wait"]

    terminate_broken = Process((b"x" * 1025,), (), terminate_fails=True)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(terminate_broken)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is DockerPlatformCodeV1.OUTPUT_BOUND_EXCEEDED
    assert terminate_broken.terminated == 1 and terminate_broken.killed == 1
    assert terminate_broken.events == ["terminate", "wait", "kill", "wait"]

    broken = Process((b"x" * 1025,), (), terminate_wait_fails=True,
                     kill_fails=True)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(broken)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE
    assert broken.events == ["terminate", "wait", "kill", "wait"]

    final_reap_broken = Process(
        (b"x" * 1025,), (), terminate_wait_fails=True,
        final_wait_fails=True,
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(
            _policy(), popen_factory=Factory(final_reap_broken)
        ).run(DockerCLICommandV1.build(DockerCLIVerbV1.PS))
    assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE
    assert final_reap_broken.events == ["terminate", "wait", "kill", "wait"]


def test_spawn_and_close_exceptions_are_closed_without_secrets():
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(error=True)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is DockerPlatformCodeV1.SPAWN_INDETERMINATE
    assert "secret" not in str(caught.value)

    process = Process(stdout_stream=Stream(close_error=True), stderr_stream=Stream())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=Factory(process)).run(
            DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        )
    assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE


def test_command_snapshot_rejects_mutation_before_spawn():
    command = DockerCLICommandV1.build(DockerCLIVerbV1.PS)
    object.__setattr__(command, "verb", DockerCLIVerbV1.CREATE)
    factory = Factory(Process())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerCLIRunnerV1(_policy(), popen_factory=factory).run(command)
    assert caught.value.code is DockerPlatformCodeV1.COMMAND_INVALID
    assert factory.calls == []


def _typed_runner(payload, *, exit_code=0):
    chunks = tuple(payload[index:index + 65_536]
                   for index in range(0, len(payload), 65_536))
    factory = Factory(Process(chunks, exit_code=exit_code))
    policy = _policy(stdout_limit=MAX_DOCKER_STREAM_BYTES_V1,
                     stderr_limit=MAX_DOCKER_STREAM_BYTES_V1,
                     combined_limit=MAX_DOCKER_COMBINED_BYTES_V1)
    return DockerCLIRunnerV1(policy, popen_factory=factory), factory


def _container_record(container_ref="a" * 64):
    labels = {
        OWNED_LABEL_PREFIX_V1 + name: (
            "1" if name == "schema-version" else "b" * 64
        ) for name in OWNED_LABEL_NAMES_V1
    }
    return {
        "Id": container_ref, "Name": "/synaptic-job",
        "Image": "sha256:" + "c" * 64,
        "Config": {"Labels": labels, "Env": ["TOKEN=raw-secret"],
                   "Cmd": ["python", "raw-secret.py"]},
        "HostConfig": {"NetworkMode": "none", "NanoCpus": 1000000000,
                       "Memory": 4096},
        "Mounts": [{"Type": "bind", "Source": "C:\\raw-secret",
                    "Destination": "/artifacts", "RW": True}],
        "State": {"Status": "created", "Running": False, "ExitCode": 0,
                  "StartedAt": "0001-01-01T00:00:00Z",
                  "Error": "raw-secret-state"},
        "RestartCount": 0,
        "FutureDockerField": {"ignored": True},
    }


def test_typed_inventory_builds_exact_argv_and_returns_only_ids():
    runner, factory = _typed_runner(("a" * 64 + "\n" + "b" * 64 + "\n").encode())
    result = runner.inventory_exact_name("synaptic-job")
    assert result.projection.container_refs == ("a" * 64, "b" * 64)
    assert factory.calls[0][0][-6:] == (
        "ps", "--all", "--quiet", "--no-trunc", "--filter",
        "name=^/synaptic-job$",
    )


def test_typed_image_inspect_is_exact_and_nonzero_is_not_parsed():
    image = "sha256:" + "d" * 64
    runner, factory = _typed_runner(json.dumps([{"Id": image, "Extra": 1}]).encode())
    result = runner.inspect_image(image)
    assert result.projection.image_digest == image
    assert factory.calls[0][0][-4:] == ("inspect", "--type", "image", image)

    runner, _ = _typed_runner(b"raw-secret not json", exit_code=1)
    result = runner.inspect_image(image)
    assert result.projection is None
    assert "raw-secret" not in repr(result)


def test_typed_container_projection_never_exposes_raw_values():
    ref = "a" * 64
    runner, factory = _typed_runner(json.dumps([_container_record(ref)]).encode())
    result = runner.inspect_container(ref)
    projection = result.projection
    assert projection.container_name == "synaptic-job"
    assert projection.network_mode == "none"
    assert len(projection.environment.entries) == 1 and projection.argument_count == 2
    assert projection.state.started is False
    rendered = repr(result)
    for secret in ("raw-secret", "C:\\raw-secret", "/artifacts"):
        assert secret not in rendered
    assert factory.calls[0][0][-4:] == ("inspect", "--type", "container", ref)


@pytest.mark.parametrize("payload", (
    b"\xff", b"{}", b"[]", b"[{},{}]", b"[NaN]",
    b'[{"Id":"x","Id":"y"}]',
))
def test_typed_inspect_rejects_invalid_utf8_json_shape_and_duplicates(payload):
    runner, _ = _typed_runner(payload)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_image("sha256:" + "d" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)
    assert "raw-secret" not in str(caught.value)


@pytest.mark.parametrize("payload", (
    b"a", b"A" * 64, b"a" * 63, b"a" * 64 + b" ",
    b"a" * 64 + b"\n\n", b"a" * 64 + b"\n" + b"a" * 64,
))
def test_typed_inventory_rejects_malformed_or_duplicate_ids(payload):
    runner, _ = _typed_runner(payload)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inventory_exact_name("synaptic-job")
    assert caught.value.code is DockerPlatformCodeV1.OUTPUT_INVALID


def test_container_owned_label_set_and_schema_are_exact():
    record = _container_record()
    record["Config"]["Labels"][OWNED_LABEL_PREFIX_V1 + "extra"] = "raw-secret"
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_container("a" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)

    record = _container_record()
    del record["Config"]["Labels"][OWNED_LABEL_PREFIX_V1 + "effect-id"]
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1):
        runner.inspect_container("a" * 64)


def test_json_resource_bounds_and_raw_parse_errors_are_closed():
    nested = {"Id": "sha256:" + "d" * 64}
    for _ in range(18):
        nested = {"future": nested}
    runner, _ = _typed_runner(json.dumps([nested]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_image("sha256:" + "d" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


def test_container_and_nested_projection_digests_recompute_on_reconstruction():
    runner, _ = _typed_runner(json.dumps([_container_record()]).encode())
    projection = runner.inspect_container("a" * 64).projection
    mutations = (
        lambda: replace(projection, memory_bytes=projection.memory_bytes + 1),
        lambda: replace(projection, owned_labels=tuple(reversed(projection.owned_labels))),
        lambda: replace(projection, mounts=(replace(
            projection.mounts[0], read_write=False),)),
        lambda: replace(projection, state=replace(
            projection.state, restart_count=1)),
        lambda: replace(projection, environment=replace(
            projection.environment,
            entries=(replace(projection.environment.entries[0],
                             value_digest="e" * 64),))),
    )
    for mutate in mutations:
        with pytest.raises(DockerPlatformErrorV1) as caught:
            mutate()
        _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


def test_environment_projection_is_order_independent_and_keeps_defaults():
    first = _container_record()
    first["Config"]["Env"] = ["REQUESTED=one", "IMAGE_DEFAULT=two"]
    second = _container_record()
    second["Config"]["Env"] = list(reversed(first["Config"]["Env"]))
    runner, _ = _typed_runner(json.dumps([first]).encode())
    left = runner.inspect_container("a" * 64).projection.environment
    runner, _ = _typed_runner(json.dumps([second]).encode())
    right = runner.inspect_container("a" * 64).projection.environment
    assert left == right and len(left.entries) == 2
    requested_key = sha256(b"REQUESTED").hexdigest()
    assert [x.value_digest for x in left.entries if x.key_digest == requested_key] == [
        sha256(b"one").hexdigest()
    ]

    duplicate = _container_record()
    duplicate["Config"]["Env"] = ["REQUESTED=one", "REQUESTED=altered"]
    runner, _ = _typed_runner(json.dumps([duplicate]).encode())
    with pytest.raises(DockerPlatformErrorV1):
        runner.inspect_container("a" * 64)


@pytest.mark.parametrize("started_at", (
    "2026-01-02 03:04:05Z", "2026-01-02T03:04:05+00:00",
    "2026-02-30T03:04:05Z", "2026-01-02T03:04:05.1234567890Z",
    "0001-01-01T00:00:00.0Z",
))
def test_started_at_grammar_and_state_matrix_are_closed(started_at):
    record = _container_record()
    record["State"]["StartedAt"] = started_at
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_container("a" * 64)
    assert caught.value.code is DockerPlatformCodeV1.OUTPUT_INVALID


def test_typed_result_rejects_cross_command_evidence_and_empty_target():
    image = "sha256:" + "d" * 64
    runner, _ = _typed_runner(json.dumps([{"Id": image}]).encode())
    result = runner.inspect_image(image)
    other_runner, _ = _typed_runner(b"")
    other = other_runner.inventory_exact_name("different-name")
    with pytest.raises(DockerPlatformErrorV1):
        DockerImageInspectResultV1.build(
            image, result.request_digest, result.command,
            other.evidence, result.projection,
        )
    with pytest.raises(DockerPlatformErrorV1):
        DockerImageInspectResultV1.build(
            "", result.request_digest, result.command,
            result.evidence, result.projection,
        )


def test_inventory_exact_64_and_65_boundary():
    refs = [f"{index:064x}" for index in range(64)]
    runner, _ = _typed_runner(("\n".join(refs) + "\n").encode())
    assert len(runner.inventory_exact_name("synaptic-job").projection.container_refs) == 64
    runner, _ = _typed_runner(("\n".join(refs + ["f" * 64]) + "\n").encode())
    with pytest.raises(DockerPlatformErrorV1):
        runner.inventory_exact_name("synaptic-job")


def _inspect_image_payload(extra):
    image = "sha256:" + "d" * 64
    record = {"Id": image}
    record.update(extra)
    runner, _ = _typed_runner(json.dumps([record]).encode())
    return runner, image


def test_json_depth_nodes_items_and_string_exact_boundaries():
    nested = 1
    for _ in range(14):
        nested = {"k": nested}
    runner, image = _inspect_image_payload({"future": nested})
    assert runner.inspect_image(image).projection is not None
    nested = {"k": nested}
    runner, image = _inspect_image_payload({"future": nested})
    with pytest.raises(DockerPlatformErrorV1): runner.inspect_image(image)

    runner, image = _inspect_image_payload({f"k{i}": None for i in range(1023)})
    assert runner.inspect_image(image).projection is not None
    runner, image = _inspect_image_payload({f"k{i}": None for i in range(1024)})
    with pytest.raises(DockerPlatformErrorV1): runner.inspect_image(image)

    runner, image = _inspect_image_payload({"future": "x" * 65_536})
    assert runner.inspect_image(image).projection is not None
    runner, image = _inspect_image_payload({"future": "x" * 65_537})
    with pytest.raises(DockerPlatformErrorV1): runner.inspect_image(image)

    exact_nodes = {f"x{i}": [None] * (1024 if i < 7 else 1013)
                   for i in range(8)}
    runner, image = _inspect_image_payload(exact_nodes)
    assert runner.inspect_image(image).projection is not None
    exact_nodes["x7"].append(None)
    runner, image = _inspect_image_payload(exact_nodes)
    with pytest.raises(DockerPlatformErrorV1): runner.inspect_image(image)


def test_container_collection_and_integer_exact_boundaries():
    record = _container_record()
    record["Config"]["Env"] = [f"K{i}=V" for i in range(256)]
    record["Config"]["Cmd"] = ["x"] * 256
    record["Mounts"] = [
        {"Type": "bind", "Source": f"C:\\s{i}",
         "Destination": f"/d{i}", "RW": bool(i % 2)} for i in range(64)
    ]
    record["HostConfig"]["NanoCpus"] = 2**63 - 1
    record["HostConfig"]["Memory"] = 2**63 - 1
    record["State"].update({"Status": "exited", "Running": False,
                            "ExitCode": -(2**31),
                            "StartedAt": "2026-01-02T03:04:05.123456789Z"})
    record["RestartCount"] = 2**31 - 1
    runner, _ = _typed_runner(json.dumps([record]).encode())
    assert runner.inspect_container("a" * 64).projection.argument_count == 256

    mutations = (
        lambda x: x["Config"].update(Env=[f"K{i}=V" for i in range(257)]),
        lambda x: x["Config"].update(Cmd=["x"] * 257),
        lambda x: x.update(Mounts=x["Mounts"] + [{"Type":"bind","Source":"C:\\z","Destination":"/z","RW":True}]),
        lambda x: x["HostConfig"].update(NanoCpus=2**63),
        lambda x: x["HostConfig"].update(Memory=-1),
        lambda x: x["State"].update(ExitCode=2**31),
        lambda x: x.update(RestartCount=2**31),
    )
    for mutate in mutations:
        bad = json.loads(json.dumps(record))
        mutate(bad)
        runner, _ = _typed_runner(json.dumps([bad]).encode())
        with pytest.raises(DockerPlatformErrorV1): runner.inspect_container("a" * 64)


def test_typed_paths_reuse_timeout_overflow_and_cleanup_dominance():
    gate = Event()
    process = Process(stdout_stream=Stream(gate=gate),
                      stderr_stream=Stream(gate=gate))
    runner = DockerCLIRunnerV1(
        _policy(timeout_ms=1), popen_factory=Factory(process),
        monotonic=AdvancingClock(),
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inventory_exact_name("synaptic-job")
    assert caught.value.code is DockerPlatformCodeV1.TIMEOUT
    assert process.events == ["terminate", "wait"]

    process = Process((b"x" * 1025,), (), stdout_stream=Stream(
        (b"x" * 1025,), close_error=True
    ))
    runner = DockerCLIRunnerV1(_policy(), popen_factory=Factory(process))
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_image("sha256:" + "d" * 64)
    assert caught.value.code is DockerPlatformCodeV1.TERMINATION_INDETERMINATE


def _reconstruct_typed_result(result):
    return type(result)(
        result.result_kind, result.target, result.request_digest,
        result.command, result.evidence, result.projection,
        result.result_digest,
    )


def test_real_name_a_evidence_cannot_forge_empty_name_b_inventory():
    runner, _ = _typed_runner(b"")
    real_a = runner.inventory_exact_name("name-a")
    runner, _ = _typed_runner(b"")
    real_b = runner.inventory_exact_name("name-b")
    with pytest.raises(DockerPlatformErrorV1) as caught:
        type(real_b)(
            real_b.result_kind, real_b.target, real_b.request_digest,
            real_b.command, real_a.evidence, real_b.projection,
            real_b.result_digest,
        )
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


def test_result_boundary_recursively_rejects_mutated_command_and_evidence():
    image = "sha256:" + "d" * 64
    runner, _ = _typed_runner(json.dumps([{"Id": image}]).encode())
    result = runner.inspect_image(image)
    object.__setattr__(result.command, "arguments", ("--type", "image", "sha256:" + "e" * 64))
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _reconstruct_typed_result(result)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)

    runner, _ = _typed_runner(json.dumps([{"Id": image}]).encode())
    result = runner.inspect_image(image)
    object.__setattr__(result.evidence, "stdout_size", result.evidence.stdout_size + 1)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _reconstruct_typed_result(result)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


@pytest.mark.parametrize("family", ("parent", "label", "env_entry", "env", "mount", "state"))
def test_result_boundary_recursively_rejects_each_mutated_projection_family(family):
    runner, _ = _typed_runner(json.dumps([_container_record()]).encode())
    result = runner.inspect_container("a" * 64)
    projection = result.projection
    target = {
        "parent": projection,
        "label": projection.owned_labels[0],
        "env_entry": projection.environment.entries[0],
        "env": projection.environment,
        "mount": projection.mounts[0],
        "state": projection.state,
    }[family]
    field, value = {
        "parent": ("memory_bytes", projection.memory_bytes + 1),
        "label": ("value_digest", "e" * 64),
        "env_entry": ("value_digest", "e" * 64),
        "env": ("projection_digest", "e" * 64),
        "mount": ("read_write", False),
        "state": ("restart_count", 1),
    }[family]
    object.__setattr__(target, field, value)
    with pytest.raises(DockerPlatformErrorV1) as caught:
        _reconstruct_typed_result(result)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


def test_duplicate_mount_destination_is_causally_closed_and_redacted():
    record = _container_record()
    secret = "/raw-secret-duplicate-destination"
    source_one = "C:\\raw-secret-source-one"
    source_two = "C:\\raw-secret-source-two"
    record["Mounts"] = [
        {"Type": "bind", "Source": source_one, "Destination": secret, "RW": True},
        {"Type": "bind", "Source": source_two, "Destination": secret, "RW": False},
    ]
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_container("a" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)
    rendered = "".join(traceback.format_exception(caught.value))
    for raw_value in (source_one, source_two, secret):
        assert raw_value not in rendered


@pytest.mark.parametrize(
    "status,running,started_at",
    (
        ("created", False, "0001-01-01T00:00:00Z"),
        ("running", True, "2026-01-02T03:04:05Z"),
        ("paused", True, "2026-01-02T03:04:05Z"),
        ("restarting", True, "2026-01-02T03:04:05Z"),
        ("exited", False, "2026-01-02T03:04:05Z"),
        ("dead", False, "2026-01-02T03:04:05Z"),
    ),
)
def test_exact_valid_state_matrix(status, running, started_at):
    record = _container_record()
    record["State"].update(Status=status, Running=running, StartedAt=started_at)
    runner, _ = _typed_runner(json.dumps([record]).encode())
    assert runner.inspect_container("a" * 64).projection.state.status.value == status


@pytest.mark.parametrize("status", ("removing", "hostile-unknown-status"))
def test_unsupported_and_unknown_states_are_closed_without_raw_status(status):
    record = _container_record()
    record["State"].update(Status=status, Running=False,
                           StartedAt="2026-01-02T03:04:05Z")
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_container("a" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)
    assert status not in str(caught.value)


_VALID_STATE_MATRIX = {
    "created": (False, False),
    "running": (True, True),
    "paused": (True, True),
    "restarting": (True, True),
    "exited": (False, True),
    "dead": (False, True),
}
_INVALID_STATE_MATRIX = tuple(
    (status, running, started)
    for status, valid_pair in _VALID_STATE_MATRIX.items()
    for running in (False, True)
    for started in (False, True)
    if (running, started) != valid_pair
)


@pytest.mark.parametrize("status,running,started", _INVALID_STATE_MATRIX)
def test_all_18_invalid_supported_state_combinations_are_causally_closed(
    status, running, started,
):
    assert len(_INVALID_STATE_MATRIX) == 18
    record = _container_record()
    record["State"].update(
        Status=status,
        Running=running,
        StartedAt=(
            "2026-01-02T03:04:05Z"
            if started else "0001-01-01T00:00:00Z"
        ),
    )
    runner, _ = _typed_runner(json.dumps([record]).encode())
    with pytest.raises(DockerPlatformErrorV1) as caught:
        runner.inspect_container("a" * 64)
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)


def test_internally_valid_wrong_command_is_rejected_by_exact_expected_argv():
    image = "sha256:" + "d" * 64
    wrong_command = DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT,
        ("--type", "image", image, "extra-valid-argument"),
    )
    runner, _ = _typed_runner(b"ignored by digest-only run")
    wrong_evidence = runner.run(wrong_command)
    wrong_request = docker_typed_request_digest_v1(
        DockerTypedResultKindV1.IMAGE_INSPECT,
        image,
        wrong_command.command_digest,
    )
    wrong_projection = DockerImageInspectProjectionV1.build(
        image, wrong_request, wrong_command.command_digest
    )
    with pytest.raises(DockerPlatformErrorV1) as caught:
        DockerImageInspectResultV1.build(
            image, wrong_request, wrong_command,
            wrong_evidence, wrong_projection,
        )
    _assert_closed_causal_error(caught, DockerPlatformCodeV1.OUTPUT_INVALID)
