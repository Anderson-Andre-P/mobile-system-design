"""Book definition: metadata, curated chapter plan, and output settings.

The chapter order is deliberately NOT alphabetical. It follows the reading
path designed by the original author:

* Part I is the main guide (README.md), which is the narrative core.
* Part II contains the ``topics/`` deep dives in the order README.md first
  references each of them, preserving the author's pedagogical sequence.
* Part III contains the worked exercises in the order listed by the
  exercises index (exercises/README.md), which also keeps the one
  exercise-to-exercise cross reference pointing backwards.
* Part IV groups the preparation material README.md points to at its end.
* Part V is back matter (contributing guidelines and license).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

# Where the original content lives on the web. Used for the colophon and as
# a graceful fallback for links to repository paths not included in the book.
REPO_WEB_URL = "https://github.com/weeeBox/mobile-system-design"
REPO_DEFAULT_BRANCH = "master"

# Page geometry for the PDF ("A4" or "letter").
PAGE_SIZE = "A4"

# Table of contents depth: 1 = chapters, 2 = sections (h2), 3 = subsections (h3).
TOC_DEPTH = 3


@dataclass(frozen=True)
class BookMeta:
    title: str = "A Simple Framework for Mobile System Design Interviews"
    subtitle: str = "A complete guide for iOS & Android engineers"
    author: str = "Alex Lementuev and contributors"
    copyright_notice: str = "Content © 2021–present Alex Lementuev. All rights reserved."
    language: str = "en"


@dataclass(frozen=True)
class PartSpec:
    number: str  # Roman numeral, e.g. "II"
    title: str
    description: str
    files: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def part_id(self) -> str:
        return f"part-{self.number.lower()}"


PARTS: Tuple[PartSpec, ...] = (
    PartSpec(
        number="I",
        title="The Interview Framework",
        description=(
            "The complete interview framework — from requirement gathering to "
            "the final Q&A — illustrated end-to-end with the “Design "
            "Twitter Feed” example."
        ),
        files=("README.md",),
    ),
    PartSpec(
        number="II",
        title="Technical Deep Dives",
        description=(
            "Focused chapters that expand the framework's core technical "
            "topics, presented in the order the framework references them."
        ),
        files=(
            "topics/image-loading-deep-dive.md",
            "topics/mobile-navigation-deep-dive.md",
            "topics/in-app-api-design-deep-dive.md",
            "topics/restful-api-design-deep-dive.md",
            "topics/mobile-pagination-deep-dive.md",
            "topics/offline-first-architecture-deep-dive.md",
            "topics/caching-deep-dive.md",
            "topics/quality-of-service.md",
            "topics/resumable-uploads.md",
            "topics/prefetching.md",
        ),
    ),
    PartSpec(
        number="III",
        title="Interview Exercises",
        description=(
            "Worked mock-interview exercises that apply the framework to "
            "typical library- and app-design questions."
        ),
        files=(
            "exercises/README.md",
            "exercises/file-downloader-library.md",
            "exercises/caching-library.md",
            "exercises/image-library.md",
            "exercises/chat-app.md",
        ),
    ),
    PartSpec(
        number="IV",
        title="Preparation Toolkit",
        description=(
            "Practical preparation material: an interview note-taking "
            "template, common mistakes to avoid, and curated further reading."
        ),
        files=(
            "TEMPLATE.md",
            "common-interview-mistakes.md",
            "BLOGPOSTS.MD",
        ),
    ),
    PartSpec(
        number="V",
        title="About This Guide",
        description=(
            "Contribution guidelines and the license governing the original "
            "material."
        ),
        files=(
            "CONTRIBUTING.md",
            "LICENSE.md",
        ),
    ),
)
