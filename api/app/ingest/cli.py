"""Read a repository and write its chunks to a JSONL file."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from app.ingest.chunker import chunk_file
from app.ingest.languages import PARSED
from app.ingest.models import Chunk
from app.ingest.walk import load


def ingest(root: Path) -> tuple[list[Chunk], Counter[str], Counter[str]]:
    files, skipped = load(root)
    chunks: list[Chunk] = []
    for source in files:
        chunks.extend(chunk_file(source.path, source.text, source.language))
    languages = Counter(source.language or "no parser" for source in files)
    return chunks, languages, skipped


def _resolve(source: str, stack: list[tempfile.TemporaryDirectory[str]]) -> Path:
    if not source.startswith(("http://", "https://", "git@")):
        root = Path(source).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"error: {root} is not a directory")
        return root
    holder = tempfile.TemporaryDirectory()
    stack.append(holder)
    subprocess.run(["git", "clone", "--depth", "1", "--quiet", source, holder.name], check=True)
    return Path(holder.name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cut a repository into chunks.")
    parser.add_argument("source", help="A local path or a Git URL")
    parser.add_argument("--out", default="data/chunks.jsonl")
    args = parser.parse_args(argv)

    stack: list[tempfile.TemporaryDirectory[str]] = []
    started = time.perf_counter()
    root = _resolve(args.source, stack)
    chunks, languages, skipped = ingest(root)
    elapsed = time.perf_counter() - started

    if not chunks:
        for holder in stack:
            holder.cleanup()
        raise SystemExit(f"error: {root} gave no chunks. Is it a source repository?")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict()) + "\n")

    parsed = sum(count for name, count in languages.items() if name in PARSED)
    total_files = sum(languages.values())
    kinds = Counter(chunk.kind for chunk in chunks)
    from_syntax = sum(count for kind, count in kinds.items() if kind != "file_part")

    print(f"source      {root}")
    print(f"files       {total_files} indexed, {sum(skipped.values())} skipped")
    print(f"parsed      {parsed} of {total_files} files have a parser")
    windowed = len(chunks) - from_syntax
    print(f"chunks      {len(chunks)} total, {from_syntax} from syntax, {windowed} from a window")
    print(f"time        {elapsed:.2f}s")
    print(f"written     {out}")
    print()
    _table("language", languages)
    _table("chunk kind", kinds)
    if skipped:
        _table("skipped", skipped)

    for holder in stack:
        holder.cleanup()
    return 0


def _table(title: str, counts: Counter[str]) -> None:
    print(f"  {title}")
    for name, count in counts.most_common():
        print(f"    {name:<22} {count:>6}")
    print()


if __name__ == "__main__":
    sys.exit(main())
