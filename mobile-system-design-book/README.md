# Mobile System Design — Book Builder

Compiles the documentation of the [`mobile-system-design`](https://github.com/weeeBox/mobile-system-design)
repository into a single, professionally formatted book (PDF, with an
intermediate self-contained HTML build).

**The repository content is strictly read-only for this tool.** It reads the
Markdown sources and copies the referenced images into its own `output/`
directory; it never edits, renames, rewrites, or reorganizes any repository
content. All generated files stay inside this project folder (the tool
refuses any output path that would land among the repository's own files).

## Requirements

- Python **3.9 or newer**
- This project lives inside the documentation repository; the repo root is
  auto-detected as the parent directory (override with `--repo` if you move
  the project elsewhere)
- For the PDF step, WeasyPrint needs the native **Pango** library:
  - **macOS:** `brew install pango`
  - **Debian/Ubuntu:** `sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
  - **Windows:** install the GTK3 runtime (see the
    [WeasyPrint installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html))

## Setup (virtual environment)

From this project's directory:

```bash
# 1. Create the virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (cmd/PowerShell)

# 3. Install the dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Build HTML + PDF (repo auto-detected as the parent directory)
python build_book.py

# Equivalent module form
python -m bookbuilder

# Explicit paths
python build_book.py --repo /path/to/the/repo --output ./output

# HTML only (works even without Pango/WeasyPrint installed)
python build_book.py --html-only
```

Outputs:

| File | Description |
| --- | --- |
| `output/book.pdf` | The final book — cover, clickable TOC with page numbers, running headers, page numbers, chapter page breaks, PDF outline bookmarks |
| `output/book.html` | The intermediate single-document build (also fully readable in a browser) |
| `output/assets/` | Copies of the repository images referenced by the book |

Note: the book contains one remote image (a Discord badge in the
introduction). If you build while offline, WeasyPrint logs a warning and
skips it; everything else is local.

## Dependencies (what and why)

| Package | Purpose |
| --- | --- |
| `markdown-it-py` | Markdown → HTML. CommonMark engine with the `gfm-like` preset, matching GitHub's rendering rules the repo was written for — GFM tables, raw HTML (`<ul><li>` inside table cells), lists that interrupt paragraphs, autolinked URLs |
| `mdit-py-plugins` | GitHub-style heading anchors (keeps the repo's `file.md#fragment` cross-links working), footnotes, task lists |
| `linkify-it-py` | Required by the `gfm-like` preset for bare-URL autolinking |
| `Pygments` | Syntax highlighting for fenced code blocks (`kotlin`, `swift`, `json`, `http`) — code content itself is never altered |
| `weasyprint` | HTML → PDF with real CSS Paged Media: margins, running headers/footers, page numbers, `target-counter()` TOC page numbers, dot leaders, PDF bookmarks |

## Project structure

```
mobile-system-design-book/
├── build_book.py            # entry point (same as `python -m bookbuilder`)
├── requirements.txt
├── README.md
├── output/                  # generated (created on first build)
└── bookbuilder/
    ├── config.py            # book metadata, curated chapter order, page size, TOC depth
    ├── loader.py            # read-only loading of the repo's Markdown files
    ├── renderer.py          # Markdown → HTML (GitHub-compatible), heading collection
    ├── links.py             # internal link/anchor rewriting, image path resolution
    ├── assets.py            # copies referenced images into output/assets/
    ├── assembler.py         # cover, colophon, TOC, part pages, final HTML document
    ├── pdfgen.py            # WeasyPrint PDF rendering
    ├── cli.py               # argument parsing and build orchestration
    └── assets/book.css      # the book's print stylesheet (CSS Paged Media)
```

## Configuration

Everything configurable lives in `bookbuilder/config.py`:

- `BookMeta` — title, subtitle, author, copyright line
- `PARTS` — the chapter plan (which files, in which order, grouped into parts)
- `PAGE_SIZE` — `"A4"` (default) or `"letter"`
- `TOC_DEPTH` — how deep the table of contents goes (default 3 = chapters,
  sections, subsections)

Typography and layout are in `bookbuilder/assets/book.css`.

## Why this chapter order?

The order follows the reading path the original author designed, not the
alphabet:

1. **Part I — The Interview Framework**: `README.md`, the narrative core of
   the guide.
2. **Part II — Technical Deep Dives**: the ten `topics/` files, in the order
   `README.md` first references each of them, preserving the pedagogical
   sequence (image loading → navigation → in-app API design → REST API →
   pagination → offline-first → caching → QoS → resumable uploads →
   prefetching).
3. **Part III — Interview Exercises**: the exercises index first, then the
   four worked exercises in the order that index lists them.
4. **Part IV — Preparation Toolkit**: interview template, common mistakes,
   curated blog posts — the material `README.md` recommends at its end.
5. **Part V — About This Guide**: contributing guidelines and the license.

A coverage check warns at build time if the repository contains Markdown
files that are not part of the plan, so nothing can go missing silently.

## Content fidelity

- Chapter text, code blocks (indentation, language tags), tables, and images
  are reproduced exactly as authored.
- The only transformation applied is navigational: internal `*.md` links are
  remapped to in-book anchors, image paths are resolved to the copied assets,
  and heading ids are namespaced per chapter to avoid collisions between
  files that repeat the same heading. Two anchors that are already stale in
  the source (`README.md#resumable-uploads`, `README.md#quality-of-service`)
  degrade gracefully to the start of the target chapter, with a build
  warning. Links to repository paths outside the book fall back to the
  project's GitHub page. External links are untouched and clickable.

## License note

The book content is © Alex Lementuev (see `LICENSE.md` in the source
repository, reproduced as the book's final chapter). The generated book is
intended for personal, offline reading.
