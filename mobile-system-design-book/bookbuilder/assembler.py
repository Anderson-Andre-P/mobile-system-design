"""Assembles the final single-document HTML book.

Structure: cover → colophon → table of contents → parts (divider page +
chapters). All styling lives in ``assets/book.css`` (CSS Paged Media),
plus the Pygments stylesheet generated at build time.
"""
from __future__ import annotations

import datetime
from html import escape
from pathlib import Path
from typing import Dict, List

from .config import PAGE_SIZE, REPO_WEB_URL, TOC_DEPTH, BookMeta
from .loader import BoundPart, Chapter
from .renderer import Heading, pygments_css

_CSS_PATH = Path(__file__).parent / "assets" / "book.css"

# Physical page heights for the sizes supported in config.PAGE_SIZE; used to
# give the full-bleed cover an explicit height (percentage heights collapse
# on the paged body).
_PAGE_HEIGHTS = {"a4": "297mm", "letter": "279.4mm"}


def assemble(parts: List[BoundPart], meta: BookMeta) -> str:
    today = datetime.date.today()
    date_text = f"{today:%B} {today.day}, {today.year}"

    body = [
        _cover(meta, date_text),
        _colophon(meta, date_text),
        _toc(parts),
    ]
    for part in parts:
        body.append(_part_page(part))
        for chapter in part.chapters:
            body.append(
                f'<section class="chapter" id="{chapter.chapter_id}">\n'
                f"{chapter.html}\n</section>"
            )

    css = (
        _CSS_PATH.read_text(encoding="utf-8")
        .replace("__PAGE_SIZE__", PAGE_SIZE)
        .replace("__PAGE_HEIGHT__", _PAGE_HEIGHTS.get(PAGE_SIZE.lower(), "297mm"))
    )
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{escape(meta.language)}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{escape(meta.title)}</title>\n"
        f'<meta name="author" content="{escape(meta.author)}">\n'
        f'<meta name="description" content="{escape(meta.subtitle)}">\n'
        f'<meta name="generator" content="mobile-system-design-book builder">\n'
        f"<style>\n{css}\n\n/* Pygments */\n{pygments_css()}\n</style>\n"
        "</head>\n<body>\n"
        + "\n".join(body)
        + "\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------------- #
# Front matter
# ---------------------------------------------------------------------- #

def _cover(meta: BookMeta, date_text: str) -> str:
    return f"""
<section class="cover">
  <div class="cover-inner">
    <p class="cover-eyebrow">Mobile System Design</p>
    <div class="cover-rule"></div>
    <h1 class="cover-title">{escape(meta.title)}</h1>
    <p class="cover-subtitle">{escape(meta.subtitle)}</p>
  </div>
  <div class="cover-footer">
    <p class="cover-author">{escape(meta.author)}</p>
    <p class="cover-meta">Compiled edition &middot; {escape(date_text)}</p>
  </div>
</section>"""


def _colophon(meta: BookMeta, date_text: str) -> str:
    return f"""
<section class="colophon">
  <h2>About this edition</h2>
  <p>This book was compiled automatically from the public repository
     <a href="{REPO_WEB_URL}">{escape(REPO_WEB_URL.removeprefix("https://"))}</a>.
     The source files were read without modification; only internal links and
     image paths were remapped so the material works as a single document.</p>
  <p>{escape(meta.copyright_notice)}</p>
  <p>Generated on {escape(date_text)} for personal, offline reading.</p>
</section>"""


def _part_page(part: BoundPart) -> str:
    spec = part.spec
    chapters = "".join(
        f'<li><a href="#{chapter.chapter_id}">'
        f'<span class="part-ch-num">{chapter.number}</span>'
        f"{escape(chapter.title)}</a></li>"
        for chapter in part.chapters
    )
    return f"""
<section class="part" id="{spec.part_id}">
  <p class="part-eyebrow">Part {escape(spec.number)}</p>
  <h1 class="part-title">{escape(spec.title)}</h1>
  <div class="part-rule"></div>
  <p class="part-desc">{escape(spec.description)}</p>
  <div class="part-contents">
    <p class="part-contents-label">In this part</p>
    <ol>{chapters}</ol>
  </div>
</section>"""


# ---------------------------------------------------------------------- #
# Table of contents
# ---------------------------------------------------------------------- #

def _toc(parts: List[BoundPart]) -> str:
    rows = ['<nav class="toc">', "<h1>Contents</h1>", '<ol class="toc-root">']
    for part in parts:
        spec = part.spec
        rows.append(
            f'<li class="toc-part"><a href="#{spec.part_id}">'
            f'<span class="toc-part-label">Part {escape(spec.number)}</span> '
            f"{escape(spec.title)}</a><ol>"
        )
        for chapter in part.chapters:
            rows.append(
                f'<li class="toc-chapter">'
                f'<a href="#{chapter.chapter_id}">'
                f'<span class="toc-num">{chapter.number}</span> '
                f"{escape(chapter.title)}</a>"
                f"{_sections_html(chapter)}</li>"
            )
        rows.append("</ol></li>")
    rows.append("</ol></nav>")
    return "\n".join(rows)


def _sections_html(chapter: Chapter) -> str:
    headings = [h for h in chapter.headings if 2 <= h.level <= TOC_DEPTH]
    tree = _nest(headings)
    return _render_nodes(tree, chapter.chapter_id)


def _nest(headings: List[Heading]) -> List[Dict]:
    root: List[Dict] = []
    stack = [(1, root)]
    for heading in headings:
        node: Dict = {"heading": heading, "children": []}
        while len(stack) > 1 and stack[-1][0] >= heading.level:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((heading.level, node["children"]))
    return root


def _render_nodes(nodes: List[Dict], chapter_id: str) -> str:
    if not nodes:
        return ""
    items = []
    for node in nodes:
        heading = node["heading"]
        items.append(
            f'<li class="toc-l{heading.level}">'
            f'<a href="#{chapter_id}--{heading.hid}">{escape(heading.text)}</a>'
            f'{_render_nodes(node["children"], chapter_id)}</li>'
        )
    return "<ol>" + "".join(items) + "</ol>"
