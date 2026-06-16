#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology  # noqa: E402
from kg_index import connect, dangling_references, index_root  # noqa: E402
from kg_search import search  # noqa: E402
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

    def test_kg_index_searches_python_symbols_and_traverses_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "main.py").write_text(
                """import helper

def main_entry():
    return helper.helper_function()
""",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                """def helper_function():
    return "ok"
""",
                encoding="utf-8",
            )

            summary = index_root(root, db)
            self.assertEqual(2, summary["files"])
            results = search(db, "main_entry", limit=5, traverse_depth=2)
            paths = {result.path for result in results}

            self.assertIn("main.py", paths)
            self.assertIn("helper.py", paths)

    def test_kg_index_traverses_config_references_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "config.yaml").write_text(
                """runner:
  script: runner.py
  mode: smoke
""",
                encoding="utf-8",
            )
            (root / "runner.py").write_text(
                """def run_smoke():
    return "configured"
""",
                encoding="utf-8",
            )

            index_root(root, db)
            results = search(db, "runner script", limit=5, traverse_depth=2)
            paths = {result.path for result in results}

            self.assertIn("config.yaml", paths)
            self.assertIn("runner.py", paths)

    def test_kg_index_reports_dangling_config_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "config.yaml").write_text(
                """runner:
  script: missing.py
""",
                encoding="utf-8",
            )

            index_root(root, db)
            dangling = dangling_references(db)
            self.assertEqual(1, len(dangling))
            self.assertEqual("file:missing.py", dangling[0]["target_id"])

    def test_kg_index_ignores_generated_output_filenames_as_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "config.yaml").write_text(
                """input:
  path: missing.jsonl
output:
  manifest_filename: manifest.json
  rows_filename: rows.jsonl
""",
                encoding="utf-8",
            )

            index_root(root, db)
            dangling = dangling_references(db)
            self.assertEqual(1, len(dangling))
            self.assertEqual("file:missing.jsonl", dangling[0]["target_id"])

    def test_kg_index_treats_jsonl_csv_as_metadata_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            data_dir = root / "datasets" / "sample"
            data_dir.mkdir(parents=True)
            (root / "config.yaml").write_text(
                """dataset:
  train: datasets/sample/train.jsonl
  eval: datasets/sample/eval.csv
""",
                encoding="utf-8",
            )
            (data_dir / "train.jsonl").write_text(
                '{"prompt": "alpha", "answer": "rawdatasetsecret"}\n',
                encoding="utf-8",
            )
            (data_dir / "eval.csv").write_text("question,label\nwhat,yes\n", encoding="utf-8")

            index_root(root, db)
            self.assertEqual([], dangling_references(db))
            self.assertFalse(search(db, "rawdatasetsecret", limit=3))
            paths = {result.path for result in search(db, "prompt answer question label", limit=5)}
            self.assertIn("datasets/sample/train.jsonl", paths)
            self.assertIn("datasets/sample/eval.csv", paths)

    def test_kg_index_full_texts_small_fixture_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            fixtures = root / "tests" / "fixtures"
            fixtures.mkdir(parents=True)
            (fixtures / "tiny.jsonl").write_text(
                '{"prompt": "fixtureonlytoken", "answer": "ok"}\n',
                encoding="utf-8",
            )

            index_root(root, db)
            paths = {result.path for result in search(db, "fixtureonlytoken", limit=3)}
            self.assertIn("tests/fixtures/tiny.jsonl", paths)

    def test_kg_search_does_not_let_fixture_data_outrank_code_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "hidden_state_probe.py").write_text(
                """def hidden_state_probe():
    return "code"
""",
                encoding="utf-8",
            )
            fixtures = root / "tests" / "fixtures"
            fixtures.mkdir(parents=True)
            (fixtures / "hidden_state_probe_results.jsonl").write_text(
                '{"prompt": "hidden_state_probe", "answer": "fixture"}\n',
                encoding="utf-8",
            )

            index_root(root, db)
            results = search(db, "hidden_state_probe", limit=3)
            self.assertEqual("hidden_state_probe.py", results[0].path)

    def test_kg_search_does_not_expand_through_external_import_hubs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "target.py").write_text(
                """import json

def hidden_state_probe():
    return json.dumps({"ok": True})
""",
                encoding="utf-8",
            )
            (root / "unrelated.py").write_text(
                """import json

def unrelated():
    return json.loads("{}")
""",
                encoding="utf-8",
            )

            index_root(root, db)
            paths = {result.path for result in search(db, "hidden_state_probe", limit=5, traverse_depth=2)}
            self.assertIn("target.py", paths)
            self.assertNotIn("unrelated.py", paths)

    def test_kg_index_reindexes_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            note = root / "note.md"
            note.write_text("# Before\n\nalpha marker\n", encoding="utf-8")

            first = index_root(root, db)
            self.assertEqual(1, first["changed"])
            self.assertTrue(search(db, "alpha", limit=3))

            note.write_text("# After\n\nbeta marker\n", encoding="utf-8")
            second = index_root(root, db)
            self.assertEqual(1, second["changed"])
            self.assertFalse(search(db, "alpha", limit=3))
            self.assertTrue(search(db, "beta", limit=3))

    def test_kg_index_schema_has_feedback_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "note.md").write_text("# Note\n\ncontent\n", encoding="utf-8")
            index_root(root, db)
            conn = connect(db)
            try:
                tables = {
                    row["name"]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
            finally:
                conn.close()
            self.assertIn("feedback_events", tables)

    def test_kg_index_rejects_missing_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                index_root(root / "missing", root / ".kg" / "index.sqlite")

    def test_kg_index_skips_dot_directories_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            hidden = root / ".hidden"
            hidden.mkdir()
            (hidden / "note.md").write_text("# Secret\n\nconcealedtoken\n", encoding="utf-8")
            (root / "note.md").write_text("# Public\n\nvisibletoken\n", encoding="utf-8")

            summary = index_root(root, db)
            self.assertEqual(1, summary["files"])
            self.assertFalse(search(db, "concealedtoken", limit=3))
            self.assertTrue(search(db, "visibletoken", limit=3))

    def test_kg_index_includes_fulltext_html_and_links_to_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            fulltext = root / "library" / "fulltext"
            fulltext.mkdir(parents=True)
            (fulltext / "2402.01306.html").write_text(
                """<html><head><title>KTO paper</title><style>.x{}</style></head>
<body><h1>Kahneman-Tversky Optimization</h1><script>ignored()</script>
<p>prospect theory alignment objective</p></body></html>
""",
                encoding="utf-8",
            )

            index_root(root, db)
            results = search(db, "prospect theory alignment", limit=5, traverse_depth=1)
            paths = {result.path for result in results}
            self.assertIn("library/fulltext/2402.01306.html", paths)

            conn = connect(db)
            try:
                edge = conn.execute(
                    """
                    SELECT edge_type FROM edges
                    WHERE source_id = ? AND target_id = ?
                    """,
                    ("file:library/fulltext/2402.01306.html", "paper:2402.01306"),
                ).fetchone()
            finally:
                conn.close()
            self.assertIsNotNone(edge)
            self.assertEqual("fulltext_for", edge["edge_type"])


if __name__ == "__main__":
    unittest.main()
