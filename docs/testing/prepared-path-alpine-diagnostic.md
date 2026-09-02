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

---
---

# Run 2 — 2026-09-02, released checkout `48375bc3`

Second execution of the prepared path, from the clean released checkout
`F:\Code\ehr-release-48375bc3` at commit
`48375bc39f6880961f742babaf9d96da58ac60bb`, after B-3, B-1' and B-4 were fixed.
Same Windows host, same Docker Desktop Linux engine, same committed image
digest. B-2 was known-unfixed going in and was expected to fail at artifact
verification; that expectation was never reached, because the run stopped
earlier for a new reason.

## 11. Run 2 verdict by step

| # | Step | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Prerequisite 7 — `--entrypoint env` one-off probe | **GREEN** | printed exactly `ok` |
| 2 | Materialize model inventory | **GREEN** | 25 files, 1 969 841 187 bytes |
| 3 | Driver `--probe-only` | **GREEN** | P1–P6, B1-bind-probe, A1–A4 all pass |
| 4 | Real run via the driver | **RED** | cut 1, `RESOLUTION_UNAVAILABLE` |
| 5 | Section 10.2 durable-row contract | **NOT REACHED** | no row written — see 11.5 |
| 6 | This report section | done | — |

Overall: **RED**, on a new blocker (**B-6**) that is upstream of everything
Run 1 found. The three Run 1 blockers are all confirmed fixed.

### 11.1 The three Run 1 fixes are confirmed working

**B-4 (`--entrypoint`) — fixed.** The prerequisite 7 probe

```
docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine run --rm \
  --pull never --network none --entrypoint env <image@sha256:5266c57b…> \
  /opt/conda/bin/python3 -c "print('ok')"
```

printed exactly `ok`. In Run 1 the same shape without `--entrypoint` produced
supervisord starting jupyter, ollama and sshd, and the workload argv was
discarded. `env` is on the image's PATH, so the `/usr/bin/env` fallback was not
needed.

**B-3 (CRLF stdin) — fixed.** Inventory materialization completed against the
real tree, which it had never done before:

| Measurement | Value |
|---|---|
| Files | 25 |
| Total bytes | 1 969 841 187 |
| Fingerprint | `sha256:0e2a8df272426dd2fc804c6aa4886abf26b060b9dea7ed03aa068266eb58a2c6` |

`--verify-only` then re-ran clean and reported `A4-inventory-link-free`, so
risk **R6** is resolved: `copyfile` dereferenced the Hugging Face symlinks and
the resulting tree contains regular files only.

**B-1' (mount source) — fixed.** The driver rendered the mount source from the
committed profile (`wsl_distro=Ubuntu-22.04`, `drive_mount_root=/mnt`) as

```
\\wsl.localhost\Ubuntu-22.04\mnt\f\Code\ehr-release-48375bc3
```

and the bind probe listed 20 entries, first `AGENTS.md`. The Run 1 failure
(`stat /run/guest-services/distro-services/docker-desktop.sock: no such file or
directory`) did not recur.

### 11.2 First-ever observations of A1–A4

Section 10 of the design lists these as never-observed. All four ran, and all
four passed. This closes four open risks.

| Probe | Result | Risk closed |
|---|---|---|
| A1 GPU visible | `GPU 0: NVIDIA GeForce RTX 3090 (UUID: GPU-ac4398bb-fc15-d722-b39c-2790b4b5f9cc)` | **R3** — the toolkit accepts the host driver against the image's `NVIDIA_REQUIRE_CUDA` bands |
| A2 artifacts writable | `unsloth:runtimeusers` created and removed a file over the bind | **R4** |
| A3 Python version | `3.11.14`, exactly the value the committed profile asserts | **R5** |
| A4 inventory link-free | pass | **R6** |

### 11.3 The real run — B-6, a new blocker

The driver issued the committed 8-token command:

```
python.exe -m synaptic_host training run --provider docker \
  --config project://training/smokes/docker-sft.json --destination local-default
```

and cut 1 returned:

```
[cut 1] exit=4 status=unavailable run_id=None phase=None
FAILED L6-command-refused: the Host returned status=unavailable
    code=RESOLUTION_UNAVAILABLE on cut 1
```

No container was created. `docker ps` showed no synaptic container at any point.
The driver's trainer-log tail reported

```
none found: F:\Code\ehr-release-48375bc3\.synaptic\state\docker\stages does not exist
```

which is correct and not itself a defect: the stage directory is created during
activation, and the run never reached activation.

**Cause, established by instrumented re-issue.** The Host's result envelope
(`TrainingRunCommandResultV2.to_dict`) carries no detail field, and
`execute_docker_training_admission_v1` maps three different failures onto
`RESOLUTION_UNAVAILABLE` behind bare `except BaseException` handlers
(`synaptic_host/docker_training.py` at the `session.prove`, plan-compile, and
model-inventory sites). To tell them apart, a scratch harness re-issued the same
command with those call sites wrapped in memory so the traceback prints before
the handler swallows it. Nothing on disk was modified. The harness patches the
module through a `sys.meta_path` hook at import time rather than importing it
eagerly, because an eager import trips the engine-contract loader's `sys.modules`
cache invariant and yields `BOOTSTRAP_UNAVAILABLE` instead — a different code,
which would have misattributed the failure.

The instrumented cut reproduced `RESOLUTION_UNAVAILABLE` with the identical
envelope and printed:

```
### session.prove ...
### EXCEPTION raised inside session.prove ###
Traceback (most recent call last):
  File "…\synaptic_host\docker_training.py", line 242, in prove
    project_source = self._verified_remote_source(inspected.project_source)
  File "…\synaptic_host\docker_training.py", line 212, in _verified_remote_source
    raise ValueError("source lacks an exact upstream branch")
ValueError: source lacks an exact upstream branch
```

Line 242 is the **project** source, not the engine source.

**Why the branch is absent.** The released checkout is in detached HEAD:

```
$ git -C F:\Code\ehr-release-48375bc3 status -sb
## HEAD (no branch)
$ git -C F:\Code\ehr-release-48375bc3 branch -vv
* (HEAD detached at 48375bc3)      48375bc3 fix(docker_v1): pass --entrypoint env …
  feat/submodule-cloud-api-v1-host  48375bc3 [origin/feat/submodule-cloud-api-v1-host] …
```

`inspect_git_source` derives the branch as
`git branch --show-current … or None` (`synaptic-tuner/tuner/project/source_bundle.py`).
Under detached HEAD that command prints an empty string, so `branch` is `None`,
and `_verified_remote_source` rejects it before any remote read happens.

**The guard is intentional, and the checkout is one step short of satisfying it.**
The local branch `feat/submodule-cloud-api-v1-host` already exists at exactly the
checked-out commit and already tracks `origin/feat/submodule-cloud-api-v1-host`.
Both remote heads were read and both equal the locked commits, so the
`ls-remote` equality check the guard performs next would pass:

| Repository | Locked commit | `git ls-remote --refs` head | Equal |
|---|---|---|---|
| Epistemic-Humility-Research, `refs/heads/feat/submodule-cloud-api-v1-host` | `48375bc39f68…` | `48375bc39f68…` | yes |
| Synaptic-Tuner, `refs/heads/feat/submodule-cloud-api-v1` | `aec998ee8d6a…` | `aec998ee8d6a…` | yes |

So B-6 is not a Host code defect. The guard is doing exactly its job — refusing
to admit a run whose source is not identifiable as a pushed named branch. B-6 is
a **release-procedure and driver-precondition gap**: nothing in the recipe puts
the released checkout on its branch, and nothing in the preconditions detects
that it is not.

**An asymmetry worth recording.** The engine submodule is *also* in detached
HEAD, and that is tolerated, because `GitCliLocalSourceInspector.inspect` reads
the branch out of the committed `.gitmodules`
(`submodule."synaptic-tuner".branch = feat/submodule-cloud-api-v1`) and
substitutes it with `engine_source = replace(engine_source, branch=committed_branch)`.
The superproject has no equivalent fallback, and none is available to it —
there is no committed file that names the superproject's own branch. That is why
the failure lands on the project source and not the engine source, and it is why
the remedy has to be operational rather than a symmetric code fix.

**Recommended remedy** (not applied — see 11.6): put the released checkout on the
branch it already has, at the commit it is already on, and add a precondition
that fails loudly when it is not.

```
git -C F:\Code\ehr-release-48375bc3 checkout feat/submodule-cloud-api-v1-host
```

This moves `.git/HEAD` only. The branch points at the same commit, so no tracked
file changes and the working tree stays byte-identical. Reversible with
`git checkout --detach 48375bc3`.

The durable half of the remedy belongs in the run recipe: section 9.1 checks
P1–P6 and none of them looks at HEAD. A **P7** should assert that the project
checkout is on a branch, that the branch has `origin` as its upstream remote,
and that `git ls-remote` on that branch equals HEAD — the same three conditions
the Host is about to enforce, checked before a run is issued rather than
discovered as an opaque `RESOLUTION_UNAVAILABLE` at cut 1.

### 11.4 B-2 remains unverified, and version evidence was re-captured

The run stopped before the trainer started, so nothing was measured about
`adapter_config.json` in Run 2. Per the standing rule not to come back empty on
B-2, the in-image versions were re-captured from the committed image digest with
a read-only, `--network none`, no-bind, no-GPU container. They are unchanged
from Run 1:

| Package | Version |
|---|---|
| peft | 0.18.0 |
| transformers | 4.57.1 |
| unsloth | 2026.1.2 |
| unsloth_zoo | 2026.1.2 |
| torch | 2.9.0+cu128 |
| trl | 0.24.0 |
| accelerate | 1.12.0 |

The Run 1 finding therefore stands unchanged: `peft 0.18.0` assigns
`peft_config.base_model_name_or_path = model.__dict__.get("name_or_path", None)`
unconditionally, which stamps the snapshot path rather than the locked repo id.

### 11.5 Durable state — no row written

This is reported as its own outcome, not as "phase did not advance". There was
no phase to advance.

```
$ find F:\Code\ehr-release-48375bc3\.synaptic\state
No such file or directory
```

The state directory does not exist, so `training.sqlite3` does not exist, so
there is no `docker_run_mutations` table and no row in it. The section 10.2
durable-row contract and the `command_digest` check could not be evaluated and
remain unverified. The failure occurred during admission, before any durable
effect is written, which is the correct ordering: a run that cannot prove its
source must leave no trace.

### 11.6 Cleanliness and what was touched

- Nothing in the released checkout or the worktree was modified beyond this
  report and the gitignored `scratch/` tree. The detached HEAD was **not**
  corrected; that is the lead's call, because the released checkout is the
  evidence.
- No secrets were read, passed, or logged. No `HF_TOKEN` anywhere. Every
  container ran `--network none` except the A1 GPU probe, which takes no network
  either.
- One stray container from Run 1 (`quizzical_dijkstra`, the version-capture
  container that B-4's entrypoint hijack left running under supervisord) was
  removed with `docker rm -f`. Three unrelated pre-existing containers
  (`cc-test-pg`, `heuristic_lamarr`, `youthful_margulis`) were left alone.
- Scratch artifacts for this run are under
  `F:\Code\ehr-release-48375bc3\scratch\test-phase\` — `logs\03-real-run.log`,
  `logs\04-diagnose-resolution.log`, and the read-only harness
  `diagnose_resolution.py`.

## 12. What Run 2 changed about what is unproven

Resolved since Run 1: R3 (GPU visibility), R4 (artifact writability), R5 (image
Python version), R6 (inventory materialization and link-freedom), plus the B-3,
B-1' and B-4 fixes themselves.

Still unproven, and now blocked behind B-6:

- Everything downstream of admission. The container has still never been created
  by the prepared path, so the real bind of the stage directory, stage reuse and
  replay idempotency are all untested.
- The whole of section 10.2: the durable `docker_run_mutations` row contract,
  `command_digest`, and the observe/verify/publish cut sequence.
- B-2 end to end. It has been confirmed by measurement at the library level but
  never observed on a real SmolLM2 run driven through unsloth's
  `FastLanguageModel`.
- Whether the 9p bind is fast enough to move ~1.97 GB of model weights into the
  container within the run budget.

Ordering note for whoever resumes: **B-6 now gates everything**, in the same way
B-4 gated Run 1. It is cheap to clear — one `git checkout` plus a P7 precondition
— and until it is cleared no cut can produce information about anything else.

---
---

# Run 3 — 2026-09-02, released checkout `48375bc3`, now on its branch

Third execution, after the lead moved `F:\Code\ehr-release-48375bc3` onto
`feat/submodule-cloud-api-v1-host` to clear B-6. Same commit, same host, same
image digest.

**Verdict: RED on a new blocker, B-7.** B-6 is confirmed cleared. A second, weaker
finding (B-8) is recorded as an intermittent risk rather than a blocker. The
single most useful result is not the failure itself but what an effect-free probe
established behind it: **B-7 is the last known blocker before activation.**

## 13. Run 3 verdict by step

| # | Step | Verdict |
|---|------|---------|
| 0 | Verify the lead's four preconditions | **GREEN** |
| 4 | Real run through the driver | **RED** — cut 1, `RESOLUTION_UNAVAILABLE` |
| 5 | Section 10.2 durable-row contract | **NOT REACHED** — still no row |
| 6 | This report section | done |

### 13.1 B-6 is cleared, verified two ways

The four facts were checked before anything else, and all four hold:

| Fact | Measured |
|---|---|
| On a branch | `## feat/submodule-cloud-api-v1-host...origin/feat/submodule-cloud-api-v1-host` |
| Commit | `48375bc39f6880961f742babaf9d96da58ac60bb` |
| Upstream | `branch.….remote = origin`, `branch.….merge = refs/heads/feat/submodule-cloud-api-v1-host` |
| Clean tree, submodule | empty `--porcelain`, submodule ` aec998ee…` (no `+`) |

The stronger confirmation is behavioural. In Run 2 `prove` died at
`docker_training.py:212` on the branch check. In Run 3 it reaches
`docker_training.py:214`, the remote read on the next line. The guard that
blocked Run 2 now passes.

### 13.2 B-7 — the Host's scrubbed environment breaks all networking on Windows

The driver's cut 1 returned the same outward code as Run 2:

```
[cut 1] exit=4 status=unavailable run_id=None phase=None
FAILED L6-command-refused: … code=RESOLUTION_UNAVAILABLE on cut 1
```

Same code, different cause. The instrumented re-issue showed:

```
  docker_training.py:214 in _verified_remote_source -> self._reader.read_ref(…)
  security.py:861 in read_ref -> self._runner(("git","ls-remote","--refs",…))
  security.py:849 in _run -> subprocess.run(…)
  subprocess.CalledProcessError: … returned non-zero exit status 128
```

`check=True` discards the child's stderr, so the exit code alone says nothing.
Reproducing the exact call with the identical environment recovers it:

```
fatal: unable to access 'https://github.com/ProfSynapse/Epistemic-Humility-Research.git/':
getaddrinfo() thread failed to start
```

**Cause.** `ScopedGitRemoteReader._run` (`synaptic_host/security.py:836-848`)
replaces the child environment with a nine-key allowlist: `PATH`,
`GIT_TERMINAL_PROMPT`, `GCM_INTERACTIVE`, `GIT_CONFIG_NOSYSTEM`,
`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_OPTIONAL_LOCKS`, `LC_ALL`,
`LANG`. That list is POSIX-shaped. On Windows, Winsock cannot initialise without
`SystemRoot`, so `getaddrinfo` fails in the child and every remote Git operation
dies with exit 128.

**Single-variable isolation.** The same argv was run under the exact scrub and
under the scrub plus one variable at a time:

| Environment | Exit | Result |
|---|---|---|
| exact scrub, as the Host builds it | 128 | `getaddrinfo() thread failed to start` |
| scrub + `SystemRoot` | **0** | `48375bc39f68… refs/heads/feat/submodule-cloud-api-v1-host` |
| scrub + `TEMP` | 128 | same failure |
| scrub + `USERPROFILE` | 128 | same failure |
| scrub + `APPDATA` | 128 | same failure |
| scrub + `ProgramData` | 128 | same failure |
| scrub + all of the above | 0 | correct SHA |
| inherited environment (control) | 0 | correct SHA |

`SystemRoot` alone is necessary and sufficient. `git.exe` resolves fine from
`PATH` (`C:\Program Files\Git\cmd\git.exe`), so this is not a lookup failure.

**Severity.** There is no operator workaround. `subprocess.run(env=…)` replaces
the environment wholesale, the reader is constructed with no injected runner, and
no committed configuration reaches it. Both call sites are affected, since
`prove` verifies the project source and the engine source through the same
method. **In its current form the prepared path cannot complete admission on
Windows at all** — which is the platform this workstream exists to support. This
is a Host source defect and needs a code fix; it cannot be cleared from the
run recipe the way B-6 was.

**Suggested shape of the fix** (for the owner, not applied here): on Windows,
carry `SystemRoot` through into the allowlist. It names `C:\WINDOWS`, carries no
credential material, and does not re-admit ambient Git configuration, so the
scrub's security intent is preserved. `SystemDrive`, `windir`, `COMSPEC` and
`PATHEXT` are the usual companions and are worth considering in the same ruling.
The fix should be platform-conditioned so the POSIX lane keeps the tighter list.

A second, smaller point for the same owner: `check=True` throws away the child's
stderr, so a networking failure surfaces as a bare exit code that then collapses
into `RESOLUTION_UNAVAILABLE`. Capturing stderr into the raised error would have
turned this diagnosis into one line of log.

### 13.3 The useful result — B-7 is the last known blocker before activation

An **effect-free** probe answered the question the failure would otherwise leave
open. Two in-memory patches, applied lazily through the same `sys.meta_path`
hook: `ScopedGitRemoteReader._run` gains `SystemRoot`, simulating the B-7 fix,
and `_activate_docker_training_v1` raises immediately. Admission is therefore
exercised in full while no container is created and no durable state is written
— `docker_training` is effect-free up to activation, and this was confirmed
afterwards.

With B-7 simulated, the run reaches the deliberate activation stop:

```
### compile_training_plan_v1 OK
### resolve_docker_model_inventory_v1 OK
### ADMISSION COMPLETE — activation deliberately blocked, no container created,
    no durable state written
```

Reaching the inventory step proves `session.bind` and `session.verify_plan` both
passed, since both sit between the plan compile and that call in the same block.
So every admission stage — source proof, committed-blob checks, destination
policy, plan compilation, plan verification and model-inventory resolution —
passes once B-7 is cleared. **The plan compiled for the first time in this
workstream.** Fixing B-7 should therefore carry the run into activation, where
the expected B-2 failure at artifact verification finally becomes reachable.

This is a projection from a patched process, not an observation of the shipped
path, and should be read as such.

### 13.4 B-8 — an intermittent inventory failure, recorded as a risk not a blocker

On the **first** execution of that depth probe, admission failed one step earlier:

```
  docker_model_inventory.py:262 in resolve_docker_model_inventory_v1
  docker_model_inventory.py:185 in _inventory_snapshot
  ValueError: model snapshot changed during inventory
```

`_inventory_snapshot` records a `(st_dev, st_ino, st_mode, st_nlink, st_size,
st_mtime_ns, st_ctime_ns)` identity for every directory and file, hashes all 25
files, then re-stats everything and rejects the inventory if any identity moved.

It did not reproduce. Three subsequent executions of the identical path passed.
A standalone replication of the two-phase check reported **0 of 4 directory and
0 of 25 file mismatches**, hashing all 1.97 GB in 1.3 s against a warm cache.

**Honest limits.** I did not capture which path or which field moved, because the
failure never recurred while instrumented. The evidence is consistent with a
time-of-check/time-of-use window that widens with a cold read of 1.97 GB from the
F: drive — the first execution was the only cold one — but that mechanism is a
hypothesis, not a measurement. What is established is narrower and still worth
acting on: **this check can reject a valid, unmodified inventory**, it did so
once, and its failure probability scales with read time. It is a flake in the
admission path, and a run that trips it fails with the same opaque
`RESOLUTION_UNAVAILABLE` as everything else. Recommend the owner add the
offending path and field to the message so the next occurrence is self-diagnosing.

### 13.5 One instrument artifact, recorded so it is not mistaken for a finding

The first depth probe wrapped the admission session in a delegating proxy. It
failed before `compile_training_plan_v1` was ever called, which briefly looked
like a fourth blocker. It was not: `DockerAdmissionResolverV1.__post_init__`
enforces `type(self.session) is not _AdmissionSessionV1`, so the proxy was
rejected by an exact-type guard. Removing the proxy removed the failure. The
guard is correct and the harness was wrong.

### 13.6 Durable state — still no row

`F:\Code\ehr-release-48375bc3\.synaptic\state` still does not exist, so there is
no `training.sqlite3`, no `docker_run_mutations` table and no row. Section 10.2's
row contract and `command_digest` check remain unverified for a third run. The
effect-free probes wrote nothing, created no container, and left the tracked tree
clean, all confirmed after the fact.

### 13.7 Cleanliness

Nothing was modified in the released checkout or the worktree beyond this report
and the gitignored `scratch/` tree. No secrets were read, passed or logged; the
one network operation is an unauthenticated `ls-remote` against a public
repository. New scratch artifacts: `logs/05-run3.log`, `logs/06-diagnose-run3.log`,
`logs/07-admission-depth.log`, and the read-only probes
`probe_lsremote_env.py`, `probe_admission_depth.py`, `probe_inventory_toctou.py`.

## 14. What Run 3 changed about what is unproven

Newly established: B-6 is cleared; the plan compiles; every admission stage
passes once B-7 is simulated. Newly blocked: everything downstream of admission,
now behind B-7 rather than B-6.

Still unproven, unchanged from Run 2: container creation by the prepared path,
the stage bind, stage reuse and replay idempotency, the whole of section 10.2,
B-2 end to end on a real SmolLM2 run, and whether the 9p bind moves ~1.97 GB
inside the run budget.

Ordering note: **B-7 gates everything**, it needs a source fix rather than an
operator step, and it is the third platform-conditioned defect in this workstream
that only a real Windows host could surface — after B-3's CRLF stdin and B-4's
entrypoint hijack. B-8 should be fixed alongside it but does not gate a run
attempt.

---
---

# Run 4 — 2026-09-02, released checkout `428496ae`, engine `4a01fc55`

Fourth execution, from the new released checkout
`F:\Code\ehr-release-428496ae` at commit `428496aeb265…` on
`feat/submodule-cloud-api-v1-host`, submodule `synaptic-tuner` at `4a01fc55`.
Both trees clean. This is the first run in which B-7 is fixed in the shipped
source rather than simulated, and the first that could have reached activation.

**Verdict: RED on a new blocker, B-9,** raised by assertion **A2** during
`--probe-only`, before any training container was created. B-7 is not reached
and therefore neither confirmed nor refuted by this run. Every step ahead of A2
is GREEN, including the first-ever green **P7**.

## 15. Run 4 verdict by step

| # | Step | Verdict | Evidence |
|---|------|---------|----------|
| 0 | Released-checkout preconditions | **GREEN** | HEAD `428496ae…`, branch + upstream `origin`, submodule `4a01fc55…`, both `--porcelain` empty (0 bytes) |
| 1 | Prerequisite 7 — `--entrypoint env` probe | **GREEN** | printed exactly `ok`; image present at the locked digest |
| 2 | Model inventory in the new checkout | **GREEN** | copy route; 25 files, 1 969 841 187 bytes, fingerprint matches |
| 3 | Driver `--probe-only` | **RED** | P1–P7 + bind probe + A1 pass; **A2 fails** |
| 4 | Real run via the driver | **NOT REACHED** | not issued — A2 is the gate |
| 5 | Section 10.2 durable-row contract | **NOT REACHED** | `.synaptic\state` still does not exist |
| 6 | This report section | done | — |

### 15.1 Docker Desktop was down and was started

The Linux engine pipe was absent at first contact
(`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file
specified`) and `tasklist` showed zero Docker processes: the host had restarted
since run 3. Docker Desktop was started and the engine was ready within 10 s
(`Server 29.3.1 / OS linux`). This is recorded because it is the same restart
that produced B-9, not because it is a defect.

### 15.2 The inventory was copied, then verified — route recorded

Per the lead's ruling, the 25 files were copied from
`F:\Code\ehr-release-48375bc3` with `shutil.copyfile` per file (never a
link-preserving copy) by the gitignored operator script
`scratch\test-phase\copy_inventory.py`, then verified through the skill.

| Measurement | Value |
|---|---|
| Files | 25 |
| Total bytes | 1 969 841 187 |
| Source symlinks flattened | 0 |
| Destination non-regular entries | 0 |
| Fingerprint | `sha256:0e2a8df272426dd2fc804c6aa4886abf26b060b9dea7ed03aa068266eb58a2c6` |

`--verify-only` reported `OK 25 file(s), 1969841187 byte(s)` and the expected
fingerprint, so the copy route is sound and the inventory contract at `428496ae`
is unchanged from `48375bc3`.

### 15.3 P7 passes for the first time on a run that was not hand-corrected

The released checkout was cloned onto its branch rather than moved onto it after
the fact, so P7 passed on first contact and printed the full triple:

```
$ git.exe -C F:\Code\ehr-release-428496ae rev-parse HEAD
$ git.exe -C F:\Code\ehr-release-428496ae branch --show-current
$ git.exe -C F:\Code\ehr-release-428496ae config --local --get branch.feat/submodule-cloud-api-v1-host.remote
$ git.exe -C F:\Code\ehr-release-428496ae ls-remote origin refs/heads/feat/submodule-cloud-api-v1-host
    PASS P7-branch-publishable: feat/submodule-cloud-api-v1-host tracks origin at 428496aeb265
```

P7 also reached the network and returned, which is the first evidence in this
workstream of a successful `ls-remote` from the run recipe. It does **not**
exercise B-7: P7 runs `git.exe` from the driver with an inherited environment,
whereas B-7 is about the Host's own scrubbed environment inside
`ScopedGitRemoteReader`. Only admission exercises that, and admission was never
reached.

### 15.4 B-9 — the container user cannot write `/artifacts` over the bind

```
    PASS A1-gpu-visible: GPU 0: NVIDIA GeForce RTX 3090 (UUID: GPU-ac4398bb-…)

FAILED A2-artifacts-writable: unsloth:runtimeusers could not write /artifacts
  over \\wsl.localhost\Ubuntu-22.04\mnt\f\Code\ehr-release-428496ae\scratch\test-phase\a2-artifact-probe:
  touch: cannot touch '/artifacts/.a2probe': Permission denied
```

**This is not an artifact of the new checkout or of the copy.** The identical
probe was run against the *old* checkout's probe directory, which passed in
run 2, and it now fails the same way. That is the control.

**Cause, established by measurement.** Ubuntu-22.04 carries a persistent
automount policy:

```
$ cat /etc/wsl.conf
[automount]
options = "metadata,umask=22,fmask=11"

$ awk '$2=="/mnt/f"{print $4}' /proc/mounts
rw,noatime,aname=drvfs;path=F:\;uid=1000;gid=1000;metadata;umask=22;fmask=11;…
```

With `metadata`, DrvFs honours stored POSIX modes instead of reporting
everything world-writable. Every path under `/mnt/f` therefore presents as mode
`755`, owner `uid=1000`. The container runs as `uid=1001`, so it has only
`r-x` and cannot create the artifact tree.

The container user is not a driver choice. The prepared composition passes **no
`--user`** at all (`synaptic_host/docker_v1/control_private.py:394-413`), so the
container runs as the image's own `User`, and it binds `/artifacts` read-write
over the same UNC:

```
image inspect → User=unsloth:runtimeusers
"--mount", f"type=bind,source={…artifact_path.unc_path},destination=/artifacts"
```

**Single-variable isolation.** Same image, same bind shape, same default user;
only the host-side mode differs.

| Host-side directory mode | Container `id` | Result |
|---|---|---|
| `755` (uid 1000) | `uid=1001(unsloth) gid=102(runtimeusers)` | `Permission denied` |
| `777` (uid 1000) | same | `WRITABLE` |

Creator does not matter: a directory made by WSL `mkdir` and one made by Windows
Host Python both present as `755`, because the mode comes from the mount policy.

**Why runs 1–3 did not see it.** `/etc/wsl.conf` is dated 2026-03-11, so the
policy is not new, but automount options are applied at **distro boot**. Run 3's
scratch artifacts are timestamped 09:06–09:12 local; the Ubuntu-22.04 distro's
current boot is 11:14 local. Runs 1–3 therefore ran under a different distro
boot. That the earlier boot mounted `/mnt/f` without `metadata` is the inference
that fits A2's flip from PASS to FAIL; the earlier mount itself was not observed
and cannot now be.

**Severity and shape.** A2 is doing exactly its job — the assertion exists so a
non-writable `/artifacts` fails early and by name instead of late and disguised.
The real run would bind the Host-created stage directory under
`F:\Code\ehr-release-428496ae\.synaptic\state\docker\stages\…`, on the same
drive under the same policy, so the trainer would fail at artifact assembly. The
run was not issued.

B-9 is **not** a Host source defect in the way B-7 was, and it is **not** a
recipe gap of the B-6 kind that an operator step inside the checkout can clear.
It is an undeclared **environment precondition**: the prepared path requires that
the pinned WSL distro expose the project drive in a way the container's non-root
user can write. Nothing in the committed profile, the preconditions, or the skill
states that, and nothing detects it before A2.

**Candidate remedies, for the owner to rule on — none applied.**

1. **Host-wide, restores the runs 1–3 environment.** Drop `metadata` (or set
   `umask=000,fmask=000`) in `/etc/wsl.conf` `[automount]` and `wsl --shutdown`.
   Cheapest, but it changes file semantics for every project on this machine and
   is outside the released checkout, so it is the lead's call, not the runner's.
2. **Profile.** Point `docker_host.wsl_distro` at a distro whose `/mnt/f` mount
   the container can write. Only `docker-desktop` is also installed and it is
   already refuted for mount resolution (run 2, section 4). Takes effect only
   once committed and a new released checkout is built.
3. **Composition.** Have the prepared composition pass `--user` matching the host
   owner, or have the Host create the stage directory group- or world-writable.
   This is a design change to a committed surface and belongs to `architect-run`.

Recommend also adding a **P8** precondition that binds a throwaway directory and
writes to it as the image's own user, so this fails by name in the precondition
block rather than at A2 — the same hardening P7 gave B-6.

### 15.5 B-8 did not fire, and could not have

The `docker_model_inventory.py:185` stat-identity re-check is exercised during
`resolve_docker_model_inventory_v1`, inside admission. Run 4 stopped in the
driver's assertion block, before any Host command was issued, so admission never
ran. **B-8 neither fired nor was tested.** It remains an open intermittent risk
carried forward from run 3, unchanged.

### 15.6 Durable state — still no row, for the fourth run

`F:\Code\ehr-release-428496ae\.synaptic\state` does not exist, so there is no
`training.sqlite3`, no `docker_run_mutations` table and no row. Section 10.2's
row contract and the `command_digest` check remain unverified. This run stopped
even earlier than the previous three: no Host command was issued at all.

### 15.7 Cleanliness

- Nothing was modified in either released checkout or in the worktree beyond
  this report and the gitignored `scratch/` trees.
- Both released checkouts remain clean: `git status --porcelain` is 0 bytes for
  the superproject and for the submodule.
- No secrets were read, passed or logged. Every container ran `--network none`
  except the A1 GPU probe, which takes no network. No `HF_TOKEN` anywhere.
- Two pre-existing exited containers (`eh-grpocold-…-eval-…`,
  `eh-grpocold-…-train-…`) were left alone. No container was created by this run
  other than the short-lived probes, all `--rm`.
- New scratch artifacts under
  `F:\Code\ehr-release-428496ae\scratch\test-phase\`: `copy_inventory.py`,
  `perm-experiment\` (the B-9 isolation), and `logs\08-run4-prereq7.log`,
  `logs\09-run4-inventory-copy.log`, `logs\10-run4-inventory-verify.log`,
  `logs\11-run4-probe-only.log`. Logs `01`–`07` in that directory are carried
  over from runs 1–3 by the scaffolding copy and are **not** run-4 evidence.

## 16. What Run 4 changed about what is unproven

Newly established: the copy-plus-verify inventory route is sound at `428496ae`;
P7 passes on a checkout that was cloned correctly rather than corrected;
A1 and the mount-source bind still pass after a host restart.

Newly blocked: everything from admission onward, now behind **B-9** rather than
B-7. B-7's fix is untested on the shipped path — run 4 stopped before admission,
so the SystemRoot fix has still never executed for real.

Still unproven, unchanged from run 3: container creation by the prepared path,
the stage bind, stage reuse and replay idempotency, the whole of section 10.2,
B-2 end to end on a real SmolLM2 run, the B-5 argv equality against the
regenerated closure manifest, and whether the 9p bind moves ~1.97 GB inside the
run budget.

Ordering note: **B-9 gates everything**, and it is the fourth
platform-conditioned defect this workstream has surfaced that only a real
Windows host could produce — after B-3's CRLF stdin, B-4's entrypoint hijack and
B-7's POSIX-shaped environment scrub. Unlike those three it is not in the source
at all; it is a property of the host the prepared path never declared it needed.

## 17. Run 5 verdict by step

Run 5, 2026-09-02, from the released checkout `F:\Code\ehr-release-ab741054`
(branch `feat/submodule-cloud-api-v1-host` at `ab741054…`, submodule
`synaptic-tuner` at `ba844137…`). B-9, B-9-R1 and B-10 are shipped; B-10-R1 was
to be measured at cut 2.

| # | Step | Verdict | Evidence |
|---|------|---------|----------|
| 0 | Released-checkout preconditions | **GREEN** | HEAD `ab74105454ea…`, branch tracks `origin`, `ls-remote` equals HEAD, `--porcelain` empty (0 bytes), submodule `ba844137…` |
| 1 | Prerequisite 7 — `--entrypoint env` probe | **GREEN** | printed exactly `ok`; image present at the locked digest |
| 2 | Prerequisite 9 — mount identity | **GREEN** | `/proc/mounts` for `/mnt/f` still `uid=1000,gid=1000,metadata,umask=22,fmask=11`; host unmodified |
| 3 | Model inventory in the new checkout | **GREEN** | copy route; 25 files, 1 969 841 187 bytes, fingerprint `sha256:0e2a8df2…` |
| 4 | Driver `--probe-only` | **GREEN** | P1–P8, bind probe and A1–A4 all pass; **A2 passes**, the assertion that stopped run 4 |
| 5 | Real run, cut 1 | **RED** | `START_UNAVAILABLE`, exit 4; no stage, no container, no durable row |
| 6 | Cuts 2+ | **NOT REACHED** | the run never left cut 1 |
| 7 | Section 10.2 durable-row contract | **NOT REACHED** | `.synaptic\state\training.sqlite3` was never created |
| 8 | This report section | done | — |

**Verdict: RED at activation, on a new blocker, B-11.** B-9 is fixed as far as
every probe can see. Admission passed for the first time in this workstream.
Activation then failed before any container existed.

### 17.1 What went right, and it is most of the ladder

Run 4 died at A2 because the container user could not write `/artifacts`. Run 5
passes A2 with the same bind and the same image, now with `--user 1000:1000`
from the committed profile:

```
p8| uid=1000 gid=1000 groups=1000
p8| WRITABLE
p8| HOME=/ home-not-writable
WARN P8-home: HOME is not writable for this user. EXPECTED on this host and NOT a failure
PASS P8-stage-writable-as-container-user: 1000:1000 wrote and removed a file under the real stage parent
PASS A2-artifacts-writable: 1000:1000 wrote and removed a file
```

`WARN P8-home` fired exactly as prerequisite 9 says it would, and is not a
fault. A1 saw the GPU (`NVIDIA GeForce RTX 3090`), A3 matched the profile at
full patch level (`3.11.14`), A4 re-verified the inventory fingerprint.

Admission also passed for the first time: the run reached
`_activate_docker_training_v1`, which means the source proof, the plan compile,
the plan verify and the model-inventory resolution all succeeded. **B-7's
SystemRoot fix has therefore now executed for real**, and so has P7 against a
published branch.

### 17.2 The failure, and the one line that names it

Cut 1, verbatim, with the B10-EVIDENCE pair:

```
[cut 1] entering with phase=None
B10-EVIDENCE cut=1 stage=NONE state_nonempty=unknown artifacts_nonempty=unknown tmp_nonempty=unknown tracking_nonempty=unknown
B10-EVIDENCE cut=1 result=START_UNAVAILABLE status=unavailable exit=4
[cut 1] exit=4 status=unavailable run_id=None phase=None
```

The command result carries no message:

```
{"code":"START_UNAVAILABLE","input_digest":"a74e16532990cb90050403fbcbbab2d6da57df05167d91085b5f55c15c838589","plan_fingerprint":null,"run_id":null,"status":"unavailable",…}
```

`synaptic_host/docker_training.py:694-696` wraps activation in a bare
`except BaseException: return fail(START_UNAVAILABLE)`, so the cause never
reaches stdout. It was recovered by wrapping
`_activate_docker_training_v1` from a `sys.meta_path` loader hook in a
gitignored operator probe — no file under `synaptic_host` was modified, and the
probe reproduced the identical `input_digest` and code, so the harness is
faithful:

```
File "…\synaptic_host\docker_training.py", line 809, in _activate_docker_training_v1
    authenticator = FileHmacAuthenticator.for_docker(
File "…\synaptic_host\security.py", line 534, in for_docker
    value._ensure_private_storage_directories()
File "…\synaptic_host\security.py", line 606, in _ensure_private_storage_directories
    self._validate_private_directory(directory)
File "…\synaptic_host\security.py", line 583, in _validate_private_directory
    raise _private_storage_error() from None
ValueError: HMAC private storage validation failed
```

A second probe wrapped `_private_storage_error` to print its raising frame and
`_validate_private_directory` to print its path:

```
probe: validating F:\Code\ehr-release-ab741054\.synaptic
probe: ntfs ok F:\Code\ehr-release-ab741054\.synaptic
probe: _private_storage_error raised at …\synaptic_host\security.py:373 in _win_validate_acl
probe: FAILED on F:\Code\ehr-release-ab741054\.synaptic
```

### 17.3 B-11 — the HMAC private storage root is created by the operator, with an inherited ACL

`FileHmacAuthenticator.for_docker` (`security.py:524-534`) sets the private
storage root to `<project_root>\.synaptic` and validates the whole chain
`.synaptic` → `.synaptic\state` → `.synaptic\state\docker`
(`security.py:585-606`). On Windows each must satisfy `_win_validate_acl`
(`security.py:349-402`):

- the DACL must be **protected** (`_SE_DACL_PROTECTED`), and
- the owner must be the current user, and
- there must be **exactly two** ACEs, neither inherited, each
  `FILE_ALL_ACCESS`, for the current user and `S-1-5-18`.

That is precisely what `_win_create_private_directory` (`security.py:286-295`)
produces, via the SDDL `O:<sid>G:<sid>D:P(A;;FA;;;SY)(A;;FA;;;<sid>)`.

But `_ensure_private_storage_directories` **only creates directories that do not
exist**; it never repairs one that does. And on this path the operator is
required to create `.synaptic` first:

| Creator | Path | Line |
|---|---|---|
| `materialize_model_inventory.py` (prerequisite 3) | `<root>\.synaptic\model-inventory\…` | `dest.mkdir(parents=True, exist_ok=True)` at `:177` |
| `run_prepared_training.py` P8, added for B-9 | `<root>\.synaptic\state\docker\stages` | stage-parent creation, `--probe-only` included |

Both use `pathlib.Path.mkdir`, which inherits the parent ACL. Measured on the
failing directory:

| Property | Value |
|---|---|
| Owner | `DESKTOP-2A4U5KR\Joseph` (correct — the owner test passes) |
| `AreAccessRulesProtected` | **False** |
| ACE count | 11, **every one inherited** (`Administrators`, `SYSTEM`, `Authenticated Users`, `Users`, `CodexSandboxUsers`, …) |

The Host validator refuses all three chain directories:

```
F:\Code\ehr-release-ab741054\.synaptic:               REFUSED
F:\Code\ehr-release-ab741054\.synaptic\state:         REFUSED
F:\Code\ehr-release-ab741054\.synaptic\state\docker:  REFUSED
```

**This is not caused by the copy shortcut.** The control is
`F:\Code\ehr-release-48375bc3\.synaptic`, created in run 2 by the documented
`materialize_model_inventory.py` under Windows Host Python: it carries the
identical inherited-ACL shape. The documented sequence produces the defect.

**Mechanism, isolated to one variable.** Two throwaway directories in the same
parent, same volume, same user, differing only in creator, judged by the Host's
own validator:

```
A pathlib.Path.mkdir:    REFUSED  (HMAC private storage validation failed)
B host private creator:  ACCEPTED
```

`B`'s ACL is exactly `NT AUTHORITY\SYSTEM:(F)` and `DESKTOP-2A4U5KR\Joseph:(F)`,
non-inherited. Location, volume, NTFS and user are all eliminated; the creator
is the whole difference.

**The remedy direction is viable on this host.** A protected owner-only
directory is still fully usable by the rest of the path: WSL sees it as
`drwxr-xr-x profsynapse:profsynapse` and can write it, and the container reads a
file inside it over the `wsl.localhost` bind as `uid=1000`. Locking `.synaptic`
down does not break the inventory bind. The remedy itself is architect-run's
call; candidates are (i) the Host repairs or protects a chain directory it
already owns, (ii) the private storage root moves below a directory the operator
never creates, or (iii) the skill creates `.synaptic` privately before
prerequisite 3 — but (iii) leaves P8 creating `state` and `state\docker` the
wrong way, so it is not sufficient alone.

### 17.4 The three measurements this run was to record

All three are **unmeasured**, because the run never reached cut 2 and no
container was created. Reporting them as anything else would close blockers on
assumption.

**(a) B-10.** Only cut 1 exists, and its pair is quoted verbatim in 17.2 above.
`stage=NONE` with `unknown` flags is the documented normal reading before
staging. **The 19.14 table cannot be applied at all**: there is no cut 2, so
this is neither the confirmed row nor the deferral row. B-10 remains latent and
untested on the shipped path.

**(b) B-10-R1.** No stage directory was ever created, so there is no
`<stage>\artifacts\cache` to list, at cut 2 or at the end. Nothing was written
under a cache root because activation stopped before staging. B-10-R1 stays
unproven-as-active, on no evidence from this run.

**(c) B-9-R1.** No training container was created, so `/tmp/torch`,
`/tmp/triton`, `/tmp/xdg` and `/tmp/home` were never populated and there is
nothing to `docker exec` into. The container is not "gone"; it never existed.
The only HOME evidence this run produced is the P8 probe's `HOME=/
home-not-writable`, which is the pre-existing measurement from task #131 and not
the trainer's own output that B-9-R1 needs.

### 17.5 B-8 note

`docker_model_inventory.py`'s stat-identity re-check **did not fire**. The run
reached `_activate_docker_training_v1`, which is downstream of
`resolve_docker_model_inventory_v1` and of both `RESOLUTION_UNAVAILABLE` gates
(`docker_training.py:679-686`), so inventory resolution completed cleanly over
the 1.97 GB tree on the 9p mount.

### 17.6 State preserved

Nothing was cleaned. There is no container to preserve — none was created. There
is no stage: `.synaptic\state\docker\stages` is empty. There is no durable row:
`.synaptic\state\training.sqlite3` does not exist. The `.synaptic` tree is left
with the ACLs it failed on; **no ACL was modified**, so the blocker is
reproducible as it stands.

### 17.7 What Run 5 changed about what is unproven

Newly proven: `--user 1000:1000` from the committed profile makes the stage
parent and `/artifacts` writable for the container user (B-9's fix works at the
probe layer); admission end to end, which had never passed before, so B-7's
SystemRoot fix and P7 have now executed for real; and the inventory contract
over 1.97 GB on the 9p mount.

Newly blocked: activation, and therefore everything after it, now behind
**B-11**. B-9's driver change (P8) is a contributing cause, not a bystander: it
creates two of the three refused chain directories, and it does so on a
`--probe-only` pass.

Still unproven, unchanged: container creation by the prepared path, the stage
bind, stage reuse and replay idempotency, the whole of section 10.2, B-2 end to
end, the B-5 argv equality against the regenerated closure, B-10, B-10-R1 and
B-9-R1.

Ordering note: B-11 is the **fifth** platform-conditioned defect this workstream
has surfaced that only a real Windows host could produce, after B-3's CRLF
stdin, B-4's entrypoint hijack, B-7's POSIX-shaped environment scrub and B-9's
DrvFs mount identity. Like B-9 it is a collision between a POSIX-shaped
assumption and a Windows security primitive; unlike B-9 it is in the source, and
the source and the operator recipe disagree about who owns `.synaptic`.
