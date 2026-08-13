---
name: kg-ingest
description: Ingest a research paper (or a batch) into the library's atomic knowledge graph the Agents-K1 way. Use when you are handed a paper (URL, arXiv id, or a note already in library/) and you want it folded in as typed concept atoms, mechanisms, lineage edges, and a patched paper note, reconciled against the atoms already in the vault rather than re-extracted from scratch. Also use to backfill spine papers not yet atomized. This is the standing ingestion posture for growing the graph one paper at a time.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Workflow, WebFetch
---

# Knowledge-graph ingestion (kg-ingest)

The library (`library/`) is an Obsidian-style vault. Paper notes live in
`library/notes/<arxiv>--<slug>.md`; reusable atomic concepts live in
`library/concepts/{methods,metrics,datasets,models,terms,mechanisms}/`. The
graph design follows **Agents-K1 (arXiv:2606.13669)**: papers connect to typed
nodes (entities, claims, evidence, mechanisms, method lineages) instead of flat
`cites` edges. Ontology detail is in `library/SCHEMA.md`; the gold-format
exemplar is `library/concepts/methods/direct-preference-optimization.md`.

The job: take a paper and fold it in, REUSING existing canonical atoms (no
duplicate `expected-calibration-error` note on every ingest). One concept = one
file, reused by many papers; a paper note *references* atoms through typed edges,
it never redefines them.

## When to use

- You are handed a paper to add: a URL, an arXiv id, or a note already sitting
  in `library/notes/`.
- Backfilling existing papers that predate the graph.

## The shape of one ingest

Every ingest is the same five moves. The ONLY fork is move 3 (authoring): one
paper you do by hand; a batch you fan out with the Workflow.

| Move | What | Tooling |
|------|------|---------|
| 0 | **Acquire** the paper: check existence, note stub + fulltext on disk | `fetch_paper.py` |
| 1 | **Snapshot** the vault inventory | `kg_inventory.py` |
| 2 | **Mine** the source for atoms / edges / mechanisms / claims | read fulltext |
| 3 | **Author** the subgraph: reuse atoms, write only new ones, patch the note | by hand (1 paper) or Workflow (batch) |
| 4 | **Finalize**: regen MOC, canonicalize, validate, reindex | tail scripts |

**Default to the by-hand path.** For a single paper it is faster and gives you
full control of slug reuse. Reach for the Workflow only when you are handed
several papers at once (or a backfill set): it parallelizes move 3 across papers,
and that is the only thing it buys you. Moves 0, 1, 2, 4 are identical either way.

Throughout, scripts are referenced at `.agents/skills/kg-ingest/scripts/` (the
mirror an agent runs from). They are identical across `.skills/` (canonical),
`.agents/`, and `.claude/`; run from any one.

---

## Move 0: Acquire the paper

For arXiv papers, **do not hand-grab anything** and do not hand-search whether the
paper already exists. One script does both: it reports existence status and
acquires what is missing.

```bash
# Check first (offline-friendly; no downloads, no writes). Tells you exactly
# where the paper stands so you never grep library/notes by hand:
python3 .agents/skills/kg-ingest/scripts/fetch_paper.py <arxiv-id-or-url> --check
#   STATUS: NEW       -> not in the vault; run the acquire command below
#   STATUS: STUB      -> note exists but NOT ingested; skip to Move 1
#   STATUS: INGESTED  -> already in the graph; nothing to do
# Exit codes for scripting: 0 INGESTED, 10 STUB, 20 NEW.

# Acquire (pulls title/authors/year/abstract from the arXiv API, downloads the
# HTML render + PDF, writes the note stub). Idempotent; never makes a 2nd note:
python3 .agents/skills/kg-ingest/scripts/fetch_paper.py <arxiv-id-or-url> --print-cmd
```

The script prints the `<id> | <noteStem> | <src>` line the later moves need, plus
the Move 2 scan command. Useful flags: `--slug` (override the auto title slug,
ignored if a note already exists), `--area` (default `verification`), `--no-pdf`,
`--force` (re-download). It fetches via `curl` to use the system cert store
(plain `urllib` fails cert verification on macOS Python).

Notes:
- `library/fulltext/` and `library/pdfs/` are gitignored data: never commit them.
- Older papers have no HTML render; the script warns and falls back to the PDF as
  `src` (extract from the PDF, or `WebFetch` the abstract page for metadata).
- It reuses an existing note for the id regardless of slug, so a patched note is
  never clobbered or duplicated.
- Non-arXiv source: do Move 0 by hand. Put the fulltext under `library/fulltext/`
  or `library/pdfs/` and write the note stub in the shape the script emits
  (frontmatter: `title, arxiv, year, url, area, status, tags, authors, models,
  metrics, pdf`; then `## Abstract` verbatim and stub `## Summary` /
  `## Extracted numbers` / `## Relevance to experiment` sections).

## Move 1: Snapshot the inventory

So you reuse atoms already in the vault instead of duplicating them.

```bash
python3 .agents/skills/kg-ingest/scripts/kg_inventory.py > /tmp/kg_inventory.json
```

This lists every existing atom and mechanism by `id`. Before inventing a slug for
a concept the paper names, grep this file: if `truthfulqa`, `auroc`,
`expected-calibration-error`, `abstention`, etc. already exist, you REUSE the
slug, you do not create a new file.

## Move 2: Mine the source

Read the fulltext and pull out, for this paper:

- **Atoms** it names: methods, metrics, datasets, models, terms. Tag each as
  reuse-existing (in the inventory) or genuinely new.
- **Paper edges**: which atoms it proposes / uses / evaluates on / measures /
  studies (see the edge cheatsheet below).
- **Mechanisms**: cause -> effect claims the paper provides evidence for (these
  become `mechanism:` atoms the paper `supports`).
- **Claims**: 2-4 headline findings with the table/figure/section they come from.

A fast way to see which known datasets/models/metrics/baselines a paper touches
(a hint, not a substitute for reading the fulltext):

```bash
python3 .agents/skills/kg-ingest/scripts/scan_entities.py library/fulltext/<id>.html
# add --term "Grad Detect" --term SmolLM3 to count paper-specific names;
# accepts a .pdf source too (needs `pdftotext`).
```

## Move 3a (default): author the subgraph by hand

Reuse-existing atoms need no file. For each GENUINELY NEW atom/mechanism, write
one file. Then patch the paper note. Templates below are the exact on-disk shape
the validator expects (canonical `kg` + `relationships` + `related`).

**Edge vocabulary** (the `type:` values; `related` mirrors every edge target):

- Paper -> entity: `proposes`, `uses`, `evaluates_on`, `measures`, `studies`,
  `supports` (paper -> mechanism)
- Entity lineage: `derived_from`, `variation_of`, `required_by`, `related_to`
- Reverse forms on the atom side: `proposed_by`, `supported_by`

**New concept atom** -> `library/concepts/<type>/<slug>.md` (`<type>` is one of
methods/metrics/datasets/models/terms):

```markdown
---
aliases:
- <Display Name>
- <other surface form>
tags:
- kg/<type>
- concept
- <type>
kg:
  id: <type>:<slug>
  type: <type>
  status: canonical
area: <methods|metrics|datasets|models|terms>
related:
- '[[<arxiv>--<slug>]]'       # the introducing paper
- '[[<related-atom>]]'
relationships:
- type: proposed_by
  target: '[[<arxiv>--<slug>]]'
  target_id: paper:<arxiv>
  confidence: high
- type: related_to
  target: '[[<related-atom>]]'
  target_id: <type>:<related-atom>
  confidence: medium
---

<2-4 sentence definition.>

**Why it matters here:** <tie to abstention / calibration / hallucination /
the experiment.>

**Lineage:** <what it derives from or contrasts with.>
```

**New mechanism** -> `library/concepts/mechanisms/<slug>.md` (cause -> effect
claim):

```markdown
---
aliases:
- <plain-language restatement>
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:<slug>
  type: mechanism
  status: canonical
cause: "<what is done>."
effect: "<what results>."
# Optional, forward-only. A magnitude with no source fails the commit (KG124),
# so never add `coefficient` without `coefficient_source`. Do not backfill.
# coefficient: 19.8
# coefficient_units: "percentage points of answer-matching rate, 8B to 62B"
# coefficient_source: "2308.03958 Section 2, Figure 2"
polarity: enables          # REQUIRED, closed vocabulary, ERROR if wrong.
                           # increases | decreases | enables | prevents | mediates
                           # causes | modulates | trades_off | redistributes | limits
                           # complicates | decouples | explains
                           # Definitions: library/SCHEMA.md "polarity is a closed
                           # vocabulary". Nulls and confounds belong in the last
                           # three, not squeezed into `decreases`.
related:
- '[[<arxiv>--<slug>]]'
- '[[<atom-in-cause-or-effect>]]'
relationships:
- type: supported_by
  target: '[[<arxiv>--<slug>]]'
  target_id: paper:<arxiv>
  confidence: high
- type: related_to
  target: '[[<atom>]]'
  target_id: <type>:<atom>
  confidence: high
---

<1-3 sentences: what the paper found and the evidence.>
```

**Patch the paper note**: into its frontmatter (between the `---` fences) add the
`kg` block, a `related` list, and a `relationships` list with one edge per atom
and mechanism; add `kg/paper` to its tags. Then append a `## Claims` section.
Pattern:

```yaml
kg:
  id: paper:<arxiv>
  type: paper
  status: canonical
related:
- '[[<every edge target>]]'
relationships:
- type: proposes
  target: '[[<new-method>]]'
  target_id: method:<new-method>
  confidence: high
- type: evaluates_on
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: high
- type: supports
  target: '[[<mechanism>]]'
  target_id: mechanism:<mechanism>
  confidence: high
# ...one entry per atom (measures/studies/uses) and mechanism
```

```markdown
## Claims

- Evidence label: <kind>. <claim, with the table/figure/section cite>.
```

## Move 3b (batch): run the Workflow

For 2+ papers, fan out move 3 with `scripts/ingest_workflow.js`. It is **not a
registered named workflow**, so `Workflow({name: "kg-ingest"})` fails with "not
found"; invoke it by path:

```
Workflow({ scriptPath: ".../kg-ingest/scripts/ingest_workflow.js", args: {...} })
```

`args` (a real JSON object; the script also tolerates a JSON string):

```json
{
  "repoRoot": "<abs repo root>",
  "papers": [{ "arxiv": "...", "noteStem": "<id>--<slug>", "src": "library/fulltext/<id>.html" }],
  "existing": <contents of /tmp/kg_inventory.json>
}
```

Phases: Extract (one Sonnet agent per paper, structured returns, no writes) ->
Resolve (deterministic slug clustering in JS + a tiny synonym-merge agent that
reconciles new atoms AND mechanisms against the inventory) -> Author (batched
Sonnet agents write only the genuinely new notes, skip-if-exists). It returns
`paperPatches`, `newAtoms`, `newMechanisms`, and `existingMechSupport`. Save the
return to a file and feed it to move 4.

## Move 4: Finalize (regen MOC, canonicalize, validate, reindex)

Same tail for both paths.

```bash
# a. splice paper-note edges + Claims, union mechanism support, regen the MOC.
#    BATCH: pass the workflow result file.
python3 .agents/skills/kg-ingest/scripts/apply_kg_patches.py <result.json>
#    BY-HAND: you already patched the note; feed an empty result so this step
#    only regenerates the MOC and runs the dangling-link check.
echo '{"paperPatches":[],"existingMechSupport":[]}' > /tmp/empty.json
python3 .agents/skills/kg-ingest/scripts/apply_kg_patches.py /tmp/empty.json

# b. normalize any flat-key notes into canonical kg/relationships/related
python3 .agents/skills/kg-ingest/scripts/migrate_to_canonical.py

# c. validate + inspect (authority on correctness)
python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root library
python3 .agents/skills/knowledge-graph/scripts/analyze_kg.py --root library

# d. make the new notes findable by ./search (the indexer reads GIT-TRACKED
#    files via `git ls-files`, so stage the new .md before reindexing).
git add library/notes/<id>--*.md library/concepts/**/<new-slugs>.md
python3 .agents/skills/knowledge-graph/scripts/kg_index.py
```

Step c is the gate: it reports unresolved wikilink targets, ontology drift, and
orphans. A dangling link is almost always a near-synonym slug you should have
reused (fix the edge to point at the canonical atom). `apply_kg_patches.py` also
prints dangling links; ignore ones that predate your change (confirm with
`grep -rn "[[<target>]]" library/`).

The graph format and analysis tooling are owned by the vendored `knowledge-graph`
skill; `library/SCHEMA.md` is the domain overlay (namespaces + research edges).

## Move 4e: Retrieval verification (mandatory)

Passing validation only proves the graph is well-formed; it does not prove a
future session can find what you just wrote. Do this for every ingest, with
special force when the ingest is an experimental result or resolution:

1. Write 2-3 `bin/search` queries phrased the way a FUTURE session would
   naturally ask the question this ingest answers ("does `<family>` actuate",
   "`<family>` `<site>` result", "`<slug>` verdict"), not queries built from
   the new note's own title words. A query that just echoes the filename tests
   nothing.
2. Run them: `bin/search <query terms> --limit 10`. Confirm the new note (or
   its mechanism/claim) appears in the top hits.
3. If it does not surface, fix it before declaring the ingest done: add a
   missing edge, broaden `aliases`, or re-check indexing (`kg_index.py` only
   sees git-tracked files; stage the note first per Move 4d). Do not ship an
   ingest whose result cannot be found by the query a reader would actually
   type.

**Superseding-edge rule.** When this ingest overturns, corrects, or revises an
earlier claim (a null result overturned, a verdict reversed, a stale reading
corrected), do not just add the new node: mark the old one deprecated and
point it at the successor, per the Supersession convention in
`references/relationship-schema.md` (owned by the `knowledge-graph` skill):

```yaml
kg:
  id: <old-node-id>
  type: <type>
  status: deprecated
  deprecated_by: <successor-node-id>
```

A stale claim with no forward pointer is how the graph tells a future reader a
false thing: default `bin/search` already hides deprecated notes and surfaces
the successor via graph expansion, but only once the pointer exists. After
adding it, rerun the retrieval-verification queries above and confirm the
successor ranks at or above where the stale node used to rank; if the stale
node still shows without the pointer, the supersession edge is the thing that
was missing.

*Worked example (2026-07-31, gemma kv-seam quarantine cell):* a parent
experiment's stale null note ("gemma never actuated") stayed indexed after a
Phase A shallow-ladder result showed gemma's first actuation (hs15 held-out G1
PASS, 0.786). Nobody added a deprecation pointer from the null note to the new
result, and nobody tested retrieval, so a later session ran
`bin/search gemma actuation usable dose`, got the stale null ranked above the
successor, stopped at the default limit, and told the user gemma never
actuated. A sharper query (`bin/search gemma hs15 G1 pass shallow ladder`)
would have surfaced the right artifact immediately, but the real fix is
upstream of query skill: the ingest that produced the successor result should
have deprecated the stale node and self-tested retrieval before being called
done.

---

## Enriching existing notes (cluster backfill)

Moves 0-4 above ingest a *new* paper. The complementary job is bringing the many
**skeleton notes** already in `library/notes/` up to the enriched standard: a real
`## Summary`, an `## Extracted numbers` block where every figure cites its
table/figure, a `## Relevance to experiment` section, plus (for notes that predate
the graph) the `kg:` block, typed edges, new atoms/mechanisms, and `## Claims`.
The gold-standard targets are `2606.24790--grad-detect...` and
`2401.13275--can-ai-assistants...`.

Two note modes, handled automatically by the applier:

- **pre-graph** (no `kg:` block): gets body + full graph + Claims.
- **body-only** (already has `kg:`): gets only the three body sections; its
  existing graph and Claims are left untouched.

Do this a **topic cluster at a time** (use the note `area:` field as the cluster
axis). The loop is four steps:

```bash
SCRATCH=<a tmp dir>; ID="<id1> <id2> ..."   # the cluster's skeleton ids

# 1. Prep: acquire + render clean fulltext to $SCRATCH/<id>.md (pandoc, pdftotext fallback)
python3 .agents/skills/kg-ingest/scripts/enrich_prep.py --out $SCRATCH/papertext $ID

# 2. Enrich: extract -> adversarial verify -> revise, all on Sonnet 4.6.
#    Invoke enrich_cluster.js by path with args; save the return to a file.
#    args = { root, textDir: "$SCRATCH/papertext", papers: [{arxiv, note}] }

# 3. Apply deterministically (normalizes slugs, drops unresolved edges, blanks
#    unresolved claim links, drops bare-arxiv-id claim sources, dedupes dup slugs).
python3 .agents/skills/kg-ingest/scripts/enrich_apply.py $SCRATCH/cluster_result.json

# 4. Finalize: Move 4 tail (apply_kg_patches empty -> MOC + dangling check;
#    validate_kg_relationships; stage new .md; kg_index).
```

Why this shape (same spirit as Move 3's gotchas):

- **Agents never write notes.** Extract/verify/revise return structured data only;
  `enrich_apply.py` does every disk write serially, so parallel papers cannot
  collide and provenance stays deterministic.
- **The verify stage is not optional.** It refutes each extracted number against
  the source; the revise stage drops rejected numbers, keeps uncertain ones with
  an inline flag, and folds in corrections. This has caught backwards metric
  comparisons, figure/term misattributions, and genuine inconsistencies in source
  papers. Provenance is a hard requirement here.
- **Dedup is the cluster-scale risk.** 15-20 papers propose many overlapping
  atoms; the applier keeps the first definition of a duplicate slug and resolves
  every edge/claim/related target against on-disk concepts + the batch's new
  atoms, dropping or blanking anything unresolved so a big cluster never lands a
  dangling link. Always run the Move 4c validator as the gate.
- **Skeleton detection (`grep "filled during extraction"`) has false positives.**
  An already-enriched note can still match; the applier no-ops safely (logs
  `WARN stub missing` and writes the body unchanged), so a stray re-run is cheap.
- **Provenance must name the durable source** (`library/fulltext/<id>.html` or
  `library/pdfs/<id>.pdf`), never a scratch path. The revise prompt enforces this;
  spot-check and normalize if an agent slips.

## Gotchas (these are why the steps are shaped this way)

- **The paper is usually NOT in the vault yet.** The common entry is a URL or
  arXiv id, so Move 0 (acquire + stub) is part of the job, not a precondition.
  Never hand-search whether it exists: `fetch_paper.py <id> --check` reports
  NEW / STUB / INGESTED off the local vault.
- **`./search` only sees git-tracked files.** `kg_index.py` enumerates via
  `git ls-files --cached --others --exclude-standard`, so a brand-new note is
  invisible to search until it is staged. Always do move 4d.
- **Validate before you trust it.** Move 4c is the only authority on link
  integrity; a clean by-hand ingest still needs it (a fat-fingered `target_id`
  passes the eye but fails the validator).
- **Never have one Resolve agent emit the whole graph + a full alias map in a
  single `StructuredOutput`.** With ~20 papers that mega-output wedged for 6+
  minutes with zero flush (a `.jsonl` only flushes when the tool block completes,
  so a stall looks identical to slow generation). The fix: cluster atoms
  deterministically in JS by exact slug, and give the agent only a compact
  `id + type + aliases` list, returning just merge groups.
- **Mechanisms need the same synonym-merge as atoms.** Aggregating by exact slug
  alone leaves cross-paper duplicates (the spine run produced
  `model-size-improves-calibration` and `model-scale-improves-calibration` for
  the same claim, one with no file, causing a dangling link). The workflow runs
  mechanisms through the merge agent too.
- **Keep file writes collision-free.** Extract does no writes. Author agents own
  disjoint new files (skip-if-exists). Paper-note patching is deterministic
  Python in `apply_kg_patches.py`, never parallel agents editing the same note.
- **Windows temp JSON must be UTF-8 without BOM.** PowerShell `Set-Content
  -Encoding utf8` can emit a BOM that makes `apply_kg_patches.py` fail with
  `Unexpected UTF-8 BOM`. For by-hand empty patch files on Windows, use
  `[System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))`
  or another no-BOM writer.
- Generated prose: no em dashes; do not use the phrase "load-bearing".

## Provenance

Bootstrapped over a ~21-paper experiment spine (SFT / DPO / KTO / abstention /
calibration / knowledge-boundary), producing 103 atoms + 58 mechanisms with
~1,070 typed links. See `library/SCHEMA.md` for the ontology this enforces.
