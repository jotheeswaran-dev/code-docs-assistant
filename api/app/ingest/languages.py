"""Which language a file holds, and which syntax nodes become a chunk."""

from __future__ import annotations

import re

EXTENSIONS = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".rb": "ruby",
    ".rake": "ruby",
}

FILENAMES = {
    "Gemfile": "ruby",
    "Rakefile": "ruby",
    "Brewfile": "ruby",
}

# A container holds other definitions. We recurse into it and keep its header as one chunk.
CONTAINERS = {
    "python": frozenset({"class_definition"}),
    "ruby": frozenset({"class", "module"}),
    "typescript": frozenset({"class_declaration"}),
    "tsx": frozenset({"class_declaration"}),
    "javascript": frozenset({"class_declaration"}),
}

# A definition becomes one chunk. We do not recurse into it, so a closure stays with its owner.
DEFINITIONS = {
    "python": frozenset({"function_definition"}),
    "ruby": frozenset({"method", "singleton_method"}),
    "typescript": frozenset(
        {
            "function_declaration",
            "generator_function_declaration",
            "method_definition",
            "interface_declaration",
            "type_alias_declaration",
            "enum_declaration",
        }
    ),
}
DEFINITIONS["tsx"] = DEFINITIONS["typescript"]
DEFINITIONS["javascript"] = frozenset(
    {"function_declaration", "generator_function_declaration", "method_definition"}
)

# A declaration may sit inside a wrapper. The chunk must start at the wrapper, so that
# `export` and a decorator stay with the code that they change.
WRAPPERS = frozenset({"export_statement", "decorated_definition", "export_default_declaration"})

# `const handler = () => {}` holds no name field, so it needs its own rule.
VALUE_FUNCTIONS = frozenset({"arrow_function", "function_expression", "function"})

IMPORT_PATTERNS = {
    "python": re.compile(r"^\s*(?:import|from)\s+\S"),
    "typescript": re.compile(r"^\s*(?:import|export)\s+.*\bfrom\b"),
    "ruby": re.compile(r"^\s*(?:require|require_relative|load)\s+\S"),
}
IMPORT_PATTERNS["tsx"] = IMPORT_PATTERNS["typescript"]
IMPORT_PATTERNS["javascript"] = IMPORT_PATTERNS["typescript"]

PARSED = frozenset(DEFINITIONS)


def detect(path: str) -> str | None:
    """Return the language name, or None when no parser covers the file."""
    name = path.rsplit("/", 1)[-1]
    if name in FILENAMES:
        return FILENAMES[name]
    dot = name.rfind(".")
    return EXTENSIONS.get(name[dot:]) if dot > 0 else None
