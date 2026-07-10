# Shared methods component: the AI-assisted research workflow

This is the canonical description of how this research program uses AI, written
once and adapted per paper. Each paper includes a version of the subsection
below in its Methods, and may point to the appendix for the full governance
rules. Numbers in [brackets] are slots the adapting paper fills from its own
experiments.

Status: draft for PI redline. Nothing here is boilerplate disclosure; the
workflow is part of the method and is described with the same precision as the
experiments.

---

## Methods subsection (adapt per paper)

### How this research was conducted with AI

This program is run by a human principal investigator working with a frontier
language model (Claude, Anthropic) acting as a research orchestrator, which in
turn dispatches specialized AI agents for bounded tasks. We describe the
arrangement in detail because it is part of the method: the division of
authority is designed so that the parts of science that require accountability
stay human, while the parts that benefit from tireless, parallel, adversarial
labor are delegated, under controls that make the delegation auditable.

The unit of work is a governed experiment. Each one is a self-contained
directory holding a signed amendment document (the experimental design in
prose), a machine-readable manifest, and the instrument code. Before anything
runs, the design registers: a hypothesis, gates with numeric floors, a
falsifier stating what outcome would kill the claim, and two independent
predictions recorded side by side, one from the PI and one from the
orchestrator. At signing, every instrument file is pinned by content hash
(SHA-256) in the manifest. After signing, gates and thresholds cannot move; a
change requires a new signed revision with a changelog, and post-outcome
changes to the registered surface are prohibited outright. [Cite: this paper's
experiments and their registered predictions, including which ones were
wrong.]

The trust boundary is explicit:

The AI side (orchestrator and agents) builds harnesses against the locked
design, runs and monitors experiments, computes results, drafts documents,
red-teams findings, and proposes interpretations.

The human side holds everything with consequence: approving and signing
designs, registering their own prediction before each run, authorizing every
paid compute launch, adjudicating gate outcomes when judgment is required,
merging evidence into the record, and deciding verdicts.

Three controls do most of the work of keeping the AI honest:

1. Adversarial review before any verdict. Results, especially good ones, are
   handed to a separate red-team agent with no stake in the outcome and an
   explicit brief to refute: to hunt oracle leaks, circular evaluation,
   goalpost drift, seed and provenance holes, and statistical errors. A
   result that looks too good triggers this review automatically, before the
   lead is allowed to write a verdict. [Cite: an instance from this paper
   where red-team review changed or confirmed a number.]

2. Read-before-cite. Signed amendment documents are the sole source of truth
   for what any prior experiment showed. No agent, including the
   orchestrator, may state a prior result from memory; the claim must trace
   to the document, and delegation prompts forbid handing agents a remembered
   interpretation to confirm. This exists because language models
   pattern-match plausible histories, and a plausible-but-wrong account of
   your own prior experiment is the most dangerous artifact in an AI-run lab.

3. Provenance by construction. Long runs checkpoint per item to append-only
   logs and are resumable; instruments are content-hashed at signing; model
   weights are pinned by revision; run environments are pinned container
   images recorded by digest. A reported number can be traced from the paper
   through the amendment to the run log to the exact instrument bytes that
   produced it. [Cite: this paper's artifact trail.]

The failure modes we observed are reported alongside the method, because they
are findings about the method. AI agents completing background work
occasionally failed to report until prompted; the remedy was verifying agent
claims against on-disk artifacts rather than trusting summaries. Registered
instrument pinning caught cases where files drifted after signing. The
orchestrator's own predictions were wrong in specific, instructive ways
[cite], and those misses are retained in the record and in this paper, because
a workflow that quietly discards its wrong predictions is optimizing for the
appearance of foresight, which is precisely the failure mode this research
program studies in language models.

We make no claim that this workflow removes the need for human scientific
judgment. The claim is narrower and testable: it makes AI participation in
research auditable, it keeps a durable line from every published number to the
bytes that produced it, and it forces both the human and the AI to say, in
advance and in writing, what would prove them wrong.

---

## Appendix: governance rules (shared across papers)

The following rules bind all AI agents in this program. They are reproduced
from the repository's operating instructions, lightly edited for
self-containment.

1. One experiment, one signed design. Every evidence-producing run belongs to
   a signed amendment with pre-stated prediction, falsifier, and gates. Gates
   and thresholds never move after signing, regardless of outcome.
2. Dual pre-registration. The PI and the orchestrator each register a
   prediction before the run. Both are retained verbatim, hits and misses.
3. Headline versus exploratory. Confirmatory claims come only from the
   registered surface. Exploratory results are reported separately and never
   pooled with confirmatory numbers. Promotion of an exploratory win to a
   claim requires a fresh confirmatory replication registered before it runs.
4. Instrument pinning. All instrument files are SHA-256 pinned at signing.
   Any post-sign change is a governed revision with a written rationale in
   the experiment's notebook.
5. Adversarial review before verdicts. No verdict is written on a result
   that has not survived a red-team pass briefed to refute it.
6. Read-before-cite. Prior results are cited only from their governed
   documents, never from memory or summaries.
7. Nulls are reported straight, with the full characterization (dose curves,
   collapse points, decomposed failure modes), not as absence.
8. Human-only holds: signing, paid-compute authorization, verdict
   adjudication, merging evidence into the permanent record.
9. Provenance: per-item resumable run logs for any long run; pinned model
   revisions; pinned container images recorded by digest; append-only session
   notes checkpointing decisions as they happen.
10. Data containment: restricted or licensed row-level data (question text,
    generations) never enters the public repository; committed artifacts are
    ID-manifests, fitted parameters, and aggregates.

---

## Adaptation notes for drafting agents

- Fill every [bracket] slot from the paper's own experiments; do not leave
  template language in a submitted draft.
- The subsection should run 400 to 700 words in a paper; cut the failure-mode
  paragraph last, it is the part reviewers remember.
- Keep the trust-boundary lists parallel and concrete. Resist the urge to
  soften "the AI was wrong twice" into "predictions were iteratively
  refined". The former is the house voice; the latter is the polite liar.
- Venue disclosure statements (e.g., "AI was used in the preparation of this
  manuscript") are satisfied by pointing at this section; write them as one
  sentence, not a second copy of it.
