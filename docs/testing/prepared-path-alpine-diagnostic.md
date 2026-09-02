# Prepared-path host run — TEST report

**Task** #93 (TEST phase #77, feature #73), agent `test-host`, 2026-09-02.
**Design of record** `docs/architecture/prepared-path-alpine-diagnostic.md`
(sections 9, 10, 6.3, 7, 4).
**Verdict** RED. The run did not reach the trainer. Three defects block it, and
one previously-open blocker is now settled as a measured fact.

---

## 0. Summary, in the order the lead has to act

| # | Finding | Kind | Owner | Blocks the run? |
|---|---|---|---|---|
| **B-3** | `materialize_model_inventory.py` sends CRLF to `sh -s`; the container dies on `set -eu\r` | Operator-script defect, Windows-only | `coder-workflow` | Yes — no inventory |
| **B-1'** | The committed mount candidate `docker-desktop` + `/mnt/host` **cannot be bound by the engine**. The designed fallback `Ubuntu-22.04` + `/mnt` **works** | Configuration; needs a COMMITTED profile edit | lead ruling | Yes — no mounts |
| **B-4** | The prepared composition emits **no `--entrypoint`**, and the committed image's `ENTRYPOINT` discards the workload argv and `exec`s `supervisord` | **Host defect**, structural | lead routes | Yes — trainer never runs |
| **B-2** | LoRA adapter ref equality | **CONFIRMED by measurement** on this image | user pin decision | Would block verification |

Nothing was fixed. No code was edited in either tree. The released checkout is
byte-clean (section 7).

---

## 1. Trees, toolchain, and the clean baseline

Execution root (the project root for everything below):
`F:\Code\ehr-release-808e9f4d`. Report root (this file):
`F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host-clean`.

```
$ git.exe -c safe.directory='*' -C 'F:\Code\ehr-release-808e9f4d' rev-parse HEAD
808e9f4df6c0af6f22b6c0028c95a4e20b86b251
$ git.exe ... rev-parse --abbrev-ref HEAD
feat/submodule-cloud-api-v1-host
$ git.exe ... status --porcelain
(no output, exit 0)
$ git.exe ... submodule status
 aec998ee8d6a2e58d86e19e8132bc59aa21ebd53 synaptic-tuner (aec998e)
```

Baseline clean, engine pinned at `aec998ee`.

### 1.1 The winpy recipe had to be retargeted, and that is load-bearing

The worktree's `scratch/test-phase/winpy2.sh` sets
`WINROOT='F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host-clean'`
and ends in `-m pytest`. Copied verbatim it would put the **worktree** on
`PYTHONPATH`, and since the project root is computed from the package location
(`synaptic_host/__main__.py:19`, `parents[1]`), every derived mount source would
then name the worktree rather than the released checkout.

Both files were copied verbatim into `F:\Code\ehr-release-808e9f4d\scratch\test-phase\`
for provenance, and a retargeted sibling `winpy-release.sh` was added there
(`scratch/` is gitignored at `.gitignore:9`). Import smoke:

```
$ scratch/test-phase/winpy-release.sh -c "import synaptic_host; ..."
synaptic_host: F:\Code\ehr-release-808e9f4d\synaptic_host\__init__.py
project root: F:\Code\ehr-release-808e9f4d
python: 3.12.7 (tags/v3.12.7:0b05ead, Oct  1 2024) [MSC v.1941 64 bit (AMD64)]
[exit 0]
```

Assumption (9) of the teachback is **confirmed**: the released checkout is what
Windows Python imports, and `parents[1]` resolves there.

---

## 2. Orientation (no containers started, no image pulled)

| Check | Command | Result |
|---|---|---|
| Engine version | `docker.exe version --format '{{.Client.Version}} \| server={{.Server.Version}}'` | `29.3.1 \| server=29.3.1` |
| Context | `docker.exe context show` | `desktop-linux` |
| Endpoint | `docker.exe context inspect desktop-linux --format '{{.Endpoints.docker.Host}}'` | `npipe:////./pipe/dockerDesktopLinuxEngine` |
| nvidia runtime | `docker.exe info --format '{{json .Runtimes}}'` | key `"nvidia"` present, `path: nvidia-container-runtime` |
| Training image by digest | `docker.exe image inspect '…@sha256:5266c57b…'` | present; `User=unsloth:runtimeusers`; RepoDigest matches |
| Probe image | `docker.exe image inspect python:3.12-slim` | present, `sha256:09f7da3b…` |
| Host GPU | `nvidia-smi.exe --query-gpu=name,driver_version,memory.total --format=csv` | `NVIDIA GeForce RTX 3090, 610.88, 24576 MiB` |

Every measured host fact in `docs/preparation/environment-model-prepared-path-alpine-diagnostic.md`
that I re-checked **agrees**, including the image `User`, which `preparer-host`
measured and `SKILL.md` cites next to A2.

---

## 3. B-3 — the materialization script cannot run on Windows

Step 4 of the mission. First execution, exit 1:

```
[3/3] running the throwaway container (no -e flag, no credentials forwarded)
    $ "C:\Program Files\Docker\Docker\resources\bin\docker.exe" run --rm -i \
        -v F:\Code\ehr-release-808e9f4d\.synaptic\model-inventory:/out python:3.12-slim sh -s

FAILED M2-container: materialization container exited 2: sh: 1: set: Illegal option -
```

The image pull and digest resolution both succeeded first
(`python@sha256:78387bc3…`), so this is not a network or auth failure. **No
credential was read or passed at any point, and the failure is not auth-related**,
so the mission's "stop and report on an auth failure" branch does not apply;
this is a different stop.

### Cause, established by two controlled runs

`materialize_model_inventory.py:261` calls `_run(argv, stdin_text=shell)`, and
`_run` (`:197-205`) uses `subprocess.run(..., input=<str>, text=True)`. On
Windows, text mode translates `\n` to `\r\n` on the way to the child's stdin.
`dash` inside the container then parses `set -eu\r` and rejects `-eu\r`.

Direct reproduction, isolating only the line ending:

```
$ printf 'set -eu\necho HELLO_LF\n'     | docker.exe run --rm -i --network none --pull never python:3.12-slim sh -s
HELLO_LF                                                                  [exit 0]
$ printf 'set -eu\r\necho HELLO_CRLF\r\n' | docker.exe run --rm -i --network none --pull never python:3.12-slim sh -s
sh: 1: set: Illegal option -                                              [exit 2]
```

And that Windows Python is the source of the CRLF, measured through the same
call shape the script uses:

```
$ winpy-release.sh -c "subprocess.run(['cmd','/c','more'], input='set -eu\necho X\n', text=True, ...)"
text=True  stdout repr: 'set -eu\necho X\n\n'
bytes      stdout repr: b'set -eu\r\necho X\r\n\r\n'
```

The byte-mode round trip shows the `\r\n` that the text-mode round trip hides
(`more` normalises its own output, so the second line is the diagnostic one).

**Class.** A platform-conditioned defect in an operator script, invisible to
CODE because `coder-workflow` could not execute any `docker.exe` invocation in
that phase and correctly said so (`#90` `metadata.consultant_availability`,
"every docker.exe invocation in both scripts is unexecuted"). It is Windows-only,
and Windows is the only platform the script is meant to run on.

**Fix is one line and belongs to `coder-workflow`,** not to me: pass bytes
(`shell.encode("utf-8")` with `text=False`), or open the pipe with
`newline=""`. I did not apply it.

---

## 4. B-1' — the committed mount candidate cannot be bound; the fallback can

Step 5. The checked-in driver, run exactly as the skill prescribes:

```
$ winpy-release.sh 'F:\…\run_prepared_training.py' --probe-only
    PASS P1-single-docker: C:\Program Files\Docker\Docker\resources\bin\docker.exe
    PASS P2-endpoint: npipe:////./pipe/dockerDesktopLinuxEngine
    PASS P3-drive-letter-root: F:
    PASS P5-drive-mount-root: distro=docker-desktop root=/mnt/host
    PASS P6-config-committed: training/smokes/docker-sft.json matches the committed blob

=== mount-source bind probe (blocker B-1 residual) ===
    rendered mount source: \\wsl.localhost\docker-desktop\mnt\host\f\Code\ehr-release-808e9f4d
    $ docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine run --rm --pull never \
        --network none --mount type=bind,source=\\wsl.localhost\docker-desktop\mnt\host\f\Code\ehr-release-808e9f4d,target=/probe,readonly \
        python:3.12-slim sh -c "ls -1 /probe | head -20"

FAILED B1-bind-probe: the engine could not bind
  \\wsl.localhost\docker-desktop\mnt\host\f\Code\ehr-release-808e9f4d
  (candidate drive_mount_root='/mnt/host', wsl_distro='docker-desktop'):
  docker: Error response from daemon: accessing specified distro mount service:
  stat /run/guest-services/distro-services/docker-desktop.sock: no such file or directory
```

Five preconditions passed. The driver stopped at the right place, named the
failing candidate, and printed the exact argv. **The instrument worked.**

The failure is not "the path is empty" (the stale-skeleton symptom section 6.1
warns about). It is that Docker Desktop exposes **no distro mount service for
its own internal `docker-desktop` distro**, so that distro cannot be a bind
source at all. This is risk **R2** materialising.

### The designed fallback was probed and works

Both distros exist:

```
$ wsl.exe -l -v
* Ubuntu-22.04      Running    2
  docker-desktop    Running    2
```

Section 6.3's fallback pair, probed read-only with no profile edit:

```
$ docker.exe --host npipe:… run --rm --pull never --network none \
    --mount type=bind,source=\\wsl.localhost\Ubuntu-22.04\mnt\f\Code\ehr-release-808e9f4d,target=/probe,readonly \
    python:3.12-slim sh -c 'ls -1 /probe | head -10'
AGENTS.md
CLAUDE.md
CONTRIBUTING.md
…
[exit 0]
```

Binds, and lists the released checkout **non-empty**, so it is the real drive
and not a skeleton.

**This is the lead's ruling, not mine.** The change is
`docker_host.drive_mount_root` `/mnt/host` → `/mnt` and `docker_host.wsl_distro`
`docker-desktop` → `Ubuntu-22.04`, and it must be **committed** before it can
take effect, because the config is read as a git blob at the locked project
commit.

> **Flag for the ruling, and I am not resolving it.** The candidate that works
> resolves through `Ubuntu-22.04`'s `/mnt/f`, which is the DrvFs/9p view of the
> F: drive. A standing pinned note in this session's project instructions says
> mount sources should be `wsl.localhost` ext4 and never `/mnt/f` 9p. The design
> also fixes the project root to a Windows drive letter and derives every mount
> source from it (sections 9.1.2, 14.2), so an ext4 source is not reachable
> without contradicting that. The two constraints appear to collide, and which
> one gives is a decision above my level. Model weights over 9p may also be slow,
> but that is performance, not correctness.

### The driver's path rendering is correct

The driver's restated `_wsl_path` produced
`\\wsl.localhost\docker-desktop\mnt\host\f\Code\ehr-release-808e9f4d`, byte for
byte what I rendered by hand from `docker_v1/prepared.py` and what sections 6.1
and 6.3 predict. B-1's implementation (#89) is not at fault; the value it
carries is.

---

## 5. B-4 — NEW: the prepared path never overrides the image ENTRYPOINT

Found while capturing B-2 evidence, then confirmed by reading. **This is a Host
defect and it is structural: it does not depend on B-3 or B-1'.**

### Observed

Running the committed image with a command appended, as the composition does:

```
$ docker.exe run --rm --network none --pull never <image@sha256:5266c57b…> \
    /opt/conda/bin/python3 -c "…"
Exporting environment variables for SSH sessions...
Generating Jupyter configuration...
Setting up Ollama environment...
Handing over control to supervisord...
INFO spawned: 'jupyter' with pid 347
INFO spawned: 'ollama' with pid 348
INFO spawned: 'sshd' with pid 349
```

The command was **discarded**. The container ran Jupyter, Ollama and sshd, and
kept running until I killed it.

### Cause

```
$ docker.exe image inspect '…@sha256:5266c57b…' \
    --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}'
Entrypoint=["/usr/local/bin/entrypoint.sh"] Cmd=null
```

and that script ends:

```
# Final step: hand off control to supervisor
echo "Handing over control to supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

It never `exec "$@"`. Anything passed as CMD is dropped.

The Host appends the workload argv as CMD and passes **no `--entrypoint`**:

```
synaptic_host/docker_v1/control_private.py:396-414
    arguments = ["--name", …, "--pull", "never", "--network", "none", …]
    …
    arguments.append(image.image_digest)
    arguments.extend(workload.arguments)
```

and the final process argv adds only the verb:

```
synaptic_host/docker_v1/cli.py:788-791
    raw = self._execute_argv(
        (policy.executable, "--host", policy.endpoint.host,
         command.verb.value, *command.arguments), …)
```

`grep -rni entrypoint synaptic_host/*.py` returns only workload-document and
closure-manifest fields (`docker_execution.py:961`, `docker_staging.py:36…1574`).
Those are the *engine's* entrypoint **inside** the closure, a different thing.
There is no `--entrypoint` flag anywhere on this path. For contrast the engine's
other lanes do pass one: `tuner/handlers/local_run_handler.py:525`, `:1434`,
`:1491`, and `tuner/cloud/hf_training_image_lock.py:666`, `:715`.

The argv that would be discarded is the one the closure-equality check pins
(`docker_staging.py:1555-1567`):

```
expected_argv = (worker.interpreter, "<engine root>/…/offline_sft_worker.py",
                 "--canonical-workload-file", …, "--canonical-workload-sha256", …)
```

### Consequence, if B-3 and B-1' were fixed and nothing else changed

`docker create`/`start` would succeed, the durable phase would reach `SUBMITTED`,
and the container would sit in supervisord forever. The observe cut returns the
record unchanged on `RUNNING` (`docker_execution.py:1201-1202`), which section
9.2 correctly says **is not a stall** — so the driver would keep observing until
`--max-seconds` (default 3600) and fail as `L2-wall-clock`. An operator would
read an hour of "healthy" observe cuts and a timeout, with no trainer output and
no `trainer.stderr.log`, because the trainer never started. That is the most
expensive possible way to learn this, which is why it is worth stopping now.

**Not mine to fix.** It touches `control_private.py`, which is Host code, and it
interacts with the plan fingerprint and the closure argv equality. It needs the
architect and the lead.

### Same cause, second impact: A1–A3 in the driver

`_assert_a1_gpu`, `_assert_a2_artifacts_writable` and `_assert_a3_python_version`
all append a command to the **profile image** with no `--entrypoint`
(`run_prepared_training.py:329-333`, `:353-360`, `:378-382`). Each would start
supervisord, block, and surface as `T1-timeout` after `_run`'s 300 s — a
misleading verdict for three assertions whose entire purpose is to name a true
cause. Only the bind probe is unaffected, because it uses `python:3.12-slim`.
I could not observe this directly: the driver stops at the bind probe, which runs
before A1. It follows from the same measured entrypoint behaviour.

---

## 6. B-2 — CONFIRMED by measurement, not inference

Section 7.4 rated B-2 "likely but not certain" for exactly one reason: the
`peft`/`transformers`/`unsloth` versions inside the committed image could not be
read. **They have now been read, and the behaviour has been measured.**

### The versions

```
$ docker.exe run --rm --network none --pull never \
    --entrypoint /opt/conda/bin/python3 <image@sha256:5266c57b…> -c "import importlib.metadata …"
peft 0.18.0
transformers 4.57.1
unsloth 2026.1.2
unsloth_zoo 2026.1.2
torch 2.9.0+cu128
trl 0.24.0
accelerate 1.12.0
```

(The `--entrypoint` override was needed for this read too — see B-4.)

### The assignment, read from the installed package

```
peft/mapping_func.py:64-66      # get_peft_model
    old_name = peft_config.base_model_name_or_path
    new_name = model.__dict__.get("name_or_path", None)
    peft_config.base_model_name_or_path = new_name
```

Unconditional. It overwrites whatever the config carried, from the model's
`name_or_path`. The save-time fallback at `peft/peft_model.py:347-352` only fires
when the value is still `None`.

### The measured value

Run offline in the committed image, reproducing the trainer's load-by-local-path
shape (`Trainers/sft/src/model_loader.py:208-228`, whose reason is documented at
`:176-179`) with a tiny locally-built model so no download is needed:

```
model.config._name_or_path : '/tmp/…/models--X--Y/snapshots/12fd25f77366fa6b3b4b768ec3050bf629380bac'
model.name_or_path         : '/tmp/…/models--X--Y/snapshots/12fd25f77366fa6b3b4b768ec3050bf629380bac'
name_or_path in __dict__?  : True

peft_type                  : 'LORA'
base_model_name_or_path    : '/tmp/…/models--X--Y/snapshots/12fd25f77366fa6b3b4b768ec3050bf629380bac'

verifier requires equality to: 'HuggingFaceTB/SmolLM2-135M-Instruct'
EQUAL?                      : False
```

`adapter_config.json` carries the **snapshot directory**, and
`tuner/runtime/verification.py:940-953` requires equality with the locked repo
id. The in-container twin raises first at
`Trainers/sft/runtime_v1.py:1803-1814`.

The smoke config makes this reachable: `training/smokes/docker-sft.json` sets
`lora_rank: 8` with four target modules, and `apply_lora_adapters` is called
unconditionally at `Trainers/sft/train_sft.py:1159`, so there is no workload on
this path that reaches a full fine-tune.

### Honest limits of this measurement

1. I drove **plain `transformers` + `peft`**, not unsloth's `FastLanguageModel`
   plus `apply_lora_adapters`. unsloth could in principle set `name_or_path`
   differently. It is constrained though: the trainer asserts
   `model.config._name_or_path` **is** the snapshot path
   (`model_loader.py:232-235`), and `mapping_func.py:65` reads
   `model.__dict__["name_or_path"]`, which I measured as present and equal to
   that path. Both routes lead to a path, never to the repo id.
2. I used a synthetic tiny Llama model, because the real SmolLM2 snapshot does
   not exist yet (B-3). The identifier plumbing under test does not depend on the
   weights.
3. Nothing rewrites the field afterwards: it has only readers across `Trainers/`
   and `_archive_artifact` streams files verbatim (section 7.1).

**This is a pin question for the user, and I am not proposing an answer.** The
options the evidence supports are: move the engine pin off `aec998ee`; change the
trainer to stamp the repo id; or accept that LoRA workloads cannot verify on this
path. Section 7.5 still holds — a B-2 stop would leave admission, staging, argv
equality, composition, container create/start and the durable record proven.

---

## 7. Durable state and cleanliness

The acceptance contract of section 10.2 is **not checkable**: no run was
submitted, so there is no `docker_run_mutations` row, no artifact record, no
publication row, and `.synaptic/state/training.sqlite3` was never created.

Per the lead's ruling, this is reported as **"no row written"**, which is its own
outcome and explicitly *not* "the phase did not advance".

```
$ find F:\Code\ehr-release-808e9f4d\.synaptic
.synaptic
.synaptic/model-inventory          (created empty by the script before it failed)

$ git.exe -c safe.directory='*' -C 'F:\Code\ehr-release-808e9f4d' status --porcelain
(no output, exit 0)

$ git.exe … check-ignore -v .synaptic scratch
.gitignore:97:.synaptic/	.synaptic
.gitignore:9:scratch/	scratch

$ git.exe … rev-parse HEAD          → 808e9f4df6c0af6f22b6c0028c95a4e20b86b251
$ git.exe … submodule status        →  aec998ee8d6a2e58d86e19e8132bc59aa21ebd53
```

Both directories I touched are gitignored, the tree is clean, HEAD and the
submodule pin are unmoved. One stray container from the entrypoint discovery was
killed; nothing else was left running.

---

## 8. Secondary read-only check (mission item 9) — AGREES

| Claim in the preparation doc | Code | Verdict |
|---|---|---|
| Empty name, `Length=0`, `RootDirectory` set → `STATUS_SUCCESS` (doc line 341) | `local_io_v1/windows.py:610-626`, `_reopen_by_handle`, docstring "The canonical NT form is an EMPTY ObjectName with `RootDirectory` set", and the call `_nt_open_relative(parent_handle, "", directory=True, …)` | **Agrees.** The code uses exactly the measured form, and refuses the literal `"."` alternative twice over |
| `ntpath.realpath` never emits a `\\?\` prefix (doc lines 356-360, 438) | `grep` for `realpath` and for an extended-length literal over `windows.py` returns **nothing** | **Agrees**, and more strongly than the probe required: the port never calls `realpath` and never writes the prefix, so it cannot introduce one |

No line disagrees. R-4's `IO_FAILED` discipline at `windows.py:188-198` is intact
and was not exercised, since no publication ran.

---

## 9. Assertion outcome table

| ID | Assertion | Outcome | Evidence |
|---|---|---|---|
| Import smoke | Host imports from the released checkout | **PASS** | §1.1 |
| Orientation | context, endpoint, nvidia runtime, image by digest, GPU | **PASS** (7/7) | §2 |
| P1 | exactly one `docker.exe` | **PASS** | §4 |
| P2 | npipe endpoint | **PASS** | §4 |
| P3 | drive-letter root | **PASS** | §4 |
| P5 | `drive_mount_root` present and well-formed | **PASS** | §4 |
| P6 | smoke config matches the committed blob | **PASS** | §4 |
| Inventory | materialize + `--verify-only` | **FAIL (B-3)** | §3 |
| B-1 bind probe | committed candidate | **FAIL** | §4 |
| B-1 bind probe | fallback candidate | **PASS** (probe only, not committed) | §4 |
| A1 | GPU in container | **NOT REACHED**; would fail as `T1-timeout` for the B-4 reason | §5 |
| A2 | `/artifacts` writable by `unsloth:runtimeusers` | **NOT REACHED**; same | §5 |
| A3 | container Python `== 3.11.14` | **NOT REACHED**; same | §5 |
| A4 | snapshot present and link-free | **NOT REACHED** (needs B-3) | §3 |
| Run loop | observe / verify / publish cuts | **NOT REACHED** | §7 |
| §10.2 | acceptance contract | **NOT CHECKABLE** — no durable row exists | §7 |
| §10.3 | M-8 submitted-consistency | **NOT REACHED** | §7 |
| §10.3 | `PUBLICATION_COMPOSITION_ABSENT` | **NOT ASSERTABLE HERE** by design (race-only) | design §10.3 |
| R-3 / R-4 | five-role emission, Windows publication | **NOT REACHED** | §7 |
| B-2 | LoRA adapter ref equality | **CONFIRMED** by measurement | §6 |
| Item 9 | `windows.py` vs measured probes | **AGREES** | §8 |

---

## 10. What remains unproven

Everything downstream of the container actually starting the trainer:

- A1, A2 and A3 have **never been observed**, on any image, in any form. My B-4
  claim about how they would fail is an inference from a measured entrypoint,
  not an observation of those three probes.
- Whether the toolkit accepts driver 610.88 against the image's
  `NVIDIA_REQUIRE_CUDA` bands (R3) — untested, and it is the next unknown after
  the three blockers.
- Whether `/artifacts` is writable by `unsloth:runtimeusers` over whichever bind
  candidate is ruled in (R4).
- Whether the image's Python is exactly `3.11.14` (R5). The profile asserts it;
  nothing has read it.
- The whole of section 10.2, plus stage reuse and replay idempotency.
- Whether the inventory materialises correctly once B-3 is fixed, and whether
  `copyfile` dereferences as intended (R6). The `--verify-only` path has never
  run against a real tree.
- Whether the fallback bind candidate is fast enough for model weights over 9p.

Ordering note for whoever resumes: B-3 and B-1' can be fixed in either order, but
**B-4 gates any conclusion drawn from a run**, because with B-4 open a run that
looks healthy for an hour proves nothing.
