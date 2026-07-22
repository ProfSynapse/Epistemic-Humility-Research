# Organization

Read this when deciding where configs, directions, renderers, graders, outputs,
and signing pins belong.

## Experiments-first layout

New evidence-producing work follows the experiments-first layout: one
self-contained directory per experiment at `experiments/<semantic-slug>/`. A
typical cell directory contains a signed `AMENDMENT.md` when the work is
governed, an `experiment.yaml` manifest, `NOTEBOOK.md`, and mechinterp configs
such as `pipeline.yaml`, `extract.yaml`, `probe_fit.yaml`, `cell.yaml`,
`dose_calibration.yaml`, and `gates.yaml`.

The singular `archive/experiment/phase1/` tree is the historical locked training-regimen record. Do not
add new cells there.

Use the `experiments` skill and `bin/exp` tooling for directory lifecycle,
manifest fields, generated indices, signing, resolving, and validation. Use the
experiment-runner reference `../experiment-runner/reference/amendment-vs-lab-notebook.md`
before deciding whether a task needs a signed amendment, a lab-notebook entry,
or no governed record.

## Cell configs

Cell configs live with the experiment that owns them:

```text
experiments/<semantic-slug>/
  pipeline.yaml
  extract.yaml
  probe_fit.yaml
  cell.yaml
  dose_calibration.yaml
  gates.yaml
```

Use semantic slugs that describe the work. Avoid legacy letter-code naming for
new experiment slugs.

## Directions

Direction JSONs are data in `mechinterp-direction/v1` format. Their first home
is the consuming experiment's own gitignored direction directory:

```text
experiments/<semantic-slug>/directions/
```

When a second experiment consumes the same direction, promote it to a shared
location and record the originating experiment in provenance:

```text
experiments/common/directions/<checkpoint>/
```

Recipes reference directions by relative repo path.

## Shared renders and graders

Shared project plug-ins live under:

```text
experiments/common/renders/
experiments/common/graders/
```

Reference them as `module:callable` and put those directories on `PYTHONPATH`.
A signed cell byte-pins every helper that can affect rows, prompts, grades, or
gates. Record sha256 pins in the governed doc alongside config shas.

## Signing discipline

At signing, pin sha256 for:

- `cell.yaml`
- `gates.yaml`
- grader modules
- render modules
- any other helper listed in the experiment instrument

Also pin the execution surface for every GPU stage:

- engine and exact library version;
- container image digest and GPU hardware class;
- model and tokenizer revisions;
- dtype, tensor parallel size, scheduler limits, and batch-invariance setting;
- renderer, generation, EOS, stopping, and structured-output schema hashes;
- hidden-state layer/index, normalization, and anchor contracts when capturing.

For new unsteered work, read the experiment-runner
`reference/batched-generation.md` and prefer vLLM. Record the required smoke or
HF bridge in `NOTEBOOK.md` before signing. A parity-locked cell retains its
registered engine even when another backend is faster.

Set `surface.expected_config_sha` in `cell.yaml` to the signed cell config pin.
The tuner enforces that value at runtime so the config cannot drift silently.

Do not move goalposts after the result. If exploratory work produces a promising
signal, register a confirmatory replication before using it as a claim.

Every module listed in `instrument.modules` also needs a persistence
declaration in `experiment.yaml` before `bin/exp sign` will pin it: see the
experiments SKILL.md "Persistence declarations" section for the
`persistence: incremental` / `persistence: short-run` shapes. `bin/exp sign`
refuses to sign an instrument whose modules are missing one.

### Kill-resume smoke drill (mandatory pre-sign for `persistence: incremental`)

A module declared `persistence: incremental` claims it survives a kill and
resumes cleanly. That claim is only real once it has been drilled, not once
it has been read. Before signing any experiment whose instrument declares an
`incremental` module, run this drill and record the result (pass/fail, dated)
in the experiment's `NOTEBOOK.md`:

1. Launch the module's smoke run (small `n_rows`, same config the signed cell
   will use) through `experiments/common/launch_detached.sh` so it is not
   tied to this session.
2. Once it has written at least one checkpointed item (confirm via the
   `RunLog` JSONL / summary sidecar, not just a process-alive check), kill it
   with `kill -9 <pid>` read from the `.pid` file `launch_detached.sh` wrote.
   This must be a hard kill (`SIGKILL`), not a graceful stop: a graceful
   `SIGTERM` handler can paper over a design that would not actually survive
   an OOM, a host bounce, or a session teardown.
3. Relaunch the identical command. It must pick up from the checkpoint (via
   `RunLog.iter_pending`, see `experiments/common/README-runlog.md`), not
   restart from item zero and not silently drop the items that were already
   in flight when it was killed.
4. Assert the resumed run's final output (rows, summary counts, any derived
   stats) is identical to an uninterrupted smoke run over the same rows.
   A resumed run that completes but produces a different row count or a
   different summary than the uninterrupted baseline is a fail, not a pass
   with caveats.

A validator or `grep` check that the module imports `RunLog` is NOT
acceptable evidence for this drill. Import presence proves the module knows
the class exists; it proves nothing about whether the checkpoint is written
at the right cadence, whether `iter_pending` is called correctly, or whether
resume actually reproduces the uninterrupted result. Only the drill above,
actually executed and actually observed to resume and match, is acceptable
pre-sign evidence.

## Outputs and run tags

Outputs are untracked under the experiment's own analysis area:

```text
experiments/<semantic-slug>/analysis/
```

Committed aggregate artifacts belong only where the experiment manifest and
governance say they belong, commonly an `analysis-committed/` style directory
when the project has established one for that experiment. Do not commit
restricted row text or raw per-row generations.

Use run tags shaped like:

```text
<semantic-slug>-r<N>
```

Smoke-state files live with outputs and are not committed.
