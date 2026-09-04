# B-16 spike: the unsloth import failure in the pinned trainer image

Blocker B-16 (task #256), feature #73, TEST phase #77, imPACT cycle 11, user ruling A
(spike first). Read-only toward the project: this document proposes nothing and changes
no source, composition or pin. The architect rules after it.

Prepared by `preparer-b16`, 2026-09-04. All measurements were taken on the Windows
Docker Desktop host with probe containers only (`--rm`, `probe-b16-` name prefix).
Container census read four before and four after, identical IDs. No image was pulled.

---

## 1. Executive summary

**B-16 is not an image defect and not a version mismatch. It is a consequence of the
B-9 fix.** The pinned image imports `unsloth` cleanly. It fails only when the container
runs as a uid that has no `/etc/passwd` entry, which is exactly what B-9 introduced when
it began emitting `--user 1000:1000`.

The image's own user is `unsloth`, **uid 1001**, gid 102. **uid 1000 does not exist in
this image.** Under an unresolvable uid, `getpass.getuser()` raises, an unsloth
`try: ... except: pass` block swallows a half-executed `torch._inductor.codecache`
import, and the module's registration side effect survives while the module itself is
evicted from `sys.modules`. The next import of that module re-executes it and trips the
duplicate-registration assert. The traceback the team has been reading is the *second*
registration; the first one is invisible because unsloth prints a one-line message and
continues.

Four remedies make the exact failing import succeed in the pinned image. The two that
matter are a single environment variable (`USER`, or any of `LOGNAME` / `LNAME` /
`USERNAME`), and changing the container uid to one the image actually defines. Both are
small. They differ in which repository they touch and which prior acceptance evidence
they disturb, which is the real decision for the architect.

**Swapping the image does not fix this.** `unsloth/unsloth:latest` appears to work only
because it happens to ship an `ubuntu:x:1000:1000` passwd line. Run it under any other
unmapped uid and it fails identically, on newer torch, with a newer library set. That is
a coincidence, not a remedy, and it would break again the moment `container_user` moved.

---

## 2. Reproduction

### 2.1 The equality target

Run 10's traceback, from `10-driver.log` in the released checkout
(`F:\Code\ehr-release-f0278a52\scratch\test-phase\logs`), reproduced through
`trainer.stderr.log`. Note that `docker logs ad2a2e607028` carries only the string
`SFT_RUNTIME_V1_REJECTED`; the traceback is in the artifact log, not in the container
log. The two frames that identify the failure:

```
File ".../unsloth_zoo/temporary_patches/utils.py", line 107, in <module>
    from transformers.processing_utils import Unpack
    ...
File ".../torch/compiler/_cache.py", line 75, in register
    assert artifact_cls.type() not in cls._artifact_types, (
AssertionError: Artifact of type=inductor already registered in mega-cache artifact factory

During handling of the above exception, another exception occurred:
    ...
File ".../unsloth_zoo/temporary_patches/utils.py", line 128, in <module>
    raise Exception(e)
Exception: Artifact of type=inductor already registered in mega-cache artifact factory
```

### 2.2 The minimal reproduction command

```
docker.exe run --rm --network none --name probe-b16-8 --gpus all \
  --user 1000:1000 \
  --entrypoint /opt/conda/bin/python3 \
  unsloth/unsloth@sha256:5266c57be21059bfb407d80dc2f448868a5c2e2dbe7b2aa27780f48b48cbec39 \
  -c "from unsloth import is_bfloat16_supported"
```

Exit 1, and both frames above appear verbatim. `--user 1000:1000` is the entire trigger.
Nothing else from run 10 is needed: no mounts, no staged closure, no `SYNAPTIC_*` roots,
no cache redirection.

Docker is at the absolute path `/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe`.

### 2.3 What each check enumerated, and how it could have failed

The first probe ran the pinned image with **no** overrides and **succeeded** (exit 0).
That is the finding that reframed the blocker, and it is why the environment was
bisected rather than the library versions.

| Probe | Condition | Exit | B-16? |
|---|---|---|---|
| 1 | pinned image, `--gpus all`, no overrides | 0 | no |
| 2 | pinned image, **no** `--gpus` | 1 | no — different failure |
| 3 | pinned image, `--gpus all`, full run-10 environment + `--user 1000:1000` | 1 | **yes** |
| 4 | group A: `--user 1000:1000` + `HOME` + scrubbed `PATH` | 1 | **yes** |
| 5 | group B: the five cache keys alone | 0 | no |
| 6 | group C: `PYTHONNOUSERSITE` + `PYTHONSAFEPATH` alone | 0 | no |
| 7 | group D: the four offline flags alone | 0 | no |
| 8 | `--user 1000:1000` **alone** | 1 | **yes** |
| 9 | `HOME=/tmp/home` alone | 0 | no |
| 10 | scrubbed `PATH` alone | 0 | no |

The group bisection could have failed by finding two interacting keys, or none. It found
exactly one, and probe 8 isolated it to a single flag. Probe 2 is recorded because it is
a *different* failure and must not be mistaken for this one: with no GPU the import dies
earlier and cleanly at `unsloth_zoo/device_type.py:46`,
`NotImplementedError: Unsloth cannot find any torch accelerator? You need a GPU.` The
B-16 assert never appears. **B-16 is therefore not GPU-independent in the practical
sense**: a GPU must be attached for the import to get far enough to fail this way. Every
remedy below was tested with `--gpus all` so the comparison is like for like.

---

## 3. The exact mismatch

### 3.1 Versions in the pinned image

Image `unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update`, digest
`sha256:5266c57be21059bfb407d80dc2f448868a5c2e2dbe7b2aa27780f48b48cbec39`,
Python 3.11 at `/opt/conda`.

| Package | Version |
|---|---|
| torch | 2.9.0+cu128 |
| torchao | 0.14.0 |
| unsloth | 2026.1.2 |
| unsloth_zoo | 2026.1.2 |
| transformers | 4.57.1 |
| triton | 3.5.0 |
| trl | 0.24.0 |
| peft | 0.18.0 |

Image identity: `/etc/passwd` defines `unsloth:x:1001:1001`, `/etc/group` defines
`runtimeusers:x:102`, and the image default is `uid=1001(unsloth) gid=102(runtimeusers)`.
**There is no uid 1000.**

### 3.2 What the assert guards

`torch/compiler/_cache.py:71-80` is a process-global registry keyed by artifact type
name:

```python
_artifact_types: dict[str, type[CacheArtifact]] = {}

@classmethod
def register(cls, artifact_cls: type[CacheArtifact]) -> type[CacheArtifact]:
    artifact_type_key = artifact_cls.type()
    assert artifact_cls.type() not in cls._artifact_types, (
        f"Artifact of type={artifact_type_key} already registered in mega-cache artifact factory"
    )
```

It guards against a type name being registered twice. Under normal single-import
semantics this cannot happen, because the registering module executes once.

### 3.3 Who registers first, who registers second

This is the load-bearing question, and it was answered by direct measurement rather than
inference. Probe 13 ran, as uid 1000, the import that unsloth performs, with the
exception printed instead of swallowed, and then inspected the registry:

```
File ".../torch/_inductor/async_compile.py", line 28, in <module>
    from torch._inductor.codecache import (
File ".../torch/_inductor/codecache.py", line 2560, in <module>
    _HEADER_DIR = os.path.join(default_cache_dir(), "precompiled_headers")
File ".../torch/_inductor/runtime/cache_dir_utils.py", line 23, in default_cache_dir
    sanitized_username = re.sub(r'[\\/:*?"<>|]', "_", getpass.getuser())
File "/opt/conda/lib/python3.11/getpass.py", line 169, in getuser
    return pwd.getpwuid(os.getuid())[0]
KeyError: 'getpwuid(): uid not found: 1000'

codecache in sys.modules: False
registered types: ['autotune', 'inductor', 'pgo']
```

Those last two lines are the proof. After the failed import, `'inductor'` **is** in the
registry and `torch._inductor.codecache` **is not** in `sys.modules`. The registration
survived; the module did not.

The full sequence:

1. **First registrant — unsloth itself.** `unsloth_zoo/temporary_patches/common.py:74`
   (identical code at `unsloth_zoo/compiler.py:2210`) runs:

   ```python
   try:
       import torch._inductor.async_compile
       from torch.hub import tqdm
       ...
   except:
       print("Unsloth: Failed editing tqdm to replace Inductor Compilation:")
   ```

   A bare `except:`. That import executes `torch/_inductor/codecache.py`, which at
   **line 1121** runs `@CacheArtifactFactory.register` on `InductorCacheArtifact` and
   registers `'inductor'` successfully.

2. **The half-import.** Execution of the same module continues to **line 2560**,
   `_HEADER_DIR = os.path.join(default_cache_dir(), ...)`, which calls
   `getpass.getuser()`, which calls `pwd.getpwuid(1000)`, which raises `KeyError`
   because uid 1000 is not in this image's passwd database. `codecache` therefore
   raises, and Python removes the partially-initialized module from `sys.modules`. The
   entry it wrote into the process-global `CacheArtifactFactory._artifact_types` is not
   rolled back.

3. **The swallow.** unsloth's bare `except:` catches the `KeyError`, prints
   `Unsloth: Failed editing tqdm to replace Inductor Compilation:` on stdout, and
   continues. This single line is the only visible symptom of the real cause, and it
   appears in run 10's log.

4. **Second registrant — torchao, via transformers.**
   `unsloth_zoo/temporary_patches/utils.py:107` imports `transformers.processing_utils`,
   which reaches `transformers/quantizers/quantizer_torchao.py:39 import torchao`, which
   descends through `torchao/dtypes/uintx/dyn_int8_act_int4_wei_cpu_layout.py:317` into
   `torchao/prototype/inductor/fx_passes/qsdpa_fusion.py:7`,
   `from torch._inductor.lowering import lowerings as L`, and eventually back to
   `from torch._inductor.codecache import (...)`. Because `codecache` is no longer in
   `sys.modules`, it **re-executes**, reaches line 1121 again, and the assert fires.

5. **The re-raise.** `unsloth_zoo/temporary_patches/utils.py:128` catches and re-raises
   as a bare `Exception`, which is what the trainer and the worker see.

So `torchao` is the messenger, not the culprit. It is simply the first thing after
unsloth's swallowed attempt that imports `codecache` again.

### 3.4 What the unsloth_zoo patch at utils.py:107 is for, and whether a switch skips it

`utils.py:107` is not itself the tqdm patch. It is the ordinary import of
`transformers.processing_utils` at the top of unsloth_zoo's temporary-patch module,
pulled in by `temporary_patches/__init__.py:19 -> gemma.py:22`. Its `try/except` at line
128 exists to convert import problems into a visible error.

The tqdm patch at `common.py:70-81` is cosmetic. It replaces the progress-bar factory in
`torch._inductor.async_compile` so compilation shows "Unsloth: Compiling kernels". It has
no functional role in training.

**No documented switch skips it.** The environment variables read in the surrounding
function are `UNSLOTH_COMPILE_DEBUG`, `UNSLOTH_COMPILE_MAXIMUM`,
`UNSLOTH_COMPILE_IGNORE_ERRORS` and `UNSLOTH_ENABLE_LOGGING`, and none of them guards the
`try` block. The block runs unconditionally at import. That is why no `UNSLOTH_*`
variable appears among the working remedies below.

### 3.5 Upstream status

The underlying PyTorch defect is
[pytorch/pytorch#140765, "KeyError in default_cache_dir() when user account doesn't exist"](https://github.com/pytorch/pytorch/issues/140765),
opened 2024-11-14 and **closed as completed 2026-05-19**. The report describes exactly
this deployment shape: containers forced to run as an ordinary user for security, with no
matching `useradd` in the image.

Two corrections to that issue as it applies here, both measured:

- The issue states "Setting `TORCHINDUCTOR_CACHE_DIR` does work around the problem."
  **In this image it does not.** Probe 17 set it and B-16 still reproduced. The reason is
  that `cache_dir_utils.py` has two functions: `cache_dir()` honours the variable, but
  `default_cache_dir()` calls `getpass.getuser()` unconditionally, and
  `codecache.py:2560` calls `default_cache_dir()` directly. The upstream workaround
  addresses a different call site.
- The fix is **not effective in torch 2.10.0** as shipped in `unsloth/unsloth:latest`.
  Probe 27 ran that image under an unmapped uid and reproduced the same
  duplicate-registration assert, on artifact type `precompile` rather than `inductor`.

No upstream issue was found for the duplicate-registration assert as a *symptom* of the
swallowed import. The unsloth bare `except:` that converts a fatal environment problem
into a confusing assert five frames away is, on this evidence, unreported.

---

## 4. Remedies tested in the pinned image

Every row below ran the identical command from section 2.2 with one change applied, in
the pinned image by digest, with `--gpus all`, no network, and no `pip`. A remedy counts
as working only if `from unsloth import is_bfloat16_supported` exits 0.

| # | Change | Exit | Works? |
|---|---|---|---|
| A1 | `-e USER=synaptic` | 0 | **yes** |
| A1' | `-e LOGNAME=synaptic` | 0 | **yes** |
| A1'' | `-e USERNAME=synaptic` | 0 | **yes** |
| A2 | `--user 1001:102` (the image's own user) | 0 | **yes** |
| A3 | `-e TORCHINDUCTOR_CACHE_DIR=/tmp/ind` | 1 | no |
| A4 | `import torchao` before `unsloth` | 1 | no |
| A5 | full run-10 environment **plus** `-e USER=synaptic` | 0 | **yes** |
| B | `unsloth/unsloth:latest` under `--user 1000:1000` | 0 | yes, but see 4.3 |

### 4.1 Why A3 and A4 fail

**A3** fails for the reason given in 3.5: `codecache.py:2560` calls `default_cache_dir()`,
which ignores the variable.

**A4 is the important negative result.** Importing `torchao` first does not reorder the
problem away, it *unmasks* it. Without unsloth's bare `except:` to swallow it, the
`KeyError: 'getpwuid(): uid not found: 1000'` propagates directly out of
`codecache.py:2560` and the process dies there. The B-16 assert never appears, but the
import still fails. Import order is therefore not a remedy at all, and any ruling that
reorders imports in the staged trainer would trade one failure for another.

### 4.2 Why the environment-variable remedies work

`getpass.getuser()` in the CPython 3.11 standard library consults the environment before
the password database:

```python
for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
    user = os.environ.get(name)
    if user:
        return user
import pwd
return pwd.getpwuid(os.getuid())[0]
```

Any one of those four keys, set to any non-empty string, short-circuits the lookup.
`pwd` is never consulted, `codecache` completes, `'inductor'` is registered exactly once,
and torchao's later import finds the module in `sys.modules` and does not re-execute it.
The value is used only to name a cache directory under the temp root, so it is arbitrary.

A5 is the realistic case: the full run-10 environment, the run-10 uid, and one added
key. It passes, which is the strongest single piece of evidence that this is sufficient
in the real composition and not an artifact of a stripped-down probe.

### 4.3 Why remedy B is a coincidence and should be rejected

`unsloth/unsloth:latest`, digest
`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`, carries
torch 2.10.0+cu128, torchao **0.14.0 (identical to the pinned image)**, unsloth 2026.5.9,
unsloth_zoo 2026.5.5, transformers 4.57.6, Python 3.12 at `/opt/venv`.

It imports cleanly under `--user 1000:1000`. It does so for one reason only: its
`/etc/passwd` contains `ubuntu:x:1000:1000`, so the lookup succeeds. Probe 27 removed
that coincidence by running it as `--user 4242:4242`, unmapped in both images, and it
reproduced the identical duplicate-registration assert. The control, probe 26, ran the
pinned image as `--user 4242:4242` and also reproduced.

That pair of probes is what rules out the "newer image fixes it" hypothesis. torchao is
the same version in both images, so torchao was never the variable. A pin move to
`latest` would carry torch 2.9.0 to 2.10.0 and unsloth 2026.1.2 to 2026.5.9 with all the
retraining-behaviour risk that implies, would invalidate the image half of every prior
acceptance row, and would leave the actual defect in place, latent until the next time
`container_user` changes. It also surfaced a new warning under uid 1000,
`Unsloth: Failed to create directory 'unsloth_compiled_cache' because [Errno 13]
Permission denied`, which is an unrelated writability problem this path has not yet met.

**Remedy class (b) is therefore not recommended, and no image was pulled.** The two
candidate tags the lead authorised were not needed: `unsloth/unsloth:latest` was already
present on the host, which supplied the class (b) data point at zero cost and zero
durable footprint. Testing further tags would consume disk to re-measure a hypothesis
that probes 26 and 27 have already falsified. If the architect disagrees, the
falsification is cheap to revisit: any candidate tag must be probed under an unmapped
uid, not under 1000.

**Remedy class (c), a derived image, is unnecessary** and is not costed here. It was
reserved for the case where no in-image remedy existed. Four do.

---

## 5. What each working remedy costs

### A1 — add one environment key (recommended for the architect's consideration)

The Host emits the container environment in
`synaptic_host/docker_training.py` at the dict containing `"TRITON_CACHE_DIR": "/tmp/triton"`
(line 486). A1 adds one entry, for example `"USER": "synaptic"`.

That single line is **not** the whole cost. The engine's SFT runtime requirements pin a
strict `allowed_environment` list at
`synaptic-tuner/tuner/training/methods/sft.py:52-63`, which today reads
`COMSPEC, CUDA_VISIBLE_DEVICES, LANG, LC_ALL, LD_LIBRARY_PATH, NVIDIA_VISIBLE_DEVICES,
PATH, PATHEXT, PYTHONIOENCODING, SystemRoot, WINDIR, PYTHONNOUSERSITE, PYTHONSAFEPATH,
PYTHONPATH, HF_HOME, TRANSFORMERS_CACHE, HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE,
WANDB_DISABLED, HOME, XDG_CACHE_HOME, TORCH_HOME, TRITON_CACHE_DIR` plus the eight
`SYNAPTIC_*` roots. `USER` is not in it. This is the same wall B-9-R1 hit with the four
cache keys, and the same procedure applies: admit the key in the engine, regenerate the
`offline-sft-worker-v1` closure per the B-5 procedure, move the pin, cut a release.
The assertion at `synaptic-tuner/tests/training/test_sft_compilation.py:193` is the
matching test surface.

- **Touches:** engine (allowlist + closure regeneration + pin move) and Host (one env line).
- **Prior acceptance evidence disturbed:** the recorded child environment key set
  (section 22.11 row 2) gains one key. The engine closure digest changes, as it did for
  B-9-R1. B-9's `--user 1000:1000` and its P8 stage-writability evidence are untouched,
  as are the B-9-R1 `/tmp` cache readings, the B-10 four-row table and the B-10-R1 cache
  tree.
- **Robustness:** works for any uid, mapped or not. It does not depend on the image's
  passwd file, so it survives a future image change.

### A2 — change `container_user` to the image's own user

`docker_host.container_user` is a Host profile field
(`synaptic_host/docker_prepared_composition.py:65`, grammar at
`synaptic_host/docker_provider.py:20`). Setting it to `1001:102` makes the container run
as the image's real `unsloth` user, the passwd lookup succeeds, and the import passes.

- **Touches:** Host profile value only. No engine change, no closure regeneration, no
  new environment key, no pin move.
- **Prior acceptance evidence disturbed:** this is the expensive half. B-9 chose
  `1000:1000` specifically so the container user could write `/artifacts` across the
  DrvFs bind, and B-9's whole acceptance rests on that. Changing the uid re-opens B-9,
  B-9-R1 and the P8 stage-writability probe, all of which would have to be re-measured
  on the mandated mount. **This spike did not measure whether uid 1001 can write the
  staged `/artifacts` tree over the DrvFs bind**, and that measurement is the gate on
  A2 being viable at all.
- **Robustness:** brittle in the same way remedy B is. It depends on the image's passwd
  file, so a future image with a different internal uid re-opens B-16.

### Ranking

A1 first, A2 second, B rejected, C unnecessary.

A1 is ranked first despite crossing two repositories because it is the only remedy that
fixes the actual defect rather than avoiding it, and it is the only one that leaves
B-9's hard-won mount evidence alone. A2 is smaller on paper, one profile value against
an engine change, but "smallest change" was defined by the dispatch as least disturbance,
and A2 disturbs the one thing this feature spent three imPACT cycles establishing. If the
architect prefers A2 on repository-count grounds, the DrvFs writability of uid 1001 must
be measured first.

---

## 6. Risks and open questions

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A1's engine allowlist change invalidates the worker closure | certain | medium | B-5 regeneration procedure, already exercised twice (B-9-R1, B-14) |
| A2 re-opens B-9 stage writability | high | high | measure uid 1001 writing `/artifacts` over the DrvFs bind before ruling |
| The import succeeds but training later re-enters the same path | low | medium | run 11 must reach past the import, not merely past line 137 |
| A later image bump reintroduces B-16 under a different uid | moderate | medium | A1 is uid-independent; A2 and B are not |

Open questions for the architect:

1. Which of `USER`, `LOGNAME`, `LNAME` or `USERNAME` should be set, and to what value?
   All four work. `USER` is the conventional choice on Linux; the value is arbitrary and
   only names a temp-directory suffix.
2. Can uid 1001 write the staged `/artifacts` tree over the DrvFs bind? Unmeasured here,
   and it decides whether A2 is even available.
3. Does anything else in the trainer or the engine call `getpass.getuser()`, or otherwise
   assume a resolvable uid? Not surveyed. The same class of failure could recur past the
   import.
4. Should the swallowed-exception behaviour be reported upstream to unsloth? The bare
   `except:` at `unsloth_zoo/temporary_patches/common.py:74` is what made this blocker
   cost a full run to diagnose.

---

## 7. Evidence

Probe transcripts, verbatim stdout, stderr and exit codes, plus the opening and closing
container censuses, are under `scratch/b16-spike/` in this worktree (untracked):
`census-before.txt`, `census-after.txt`, `run10-traceback-target.txt`,
`run10-container-ad2a2e607028.log`, `run10-inspect.json`, `probe-*.stdout`,
`probe-*.stderr`, `probe-11-versions.txt`, `probe-12-patchsource.txt`,
`probe-13-firstregistrant.txt`, `probe-14-source.txt`, `probe-22-latest-versions.txt`,
`probe-24-latest.txt`, `upstream-140765.json`.

Sources:

- [pytorch/pytorch#140765 — KeyError in default_cache_dir() when user account doesn't exist](https://github.com/pytorch/pytorch/issues/140765)
- [pytorch/pytorch torch/_inductor/codecache.py](https://github.com/pytorch/pytorch/blob/main/torch/_inductor/codecache.py)
