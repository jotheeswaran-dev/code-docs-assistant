from pathlib import Path

import pytest

from app.ingest.chunker import MAX_CHARS, TRIVIAL, chunk_file
from app.ingest.languages import detect

FIXTURES = Path(__file__).parent / "fixtures" / "repo"
ALL_FIXTURES = ["sample.py", "sample.ts", "sample.rb", "broken.py", "notes.md"]


def chunks_for(name: str):
    text = (FIXTURES / name).read_text()
    return chunk_file(name, text, detect(name)), text


def test_python_cuts_on_symbol_boundaries():
    chunks, _ = chunks_for("sample.py")
    found = {(c.kind, c.symbol, c.start_line, c.end_line) for c in chunks}
    assert ("class", "Session", 9, 13) in found
    assert ("method", "Session.send", 14, 16) in found
    assert ("method", "Session.close", 18, 19) in found
    assert ("function", "build", 22, 23) in found


def test_a_class_header_stops_before_the_first_method():
    chunks, _ = chunks_for("sample.py")
    header = next(c for c in chunks if c.kind == "class" and c.symbol == "Session")
    assert "retries = 3" in header.text
    assert "def send" not in header.text


def test_a_method_records_its_class():
    chunks, _ = chunks_for("sample.py")
    send = next(c for c in chunks if c.symbol == "Session.send")
    assert send.parent == "Session"
    assert send.text.startswith("    def send")


def test_typescript_keeps_the_export_keyword():
    chunks, _ = chunks_for("sample.ts")
    assert next(c for c in chunks if c.symbol == "User").text.startswith("export interface User")
    assert next(c for c in chunks if c.symbol == "Service").text.startswith("export default class")


def test_typescript_names_an_arrow_function():
    chunks, _ = chunks_for("sample.ts")
    greet = next(c for c in chunks if c.symbol == "greet")
    assert greet.kind == "function"
    assert (greet.start_line, greet.end_line) == (9, 11)


def test_ruby_qualifies_a_nested_symbol():
    chunks, _ = chunks_for("sample.rb")
    symbols = {c.symbol for c in chunks}
    assert {"Store", "Store.Entry", "Store.Entry.initialize", "Store.Entry.build"} <= symbols


def test_imports_travel_with_every_chunk():
    chunks, _ = chunks_for("sample.py")
    assert all(c.imports == ("import os", "from pathlib import Path") for c in chunks)


@pytest.mark.parametrize("name", ALL_FIXTURES)
def test_chunks_never_overlap(name):
    chunks, _ = chunks_for(name)
    ordered = sorted(chunks, key=lambda c: c.start_line)
    for earlier, later in zip(ordered, ordered[1:], strict=False):
        assert earlier.end_line < later.start_line, f"{earlier.label} overlaps {later.label}"


@pytest.mark.parametrize("name", ALL_FIXTURES)
def test_every_line_that_carries_meaning_lands_in_a_chunk(name):
    chunks, text = chunks_for(name)
    covered = {n for c in chunks for n in range(c.start_line, c.end_line + 1)}
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip() not in TRIVIAL:
            assert number in covered, f"{name}:{number} belongs to no chunk"


@pytest.mark.parametrize("name", ALL_FIXTURES)
def test_every_chunk_has_its_own_id(name):
    chunks, _ = chunks_for(name)
    assert len({c.id for c in chunks}) == len(chunks)


def test_a_file_without_a_parser_uses_a_line_window():
    chunks, _ = chunks_for("notes.md")
    assert {c.kind for c in chunks} == {"file_part"}
    assert all(c.symbol is None for c in chunks)


def test_a_broken_file_still_produces_chunks():
    chunks, _ = chunks_for("broken.py")
    assert {c.symbol for c in chunks} == {"ok", "broken"}


def test_a_large_symbol_splits_into_parts():
    body = "\n".join(f"    value_{n} = {n}" for n in range(MAX_CHARS // 10))
    chunks = chunk_file("big.py", f"def huge():\n{body}\n", "python")
    parts = [c for c in chunks if c.symbol == "huge"]
    assert len(parts) > 1
    assert [c.part for c in parts] == list(range(1, len(parts) + 1))
    assert {c.parts for c in parts} == {len(parts)}
    assert f"(part 1 of {len(parts)})" in parts[0].label


def test_the_label_names_the_file_and_the_symbol():
    chunks, _ = chunks_for("sample.py")
    send = next(c for c in chunks if c.symbol == "Session.send")
    assert send.label == "sample.py:14-16 · Session.send"
