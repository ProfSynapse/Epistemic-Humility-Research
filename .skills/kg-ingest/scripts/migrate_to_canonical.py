#!/usr/bin/env python3
"""One-time migration: rewrite library/ notes from flat-key frontmatter into the
canonical knowledge-graph shape (`kg` node metadata + typed `relationships`
objects + `related` projection) used by the vendored `knowledge-graph` skill.

Deterministic: it only re-serializes edges already present in the frontmatter.
Idempotent: notes that already carry a `kg:` block are skipped.

Run from the repo root:
    python3 .agents/skills/kg-ingest/scripts/migrate_to_canonical.py
    python3 .agents/skills/kg-ingest/scripts/migrate_to_canonical.py --dry-run
"""
import glob
import os
import re
import sys

import yaml

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)\Z", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

CONCEPT_DIRS = ["methods", "metrics", "datasets", "models", "terms"]

# flat key -> canonical edge type
PAPER_EDGES = {
    "proposes": "proposes",
    "uses-method": "uses",
    "evaluates-on": "evaluates_on",
    "measures": "measures",
    "studies": "studies",
    "mechanisms": "supports",
}
ATOM_EDGES = {
    "extends": "derived_from",
    "derives-from": "derived_from",
    "variant-of": "variation_of",
    "prerequisite-of": "required_by",
    "related": "related_to",
}
HIGH_CONF = {"proposed_by", "supported_by"}


def split_note(path):
    text = open(path, encoding="utf-8").read()
    m = FM_RE.match(text)
    if not m:
        return None, None
    fm = yaml.safe_load(m.group(1)) or {}
    return (fm if isinstance(fm, dict) else None), m.group(2)


def links(value):
    out = []
    items = value if isinstance(value, list) else [value]
    for it in items:
        if not isinstance(it, str):
            continue
        m = WIKILINK.search(it)
        out.append(m.group(1).strip() if m else it.strip())
    return out


def build_id_index():
    """target wikilink stem -> kg.id."""
    idx = {}
    for d in CONCEPT_DIRS:
        for p in glob.glob(f"library/concepts/{d}/*.md"):
            fm, _ = split_note(p)
            stem = os.path.basename(p)[:-3]
            t = (fm or {}).get("type") or d.rstrip("s")
            idx[stem] = f"{t}:{(fm or {}).get('id', stem)}"
    for p in glob.glob("library/concepts/mechanisms/*.md"):
        fm, _ = split_note(p)
        stem = os.path.basename(p)[:-3]
        idx[stem] = f"mechanism:{(fm or {}).get('id', stem)}"
    for p in glob.glob("library/notes/*.md"):
        stem = os.path.basename(p)[:-3]
        idx[stem] = f"paper:{stem.split('--')[0]}"
    return idx


def target_id(stem, idx):
    if stem in idx:
        return idx[stem]
    if "--" in stem:  # looks like a paper note stem
        return f"paper:{stem.split('--')[0]}"
    return ""


def rel(edge, stem, idx):
    obj = {"type": edge, "target": f"[[{stem}]]"}
    tid = target_id(stem, idx)
    if tid:
        obj["target_id"] = tid
    if edge in HIGH_CONF:
        obj["confidence"] = "high"
    return obj


def order_frontmatter(fm, kg, relationships, related):
    """Preserve original keys, drop consumed flat keys, inject kg/related/relationships."""
    drop = set(PAPER_EDGES) | set(ATOM_EDGES) | {
        "introduced-by", "supported-by", "contradicted-by", "kg", "related", "relationships",
        "id", "type",  # now carried by kg.id / kg.type
    }
    out = {}
    # kg first after title/aliases/tags if present
    for k in ("title", "aliases", "tags"):
        if k in fm:
            out[k] = fm[k]
    out["kg"] = kg
    for k, v in fm.items():
        if k in drop or k in ("title", "aliases", "tags"):
            continue
        out[k] = v
    if related:
        out["related"] = related
    if relationships:
        out["relationships"] = relationships
    return out


def add_tag(fm, tag):
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [tag] + [t for t in tags if t != tag]


def dump(fm, body):
    text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000)
    return f"---\n{text}---\n{body}"


def migrate_concept(path, idx, kind):
    fm, body = split_note(path)
    if fm is None or "kg" in fm:
        return False
    stem = os.path.basename(path)[:-3]
    ntype = fm.get("type") or kind.rstrip("s")
    kgid = f"{ntype}:{fm.get('id', stem)}"
    rels, related = [], []
    if fm.get("introduced-by"):
        for s in links(fm["introduced-by"]):
            rels.append(rel("proposed_by", s, idx))
            related.append(f"[[{s}]]")
    for key, edge in ATOM_EDGES.items():
        if fm.get(key):
            for s in links(fm[key]):
                rels.append(rel(edge, s, idx))
                related.append(f"[[{s}]]")
    kg = {"id": kgid, "type": ntype, "status": "canonical"}
    fm["tags"] = add_tag(fm, f"kg/{ntype}")
    new = order_frontmatter(fm, kg, rels, dedupe(related))
    open(path, "w", encoding="utf-8").write(dump(new, body))
    return True


def migrate_mechanism(path, idx):
    fm, body = split_note(path)
    if fm is None or "kg" in fm:
        return False
    stem = os.path.basename(path)[:-3]
    kgid = f"mechanism:{fm.get('id', stem)}"
    rels, related = [], []
    for s in links(fm.get("supported-by") or []):
        rels.append(rel("supported_by", s, idx))
        related.append(f"[[{s}]]")
    for s in links(fm.get("contradicted-by") or []):
        rels.append(rel("opposed_by", s, idx))
        related.append(f"[[{s}]]")
    # connect mechanism to the concept atoms embedded in cause/effect prose
    for field in ("cause", "effect"):
        for s in links(WIKILINK_in(fm.get(field, ""))):
            if s in idx:
                rels.append(rel("related_to", s, idx))
                related.append(f"[[{s}]]")
    kg = {"id": kgid, "type": "mechanism", "status": "canonical"}
    fm["tags"] = add_tag(fm, "kg/mechanism")
    new = order_frontmatter(fm, kg, rels, dedupe(related))
    open(path, "w", encoding="utf-8").write(dump(new, body))
    return True


def WIKILINK_in(text):
    return [f"[[{m.group(1)}]]" for m in WIKILINK.finditer(text or "")]


def migrate_paper(path, idx):
    fm, body = split_note(path)
    if fm is None or "kg" in fm:
        return False
    if not any(k in fm for k in PAPER_EDGES):
        return False  # only spine papers that carry flat edges
    stem = os.path.basename(path)[:-3]
    arxiv = str(fm.get("arxiv") or stem.split("--")[0])
    rels, related = [], []
    for key, edge in PAPER_EDGES.items():
        if fm.get(key):
            for s in links(fm[key]):
                rels.append(rel(edge, s, idx))
                related.append(f"[[{s}]]")
    kg = {"id": f"paper:{arxiv}", "type": "paper", "status": "canonical"}
    fm["tags"] = add_tag(fm, "kg/paper")
    new = order_frontmatter(fm, kg, rels, dedupe(related))
    open(path, "w", encoding="utf-8").write(dump(new, body))
    return True


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main():
    dry = "--dry-run" in sys.argv
    if dry:
        print("(dry-run: no scripts will be patched here; this reports counts only)")
        return
    idx = build_id_index()
    n_concept = n_mech = n_paper = 0
    for d in CONCEPT_DIRS:
        for p in sorted(glob.glob(f"library/concepts/{d}/*.md")):
            n_concept += migrate_concept(p, idx, d)
    for p in sorted(glob.glob("library/concepts/mechanisms/*.md")):
        n_mech += migrate_mechanism(p, idx)
    for p in sorted(glob.glob("library/notes/*.md")):
        n_paper += migrate_paper(p, idx)
    print(f"migrated: {n_concept} concept atoms, {n_mech} mechanisms, {n_paper} paper notes")


if __name__ == "__main__":
    main()
