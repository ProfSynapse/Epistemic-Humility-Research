# Host path simplification review — ARCHITECT

**Phase:** ARCHITECT (plan consultation, #286) for review plan #282 / follow-up #209.
**Author:** `architect-simplify`, a fresh architect chosen for independence from `architect-run`,
who wrote sections 17-25 of `docs/architecture/prepared-path-alpine-diagnostic.md` (cited **diag:N**).
**Upstream:** `docs/preparation/host-path-simplification-inventory.md` (preparer-b16, #285, 893 lines,
cited **inv:N**).
**Tree read:** `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean` at HEAD
`557ce1be48363e18c405e869da95d341a639df96`; engine submodule pin `ce539b70`. Both confirmed by
`git rev-parse` and `git submodule status` before any citation was taken. **Every `file:line` below is
true at that pair and only there.**

This document rules. It does not re-state the preparer's evidence except where I checked it myself or
where a number is load-bearing for a verdict.

No code was changed. Nothing was staged, committed or pushed. No container or image was touched.

---

## 0. The rulings, up front

| # | Question | Ruling |
|---|---|---|
| **3** | Docker Engine API over the named pipe | **DEFER.** It buys 1 blocker of 21 and one ~138-line layer. Migrate only if non-Windows local execution enters scope, and then by Route B (stdlib + the ctypes bindings this codebase already has), never Route A. |
| **4** | B-10-R2 / B-10-R1 coupling | **NEITHER option in the brief.** Scope the inventory verifier to the inventory's own `model/` subtree. Host-only, one file, **one release**, and it *preserves* the identity property that the verifier-guard option would have sacrificed. **B-10-R1 (#153) stops being a blocker but is NOT disposed of** — it becomes open architectural debt, and that downgrade changes a recorded ruling, so it goes to the user as Q6. See §3.6. |
| **5** | Keep / simplify / replace per layer | The path is **not over-engineered as a whole**. It is over-engineered in **exactly two places** — the `.synaptic` ACL chain and the driver — and it contains one property that is **declared but not actually enforced** on the only supported platform. Details in section 4. |

**The user asked not to be agreed with by default.** So, plainly: the "are we over-engineering?" premise
is about 40% supported by the record, not 100% and not 0%. Nine of twenty-one blockers would have
happened under any design (inv:520). Five of the twelve that a layer made possible come from just two
layers. One layer — the network-disabled, credential-free container — cost 60 lines and caused zero
blockers (inv:343), which proves cheap hardening is achievable here and that "hardening" is not one thing
to be judged as a bloc.

---

## 1. What I verified myself, and four things the inventory does not carry

I did not inherit the preparer's load-bearing claims. I re-read every one I rule on. The inventory is
accurate everywhere I checked it. These four findings are mine and are additional.

### 1.1 The file-mode layer is inert on the mandated platform

The lead asked me to rule on the B-14 asymmetry: the engine deleted its staged-member exec-bit equality
(diag section 23) and the Host still checks one at `docker_staging.py:1289-1291`. The asymmetry is real
but it is **not the finding**. The finding is that the Host check cannot fire at all.

```
docker_staging.py:168-174
def _verify_file_mode(
    info: os.stat_result, *, executable: bool, read_only: bool = False
) -> bool:
    if os.name == "nt":
        return True
```

`_verify_file_mode` returns `True` unconditionally on Windows. It has exactly two call sites,
`docker_staging.py:1289` (the closure exec-bit) and `:1492` (the model inventory's read-only bit). **Both
are no-ops on the only platform the Host supports.** The exec-bit check is inert twice over: I parsed the
closure manifest and all **66 of 66 members carry `git_mode` `100644`**, so the `executable=True` arm is
unreachable for this closure even on POSIX.

This is not a security hole. Both call sites sit inside a boolean whose other terms are a byte-length
comparison and a sha256 comparison (`:1287-1288`, `:1493-1494`), and content hashing subsumes the mode.
It matters for three reasons: it resolves the asymmetry the lead asked about, it is a free deletion, and
it is a case where the codebase looks more defended than it is. Note the counterpart at `:161-165`:
`_apply_file_mode` *does* act on Windows, setting the read-only attribute. The property is applied and
then not verified.

### 1.2 The model inventory has a prefix, and that changes ruling (4)

Every inventory entry's `relative_path` is built at `docker_model_inventory.py:259-262`:

```
staged_prefix = PurePosixPath(
    "model", f"models--{namespace}--{repository}", "snapshots", revision
)
```

So the entire content-addressed inventory lives under `cache/model/…`, and the engine reads exactly that
path: `--model-cache-dir {roots['cache']}/model` at `synaptic-tuner/tuner/runtime/verification.py:675`.
`cache/huggingface/` and `cache/transformers/` are **siblings the verifier has no business inspecting.**
This is what makes the cheap ruling in section 3 available, and neither the brief nor the inventory
draws the consequence.

### 1.3 The HF cache pair is pinned at four engine sites, not two

`docker_training.py:479` states that "two further engine sites encode the same pair". At `ce539b70` I
count **four** value-pinning sites:

| Site | Role |
|---|---|
| `tuner/project/execution_source.py:497-498` | admission gate (`required_environment`) |
| `tuner/execution/providers/modal/resolution.py:571` | **the cloud provider** |
| `tuner/runtime/verification.py:635` | runtime verification |
| `Trainers/sft/runtime_v1.py:1207` | the worker, and the closure entrypoint |

Plus a fifth site of a different kind, `tuner/training/methods/sft.py:56`, which admits the two key
*names* in the allowlist. Two of the four are closure members, one being the entrypoint itself, so a
cache-root move regenerates the closure. **This is the cost basis for the option I decline in section 3.**
It also means the pin is a cross-provider contract, not a local-Docker artifact — moving it locally forks
the two providers or forces a matched change in all four.

### 1.4 Two enum members are dead

`DockerVerb.STOP` (`docker_v1/model.py:1015`) and `DockerVerb.LOGS` (`:1018`) each occur exactly once in
`synaptic_host/`, at their own definition. Zero call sites. The public surface separately refuses logs at
`docker_publication.py:275-276`. Confirmed with an unanchored search after a proxy false-zero check.

### 1.5 Counts I adopt

I use the preparer's counts: **21 classifiable blockers** (B-8 excluded, inv:476), **11 numbered imPACT
cycles** (inv:552-561). The lead's #73 counter reads 12 because they entered imPACT on B-10-R2 before the
user chose review; the twelfth cycle became this review instead. Four open blockers (#120, #128, #137,
#175) have shipped fixes and are open only for want of an acceptance observation — **I do not count them
as unfinished work** (inv:532-533). Only #153 and #280 are genuinely unfixed. Section 3 clears #280 and
downgrades #153 from blocker to open architectural debt; it does not close #153. See §3.6 and Q6.

### 1.6 Consultations

I queried the secretary for pact-memory `0ccce5bc`, `e3e5f090`, `a2fc1f3d`, `1265946e`, and `architect-run`
for the intent behind five layers whose purpose is not written down (the composition digests, the four-key
sealing, the exact-set inventory clause, the Host exec-bit check, and the `.synaptic` threat model).

**Both replies arrived and both are incorporated.** They were stamped on this task's metadata at about
10:45Z, before the first draft, but an idle guard blocked their direct delivery and `TaskGet` does not
show metadata, so the first revision of this document wrongly recorded them as absent. That is corrected
here. Per the relay's own attribution rule I do **not** attribute quoted material to the secretary: it is
attributed to the record and its author (a user ruling, an `architect-run` derivation, a `test-host`
measurement), and the gap assessments alone are the relay's.

**What moved after reading them.**

| Verdict | Moved? | Why |
|---|---|---|
| Ruling (4), the Host fix | **No, and its justification is stronger** | `architect-run`'s own citation places the engine's read at `cache_root/model/<repo>/snapshots/<revision>` (`tuner/runtime/dispatch.py:189-211`), which is exactly the subtree my ruling keeps under exact-set verification. See §3.6. |
| Ruling (4)'s disposal of B-10-R1 | **Yes, materially** | It was wrong to present the closure as costless. It retires a pre-registered reading. Now §3.6 and user decision Q6. |
| §4.6, the four-key tuple | **Strengthened** | `architect-run`: "I DID NOT CHOOSE THE FOUR; I CHOSE NOT TO MAKE IT FIVE." The tightness survived on an argument about what the probe asks, **not on a threat model**, and he records the seven-key and nine-key git allowlists as an asymmetry he "never reconciled". |
| §4.8, the exec-bit deletion | **Confirmed independently** | `architect-run` reached the same two facts (`os.name == "nt"` short-circuit; 66/66 members `100644`) and calls the predicate "vacuous, not merely asymmetric". |
| §4.5, the `.synaptic` model | **Sharpened, verdict unchanged** | See below. |
| Layer 4, the composition digests | **Unchanged, with a recorded weakness** | See below. |

**On the `.synaptic` threat model (§4.5).** `architect-run` states he never established one and declines to
invent one. What he offers, explicitly labelled as *the model his own B-11 rulings assume* rather than the
original author's intent, is a tamper-mask model: the predicate distinguishes states the filesystem
produced from states an actor decided, and widening it would leave the code unable to tell its own
footprint from a third party's. He adds that this "reads as a local-tampering model on a single machine
rather than a multi-tenant one", inferred from the predicate's shape and not defended as intent. My §4.5
verdict is unchanged and now rests on a named model rather than on my own reading of the code. He also
confirms #170 is "a live hole in whatever the model is". The relay separately records that **which
consumer shape requires this layer is not in the record and the silence is by design**, so Q1 and Q2 are
correctly user questions and must not be answered from memory.

**On the composition digests (layer 4).** `architect-run`: "NO RECORDED RATIONALE AND I DID NOT ESTABLISH
ONE." He gives a scope argument only, that the digests are the only prepare-time-to-execute-time bind on
the Host invocation surface, enforced at `docker_prepared_composition.py:228-230`. Two facts I fold into
the table: the chain is **inherited from the shared provider surface and was not designed for the local
path** (`policy_digest` originates in `artifact_destinations.py`, which predates the prepared path;
`cli.py:87` shows the provider set is `{modal, docker}`), which independently corroborates my SHARED
marking; and per section 22.4 `environment_digest` **appears in zero tests** and cannot be pinned to a
literal because the policy digest also covers a machine-specific absolute path. I keep the KEEP verdict —
the audit record is real and the cloud consumer needs it — but a layer with no recorded rationale and no
test coverage is the weakest KEEP in the table, and I record it as such rather than smoothing it over.

---

## 2. RULING (3) — the Docker Engine API alternative

### 2.1 The premise in #209 is wrong by about a factor of three

#209 estimates "B-7, B-13, part of B-9". I confirm the preparer's correction (inv:704-717) and I checked
the decisive one myself. **B-7 is not a docker child.** The `SystemRoot` carry lives at
`synaptic_host/security.py:1142-1147`, inside `ScopedGitRemoteReader`, whose `subprocess.run` at `:1149`
runs `git ls-remote` at `:1169`. Admission reads a git remote under any docker transport. The comment at
`:1143` says so in its own words: "Winsock will not initialise without SystemRoot, so ls-remote dies".

The sealed four-key tuple is a separate mechanism at `docker_prepared_composition.py:116`, re-validated at
`docker_v1/model.py:1144`. The seven-key tuples at `cli.py:625` and `docker_staging.py:1016` are for other
children again. Three different scrub sites, one failure family, only one of them on the docker path.

**Net: one blocker of twenty-one eliminated outright — B-13 — plus deletion of one ~138-line layer with 12
tests.** B-9, B-9-R1, B-14, B-16, B-1 and B-1' are untouched, because bind semantics, uid presentation and
DrvFs file modes are properties of Docker Desktop and the mount, not of the client.

### 2.2 Migration size

Host-only. The engine never learns the transport: the three container-side modules contain zero matches
for `docker`, `container`, `/proc/1/cgroup` or `dockerenv` (inv:723-726), and the provider port package
docstring at `tuner/execution/providers/docker_provider_v1/ports.py:1` reads "No shell, daemon client, or
SDK is imported here." **No engine edit, no closure regeneration, no pin move** — which makes it
procedurally cheaper than any environment-key change, each of which costs the full B-5 shape.

| Item | Size |
|---|---|
| Production files touched | 5 (`docker_v1/cli.py`, `docker_v1/model.py`, `docker_prepared_composition.py`, `docker_v1/control_private.py`, `docker_v1/interop.py`) plus 1 new transport module |
| Production lines removed | ~427 runner + ~138 sealing + ~120 child-process framing |
| Text-parsing sites deleted | 6 (inv:624-631) |
| Test lines rewritten | 2,743 — `test_cli.py` 1,843, `test_real_docker_wsl.py` 531, `test_interop.py` 369 — plus the 12 sealing tests |

That test figure is the honest headline: **the transport is ~427 production lines guarded by ~2,700 test
lines.** A migration is a test rewrite with a small code change attached.

### 2.3 Ruling: defer, with a named trigger

**Do not migrate now.** Three reasons, in order of weight.

1. **It buys one blocker.** Twenty-one blockers, one eliminated. The layer it deletes is the four-key
   sealing, and section 4.6 shows that layer can be simplified out of its failure mode *without* changing
   transport, for about ten lines. Paying a 2,700-line test rewrite to delete a layer you can fix for ten
   lines is the wrong trade.
2. **The one real cost is unmeasured, and it replaces a mechanism that currently works.** Today a hung
   daemon is bounded by killing a child process (`cli.py:723`, `:758`) — blunt, simple, correct. Route B
   replaces that with overlapped I/O: `CreateEvent` / `WaitForSingleObject` / `CancelIo` /
   `GetOverlappedResult`, none of which is bound anywhere in this tree (inv:671). Everything asserted about
   that surface is tagged UNVERIFIED-BY-EXECUTION; no pipe was ever opened.
3. **It is a portability change wearing a simplification's clothes.** There is no `unix://` string anywhere
   in `synaptic_host/`. Today's endpoint layer is Windows-only by construction. An HTTP client does not
   make the Host portable; it relocates the platform assumption into a new transport module.

**The trigger.** If local execution on macOS or Linux enters scope, migrate, and migrate by **Route B**.
At that point the CLI's per-platform discovery becomes a recurring cost rather than a one-off, and the
endpoint layer must be rewritten anyway. Route A is refused independently of the trigger: `synaptic_host`
imports **zero** third-party packages today (inv:650), and Route A costs three plus `pywin32` in a package
that must ship inside a desktop installer without a Python toolchain.

**Where it belongs.** In the Host, not the engine and not neither. The engine is correctly ignorant of the
transport and must stay so.

**Before any migration is approved, one spike.** Open `\\.\pipe\dockerDesktopLinuxEngine` with the
`CreateFileW` binding that already exists at `security.py:171-176`, issue `GET /v1.56/version`, read the
response. That single measurement settles the overlapped-I/O question, which is the only genuine cost in
Route B. A transport ruling must not rest on section 3 of the inventory, and this one does not: I am
deferring, which is the ruling that needs the least evidence.

---

## 3. RULING (4) — the B-10-R2 / B-10-R1 coupling

### 3.1 What is actually wrong

Not a misplaced line. `cache` carries three contracts that cannot all hold:

1. It is a member of `_ARTIFACT_DIRECTORY_NAMES` (`docker_staging.py:49`) — topology identity.
2. It is deliberately **excluded** from `_EMPTY_ARTIFACT_DIRECTORY_NAMES` (`:50`), because the inventory
   lives there, so it is the one directory expected to be non-empty at the start.
3. It is a **writable** runtime mount: `_layout` at `:1576-1591` puts `"cache"` in the writable tuple at
   `:1581` with `read_only=False`.

Against that, `_verify_inventory_at` demands set equality on files (`:1474`) and on directories
(`:1476-1479`), rooted at that same directory. **A writable mount and an exact-set verifier over the same
tree are inconsistent by construction.** Any container write into `/artifacts/cache` trips it. The source
lock's HF pin does not cause the defect; it merely guarantees a write happens on every run.

The comment at `:1513-1520` classifies everything above `:1546` as identity that must run unconditionally.
That reasoning is sound and I am not overturning it. Line `:1545` is simply misplaced *within* it: as the
preparer puts it, a use check wearing an identity check's clothes (inv:787).

### 3.2 Why both options in the brief are wrong

**Verifier guard only** (move `:1545` under the `:1546` guard). Cheap, and it contradicts a documented
ruling to no purpose. After the guard, the inventory is content-verified on the pre-run cut and **never
again**. That discards precisely the property the `:1513-1520` comment exists to protect, on the tree that
determines what executes. I decline it.

**Cache root move** (engine stops pinning `HF_HOME` / `TRANSFORMERS_CACHE` to the cache root). Expensive
and unnecessary. Four engine value-pin sites (section 1.3), two of them closure members including the
entrypoint, so: engine commit, closure regeneration, pin move, second release. And per inv:738-756,
**nothing on the Host reads `cache/` after the container exits** — the only reader is the failing verifier
itself. You would pay the full B-5 tax and a second release to relocate a directory nobody reads, while
forking the local path from the Modal provider that shares the pin at `modal/resolution.py:571`.

### 3.3 The ruling: scope the verifier to the inventory's own subtree

Every inventory entry is prefixed `model/` (section 1.2), and the engine reads `{cache}/model`. So verify
there.

**Change shape.** One file, `synaptic_host/docker_staging.py`.

1. Introduce a module constant naming the inventory's staged prefix — `_MODEL_INVENTORY_PREFIX = "model"` —
   sited beside `_ARTIFACT_DIRECTORY_NAMES` at `:49-50`, with a comment that it mirrors the engine contract
   at `verification.py:675` and the Host's own construction at `docker_model_inventory.py:259-262`. This is
   the B-13 precedent: construct the constant you already have written down twice, rather than discovering
   it at runtime.
2. `_verify_artifact_topology` calls `_verify_inventory_at(entries, root / "cache" / _MODEL_INVENTORY_PREFIX)`,
   comparing against entry paths with the prefix stripped. Equivalently, `_verify_inventory_at` takes the
   prefix and restricts both its walk and its expected set. Either shape is acceptable; the coder picks.
3. **Line `:1545` stays outside the `expect_unused_artifacts` guard.** This is the point of the ruling.
4. `:1543`'s five-name topology equality is untouched. `:1546`'s emptiness loop is untouched.

**What is preserved.** Exact-set identity over the inventory, on every cut, including after training:
no missing file, no extra file, no extra directory, every byte hashed. Anti-injection within the subtree is
intact, which matters because a stray file inside a model snapshot directory could change what a loader
picks up.

**What is lost.** The ability to notice an extra file in `cache/` but *outside* `model/`. That property is
already unavailable — `cache` is a writable mount and the container is entitled to write there — and it is
worth nothing: the engine resolves models from `{cache}/model`, so a sibling cannot enter the model
resolution path.

**Release count: one.** No engine change, no closure regeneration, no pin move.

**Disposition of B-10-R1 (#153): it stops blocking, and it is not closed.** The HF pin stays at all four
engine sites. Its blocking harm was tripping this verifier, and the verifier is what changes. Keeping the
pin also keeps the local Docker path and the cloud provider on one shared contract.

*This paragraph originally read "close it as not-a-blocker … at zero cost". That was wrong.* The cost is
not zero: the change ends the pre-registered section 19.10 reading that the exact-set property was the
instrument for, and it leaves the HF writers inside a tree section 19.10 characterised as an input tree
with nothing left to complain if that ever became unsafe. B-10-R1 is therefore **downgraded from blocker
to open architectural debt with a recorded remedy**, not closed. §3.6 argues the downgrade; **Q6 in
§10 puts it to the user**, because 19.10 is a recorded ruling and I do not overturn one on my own
authority.

### 3.4 Tests

Red-first on V1. All in `tests/synaptic_host/test_docker_staging.py`.

| # | Test | Asserts |
|---|---|---|
| V1 | Verify cut with `cache/huggingface/x` and `cache/transformers/y` present, `expect_unused_artifacts=False` | Passes. **Red before the change** — this is B-10-R2. |
| V2 | One inventory file's bytes altered, verify cut | Raises "content-addressed model inventory differs from preparation". Proves identity survives the scoping. |
| V3 | One inventory file deleted | Raises "missing or extra files". |
| V4 | Extra file added **inside** `cache/model/…` | Raises. Anti-injection preserved where it means something. |
| V5 | Extra directory added inside the model subtree | Raises "extra directories". |
| V6 | Pre-run cut, `expect_unused_artifacts=True`, `artifacts/` non-empty | Still raises "artifact writable directory is not empty". Proves the guard's other half is untouched. |

V2 and V4 are the ones that would fail if a coder implemented this as the verifier-guard option by mistake.
They are the acceptance test for the ruling, not just for the code.

### 3.5 Run 12 acceptance rows

| Row | Observation |
|---|---|
| 0 | The verify cut after a completed training returns success, not `START_UNAVAILABLE`. B-10-R2 cleared. |
| 1 | `cache/huggingface` and `cache/transformers` exist and are non-empty at that cut, and the run still succeeds. |
| 2 | Every file under `cache/model` matches the preparation projection by sha256 at the verify cut. |
| 3 | The B-10 four-row table reads at cut 2 exactly as it did at run 11. The phase guard is unaffected. |
| 4 | Publication completes; no path under `cache/` appears in the publication trace. |
| 5 | The submodule pin is still `ce539b70` in the release range. **No engine commit, no closure regeneration, no pin move.** This row is the proof that the ruling cost one release, and it is a diff against the pinned baseline, not a count. |

### 3.6 Reconciliation with section 19.10, and what ruling (4) costs

This subsection exists because ruling (4) was first written without two consultation replies that were
already on the record. They do not overturn the ruling. They do overturn one sentence of it, and that
sentence was the one that made the ruling look free.

**What 19.10 actually says.** I re-read it at the pinned baseline rather than working from a paraphrase.
Three claims matter, and I quote them.

1. *The evidence.* "`SYNAPTIC_CACHE_ROOT` is a **read** root, not a scratch root: the engine resolves the
   locked model snapshot at `cache_root / "model" / <repository folder> / "snapshots" / <revision>`"
   (diag:2113-2116, citing `tuner/runtime/dispatch.py:189-211` and `Trainers/sft/runtime_v1.py:634-660`).
2. *The generalisation drawn from it.* "So `/artifacts/cache` is an input tree, `_verify_inventory_at` is
   right to demand exact equality, and this ruling keeps that check **unconditional on every cut**"
   (diag:2117-2118), and later, of the extra-directories branch, "a check I am explicitly ruling must
   never be relaxed" (diag:2125).
3. *The pre-registered reading.* "Reading at cut 2: cache inventory-exact through the run means
   unproven-as-active (ledger Future); `"content-addressed model inventory has extra directories"` means
   active, engine rePACT with evidence" (diag:2150-2152), with the recorded remedy filed as **B-10-R1
   (engine), task #153** and the user ruling recorded as "META-BLOCK #154, option A: release without the
   move" (diag:2147-2148).

**The three uses of the exact-set property, and what my ruling does to each.**

| Use | What it is | Under ruling (4) |
|---|---|---|
| Anti-injection over the input tree | Nothing may be added to the tree the trainer loads the model from | **Preserved, over the same paths.** |
| Identity of the prepared stage | The verify cut proves this is the stage we prepared | **Preserved.** Every inventory entry is still matched by sha256. |
| The 19.10 instrument | An extra-directories failure is the evidence that the HF writers are active | **Ended.** After the change the verifier stops looking at that part of the tree, so it can no longer report it. |

**On the read-root argument: it does not defeat the scoping, and 19.10's own evidence is why.** The claim
that must be protected is that nothing can be introduced into the tree the engine loads the model from.
19.10 establishes where that tree is, and it is not the cache root: the resolution it cites happens at
`cache_root/model/<repository folder>/snapshots/<revision>`. Ruling (4) keeps exact-set verification over
`cache/model` — the whole of the path in that citation, and every path the inventory enumerates, since
`docker_model_inventory.py:259-262` builds every entry under the `model/` prefix. An injected file
anywhere the engine can reach still fails the verifier after the change, exactly as before. What stops
being verified is `cache/huggingface` and `cache/transformers`, which no engine resolution reads.

Step 2 above is a generalisation from step 1, and it is the step I dispute. It reads the whole cache root
as an input tree. The same root is also declared writable by the Host's own mount layout
(`docker_staging.py:1581`, `read_only=False`) and is deliberately excluded from the must-be-empty set
(`docker_staging.py:50`). An exact-set check and a writable mount over the same directory cannot both
hold. That is not a defect anyone introduced; §3.1 shows it was unobservable until a container actually
wrote there, which is what run 11 did. The consultation reply names the same thing from the other
direction: at the time the verifier was written, emptiness and integrity were one predicate, so a
container legitimately writing between two calls could not be modelled. B-10 split that predicate part of
the way. Ruling (4) finishes the split.

**On the instrument: the loss is real, and it is smaller than it looks, but it is not mine to write off.**
The exact-set property over the whole root is what makes the 19.10 reading possible, and my change ends
it. Two things reduce the cost and one does not.

- The instrument has already fired. Blocker #280 is precisely the `"extra directories"` branch of the
  pre-registered reading, raised at the verify cut once the trainer wrote `cache/huggingface`. Under
  19.10's own terms that is the *active* reading. The measurement the user authorised on META-BLOCK #154
  has been taken and it came back positive. Re-arming the instrument cannot return new information about
  the question it was registered to answer.
- The reading's stated consequence is an engine rePACT, not a Host change. Ruling (4) is a Host change.
  It unblocks run 12; it does not perform the consequence.
- What it does do, and this is the part I got wrong the first time, is remove the standing signal that
  would fail loudly if the arrangement ever became unsafe. After the change the writers stay inside a
  tree that 19.10 characterised as an input tree, and nothing complains. Today they write to sibling
  directories that no resolution reads. That is a property of the `HF_HOME` layout convention, not
  anything this codebase enforces.

**Therefore ruling (4) stands, with one correction.** The Host fix is unchanged: scope
`_verify_inventory_at` to `cache/model`, one file, one release, no engine commit, no closure
regeneration, no pin move. Tests V1-V6 and the six run-12 rows stand as written.

What does not stand is the sentence in §0 and §3.3 closing **B-10-R1 (#153) as not-a-blocker**. That was
wrong, and it was wrong in the direction that flattered my own ruling. B-10-R1 is not a blocker after
this change — it no longer stops a run — but it is not disposed of either. It becomes **open
architectural debt with a recorded remedy and a user ruling behind it**, and ruling (4) *decouples* it
from run 12 rather than answering it. Downgrading a blocker to debt is a change to a recorded ruling
(19.10's "must never be relaxed", and the remedy filed at #153), and changing a recorded ruling is not
mine to do silently. **It goes to section 10 as Q6.**

One boundary from the consultation reply, honoured: the argument that the no-extra half is load-bearing
was offered as being specifically about the cache root because it is a read root, and was flagged as not
transferring to a disposition that touches a different root. Ruling (4) touches that same root. The
argument therefore applies in full, and the paragraphs above are my engagement with it, not a way around
it.

---

## 4. RULING (5) — keep / simplify / replace, per layer

**SHARED** marks a layer the Modal and HF Jobs providers reuse; those providers are 2,512 lines that this
review did not inventory (inv:884), so a change to a SHARED layer is not a local-path change. I verified
sharing for layers 1 and 7 directly: `modal/bundle.py:18` imports `ExecutionSourceV1` and `:20-22` imports
the closure manifest parser, invoked at `:271`.

*Numbering note: the subsections below are numbered after the LAYER they rule on, so §4.5 discusses
layer 5, §4.6 layer 6, and §4.7 layer 11's disposition. There are no missing subsections 4.1-4.4; the
table above carries every layer, and only the layers whose verdict needs argument get a subsection.*

| # | Layer | Verdict | Desktop | Cloud | Blockers | Property lost if removed | Cost of the change |
|---|---|---|---|---|---|---|---|
| 1 | Source lock `ExecutionSourceV1` **SHARED** | **KEEP** unchanged | provenance | **essential** (trust boundary) | 1 caused (B-10-R1) | run attribution; tenant pinning | none — §3 removes the need |
| 2 | Staging bound + scoped staging | **KEEP** | bounded work | **essential** (billing/DoS) | 4 | resource bound; proven input set | keep the dead belt: removal is 8 files to delete an unreachable constant (diag:4398) |
| 3 | Admission resolver + 19-key env | **KEEP**, watch the failure mode | determinism | **essential** (isolation) | 3 | one authored environment | none now; see §4.5 |
| 4 | Composition policy + 3 digests | **KEEP** | tamper-evidence | **essential** (audit record) | 0 caused | after-the-fact proof of policy | none; but it multiplies every profile-field change (B-1 five files, B-9 eight) |
| 5 | HMAC + `.synaptic` ACL chain | **SIMPLIFY** — split it | **weak** | conditional | **2** | see §4.5 | ~490 lines + most of 1,093 test lines |
| 6 | Sealed four-key CLI env | **SIMPLIFY** now | real | **almost none** | 1 | ambient-environment hijack defence | ~10 lines, §4.6 |
| 7 | Worker closure manifest **SHARED** | **KEEP** | **essential** | **essential** | 4 | "the engine at commit X" meaning bytes | none; the B-5 tax is the price |
| 8 | Container user + cache keys | **KEEP** | **essential** (function) | **essential** | 3 | the container can write files the user can read | none — not hardening |
| 9 | Network-disabled, credential-free | **KEEP** | strong | **essential** | **0** | offline reproducibility; tenancy | none |
| 10 | Result envelope + cause line | **KEEP** | **essential** (sole support channel) | **essential** (agent-facing) | 2 | branchable failure reporting | none |
| 11 | Driver probes P1-P11 | **FREEZE, do not productise** | operator-only | **none** | 0 caused | operator pre-flight | §4.7 |
| 12 | CLI verb enum + runner | **SIMPLIFY** now, replace conditionally | transport | transport | 2 | none intrinsic | 2 lines now; §2 later |

### 4.5 Layer 5 is where the over-engineering verdict lands

This is the single most expensive layer: **~555 of the 1,169 lines in `security.py`**, a 1,093-line test
file, two blockers (B-11, B-11-R1), two imPACT cycles, and one open residual (#170).

The preparer states the desktop case honestly and I agree with it (inv:209-213): the threat is another
*local* principal reading or forging the HMAC key, and on a desktop app an attacker who can write the
user's project directory has already won by editing the project. The cloud case holds **only if the Host
runs on a shared server** (inv:215-218).

**The threat model was never established, and I now have that on the record rather than as an inference.**
I asked `architect-run`, whose B-11 and B-11-R1 rulings are the ones that grew this layer. The answer is
that he never established one and declines to invent one after the fact. What he offers, and labels
explicitly as *the model his own B-11 rulings assume* rather than the original author's intent, is a
tamper-mask model: the predicate distinguishes states the filesystem produced from states an actor
decided, and the failure it guards is a tamper **mask** — widen it and the code can no longer tell its own
footprint from a third party's. He adds that this "reads as a local-tampering model on a single machine
rather than a multi-tenant one", inferred from the predicate's shape, and says he "would not defend it as
the author's intent".

That matters three ways for the ruling below. It confirms the preparer's characterisation of the threat
rather than contradicting it. It means no one in the record is defending a multi-tenant reading, so Q1
and Q2 are genuinely open rather than settled-and-forgotten. And it means the REMOVE half is a removal of
machinery whose *purpose* is documented only as one agent's working assumption — which raises the value
of removing it deliberately with tests, and lowers the weight of "it must be there for a reason".

**Ruling: split the layer and keep the cheap half.**

- **KEEP** the keyed-HMAC signing and verification — `security.py:1050-1058` (domain-separated
  `purpose.encode("ascii") + b"\0" + payload`, verified at HEAD) and `:1060-1062` (`hmac.compare_digest`),
  with the typed authorities at `docker_v1/authority.py:142-190`. **Also KEEP the factory
  `FileHmacAuthenticator.for_docker` at `:672-701`**, which opens or exclusively creates the one stable
  Docker control key and enforces that the key stays below host state (`:689-690`). This is a small,
  cheap, blocker-free integrity property against accidental corruption and against a second tool writing
  the same tree. It caused none of the pain.
- **REMOVE**, conditional on the user's answer to questions 1 and 2, the Windows-ACL and POSIX-mode chain
  validation and repair: `security.py:807-876` (`_ensure_private_storage_directories`, the two-pass
  leaf-first branch at `:856`, the chain loop at `:864`), `:536` (`_win_repair_private_directory`),
  `:467-531` (`_win_never_protected`), `:445` (`_win_validate_directory`), `:388-439`
  (`_win_validate_acl`), and the POSIX arms at `:718`, `:754-775`, `:783-805`. **Both blockers, both
  cycles, and the open residual are entirely here.**

**The excision has three call sites, and the CODE phase must not be told there is one.** The comment at
`security.py:695-700` says `:701` is "the only call site that repairs", and that is true but narrower than
it reads. Grepping the symbol gives:

| Call site | Argument | Role |
|---|---|---|
| `security.py:701` | `repair=True` | the only repairing site, in `for_docker` |
| `security.py:882` | `repair=False` | validation on a live path |
| `security.py:972` | `repair=False` | validation on a live path |

So removal is *not* a one-line excision. `:701` drops the repair; `:882` and `:972` are validation sites
that must each be removed or neutered deliberately, and they are the ones that decide whether the layer
still refuses a bad chain after the repair machinery is gone. The Modal authenticator (`from_context`,
`:666-669`) is correctly outside this set.

**One structural test pin must be updated in the same commit.**
`tests/synaptic_host/test_security.py:1085-1092` reads the function's own source text and asserts the
literal substring `"_ensure_private_storage_directories(repair=False)"` is present. That is a
source-scraping pin, not a behavioural test: it fails the moment the call site is edited, regardless of
whether behaviour is preserved. Any CODE task for this removal must carry it in scope with a stated
justification, or the implementer will hit it mid-change and have to stop and ask.

**Do not confuse `:672-701` with the layer being removed.** The factory is the KEEP half; only its call at
`:701` and the machinery below belong to the REMOVE half. I record this because I initially mis-cited the
factory as removable, and a coder following that list would have deleted the control-key opener.

Property lost by the removal: defence of the key file against a local principal. Retained everywhere it is
actually load-bearing, because in a cloud shape with per-tenant container or VM isolation that threat is
already handled a layer down, and the ACL chain is paying for it twice.

I flag the strongest counter-argument against my own ruling: B-11-R1's mechanism is still recorded as a
hypothesis rather than a fact, because its author "asserted a mechanism twice in this section and been
wrong twice" (diag:3320-3321). If the mechanism is not what we think, the layer's cost is understood but
its behaviour is not, and removing code you do not fully understand is its own risk. That is a reason to
remove it deliberately with tests, not a reason to keep it.

### 4.6 Layer 6 — keep the property, delete the failure mode

The four-key sealing has two distinct parts, and only one of them caused B-13.

- The **key-name denylist** at `docker_v1/model.py:1156-1161` refuses `DOCKER_*`, `TOKEN`, `AUTH`, `PROXY`.
  **This is the part that carries the property**: it is what stops a `DOCKER_HOST` or proxy variable in the
  user's shell silently redirecting the run.
- The **exact tuple equality** at `:1144-1149` against `("SystemRoot", "TEMP", "TMP", "WINDIR")` is what
  caused B-13, by omitting `USERPROFILE`.

**Ruling: relax the tuple equality to a required-subset check, keep the denylist and the per-value
Windows-drive-path check at `:1155` unchanged.** About ten lines. The ambient-hijack property is fully
retained; the whole "we failed to enumerate a variable the child needed" class becomes impossible for this
child. This is a strictly better answer than the transport migration for the same failure, at 0.4% of the
cost.

**The consultation reply strengthens this and removes my one hesitation.** I had assumed the exact tuple
might encode a deliberate minimum. `architect-run`, who ruled B-13, states the opposite: "I did not choose
the four; I chose not to make it five", and records that the tightness survived his B-13 review on an
argument about what the version probe asks of the CLI, **not on a threat model**. He also names an
asymmetry he says he never reconciled: the same codebase seals a git child with seven keys
(`cli.py:623-627`) and another with nine (`docker_staging.py:1013-1020`), while this child gets four.

I read all three tuples rather than relaying the count, and the asymmetry is real but narrower than it
sounds. The seven and the nine are the *same* seven — `PATH`, `SystemRoot`, `WINDIR`, `COMSPEC`,
`PATHEXT`, `TEMP`, `TMP` — with the nine adding only `LANG` and `LC_ALL`, which `cli.py:632` sets to `C`
by hand instead. So the two git children are effectively one tuple, and the real gap is those seven
against this child's four. What the Docker CLI child is missing relative to its siblings is `PATH`,
`COMSPEC` and `PATHEXT`, and B-13 was `USERPROFILE`, which none of the three carries. That is the
substance: the tuple is not a designed minimum, it is what each site happened to need, and relaxing it to
a required subset gives up nothing anyone chose.

For the git-side tuples I record the opposite finding rather than generalising: the B-7 decision is on the
record as deliberate — "carrying the whole Windows core set would have been easy and would have made the
scrub stop being a scrub". **This ruling therefore applies to the Docker CLI child only.** Do not let a
CODE task widen it into the git scrub on the strength of the asymmetry.

### 4.7 Layer 11 — the driver is a scaffold, and should be named one

2,882 lines including tests, the **largest single artifact in the inventory**, larger than any production
layer. It caused no blockers. It detected several and it is the reason B-12, B-13 and B-15 were diagnosed
quickly — that value was real and I am not dismissing it.

But six of the eleven probes (P1, P2, P3, P6, P7, P11) exist because a human operator can get a shell
wrong, and have no analogue in either product shape: an app controls its own PATH, its own checkout, and
its own import roots.

**Ruling: freeze it. Do not grow it, do not productise it, do not migrate it into the Host.** Retire
P1, P2, P3, P6, P7 and P11 when the manual run procedure ends. Rule on it separately from the Host, per
inv:870 — bundling it with the hardening layers produces a worse answer for both.

### 4.8 Free deletions, needing no user decision

| Item | Site | Lines | Property lost |
|---|---|---|---|
| `DockerVerb.STOP`, `DockerVerb.LOGS` | `docker_v1/model.py:1015`, `:1018` | 2 | none — zero call sites |
| Host exec-bit arm | `docker_staging.py:1289-1291` | 3 | **none on Windows** (§1.1); resolves the B-14 asymmetry the way B-14 already ruled it engine-side |
| Four-key tuple equality → required subset | `docker_v1/model.py:1144-1149` | ~10 changed | none — denylist retains the property |

On the exec-bit arm I considered the opposite ruling: make the check *real* rather than delete it. I reject
that. Making it real means implementing mode semantics on a platform that does not have them, to enforce a
distinction that the closure's own data never exercises (66/66 members are `100644`), guarding a property
that sha256 already guarantees. Delete it, and if non-Windows execution later enters scope, reintroduce it
there deliberately.

**Independently confirmed.** `architect-run` traced the same predicate without seeing my finding and
reached both facts — the `os.name == "nt"` short-circuit and the 66/66 `100644` closure — and states the
check "is vacuous, not merely asymmetric". He adds two facts I did not have. Nothing ever execs a staged
member: the trainer entry point is `runpy.run_path`, in process, so the executable bit has no consumer at
all on any platform. And the engine's real defence against a substituted module is import-origin based
(`install_owned_module_guard`, `verify_loaded_owned_module_origins`), not file-mode based. That closes the
question: the arm is not a weakened check, it is a check with no referent. The lead has adopted this
finding.

### 4.9 The sums

**Immediate, no user decision required:** ~15 production lines, **1 blocker class made impossible**
(B-13's), 2 dead enum members retired, 1 documented asymmetry resolved.

**Conditional on the user's answers to questions 1 and 2:** ~490 production lines and roughly 800 test
lines, **2 further blockers made impossible** (B-11, B-11-R1), **1 open blocker retired** (#175), **1 open
residual closed** (#170).

**Total if both land:** ~505 production lines, ~800 test lines, **3 of 21 blockers made impossible**, two
open items closed. Against a 40,109-line Host, that is 1.3% of the source. **The honest conclusion is that
simplification is worth doing and is not where the leverage is.** The leverage was in section 3: one
correctly-placed ruling closes both remaining unfixed blockers for one file and one release.

### 4.10 The over-engineering verdict, stated plainly

**No, the path is not over-engineered as a whole. Yes, it is over-engineered in two specific places, and
it is over-*claimed* in a third.**

- **Over-engineered:** the `.synaptic` ACL chain for a single-user desktop consumer (layer 5), and the
  driver as a permanent artifact (layer 11). Together they are ~3,400 lines including tests and two of the
  twenty-one blockers.
- **Not over-engineered:** the other ten layers. Nine of twenty-one blockers would have occurred under any
  design. Six were found by reading rather than running. Layer 9 shows that 60 lines of the right hardening
  costs nothing and catches its class by construction. The two consumer columns agree for nine of twelve
  layers (inv:832-834), which is a stronger argument for the design than the blocker count is against it.
- **Over-claimed:** the file-mode layer is applied but never verified on the mandated platform (§1.1). That
  is the opposite failure from over-engineering, and the user asked not to be agreed with by default, so it
  belongs in the same verdict.

The headline the user is reacting to — eleven runs to one training step — is real. Its cause is
approximately 40% our own layers, 40% product logic that any design would have hit, and 20% platform and
operator friction. It is not principally over-engineering, and the two places where it *is* over-engineering
are nameable and removable.

---

## 5. SCOPE IN MY DOMAIN

Mine: the three rulings above, the change shape and tests for ruling (4), the migration trigger for ruling
(3), the per-layer verdicts, and the sequencing in section 9.

Not mine, and deliberately absent: any code change (none was made), the Modal and HF Jobs inventory (2,512
lines, not read — every layer I believe they share is marked SHARED and my verdicts on those layers are
KEEP, so no ruling here depends on that gap), the choice between the consumer shapes in section 10, and the
acceptance of run 12.

I rule on the local path only, per the lead's scope ruling.

## 6. DEPENDENCIES AND INTERFACES

**Interface contracts that change under my rulings:** exactly one, and it is internal.
`_verify_inventory_at`'s contract narrows from "this directory contains the inventory and nothing else" to
"the inventory's subtree contains the inventory and nothing else". No public surface, no engine contract,
no provider contract, no persisted digest changes. `ExecutionSourceV1.required_environment` is untouched,
which is why the release count is one.

**Contracts that do NOT change and must be protected during implementation:** the closure manifest and its
digest, the composition environment/descriptor/policy digest chain, the seven roots, the thirteen required
environment keys, and the `_ARTIFACT_DIRECTORY_NAMES` five-name topology.

**Host → engine** stays one-directional and narrow. **Host → Docker** stays five live CLI verbs.
**Engine → container** stays environment variables and absolute paths, with no container awareness.

## 7. KEY DECISIONS AND TRADE-OFFS

1. **Scoping beats guarding.** The whole of ruling (4) turns on preferring a narrower *domain* for a check
   over a narrower *schedule* for it. Guarding trades a property for a fix; scoping keeps both. Where a
   check is failing because its domain grew, narrow the domain first.
2. **The enumeration failure has now happened three times** (B-7, B-9-R1, B-16) and each instance costs an
   engine release. I am not recommending a contract change for it now, because the fix in §4.6 removes the
   instance that is cheapest to remove and the remaining two are in a SHARED layer I did not inventory.
   **But a fourth instance should trigger a contract change, not a fourth allowlist edit.** I record that as
   the standing disposition rather than a per-blocker reflex.
3. **Cheap hardening exists.** Layer 9 is the counter-example that stops "hardening" being judged as a
   bloc: 60 lines, zero blockers, essential to both consumers.
4. **The test tree is the real cost multiplier.** 40,028 test lines against 40,109 source lines. Every
   removal frees roughly its own size again, and every migration costs roughly its own size again. That
   ratio, not the production line count, is what makes the transport migration expensive.
5. **A property that is applied but not verified is worse than one that is absent**, because it is
   believed. §1.1 is the instance.

## 8. RISKS AND CONCERNS

- **My ruling (4) has not been executed.** It is a code reading. V1 must be red before the change, and if it
  is not, my mechanism is wrong and the ruling must be re-opened before the fix ships.
- **I did not inventory the Modal and HF Jobs providers.** Every layer I believe they share is marked SHARED
  and carries a KEEP verdict, so no recommendation here should disturb them — but that is an argument from
  my own marking, and the marking rests on two verified imports plus the preparer's line counts, not on a
  read of those 2,512 lines.
- **Section 3 of the inventory is unverified by execution**, and I have leaned on it only where it agrees
  with code I read myself. My deferral in ruling (3) is deliberately the disposition that needs the least
  evidence from it.
- **No secretary or architect-run reply had arrived.** Sections 3.4 and 4.5 are where their view would
  matter, and both should be re-read if it lands.
- **Citation drift is a measured hazard in this record** (diag:4353-4356). Every line number here was read
  at `557ce1be`. I have named symbols alongside lines wherever a symbol exists, so a reader on a later
  commit can re-find the site.
- **I am recommending the removal of code whose failure mechanism is recorded as a hypothesis** (§4.5).
  Stated as a risk, not resolved.

## 9. RECOMMENDED APPROACH

**Sequence, in dependency order.**

1. **Ruling (4), alone, first.** One file, one release, six tests, V1 red-first. It closes #280 and
   downgrades #153 from blocker to debt. It depends on no user answer and no other change. Run 12
   acceptance per §3.5. **Q6 does not gate it** — Q6 decides what happens to #153 afterwards, and every
   Q6 option is compatible with shipping this step now.
2. **The free deletions (§4.8), in one commit, after run 12.** Two dead enum members, the exec-bit arm, and
   the four-key tuple relaxation with its own red-first test proving a `USERPROFILE`-shaped omission can no
   longer fail the composition. Do not bundle these with step 1: step 1 must be a clean single-cause
   release so run 12 reads unambiguously.
3. **Ask the user questions 1 and 2 (§10) before touching layer 5.** The largest single simplification
   available is gated on an answer nobody in this session can supply.
4. **Freeze the driver (§4.7).** A documentation change, not a code change.
5. **The transport spike, only if the trigger in §2.3 fires.** One pipe open, one `GET /v1.56/version`.

**Do not** do steps 2 through 5 before run 12 confirms step 1. The record's clearest lesson is that
bundled changes make a failed run ambiguous, and this path has spent eleven runs learning it.

## 10. QUESTIONS ONLY THE USER CAN ANSWER

**Q1. Which consumer shape is the Host itself for?** This reprices the whole inventory, and layer 5 in
particular.

- *(a) The user's machine only.* Layer 5's ACL chain goes; ~490 lines and two blockers with it.
- *(b) A shared server, or both.* The ACL chain stays and #170 becomes work rather than a residual.
- *(c) Both, with different builds.* Cheapest in lines, most expensive in ongoing divergence; I would
  advise against it unless (a) and (b) are both firm.

**Q2. In the cloud shape, does the Host run on a shared machine with per-tenant isolation below it?** If
tenant isolation is at the container or VM level, layer 5's threat is already handled and the layer is
paying twice. If the Host is the isolation boundary, it is load-bearing and Q1(a) does not apply.

**Q3. Is a third-party dependency ever acceptable in `synaptic_host`?** It has zero today.

- *(a) Never.* Route A is dead permanently; any future transport work is Route B. This is my
  recommendation, because the value of a dependency-free desktop installer compounds.
- *(b) Acceptable if vendored and pinned.* Route A returns as an option and the transport migration gets
  materially cheaper.

**Q4. Is macOS or Linux local execution in scope?** This is the trigger for ruling (3) and the only thing
that would change my deferral.

- *(a) Windows only, indefinitely.* Keep `docker.exe`; revisit nothing.
- *(b) In scope within the next few cycles.* Do the transport spike now, so the decision is made with a
  measurement instead of with docker-py's source.

**Q5. Does the manual driver survive the product?** 2,882 lines.

- *(a) Temporary scaffold.* Freeze it now and retire six probes when the manual procedure ends.
  Recommended.
- *(b) Permanent diagnostic tool.* Then it needs an owner and a test budget, and it should be said out loud
  that it serves neither product shape.

**Q6. Ruling (4) ends a pre-registered reading. Does it stand, and what happens to B-10-R1 (#153)?** This
is the only question in this section raised by a *recorded ruling* rather than by missing product context,
and it is the only one where my own ruling is on one side of it. §3.6 is the full argument; this is the
decision.

Section 19.10 ruled the exact-set inventory check "must never be relaxed" (diag:2125) and pre-registered
an extra-directories failure as the evidence that the HuggingFace cache writers are active, with the
remedy filed as B-10-R1 (#153) and released-without-the-move by your ruling on META-BLOCK #154 so that a
run would measure it. Run 11 took that measurement: blocker #280 **is** that failure. Ruling (4) keeps
exact-set verification over `cache/model`, which is where the engine actually resolves the model
(diag:2114-2116), and stops verifying `cache/huggingface` and `cache/transformers`, which no engine
resolution reads. The anti-injection property survives over the read path. The instrument does not.

- *(a) Ship ruling (4); downgrade #153 to open debt; do not move the writers.* **My recommendation.** One
  Host file, one release, run 12 unblocked. The instrument has already returned its answer, so re-arming
  it buys no new information. Accepts, permanently unless revisited, that the container writes two
  sibling directories inside a tree 19.10 called an input tree, with no standing check that would notice
  if that ever stopped being safe. Cost: the 19.10 reading is retired.
- *(b) Ship ruling (4) now, and execute the 19.10 remedy afterwards as its own cycle.* Same immediate
  unblock, and the arrangement 19.10 objected to is eventually removed rather than tolerated. Cost: a
  full B-5-shaped engine change later — `execution_source.py:489-502` plus the same pair at
  `verification.py:635-636` and `runtime_v1.py:1207-1208`, closure regeneration, pin move, second
  release — and `execution_source.py` is a SHARED layer, so the cloud provider moves with it. This is
  the option that keeps faith with the recorded ruling at a known price.
- *(c) Do not ship ruling (4); execute B-10-R1 first.* Honours 19.10 literally and keeps the exact-set
  property over the whole root. Cost: run 12 waits for a two-release engine cycle, and the underlying
  contradiction stays — the same root is still declared writable at `docker_staging.py:1581` and
  deliberately non-empty at `:50`, so the next writer that lands there reopens this exact question.

I recommend (a), and (b) if you want the 19.10 remedy honoured rather than retired; I do not recommend
(c). If you pick (b), ruling (4) still ships first and unchanged — the two are sequential, not
alternatives.

---

*Ruled by architect-simplify for task #286. Read-only against `557ce1be` / engine `ce539b70`; the only file
written was this one. No code change, no commit, no push. Sections 3 and 4 are rulings; section 1 reports
findings I verified myself and which the upstream inventory does not carry.*
