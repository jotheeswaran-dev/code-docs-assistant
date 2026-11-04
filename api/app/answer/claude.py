"""The Claude call. It is the only part of the answer step that uses the network."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from anthropic import Anthropic

from app.answer.pipeline import Completed, Event, TextDelta, Usage
from app.config import Settings


class ClaudeAnswerer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    def stream(
        self, system: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> Iterator[Event]:
        with self._client.beta.messages.stream(
            model=self._settings.answer_model,
            max_tokens=self._settings.max_answer_tokens,
            system=system,
            messages=messages,
            thinking={"type": "adaptive"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            for text in stream.text_stream:
                yield TextDelta(text)
            final = stream.get_final_message()

        usage = final.usage
        yield Completed(
            usage=Usage(
                input_tokens=getattr(usage, "input_tokens", 0) or 0,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
                cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            ),
            stop_reason=final.stop_reason or "end_turn",
        )
