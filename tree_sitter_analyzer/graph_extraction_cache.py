"""Global, content-addressed cache for call-graph extraction.

``CallGraph.build`` re-parses every source file on every run. Parsing dominates
the cost; the extraction it produces (``walk_tree`` definitions + call sites and
``walk_imports`` imports) is a pure function of a single file's bytes. This
module memoises that extraction in a global store keyed by file *content*, so the
same file hits the same entry regardless of which project root reached it — which
is what makes repeat runs and monorepo / nested invocations cheap.

Design notes live in ``docs/design/global-extraction-cache.md``. Key points:

- The key is ``blake2b(bytes + language + version)`` — content, not path.
- ``_EXTRACT_VERSION`` is in the key, so a change to extraction output
  invalidates every entry after an upgrade.
- The cache is best-effort: any I/O or decode failure falls back to a live parse.
  A broken cache can never fail a build or return a stale answer.
- Objects are immutable, written temp-then-atomic-rename, so concurrent
  invocations (monorepo CI) need no locking.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

#: Bump when the shape of ``walk_tree`` / ``walk_imports`` output changes, so an
#: upgraded extractor never reads entries written by an older one.
_EXTRACT_VERSION = 1

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
        digest = hashlib.blake2b(
            content + b"\0" + language.encode("utf-8") + b"\0" + str(_EXTRACT_VERSION).encode("ascii"),
            digest_size=20,
        ).hexdigest()
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
