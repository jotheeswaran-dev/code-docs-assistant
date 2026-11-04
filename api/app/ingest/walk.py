"""Find the files in a repository that are worth an index."""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.ingest.languages import detect

MAX_FILE_BYTES = 512_000
BINARY_SNIFF_BYTES = 8_000

SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "out",
        ".next",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "target",
        "coverage",
        ".terraform",
    }
)

SKIP_NAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "uv.lock",
        "Gemfile.lock",
        "poetry.lock",
        "Cargo.lock",
        "composer.lock",
    }
)

MINIFIED = re.compile(r"\.(min|bundle)\.(js|css)$")

# A key or a password must never reach the index, and never reach the model.
SECRET_HINT = re.compile(
    r"(^|/)(\.env($|\.)|.*\.(pem|key|p12|pfx|keystore)$|id_[rd]sa|.*secret.*|.*credential.*)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: str
    language: str | None
    text: str


def load(root: Path) -> tuple[list[SourceFile], Counter[str]]:
    """Return the files to index, and a count of the reasons for each file skipped."""
    skipped: Counter[str] = Counter()
    files: list[SourceFile] = []

    for relative in _candidates(root):
        reason = _skip_reason(relative)
        if reason:
            skipped[reason] += 1
            continue

        absolute = root / relative
        try:
            raw = absolute.read_bytes()
        except OSError:
            skipped["unreadable"] += 1
            continue

        if len(raw) > MAX_FILE_BYTES:
            skipped["too large"] += 1
            continue
        if b"\x00" in raw[:BINARY_SNIFF_BYTES]:
            skipped["binary"] += 1
            continue
        try:
            text = raw.decode()
        except UnicodeDecodeError:
            skipped["not utf-8"] += 1
            continue
        if not text.strip():
            skipped["empty"] += 1
            continue

        files.append(SourceFile(path=relative, language=detect(relative), text=text))

    return files, skipped


def _candidates(root: Path) -> list[str]:
    """Prefer `git ls-files`, so the ignore rules of the repository apply for free."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return sorted(p for p in result.stdout.decode(errors="replace").split("\0") if p)

    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and not SKIP_DIRS & set(p.relative_to(root).parts)
    )


def _skip_reason(relative: str) -> str | None:
    parts = relative.split("/")
    if SKIP_DIRS & set(parts[:-1]):
        return "ignored directory"
    if parts[-1] in SKIP_NAMES:
        return "lock file"
    if MINIFIED.search(parts[-1]):
        return "minified"
    if SECRET_HINT.search(relative):
        return "possible secret"
    return None
