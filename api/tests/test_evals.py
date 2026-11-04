import pytest

from app.evals.run import Score, load, rank_of, rankings_for, retrieval_scores
from app.ingest.models import Chunk
from app.retrieval import search as search_module
from app.store import EMBEDDING_SIZE, Store


def vector(slot: int) -> list[float]:
    values = [0.0] * EMBEDDING_SIZE
    values[slot % EMBEDDING_SIZE] = 1.0
    return values


def test_the_question_set_is_well_formed():
    questions = load()
    assert len(questions) >= 10

    for item in questions:
        assert item.question.endswith("?"), item.question
        if item.answerable:
            assert item.expect_files, f"an answerable question needs a target: {item.question}"
        else:
            assert not item.expect_files, f"an unanswerable question needs none: {item.question}"


def test_the_set_holds_questions_that_must_be_refused():
    """Without these, a model that answers everything would score full marks."""
    assert sum(1 for item in load() if not item.answerable) >= 3


def test_a_question_is_not_asked_twice():
    asked = [item.question for item in load()]
    assert len(set(asked)) == len(asked)


def test_rank_of_finds_the_first_wanted_path():
    assert rank_of(["a.py", "b.py", "c.py"], ["c.py"]) == 3
    assert rank_of(["a.py", "b.py"], ["b.py", "a.py"]) == 1
    assert rank_of(["a.py"], ["z.py"]) is None
    assert rank_of([], ["a.py"]) is None


def test_the_score_reports_recall_and_mrr():
    score = Score(hits=3, asked=4, reciprocal=1 + 0.5 + 0.25)
    assert score.recall == pytest.approx(0.75)
    assert score.mrr == pytest.approx(1.75 / 4)


def test_an_empty_score_does_not_divide_by_zero():
    assert Score().recall == 0.0
    assert Score().mrr == 0.0


@pytest.fixture
def store(tmp_path):
    made = Store.open(tmp_path / "eval.db", create=True)
    made.write(
        [
            Chunk(
                path="src/auth.py",
                language="python",
                kind="function",
                start_line=1,
                end_line=3,
                text="def basic_auth(user): ...",
                symbol="basic_auth",
            ),
            Chunk(
                path="src/other.py",
                language="python",
                kind="function",
                start_line=1,
                end_line=3,
                text="def unrelated(): ...",
                symbol="unrelated",
            ),
        ],
        [vector(0), vector(1)],
    )
    yield made
    made.close()


def test_every_mode_returns_a_ranking(store, monkeypatch):
    monkeypatch.setattr(search_module, "embed_query", lambda _: vector(0))
    monkeypatch.setattr("app.evals.run.embed_query", lambda _: vector(0))

    rankings = rankings_for(store, "basic_auth", 5)
    assert set(rankings) == {"word", "vector", "fused"}
    assert rankings["word"][0] == "src/auth.py"


def test_the_report_counts_only_answerable_questions(store, monkeypatch):
    from app.evals.run import Question

    monkeypatch.setattr(search_module, "embed_query", lambda _: vector(0))
    monkeypatch.setattr("app.evals.run.embed_query", lambda _: vector(0))

    questions = [
        Question("Where is basic auth?", ("src/auth.py",), True),
        Question("Where is the database?", (), False),
    ]
    recall, overall = retrieval_scores(store, questions, [1, 3])

    assert overall["word"].asked == 1
    assert recall["word"][3] == pytest.approx(1.0)
