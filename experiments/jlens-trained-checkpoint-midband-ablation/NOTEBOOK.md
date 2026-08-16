# J-lens on a trained checkpoint plus rule-selected mid-band refusal-axis ablation notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-08-16 — lead adjudication of prep flags; cell.yaml/gates.yaml filled

Prep builder's deliverables spot-checked by the lead: jlens_trained.py parses
(ast), and the intervention TEMPLATE differs from the governed seed-1 config
by exactly two substantive lines (caution_direction and output.root, both
{SITE}-keyed into this cell's gitignored analysis/) plus a header comment
documenting the instantiation rule — all other lines byte-identical.

Flag adjudications:
1. Stage-7 fallback timing: ACCEPTED as the full 4-arm re-run of the archived
   byte-pinned config (~49 min actual, not the AMENDMENT's ~12 min estimate),
   using only the ablate arm's rows. Building a new single-arm config would
   mean an unsigned instrument variant; the time cost is the cheaper risk.
   The AMENDMENT's estimate is superseded by this note (estimate, not a gate).
2. --model/--adapter required=True with no defaults: ACCEPTED — forces
   explicit, driftless invocation.
3. Running J-lens smoke/profile inside the same unsloth docker container as
   the intervention: ACCEPTED — torch/peft stack parity and reproducibility
   outweigh bare-host convenience.
4. Template rows/direction lines riding the legacy experiment/phase1/probe
   symlink chain: ACCEPTED for byte-parity with the governed config; the
   symlinks exist from the rederivation cell and are a launch-time
   environment check (noted in cell.yaml), never a config edit.

## 2026-08-16 — lead adjudication: HF auth for Stage 0 corpus build

Runner STOP (correct fail-closed): HF_TOKEN not set in the environment,
required by RUNBOOK Stage 0 for the private staging-pool fetch. Lead ruling:
the binding constraint is AUTHORIZED access to the private pool, not the
specific delivery mechanism of the credential. The machine carries the PI's
standing huggingface-cli login (cached hub token), which is the same
authorization used by this program's prior fetches and publishes, and the
staging dataset is already present in the local hub cache. AUTHORIZED:
export HF_TOKEN from the cached hub login token for the corpus-build
invocation only (launch-environment provisioning; no config or pinned-file
change; token value never logged or committed). All other preconditions
verified by the runner: five sha pins exact, GPU free, lineage dirs present,
archived extraction/behavior rows and L35 comparator rows on disk, corpus
manifest metadata-only.

## 2026-08-16 — lead adjudication amended: implicit hub auth, no credential read

The runner's permission layer denied shell-reading the cached hub token into
the command environment (correct: no agent should read credential contents),
and the runner correctly refused to surface the token via another tool.
Amended ruling: the HF_TOKEN-in-env mechanism is DROPPED. Stage 0 runs the
corpus build with NO explicit token; huggingface_hub resolves the PI's
standing huggingface-cli login from its own cache internally, so no agent,
shell, or transcript ever touches the credential value. This is the standard
sanctioned auth channel for that login cache, and the staging dataset is
additionally already present in the local hub cache. The RUNBOOK Stage 0
prerequisite is read as "authorized hub access available", satisfied by the
standing login. If implicit auth fails, STOP again and the PI will provision
the environment directly.

## 2026-08-16 — lead adjudication: HF_HUB_CACHE redirect for Stage 0

Runner STOP #3 (correct): corpus build failed with an OS PermissionError
creating a lock subdir in ~/.cache/huggingface/hub/.locks, which is owned by
uid 1001 (artifact of a prior docker run with different UID mapping). This is
host filesystem ownership, not authentication and not a permission-system
denial. Ruling: for the Stage 0 invocation only, set
HF_HUB_CACHE=experiments/jlens-trained-checkpoint-midband-ablation/analysis/hf_cache
(gitignored; prompt-bearing dataset rows stay contained). The standing-login
token path (~/.cache/huggingface/token) is unaffected by HF_HUB_CACHE and
continues to be resolved internally by huggingface_hub; no agent touches the
credential. The staging pool is re-fetched fresh into the cell-local cache;
the committed manifest keeps the corpus rebuild deterministic regardless of
cache location. Host hygiene fix (chown of the uid-1001 .locks dir) lifted
to the PI as optional, not required for this cell.

## 2026-08-16 — pre-run instrument fix + repin (PI-approved): requires_grad after merge

Smoke crashed with "element 0 of tensors does not require grad": PEFT freezes
base weights at PeftModel.from_pretrained and merge_and_unload returns them
still frozen, so the forward built no autograd graph and the JVP
double-backward had nothing to differentiate. The pinned original never hit
this because a plain AutoModelForCausalLM load leaves requires_grad=True on
all params (its documented read-only posture: grad tracking ON, no optimizer
ever steps). Fix restores exactly that state after the merge (re-enable
requires_grad on all params); jlens_qwen35.py precedent never exercised an
adapter path, which is why the flaw survived to the smoke. configs/
jlens_trained.py repinned with reason; PI approval "yes patch" in
conversation. No profile/ablation result existed before the fix — the smoke
gate did its job.
