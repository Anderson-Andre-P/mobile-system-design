"""HTML-to-PDF conversion via WeasyPrint.

WeasyPrint is imported lazily so that ``--html-only`` builds work even on a
machine where WeasyPrint's native dependencies (Pango) are not installed.

macOS note: Homebrew installs Pango/GObject under ``/opt/homebrew/lib``
(Apple Silicon) or ``/usr/local/lib`` (Intel), which the dynamic loader does
not search by default — and ``DYLD_FALLBACK_LIBRARY_PATH`` is read only at
process start, so it cannot be set from within a running interpreter. When
the import fails for that reason, the build re-executes itself once with the
variable set.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REEXEC_MARKER = "BOOKBUILDER_DYLD_RETRY"
_HOMEBREW_LIB_DIRS = ("/opt/homebrew/lib", "/usr/local/lib")


def build_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as error:  # OSError: missing Pango/GObject
        _maybe_reexec_with_homebrew_libs()  # does not return if it can help
        raise RuntimeError(
            "WeasyPrint is not available. Install the requirements inside "
            "your virtual environment and make sure the system Pango "
            "library is installed (macOS: `brew install pango`, then run "
            "with DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib if needed). "
            f"Original error: {error}"
        ) from error

    document = HTML(filename=str(html_path), base_url=str(html_path.parent))
    document.write_pdf(str(pdf_path))


def _maybe_reexec_with_homebrew_libs() -> None:
    """Relaunch the current command once with Homebrew's library directories
    on the dynamic-loader fallback path (macOS only)."""
    if sys.platform != "darwin" or os.environ.get(_REEXEC_MARKER):
        return
    lib_dirs = [
        directory
        for directory in _HOMEBREW_LIB_DIRS
        if any(Path(directory).glob("libgobject-2.0*.dylib"))
    ]
    if not lib_dirs:
        return

    environment = dict(os.environ)
    existing = environment.get("DYLD_FALLBACK_LIBRARY_PATH")
    if existing:
        lib_dirs.append(existing)
    environment["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(lib_dirs)
    environment[_REEXEC_MARKER] = "1"

    print(
        "WeasyPrint could not find the Homebrew libraries; retrying with "
        f"DYLD_FALLBACK_LIBRARY_PATH={environment['DYLD_FALLBACK_LIBRARY_PATH']}"
    )
    sys.stdout.flush()
    os.execve(sys.executable, [sys.executable] + sys.argv, environment)
