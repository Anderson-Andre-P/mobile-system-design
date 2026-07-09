"""Presentation-only HTML enhancements applied after rendering.

Nothing here rewrites, reorders, or summarizes the authored text. The
transforms only add visual structure around content that is already there:

* ``_NOTE: …_`` / ``**Note:** …`` paragraphs (a recurring pattern in the
  source material) become styled admonition asides — the original words,
  emphasis and links inside are preserved verbatim.
* GitHub-style alerts (``> [!NOTE]``) get the matching admonition class,
  should the source ever use them.
* Standalone images become figures with a numbered caption derived from
  the image's own alt text.
* A small "Chapter N" eyebrow is added above each chapter title, matching
  the numbering used in the table of contents.
"""
from __future__ import annotations

import re

_ADMONITION_KIND = {
    "note": "note",
    "info": "note",
    "tip": "tip",
    "success": "tip",
    "warning": "warning",
    "danger": "warning",
    "important": "important",
    "caution": "caution",
}

_EM_NOTE_RE = re.compile(r"<p><em>NOTE:(?P<body>.*?)</em>\s*</p>", re.DOTALL)
_STRONG_RE = re.compile(
    r"<p>(?P<label><strong>(?P<kind>Note|Tip|Warning|Important|Caution|Info)"
    r"[:!]?\s*</strong>)(?P<body>.*?)</p>",
    re.DOTALL,
)
_GH_ALERT_RE = re.compile(
    r"<blockquote>\s*<p>\[!(?P<kind>NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*"
    r"(?:<br\s*/?>)?\n?"
)
_FIGURE_RE = re.compile(r"<p>(?P<img><img\b[^>]*>)</p>")
_ALT_RE = re.compile(r'\balt="(?P<alt>[^"]*)"')


def polish_chapter(html: str, chapter_number: int) -> str:
    html = _admonitions(html)
    html = _figures(html, chapter_number)
    eyebrow = f'<p class="chapter-eyebrow">Chapter {chapter_number}</p>\n'
    return eyebrow + html


def _admonitions(html: str) -> str:
    def em_note(match: re.Match) -> str:
        return (
            '<aside class="admonition note">'
            f'<p><em>NOTE:{match.group("body")}</em></p></aside>'
        )

    def strong_note(match: re.Match) -> str:
        kind = _ADMONITION_KIND.get(match.group("kind").lower(), "note")
        return (
            f'<aside class="admonition {kind}">'
            f'<p>{match.group("label")}{match.group("body")}</p></aside>'
        )

    def gh_alert(match: re.Match) -> str:
        kind = _ADMONITION_KIND.get(match.group("kind").lower(), "note")
        return f'<blockquote class="admonition {kind}"><p>'

    html = _EM_NOTE_RE.sub(em_note, html)
    html = _STRONG_RE.sub(strong_note, html)
    html = _GH_ALERT_RE.sub(gh_alert, html)
    return html


def _figures(html: str, chapter_number: int) -> str:
    counter = 0

    def replace(match: re.Match) -> str:
        nonlocal counter
        counter += 1
        image = match.group("img")
        alt_match = _ALT_RE.search(image)
        alt = alt_match.group("alt") if alt_match else ""
        label = f'<span class="figure-label">Figure {chapter_number}.{counter}</span>'
        caption = f"<figcaption>{label}{alt}</figcaption>"
        return f"<figure>{image}{caption}</figure>"

    return _FIGURE_RE.sub(replace, html)
