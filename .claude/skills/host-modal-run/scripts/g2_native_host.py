#!/usr/bin/env python3
"""Prepare and verify the existing locked native Host runtime; never call Modal."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


CHECK = '''import importlib.util, pathlib, platform, sys
import modal
engine = pathlib.Path(sys.argv[1]).resolve()
assert platform.python_version() == sys.argv[2]
assert modal.__version__ == '1.5.4'
assert importlib.util.find_spec('tuner') is None
assert importlib.util.find_spec('synaptic_host') is None
sys.path.insert(0, str(engine))
for name in ('tuner', 'synaptic_tuner'):
    spec = importlib.util.find_spec(name)
    assert spec is not None
    locations = list(spec.submodule_search_locations or ())
    if spec.origin not in (None, 'namespace'):
        locations.append(spec.origin)
    assert locations and all(pathlib.Path(p).resolve().is_relative_to(engine) for p in locations)
print('G2 NATIVE CHILD PASS')
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-runtime', action='store_true',
                        help='allow the existing hash-pinned uv/Python dependency bootstrap')
    args = parser.parse_args(argv)
    project = Path(__file__).resolve().parents[3]
    engine = project / 'synaptic-tuner'
    git = '/mnt/c/Program Files/Git/cmd/git.exe' if str(project).startswith('/mnt/') and Path('/mnt/c/Program Files/Git/cmd/git.exe').is_file() else 'git'
    def read_git(root, *arguments):
        return subprocess.check_output([git, '-c', 'safe.directory=*', *arguments],
                                       cwd=root, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       text=True).strip()
    try:
        head = read_git(project, 'rev-parse', 'HEAD')
        pin = read_git(project, 'ls-tree', 'HEAD', '--', 'synaptic-tuner').split()[2]
        if read_git(project, 'status', '--porcelain') or read_git(engine, 'status', '--porcelain'):
            raise ValueError('dirty source')
        if read_git(engine, 'rev-parse', 'HEAD') != pin:
            raise ValueError('engine pin mismatch')
        sys.path.insert(0, str(project))
        from synaptic_host import launcher
        from synaptic_host.cli import _read_committed_git_blob_v1
        # Exercise the real committed-source reader, including its Git environment.
        _read_committed_git_blob_v1(project, 'synaptic.yaml', maximum_bytes=1048576,
                                    expected_commit=head)
        try:
            launcher._runtime_proof(project, engine)
        except Exception:
            if not args.prepare_runtime:
                print('G2 NATIVE REFUSED: locked runtime not prepared; use --prepare-runtime')
                return 1
            requirements = engine / 'requirements/modal-launcher-v1.lock'
            launcher._build_runtime(project_root=project, requirements=requirements,
                                    expected=launcher._runtime_stamp(requirements))
        launcher._runtime_proof(project, engine)
        # Disable saved-profile reads in the credential-free verification child.
        environment = {'PATH': '/usr/bin:/bin', 'MODAL_IS_REMOTE': '1'}
        result = subprocess.run([str(launcher.launcher_python(project)), '-I', '-B', '-c', CHECK,
                                 str(engine), launcher._PYTHON_VERSION], cwd=project,
                                env=environment, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True)
        if result.returncode or result.stdout.strip() != 'G2 NATIVE CHILD PASS':
            raise ValueError('native child check failed')
    except Exception:
        print('G2 NATIVE FAIL: source, storage, bootstrap or isolated-runtime check refused')
        return 1
    print('G2 NATIVE PASS: committed source, engine pin, runtime proof, SDK, containment, closed environment')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
