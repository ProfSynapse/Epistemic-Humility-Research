"""Sequential CPU half of the one-edit construction, run after the signed capture.

Uses only the registered entry points. It stops at the first refusal and never
rescales or retries. Output is hash-only: it prints no row text. A refusal from
prepare, validate, export or audit ends the proposal under AMENDMENT section 3.
"""
import json
import shutil
import sys
from pathlib import Path

from hs20_nwe import astra_fixed as af
from hs20_nwe import astra_run as run
from hs20_nwe import weights
from hs20_nwe.config import EXPERIMENT_DIR, Layout
from hs20_nwe.engine import Engine

ROOT = Path('/workspace')
layout = Layout(ROOT)
engine = Engine(ROOT, [])
proposal_path = EXPERIMENT_DIR / 'astra_r1.yaml'
proposal = af.load_proposal(proposal_path)
P = 'astra-r1/patch'
local = layout.local
base = local('base_model')
edited = local('astra-r1/checkpoints/edited')


def say(step, **fields):
    print(json.dumps({'step': step, **fields}, sort_keys=True), flush=True)


def stop(step, code):
    say(step, passed=False, exit_code=code)
    raise SystemExit(code or 1)


def engine_json(step, verb, ref, *flags):
    out = local(f'{P}-inputs/{step}.json')
    code, document = engine.run_json([verb, '--weights-config', ref, *flags, '--json'], out)
    if code != 0 or document is None:
        stop(step, code)
    return document


def fixed(*args):
    return af.main(['--proposal', str(proposal_path), *args])


def main():
    local(f'{P}-inputs').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(EXPERIMENT_DIR / 'runtime/inspect.yaml', local(f'{P}-inputs/inspect.yaml'))
    listing = engine_json('inspect', 'weights-inspect', layout.ref(f'{P}-inputs/inspect.yaml'))
    target, _ = af.resolve_target(proposal, weights.unwrap(listing))
    base_npy = local(f'{P}-inputs/base_tensor.npy')
    say('read_base', **run.read_tensor(proposal, base, target['sha256'], base_npy))
    shared = ['--roster', str(local('astra-r1/inputs/roster.json')), '--capture-dir', str(local('astra-r1/capture')),
              '--capture-binding', str(local('astra-r1/capture_request.json')),
              '--c-hat', str(ROOT / 'experiments/common/directions/qwen35-4b-hs20/c_hat.json'),
              '--base-tensor-npy', str(base_npy)]
    code = fixed('prepare', *shared, '--inspect-listing', str(local(f'{P}-inputs/inspect.json')),
                 '--checkpoint-ref', layout.ref('base_model'), '--payload-ref', layout.ref(f'{P}/payload.safetensors'),
                 '--export-ref', layout.ref('astra-r1/checkpoints/edited'), '--out-dir', str(local(P)))
    if code:
        stop('prepare', code)
    spec = layout.ref(f'{P}/spec.yaml')
    engine_json('validate', 'weights-patch', spec, '--validate')
    exported = weights.unwrap(engine_json('export', 'weights-patch', spec, '--export'))['manifest']
    edited_npy = local(f'{P}-inputs/edited_tensor.npy')
    say('read_edited', **run.read_tensor(proposal, edited, exported['tensors'][0]['after_sha256'], edited_npy))
    code = fixed('audit', *shared, '--prepare-report', str(local(f'{P}/prepare_report.json')), '--spec', str(local(f'{P}/spec.yaml')),
                 '--payload', str(local(f'{P}/payload.safetensors')), '--edited-tensor-npy', str(edited_npy),
                 '--out', str(local(f'{P}/audit.json')))
    if code:
        stop('audit', code)
    code = run.main(['freeze', '--base-model', str(base), '--edited-model', str(edited),
                     '--audit-ref', layout.ref(f'{P}/audit.json'), '--spec-ref', spec,
                     '--payload-ref', layout.ref(f'{P}/payload.safetensors'),
                     '--prepare-ref', layout.ref(f'{P}/prepare_report.json')])
    if code:
        stop('freeze', code)
    say('construction', passed=True)


if __name__ == '__main__':
    sys.exit(main())
