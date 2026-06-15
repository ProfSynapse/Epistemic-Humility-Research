---
name: kg-ingest
description: Ingest a research paper (or a batch) into the library's atomic knowledge graph the Agents-K1 way. Use when a new paper has been added to library/ (note + fulltext/pdf) and you want it integrated as typed concept atoms, mechanisms, lineage edges, and a patched paper note, reconciled against the atoms already in the vault rather than re-extracted from scratch. Also use to backfill spine papers not yet atomized. This is the standing ingestion posture for growing the graph one paper at a time.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Workflow
---

# Knowledge-graph ingestion (kg-ingest)

The library (`library/`) is an Obsidian-style vault. Paper notes live in
`library/notes/`; reusable atomic concepts live in `library/concepts/`. The
graph design follows **Agents-K1 (arXiv:2606.13669)**: papers connect to typed
nodes (entities, claims, evidence, mechanisms, method lineages) instead of flat
`cites` edges. The full ontology and frontmatter templates are in
`library/SCHEMA.md`; the gold-format exemplar is
`library/concepts/methods/direct-preference-optimization.md`.

This skill is the repeatable **ingestion** step: take new paper(s) and fold them
into the graph, REUSING existing canonical atoms (no duplicate
`expected-calibration-error` notes on every ingest).

## When to use

- A new paper was added to `library/notes/` (with fulltext in
  `library/fulltext/<arxiv>.html` or `library/pdfs/<arxiv>.pdf`).
- Backfilling existing papers that predate the graph.

## The four moves

The intelligence runs as a background Workflow; the writes are deterministic.
Never let one agent hold the whole graph in a single output (see Gotchas).

1. **Snapshot the vault inventory** so Resolve can reconcile against it:

   ```bash
   python3 .agents/skills/kg-ingest/scripts/kg_inventory.py > /tmp/kg_inventory.json
   ```

2. **Resolve each paper's note + source paths** (the workflow reads them):

   ```bash
   for id in <arxiv-ids>; do
     note=$(ls library/notes/${id}--*.md 2>/dev/null | head -1)
     if   [ -f library/fulltext/${id}.html ]; then src=library/fulltext/${id}.html
     elif [ -f library/pdfs/${id}.pdf ];      then src=library/pdfs/${id}.pdf
     else src=none; fi
     printf '%s | %s | %s\n' "$id" "$note" "$src"
   done
   ```

3. **Run the ingestion workflow** (Workflow tool) with
   `scripts/ingest_workflow.js`. Pass `args` as a real JSON object (the script
   also tolerates a JSON string):

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
   Sonnet agents write only the genuinely new notes, skip-if-exists). The
   workflow returns `paperPatches`, `newAtoms`, `newMechanisms`, and
   `existingMechSupport`.

4. **Apply, canonicalize, validate, analyze** from the workflow result file:

   ```bash
   # a. splice paper-note edges + Claims, union mechanism support, regen the MOC
   python3 .agents/skills/kg-ingest/scripts/apply_kg_patches.py <result.json>
   # b. normalize the new notes into the canonical kg/relationships/related shape
   python3 .agents/skills/kg-ingest/scripts/migrate_to_canonical.py
   # c. validate + inspect with the vendored knowledge-graph skill
   python3 .agents/skills/knowledge-graph/scripts/validate_kg_relationships.py --root library
   python3 .agents/skills/knowledge-graph/scripts/analyze_kg.py --root library
   ```

   Step a splices each new paper note's typed-edge frontmatter + `## Claims`
   section (idempotent), and adds `supported_by` edges to existing mechanism
   notes for the new paper. Step b rewrites any flat-key notes into the canonical
   shape (notes already carrying `kg:` are skipped). Step c is the authority on
   correctness: it reports unresolved targets, ontology drift, and orphans.
   Resolve dangling links by hand (usually a near-synonym slug to merge).

The graph format and analysis tooling are owned by the vendored `knowledge-graph`
skill; see `library/SCHEMA.md` for the domain overlay (node-type namespaces and
the research edge vocabulary).

## Gotchas (these are why the steps are shaped this way)

- **Never have one Resolve agent emit the whole graph + a full alias map in a
  single `StructuredOutput`.** With ~20 papers that single mega-output wedged for
  6+ minutes with zero flush (a `.jsonl` only flushes when the tool block
  completes, so a stall looks identical to slow generation). The fix used here:
  cluster atoms deterministically in JS by exact slug (extractors emit canonical
  kebab-case slugs, so the same concept collides for free), and give the agent
  only a compact `id + type + aliases` list, returning just merge groups.
- **Mechanisms need the same synonym-merge as atoms.** Aggregating mechanisms by
  exact slug alone leaves cross-paper duplicates (the spine run produced
  `model-size-improves-calibration` and `model-scale-improves-calibration` as the
  same claim from two papers, one with no file, causing a dangling link). The
  workflow now runs mechanisms through the merge agent too.
- **Keep file writes collision-free.** Extract does no writes. Author agents each
  own disjoint new files (skip-if-exists). Paper-note frontmatter patching is
  deterministic Python in `apply_kg_patches.py`, never parallel agents editing
  the same note.
- **Reconcile against the vault, not just the batch.** Always pass the
  `kg_inventory.py` snapshot as `existing` so a concept already in the vault is
  reused by id, not duplicated.
- Generated prose: no em dashes; do not use the phrase "load-bearing".

## Provenance

Bootstrapped over a ~21-paper experiment spine (SFT / DPO / KTO / abstention /
calibration / knowledge-boundary), producing 103 atoms + 58 mechanisms with
~1,070 typed links. See `library/SCHEMA.md` for the ontology this enforces.
