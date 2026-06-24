#!/usr/bin/env python3
"""Apply knowledge-graph ingestion results to the vault, then verify + reindex.

Takes the JSON returned by the ingestion workflow (scripts/ingest_workflow.js).
Accepts either the raw workflow return or the wrapped task-output file
(`{"result": {...}}`). Idempotent: re-running does not double-apply.

Steps:
  1. Splice each paper note's typed-edge frontmatter block + `## Claims` section.
  2. Report any dangling [[wikilinks]] across concepts/ and notes/.
  3. Regenerate library/concepts/README.md (the map-of-content).

Usage:
    python .agents/skills/kg-ingest/scripts/apply_kg_patches.py <result.json>

Run from the repo root.
"""
import glob
import json
import os
import re
import sys

LINK = re.compile(r"\[\[([^\]|#]+?)\]\]")
REL_KEYS = ("proposes", "uses-method", "evaluates-on", "measures", "evaluates", "studies", "mechanisms")


def load_result(path):
    d = json.load(open(path, encoding="utf-8"))
    return d.get("result", d)


def apply_patches(patches):
    changed, skipped = 0, []
    for p in patches:
        note = f"library/notes/{p['noteStem']}.md"
        if not os.path.exists(note):
            skipped.append((p["noteStem"], "missing note"))
            continue
        txt = open(note, encoding="utf-8").read()
        lines = txt.split("\n")
        fm = [i for i, l in enumerate(lines) if l.strip() == "---"]
        yamlb = (p.get("yamlBlock") or "").strip()
        claimsb = (p.get("claimsBlock") or "").strip()
        did = False
        if yamlb and len(fm) >= 2:
            first_key = yamlb.split(":")[0]
            if first_key + ":" not in txt:
                lines[fm[1] : fm[1]] = yamlb.split("\n")
                did = True
        txt = "\n".join(lines)
        if claimsb and "## Claims" not in txt:
            if not txt.endswith("\n"):
                txt += "\n"
            txt += "\n## Claims\n\n" + claimsb + "\n"
            did = True
        if did:
            open(note, "w", encoding="utf-8").write(txt)
            changed += 1
        else:
            skipped.append((p["noteStem"], "already applied"))
    return changed, skipped


def stem_for_arxiv(arxiv):
    hits = glob.glob(f"library/notes/{arxiv}--*.md")
    return os.path.basename(hits[0])[:-3] if hits else None


def apply_mech_support(additions):
    """Union new supporting papers into existing (canonical) mechanism notes as
    `supported_by` relationship objects + `related` entries. Idempotent."""
    from migrate_to_canonical import split_note, dump  # sibling script, same dir

    updated = 0
    for item in additions or []:
        path = f"library/concepts/mechanisms/{item['id']}.md"
        if not os.path.exists(path):
            continue
        fm, body = split_note(path)
        if fm is None or "kg" not in fm:
            continue  # not yet canonical; migrate_to_canonical will handle it
        rels = fm.get("relationships") or []
        related = fm.get("related") or []
        existing = {r.get("target") for r in rels if isinstance(r, dict)}
        changed = False
        for arxiv in item.get("arxiv", []):
            stem = stem_for_arxiv(arxiv)
            if not stem:
                continue
            tgt = f"[[{stem}]]"
            if tgt in existing:
                continue
            rels.append({"type": "supported_by", "target": tgt, "target_id": f"paper:{arxiv}", "confidence": "high"})
            if tgt not in related:
                related.append(tgt)
            changed = True
        if changed:
            fm["relationships"] = rels
            fm["related"] = related
            open(path, "w", encoding="utf-8").write(dump(fm, body))
            updated += 1
    return updated


def valid_targets():
    # any markdown anywhere in the vault is a legal wikilink target (SCHEMA, READMEs, ...)
    return set(os.path.basename(p)[:-3] for p in glob.glob("library/**/*.md", recursive=True))


def integrity():
    valid = valid_targets()
    unresolved = {}
    for fp in glob.glob("library/concepts/**/*.md", recursive=True) + glob.glob("library/notes/*.md"):
        for m in LINK.finditer(open(fp, encoding="utf-8").read()):
            t = m.group(1).strip()
            if t not in valid:
                unresolved[t] = unresolved.get(t, 0) + 1
    return unresolved


def first_line_body(path):
    text = open(path, encoding="utf-8").read()
    if text.startswith("---"):
        try:
            text = text[text.index("\n---", 3) + 4 :]
        except ValueError:
            pass
    for line in text.strip().split("\n"):
        if line.strip():
            return re.sub(r"\[\[|\]\]|\*\*", "", line)[:140]
    return ""


def frontmatter_field(path, field):
    for line in open(path, encoding="utf-8"):
        if line.startswith(field + ":"):
            return re.sub(r"\[\[|\]\]", "", line.split(":", 1)[1]).strip().strip('"')
        if line.strip() == "---" and field == "_done":
            break
    return ""


def regen_moc():
    order = [
        ("methods", "Methods & algorithms"),
        ("metrics", "Metrics"),
        ("datasets", "Datasets & benchmarks"),
        ("models", "Models"),
        ("terms", "Terms"),
        ("mechanisms", "Mechanisms (cause -> effect)"),
        ("gaps", "Gaps (verified literature absences)"),
    ]
    out = [
        "# Concepts: knowledge-graph map",
        "",
        "Atomic notes extracted from the library papers via the Agents-K1 ingestion "
        "skill (`kg-ingest`). See [[SCHEMA]] for the ontology. Regenerated by "
        "`apply_kg_patches.py`; do not hand-edit.",
        "",
    ]
    total = 0
    for d, label in order:
        files = sorted(glob.glob(f"library/concepts/{d}/*.md"))
        out.append(f"## {label} ({len(files)})")
        out.append("")
        for fp in files:
            stem = os.path.basename(fp)[:-3]
            if d == "mechanisms":
                cause = frontmatter_field(fp, "cause")
                effect = frontmatter_field(fp, "effect")
                pol = frontmatter_field(fp, "polarity")
                desc = f"{cause} **{pol}** {effect}"[:160]
            else:
                desc = first_line_body(fp)
            out.append(f"- [[{stem}]] : {desc}")
            total += 1
        out.append("")
    open("library/concepts/README.md", "w", encoding="utf-8").write("\n".join(out))
    return total


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: apply_kg_patches.py <result.json>")
    res = load_result(sys.argv[1])
    patches = res.get("paperPatches", [])
    changed, skipped = apply_patches(patches)
    print(f"patched notes: {changed} changed, {len(skipped)} skipped")
    for s in skipped:
        print("  skip:", s)
    mech_updated = apply_mech_support(res.get("existingMechSupport", []))
    if mech_updated:
        print(f"existing mechanism supported-by updated: {mech_updated}")
    total = regen_moc()
    print(f"regenerated library/concepts/README.md ({total} entries)")
    unresolved = integrity()
    if unresolved:
        print(f"DANGLING LINKS ({len(unresolved)} distinct) -- review:")
        for t, c in sorted(unresolved.items(), key=lambda x: -x[1]):
            print(f"  {c:3d}  {t}")
    else:
        print("link integrity: all wikilinks resolve")


if __name__ == "__main__":
    main()
