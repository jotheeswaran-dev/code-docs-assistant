"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { AnswerBody } from "@/components/AnswerBody";
import { Composer } from "@/components/Composer";
import { SourcePanel } from "@/components/SourcePanel";
import { TracePanel } from "@/components/TracePanel";
import type { Health } from "@/lib/types";
import { useChat } from "@/lib/useChat";

const EXAMPLES = [
  "What does this repository do?",
  "How is the configuration loaded?",
  "Where does it handle errors?",
];

export default function Home() {
  const { turns, busy, ask, stop } = useChat();
  const [health, setHealth] = useState<Health | null>(null);
  const [tab, setTab] = useState<"sources" | "trace">("sources");
  const [citation, setCitation] = useState<string | null>(null);
  const tail = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const last = turns.at(-1) ?? null;
  useEffect(() => {
    tail.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [last?.answer, turns.length]);

  const ready = Boolean(health?.indexed_chunks);
  const repo = useMemo(
    () => health?.indexed_source?.split("/").filter(Boolean).pop() ?? null,
    [health],
  );

  const openCitation = (id: string) => {
    setCitation(id);
    setTab("sources");
  };

  return (
    <div className="flex h-screen flex-col bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <header className="flex shrink-0 items-center gap-3 border-b border-neutral-200 bg-white px-4 py-2.5 dark:border-neutral-800 dark:bg-neutral-950">
        <h1 className="text-[13px] font-semibold tracking-tight">Code Documentation Assistant</h1>
        {repo && (
          <span className="truncate rounded bg-neutral-100 px-2 py-0.5 font-mono text-[11.5px] text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">
            {repo}
          </span>
        )}
        <div className="ml-auto flex items-center gap-3 text-[11px] text-neutral-500">
          {health?.indexed_chunks != null && (
            <span>{health.indexed_chunks.toLocaleString()} chunks</span>
          )}
          <span className="hidden font-mono sm:inline">{health?.answer_model}</span>
          <span
            title={health?.anthropic_key_set ? "API key is set" : "No API key"}
            className={`h-1.5 w-1.5 rounded-full ${
              health?.anthropic_key_set ? "bg-emerald-500" : "bg-amber-500"
            }`}
          />
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        <main className="flex min-h-0 flex-1 flex-col lg:border-r lg:border-neutral-200 lg:dark:border-neutral-800">
          <div className="min-h-0 flex-1 overflow-y-auto">
            <div className="mx-auto max-w-3xl px-4 py-6">
              {!turns.length && <Welcome health={health} ready={ready} onPick={ask} />}

              {turns.map((turn, index) => (
                <article key={index} className="mb-8">
                  <h2 className="mb-3 text-[15px] font-semibold">{turn.question}</h2>

                  {turn.error ? (
                    <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-red-800 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                      {turn.error}
                    </p>
                  ) : (
                    <>
                      <AnswerBody
                        text={turn.answer}
                        onCite={openCitation}
                        activeCitation={citation}
                      />
                      {turn.streaming && !turn.answer && (
                        <p className="text-[13px] text-neutral-400">
                          {turn.sources.length
                            ? `Reading ${turn.sources.length} sources…`
                            : "Searching the repository…"}
                        </p>
                      )}
                      {turn.streaming && turn.answer && (
                        <span className="ml-0.5 inline-block h-3.5 w-[2px] animate-pulse bg-neutral-400 align-middle" />
                      )}
                    </>
                  )}
                </article>
              ))}
              <div ref={tail} />
            </div>
          </div>

          <Composer onAsk={ask} onStop={stop} busy={busy} disabled={!ready} />
        </main>

        <aside className="flex min-h-0 shrink-0 flex-col border-t border-neutral-200 bg-white lg:w-[380px] lg:border-t-0 dark:border-neutral-800 dark:bg-neutral-950">
          <div className="flex shrink-0 gap-1 border-b border-neutral-200 px-2 pt-2 dark:border-neutral-800">
            {(["sources", "trace"] as const).map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => setTab(name)}
                className={`rounded-t-md px-3 py-1.5 text-[12px] font-medium capitalize transition ${
                  tab === name
                    ? "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-100"
                    : "text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-300"
                }`}
              >
                {name}
                {name === "sources" && last?.sources.length ? ` (${last.sources.length})` : ""}
              </button>
            ))}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {tab === "sources" ? (
              <SourcePanel
                sources={last?.sources ?? []}
                active={citation}
                onSelect={setCitation}
              />
            ) : (
              <TracePanel trace={last?.trace ?? null} />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

function Welcome({
  health,
  ready,
  onPick,
}: {
  health: Health | null;
  ready: boolean;
  onPick: (question: string) => void;
}) {
  // Until health answers we know nothing, so we must not claim that the index is missing.
  if (health === null) {
    return <div className="h-24 animate-pulse rounded-lg bg-neutral-100 dark:bg-neutral-900" />;
  }

  if (!ready) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="text-[14px] font-semibold">No repository is indexed yet</h2>
        <p className="mt-1.5 text-[13px] text-neutral-600 dark:text-neutral-400">
          Index one, then reload this page.
        </p>
        <pre className="mt-3 overflow-x-auto rounded-md bg-neutral-100 px-3 py-2 font-mono text-[12.5px] dark:bg-neutral-800">
          <code>make ingest REPO=~/some/repository</code>
        </pre>
        {health && !health.anthropic_key_set && (
          <p className="mt-3 text-[12.5px] text-amber-700 dark:text-amber-400">
            No API key is set. Put ANTHROPIC_API_KEY in .env to get answers. Search works
            without it.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="py-6">
      <h2 className="text-[15px] font-semibold">Ask about this repository</h2>
      <p className="mt-1 max-w-md text-[13px] text-neutral-600 dark:text-neutral-400">
        Every answer points at the exact file and lines that prove it. Open the trace to
        see what was retrieved and what it cost.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {EXAMPLES.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onPick(question)}
            className="rounded-full border border-neutral-300 px-3 py-1.5 text-[12.5px] text-neutral-700 transition hover:border-neutral-400 hover:bg-white dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
