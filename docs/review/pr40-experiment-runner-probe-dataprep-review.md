# Peer Review Synthesis — Feature #40 (experiment-runner probe data-prep + cloud-extract verb)

> Reviewed LOCAL diff (review-then-PR; submodule NOT yet pushed). Runner-side: branch `experiment-runner-probe-dataprep`. Submodule: synaptic-tuner `f948c21` (branch `feature/cloud-extract-verb`, diff `040054021c..f948c21`).
> Reviewers: architect (#61), test-engineer (#63), devops-engineer (#65), backend-coder (#67), security-engineer (#69).
> Synthesized by team-lead, 2026-06-15.

## Verdict

**APPROVE — zero Blocking, zero High, from all five reviewers.** The feature is safe as shipped. Every SACROSANCT and mission invariant was independently re-verified against the as-built code (not trusted from HANDOFFs):

- **§6.6 no-pollution boundary HOLDS** (architect + backend-coder, converged): the cloud-extract verb imports zero `tuner.backends.training.*` symbols (proven by grep + AST test + a counter-test that flags a synthetic training import and passes a clean one). The eager `TrainHandler` import via `tuner/handlers/__init__` is a package-init side effect incurred identically by sanctioned off-path siblings — NOT a code-path contingency. Judged at the execution path per the confirmed criterion.
- **HF_TOKEN is secret-only and unit-tested** (security): env → `get_hf_token` → `build_hf_job_secrets` → `CloudJobSpec.secrets` → `run_job(secrets=...)` as a kwarg separate from command/labels. Never in argv (not process-listing-visible), never on disk, dry-run uses `token=None`. Negative no-leak test asserts token absent from command+labels; submit fail-closed without token.
- **SACROSANCT counts 19/9/2 byte-identical** across all three skill trees (.skills/.agents/.claude); extraction stays OFF-matrix (lives in separate `prepare_extraction_cell.py`, not `matrix.yaml`).
- **SKIP-not-abort discipline**: `check_extraction_cell` has zero `raise` statements (returns `skip=True`); `check_cell` still raises `PrereqError` — contrast preserved, locked train/eval gate untouched (additive-only).
- **link-never-mutate**: resolver has zero write-ops; prep writes only a tempfile effective-config; nothing writes `run_records/`.
- **Zero CRLF churn**: all staged files LF-only.
- **Runtime reconfirmed**: runner 97 passed, submodule cloud-extract 23 passed, `sync_skills.py --check` exit 0, from the `.agents` mirror (per the 4-deep-layout gotcha).

## Findings (all non-blocking)

| # | Finding | Severity | Reviewer | Notes |
|---|---------|----------|----------|-------|
| MINOR-1 | Dead `research_repo_root` kwarg in resolver | Minor | architect | Dead-code cleanup |
| sys.path leak | Leaked `sys.path.insert` in gate `needs_mirror` branch (never popped) | Minor / Nit | architect (MINOR-2) + devops (N2) | **Converged** — same item, two reviewers; short-lived CLI, low impact |
| parents off-by-one | `_infer_repo_root` `parents[3]` off-by-one for 4-deep mirror (devops M2); `run_matrix` `parents[4]` location-portability (architect FUTURE-1) | Minor / Future | devops (M2) + architect (FUTURE-1) | **Same class** — fixed-ancestor-index; both DORMANT (primary walk-up always succeeds) |
| M1 | Explicit-id validator branch bypasses the verified-gate that reverse-lookup enforces | Minor | devops | Operator-override semantics; DORMANT (committed YAML pins `aligned_run_record_id: null`). Recommend doc OR enforce-verified-unless-`--allow-unverified` |
| M3 | Validator branch untested | Minor | devops | Cross-refs test #63; dormant until validator path goes live |
| SEC-L1 | `_handle_dry_run` prints full clone URL — if operator's git origin embeds a PAT it's echoed to stdout/JSON | Low | security | HF_TOKEN unaffected; fix = redact userinfo OR runbook note "origins must not embed credentials" |
| F1 | `sync_skills.main()` exit-1-on-drift CLI path untested (function-level detection IS covered) | Low | test | Optional follow-up test; reviewer rec = accept |
| LOW-1 | `handle()`-level CONFIG_ERROR wrapper green-by-omission (validation tested at `build_launch_plan()` level) | Low | backend | Error-branch coverage |
| LOW-2 | `_handle_submit` `load_huggingface_hub`-raises sub-branch (ENV_ERROR) unexercised (token-None IS covered) | Low | backend | Error-branch coverage |
| LOW-3 | `CLOUD_EXTRACT_SUBMIT_ERROR` (`executor.submit` raises) unexercised — operationally most-likely failure (network/quota) | Low | backend | **Highest-value gap**; matters when real cloud RUN goes live (#54-adjacent) |
| LOW-4 | `_resolve_repo_source` override uses truthiness not `is not None`; empty `--repo-url ''` falls through to git fallback | Low | backend | Harmless, fails-closed anyway |

## Informational / not-violations (no action)

- **F2 (test, INFO)**: `.claude/skills` `run_matrix.py` changed vs HEAD (3 lines: a genuine `{{lane}}→{lane}` bug fix that existed at HEAD only in `.claude`, + 2 `.as_posix()` normalizations). This is the canonical sync forward-porting `.agents`'s pre-existing fixes into the behind `.claude` mirror. Counts 19/9/2 pristine. **Net fix, not a violation.**
- **SEC-I1/I2 (security, INFO)**: `repr`-into-shell in baseline `build_repo_checkout_steps` download fallback; substring `hf_` error scrubbing. Both PRE-EXISTING baseline `tuner.cloud` code the verb depends on — OUT of the #40 diff. Tech-debt, not gating.

## Coverage ground-truth caveat

backend-coder could not produce an automated branch-coverage report: `pytest-cov` instrumentation hits a `transformers` lazy-import failure under `--cov` only (environmental, WSL). Uninstrumented suite is a clean 23 passed. GREEN basis = "all tests pass + rigorous manual branch→test mapping", NOT "coverage-verified". A real coverage number would need a cov config that handles transformers — not gating this PR.

## Theme: error-branch coverage aligns with deferred run-enablement

LOW-1/2/3, F1, and M3 are all coverage of error/CLI branches that exercise primarily when the **actual probe RUN goes live** — which is already deferred post-KTO and approval-gated (tracked #54). They are naturally a bundle with the run-enablement work rather than this reproducibility-tooling PR.

## Remediation plan

No blocking remediation. Minor/Low/Future items pending user decision at the minor-review gate.
