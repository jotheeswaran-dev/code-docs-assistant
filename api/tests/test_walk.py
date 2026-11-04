from pathlib import Path

from app.ingest.languages import detect
from app.ingest.walk import load


def build_repo(root: Path) -> Path:
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("def f():\n    return 1\n")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "dep.js").write_text("module.exports = 1;\n")
    (root / "uv.lock").write_text("lock\n")
    (root / "app.min.js").write_text("var a=1;\n")
    (root / "server.pem").write_text("-----BEGIN PRIVATE KEY-----\n")
    (root / ".env").write_text("TOKEN=abc\n")
    (root / "logo.png").write_bytes(b"\x89PNG\x00\x00binary")
    (root / "empty.py").write_text("   \n")
    return root


def test_it_indexes_source_and_skips_the_rest(tmp_path):
    files, skipped = load(build_repo(tmp_path))

    assert [f.path for f in files] == ["src/app.py"]
    assert skipped["lock file"] == 1
    assert skipped["minified"] == 1
    assert skipped["possible secret"] == 2
    assert skipped["binary"] == 1
    assert skipped["empty"] == 1


def test_a_key_file_never_reaches_the_index(tmp_path):
    files, _ = load(build_repo(tmp_path))
    text = " ".join(f.text for f in files)
    assert "PRIVATE KEY" not in text
    assert "TOKEN=abc" not in text


def test_a_vendored_directory_is_not_walked(tmp_path):
    files, _ = load(build_repo(tmp_path))
    assert not any("node_modules" in f.path for f in files)


def test_it_names_the_language():
    assert detect("a/b/thing.py") == "python"
    assert detect("Component.tsx") == "tsx"
    assert detect("lib/store.rb") == "ruby"
    assert detect("Gemfile") == "ruby"
    assert detect("README.md") is None
