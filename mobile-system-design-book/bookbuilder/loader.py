"""Read-only loading of the repository's Markdown sources.

This module only ever opens repository files for reading. Nothing in the
project writes inside the repository.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .config import PARTS, PartSpec
from .renderer import Heading

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Chapter:
    relpath: str  # repository-relative POSIX path, e.g. "topics/caching-deep-dive.md"
    number: int  # 1-based chapter number across the whole book
    source: str  # raw, unmodified Markdown text
    title: str = ""
    html: str = ""
    headings: List[Heading] = field(default_factory=list)

    @property
    def chapter_id(self) -> str:
        stem = re.sub(r"\.md$", "", self.relpath, flags=re.IGNORECASE)
        return "ch-" + re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


@dataclass
class BoundPart:
    spec: PartSpec
    chapters: List[Chapter] = field(default_factory=list)


def load_book(repo_root: Path) -> List[BoundPart]:
    """Load every planned chapter from the repository, in book order."""
    parts: List[BoundPart] = []
    number = 0
    missing: List[str] = []
    for spec in PARTS:
        bound = BoundPart(spec=spec)
        for relpath in spec.files:
            path = repo_root / relpath
            if not path.is_file():
                missing.append(relpath)
                continue
            number += 1
            source = path.read_text(encoding="utf-8")
            chapter = Chapter(relpath=relpath, number=number, source=source)
            chapter.title = _fallback_title(chapter)
            bound.chapters.append(chapter)
        parts.append(bound)
    if missing:
        raise FileNotFoundError(
            "Planned chapter files are missing from the repository: "
            + ", ".join(missing)
        )
    return parts


def _fallback_title(chapter: Chapter) -> str:
    """Title from the first Markdown H1, else a cleaned-up file name."""
    match = _H1_RE.search(chapter.source)
    if match:
        # Strip inline markup that may appear in a heading.
        return re.sub(r"[*_`]", "", match.group(1)).strip()
    stem = Path(chapter.relpath).stem
    return stem.replace("-", " ").replace("_", " ").title()


def find_unplanned_markdown(repo_root: Path, exclude: Optional[Path] = None) -> List[str]:
    """Return Markdown files present in the repo but absent from the plan.

    ``exclude`` skips a directory tree (used for this project's own files,
    since the builder lives inside the repository).
    """
    planned = {relpath.casefold() for part in PARTS for relpath in part.files}
    found: List[str] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if exclude is not None and exclude in path.resolve().parents:
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith(".git/"):
            continue
        if rel.casefold() not in planned:
            found.append(rel)
    return found
