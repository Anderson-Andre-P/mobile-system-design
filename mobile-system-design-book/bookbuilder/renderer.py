"""Markdown to HTML rendering with GitHub-compatible behaviour.

Uses markdown-it-py with the "gfm-like" preset because the repository was
authored for GitHub rendering. This matters for two constructs the strict
python-markdown package handles differently:

* lists that interrupt a paragraph without a preceding blank line;
* raw HTML (``<ul><li>…``) embedded inside GFM table cells.

Heading anchors follow GitHub's slug algorithm so the repository's existing
``file.md#fragment`` cross-links keep working inside the book.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import List, Optional, Tuple

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight as pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

PYGMENTS_STYLE = "friendly"
_CODE_FORMATTER = HtmlFormatter(nowrap=True)


@dataclass(frozen=True)
class Heading:
    level: int  # 1-6
    hid: str  # slug id, without the per-chapter prefix
    text: str  # plain heading text


def github_slugify(text: str) -> str:
    """GitHub's heading-anchor algorithm (close approximation)."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def pygments_css() -> str:
    return HtmlFormatter(style=PYGMENTS_STYLE).get_style_defs(".highlight")


def _highlight_fence(code: str, lang: str, attrs: str) -> str:
    """Fence highlighter for markdown-it. Returning "" keeps the default
    escaped output, so code content is never altered either way."""
    if not lang:
        return ""
    try:
        lexer = get_lexer_by_name(lang.strip())
    except ClassNotFound:
        return ""
    body = pygments_highlight(code, lexer, _CODE_FORMATTER)
    name = escape(lang.strip())
    return (
        f'<pre class="highlight language-{name}" data-lang="{name}">'
        f"<code>{body}</code></pre>"
    )


class ChapterRenderer:
    def __init__(self) -> None:
        self._md = (
            MarkdownIt("gfm-like", {"highlight": _highlight_fence})
            .use(anchors_plugin, min_level=1, max_level=6, slug_func=github_slugify)
            .use(footnote_plugin)
            .use(tasklists_plugin)
        )

    def render(self, source: str) -> Tuple[str, List[Heading]]:
        """Render one chapter. Returns (html, headings found in order)."""
        html = self._md.render(source)
        headings = self._collect_headings(source)
        return html, headings

    def _collect_headings(self, source: str) -> List[Heading]:
        tokens = self._md.parse(source)
        headings: List[Heading] = []
        for index, token in enumerate(tokens):
            if token.type != "heading_open":
                continue
            hid = str(token.attrs.get("id", ""))
            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            headings.append(
                Heading(
                    level=int(token.tag[1]),
                    hid=hid,
                    text=_inline_text(inline),
                )
            )
        return headings


def _inline_text(token: Optional[object]) -> str:
    if token is None or getattr(token, "children", None) is None:
        return getattr(token, "content", "") or ""
    parts = []
    for child in token.children:  # type: ignore[attr-defined]
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
    return "".join(parts).strip()
