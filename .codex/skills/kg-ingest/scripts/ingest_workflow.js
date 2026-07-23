export const meta = {
  name: 'kg-ingest',
  description: 'Agents-K1 style ingestion: integrate new library paper(s) into the atomic knowledge graph',
  phases: [
    { title: 'Extract', detail: 'one Sonnet agent per paper returns typed atoms/edges/mechanisms/claims' },
    { title: 'Resolve', detail: 'deterministic slug clustering + lightweight synonym-merge against the on-disk vault' },
    { title: 'Author', detail: 'batched Sonnet agents write only the genuinely new concept notes' },
  ],
  model: 'sonnet',
}

// ---- inputs ----
const A = typeof args === 'string' ? JSON.parse(args) : args
const ROOT = A.repoRoot
const PAPERS = A.papers                      // [{arxiv, noteStem, src}]  src = repo-relative path or 'none'
const EXISTING = A.existing || { atoms: [], mechanisms: [] }
const existingAtomIds = new Set((EXISTING.atoms || []).map(a => a.id))
const existingMechIds = new Set((EXISTING.mechanisms || []).map(m => m.id))
const FORMAT_REF = `Read ${ROOT}/library/SCHEMA.md and the gold exemplar ${ROOT}/library/concepts/methods/direct-preference-optimization.md to learn the node kinds, controlled relation vocabulary, and frontmatter format before doing anything.`

const EXTRACT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    arxiv: { type: 'string' },
    atoms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      raw_id: { type: 'string', description: 'canonical kebab-case slug; reuse the obvious slug so shared concepts collide (e.g. expected-calibration-error)' },
      display: { type: 'string' },
      atom_type: { type: 'string', enum: ['method','metric','dataset','model','term'] },
      aliases: { type: 'array', items: { type: 'string' } },
      area: { type: 'string' },
      definition: { type: 'string' },
      introduced_here: { type: 'boolean' },
    }, required: ['raw_id','display','atom_type','aliases','area','definition','introduced_here'] } },
    paper_edges: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      relation: { type: 'string', enum: ['proposes','uses-method','evaluates-on','measures','evaluates','studies'] },
      target_raw: { type: 'string' },
    }, required: ['relation','target_raw'] } },
    lineage: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      src_raw: { type: 'string' },
      relation: { type: 'string', enum: ['extends','derives-from','variant-of','prerequisite-of','related'] },
      dst_raw: { type: 'string' },
    }, required: ['src_raw','relation','dst_raw'] } },
    mechanisms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      raw_id: { type: 'string' }, display: { type: 'string' },
      cause: { type: 'string' }, effect: { type: 'string' },
      polarity: { type: 'string', enum: ['increases','decreases','enables','prevents'] },
      claim: { type: 'string' },
    }, required: ['raw_id','display','cause','effect','polarity','claim'] } },
    claims: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      statement: { type: 'string' }, target_raw: { type: 'string' }, source: { type: 'string' },
    }, required: ['statement','target_raw','source'] } },
  },
  required: ['arxiv','atoms','paper_edges','lineage','mechanisms','claims'],
}

// ---- Extract: one agent per paper, structured returns, NO file writes ----
phase('Extract')
const extracted = await parallel(PAPERS.map(p => () => agent(
  `You are extracting an agent-native knowledge subgraph from ONE paper for an Obsidian research vault on epistemic humility in LLMs.

${FORMAT_REF}

PAPER: arXiv ${p.arxiv}
Paper note: ${ROOT}/library/notes/${p.noteStem}.md  (read this FIRST: abstract + frontmatter)
Source material: ${p.src === 'none' ? 'NONE beyond the note: rely on the note + abstract; only assert well-established facts.' : ROOT + '/' + p.src + '  (use Grep/targeted Read for method/dataset/metric names and key result numbers; do NOT read the whole file blindly)'}

Extract ONLY the concepts genuinely central to THIS paper (aim 3-8 atoms, not a dump). Use the obvious canonical kebab-case slug as raw_id so shared concepts collide on one string. introduced_here=true ONLY for atoms this paper proposes. paper_edges connect the paper to its atoms (proposes/uses-method/evaluates-on/measures/evaluates/studies); target_raw must be one of your raw_ids. lineage = method-to-method edges you can support. mechanisms = causal cause->effect findings this paper evidences. claims = 1-4 key findings with a number + table/figure source. Return ONLY the structured object; write no files.`,
  { label: `extract:${p.arxiv}`, phase: 'Extract', model: 'sonnet', schema: EXTRACT_SCHEMA }
)))
const goodEx = extracted.filter(Boolean)
log(`Extracted ${goodEx.length}/${PAPERS.length} papers`)

// ---- Resolve: deterministic clustering + lightweight synonym-merge reconciled vs the on-disk vault ----
phase('Resolve')
const top = obj => Object.entries(obj).sort((x, y) => y[1] - x[1])[0]?.[0]

const rawAtoms = {}
for (const ex of goodEx) for (const a of (ex.atoms || [])) {
  const r = rawAtoms[a.raw_id] ||= { type: {}, area: {}, aliases: new Set(), defs: [], introBy: new Set() }
  r.type[a.atom_type] = (r.type[a.atom_type] || 0) + 1
  if (a.area) r.area[a.area] = (r.area[a.area] || 0) + 1
  ;(a.aliases || []).forEach(x => r.aliases.add(x))
  if (a.display) r.aliases.add(a.display)
  if (a.definition) r.defs.push(a.definition)
  if (a.introduced_here) r.introBy.add(ex.arxiv)
}
const prelim = Object.entries(rawAtoms).map(([id, r]) => ({
  id, atom_type: top(r.type) || 'term', area: top(r.area) || '',
  aliases: [...r.aliases].filter(a => a && a.toLowerCase() !== id.replace(/-/g, ' ').toLowerCase()),
  definition: r.defs.sort((a, b) => b.length - a.length)[0] || '',
  introduced_by_arxiv: [...r.introBy][0] || '',
}))

const MERGE_SCHEMA = { type: 'object', additionalProperties: false, properties: {
  merges: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
    canonical: { type: 'string', description: 'the kept id; prefer an EXISTING vault id when the concept already exists' },
    duplicates: { type: 'array', items: { type: 'string' } },
  }, required: ['canonical', 'duplicates'] } },
}, required: ['merges'] }

// candidate atoms reconcile against existing atom inventory (compact: id+type+aliases)
const existingAtomCompact = (EXISTING.atoms || []).map(a => ({ id: a.id, type: a.type, aliases: a.aliases || [] }))
const atomMerge = await agent(
  `Knowledge graph on epistemic humility in LLMs. NEW candidate atom ids (with type+aliases) are being ingested. Merge groups where (a) two NEW candidates are the same concept, or (b) a NEW candidate is the same concept as an EXISTING vault atom. When merging a new candidate into an existing concept, set canonical to the EXISTING id so we reuse it (do NOT mint a duplicate). Only merge genuine same-concept duplicates; keep related-but-distinct concepts separate (DPO vs KTO; ECE vs Brier). Most ids will not merge. Return only the structured object; write no files.

EXISTING vault atoms: ${JSON.stringify(existingAtomCompact)}
NEW candidates: ${JSON.stringify(prelim.map(a => ({ id: a.id, type: a.atom_type, aliases: a.aliases })))}`,
  { label: 'resolve:atoms', phase: 'Resolve', model: 'sonnet', schema: MERGE_SCHEMA }
)
const remap = {}
for (const m of (atomMerge?.merges || [])) for (const d of (m.duplicates || [])) if (d !== m.canonical) remap[d] = m.canonical
const finalId = id => remap[id] || id
const mergedById = {}
for (const a of prelim) {
  const cid = finalId(a.id)
  const t = mergedById[cid] ||= { id: cid, atom_type: a.atom_type, area: a.area, aliases: new Set(), definition: a.definition, introduced_by_arxiv: a.introduced_by_arxiv, lineage: [] }
  a.aliases.forEach(x => t.aliases.add(x))
  if (a.id !== cid) t.aliases.add(a.id.replace(/-/g, ' '))
  if (a.definition && a.definition.length > (t.definition?.length || 0)) t.definition = a.definition
  if (!t.introduced_by_arxiv && a.introduced_by_arxiv) t.introduced_by_arxiv = a.introduced_by_arxiv
}
for (const ex of goodEx) for (const l of (ex.lineage || [])) {
  const s = finalId(l.src_raw), d = finalId(l.dst_raw)
  if (mergedById[s] && s !== d && !mergedById[s].lineage.some(e => e.relation === l.relation && e.target_id === d))
    mergedById[s].lineage.push({ relation: l.relation, target_id: d })
}
const atoms = Object.values(mergedById).map(a => ({ ...a, aliases: [...a.aliases] }))

// mechanisms: aggregate by slug, then the SAME synonym-merge step (atoms gotcha applies here too)
const rawMech = {}
for (const ex of goodEx) for (const m of (ex.mechanisms || [])) {
  const r = rawMech[m.raw_id] ||= { aliases: new Set(), cause: m.cause, effect: m.effect, polarity: m.polarity, sup: new Set() }
  if (m.display) r.aliases.add(m.display)
  r.sup.add(ex.arxiv)
}
const prelimMech = Object.entries(rawMech).map(([id, r]) => ({ id, aliases: [...r.aliases], cause: r.cause, effect: r.effect, polarity: r.polarity, sup: [...r.sup] }))
const existingMechCompact = (EXISTING.mechanisms || []).map(m => ({ id: m.id, aliases: m.aliases || [] }))
const mechMerge = prelimMech.length ? await agent(
  `Causal MECHANISM nodes (cause->effect) for a knowledge graph on epistemic humility in LLMs. Merge mechanism ids that state the SAME causal claim, including merging a NEW mechanism into an EXISTING vault mechanism (set canonical to the existing id). Keep distinct causal claims separate. Return only the structured object; write no files.

EXISTING vault mechanisms: ${JSON.stringify(existingMechCompact)}
NEW candidates: ${JSON.stringify(prelimMech.map(m => ({ id: m.id, aliases: m.aliases })))}`,
  { label: 'resolve:mechanisms', phase: 'Resolve', model: 'sonnet', schema: MERGE_SCHEMA }
) : { merges: [] }
const mremap = {}
for (const m of (mechMerge?.merges || [])) for (const d of (m.duplicates || [])) if (d !== m.canonical) mremap[d] = m.canonical
const mFinal = id => mremap[id] || id
const mechById = {}
for (const m of prelimMech) {
  const cid = mFinal(m.id)
  const t = mechById[cid] ||= { id: cid, aliases: new Set(), cause: m.cause, effect: m.effect, polarity: m.polarity, sup: new Set() }
  m.aliases.forEach(x => t.aliases.add(x))
  if (m.id !== cid) t.aliases.add(m.id.replace(/-/g, ' '))
  m.sup.forEach(s => t.sup.add(s))
}
const mechanisms = Object.values(mechById).map(m => ({ id: m.id, aliases: [...m.aliases], cause: m.cause, effect: m.effect, polarity: m.polarity, supported_by_arxiv: [...m.sup] }))

// alias maps for deterministic paper-edge rewriting
const amap = {}
for (const a of prelim) amap[a.id] = finalId(a.id)
for (const m of prelimMech) amap[m.id] = mFinal(m.id)
const canon = (raw) => amap[raw] || raw
log(`Resolved ${atoms.length} atoms (${atoms.filter(a => !existingAtomIds.has(a.id)).length} new) + ${mechanisms.length} mechanisms`)

// ---- Author: write only the genuinely new notes ----
const paperIndex = Object.fromEntries(PAPERS.map(p => [p.arxiv, p.noteStem]))
const atomById = Object.fromEntries(atoms.map(a => [a.id, a]))
const typeDir = { method: 'methods', metric: 'metrics', dataset: 'datasets', model: 'models', term: 'terms' }
const allValidIds = new Set([...atoms.map(a => a.id), ...mechanisms.map(m => m.id), ...existingAtomIds, ...existingMechIds])
const chunk = (arr, n) => { const o = []; for (let i = 0; i < arr.length; i += n) o.push(arr.slice(i, i + n)); return o }

const newAtoms = atoms.filter(a => !existingAtomIds.has(a.id))
const newMechs = mechanisms.filter(m => !existingMechIds.has(m.id))

phase('Author')
const writeJobs = chunk(newAtoms, 5).map((batch, i) => () => agent(
  `Author atomic concept notes for an Obsidian research vault. ${FORMAT_REF}

Write each atom below as ${ROOT}/library/concepts/<dir>/<id>.md where <dir> is method->methods, metric->metrics, dataset->datasets, model->models, term->terms. For EACH atom: Read the target path first and SKIP it if it already exists with content (do not overwrite). Frontmatter per the Entity template (id, type, aliases, area, introduced-by as a wikilink to the paper note stem from PAPER_NOTE_STEMS if introduced_by_arxiv is set, the lineage edges as wikilink lists to other atom ids, tags: [concept, <type>]). Body: 2-4 sentence definition + how it works, a short "Why it matters here" line tying to epistemic humility when relevant, then a lineage line. Only use [[wikilinks]] whose target is in VALID_IDS or PAPER_NOTE_STEMS. NEVER use em dashes (use colons, parentheses, commas, sentence breaks). Do not use the phrase "load-bearing". Return a one-line summary of files created vs skipped.

VALID_IDS: ${JSON.stringify([...allValidIds])}
PAPER_NOTE_STEMS: ${JSON.stringify(paperIndex)}
ATOMS (batch ${i + 1}): ${JSON.stringify(batch)}`,
  { label: `author:atoms-${i + 1}`, phase: 'Author', model: 'sonnet' }
))
const mechJob = newMechs.length ? [() => agent(
  `Author atomic MECHANISM notes (causal cause->effect) for an Obsidian research vault. ${FORMAT_REF}

Write each mechanism as ${ROOT}/library/concepts/mechanisms/<id>.md using the Mechanism template (id, type: mechanism, aliases, cause, effect, polarity, supported-by as wikilinks to the note stems in PAPER_NOTE_STEMS, contradicted-by: [], tags: [concept, mechanism]). cause/effect may embed [[wikilinks]] to ids in VALID_IDS. Body: 2-3 sentences stating the causal claim and its evidence. Read the target path first and skip if it exists. No em dashes; avoid "load-bearing". Return a one-line summary.

VALID_IDS: ${JSON.stringify([...allValidIds])}
PAPER_NOTE_STEMS: ${JSON.stringify(paperIndex)}
MECHANISMS: ${JSON.stringify(newMechs)}`,
  { label: 'author:mechanisms', phase: 'Author', model: 'sonnet' }
)] : []
await parallel([...writeJobs, ...mechJob])

// ---- Deterministic paper-note frontmatter patches (applied by apply_kg_patches.py) ----
const REL_KEYS = ['proposes', 'uses-method', 'evaluates-on', 'measures', 'evaluates', 'studies']
const wl = id => `"[[${id}]]"`
const mechByIdMap = Object.fromEntries(mechanisms.map(m => [m.id, m]))
const paperPatches = goodEx.map(ex => {
  const byRel = {}
  for (const e of (ex.paper_edges || [])) {
    const cid = canon(e.target_raw)
    if (!atomById[cid] && !existingAtomIds.has(cid)) continue
    ;(byRel[e.relation] ||= new Set()).add(cid)
  }
  const mechIds = [...new Set((ex.mechanisms || []).map(m => canon(m.raw_id)).filter(id => mechByIdMap[id] || existingMechIds.has(id)))]
  const yamlLines = []
  for (const k of REL_KEYS) if (byRel[k]?.size) yamlLines.push(`${k}: [${[...byRel[k]].map(wl).join(', ')}]`)
  if (mechIds.length) yamlLines.push(`mechanisms: [${mechIds.map(wl).join(', ')}]`)
  const claimLines = (ex.claims || []).filter(c => c.statement).map(c => {
    const cid = c.target_raw ? canon(c.target_raw) : ''
    const link = cid && (atomById[cid] || existingAtomIds.has(cid)) ? ` [[${cid}]]` : ''
    const src = c.source ? ` (${c.source})` : ''
    return `- ${c.statement}${src}${link}`
  })
  return { arxiv: ex.arxiv, noteStem: paperIndex[ex.arxiv], yamlBlock: yamlLines.join('\n'), claimsBlock: claimLines.join('\n') }
})

// existing mechanisms that gained new paper support -> apply_kg_patches unions these into their files
const existingMechSupport = mechanisms
  .filter(m => existingMechIds.has(m.id))
  .map(m => ({ id: m.id, arxiv: m.supported_by_arxiv }))

return {
  stats: { papers: goodEx.length, atoms: atoms.length, new_atoms: newAtoms.length, mechanisms: mechanisms.length, new_mechanisms: newMechs.length },
  newAtoms: newAtoms.map(a => ({ id: a.id, dir: typeDir[a.atom_type] })),
  newMechanisms: newMechs.map(m => ({ id: m.id })),
  existingMechSupport,
  paperPatches,
}
