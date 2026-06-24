export const meta = {
  name: 'enrich-cluster',
  description: 'Enrich a cluster of skeleton paper notes: extract -> adversarial verify -> revise into an applier-ready artifact, all on Sonnet 4.6. Papers and paths come from args; feed the return to enrich_apply.py.',
  phases: [
    { title: 'Extract', detail: 'Sonnet reads fulltext + note + exemplars', model: 'sonnet' },
    { title: 'Verify', detail: 'Sonnet adversarially re-checks every number', model: 'sonnet' },
    { title: 'Revise', detail: 'Sonnet folds verify corrections into the final artifact', model: 'sonnet' },
  ],
}

// args: { root: "<abs repo root>", textDir: "<abs dir of clean <arxiv>.md fulltext>",
//         papers: [{ arxiv, note }], exemplars?: [<abs note paths>] }
// Tolerate a stringified args (some callers pass JSON as a string).
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
A = A || {}
const ROOT = A.root
const TEXTDIR = A.textDir
const EXEMPLARS = A.exemplars || [
  `${ROOT}/library/notes/2606.24790--grad-detect-gradient-hallucination-detection.md`,
  `${ROOT}/library/notes/2306.03341--inference-time-intervention.md`,
]
const PAPERS = (A.papers || []).map(p => ({
  ...p, notePath: `${ROOT}/${p.note}`, text: `${TEXTDIR}/${p.arxiv}.md`,
}))

const EXTRACT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    arxiv: { type: 'string' },
    summary: { type: 'string' },
    extracted_numbers: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      claim: { type: 'string' }, source_citation: { type: 'string' } }, required: ['claim','source_citation'] } },
    relevance_to_experiment: { type: 'string' },
    new_atoms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      atom_type: { type: 'string', enum: ['method','metric','dataset','model','term'] },
      slug: { type: 'string' }, display: { type: 'string' }, definition: { type: 'string' },
      why_matters: { type: 'string' }, lineage: { type: 'string' } },
      required: ['atom_type','slug','display','definition','why_matters','lineage'] } },
    new_mechanisms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      slug: { type: 'string' }, cause: { type: 'string' }, effect: { type: 'string' },
      polarity: { type: 'string', enum: ['increases','decreases','enables','prevents','mediates'] }, note: { type: 'string' } },
      required: ['slug','cause','effect','polarity','note'] } },
    missing_edges: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      edge_type: { type: 'string', enum: ['proposes','uses','evaluates_on','measures','studies','supports'] },
      target_slug: { type: 'string' }, target_type: { type: 'string', enum: ['method','metric','dataset','model','term','mechanism'] },
      confidence: { type: 'string', enum: ['high','medium','low'] }, rationale: { type: 'string' } },
      required: ['edge_type','target_slug','target_type','confidence','rationale'] } },
  },
  required: ['arxiv','summary','extracted_numbers','relevance_to_experiment','new_atoms','new_mechanisms','missing_edges'],
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    arxiv: { type: 'string' },
    number_checks: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      claim: { type: 'string' }, verdict: { type: 'string', enum: ['confirmed','rejected','uncertain'] },
      located_at: { type: 'string' }, note: { type: 'string' } }, required: ['claim','verdict','located_at','note'] } },
    summary_verdict: { type: 'string', enum: ['ok','issues'] }, summary_issues: { type: 'string' },
    relevance_verdict: { type: 'string', enum: ['ok','issues'] }, relevance_issues: { type: 'string' },
    overall: { type: 'string' },
  },
  required: ['arxiv','number_checks','summary_verdict','summary_issues','relevance_verdict','relevance_issues','overall'],
}

const REVISE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    arxiv: { type: 'string' },
    summary: { type: 'string' },
    provenance: { type: 'string', description: 'Provenance line for Extracted numbers. Reference the DURABLE source `library/fulltext/<arxiv>.html` (or `library/pdfs/<arxiv>.pdf` if no HTML render exists). NEVER reference a /private/tmp or scratchpad path. Name the key tables/figures and add "verified against the source on <date>". Note whether numbers fit the effects.csv schema.' },
    numbers: { type: 'array', items: { type: 'string' }, description: 'Final number bullets (NO leading dash), each ending with its (Table/Figure/Section) citation. Drop rejected; keep uncertain with an inline flag; apply every verify correction.' },
    relevance: { type: 'string' },
    claims: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      text: { type: 'string' }, source: { type: 'string', description: 'Table/Figure/Section cite (no parens, not the arxiv id)' },
      link: { type: 'string', description: 'bare slug of the primary atom/mechanism (no [[ ]], no path); empty string if none' } },
      required: ['text','source','link'] } },
    new_atoms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      atom_type: { type: 'string', enum: ['method','metric','dataset','model','term'] },
      slug: { type: 'string' }, display: { type: 'string' }, aliases: { type: 'array', items: { type: 'string' } },
      definition: { type: 'string' }, why_matters: { type: 'string' }, lineage: { type: 'string' },
      related: { type: 'array', items: { type: 'string' }, description: 'bare slugs of EXISTING atoms (no brackets/paths)' } },
      required: ['atom_type','slug','display','aliases','definition','why_matters','lineage','related'] } },
    new_mechanisms: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      slug: { type: 'string' }, aliases: { type: 'array', items: { type: 'string' } },
      cause: { type: 'string' }, effect: { type: 'string' },
      polarity: { type: 'string', enum: ['increases','decreases','enables','prevents','mediates'] },
      body: { type: 'string' }, related: { type: 'array', items: { type: 'string' } } },
      required: ['slug','aliases','cause','effect','polarity','body','related'] } },
    edges: { type: 'array', items: { type: 'object', additionalProperties: false, properties: {
      edge_type: { type: 'string', enum: ['proposes','uses','evaluates_on','measures','studies','supports'] },
      target_slug: { type: 'string', description: 'bare slug (no [[ ]], no path)' }, confidence: { type: 'string', enum: ['high','medium','low'] } },
      required: ['edge_type','target_slug','confidence'] } },
  },
  required: ['arxiv','summary','provenance','numbers','relevance','claims','new_atoms','new_mechanisms','edges'],
}

const EX = `House-style exemplars (READ BOTH): ${EXEMPLARS[0]} and ${EXEMPLARS[1]}. Match their Summary / Extracted-numbers (with a Provenance line) / Relevance / Claims depth and tone.`
const LS = `ls ${ROOT}/library/concepts/methods ${ROOT}/library/concepts/metrics ${ROOT}/library/concepts/datasets ${ROOT}/library/concepts/models ${ROOT}/library/concepts/terms ${ROOT}/library/concepts/mechanisms`

const results = await pipeline(
  PAPERS,
  (p) => agent(
    `Enrich a paper note in an epistemic-humility KG vault. ROOT ${ROOT}. Paper arXiv ${p.arxiv}.\n` +
    `Clean fulltext: ${p.text}\nExisting note: ${p.notePath}\n\n${EX}\n\n` +
    `Read the note + both exemplars + the fulltext (large; page and grep "Table"/"Figure"/results). ` +
    `Before proposing new atoms/mechanisms run: ${LS} -- only propose slugs that do NOT already exist; prefer reusing existing slugs via missing_edges. ` +
    `EVERY number must cite its exact Table/Figure/Section; omit what you cannot cite. No em dashes; never use the phrase "load-bearing". Return the structured object only; write nothing.`,
    { label: `extract:${p.arxiv}`, phase: 'Extract', model: 'sonnet', schema: EXTRACT_SCHEMA }
  ),
  (ext, p) => agent(
    `Adversarial verification, ROOT ${ROOT}, paper arXiv ${p.arxiv}. Clean fulltext: ${p.text}\n\n` +
    `Another agent extracted this. REFUTE, do not rubber-stamp.\nEXTRACT:\n${JSON.stringify(ext)}\n\n` +
    `For each extracted_numbers item: locate it at its cited Table/Figure/Section. confirmed only if number AND location both check out; rejected if wrong/mislocated/absent; uncertain if ambiguous. Default to rejected/uncertain when unsure. Sanity-check summary and relevance for unsupported claims. Return the structured verdict.`,
    { label: `verify:${p.arxiv}`, phase: 'Verify', model: 'sonnet', schema: VERIFY_SCHEMA }
  ),
  (vrf, p) => agent(
    `Produce the FINAL enrichment artifact for arXiv ${p.arxiv}. ROOT ${ROOT}. Clean fulltext: ${p.text}\nExisting note: ${p.notePath}\n${EX}\n\n` +
    `Given the extract and its adversarial verification, fold ALL corrections in:\n` +
    `- Drop every number with verdict=rejected. Keep verdict=uncertain numbers but add a short inline flag. Apply every correction the verifier described.\n` +
    `- Fix any summary/relevance issues raised.\nVERIFY:\n${JSON.stringify(vrf)}\n\n` +
    `Assemble: summary; a provenance line referencing the durable library/fulltext/${p.arxiv}.html (NOT any /private/tmp path); final number bullets (no leading dash, each cited); relevance; 3-5 claims (each linking the BARE slug of its primary atom/mechanism, no brackets/paths, and a Table/Figure/Section source, never the arxiv id); genuinely-new atoms and mechanisms (carry forward only those confirmed absent via ${LS}; include aliases/related as bare slugs); and paper-level edges (proposes/supports to new atoms+mechs, uses/evaluates_on/measures/studies to existing). ` +
    `Every edge target_slug, claim link, and atom related[] must be a BARE existing concept slug OR one of your new_atoms/new_mechanisms. No em dashes; no "load-bearing".`,
    { label: `revise:${p.arxiv}`, phase: 'Revise', model: 'sonnet', schema: REVISE_SCHEMA }
  ).then(r => ({ ...r, arxiv: p.arxiv, note_path: p.note }))
)

return results.filter(Boolean)
