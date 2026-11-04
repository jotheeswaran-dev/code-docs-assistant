"""Measure the retrieval and the answers against a fixed set of questions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from app.answer.claude import ClaudeAnswerer
from app.answer.pipeline import answer as run_answer
from app.config import Settings, get_settings
from app.retrieval.embedding import embed_query
from app.retrieval.search import search
from app.store import Store

QUESTIONS = Path(__file__).with_name("questions.json")


@dataclass(frozen=True, slots=True)
class Question:
    question: str
    expect_files: tuple[str, ...]
    answerable: bool


@dataclass
class Score:
    hits: int = 0
    asked: int = 0
    reciprocal: float = 0.0
    missed: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.missed is None:
            self.missed = []

    @property
    def recall(self) -> float:
        return self.hits / self.asked if self.asked else 0.0

    @property
    def mrr(self) -> float:
        return self.reciprocal / self.asked if self.asked else 0.0


def load(path: Path = QUESTIONS) -> list[Question]:
    data = json.loads(path.read_text())
    return [
        Question(row["question"], tuple(row["expect_files"]), row["answerable"])
        for row in data["questions"]
    ]


def paths_for(store: Store, rowids: Sequence[int]) -> list[str]:
    found = store.fetch(rowids)
    return [found[rowid].path for rowid in rowids if rowid in found]


def rank_of(paths: Sequence[str], wanted: Sequence[str]) -> int | None:
    for position, path in enumerate(paths, start=1):
        if path in wanted:
            return position
    return None


MODES = ("word", "vector", "fused")


def rankings_for(store: Store, question: str, depth: int) -> dict[str, list[str]]:
    return {
        "word": paths_for(store, [hit.rowid for hit in store.lexical(question, depth)]),
        "vector": paths_for(
            store, [hit.rowid for hit in store.vector(embed_query(question), depth)]
        ),
        "fused": [result.chunk.path for result in search(store, question, limit=depth)],
    }


def retrieval_scores(
    store: Store, questions: Sequence[Question], depths: Sequence[int]
) -> tuple[dict[str, dict[int, float]], dict[str, Score]]:
    """Recall at each depth, and one overall score taken at the deepest cut."""
    deepest = max(depths)
    recall: dict[str, dict[int, float]] = {name: {k: 0.0 for k in depths} for name in MODES}
    overall = {name: Score() for name in MODES}
    asked = 0

    for item in questions:
        if not item.answerable:
            continue
        asked += 1
        for name, paths in rankings_for(store, item.question, deepest).items():
            place = rank_of(paths, item.expect_files)
            score = overall[name]
            score.asked += 1
            if place is None:
                score.missed.append(item.question)
            else:
                score.hits += 1
                score.reciprocal += 1 / place
            for k in depths:
                if place is not None and place <= k:
                    recall[name][k] += 1

    for name in MODES:
        for k in depths:
            recall[name][k] = recall[name][k] / asked if asked else 0.0

    return recall, overall


JUDGE = """You grade an answer about a code repository.

You see the question, the sources that the answer was given, and the answer.

Reply with one JSON object and nothing else:
{"faithful": true or false, "refused": true or false, "reason": "one short sentence"}

faithful: every factual claim in the answer is supported by the sources.

refused: the answer states that the sources do not hold what the question asked for.
An answer that says the thing is not in this repository, and then explains what the
repository does hold, still counts as refused. Judge the first claim, not the length.
"""


def judge(settings: Settings, question: str, sources: str, text: str) -> dict:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.bulk_model,
        max_tokens=300,
        system=JUDGE,
        messages=[
            {
                "role": "user",
                "content": f"<question>{question}</question>\n"
                f"<sources>{sources[:20000]}</sources>\n"
                f"<answer>{text}</answer>",
            }
        ],
    )
    raw = "".join(block.text for block in message.content if block.type == "text").strip()
    start, end = raw.find("{"), raw.rfind("}")
    try:
        return json.loads(raw[start : end + 1])
    except (ValueError, json.JSONDecodeError):
        return {"faithful": False, "refused": False, "reason": "the judge did not return JSON"}


def answer_scores(store: Store, settings: Settings, questions: Sequence[Question]) -> dict:
    answerer = ClaudeAnswerer(settings)
    faithful = refused_right = clean = 0
    answerable = sum(1 for item in questions if item.answerable)
    unanswerable = len(questions) - answerable
    cost = 0.0
    failures: list[str] = []

    for item in questions:
        text_parts: list[str] = []
        sources: list[dict] = []
        trace: dict | None = None
        for event in run_answer(store, settings, item.question, answerer):
            if event["type"] == "delta":
                text_parts.append(event["text"])
            elif event["type"] == "sources":
                sources = event["sources"]
            elif event["type"] == "trace":
                trace = event["trace"]

        text = "".join(text_parts)
        rendered = "\n\n".join(f"[{s['id']}] {s['label']}\n{s['text']}" for s in sources)
        verdict = judge(settings, item.question, rendered, text)
        cost += (trace or {}).get("cost_usd", 0.0)

        if item.answerable:
            if verdict.get("faithful"):
                faithful += 1
            else:
                failures.append(f"not faithful: {item.question} ({verdict.get('reason')})")
            if (trace or {}).get("citations", {}).get("clean"):
                clean += 1
        elif verdict.get("refused"):
            refused_right += 1
        else:
            failures.append(f"did not refuse: {item.question}")

    return {
        "faithful": faithful,
        "answerable": answerable,
        "clean": clean,
        "refused_right": refused_right,
        "unanswerable": unanswerable,
        "cost": cost,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure retrieval and answers.")
    parser.add_argument("--db", default="data/requests.db")
    parser.add_argument("--k", type=int, default=8, help="The deepest cut to measure")
    parser.add_argument(
        "--answers", action="store_true", help="Also ask the model. This costs money."
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    settings = settings.model_copy(update={"store_path": args.db})
    questions = load()
    store = Store.open(args.db)
    started = time.perf_counter()

    answerable = sum(1 for item in questions if item.answerable)
    depths = [k for k in (1, 3, 5, args.k) if k <= args.k]

    print(f"corpus   {args.db}, {store.count()} chunks")
    print(f"asked    {answerable} answerable, {len(questions) - answerable} unanswerable\n")

    recall, overall = retrieval_scores(store, questions, depths)
    header = "".join(f"{'recall@' + str(k):>11}" for k in depths)
    print(f"  {'retrieval':<10}{header}{'MRR':>8}")
    for name in MODES:
        row = "".join(f"{recall[name][k]:>11.2f}" for k in depths)
        print(f"  {name:<10}{row}{overall[name].mrr:>8.2f}")

    for question in overall["fused"].missed:
        print(f"\n  the join missed: {question}")

    if args.answers:
        print()
        report = answer_scores(store, settings, questions)
        print(f"  {'answers':<22}{'result':>12}")
        print(f"  {'faithful':<22}{report['faithful']}/{report['answerable']:<11}")
        print(f"  {'citations clean':<22}{report['clean']}/{report['answerable']:<11}")
        print(
            f"  {'refused when it must':<22}{report['refused_right']}/{report['unanswerable']:<11}"
        )
        print(f"  {'total cost':<22}${report['cost']:.3f}")
        for failure in report["failures"]:
            print(f"    {failure}")

    store.close()
    print(f"\ntook {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
