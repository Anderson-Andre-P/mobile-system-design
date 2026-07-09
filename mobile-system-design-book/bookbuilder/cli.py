"""Command-line interface and build orchestration.

The build is strictly read-only with respect to the repository: sources are
read, assets are copied out, and all generated files land in the output
directory (which is refused if it points inside the repository).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .assembler import assemble
from .assets import AssetStore
from .config import BookMeta
from .links import LinkRewriter
from .loader import find_unplanned_markdown, load_book
from .polish import polish_chapter
from .renderer import ChapterRenderer

# The project lives inside the documentation repository, so the repo root
# is simply the parent directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = PROJECT_ROOT.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "output"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bookbuilder",
        description=(
            "Compile the mobile-system-design repository documentation into "
            "a professionally formatted book (HTML + PDF). The repository is "
            "only ever read, never modified."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO,
        help=f"Path to the documentation repository (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Directory for generated files (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Generate only output/book.html, skipping the PDF step.",
    )
    args = parser.parse_args(argv)

    repo = args.repo.expanduser().resolve()
    output = args.output.expanduser().resolve()

    if not (repo / "README.md").is_file():
        parser.error(f"'{repo}' does not look like the documentation repo "
                     "(README.md not found). Use --repo to point at it.")
    # Generated files may only land inside this project's own directory or
    # entirely outside the repository — never among the repo's content.
    if _is_inside(output, repo) and not _is_inside(output, PROJECT_ROOT):
        parser.error("Refusing to write output among the repository's "
                     "content; choose an --output directory inside "
                     f"{PROJECT_ROOT} or outside the repository.")

    warnings: List[str] = []

    print(f"Reading repository: {repo}")
    parts = load_book(repo)
    chapters = [chapter for part in parts for chapter in part.chapters]

    print(f"Rendering {len(chapters)} chapters ...")
    renderer = ChapterRenderer()
    for chapter in chapters:
        chapter.html, chapter.headings = renderer.render(chapter.source)
        for heading in chapter.headings:
            if heading.level == 1 and heading.text:
                chapter.title = heading.text
                break

    output.mkdir(parents=True, exist_ok=True)
    assets = AssetStore(repo_root=repo, output_dir=output)
    rewriter = LinkRewriter(repo, parts, assets, warnings)
    for chapter in chapters:
        chapter.html = rewriter.rewrite_chapter(chapter)
        chapter.html = polish_chapter(chapter.html, chapter.number)
    print(f"Resolved links and copied {assets.count} image(s) to {output / 'assets'}")

    unplanned = find_unplanned_markdown(repo, exclude=PROJECT_ROOT)
    for relpath in unplanned:
        warnings.append(
            f"'{relpath}' exists in the repository but is not part of the "
            f"book plan (bookbuilder/config.py)."
        )

    html_document = assemble(parts, BookMeta())
    html_path = output / "book.html"
    html_path.write_text(html_document, encoding="utf-8")
    print(f"Wrote {html_path}")

    if not args.html_only:
        from .pdfgen import build_pdf

        pdf_path = output / "book.pdf"
        print("Rendering PDF (this can take a minute) ...")
        try:
            build_pdf(html_path, pdf_path)
        except RuntimeError as error:
            print(f"ERROR: {error}", file=sys.stderr)
            print("The HTML build succeeded; re-run without --html-only "
                  "after fixing the WeasyPrint setup.", file=sys.stderr)
            return 1
        print(f"Wrote {pdf_path}")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")

    print("\nDone. The repository was not modified.")
    return 0


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
