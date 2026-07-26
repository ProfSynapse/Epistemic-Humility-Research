export const meta = {
  name: 'kg-ingest-byref',
  description: 'Agents-K1 ingestion for large batches: inventory passed BY PATH, not inlined into args',
  phases: [
    { title: 'Extract', detail: 'one agent per paper: read fulltext + inventory, return typed atoms/mechanisms/claims' },
    { title: 'Resolve', detail: 'single agent reconciles all proposed new atoms/mechanisms against the vault and each other' },
    { title: 'Author', detail: 'write the genuinely new concept notes; one owner per file, no collisions' },
    { title: 'Patch', detail: 'splice kg/related/relationships + Claims into each paper note' },
  ],
  model: 'sonnet',
}

// ---- inputs ----
// Sibling of ingest_workflow.js. That script inlines the whole vault inventory
// into `args`; at ~700 atoms / ~450 mechanisms that is ~76KB of tool input, which
// is impractical to pass by hand. The workflow sandbox has no filesystem access,
// but the AGENTS it spawns do -- so here the inventory travels as a PATH and every
// agent reads it directly. Same five moves, same on-disk output contract.
const A = typeof args === 'string' ? JSON.parse(args) : args
const ROOT = A.repoRoot
const PAPERS = A.papers                 // [{arxiv, noteStem, src}]
const INV = A.inventoryPath             // JSON: {atoms:[{id,type,aliases}], mechanisms:[{id,type,aliases}]}

const FORMAT_REF = `Read ${ROOT}/library/SCHEMA.md and the gold exemplar ${ROOT}/library/concepts/methods/direct-preference-optimization.md FIRST: they define the node kinds, the controlled relation vocabulary, and the exact frontmatter shape the validator expects.`

const REUSE_RULE = `Read the vault inventory at ${INV} before proposing ANY slug. It lists every atom and mechanism already in the graph. One concept = one file, reused by many papers. If a concept already exists (e.g. \`abstention\`, \`steering-vector\`, \`residual-stream\`), you MUST reuse that exact slug and mark it existing. Inventing a near-synonym of an existing atom is the single most damaging error in this job -- it silently forks the graph. When a plausible existing slug is close but not identical, prefer reuse and say so.`

const TERMS = `Terminology in prose is binding: "known-unknown (KU) direction", "KU readout gate", "boundary push (dosed write)". Never write "doubt direction" or "doubt gate". Artifact, config, and variable names keep their literal on-disk spellings.`

const EXTRACT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['arxiv', 'atoms', 'mechanisms', 'claims', 'paperEdges'],
  properties: {
    arxiv: { type: 'string' },
    atoms: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'display', 'atom_type', 'existing'],
        properties: {
          id: { type: 'string', description: 'canonical kebab-case slug; reuse the vault slug verbatim when it exists' },
          display: { type: 'string' },
          atom_type: { type: 'string', enum: ['method', 'metric', 'dataset', 'model', 'term'] },
          aliases: { type: 'array', items: { type: 'string' } },
          existing: { type: 'boolean', description: 'true iff this id already appears in the inventory file' },
          definition: { type: 'string', description: '2-4 sentence definition; required when existing=false' },
          whyItMatters: { type: 'string', description: 'tie to abstention / calibration / hallucination / steering; required when existing=false' },
          lineage: { type: 'string' },
        },
      },
    },
    mechanisms: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'cause', 'effect', 'polarity', 'existing'],
        properties: {
          id: { type: 'string' },
          aliases: { type: 'array', items: { type: 'string' } },
          cause: { type: 'string' },
          effect: { type: 'string' },
          polarity: { type: 'string', enum: ['increases', 'decreases', 'enables', 'prevents', 'mediates'] },
          evidence: { type: 'string', description: '1-3 sentences: what the paper found, with the table/figure/section' },
          relatedAtomIds: { type: 'array', items: { type: 'string' } },
          existing: { type: 'boolean' },
        },
      },
    },
    paperEdges: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['type', 'targetId'],
        properties: {
          type: { type: 'string', enum: ['proposes', 'uses', 'evaluates_on', 'measures', 'studies', 'supports'] },
          targetId: { type: 'string', description: 'e.g. method:foo, metric:bar, mechanism:baz' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
    claims: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['evidenceLabel', 'text'],
        properties: {
          evidenceLabel: { type: 'string', description: 'kind of evidence, e.g. experiment / analysis / survey / theory' },
          text: { type: 'string', description: 'the finding, WITH the table/figure/section it comes from' },
        },
      },
    },
    notes: { type: 'string', description: 'anything the lead should know: unreadable source, paywall, mismatch between the id and the actual paper' },
  },
}

phase('Extract')
const extracted = (await parallel(PAPERS.map(p => () =>
  agent(
    `Mine one paper for knowledge-graph ingestion.

Paper: arXiv ${p.arxiv}
Fulltext/source on disk: ${ROOT}/${p.src}
Paper note stem: ${p.noteStem}

${FORMAT_REF}

${REUSE_RULE}

Read the source at ${ROOT}/${p.src} (it may be HTML or PDF; for PDF use pdftotext or read it directly). Then return:
- atoms: methods/metrics/datasets/models/terms the paper actually names. Mark existing=true for every one already in the inventory. Only supply definition/whyItMatters/lineage for genuinely NEW atoms.
- mechanisms: cause->effect claims this paper provides EVIDENCE for. Reuse existing mechanism ids where the vault already has the same causal claim.
- paperEdges: one typed edge per atom/mechanism (proposes/uses/evaluates_on/measures/studies for atoms; supports for mechanisms).
- claims: 2-4 headline findings, each citing the table/figure/section it came from.

Be conservative and accurate. Do NOT invent numbers, and do NOT assert a finding the paper does not actually make -- this graph is cited as provenance by downstream research, so a plausible-but-wrong edge is worse than a missing one. If the source is unreadable or the paper is clearly not what its id/title suggested, say so in notes and return empty arrays rather than guessing.

${TERMS}

Return ONLY the structured object.`,
    { label: `extract:${p.arxiv}`, phase: 'Extract', schema: EXTRACT_SCHEMA, model: 'sonnet' }
  )
))).filter(Boolean)

log(`Extract done: ${extracted.length}/${PAPERS.length} papers returned`)

// ---- deterministic pre-pass: cluster proposals by slug across papers ----
const proposedAtoms = {}
const proposedMechs = {}
for (const e of extracted) {
  for (const a of (e.atoms || [])) {
    if (a.existing) continue
    if (!proposedAtoms[a.id]) proposedAtoms[a.id] = { ...a, sources: [] }
    proposedAtoms[a.id].sources.push(e.arxiv)
  }
  for (const m of (e.mechanisms || [])) {
    if (m.existing) continue
    if (!proposedMechs[m.id]) proposedMechs[m.id] = { ...m, sources: [] }
    proposedMechs[m.id].sources.push(e.arxiv)
  }
}
const atomList = Object.values(proposedAtoms)
const mechList = Object.values(proposedMechs)
log(`Proposed NEW: ${atomList.length} atoms, ${mechList.length} mechanisms (pre-reconciliation)`)

const RESOLVE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['atoms', 'mechanisms', 'rejected'],
  properties: {
    atoms: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'display', 'atom_type', 'definition'],
        properties: {
          id: { type: 'string' }, display: { type: 'string' },
          atom_type: { type: 'string', enum: ['method', 'metric', 'dataset', 'model', 'term'] },
          aliases: { type: 'array', items: { type: 'string' } },
          definition: { type: 'string' }, whyItMatters: { type: 'string' }, lineage: { type: 'string' },
          sources: { type: 'array', items: { type: 'string' } },
          relatedIds: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    mechanisms: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'cause', 'effect', 'polarity'],
        properties: {
          id: { type: 'string' }, aliases: { type: 'array', items: { type: 'string' } },
          cause: { type: 'string' }, effect: { type: 'string' },
          polarity: { type: 'string', enum: ['increases', 'decreases', 'enables', 'prevents', 'mediates'] },
          evidence: { type: 'string' },
          sources: { type: 'array', items: { type: 'string' } },
          relatedAtomIds: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    rejected: {
      type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['proposedId', 'reason'],
        properties: {
          proposedId: { type: 'string' },
          mergedIntoId: { type: 'string', description: 'the canonical slug it should collapse into' },
          reason: { type: 'string' },
        },
      },
    },
  },
}

phase('Resolve')
const resolved = await agent(
  `Reconcile proposed NEW knowledge-graph nodes against the existing vault and against each other.

Vault inventory (every atom + mechanism already on disk): ${INV}
${FORMAT_REF}

PROPOSED NEW ATOMS (deduplicated by slug across ${extracted.length} papers):
${JSON.stringify(atomList, null, 1)}

PROPOSED NEW MECHANISMS:
${JSON.stringify(mechList, null, 1)}

Your job is to be the graph's immune system. For each proposal decide:
- KEEP as new (it is genuinely absent from the vault and distinct from every other proposal), or
- REJECT and merge into an existing vault slug, or into another proposal that is the better canonical name.

Reject aggressively when two proposals are the same concept under different wording, or when a proposal is a near-synonym of something already in the inventory -- read the inventory file and check before keeping anything. Near-duplicate atoms are the main way this graph degrades.

For every KEPT atom, ensure definition / whyItMatters / lineage read as durable reference prose (not paper-specific summary), and set relatedIds to real slugs (existing vault slugs or other kept proposals). For every KEPT mechanism, ensure cause/effect are crisp and polarity is right, and relatedAtomIds point at real slugs.

Return every rejection in \`rejected\` with the slug it merged into, so the downstream authoring step can rewrite edges. Do not silently drop anything.

${TERMS}

Return ONLY the structured object.`,
  { label: 'resolve:vault-reconcile', phase: 'Resolve', schema: RESOLVE_SCHEMA, model: 'sonnet', effort: 'high' }
)

const keptAtoms = (resolved && resolved.atoms) || []
const keptMechs = (resolved && resolved.mechanisms) || []
const rejected = (resolved && resolved.rejected) || []
log(`Resolved: keeping ${keptAtoms.length} atoms + ${keptMechs.length} mechanisms; ${rejected.length} merged away`)

// remap: proposedId -> canonical id, so paper edges never point at a rejected slug
const remap = {}
for (const r of rejected) if (r.mergedIntoId) remap[r.proposedId] = r.mergedIntoId
const canon = id => {
  if (!id) return id
  const bare = id.includes(':') ? id.split(':').slice(1).join(':') : id
  const pre = id.includes(':') ? id.split(':')[0] : null
  const mapped = remap[bare] || bare
  return pre ? `${pre}:${mapped}` : mapped
}

// ---- Author: one owner per file, so parallel writes cannot collide ----
const AUTHOR_BATCH = 4
const atomBatches = []
for (let i = 0; i < keptAtoms.length; i += AUTHOR_BATCH) atomBatches.push(keptAtoms.slice(i, i + AUTHOR_BATCH))
const mechBatches = []
for (let i = 0; i < keptMechs.length; i += AUTHOR_BATCH) mechBatches.push(keptMechs.slice(i, i + AUTHOR_BATCH))

phase('Author')
const authored = await parallel([
  ...atomBatches.map((batch, i) => () => agent(
    `Write ${batch.length} NEW concept atom note(s) into the knowledge graph.

${FORMAT_REF}

Write each to ${ROOT}/library/concepts/<atom_type-plural>/<id>.md  (methods/metrics/datasets/models/terms -- note the directory is the PLURAL form).

SKIP IF EXISTS: if the target file is already on disk, do NOT overwrite it; report it as skipped. Never clobber an existing atom.

Frontmatter must be exactly the canonical shape: aliases, tags (kg/<type>, concept, <type>), kg: {id: <type>:<slug>, type, status: canonical}, area, related (wikilinks), relationships (typed edges with target/target_id/confidence). Body: the 2-4 sentence definition, then a "**Why it matters here:**" line tying it to abstention/calibration/hallucination/steering, then "**Lineage:**".

Every wikilink target you emit must be a real slug -- an existing vault atom (check ${INV}), one of the atoms in this batch, or a paper note stem. A dangling link fails validation downstream.

ATOMS TO WRITE:
${JSON.stringify(batch, null, 1)}

${TERMS}

Return a one-line-per-file summary of what you wrote or skipped.`,
    { label: `author:atoms-${i + 1}`, phase: 'Author', model: 'sonnet' }
  )),
  ...mechBatches.map((batch, i) => () => agent(
    `Write ${batch.length} NEW mechanism note(s) into the knowledge graph.

${FORMAT_REF}

Write each to ${ROOT}/library/concepts/mechanisms/<id>.md

SKIP IF EXISTS: never overwrite an existing mechanism file; report it as skipped.

Frontmatter: aliases, tags (kg/mechanism, concept, mechanism), kg: {id: mechanism:<slug>, type: mechanism, status: canonical}, cause, effect, polarity, related, relationships (supported_by the paper note stems in \`sources\`, related_to the atoms in relatedAtomIds). Body: 1-3 sentences on what the paper found and the evidence.

Every wikilink target must resolve: an existing vault slug (check ${INV}), a newly authored atom, or a paper note stem of the form <arxiv>--<slug>.

MECHANISMS TO WRITE:
${JSON.stringify(batch, null, 1)}

${TERMS}

Return a one-line-per-file summary.`,
    { label: `author:mechs-${i + 1}`, phase: 'Author', model: 'sonnet' }
  )),
])

// ---- Patch: per-paper, so no two agents touch the same note ----
phase('Patch')
const patched = await parallel(extracted.map(e => () => {
  const p = PAPERS.find(x => x.arxiv === e.arxiv)
  if (!p) return Promise.resolve(null)
  const edges = (e.paperEdges || []).map(x => ({ ...x, targetId: canon(x.targetId) }))
  return agent(
    `Patch ONE paper note with its knowledge-graph edges and claims.

Note: ${ROOT}/library/notes/${p.noteStem}.md
${FORMAT_REF}

Into the note's EXISTING frontmatter (between the --- fences) add:
- \`kg:\` block -> {id: paper:${e.arxiv}, type: paper, status: canonical}
- \`related:\` -> a wikilink for every edge target below
- \`relationships:\` -> one entry per edge: {type, target: '[[<slug>]]', target_id: '<type>:<slug>', confidence}
- add \`kg/paper\` to tags

Then append a "## Claims" section, one bullet per claim, formatted:
- Evidence label: <kind>. <claim, with its table/figure/section cite>.

EDGES (targets already canonicalized -- use them verbatim):
${JSON.stringify(edges, null, 1)}

CLAIMS:
${JSON.stringify(e.claims || [], null, 1)}

Preserve everything already in the note (abstract, summary sections). Do not rewrite prose you did not add. Every wikilink must resolve to a real atom/mechanism slug or paper stem.

${TERMS}

Return a one-line confirmation.`,
    { label: `patch:${e.arxiv}`, phase: 'Patch', model: 'sonnet' }
  )
}))

return {
  papersExtracted: extracted.length,
  atomsKept: keptAtoms.map(a => `${a.atom_type}:${a.id}`),
  mechanismsKept: keptMechs.map(m => m.id),
  merged: rejected,
  extractionNotes: extracted.filter(e => e.notes).map(e => ({ arxiv: e.arxiv, notes: e.notes })),
  authorSummaries: authored.filter(Boolean),
  patchSummaries: patched.filter(Boolean),
}
