"""Cut a source file into chunks on syntax limits, with a line window as the fallback."""

from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from app.ingest.languages import (
    CONTAINERS,
    DEFINITIONS,
    IMPORT_PATTERNS,
    PARSED,
    VALUE_FUNCTIONS,
    WRAPPERS,
)
from app.ingest.models import Chunk

MAX_CHARS = 6000
WINDOW_LINES = 60

# A run of these lines alone carries no meaning, so it does not become a chunk.
TRIVIAL = frozenset({"", "end", "}", ")", "]", "};", "});", ")}", "end;", "')", '")'})

KINDS = {
    "class_definition": "class",
    "class_declaration": "class",
    "class": "class",
    "module": "module",
    "function_definition": "function",
    "function_declaration": "function",
    "generator_function_declaration": "function",
    "method": "method",
    "singleton_method": "method",
    "method_definition": "method",
    "interface_declaration": "interface",
    "type_alias_declaration": "type",
    "enum_declaration": "enum",
}


@dataclass(slots=True)
class _Span:
    start: int
    end: int
    kind: str
    symbol: str | None = None
    parent: str | None = None


def chunk_file(path: str, text: str, language: str | None) -> list[Chunk]:
    lines = text.splitlines()
    if not lines:
        return []

    imports = _imports(lines, language)
    spans = _parse_spans(text, language) if language in PARSED else []
    spans.extend(_gap_spans(spans, lines))
    spans.sort(key=lambda s: (s.start, s.end))

    return [c for span in spans for c in _emit(path, language or "text", span, lines, imports)]


def _parse_spans(text: str, language: str) -> list[_Span]:
    try:
        tree = get_parser(language).parse(text.encode())
    except Exception:
        return []  # A parser fault must not lose the file. The gap fill covers it.
    spans: list[_Span] = []
    _visit(tree.root_node, language, None, spans)
    return spans


def _visit(node: Node, language: str, parent: str | None, spans: list[_Span]) -> None:
    containers = CONTAINERS.get(language, frozenset())
    definitions = DEFINITIONS[language]

    for child in node.named_children:
        if child.type in containers:
            symbol = _qualify(parent, _name(child))
            inner = _inner_definitions(child, containers, definitions)
            start = _start_line(child)
            header_end = min(_start_line(d) for d in inner) - 1 if inner else _end_line(child)
            spans.append(_Span(start, max(header_end, start), _kind(child), symbol, parent))
            _visit(child, language, symbol, spans)
        elif child.type in definitions:
            kind = _kind(child)
            if kind == "function" and parent is not None:
                kind = "method"
            symbol = _qualify(parent, _name(child))
            spans.append(_Span(_start_line(child), _end_line(child), kind, symbol, parent))
        elif (name := _value_function(child)) is not None:
            symbol = _qualify(parent, name)
            spans.append(_Span(_start_line(child), _end_line(child), "function", symbol, parent))
        else:
            _visit(child, language, parent, spans)


def _inner_definitions(
    node: Node, containers: frozenset[str], definitions: frozenset[str]
) -> list[Node]:
    """The nearest definitions inside a container. It does not look inside those."""
    found: list[Node] = []

    def walk(current: Node) -> None:
        for child in current.named_children:
            if child.type in containers or child.type in definitions or _value_function(child):
                found.append(child)
            else:
                walk(child)

    walk(node)
    return found


def _value_function(node: Node) -> str | None:
    """`const handler = () => {}` holds no name field, so the declarator carries the name."""
    if node.type not in {"lexical_declaration", "variable_declaration"}:
        return None
    for declarator in node.named_children:
        if declarator.type != "variable_declarator":
            continue
        value = declarator.child_by_field_name("value")
        if value is not None and value.type in VALUE_FUNCTIONS:
            name = declarator.child_by_field_name("name")
            return name.text.decode(errors="replace") if name is not None else "anonymous"
    return None


def _start_line(node: Node) -> int:
    """A wrapper such as `export` or a decorator belongs to the chunk that it changes."""
    top = node
    while top.parent is not None and top.parent.type in WRAPPERS:
        top = top.parent
    return top.start_point[0] + 1


def _end_line(node: Node) -> int:
    return node.end_point[0] + 1


def _name(node: Node) -> str:
    field = node.child_by_field_name("name")
    return field.text.decode(errors="replace") if field is not None else "anonymous"


def _kind(node: Node) -> str:
    return KINDS.get(node.type, node.type)


def _qualify(parent: str | None, name: str) -> str:
    return f"{parent}.{name}" if parent else name


def _gap_spans(spans: list[_Span], lines: list[str]) -> list[_Span]:
    """Every line that no definition claims becomes a line window, so nothing is lost."""
    covered = bytearray(len(lines) + 2)
    for span in spans:
        for line_no in range(span.start, min(span.end, len(lines)) + 1):
            covered[line_no] = 1

    out: list[_Span] = []
    run: list[int] = []
    for line_no in range(1, len(lines) + 1):
        if covered[line_no]:
            out.extend(_windows(run))
            run = []
        else:
            run.append(line_no)
    out.extend(_windows(run))
    return [span for span in out if _substantive(span, lines)]


def _windows(run: list[int]) -> list[_Span]:
    return [
        _Span(block[0], block[-1], "file_part")
        for block in (run[i : i + WINDOW_LINES] for i in range(0, len(run), WINDOW_LINES))
    ]


def _substantive(span: _Span, lines: list[str]) -> bool:
    return any(lines[n - 1].strip() not in TRIVIAL for n in range(span.start, span.end + 1))


def _emit(
    path: str, language: str, span: _Span, lines: list[str], imports: tuple[str, ...]
) -> list[Chunk]:
    body = lines[span.start - 1 : span.end]
    text = "\n".join(body)

    def build(start: int, end: int, chunk_text: str, part: int, parts: int) -> Chunk:
        return Chunk(
            path=path,
            language=language,
            kind=span.kind,
            start_line=start,
            end_line=end,
            text=chunk_text,
            symbol=span.symbol,
            parent=span.parent,
            imports=imports,
            part=part,
            parts=parts,
        )

    if len(text) <= MAX_CHARS:
        return [build(span.start, span.end, text, 1, 1)]

    pieces: list[tuple[int, int, str]] = []
    current: list[str] = []
    start = span.start
    for offset, line in enumerate(body):
        current.append(line)
        if sum(len(item) + 1 for item in current) >= MAX_CHARS:
            pieces.append((start, span.start + offset, "\n".join(current)))
            current, start = [], span.start + offset + 1
    if current:
        pieces.append((start, span.end, "\n".join(current)))

    return [
        build(a, b, piece, index + 1, len(pieces)) for index, (a, b, piece) in enumerate(pieces)
    ]


def _imports(lines: list[str], language: str | None, limit: int = 20) -> tuple[str, ...]:
    pattern = IMPORT_PATTERNS.get(language or "")
    if pattern is None:
        return ()
    found = [line.strip() for line in lines[:200] if pattern.match(line)]
    return tuple(found[:limit])
