"""Copies referenced repository assets (images) into the output directory.

The repository is never written to: assets are copied out, and the book
references the copies via relative ``assets/…`` URLs so the generated HTML
and PDF are self-contained alongside the ``output/assets`` folder.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict
from urllib.parse import quote


class AssetStore:
    def __init__(self, repo_root: Path, output_dir: Path) -> None:
        self.repo_root = repo_root
        self.output_dir = output_dir
        self._copied: Dict[str, str] = {}

    def add(self, relpath: str) -> str:
        """Copy ``relpath`` (repo-relative) into the output and return the
        relative URL the book should use."""
        url = self._copied.get(relpath)
        if url is not None:
            return url
        source = self.repo_root / relpath
        destination = self.output_dir / "assets" / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        url = "assets/" + quote(relpath)
        self._copied[relpath] = url
        return url

    @property
    def count(self) -> int:
        return len(self._copied)
