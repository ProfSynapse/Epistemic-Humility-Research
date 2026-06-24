#!/usr/bin/env python3
"""Deterministically apply enrichment artifacts (revise-stage output) to the vault.

Companion to `enrich_cluster.js`. Input is a JSON file = list of per-paper
artifacts (the workflow's return value). For each paper:
  - splice Summary / Extracted numbers / Relevance into the note body (replacing
    the stub comments left by Move 0);
  - if the note is PRE-GRAPH (no `kg:` block): write new atom/mechanism files
    (skip-if-exists), add the kg block + related + relationships to frontmatter,
    add the kg/paper tag, and append a ## Claims section.
Body-only notes (already carrying a kg: block) get only the three body sections;
their existing graph and Claims are left untouched.

Robustness (so a large cluster never writes a dangling link):
  - agent slugs are normalized (strip [[ ]], a library/concepts/<type>/ path, .md);
  - edge / claim-link / related targets are resolved against on-disk concepts plus
    this batch's new atoms/mechanisms; unresolved edges are dropped, unresolved
    claim links are blanked;
  - a bare arxiv-id in a claim `source` is dropped (the cite is inline in the text);
  - cross-paper duplicate new slugs collapse to one file (first definition wins).

Run from the repo root, or set REPO_ROOT. Usage: enrich_apply.py <artifacts.json>
"""
import json, os, re, sys, glob

ROOT = os.environ.get("REPO_ROOT") or os.getcwd()
ID_RE = re.compile(r'^\d{4}\.\d{4,5}$')

CONCEPT_DIRS = ["methods", "metrics", "datasets", "models", "terms", "mechanisms"]
DIR_FOR_TYPE = {"method": "methods", "metric": "metrics", "dataset": "datasets",
                "model": "models", "term": "terms", "mechanism": "mechanisms"}

STUB_SUMMARY = "## Summary\n\n<!-- filled during extraction -->"
STUB_NUMBERS = "## Extracted numbers\n\n<!-- rows feeding meta-analysis/evidence/*.csv; cite table/figure of origin -->"
STUB_RELEVANCE = "## Relevance to experiment\n\n<!-- how this informs the Synaptic Tuner experiment design -->"


def norm_slug(s):
    """Strip [[ ]], a library/concepts/<type>/ path prefix, and a .md suffix."""
    if not s:
        return ""
    s = s.strip().strip('[]').strip()
    s = re.sub(r'^library/concepts/[a-z]+/', '', s)
    if s.endswith('.md'):
        s = s[:-3]
    return s.strip()


def clean_source(src):
    """Drop a bare arxiv-id source (cite is then inline in the claim text)."""
    src = (src or "").strip().strip('()')
    return "" if ID_RE.match(src) else src


def build_type_index(batch):
    """slug -> type. Read each concept's real kg.id namespace (robust to a file
    living in the 'wrong' directory); fall back to the directory if absent."""
    idx = {}
    id_re = re.compile(r'^\s*id:\s*([a-z]+):', re.M)
    for d in CONCEPT_DIRS:
        dir_t = "mechanism" if d == "mechanisms" else d[:-1]
        for p in glob.glob(os.path.join(ROOT, "library/concepts", d, "*.md")):
            with open(p, errors="ignore") as fh:
                m = id_re.search(fh.read(600))
            idx[os.path.basename(p)[:-3]] = m.group(1) if m else dir_t
    for art in batch:
        if not art:
            continue
        for a in art.get("new_atoms", []):
            idx.setdefault(norm_slug(a["slug"]), a["atom_type"])  # keep first/existing
        for m in art.get("new_mechanisms", []):
            idx.setdefault(norm_slug(m["slug"]), "mechanism")
    return idx


def yaml_list(items):
    return "".join(f"- '[[{s}]]'\n" for s in items)


def write_atom(a, type_idx, arxiv, note_stem):
    slug = norm_slug(a["slug"])
    d = DIR_FOR_TYPE[a["atom_type"]]
    path = os.path.join(ROOT, "library/concepts", d, slug + ".md")
    if os.path.exists(path):
        return f"  skip atom (exists): {slug}"
    aliases = a.get("aliases") or [a["display"]]
    rel_slugs = [s for s in (norm_slug(x) for x in a.get("related", []))
                 if s and s in type_idx and s != slug]
    related = [note_stem] + rel_slugs
    rels = [f"- type: proposed_by\n  target: '[[{note_stem}]]'\n  target_id: paper:{arxiv}\n  confidence: high\n"]
    for s in rel_slugs:
        rels.append(f"- type: related_to\n  target: '[[{s}]]'\n  target_id: {type_idx[s]}:{s}\n  confidence: medium\n")
    body = a["definition"].strip() + "\n\n**Why it matters here:** " + a["why_matters"].strip() + \
           "\n\n**Lineage:** " + a["lineage"].strip() + "\n"
    fm = ("---\naliases:\n" + "".join(f"- {x}\n" for x in aliases) +
          f"tags:\n- kg/{a['atom_type']}\n- concept\n- {a['atom_type']}\n" +
          f"kg:\n  id: {a['atom_type']}:{slug}\n  type: {a['atom_type']}\n  status: canonical\n" +
          f"area: {DIR_FOR_TYPE[a['atom_type']]}\n" +
          "related:\n" + yaml_list(related) + "relationships:\n" + "".join(rels) + "---\n\n")
    open(path, "w").write(fm + body)
    return f"  WROTE atom: {slug}"


def write_mech(m, type_idx, arxiv, note_stem):
    slug = norm_slug(m["slug"])
    path = os.path.join(ROOT, "library/concepts/mechanisms", slug + ".md")
    if os.path.exists(path):
        return f"  skip mech (exists): {slug}"
    aliases = m.get("aliases") or [slug.replace("-", " ")]
    rel_slugs = [s for s in (norm_slug(x) for x in m.get("related", []))
                 if s and s in type_idx and s != slug]
    related = [note_stem] + rel_slugs
    rels = [f"- type: supported_by\n  target: '[[{note_stem}]]'\n  target_id: paper:{arxiv}\n  confidence: high\n"]
    for s in rel_slugs:
        rels.append(f"- type: related_to\n  target: '[[{s}]]'\n  target_id: {type_idx[s]}:{s}\n  confidence: high\n")
    fm = ("---\naliases:\n" + "".join(f"- {x}\n" for x in aliases) +
          "tags:\n- kg/mechanism\n- concept\n- mechanism\n" +
          f"kg:\n  id: mechanism:{slug}\n  type: mechanism\n  status: canonical\n" +
          f"cause: {json.dumps(m['cause'].strip())}\n" +
          f"effect: {json.dumps(m['effect'].strip())}\n" +
          f"polarity: {m['polarity']}\n" +
          "related:\n" + yaml_list(related) + "relationships:\n" + "".join(rels) + "---\n\n")
    open(path, "w").write(fm + m["body"].strip() + "\n")
    return f"  WROTE mech: {slug}"


def patch_note(art, type_idx):
    note_path = os.path.join(ROOT, art["note_path"])
    txt = open(note_path).read()
    note_stem = os.path.basename(note_path)[:-3]
    arxiv = art["arxiv"]
    logs = []

    nums = "\n".join("- " + b.strip() for b in art["numbers"])
    numbers_block = "## Extracted numbers\n\n" + art["provenance"].strip() + "\n\n" + nums
    for stub, repl in [(STUB_SUMMARY, "## Summary\n\n" + art["summary"].strip()),
                       (STUB_NUMBERS, numbers_block),
                       (STUB_RELEVANCE, "## Relevance to experiment\n\n" + art["relevance"].strip())]:
        if stub not in txt:
            logs.append(f"  WARN stub missing: {stub.splitlines()[0]}")
        txt = txt.replace(stub, repl)

    pregraph = not re.search(r'^kg:', txt, re.M)

    if pregraph:
        for a in art.get("new_atoms", []):
            logs.append(write_atom(a, type_idx, arxiv, note_stem))
        for m in art.get("new_mechanisms", []):
            logs.append(write_mech(m, type_idx, arxiv, note_stem))

        edges, related, seen = [], [], set()
        for e in art.get("edges", []):
            ts = norm_slug(e["target_slug"])
            tt = type_idx.get(ts)
            if not tt or ts in seen:
                if not tt:
                    logs.append(f"  DROP edge (unresolved): {e['edge_type']} -> {ts}")
                continue
            seen.add(ts)
            related.append(ts)
            edges.append(f"- type: {e['edge_type']}\n  target: '[[{ts}]]'\n"
                         f"  target_id: {tt}:{ts}\n  confidence: {e.get('confidence','medium')}\n")
        kg_block = (f"kg:\n  id: paper:{arxiv}\n  type: paper\n  status: canonical\n"
                    "related:\n" + yaml_list(related) + "relationships:\n" + "".join(edges))

        m = re.match(r'(---\n.*?\n)(---\n)', txt, re.S)
        if not m:
            logs.append("  ERROR: no frontmatter found"); return logs
        fm, rest = m.group(1), txt[m.end():]
        if "kg/paper" not in fm:
            fm = re.sub(r'(tags:\n(?:- .*\n)+)', lambda mm: mm.group(1) + "- kg/paper\n", fm, count=1)
        txt = fm + kg_block + "---\n" + rest

        claim_lines = []
        for c in art.get("claims", []):
            src = clean_source(c.get("source"))
            link = norm_slug(c.get("link", ""))
            line = "- " + c["text"].strip()
            if src:
                line += f" ({src})"
            if link and link in type_idx:
                line += f" [[{link}]]"
            claim_lines.append(line)
        claims = "\n".join(claim_lines)
        if claims:
            txt = txt.rstrip() + "\n\n## Claims\n\n" + claims + "\n"
    else:
        logs.append("  body-only (graph already present)")

    open(note_path, "w").write(txt)
    logs.append("  patched: " + note_stem)
    return logs


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: enrich_apply.py <artifacts.json>  (run from repo root or set REPO_ROOT)")
    batch = json.load(open(sys.argv[1]))
    type_idx = build_type_index(batch)
    for art in batch:
        if not art:
            continue
        print(f"== {art['arxiv']} ==")
        for line in patch_note(art, type_idx):
            print(line)


if __name__ == "__main__":
    main()
