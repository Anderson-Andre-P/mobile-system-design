"""Rewrites links and image paths for the single-document book.

Original Markdown files are never touched; rewriting happens only on the
rendered HTML held in memory. Rules:

* External URLs (``https://…``, ``mailto:``, protocol-relative) — unchanged.
* ``#fragment`` — namespaced to the current chapter (``#<chapter>--<frag>``).
* Links to Markdown files included in the book — converted to in-book
  anchors. Fragments that do not match any heading in the target chapter
  (two such stale anchors exist in the repository) fall back to the start
  of the target chapter.
* Image paths (root-absolute ``/images/…`` or relative) — resolved against
  the repository, copied to ``output/assets/`` and re-pointed there.
* Links to repository paths not included in the book — pointed at the
  project's GitHub page so they stay functional.

Heading ``id`` attributes are namespaced per chapter (``<chapter>--<slug>``)
because several files repeat identical headings (e.g. "Providing the
Signal") which would otherwise collide in the merged document.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import quote, unquote

from .config import REPO_DEFAULT_BRANCH, REPO_WEB_URL
from .assets import AssetStore
from .loader import BoundPart, Chapter

_ATTR_RE = re.compile(r'\b(href|src)="([^"]*)"')
_HEADING_ID_RE = re.compile(r'(<h[1-6][^>]*\bid=")([^"]*)(")')
_EXTERNAL_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*:|//)")


class LinkRewriter:
    def __init__(
        self,
        repo_root: Path,
        parts: List[BoundPart],
        assets: AssetStore,
        warnings: List[str],
    ) -> None:
        self.repo_root = repo_root
        self.assets = assets
        self.warnings = warnings
        self.chapter_by_path: Dict[str, str] = {}
        self.heading_ids: Dict[str, Set[str]] = {}
        for part in parts:
            for chapter in part.chapters:
                cid = chapter.chapter_id
                self.chapter_by_path[chapter.relpath.casefold()] = cid
                # Allow directory links to resolve to the directory's README,
                # e.g. "/exercises" -> exercises/README.md.
                name = posixpath.basename(chapter.relpath).casefold()
                if name == "readme.md":
                    directory = posixpath.dirname(chapter.relpath)
                    self.chapter_by_path.setdefault(directory.casefold() or ".", cid)
                self.heading_ids[cid] = {h.hid for h in chapter.headings}

    def rewrite_chapter(self, chapter: Chapter) -> str:
        def replace(match: re.Match) -> str:
            attr, url = match.group(1), match.group(2)
            return f'{attr}="{self._map_url(chapter, attr, url)}"'

        html = _ATTR_RE.sub(replace, chapter.html)
        prefix = chapter.chapter_id + "--"
        html = _HEADING_ID_RE.sub(
            lambda m: m.group(1) + prefix + m.group(2) + m.group(3), html
        )
        return html

    # ------------------------------------------------------------------ #

    def _map_url(self, chapter: Chapter, attr: str, url: str) -> str:
        if not url or _EXTERNAL_RE.match(url):
            return url

        if url.startswith("#"):
            return self._anchor(chapter, chapter.chapter_id, unquote(url[1:]))

        path, _, fragment = url.partition("#")
        relpath = self._resolve(chapter, unquote(path))

        target_chapter = self.chapter_by_path.get(relpath.casefold())
        if target_chapter is not None and attr == "href":
            return self._anchor(chapter, target_chapter, unquote(fragment))

        if (self.repo_root / relpath).is_file():
            return self.assets.add(relpath)

        self.warnings.append(
            f"{chapter.relpath}: '{url}' does not resolve inside the "
            f"repository; linked to the project's GitHub page instead."
        )
        suffix = f"#{fragment}" if fragment else ""
        return f"{REPO_WEB_URL}/blob/{REPO_DEFAULT_BRANCH}/{quote(relpath)}{suffix}"

    def _resolve(self, chapter: Chapter, path: str) -> str:
        """Turn a link target into a repository-relative POSIX path."""
        if path.startswith("/"):
            resolved = posixpath.normpath(path.lstrip("/"))
        else:
            base = posixpath.dirname(chapter.relpath)
            resolved = posixpath.normpath(posixpath.join(base, path))
        return resolved or "."

    def _anchor(self, chapter: Chapter, target_chapter: str, fragment: str) -> str:
        if fragment:
            if fragment in self.heading_ids.get(target_chapter, set()):
                return f"#{target_chapter}--{fragment}"
            self.warnings.append(
                f"{chapter.relpath}: anchor '#{fragment}' has no matching "
                f"heading (stale in the source too); linked to the chapter "
                f"start instead."
            )
        return f"#{target_chapter}"
