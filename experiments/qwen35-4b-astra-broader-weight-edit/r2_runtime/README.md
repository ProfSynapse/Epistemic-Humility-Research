# R2 runtime fixture : integration candidate, not launch-ready

Integrate this directory at `experiments/qwen35-4b-astra-broader-weight-edit/r2_runtime`.
Integrate the uniquely named test files beside the parent's constructor tests.
No constructor, protocol, YAML, manifest, parent source or repository Git state was edited.

## Ports and boundary

`ORIGINS.json` records exact R1 source hashes and selected-definition provenance.
The runtime imports only its own ports, the intentionally parent-owned `hs20_r2`,
third-party libraries and installed public `engine_host` interfaces. It never
imports R1, Tuner internals or an engine source checkout. `astra_fixed.py` is only
roster I/O compatibility: it has no construction or min-cap implementation.
`constructor.py` calls `hs20_r2.astra_r2` and binds the complete R2 YAML separately
from the constructor's numerical-subset digest.

Unchanged functions retain R1 prompts, retry wording, JSON parsing, detector,
CG1, aliases, bootstrap and semantic acceptance gates. `benchmark_stats.py`
retains only the bootstrap closure, excluding unused SciPy/McNemar. `render.py`
retains only the thinking-scaffold assertion, excluding old renderer fallbacks.
`integrity.py` retains only the grading evidence stamp, excluding pilot stages.
New runtime behavior: exact ordered eight cells; source/host pin closure;
full checkpoint inventory equality; fresh qualification before either benchmark
arm; qualification lineage in every cell and analysis; immutable complete-cell
resume. The public CLI still owns per-request resume journals and parent-death
handling (`guard_parent=True`, inherited GPU writer lock).

## Entrypoints

- `python -B -m r2_runtime.astra_run --proposal <astra_r2.yaml> plan`
- `r2_runtime.astra_run`: materialize, preflight, read-tensor, capture, freeze,
  eval-cell. Use `--help` for exact argument order.
- `python -B -m hs20_r2.astra_r2 prepare ...` remains the constructor's own CLI.
- `python -B -m r2_runtime.checkpoint_audit --help`: reload every checkpoint
  tensor through parent-owned `audit_checkpoint`, bind preparation/spec/payload
  and the public engine export manifest, create an immutable R2 audit report.
- `r2_runtime.astra_qualification`: prepare, run, verify. **Verify is blocked**
  as described below; this is not a signable production implementation yet.
- `r2_runtime.astra_analysis`: pool-build, pool-commit, commit-hash, regrade,
  spot-pack, spot-record, apply, rollup. Git commitments remain parent actions.

## Concrete remaining blockers

1. This CPU environment has no installed `engine_host`; `find_spec` returned
   None. Actual installed source/API/version and process ownership could not be
   checked. There is no qualified public owned-SIGKILL transport in this fixture.
   The R1 code read here exposes synchronous `EngineCLI.run(operation, args,
   guard_parent=True, pass_fds=...)`. That call alone does not establish an owned
   kill handle or interrupted-request count. No claim is made that the installed
   host lacks additional APIs; the parent must inspect its actual installation.
   `run --name resume` and `verify` reject with `PUBLIC_OWNED_KILL_TRANSPORT`.
   Do not replace them with PID signalling, JSON assertions, a synthetic pass,
   an ad hoc backend or a signed `qualified: true` shortcut. Complete the reviewed
   public transport integration first. Four repeat runs reserve 20 requests each;
   the remaining interrupted/resume budget is 40, total at most 120, no retries.
2. Parent must authenticate/promote the original non-evaluation twenty-row
   qualification prompt roster and original R1 development capture. The freeze
   command requires `--qualification-rows-ref` and binds this roster before any
   benchmark. Qualification preparation checks the exact retained prompt/token
   commitments. It does not silently regenerate a new roster. Original capture
   reuse needs the parent's authenticated old-to-new dependency comparison;
   the new capture verifier intentionally cannot relabel old R1 fingerprints.
3. Parent must supply `runtime/r2_host_binding.json` from the installed public
   host (`admission.host_identity`) and sign it along with every runtime and
   constructor module. Actual host image and installed wheel are checked before
   engine calls. Runtime source and constructor files must be present together.
4. Full checkpoint bridge is CPU source integration only here. Actual engine
   export schema compatibility, broad bf16 engine/readback parity, tokenizer-only
   full surface checks, immutable T7 custody and runtime qualification remain
   parent-owned real-engine acceptance work. No torch/model/checkpoint calls ran.

## Parent manifest proposal : not applied

Include every `.py`, `.json`, `.yaml` member of `r2_runtime` and `hs20_r2` in
`instrument.modules` (or configs as appropriate), plus `runtime/r2_host_binding.json`,
`astra_r2.yaml`, `astra_runtime.yaml` and original governing configs. Pin all of
these before effects. Avoid pinning a manifest that recursively contains itself.
`admission.sources` includes code/origins but excludes this explanatory Markdown.

Use incremental persistence for `astra_run.py` and `astra_qualification.py`, with
private checkpoint paths `analysis/.../astra-r2/operations.jsonl` and
`analysis/.../astra-r2/edited-qualification/`. Engine outputs preserve each row.
The qualification request reservations are create-only and cannot replay an
uncertain consumed run. Use incremental grading declarations for `astra_analysis`
and `adjudication` at the retained `grading/` manifests/commit logs. For the
constructor, full checkpoint audit and tokenizer preflight, measure actual bounded
smokes before choosing short-run declarations. Do not put invented seconds into
the manifest. The local CPU test duration is not a T7 persistence measurement.

Qualification publication must bind complete edited checkpoint inventory, image,
proposal/spec/freeze, installed host, engine wheel and full constructor/runtime
source hashes. It must attest the exact original roster, two fixed orders times
two repeats, natural finish/schema/prompt token equality and actual owned kill /
resume, with a durable total request ledger <=120. Parent commits it before ANY
benchmark arm. No behavioral admission or format-retry rescue is allowed.

## Local CPU validation

Final invocation: Python 3.12.15, pytest 8.4.2, `python -B -m pytest -q -p
no:cacheprovider <fixture>/tests`: **12 passed**. No packages were installed or
environments changed. Because the shared Tuner CPU venv lacks jsonschema and
threadpoolctl, existing cached package directories were placed on this test
process's PYTHONPATH. No download occurred. Required paths on this host:

- interpreter: `/home/profsynapse/Code/Synaptic-Tuner/.venv/bin/python`
- EHR_R2_CONTRACT_DIR: the parent's `experiments/qwen35-4b-astra-broader-weight-edit`
- PYTHONPATH: this fixture experiment; constructor fixture experiment at
  `/home/profsynapse/.t3/worktrees/Synaptic-Tuner/t3-530322c2/scratch/ehr-r2-fixture/experiments/qwen35-4b-astra-broader-weight-edit`;
  these existing `/home/profsynapse/.cache/uv/archive-v0/` directories:
  `exIbUWRWLPdazt6Q`, `mZj0r75bh_o7McxS`, `kWkT78BiBsDCtjhw`,
  `dmfMDin6wWNj5_8u`, `DvI23DcyeDukPpjw`, `t4CqqslWR7HnaX8T`.

The external constructor path is test-only read access to the delivered
parent-owned package, not a runtime path injection in shipped code. Integration
must put both packages in the same new experiment. Real engine/GPU/export,
measured qualification and signing were not attempted. `tests/r2_runtime_delivery.json`
records final delivery hashes and the exact validation scope.
