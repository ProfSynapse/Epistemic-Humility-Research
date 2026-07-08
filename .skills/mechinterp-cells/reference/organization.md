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

The singular `experiment/phase1/` tree is the historical Phase 1 record. Do not
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

Set `surface.expected_config_sha` in `cell.yaml` to the signed cell config pin.
The tuner enforces that value at runtime so the config cannot drift silently.

Do not move goalposts after the result. If exploratory work produces a promising
signal, register a confirmatory replication before using it as a claim.

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
