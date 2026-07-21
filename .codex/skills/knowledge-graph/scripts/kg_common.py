from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required. Install pyyaml or run in the Codex workspace runtime.") from exc


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


# Sentinel walk-up is location-robust — correct from the canonical .skills/
# tree (2 deep to the root) AND both mirrors (3 deep), so default-root script
# runs anchor on the repo checkout rather than on .agents/ or .claude/.
def _find_vault_root() -> Path:
    for parent in SKILL_DIR.parents:
        if (parent / "bin" / "sync_skills.py").is_file() or (parent / ".git").exists():
            return parent
    return SKILL_DIR.parents[1]


VAULT_ROOT = _find_vault_root()
DEFAULT_ONTOLOGY = SKILL_DIR / "references" / "edge-ontology.yaml"

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", re.S)
WIKILINK_RE = re.compile(r"\[\[(?P<target>[^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
LEGACY_RELATIONSHIP_RE = re.compile(r"^\s*#(?P<edge>[A-Za-z][A-Za-z0-9_-]*)\s+(?P<targets>.+?)\s*$")
EDGE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
IGNORED_DIRS = {
    ".git",
    ".obsidian",
    ".trash",
    ".codex",
    ".claude",
    "node_modules",
    "cache",
    "log",
    "logs",
    "tmp",
    "temp",
    "export",
    "exports",
    "__pycache__",
}

CONFIDENCE_VALUES = {"high", "medium", "low"}
RELATIONSHIP_STATUS_VALUES = {"current", "historical", "disputed", "proposed", "deprecated"}
KG_STATUS_VALUES = {"canonical", "alias", "draft", "external", "deprecated"}
RELATIONSHIP_KEYS = {
    "type",
    "target",
    "target_id",
    "confidence",
    "evidence",
    "start",
    "end",
    "status",
    "note",
}


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class ParsedNote:
    path: Path
    frontmatter: dict[str, Any]

    @property
    def title(self) -> str:
        title = self.frontmatter.get("title")
        return str(title) if title else self.path.stem

    @property
    def kg(self) -> dict[str, Any]:
        value = self.frontmatter.get("kg")
        return value if isinstance(value, dict) else {}

    @property
    def kg_id(self) -> str:
        value = self.kg.get("id")
        return str(value) if value else ""

    @property
    def kg_type(self) -> str:
        value = self.kg.get("type")
        return str(value) if value else ""


@dataclass
class Triple:
    source_path: str
    source: str
    source_id: str
    source_type: str
    edge_type: str
    target: str
    target_id: str
    target_path: str
    confidence: str
    status: str
    start: str
    end: str
    evidence: list[str]
    legacy: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source": self.source,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "edge_type": self.edge_type,
            "target": self.target,
            "target_id": self.target_id,
            "target_path": self.target_path,
            "confidence": self.confidence,
            "status": self.status,
            "start": self.start,
            "end": self.end,
            "evidence": self.evidence,
            "legacy": self.legacy,
        }


def rel_path(path: Path, root: Path = VAULT_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def is_ignored(path: Path, root: Path | None = None) -> bool:
    """Check ignore names against root-relative parts only, so an ancestor of
    the vault itself (e.g. a checkout under /tmp) never suppresses its notes."""
    parts = path.parts
    if root is not None:
        try:
            parts = path.resolve().relative_to(root.resolve()).parts
        except ValueError:
            pass
    return any(part in IGNORED_DIRS for part in parts)


def iter_markdown(paths: list[Path], root: Path = VAULT_ROOT) -> list[Path]:
    if not paths:
        paths = [root]
    found: list[Path] = []
    for path in paths:
        if not path.is_absolute():
            path = root / path
        if not path.exists():
            found.append(path)
            continue
        if path.is_file() and path.suffix.lower() == ".md" and not is_ignored(path, root):
            found.append(path)
        elif path.is_dir():
            found.extend(
                sorted(
                    child
                    for child in path.rglob("*.md")
                    if child.is_file() and not is_ignored(child, root)
                )
            )
    return found


def read_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, "file is not valid UTF-8"
    except FileNotFoundError:
        return None, "file does not exist"

    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, "missing YAML frontmatter"
    try:
        data = yaml.safe_load(match.group("body")) or {}
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    return data, None


def parse_note(path: Path) -> tuple[ParsedNote | None, str | None]:
    frontmatter, error = read_frontmatter(path)
    if error:
        return None, error
    assert frontmatter is not None
    return ParsedNote(path=path, frontmatter=frontmatter), None


def is_graph_note(frontmatter: dict[str, Any]) -> bool:
    return any(key in frontmatter for key in ("kg", "relationships", "related"))


def load_ontology(path: Path = DEFAULT_ONTOLOGY) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"ontology must be a mapping: {path}")
    edges = data.get("edges")
    if not isinstance(edges, dict):
        raise ValueError(f"ontology must define an edges mapping: {path}")
    aliases: dict[str, str] = {}
    for edge, spec in edges.items():
        if not isinstance(spec, dict):
            continue
        for alias in spec.get("aliases") or []:
            aliases[str(alias)] = str(edge)
    data["_aliases"] = aliases
    return data


def canonical_edge(edge: str, ontology: dict[str, Any]) -> tuple[str, bool]:
    normalized = edge.strip().lstrip("#").replace("-", "_")
    aliases = ontology.get("_aliases", {})
    if normalized in aliases:
        return str(aliases[normalized]), True
    return normalized, False


def extract_wikilinks(value: str) -> list[str]:
    return [match.group("target").strip() for match in WIKILINK_RE.finditer(value)]


def normalize_link_target(value: str) -> str:
    target = value.strip()
    match = WIKILINK_RE.search(target)
    if match:
        target = match.group("target")
    if "#" in target:
        target = target.split("#", 1)[0]
    if "|" in target:
        target = target.split("|", 1)[0]
    if target.endswith(".md"):
        target = target[:-3]
    return target.strip()


def link_key(value: str) -> str:
    return normalize_link_target(value).casefold()


def coerce_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [coerce_str(item) for item in value]
    return [coerce_str(value)]


class NoteIndex:
    def __init__(self, root: Path = VAULT_ROOT) -> None:
        self.root = root
        self.by_title: dict[str, list[ParsedNote]] = {}
        self.by_path: dict[str, ParsedNote] = {}
        self.by_id: dict[str, ParsedNote] = {}

    @classmethod
    def build(cls, root: Path = VAULT_ROOT) -> "NoteIndex":
        index = cls(root)
        for path in iter_markdown([root], root=root):
            note, error = parse_note(path)
            if error or note is None:
                continue
            index.add(note)
        return index

    def add(self, note: ParsedNote) -> None:
        path_no_ext = rel_path(note.path, self.root)
        if path_no_ext.endswith(".md"):
            path_no_ext = path_no_ext[:-3]
        self.by_path[path_no_ext.casefold()] = note
        self.by_title.setdefault(note.path.stem.casefold(), []).append(note)
        title = note.frontmatter.get("title")
        if title:
            self.by_title.setdefault(str(title).casefold(), []).append(note)
        aliases = note.frontmatter.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        if isinstance(aliases, list):
            for alias in aliases:
                if alias:
                    self.by_title.setdefault(str(alias).casefold(), []).append(note)
        if note.kg_id:
            self.by_id[note.kg_id] = note

    def resolve_link(self, target: str) -> tuple[ParsedNote | None, str]:
        normalized = normalize_link_target(target)
        if not normalized:
            return None, "empty"
        path_match = self.by_path.get(normalized.casefold())
        if path_match:
            return path_match, "ok"
        matches = self.by_title.get(normalized.casefold(), [])
        unique = unique_notes(matches)
        if len(unique) == 1:
            return unique[0], "ok"
        if len(unique) > 1:
            return None, "ambiguous"
        return None, "missing"


def unique_notes(notes: Iterable[ParsedNote]) -> list[ParsedNote]:
    seen: set[Path] = set()
    unique: list[ParsedNote] = []
    for note in notes:
        if note.path in seen:
            continue
        seen.add(note.path)
        unique.append(note)
    return unique


def relationship_targets(entry: Any) -> list[str]:
    if isinstance(entry, dict):
        target = entry.get("target")
        return [target] if isinstance(target, str) and target else []
    if isinstance(entry, str):
        match = LEGACY_RELATIONSHIP_RE.match(entry)
        if not match:
            return []
        return extract_wikilinks(match.group("targets"))
    return []


def relationship_to_triples(
    note: ParsedNote,
    entry: Any,
    ontology: dict[str, Any],
    index: NoteIndex | None = None,
) -> list[Triple]:
    triples: list[Triple] = []
    edge = ""
    targets: list[str] = []
    target_id = ""
    confidence = ""
    status = ""
    start = ""
    end = ""
    evidence: list[str] = []
    legacy = False

    if isinstance(entry, dict):
        edge = coerce_str(entry.get("type"))
        targets = relationship_targets(entry)
        target_id = coerce_str(entry.get("target_id"))
        confidence = coerce_str(entry.get("confidence"))
        status = coerce_str(entry.get("status"))
        start = coerce_str(entry.get("start"))
        end = coerce_str(entry.get("end"))
        evidence = coerce_str_list(entry.get("evidence"))
    elif isinstance(entry, str):
        match = LEGACY_RELATIONSHIP_RE.match(entry)
        if not match:
            return []
        edge = match.group("edge")
        targets = extract_wikilinks(match.group("targets"))
        legacy = True
    else:
        return []

    edge, _ = canonical_edge(edge, ontology)
    for target in targets:
        resolved, state = index.resolve_link(target) if index else (None, "missing")
        resolved_id = resolved.kg_id if resolved else ""
        triples.append(
            Triple(
                source_path=rel_path(note.path),
                source=note.title,
                source_id=note.kg_id,
                source_type=note.kg_type,
                edge_type=edge,
                target=normalize_link_target(target),
                target_id=target_id or resolved_id,
                target_path=rel_path(resolved.path) if resolved else "",
                confidence=confidence,
                status=status,
                start=start,
                end=end,
                evidence=evidence,
                legacy=legacy,
            )
        )
    return triples


def collect_graph_notes(paths: list[Path], root: Path = VAULT_ROOT) -> tuple[list[ParsedNote], list[Finding]]:
    notes: list[ParsedNote] = []
    findings: list[Finding] = []
    for path in iter_markdown(paths, root=root):
        if path.name.startswith("_"):
            continue
        if not path.exists():
            findings.append(Finding("ERROR", "KG001", rel_path(path, root), "path does not exist"))
            continue
        note, error = parse_note(path)
        if error:
            if error == "missing YAML frontmatter":
                continue
            findings.append(Finding("WARN", "KG002", rel_path(path, root), error))
            continue
        assert note is not None
        if is_graph_note(note.frontmatter):
            notes.append(note)
    return notes, findings


def collect_triples(
    notes: list[ParsedNote],
    ontology: dict[str, Any],
    index: NoteIndex | None = None,
) -> list[Triple]:
    triples: list[Triple] = []
    for note in notes:
        relationships = note.frontmatter.get("relationships") or []
        if not isinstance(relationships, list):
            continue
        for entry in relationships:
            triples.extend(relationship_to_triples(note, entry, ontology, index=index))
    return triples
