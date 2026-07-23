#!/usr/bin/env python3
from __future__ import annotations

import io
from contextlib import redirect_stdout
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology  # noqa: E402
from kg_feedback import record_feedback  # noqa: E402
from kg_index import connect, dangling_references, index_root, iter_source_files  # noqa: E402
from kg_search import main as kg_search_main  # noqa: E402
from kg_search import lane_weights_from_feedback, search  # noqa: E402
from kg_validate_repo import validate as validate_kg_repo  # noqa: E402
from validate_kg_relationships import validate_note  # noqa: E402


def find_repo_root(path: Path) -> Path:
    for parent in [path, *path.parents]:
        if (parent / "bin" / "sync_skills.py").is_file() and (parent / ".skills").is_dir():
            return parent
    raise FileNotFoundError("repo root with bin/sync_skills.py not found")


class KnowledgeGraphScriptTests(unittest.TestCase):
    def test_default_roots_resolve_to_repo_checkout_from_any_skill_tree(self) -> None:
        import kg_common
        import kg_index

        repo_root = find_repo_root(SCRIPT_DIR)
        self.assertEqual(repo_root, kg_index.REPO_ROOT)
        self.assertEqual(repo_root, kg_common.VAULT_ROOT)
        self.assertEqual(repo_root / ".kg" / "index.sqlite", kg_index.DEFAULT_DB)

    def test_iter_markdown_ignores_relative_to_root_not_ancestors(self) -> None:
        from kg_common import iter_markdown

        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "tmp" / "vault"
            (vault / "logs").mkdir(parents=True)
            (vault / "note.md").write_text("# Note\n", encoding="utf-8")
            (vault / "logs" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")

            found = iter_markdown([vault], root=vault)

            self.assertEqual([vault / "note.md"], found)

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
                search_columns = {
                    row["name"]
                    for row in conn.execute("PRAGMA table_info(search_log)").fetchall()
                }
            finally:
                conn.close()
            self.assertIn("feedback_events", tables)
            self.assertIn("path_memory_labels", tables)
            self.assertIn("lane_weights_json", search_columns)

    def test_kg_index_labels_paths_by_memory_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            dot_skill = root / ".skills" / "demo"
            dot_skill.mkdir(parents=True)
            (dot_skill / "SKILL.md").write_text("# Dot skill\n\nCanonical workflow.\n", encoding="utf-8")
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Demo\n\nReusable workflow.\n", encoding="utf-8")
            (root / "library" / "concepts").mkdir(parents=True)
            (root / "library" / "concepts" / "term.md").write_text("# Term\n\nConcept note.\n", encoding="utf-8")
            (root / "docs" / "protocols" / "phase1").mkdir(parents=True)
            (root / "docs" / "protocols" / "phase1" / "PROTOCOL.md").write_text("# Protocol\n\nConstraint.\n", encoding="utf-8")
            (root / "docs" / "sessions").mkdir(parents=True)
            (root / "docs" / "sessions" / "phase1.md").write_text("# Session\n\nCheckpoint.\n", encoding="utf-8")

            index_root(root, db)
            conn = connect(db)
            try:
                labels = {
                    (row["path"], row["memory_type"])
                    for row in conn.execute("SELECT path, memory_type FROM path_memory_labels").fetchall()
                }
            finally:
                conn.close()

            self.assertIn((".skills/demo/SKILL.md", "procedural"), labels)
            self.assertIn(("skills/demo/SKILL.md", "procedural"), labels)
            self.assertIn(("library/concepts/term.md", "semantic"), labels)
            self.assertIn(("archive/docs/protocols/phase1/PROTOCOL.md", "normative"), labels)
            self.assertIn(("docs/sessions/phase1.md", "episodic"), labels)

    def test_kg_search_learns_lane_weights_from_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Matrix launch\n\nrepeatable launch workflow\n", encoding="utf-8")
            concepts = root / "library" / "concepts"
            concepts.mkdir(parents=True)
            (concepts / "matrix.md").write_text("# Matrix launch\n\nconceptual matrix note\n", encoding="utf-8")

            index_root(root, db)
            conn = connect(db)
            try:
                conn.execute(
                    "INSERT INTO search_log(query, results_json, lane_weights_json, created_at) VALUES (?, ?, ?, ?)",
                    ("matrix launch", "[]", "{}", 1.0),
                )
                conn.commit()
                recorded = record_feedback(
                    db,
                    "read",
                    "skills/demo/SKILL.md",
                    query="matrix launch",
                    success=True,
                )
                self.assertEqual("skills/demo/SKILL.md", recorded["path"])
                weights = lane_weights_from_feedback(conn, "matrix launch")
            finally:
                conn.close()

            self.assertGreater(weights["procedural"], weights["semantic"])
            self.assertEqual("skills/demo/SKILL.md", search(db, "matrix launch", limit=2)[0].path)

    def test_kg_search_prefers_procedural_docs_for_natural_language_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            skill = root / ".skills" / "runner"
            other_skill = root / ".skills" / "other"
            tests = skill / "tests"
            tests.mkdir(parents=True)
            other_skill.mkdir(parents=True)
            docs = root / "docs"
            docs.mkdir()
            (skill / "SKILL.md").write_text(
                "# Runner\n\nUse this runbook to run the experiment matrix.\n",
                encoding="utf-8",
            )
            (other_skill / "SKILL.md").write_text("# Workflow\n\nGeneric reusable workflow.\n", encoding="utf-8")
            (tests / "test_matrix.py").write_text(
                'def test_run_experiment_matrix():\n    assert "experiment matrix"\n',
                encoding="utf-8",
            )
            (docs / "matrix.md").write_text(
                "# Matrix\n\nDetailed run experiment matrix workflow background.\n",
                encoding="utf-8",
            )

            index_root(root, db)
            results = search(db, "how do I run experiment matrix workflow", limit=3)
            self.assertEqual(".skills/runner/SKILL.md", results[0].path)

    def test_kg_search_cli_accepts_unquoted_multi_word_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "note.md").write_text("# Note\n\nalpha beta marker\n", encoding="utf-8")
            argv = [
                "kg_search.py",
                "alpha",
                "beta",
                "--root",
                str(root),
                "--db",
                str(db),
                "--limit",
                "1",
            ]
            stdout = io.StringIO()

            with patch.object(sys, "argv", argv), redirect_stdout(stdout):
                rc = kg_search_main()

            self.assertEqual(0, rc)
            self.assertIn("KG search results for: alpha beta", stdout.getvalue())

    def test_kg_repo_validator_source_invariants_pass(self) -> None:
        repo_root = find_repo_root(SCRIPT_DIR)
        findings = validate_kg_repo(repo_root, skip_sync=True, skip_hook_installation=True)
        errors = [finding for finding in findings if finding.severity == "ERROR"]
        self.assertEqual([], errors)

    def test_kg_feedback_records_event_for_latest_matching_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            (root / "note.md").write_text("# Note\n\nalpha\n", encoding="utf-8")
            index_root(root, db)
            search(db, "alpha", limit=3)

            recorded = record_feedback(db, "read", "note.md", query="alpha", success=True)
            conn = connect(db)
            try:
                row = conn.execute(
                    "SELECT search_id, event_type, path, success FROM feedback_events WHERE id = ?",
                    (recorded["feedback_id"],),
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row)
            self.assertEqual("read", row["event_type"])
            self.assertEqual("note.md", row["path"])
            self.assertEqual(1, row["success"])

    def test_kg_index_rejects_missing_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                index_root(root / "missing", root / ".kg" / "index.sqlite")

    def test_kg_index_uses_repo_local_safe_directory_for_git_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "note.md").write_text("# Note\n", encoding="utf-8")
            proc = type("Proc", (), {"stdout": b"note.md\0"})()

            with patch("kg_index.subprocess.run", return_value=proc) as run:
                files = iter_source_files(root)

            self.assertEqual([root / "note.md"], files)
            argv = run.call_args.args[0]
            self.assertEqual("git", argv[0])
            self.assertIn("-c", argv)
            self.assertIn(f"safe.directory={root.resolve().as_posix()}", argv)

    def test_kg_index_fallback_walk_prunes_ignored_dot_caches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            cache = root / ".cache" / "hf" / "snapshots"
            cache.mkdir(parents=True)
            (cache / "config.json").write_text('{"cacheonlytoken": true}\n', encoding="utf-8")
            (root / "note.md").write_text("# Public\n\nvisibletoken\n", encoding="utf-8")

            with patch("kg_index.subprocess.run", side_effect=RuntimeError("git unavailable")):
                summary = index_root(root, db)

            self.assertEqual(1, summary["files"])
            self.assertTrue(search(db, "visibletoken", limit=3))
            self.assertFalse(search(db, "cacheonlytoken", limit=3))

    def test_kg_index_skips_dot_directories_by_default_except_canonical_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            hidden = root / ".hidden"
            hidden.mkdir()
            (hidden / "note.md").write_text("# Secret\n\nconcealedtoken\n", encoding="utf-8")
            dot_skill = root / ".skills" / "demo"
            dot_skill.mkdir(parents=True)
            (dot_skill / "SKILL.md").write_text("# Skill\n\nproceduraltoken\n", encoding="utf-8")
            (root / "note.md").write_text("# Public\n\nvisibletoken\n", encoding="utf-8")

            summary = index_root(root, db)
            self.assertEqual(2, summary["files"])
            self.assertFalse(search(db, "concealedtoken", limit=3))
            self.assertTrue(search(db, "proceduraltoken", limit=3))
            self.assertTrue(search(db, "visibletoken", limit=3))

    def _write_supersession_pair(self, root: Path, marker_in_new: bool = True) -> None:
        concepts = root / "library" / "concepts"
        concepts.mkdir(parents=True)
        (concepts / "old-claim.md").write_text(
            """---
title: "Old Claim"
tags:
  - kg/claim
kg:
  id: claim:abstention-effect-v1
  type: claim
  status: deprecated
  deprecated_by: claim:abstention-effect-v2
---

# Old Claim

supersessionmarker stale narrative
""",
            encoding="utf-8",
        )
        new_body = "supersessionmarker current narrative" if marker_in_new else "current narrative only"
        (concepts / "new-claim.md").write_text(
            f"""---
title: "New Claim"
tags:
  - kg/claim
kg:
  id: claim:abstention-effect-v2
  type: claim
  status: canonical
---

# New Claim

{new_body}
""",
            encoding="utf-8",
        )

    def test_kg_search_excludes_deprecated_notes_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            self._write_supersession_pair(root)

            index_root(root, db)
            default_paths = {result.path for result in search(db, "supersessionmarker", limit=5)}
            self.assertIn("library/concepts/new-claim.md", default_paths)
            self.assertNotIn("library/concepts/old-claim.md", default_paths)

            included = search(db, "supersessionmarker", limit=5, include_deprecated=True)
            by_path = {result.path: result for result in included}
            self.assertIn("library/concepts/old-claim.md", by_path)
            old = by_path["library/concepts/old-claim.md"]
            self.assertEqual("deprecated", old.status)
            self.assertEqual("claim:abstention-effect-v2", old.deprecated_by)

            conn = connect(db)
            try:
                edge = conn.execute(
                    "SELECT edge_type FROM edges WHERE source_id = ? AND target_id = ?",
                    ("claim:abstention-effect-v1", "claim:abstention-effect-v2"),
                ).fetchone()
            finally:
                conn.close()
            self.assertIsNotNone(edge)
            self.assertEqual("superseded_by", edge["edge_type"])

    def test_kg_search_surfaces_successor_when_only_deprecated_note_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            self._write_supersession_pair(root, marker_in_new=False)

            index_root(root, db)
            paths = {result.path for result in search(db, "supersessionmarker", limit=5, traverse_depth=2)}
            self.assertNotIn("library/concepts/old-claim.md", paths)
            self.assertIn("library/concepts/new-claim.md", paths)

    def test_kg_index_migrates_legacy_nodes_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / ".kg" / "index.sqlite"
            db.parent.mkdir(parents=True)
            legacy = sqlite3.connect(db)
            legacy.execute(
                """
                CREATE TABLE nodes (
                  node_id TEXT PRIMARY KEY,
                  path TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  label TEXT NOT NULL,
                  node_type TEXT NOT NULL,
                  line INTEGER NOT NULL
                )
                """
            )
            legacy.commit()
            legacy.close()

            conn = connect(db)
            try:
                columns = {row["name"] for row in conn.execute("PRAGMA table_info(nodes)").fetchall()}
            finally:
                conn.close()
            self.assertIn("status", columns)
            self.assertIn("deprecated_by", columns)

    def test_validator_flags_deprecated_by_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Dangling.md").write_text(
                """---
title: "Dangling"
tags:
  - kg/claim
kg:
  id: claim:dangling
  type: claim
  deprecated_by: claim:nowhere
---
""",
                encoding="utf-8",
            )
            (root / "SelfLoop.md").write_text(
                """---
title: "SelfLoop"
tags:
  - kg/claim
kg:
  id: claim:self-loop
  type: claim
  status: deprecated
  deprecated_by: claim:self-loop
---
""",
                encoding="utf-8",
            )

            ontology = load_ontology()
            index = NoteIndex.build(root)
            notes, _ = collect_graph_notes([root], root=root)
            findings = []
            for note in notes:
                findings.extend(validate_note(note, ontology, index))
            codes = {finding.code for finding in findings}

            self.assertIn("KG114", codes)  # dangling successor id
            self.assertIn("KG115", codes)  # deprecated_by without explicit status
            self.assertIn("KG113", codes)  # self-supersession is an error
            self.assertEqual(
                ["KG113"],
                [finding.code for finding in findings if finding.severity == "ERROR"],
            )

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
