from __future__ import annotations

from hashlib import sha256
from queue import Empty, Full, Queue
import subprocess
from threading import Event, Thread
import time

from synaptic_host.bundle_io_v1.model import digest_v1

from .model import (
    DockerCLICommandV1,
    DockerCLIEnvironmentV1,
    DockerCLIOutcomeV1,
    DockerCLIPolicyV1,
    DockerCLIResultV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
)
from .ports import DockerPopenFactoryPortV1


_READ_SIZE = 65_536
_EVENT_QUEUE_DEPTH = 4


def _error(code: DockerPlatformCodeV1) -> DockerPlatformErrorV1:
    return DockerPlatformErrorV1(code)


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
            self._policy = DockerCLIPolicyV1(
                policy.executable, policy.context_ref, environment,
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

    def run(self, command: DockerCLICommandV1) -> DockerCLIResultV1:
        command = self._snapshot_command(command)
        policy = self._policy
        argv = (
            policy.executable, "--context", policy.context_ref,
            command.verb.value, *command.arguments,
        )
        environment = {key: value for key, value in policy.environment.entries}
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
        result: DockerCLIResultV1 | None = None
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
                outcome = (
                    DockerCLIOutcomeV1.SUCCESS if exit_code == 0
                    else DockerCLIOutcomeV1.NONZERO_EXIT
                )
                stdout_digest = hashes["stdout"].hexdigest()
                stderr_digest = hashes["stderr"].hexdigest()
                body = {
                    "command_digest": command.command_digest,
                    "exit_code": exit_code,
                    "outcome": outcome.value,
                    "policy_digest": policy.policy_digest,
                    "schema_version": "synaptic-host-docker-cli-result/v1",
                    "stderr_digest": stderr_digest,
                    "stderr_size": sizes["stderr"],
                    "stdout_digest": stdout_digest,
                    "stdout_size": sizes["stdout"],
                }
                result = DockerCLIResultV1(
                    command.command_digest, policy.policy_digest, outcome,
                    exit_code, sizes["stdout"], stdout_digest,
                    sizes["stderr"], stderr_digest, digest_v1(body),
                )
        except DockerPlatformErrorV1 as error:
            trigger = error.code
        except BaseException:
            trigger = DockerPlatformCodeV1.IO_INDETERMINATE

        if trigger is None and type(result) is not DockerCLIResultV1:
            trigger = DockerPlatformCodeV1.IO_INDETERMINATE
        if trigger is not None:
            certain = self._cleanup(
                process=process, streams=streams, readers=readers,
                stopped=stopped, already_reaped=reaped,
            )
            code = trigger if certain else DockerPlatformCodeV1.TERMINATION_INDETERMINATE
            raise _error(code) from None
        return result


__all__: tuple[str, ...] = ()
