"""Global, content-addressed cache for call-graph extraction.

``CallGraph.build`` re-parses every source file on every run. Parsing dominates
the cost; the extraction it produces (``walk_tree`` definitions + call sites and
``walk_imports`` imports) is a pure function of a single file's bytes. This
module memoises that extraction in a global store keyed by file *content*, so the
same file hits the same entry regardless of which project root reached it — which
is what makes repeat runs and monorepo / nested invocations cheap.

Design notes live in ``docs/design/global-extraction-cache.md``. Key points:

- The key is ``blake2b(bytes + language + version + grammar_fingerprint)`` —
  content, not path.
- ``_EXTRACT_VERSION`` (this project's extractor) AND the installed
  ``tree-sitter*`` package versions are in the key, so any upgrade that can
  change extraction output — ours or a grammar's — invalidates every entry.
- The cache is best-effort: any I/O or decode failure falls back to a live parse.
  A broken cache can never fail a build or return a stale answer.
- Objects are immutable, written temp-then-atomic-rename, so concurrent
  invocations (monorepo CI) need no locking.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import tempfile
from importlib import metadata as _metadata
from pathlib import Path
from typing import Any

#: Bump when the shape of ``walk_tree`` / ``walk_imports`` output changes, so an
#: upgraded extractor never reads entries written by an older one.
_EXTRACT_VERSION = 1


@functools.lru_cache(maxsize=1)
def _grammar_fingerprint() -> str:
    """Digest of installed ``tree-sitter*`` package versions (computed once).

    Extraction output depends on the tree-sitter core and grammar libraries,
    which are versioned independently with open ranges (``tree-sitter-typescript
    >=0.23.2,<0.25.0`` etc.). A grammar upgrade within range can change the parse
    tree with no change to this project's code and no ``_EXTRACT_VERSION`` bump —
    so identical content would otherwise hit a stale entry. Folding the installed
    versions into the key invalidates the cache whenever any tree-sitter package
    changes: conservative (any grammar bump invalidates all languages) but always
    correct, and entries are cheap to rebuild. Best-effort — an unreadable
    environment yields a constant, degrading to content+version keying only.
    """
    try:
        dists = list(_metadata.distributions())
    except Exception:  # pragma: no cover - defensive: never let metadata break the cache
        return "unknown"
    parts: list[str] = []
    for dist in dists:
        # Per-distribution guard: a single corrupt/half-installed package must not
        # collapse the whole fingerprint (and, via lru_cache, disable grammar
        # invalidation for the process). Skip the bad one, keep the rest.
        try:
            name = (dist.metadata.get("Name") or "").lower()
            if name.startswith(("tree-sitter", "tree_sitter")):
                parts.append(f"{name}=={dist.version}")
        except Exception:  # pragma: no cover - defensive per-distribution skip
            continue
    return hashlib.blake2b(
        "\n".join(sorted(parts)).encode("utf-8"), digest_size=8
    ).hexdigest()

#: Extraction record: (definitions, calls, imports).
Extraction = tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]


def is_disabled() -> bool:
    """True when the cache is turned off via ``TSA_DISABLE_GRAPH_CACHE``."""
    return bool(os.environ.get("TSA_DISABLE_GRAPH_CACHE"))


def resolve_cache_dir() -> Path:
    """Locate the global store: explicit override, then XDG, then ``~/.cache``."""
    override = os.environ.get("TSA_CACHE_DIR")
    if override:
        return Path(override)
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "tree-sitter-analyzer" / "graph-extract"


class GraphExtractionCache:
    """Content-addressed store for per-file call-graph extraction."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir if cache_dir is not None else resolve_cache_dir()

    def _object_path(self, content: bytes, language: str) -> Path:
        key_material = b"\0".join(
            (
                content,
                language.encode("utf-8"),
                str(_EXTRACT_VERSION).encode("ascii"),
                _grammar_fingerprint().encode("ascii"),
            )
        )
        digest = hashlib.blake2b(key_material, digest_size=20).hexdigest()
        return self._dir / "objects" / digest[:2] / f"{digest}.json"

    def load(self, content: bytes, language: str) -> Extraction | None:
        """Return cached extraction for this content, or ``None`` on any miss."""
        path = self._object_path(content, language)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            return record["definitions"], record["calls"], record["imports"]
        except (OSError, ValueError, KeyError):
            return None

    def store(
        self,
        content: bytes,
        language: str,
        definitions: list[dict[str, Any]],
        calls: list[dict[str, Any]],
        imports: list[dict[str, Any]],
    ) -> None:
        """Persist extraction. Best-effort: swallow I/O errors, never raise."""
        path = self._object_path(content, language)
        record = {
            "version": _EXTRACT_VERSION,
            "language": language,
            "definitions": definitions,
            "calls": calls,
            "imports": imports,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, json.dumps(record))
        except OSError:
            return

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(tmp, path)
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
