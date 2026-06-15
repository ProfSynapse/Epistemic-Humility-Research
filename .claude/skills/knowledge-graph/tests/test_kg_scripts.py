#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology  # noqa: E402
from validate_kg_relationships import validate_note  # noqa: E402


class KnowledgeGraphScriptTests(unittest.TestCase):
    def test_canonical_relationships_validate_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Target.md").write_text(
                """---
title: "Target"
tags:
  - kg/concept
kg:
  id: concept:target
  type: concept
---

# Target
""",
                encoding="utf-8",
            )
            (root / "Source.md").write_text(
                """---
title: "Source"
tags:
  - kg/concept
kg:
  id: concept:source
  type: concept
related:
  - "[[Target]]"
relationships:
  - type: related_to
    target: "[[Target]]"
    target_id: concept:target
    confidence: high
---

# Source
""",
                encoding="utf-8",
            )

            ontology = load_ontology()
            index = NoteIndex.build(root)
            notes, scan_findings = collect_graph_notes([root], root=root)
            findings = list(scan_findings)
            for note in notes:
                findings.extend(validate_note(note, ontology, index))
            triples = collect_triples(notes, ontology, index=index)

            self.assertEqual([], [finding.as_dict() for finding in findings if finding.severity == "ERROR"])
            self.assertEqual(1, len(triples))
            self.assertEqual("concept:source", triples[0].source_id)
            self.assertEqual("related_to", triples[0].edge_type)
            self.assertEqual("concept:target", triples[0].target_id)

    def test_legacy_relationships_export_as_legacy_triples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Target.md").write_text("---\ntitle: Target\n---\n", encoding="utf-8")
            (root / "Source.md").write_text(
                """---
relationships:
  - "#part_of [[Target]]"
---
""",
                encoding="utf-8",
            )

            ontology = load_ontology()
            index = NoteIndex.build(root)
            notes, _ = collect_graph_notes([root], root=root)
            triples = collect_triples(notes, ontology, index=index)

            self.assertEqual(1, len(triples))
            self.assertTrue(triples[0].legacy)
            self.assertEqual("part_of", triples[0].edge_type)
            self.assertEqual("Target", triples[0].target)


if __name__ == "__main__":
    unittest.main()
