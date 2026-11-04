"""Experiment-local live-owner drill. No stored PID is ever a signal authority.

The command is constructed by astra_qualification, never supplied by recipe or
CLI. Receipts describe observations; verification re-reads actual artifacts.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
from .util import HarnessError, read_json, read_jsonl, canonical_sha256, sha256_file


def create(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


@contextlib.contextmanager
def writer(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HarnessError('ACTIVE_WRITER', 'qualification writer already active') from exc
        yield lock.fileno()


def guard(fd):
    """Anonymous live-parent pipe. EOF kills this worker's whole owned group."""
    if os.getpgrp()!=os.getpid():
        raise HarnessError('QUAL_OWNER','worker must lead its controller-created process group')
    def watch():
        try:
            while os.read(fd, 1): pass
        finally:
            os.killpg(os.getpgrp(), signal.SIGKILL)
    threading.Thread(target=watch, daemon=True).start()


def journal(path):
    data = path.read_bytes()
    if not data.endswith(b'\n'):
        raise HarnessError('QUAL_JOURNAL', 'incomplete journal record')
    rows = [json.loads(line) for line in data.splitlines()]
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise HarnessError('QUAL_JOURNAL', 'duplicate durable ids')
    return data, rows


def _signal(child, sig):
    # poll reaps a finished leader; never signal its numeric PID after that.
    if child.poll() is not None:
        raise HarnessError('QUAL_UNKNOWN', 'owned leader ended before signal')
    os.killpg(child.pid, sig)


def _wait(child, timeout):
    try: return child.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise HarnessError('QUAL_TIMEOUT', 'owned worker deadline expired') from exc


def drill(command, root, binding, *, pass_fds=(), timeout=1800, cwd=None, lease=None):
    """One consumed attempt; only this stack frame may resume its known kill."""
    root = Path(root)
    output = root/'runs/resume/completions.jsonl'
    if output.parent.exists():
        raise HarnessError('QUAL_CONSUMED', 'resume output must start absent')
    claim = {'binding': binding, 'requests_reserved': 40,
             'command_sha256': canonical_sha256(command)}
    if lease is not None:
        claim['owner_sha256'] = hashlib.sha256(lease[1]).hexdigest()
    create(root/'resume.claim.json', claim)
    started = time.monotonic()
    child = None
    with (root/'resume.private.log').open('xb') as stream:
        try:
            if lease is not None:
                os.write(lease[0], lease[1])
            child = subprocess.Popen(command, stdout=stream, stderr=stream,
                                     start_new_session=True, pass_fds=pass_fds, cwd=cwd)
            deadline = started + timeout
            while child.poll() is None and time.monotonic() < deadline:
                try: sampled, rows = journal(output)
                except (OSError, ValueError, HarnessError): rows = []
                if 4 <= len(rows) < 20:
                    # Keep the EOF guardian runnable until the actual hard
                    # kill. Stopping its group would disable parent-loss cleanup.
                    break
                time.sleep(.002)
            else:
                raise HarnessError('QUAL_NOT_INTERRUPTED', 'no committed prefix with unfinished work')
            observed_prefix = sampled
            _signal(child, signal.SIGKILL)
            killed = _wait(child, 30)
            if killed != -signal.SIGKILL:
                raise HarnessError('QUAL_UNKNOWN', 'owned kill not confirmed by wait')
            raw = output.read_bytes()
            # Retain a torn last append without editing it. The public engine
            # must recover it itself; only complete rows enter prefix parity.
            before = raw[:raw.rfind(b'\n')+1]
            rows = [json.loads(line) for line in before.splitlines()]
            if not raw.startswith(observed_prefix) or not 4 <= len(rows) < 20:
                raise HarnessError('QUAL_NOT_INTERRUPTED','need a preserved complete prefix and unfinished rows at hard kill')
            with output.open('rb') as retained:
                os.fsync(retained.fileno())
            for name,data in [('resume.before.jsonl',before),('resume.killed.raw',raw)]:
                with (root/name).open('xb') as snapshot:
                    snapshot.write(data); snapshot.flush(); os.fsync(snapshot.fileno())
            # Live observation, not a PID that can later be used as authority.
            create(root/'resume.killed.json', {**claim, 'exit_code': killed,
                   'before_sha256': hashlib.sha256(before).hexdigest(),
                   'raw_sha256': hashlib.sha256(raw).hexdigest(),'before_rows': len(rows)})
            if lease is not None:
                os.write(lease[0], lease[1])
            child = subprocess.Popen(command, stdout=stream, stderr=stream,
                                     start_new_session=True, pass_fds=pass_fds, cwd=cwd)
            result = _wait(child, max(.001, deadline-time.monotonic()))
            if result != 0:
                raise HarnessError('QUAL_UNKNOWN', 'resume did not finish successfully')
            after, completed = journal(output)
            if not after.startswith(before) or len(completed) != 20:
                raise HarnessError('QUAL_JOURNAL', 'resume changed prefix or did not finish twenty rows')
            create(root/'resume.observed.json', {**claim, 'kill_exit_code': killed,
                   'resume_exit_code': result, 'before_rows': len(rows), 'after_rows': len(completed),
                   'before_sha256': hashlib.sha256(before).hexdigest(),
                   'after_sha256': hashlib.sha256(after).hexdigest()})
        finally:
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=30)
    return read_json(root/'resume.observed.json')


def verify_drill(root, binding):
    claim = read_json(root/'resume.claim.json')
    killed = read_json(root/'resume.killed.json')
    observed = read_json(root/'resume.observed.json')
    before, prefix = journal(root/'resume.before.jsonl')
    after, rows = journal(root/'runs/resume/completions.jsonl')
    raw = (root/'resume.killed.raw').read_bytes()
    if (claim.get('binding') != binding or claim.get('requests_reserved') != 40
        or any(killed.get(k) != v or observed.get(k) != v for k,v in claim.items())
        or killed.get('exit_code') != -9 or observed.get('kill_exit_code') != -9
        or observed.get('resume_exit_code') != 0 or not 4 <= len(prefix) < 20
        or len(rows) != 20 or not after.startswith(before)
        or killed.get('before_rows') != len(prefix) or observed.get('before_rows') != len(prefix)
        or observed.get('after_rows') != 20
        or killed.get('before_sha256') != sha256_file(root/'resume.before.jsonl')
        or killed.get('raw_sha256') != hashlib.sha256(raw).hexdigest()
        or raw[:raw.rfind(b'\n')+1] != before
        or observed.get('before_sha256') != sha256_file(root/'resume.before.jsonl')
        or observed.get('after_sha256') != sha256_file(root/'runs/resume/completions.jsonl')):
        raise HarnessError('QUAL_EVIDENCE', 'owned observations or actual journals differ')
    return observed
