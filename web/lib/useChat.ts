"use client";

import { useCallback, useRef, useState } from "react";

import type { Source, Trace, Turn } from "./types";

type ServerEvent =
  | { type: "sources"; sources: Source[] }
  | { type: "delta"; text: string }
  | { type: "trace"; trace: Trace }
  | { type: "error"; message: string }
  | { type: "done" };

export function useChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const abort = useRef<AbortController | null>(null);

  const patchLast = useCallback((change: (turn: Turn) => Turn) => {
    setTurns((all) => all.map((turn, i) => (i === all.length - 1 ? change(turn) : turn)));
  }, []);

  const stop = useCallback(() => {
    abort.current?.abort();
    abort.current = null;
    setBusy(false);
    patchLast((turn) => ({ ...turn, streaming: false }));
  }, [patchLast]);

  const ask = useCallback(
    async (question: string) => {
      const controller = new AbortController();
      abort.current = controller;
      setBusy(true);
      setTurns((all) => [
        ...all,
        { question, answer: "", sources: [], trace: null, error: null, streaming: true },
      ]);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ question }),
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          const detail = await response.json().catch(() => null);
          throw new Error(detail?.detail ?? `The server answered ${response.status}.`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // An event ends with a blank line. The tail may be a partial event.
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";
          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith("data:")) continue;
            apply(JSON.parse(line.slice(5).trim()) as ServerEvent, patchLast);
          }
        }
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          patchLast((turn) => ({ ...turn, error: (error as Error).message }));
        }
      } finally {
        patchLast((turn) => ({ ...turn, streaming: false }));
        setBusy(false);
        abort.current = null;
      }
    },
    [patchLast],
  );

  return { turns, busy, ask, stop };
}

function apply(event: ServerEvent, patchLast: (change: (turn: Turn) => Turn) => void) {
  switch (event.type) {
    case "sources":
      patchLast((turn) => ({ ...turn, sources: event.sources }));
      break;
    case "delta":
      patchLast((turn) => ({ ...turn, answer: turn.answer + event.text }));
      break;
    case "trace":
      patchLast((turn) => ({ ...turn, trace: event.trace }));
      break;
    case "error":
      patchLast((turn) => ({ ...turn, error: event.message }));
      break;
    case "done":
      patchLast((turn) => ({ ...turn, streaming: false }));
      break;
  }
}
