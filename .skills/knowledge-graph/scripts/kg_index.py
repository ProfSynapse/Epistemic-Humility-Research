#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import csv
import hashlib
import html
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX fallback
    msvcrt = None

try:
    import yaml
except ImportError:  # pragma: no cover - validated by existing KG scripts too
    yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent


# Sentinel walk-up is location-robust — correct from the canonical .skills/
# tree (3 deep) AND both mirrors (4 deep), so DEFAULT_DB always lands on the
# repo's .kg/ instead of a stray index above the checkout.
def _find_repo_root() -> Path:
    for parent in SCRIPT_DIR.parents:
        if (parent / "bin" / "sync_skills.py").is_file() or (parent / ".git").exists():
            return parent
    return SCRIPT_DIR.parents[3]


REPO_ROOT = _find_repo_root()
DEFAULT_DB = REPO_ROOT / ".kg" / "index.sqlite"
PARSER_VERSION = 2
MAX_CONFIG_GRAPH_BYTES = 512 * 1024
MAX_CONFIG_KEYS = 300

SUPPORTED_EXTS = {
    ".py",
    ".md",
    ".html",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".csv",
    ".sh",
}
IGNORED_PARTS = {
    ".git",
    ".claude",
    ".kg",
    ".obsidian",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "library/pdfs",
    ".worktrees",
}
INDEXED_DOT_DIRS = {".skills"}
# The ranking regression spec pairs search queries with the paths they must
# return. Indexing it lets the instrument answer its own measurement, so it is
# kept out of the corpus.
IGNORED_PATHS = {".skills/knowledge-graph/tests/ranking_regressions.yaml"}
PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+\.(?:py|md|json|ya?ml|jsonl|txt|csv|png|html)$")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
ALIAS_ANNOTATION_RE = re.compile(r"\([^)]*\)")
ARXIV_ID_RE = re.compile(r"(?P<id>\d{4}\.\d{4,5})(?:v\d+)?")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
MAX_TEXT_CHARS = 120_000
TEXT_CHUNK_CHARS = 4_000
MAX_TEXT_CHUNKS = 40
MAX_DATA_SAMPLE_LINES = 50
MAX_FIXTURE_FULLTEXT_BYTES = 128 * 1024


@dataclass(frozen=True)
class Chunk:
    path: str
    kind: str
    symbol: str
    symbol_type: str
    title: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class Node:
    node_id: str
    path: str
    kind: str
    label: str
    node_type: str
    line: int
    status: str = ""
    deprecated_by: str = ""


@dataclass(frozen=True)
class Edge:
    source_id: str
    target_id: str
    edge_type: str
    path: str
    evidence: str


@dataclass(frozen=True)
class ParsedFile:
    chunks: list[Chunk]
    nodes: list[Node]
    edges: list[Edge]


def repo_relative(path: Path, root: Path) -> str:
    # Fast path: index_root resolves root once and builds file paths under it,
    # so plain relative_to avoids two per-file resolve() syscall chains that
    # dominated no-change reindex time. Fall back to resolving for callers
    # that pass unnormalized paths (symlinks, relative CWD paths).
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().relative_to(root.resolve()).as_posix()


def should_ignore(rel: str) -> bool:
    if rel in IGNORED_PATHS:
        return True
    parts = rel.split("/")
    if any(part.startswith(".") and part not in INDEXED_DOT_DIRS for part in parts):
        return True
    return any(part in IGNORED_PARTS for part in parts) or any(rel.startswith(prefix + "/") for prefix in IGNORED_PARTS)


def _is_supported_source_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in SUPPORTED_EXTS
    except OSError:
        return False


def _iter_git_files(root: Path) -> list[Path]:
    proc = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={root.as_posix()}",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    rels = [item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]
    return [root / rel for rel in rels]


def _iter_walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        kept_dirs = []
        for dirname in dirnames:
            try:
                rel = repo_relative(current / dirname, root)
            except ValueError:
                continue
            if not should_ignore(rel):
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            path = current / filename
            try:
                rel = repo_relative(path, root)
            except ValueError:
                continue
            if not should_ignore(rel):
                files.append(path)
    return files


def file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".yaml", ".yml", ".json"}:
        return "config"
    if suffix == ".md":
        return "markdown"
    if suffix == ".html":
        return "html"
    if suffix == ".sh":
        return "shell"
    if suffix in {".jsonl", ".csv"}:
        return "data"
    return "text"


def iter_source_files(root: Path) -> list[Path]:
    try:
        files = _iter_git_files(root)
    except Exception:
        files = _iter_walk_files(root)
    out = []
    for path in files:
        if not _is_supported_source_file(path):
            continue
        rel = repo_relative(path, root)
        if not should_ignore(rel):
            out.append(path)
    return sorted(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_schema(conn)
    return conn


def _acquire_exclusive(handle) -> None:
    """Block until an exclusive lock on the index is held (cross-platform)."""
    if fcntl is not None:  # POSIX: a true blocking lock
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    elif msvcrt is not None:  # Windows: LK_LOCK only waits ~10s then raises, so
        handle.seek(0)        # spin on the non-blocking variant until it takes.
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.1)
    # Neither primitive available: proceed unguarded (single-process best effort).


def _release_exclusive(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:  # pragma: no cover - lock already gone
            pass


@contextmanager
def index_lock(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = db_path.with_suffix(db_path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as handle:
        _acquire_exclusive(handle)
        try:
            yield
        finally:
            _release_exclusive(handle)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS files (
          path TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          size INTEGER NOT NULL,
          mtime_ns INTEGER NOT NULL,
          sha256 TEXT NOT NULL,
          parser_version INTEGER NOT NULL,
          indexed_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
          id INTEGER PRIMARY KEY,
          path TEXT NOT NULL,
          kind TEXT NOT NULL,
          symbol TEXT NOT NULL,
          symbol_type TEXT NOT NULL,
          title TEXT NOT NULL,
          start_line INTEGER NOT NULL,
          end_line INTEGER NOT NULL,
          text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS nodes (
          node_id TEXT PRIMARY KEY,
          path TEXT NOT NULL,
          kind TEXT NOT NULL,
          label TEXT NOT NULL,
          node_type TEXT NOT NULL,
          line INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT '',
          deprecated_by TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS edges (
          id INTEGER PRIMARY KEY,
          source_id TEXT NOT NULL,
          target_id TEXT NOT NULL,
          edge_type TEXT NOT NULL,
          path TEXT NOT NULL,
          evidence TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
        CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path);
        CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
        CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
        CREATE TABLE IF NOT EXISTS search_log (
          id INTEGER PRIMARY KEY,
          query TEXT NOT NULL,
          results_json TEXT NOT NULL,
          created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback_events (
          id INTEGER PRIMARY KEY,
          search_id INTEGER,
          event_type TEXT NOT NULL,
          path TEXT NOT NULL,
          command TEXT NOT NULL DEFAULT '',
          success INTEGER,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at REAL NOT NULL,
          FOREIGN KEY(search_id) REFERENCES search_log(id)
        );
        CREATE INDEX IF NOT EXISTS idx_feedback_path ON feedback_events(path);
        CREATE INDEX IF NOT EXISTS idx_feedback_search ON feedback_events(search_id);
        CREATE TABLE IF NOT EXISTS path_memory_labels (
          path TEXT NOT NULL,
          memory_type TEXT NOT NULL,
          confidence REAL NOT NULL,
          source TEXT NOT NULL DEFAULT 'heuristic',
          updated_at REAL NOT NULL,
          PRIMARY KEY(path, memory_type, source)
        );
        CREATE INDEX IF NOT EXISTS idx_path_memory_labels_path ON path_memory_labels(path);
        CREATE INDEX IF NOT EXISTS idx_path_memory_labels_type ON path_memory_labels(memory_type);
        """
    )
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(search_log)").fetchall()
    }
    if "lane_weights_json" not in columns:
        conn.execute("ALTER TABLE search_log ADD COLUMN lane_weights_json TEXT NOT NULL DEFAULT '{}'")
    node_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(nodes)").fetchall()
    }
    for column in ("status", "deprecated_by"):
        if column not in node_columns:
            conn.execute(f"ALTER TABLE nodes ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
    ensure_fts(conn)


# Triggers keep chunks_fts in lockstep with chunks within the same transaction,
# so the two can never drift. INSERT/DELETE/UPDATE on chunks are the only writers.
_FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS chunks_fts_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, path, kind, symbol, title, text)
  VALUES (new.id, new.path, new.kind, new.symbol, new.title, new.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_fts_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, path, kind, symbol, title, text)
  VALUES ('delete', old.id, old.path, old.kind, old.symbol, old.title, old.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_fts_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, path, kind, symbol, title, text)
  VALUES ('delete', old.id, old.path, old.kind, old.symbol, old.title, old.text);
  INSERT INTO chunks_fts(rowid, path, kind, symbol, title, text)
  VALUES (new.id, new.path, new.kind, new.symbol, new.title, new.text);
END;
"""


def ensure_fts(conn: sqlite3.Connection) -> None:
    """Create the external-content FTS table + sync triggers, migrating legacy DBs.

    chunks_fts is an external-content FTS5 index (content='chunks', content_rowid='id'):
    it stores no copy of the text, only the inverted index, and is maintained purely
    by triggers. This makes chunks<->FTS drift structurally impossible. Older DBs used
    a standalone (content-less) FTS table mirrored by hand; detect those by the absence
    of `content=` in the stored DDL, drop them, recreate, and repopulate from chunks.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'chunks_fts'"
    ).fetchone()
    existing_ddl = (row["sql"] if row else "") or ""
    if row and "content=" not in existing_ddl:
        for trigger in ("chunks_fts_ai", "chunks_fts_ad", "chunks_fts_au"):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        conn.execute("DROP TABLE IF EXISTS chunks_fts")
        row = None
    if row is None:
        conn.execute(
            """
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
              path, kind, symbol, title, text,
              content='chunks', content_rowid='id'
            )
            """
        )
        # Rebuild the inverted index from whatever rows chunks already holds
        # (no-op on a fresh DB, full repopulate when migrating a legacy index).
        conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
    conn.executescript(_FTS_TRIGGERS)


def memory_labels_for_path(rel: str, kind: str) -> list[tuple[str, float]]:
    """Stable path taxonomy for routing search results by memory lane."""
    parts = set(Path(rel).parts)
    labels: list[tuple[str, float]] = []

    if rel.startswith(".skills/") or rel.startswith("skills/") or "/skills/" in rel:
        labels.append(("procedural", 0.95))
    if rel.startswith("library/"):
        labels.append(("semantic", 0.9))
    if rel.startswith("experiment/protocol/") or rel.startswith("docs/protocols/") or "protocol" in parts or "protocols" in parts or rel in {"LICENSE", "CONTRIBUTING.md"}:
        labels.append(("normative", 0.9))
    if "run_records" in parts or rel.startswith("docs/review/") or rel.startswith("docs/sessions/"):
        labels.append(("episodic", 0.85))
    if "TODO" in Path(rel).name.upper() or "issues" in parts or "roadmap" in rel.casefold():
        labels.append(("prospective", 0.8))
    if "tests" in parts or rel.startswith("docs/review/"):
        labels.append(("evaluative", 0.75))
    if kind in {"config", "data"} or "config" in parts or "recipes" in parts or "manifests" in parts:
        labels.append(("artifact", 0.85))
    elif kind in {"python", "shell"}:
        labels.append(("artifact", 0.6))

    if not labels:
        labels.append(("semantic" if kind in {"markdown", "html"} else "artifact", 0.5))
    return labels


def delete_file_rows(conn: sqlite3.Connection, rel: str) -> None:
    # Deleting from chunks fires chunks_fts_ad, which removes the matching FTS
    # rows in the same transaction — no manual chunks_fts bookkeeping needed.
    conn.execute("DELETE FROM chunks WHERE path = ?", (rel,))
    conn.execute("DELETE FROM nodes WHERE path = ?", (rel,))
    conn.execute("DELETE FROM edges WHERE path = ?", (rel,))
    conn.execute("DELETE FROM path_memory_labels WHERE path = ? AND source = 'heuristic'", (rel,))
    conn.execute("DELETE FROM files WHERE path = ?", (rel,))


def insert_chunk(conn: sqlite3.Connection, chunk: Chunk) -> None:
    # Inserting into chunks fires chunks_fts_ai, which indexes the new row in the
    # same transaction. chunks_fts (external-content) is never written directly.
    conn.execute(
        """
        INSERT INTO chunks(path, kind, symbol, symbol_type, title, start_line, end_line, text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            chunk.path,
            chunk.kind,
            chunk.symbol,
            chunk.symbol_type,
            chunk.title,
            chunk.start_line,
            chunk.end_line,
            chunk.text,
        ),
    )


def insert_node(conn: sqlite3.Connection, node: Node) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO nodes(node_id, path, kind, label, node_type, line, status, deprecated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (node.node_id, node.path, node.kind, node.label, node.node_type, node.line, node.status, node.deprecated_by),
    )


def insert_edge(conn: sqlite3.Connection, edge: Edge) -> None:
    conn.execute(
        """
        INSERT INTO edges(source_id, target_id, edge_type, path, evidence)
        VALUES (?, ?, ?, ?, ?)
        """,
        (edge.source_id, edge.target_id, edge.edge_type, edge.path, edge.evidence),
    )


def insert_path_memory_labels(conn: sqlite3.Connection, rel: str, kind: str) -> None:
    now = time.time()
    for memory_type, confidence in memory_labels_for_path(rel, kind):
        conn.execute(
            """
            INSERT OR REPLACE INTO path_memory_labels(path, memory_type, confidence, source, updated_at)
            VALUES (?, ?, ?, 'heuristic', ?)
            """,
            (rel, memory_type, confidence, now),
        )


def lines_for_node(lines: list[str], node: ast.AST) -> tuple[int, int, str]:
    start = int(getattr(node, "lineno", 1))
    end = int(getattr(node, "end_lineno", start))
    text = "\n".join(lines[start - 1 : end])
    return start, end, text


def qualname(parent: str, name: str) -> str:
    return f"{parent}.{name}" if parent else name


def node_id_for_symbol(rel: str, name: str) -> str:
    return f"code:{rel}:{name}"


def _exists_safe(candidate: Path) -> bool:
    """exists() that treats an unreadable path as absent.

    Config values can name absolute paths on dead mounts (e.g. a stale
    network/9P mount), where stat() raises OSError instead of returning
    False; the indexer must not die on someone else's provenance string."""
    try:
        return candidate.exists()
    except OSError:
        return False


def module_to_internal_rel(root: Path, module: str) -> str | None:
    module_path = Path(*module.split("."))
    candidates = [root / f"{module_path}.py", root / module_path / "__init__.py"]
    for candidate in candidates:
        if _exists_safe(candidate) and candidate.is_file():
            return repo_relative(candidate, root)
    return None


def parse_python(root: Path, path: Path, rel: str, text: str) -> ParsedFile:
    kind = "python"
    file_id = f"file:{rel}"
    lines = text.splitlines()
    nodes = [Node(file_id, rel, kind, rel, "code_file", 1)]
    edges: list[Edge] = []
    chunks: list[Chunk] = [
        Chunk(rel, kind, rel, "file", rel, 1, max(1, len(lines)), text[:6000])
    ]
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        chunks.append(Chunk(rel, kind, rel, "syntax_error", f"Syntax error in {rel}", exc.lineno or 1, exc.lineno or 1, str(exc)))
        return ParsedFile(chunks, nodes, edges)

    local_symbols: dict[str, str] = {}

    def visit_defs(body: Iterable[ast.stmt], parent: str = "") -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = qualname(parent, stmt.name)
                symbol_id = node_id_for_symbol(rel, name)
                local_symbols[stmt.name] = symbol_id
                local_symbols[name] = symbol_id
                node_type = "code_class" if isinstance(stmt, ast.ClassDef) else "code_function"
                start, end, body_text = lines_for_node(lines, stmt)
                nodes.append(Node(symbol_id, rel, kind, name, node_type, start))
                edges.append(Edge(file_id, symbol_id, "contains", rel, f"{rel}:{start}"))
                edges.append(Edge(symbol_id, file_id, "defined_in", rel, f"{rel}:{start}"))
                chunks.append(Chunk(rel, kind, name, node_type, name, start, end, body_text))
                nested = getattr(stmt, "body", [])
                visit_defs(nested, name)

    visit_defs(tree.body)

    imports: list[str] = []
    for stmt in ast.walk(tree):
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                imports.append(alias.name)
        elif isinstance(stmt, ast.ImportFrom) and stmt.module:
            imports.append(stmt.module)
    for module in sorted(set(imports)):
        internal_rel = module_to_internal_rel(root, module)
        if internal_rel:
            target = f"file:{internal_rel}"
            edges.append(Edge(file_id, target, "imports", rel, module))
        else:
            target = f"external:{module}"
            nodes.append(Node(target, rel, "external", module, "external_module", 1))
            edges.append(Edge(file_id, target, "imports", rel, module))
    if imports:
        chunks.append(Chunk(rel, kind, "imports", "imports", f"Imports in {rel}", 1, 1, "\n".join(sorted(set(imports)))))

    parent_stack: list[str] = []

    class CallVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            parent_stack.append(node.name if not parent_stack else f"{parent_stack[-1]}.{node.name}")
            self.generic_visit(node)
            parent_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            parent_stack.append(node.name if not parent_stack else f"{parent_stack[-1]}.{node.name}")
            self.generic_visit(node)
            parent_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            caller = local_symbols.get(parent_stack[-1]) if parent_stack else file_id
            target_name = ""
            if isinstance(node.func, ast.Name):
                target_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target_name = node.func.attr
            target = local_symbols.get(target_name)
            if caller and target and caller != target:
                edges.append(Edge(caller, target, "calls", rel, f"{rel}:{getattr(node, 'lineno', 1)}"))
            self.generic_visit(node)

    CallVisitor().visit(tree)
    return ParsedFile(chunks, nodes, edges)


def flatten_config(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_config(child, child_key)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            child_key = f"{prefix}[{idx}]"
            yield from flatten_config(child, child_key)
    else:
        yield prefix, value


def normalize_config_path_ref(root: Path, rel: str, value: str) -> str:
    raw = Path(value)
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(root / raw)
        candidates.append(root / Path(rel).parent / raw)
        parts = [part for part in raw.parts if part not in {"..", "."}]
        if parts:
            candidates.append(root.joinpath(*parts))
    for candidate in candidates:
        if _exists_safe(candidate):
            try:
                return repo_relative(candidate.resolve(), root)
            except (ValueError, OSError):
                return value
    fallback = candidates[0]
    try:
        return repo_relative(fallback.resolve(), root)
    except (ValueError, OSError):
        return value


def should_index_config_path_ref(key: str, value: str) -> bool:
    if not PATH_RE.match(value):
        return False
    key_lower = key.lower()
    leaf = key_lower.rsplit(".", 1)[-1]
    if key_lower.startswith("output.") and (leaf.endswith("filename") or leaf.endswith("_filename")):
        return False
    return True


def parse_config(root: Path, path: Path, rel: str, text: str) -> ParsedFile:
    kind = "config"
    file_id = f"file:{rel}"
    nodes = [Node(file_id, rel, kind, rel, "config_file", 1)]
    edges: list[Edge] = []
    chunks = [Chunk(rel, kind, rel, "file", rel, 1, max(1, len(text.splitlines())), text[:6000])]
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            if yaml is None:
                data = {}
            else:
                data = yaml.safe_load(text) or {}
    except Exception as exc:
        chunks.append(Chunk(rel, kind, rel, "parse_error", f"Parse error in {rel}", 1, 1, str(exc)))
        return ParsedFile(chunks, nodes, edges)

    summary: list[str] = []
    truncated = False
    for idx, (key, value) in enumerate(flatten_config(data)):
        if idx >= MAX_CONFIG_KEYS:
            truncated = True
            break
        if not key:
            continue
        node_id = f"config:{rel}:{key}"
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
        nodes.append(Node(node_id, rel, kind, key, "config_key", 1))
        edges.append(Edge(file_id, node_id, "contains_key", rel, key))
        summary.append(f"{key}: {rendered}")
        if isinstance(value, str) and should_index_config_path_ref(key, value):
            target_rel = normalize_config_path_ref(root, rel, value)
            edges.append(Edge(node_id, f"file:{target_rel}", "references_path", rel, value))
    if summary:
        if truncated:
            summary.append(f"... truncated after {MAX_CONFIG_KEYS} config keys")
        chunks.append(Chunk(rel, kind, "config_keys", "config_keys", f"Config keys in {rel}", 1, 1, "\n".join(summary[:400])))
    return ParsedFile(chunks, nodes, edges)


def parse_frontmatter_kg(rel: str, text: str) -> tuple[list[Node], list[Edge]]:
    if yaml is None:
        return [], []
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [], []
    try:
        fm = yaml.safe_load(match.group("body")) or {}
    except Exception:
        return [], []
    if not isinstance(fm, dict):
        return [], []
    kg = fm.get("kg")
    if not isinstance(kg, dict) or not kg.get("id"):
        return [], []
    kg_id = str(kg["id"])
    title = str(fm.get("title") or Path(rel).stem)
    deprecated_by = str(kg.get("deprecated_by") or "")
    status = str(kg.get("status") or "")
    if deprecated_by and not status:
        status = "deprecated"
    nodes = [Node(kg_id, rel, "kg_note", title, str(kg.get("type") or "kg_note"), 1, status, deprecated_by)]
    edges: list[Edge] = [Edge(f"file:{rel}", kg_id, "describes", rel, title)]
    if deprecated_by and deprecated_by != kg_id:
        edges.append(Edge(kg_id, deprecated_by, "superseded_by", rel, f"kg.deprecated_by in {rel}"))
    relationships = fm.get("relationships") or []
    if isinstance(relationships, list):
        for item in relationships:
            if isinstance(item, dict) and item.get("type"):
                target_id = item.get("target_id") or item.get("target") or ""
                if target_id:
                    edges.append(Edge(kg_id, str(target_id), str(item["type"]), rel, str(item.get("evidence") or "")))
    return nodes, edges


def frontmatter_identity_chunk(rel: str, kind: str, text: str) -> Chunk | None:
    """A short chunk carrying a note's frontmatter title, aliases and tags.

    Section chunks start at the first heading, so for any note with headings the
    whole frontmatter block -- including the aliases the vault convention relies
    on for retrieval -- was in no chunk at all and could not be searched. Even
    for heading-less notes the identity was unreachable to the title/symbol
    boosts, because those carry the file path rather than the human title.

    Keeping it short and separate is deliberate: bm25 rewards a match in a small
    field, so an alias hit outranks the same word buried in a long body.
    """
    if yaml is None:
        return None
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        fm = yaml.safe_load(match.group("body")) or {}
    except Exception:
        return None
    if not isinstance(fm, dict):
        return None

    title = str(fm.get("title") or "").strip()
    aliases = [str(item).strip() for item in (fm.get("aliases") or []) if str(item).strip()]
    kg = fm.get("kg") if isinstance(fm.get("kg"), dict) else {}
    node_id = str(kg.get("id") or "").strip()
    if not (title or aliases or node_id):
        return None

    # Tags are deliberately excluded. They are a coarse topical grouping shared
    # by dozens of notes, and in a chunk this short bm25 weights them as heavily
    # as a title, so a tag like `margin-theory` pulls every note carrying it
    # above the note the query actually names. Identity only: title, aliases, id.
    label = title or Path(rel).stem
    body = [label, *aliases]
    if node_id:
        body.append(node_id)
    end_line = text[: match.end()].count("\n") + 1
    # An alias is an alternative title, so it belongs on the symbol surface the
    # title/phrase boosts read -- not only in the body text bm25 sees. `title`
    # stays the clean label because that is what gets printed.
    #
    # Parentheticals are dropped from that surface: the vault writes them as
    # annotations about the alias ("doubt direction (retired name, see
    # margin-theory-framework.md)"), not as part of the name, and matching a
    # cross-reference inside one lets an unrelated note claim the phrase boost.
    # The full alias stays in the body text, so the words remain searchable.
    names = [ALIAS_ANNOTATION_RE.sub(" ", alias).strip() for alias in aliases]
    symbol = " | ".join([label, *(name for name in names if name)])
    return Chunk(rel, kind, symbol, "frontmatter", label, 1, end_line, "\n".join(body)[:6000])


def parse_markdown(rel: str, text: str) -> ParsedFile:
    kind = "markdown"
    file_id = f"file:{rel}"
    nodes = [Node(file_id, rel, kind, rel, "doc_file", 1)]
    kg_nodes, kg_edges = parse_frontmatter_kg(rel, text)
    nodes.extend(kg_nodes)
    edges = kg_edges
    chunks: list[Chunk] = []
    identity = frontmatter_identity_chunk(rel, kind, text)
    if identity is not None:
        chunks.append(identity)
    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                headings.append((idx, title))
    if not headings:
        chunks.append(Chunk(rel, kind, rel, "file", rel, 1, max(1, len(lines)), text[:6000]))
    else:
        for i, (start, title) in enumerate(headings):
            end = headings[i + 1][0] - 1 if i + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start - 1 : end])
            chunks.append(Chunk(rel, kind, title, "section", title, start, end, body[:6000]))
    return ParsedFile(chunks, nodes, edges)


def strip_html_text(text: str) -> str:
    text = HTML_SCRIPT_STYLE_RE.sub(" ", text)
    text = HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def chunk_plain_text(rel: str, kind: str, text: str, title: str = "") -> list[Chunk]:
    clean = text[:MAX_TEXT_CHARS]
    chunks = []
    if not clean:
        return [Chunk(rel, kind, rel, "file", title or rel, 1, 1, "")]
    for idx in range(0, len(clean), TEXT_CHUNK_CHARS):
        if len(chunks) >= MAX_TEXT_CHUNKS:
            break
        part = clean[idx : idx + TEXT_CHUNK_CHARS]
        chunk_no = len(chunks) + 1
        chunks.append(
            Chunk(
                rel,
                kind,
                f"{rel}#chunk-{chunk_no}",
                "text_chunk",
                title or f"{rel} chunk {chunk_no}",
                1,
                1,
                part,
            )
        )
    return chunks


def parse_html(rel: str, text: str) -> ParsedFile:
    kind = "html"
    file_id = f"file:{rel}"
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    title = strip_html_text(title_match.group(1)) if title_match else rel
    nodes = [Node(file_id, rel, kind, rel, "html_file", 1)]
    edges: list[Edge] = []
    arxiv_match = ARXIV_ID_RE.search(Path(rel).name)
    if arxiv_match:
        paper_id = f"paper:{arxiv_match.group('id')}"
        edges.append(Edge(file_id, paper_id, "fulltext_for", rel, arxiv_match.group("id")))
        nodes.append(Node(paper_id, rel, "kg_note", paper_id, "paper", 1))
    chunks = chunk_plain_text(rel, kind, strip_html_text(text), title)
    return ParsedFile(chunks, nodes, edges)


def is_fixture_path(rel: str) -> bool:
    parts = set(Path(rel).parts)
    return "fixtures" in parts or "fixture" in parts


def count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def sample_text_lines(path: Path, limit: int = MAX_DATA_SAMPLE_LINES) -> list[str]:
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
            if len(lines) >= limit:
                break
    return lines


def parse_data_artifact(path: Path, rel: str) -> ParsedFile:
    kind = "data"
    file_id = f"file:{rel}"
    stat = path.stat()
    metadata = [
        f"path: {rel}",
        f"format: {path.suffix.lower().lstrip('.')}",
        f"size_bytes: {stat.st_size}",
    ]

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            first_line = handle.readline()
        try:
            columns = next(csv.reader([first_line])) if first_line else []
        except csv.Error:
            columns = []
        if columns:
            metadata.append("columns: " + ", ".join(column.strip() for column in columns if column.strip()))
        metadata.append(f"rows_approx: {max(0, count_lines(path) - 1)}")
    else:
        keys: set[str] = set()
        samples = sample_text_lines(path)
        for line in samples:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                keys.update(str(key) for key in obj.keys())
        if keys:
            metadata.append("jsonl_keys_sampled: " + ", ".join(sorted(keys)))
        metadata.append(f"rows_approx: {count_lines(path)}")
        metadata.append(f"sample_lines_scanned: {len(samples)}")

    chunks = [
        Chunk(
            rel,
            kind,
            f"{rel}#metadata",
            "data_metadata",
            f"Data artifact metadata for {rel}",
            1,
            1,
            "\n".join(metadata),
        )
    ]
    if is_fixture_path(rel) and stat.st_size <= MAX_FIXTURE_FULLTEXT_BYTES:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(chunk_plain_text(rel, "data_fixture", text, rel))
    return ParsedFile(chunks, [Node(file_id, rel, kind, rel, "data_file", 1)], [])


def parse_text(rel: str, text: str, kind: str) -> ParsedFile:
    file_id = f"file:{rel}"
    return ParsedFile(
        chunk_plain_text(rel, kind, text, rel),
        [Node(file_id, rel, kind, rel, f"{kind}_file", 1)],
        [],
    )


def parse_file(root: Path, path: Path, rel: str) -> ParsedFile:
    kind = file_kind(path)
    if kind == "data":
        return parse_data_artifact(path, rel)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    if kind == "python":
        return parse_python(root, path, rel, text)
    if kind == "config":
        if path.stat().st_size > MAX_CONFIG_GRAPH_BYTES:
            return parse_text(rel, text, "data")
        return parse_config(root, path, rel, text)
    if kind == "markdown":
        return parse_markdown(rel, text)
    if kind == "html":
        return parse_html(rel, text)
    return parse_text(rel, text, kind)


def index_file(conn: sqlite3.Connection, root: Path, path: Path, force: bool = False) -> bool:
    rel = repo_relative(path, root)
    stat = path.stat()
    row = conn.execute(
        "SELECT size, mtime_ns, sha256, parser_version FROM files WHERE path = ?", (rel,)
    ).fetchone()
    # Stat short-circuit: skip hashing entirely when size + mtime_ns match the
    # stored row. Hashing every file made the pre-search lazy reindex O(total
    # repo bytes) per search, which grows with every dataset/output that lands.
    if (
        not force
        and row
        and row["parser_version"] == PARSER_VERSION
        and row["size"] == stat.st_size
        and row["mtime_ns"] == stat.st_mtime_ns
    ):
        return False
    digest = sha256_file(path)
    if not force and row and row["sha256"] == digest and row["parser_version"] == PARSER_VERSION:
        # Content unchanged but stat drifted (touch, fresh checkout): refresh
        # the stored stat so future runs take the no-hash fast path.
        conn.execute(
            "UPDATE files SET size = ?, mtime_ns = ?, indexed_at = ? WHERE path = ?",
            (stat.st_size, stat.st_mtime_ns, time.time(), rel),
        )
        return False
    parsed = parse_file(root, path, rel)
    delete_file_rows(conn, rel)
    for chunk in parsed.chunks:
        insert_chunk(conn, chunk)
    for node in parsed.nodes:
        insert_node(conn, node)
    for edge in parsed.edges:
        insert_edge(conn, edge)
    kind = file_kind(path)
    insert_path_memory_labels(conn, rel, kind)
    conn.execute(
        """
        INSERT INTO files(path, kind, size, mtime_ns, sha256, parser_version, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (rel, kind, stat.st_size, stat.st_mtime_ns, digest, PARSER_VERSION, time.time()),
    )
    return True


def remove_deleted(conn: sqlite3.Connection, present: set[str]) -> int:
    rows = conn.execute("SELECT path FROM files").fetchall()
    removed = 0
    for row in rows:
        rel = row["path"]
        if rel not in present:
            delete_file_rows(conn, rel)
            removed += 1
    return removed


def index_root(root: Path, db_path: Path = DEFAULT_DB, force: bool = False) -> dict[str, int]:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"index root does not exist or is not a directory: {root}")
    with index_lock(db_path):
        conn = connect(db_path)
        files = iter_source_files(root)
        present = {repo_relative(path, root) for path in files}
        changed = 0
        try:
            with conn:
                removed = remove_deleted(conn, present)
                for path in files:
                    if index_file(conn, root, path, force=force):
                        changed += 1
            total = conn.execute("SELECT COUNT(*) AS n FROM files").fetchone()["n"]
            chunks = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
            nodes = conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]
            edges = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]
        finally:
            conn.close()
    return {"files": total, "changed": changed, "removed": removed, "chunks": chunks, "nodes": nodes, "edges": edges}


def dangling_references(db_path: Path = DEFAULT_DB) -> list[dict[str, str]]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT source_id, target_id, edge_type, path, evidence
            FROM edges
            WHERE edge_type = 'references_path'
            ORDER BY path, source_id, target_id
            """
        ).fetchall()
        out: list[dict[str, str]] = []
        for row in rows:
            target_id = str(row["target_id"])
            if not target_id.startswith("file:"):
                continue
            target_path = target_id[5:]
            exists = conn.execute("SELECT 1 FROM files WHERE path = ? LIMIT 1", (target_path,)).fetchone()
            if exists:
                continue
            out.append(
                {
                    "source_id": str(row["source_id"]),
                    "target_id": target_id,
                    "path": str(row["path"]),
                    "evidence": str(row["evidence"]),
                }
            )
        return out
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/update the local code/config/research KG search index.")
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Repository root. Defaults to the repo root, not the CWD, so the "
        "shared --db index stays consistent regardless of where the tool runs.",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite index path. Defaults to .kg/index.sqlite.")
    parser.add_argument("--force", action="store_true", help="Reparse every supported file.")
    parser.add_argument("--dangling", action="store_true", help="Report indexed config path references whose targets are missing.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()
    summary = index_root(Path(args.root), Path(args.db), force=args.force)
    if args.dangling:
        dangling = dangling_references(Path(args.db))
        if args.json:
            print(json.dumps({"summary": summary, "dangling_references": dangling}, indent=2, sort_keys=True))
        else:
            print(
                "Indexed {files} files ({changed} changed, {removed} removed), "
                "{chunks} chunks, {nodes} nodes, {edges} edges".format(**summary)
            )
            if not dangling:
                print("No dangling references_path edges.")
            else:
                print(f"Dangling references_path edges: {len(dangling)}")
                for item in dangling[:50]:
                    print(f"- {item['path']}: {item['source_id']} -> {item['target_id']} ({item['evidence']})")
        return 1 if dangling else 0
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "Indexed {files} files ({changed} changed, {removed} removed), "
            "{chunks} chunks, {nodes} nodes, {edges} edges".format(**summary)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
