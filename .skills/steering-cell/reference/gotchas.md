# Known gotchas (cloud + GPU)

Distilled from the AA/AC/AG/AK/AL/AN harnesses and the item-11 equivalence work.
Each of these has burned a real run at least once.

## hf_xet hangs multi-GB pulls with no timeout

The xet CAS backend (which supersedes hf_transfer) stalls in `xet_get` without a
timeout on large repo pulls - it froze at ~5GB and killed a RunPod run and two
Modal runs. Force the classic resolve endpoint:

```
HF_HUB_DISABLE_XET=1
HF_HUB_ENABLE_HF_TRANSFER=0
```

`steer_cell.py` sets both inside its entrypoint; `modal_steer_cell.py` bakes them
into the image env AND re-sets them in the function before any HF/unsloth import
(the image-layer env can be bypassed, so the in-function set is the one that
actually holds). Diagnosis kit if a pull hangs: `py-spy dump` the stuck PID and watch
`/proc/net/dev` RX flatten.

## PEFT / Unsloth wrapping hides the decoder layers

A PEFT-wrapped causal LM is `PeftModelForCausalLM -> LoraModel -> base`; the
decoder `ModuleList` is several attributes deep and differs across architectures.
`steer_cell._decoder_layers` unwraps via `get_base_model()` then walks the known
paths (`model.layers`, `language_model.model.layers`, `model.decoder.layers`,
`transformer.h`). If a new arch fails to resolve, add its path there rather than
special-casing the caller.

## Layer index off-by-one (hidden_states vs block)

`hidden_states[L]` is the OUTPUT of decoder block `L-1` (`[0]` is the embedding).
A direction fit at "L35" reads `hidden_states[35]`, which is block index 34's
output, so the hook registers at `layers[34]` (= `layers[L-1]`). The runner does
this mapping; a direction JSON that records `layer: 35, block: 34` is self-checking
- assert they agree.

## Clone idempotency on respawn

A retried Modal container must not fail because the workspace already exists. The
wrapper clones only when `.git` is absent, then always `git fetch` + `git checkout`
the pinned commit, so a respawn converges to the same tree.

## ULP floors for equivalence / readback checks

Batched-vs-loop and steered-vs-baseline comparisons carry bf16 accumulation noise;
an ABSOLUTE hidden-state comparison is strictly noisier than a DELTA comparison
(the delta cancels the shared batched noise). The smoke readback compares the
COMMANDED coordinate move against the observed one with a tolerance
(`readback_tolerance`), not exact equality - set it above the bf16 floor for your
model, not to zero.

## Reap-proof spawn (detach) + TaskStop skips `finally`

`modal run` without `--detach` dies with the client - always detach long runs
(see modal-launch.md). Separately: a `TaskStop` on a subagent terminates the
process and does NOT run `finally` blocks, so a checkpoint/cleanup in a `finally`
may not fire; rely on the periodic Volume checkpoint (committed every 120s), not
an end-of-run flush, for durability. The `DONE` marker is written only on clean
completion, so its absence means the run did not finish.

## Smoke-first is the cheap insurance

The most expensive failure is a write bug discovered after the full sweep burned.
The runner refuses a full arm without a recorded smoke pass for exactly this
reason. Do not `--force-no-smoke` to "save time" on a steering arm - the smoke is
one readback forward pass per flagged row over `smoke.n` rows.
