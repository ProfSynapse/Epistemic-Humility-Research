#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from kg_common import (
    CONFIDENCE_VALUES,
    EDGE_RE,
    KG_STATUS_VALUES,
    LEGACY_RELATIONSHIP_RE,
    RELATIONSHIP_KEYS,
    RELATIONSHIP_STATUS_VALUES,
    WIKILINK_RE,
    Finding,
    NoteIndex,
    ParsedNote,
    canonical_edge,
    collect_graph_notes,
    extract_wikilinks,
    link_key,
    load_ontology,
    rel_path,
    relationship_targets,
)


def add(severity: str, code: str, note: ParsedNote, message: str, findings: list[Finding]) -> None:
    findings.append(Finding(severity, code, rel_path(note.path), message))


def validate_note(note: ParsedNote, ontology: dict[str, Any], index: NoteIndex) -> list[Finding]:
    findings: list[Finding] = []
    frontmatter = note.frontmatter
    edges = ontology["edges"]
    node_types = set(ontology.get("node_types") or [])

    kg = frontmatter.get("kg")
    if kg is None:
        add("WARN", "KG100", note, "missing kg node metadata", findings)
    elif not isinstance(kg, dict):
        add("ERROR", "KG101", note, "kg must be a mapping with id and type", findings)
        kg = {}

    if isinstance(kg, dict):
        kg_id = kg.get("id")
        kg_type = kg.get("type")
        kg_status = kg.get("status")
        if not kg_id:
            add("WARN", "KG102", note, "missing kg.id durable node identifier", findings)
        elif not isinstance(kg_id, str):
            add("ERROR", "KG103", note, "kg.id must be a string", findings)
        elif ":" not in kg_id:
            add("WARN", "KG104", note, "kg.id should use namespace:value format", findings)

        if not kg_type:
            add("WARN", "KG105", note, "missing kg.type node type", findings)
        elif not isinstance(kg_type, str):
            add("ERROR", "KG106", note, "kg.type must be a string", findings)
        elif node_types and kg_type not in node_types:
            add("WARN", "KG107", note, f"kg.type {kg_type!r} is not in ontology node_types", findings)

        if kg_id and kg_type and isinstance(kg_id, str) and isinstance(kg_type, str):
            namespace = kg_id.split(":", 1)[0]
            if namespace != kg_type:
                add("WARN", "KG108", note, f"kg.id namespace {namespace!r} does not match kg.type {kg_type!r}", findings)

        if kg_status and kg_status not in KG_STATUS_VALUES:
            add("WARN", "KG109", note, f"kg.status should be one of {sorted(KG_STATUS_VALUES)}", findings)

        tags = frontmatter.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(kg_type, str) and kg_type and isinstance(tags, list):
            expected_tag = f"kg/{kg_type}"
            normalized_tags = {str(tag).lstrip("#") for tag in tags}
            if expected_tag not in normalized_tags:
                add("WARN", "KG110", note, f"tags should include {expected_tag!r}", findings)

    related = frontmatter.get("related") or []
    related_keys: set[str] = set()
    if "related" in frontmatter and not isinstance(related, list):
        add("ERROR", "KG200", note, "related must be a list of quoted wikilinks", findings)
    elif isinstance(related, list):
        for idx, item in enumerate(related, start=1):
            if not isinstance(item, str):
                add("ERROR", "KG201", note, f"related[{idx}] must be a string wikilink", findings)
                continue
            if not WIKILINK_RE.search(item):
                add("WARN", "KG202", note, f"related[{idx}] should be an Obsidian wikilink", findings)
            related_keys.add(link_key(item))

    relationships = frontmatter.get("relationships") or []
    if "relationships" in frontmatter and relationships is None:
        return findings
    if not isinstance(relationships, list):
        add("ERROR", "KG300", note, "relationships must be a list", findings)
        return findings

    relationship_target_keys: set[str] = set()
    for idx, entry in enumerate(relationships, start=1):
        location = f"relationships[{idx}]"
        if isinstance(entry, str):
            validate_legacy(entry, location, note, ontology, index, findings)
            for target in relationship_targets(entry):
                relationship_target_keys.add(link_key(target))
            continue

        if not isinstance(entry, dict):
            add("ERROR", "KG301", note, f"{location} must be a mapping or legacy string", findings)
            continue

        unknown = sorted(set(entry) - RELATIONSHIP_KEYS)
        if unknown:
            add("WARN", "KG302", note, f"{location} has unknown keys: {', '.join(unknown)}", findings)

        edge = entry.get("type")
        if not isinstance(edge, str) or not edge:
            add("ERROR", "KG303", note, f"{location}.type is required", findings)
        else:
            validate_edge(edge, location, note, ontology, findings)

        target = entry.get("target")
        if not isinstance(target, str) or not target:
            add("ERROR", "KG304", note, f"{location}.target is required", findings)
        elif not WIKILINK_RE.search(target):
            add("ERROR", "KG305", note, f"{location}.target must be an Obsidian wikilink", findings)
        else:
            relationship_target_keys.add(link_key(target))
            validate_target(target, entry.get("target_id"), location, note, index, findings)

        confidence = entry.get("confidence")
        if confidence and confidence not in CONFIDENCE_VALUES:
            add("WARN", "KG306", note, f"{location}.confidence should be one of {sorted(CONFIDENCE_VALUES)}", findings)

        status = entry.get("status")
        if status and status not in RELATIONSHIP_STATUS_VALUES:
            add("WARN", "KG307", note, f"{location}.status should be one of {sorted(RELATIONSHIP_STATUS_VALUES)}", findings)

        evidence = entry.get("evidence")
        if evidence is not None and not isinstance(evidence, list):
            add("WARN", "KG308", note, f"{location}.evidence should be a list", findings)

    if relationship_target_keys and "related" not in frontmatter:
        add("WARN", "KG400", note, "missing related projection for relationship targets", findings)
    for target in sorted(relationship_target_keys - related_keys):
        add("WARN", "KG401", note, f"relationship target {target!r} is missing from related", findings)

    return findings


def validate_edge(
    edge: str,
    location: str,
    note: ParsedNote,
    ontology: dict[str, Any],
    findings: list[Finding],
    unknown_severity: str = "ERROR",
) -> None:
    canonical, used_alias = canonical_edge(edge, ontology)
    if not EDGE_RE.match(canonical):
        add("ERROR", "KG320", note, f"{location}.type must be snake_case", findings)
        return
    if used_alias:
        add("WARN", "KG321", note, f"{location}.type {edge!r} is an alias; use canonical {canonical!r}", findings)
    elif canonical != edge:
        add("WARN", "KG322", note, f"{location}.type should be normalized to {canonical!r}", findings)
    if canonical not in ontology["edges"]:
        add(unknown_severity, "KG323", note, f"{location}.type {canonical!r} is not in edge ontology", findings)


def validate_target(
    target: str,
    target_id: Any,
    location: str,
    note: ParsedNote,
    index: NoteIndex,
    findings: list[Finding],
) -> None:
    resolved, state = index.resolve_link(target)
    if state == "missing":
        add("WARN", "KG330", note, f"{location}.target {target!r} does not resolve to a note", findings)
    elif state == "ambiguous":
        add("WARN", "KG331", note, f"{location}.target {target!r} is ambiguous", findings)
    elif target_id and resolved and resolved.kg_id and target_id != resolved.kg_id:
        add("ERROR", "KG332", note, f"{location}.target_id {target_id!r} does not match target kg.id {resolved.kg_id!r}", findings)


def validate_legacy(
    entry: str,
    location: str,
    note: ParsedNote,
    ontology: dict[str, Any],
    index: NoteIndex,
    findings: list[Finding],
) -> None:
    match = LEGACY_RELATIONSHIP_RE.match(entry)
    if not match:
        if extract_wikilinks(entry):
            add("ERROR", "KG340", note, f"{location} is missing an edge type; use object form with type and target", findings)
        else:
            add("ERROR", "KG341", note, f"{location} is not a valid relationship", findings)
        return

    add("WARN", "KG342", note, f"{location} uses legacy '#edge [[target]]' shorthand", findings)
    validate_edge(match.group("edge"), location, note, ontology, findings, unknown_severity="WARN")
    targets = extract_wikilinks(match.group("targets"))
    if not targets:
        add("ERROR", "KG343", note, f"{location} has no wikilink target", findings)
    if len(targets) > 1:
        add("WARN", "KG344", note, f"{location} has multiple targets; use one relationship object per target", findings)
    for target in targets:
        validate_target(target, "", location, note, index, findings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Obsidian knowledge graph frontmatter.")
    parser.add_argument("paths", nargs="*", help="Markdown files or folders. Defaults to the vault root.")
    parser.add_argument("--root", default=".", help="Vault root. Defaults to current directory.")
    parser.add_argument("--ontology", default="", help="Path to edge ontology YAML.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON findings.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ontology_path = Path(args.ontology).resolve() if args.ontology else None
    ontology = load_ontology(ontology_path) if ontology_path else load_ontology()
    index = NoteIndex.build(root)
    notes, findings = collect_graph_notes([Path(path) for path in args.paths], root=root)

    for note in notes:
        findings.extend(validate_note(note, ontology, index))

    findings.sort(key=lambda item: (item.path, item.severity, item.code, item.message))
    if args.json:
        print(json.dumps([finding.as_dict() for finding in findings], ensure_ascii=False, indent=2))
    else:
        if not findings:
            print(f"OK {len(notes)} graph notes validated")
        else:
            for finding in findings:
                print(f"{finding.severity} {finding.code} {finding.path}: {finding.message}")
            error_count = sum(1 for finding in findings if finding.severity == "ERROR")
            warn_count = sum(1 for finding in findings if finding.severity == "WARN")
            print(f"Validated {len(notes)} graph notes: {error_count} errors, {warn_count} warnings")

    has_errors = any(finding.severity == "ERROR" for finding in findings)
    has_warnings = any(finding.severity == "WARN" for finding in findings)
    return 1 if has_errors or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
