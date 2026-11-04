"use client";

import { useEffect, useMemo, useRef } from "react";

import { highlight } from "@/lib/highlight";

import type { Source } from "@/lib/types";

export function SourcePanel({
  sources,
  active,
  onSelect,
}: {
  sources: Source[];
  active: string | null;
  onSelect: (id: string | null) => void;
}) {
  if (!sources.length) {
    return (
      <p className="px-4 py-6 text-sm text-neutral-500">
        The code behind each answer appears here. Ask a question to begin.
      </p>
    );
  }

  return (
    <div className="divide-y divide-neutral-200 dark:divide-neutral-800">
      {sources.map((source) => (
        <SourceCard
          key={source.id}
          source={source}
          open={active === source.id}
          onToggle={() => onSelect(active === source.id ? null : source.id)}
        />
      ))}
    </div>
  );
}

function SourceCard({
  source,
  open,
  onToggle,
}: {
  source: Source;
  open: boolean;
  onToggle: () => void;
}) {
  const node = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) node.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [open]);

  return (
    <div ref={node} className={open ? "bg-indigo-50/40 dark:bg-indigo-500/5" : undefined}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start gap-2.5 px-4 py-3 text-left transition hover:bg-neutral-50 dark:hover:bg-neutral-900"
      >
        <span
          className={`mt-px inline-flex h-[18px] min-w-[18px] items-center justify-center rounded px-1 font-mono text-[11px] font-medium ${
            open
              ? "bg-indigo-600 text-white"
              : "bg-indigo-50 text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300"
          }`}
        >
          {source.id.slice(1)}
        </span>

        <span className="min-w-0 flex-1">
          <span className="block truncate font-mono text-[12.5px] text-neutral-800 dark:text-neutral-200">
            {source.symbol ?? source.path.split("/").pop()}
          </span>
          <span className="mt-0.5 block truncate text-[11.5px] text-neutral-500">
            {source.path}:{source.start_line}-{source.end_line}
          </span>
        </span>

        <span className="flex shrink-0 items-center gap-1.5 pt-px">
          <Tag>{source.kind}</Tag>
          <Rank label="w" value={source.lexical_rank} />
          <Rank label="v" value={source.vector_rank} />
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4">
          {source.enclosing && (
            <div className="mb-1.5 rounded-md border border-dashed border-neutral-300 bg-neutral-50 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900">
              <p className="mb-1 text-[10.5px] uppercase tracking-wider text-neutral-400">
                Enclosing
              </p>
              <Code
                text={source.enclosing}
                path={source.path}
                language={source.language}
                startLine={null}
              />
            </div>
          )}
          <div className="overflow-hidden rounded-md border border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900">
            <div className="border-b border-neutral-200 px-3 py-1.5 text-[11px] text-neutral-500 dark:border-neutral-800">
              {source.path} · {source.language}
            </div>
            <div className="px-3 py-2">
              <Code
                text={source.text}
                path={source.path}
                language={source.language}
                startLine={source.start_line}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Code({
  text,
  path,
  language,
  startLine,
}: {
  text: string;
  path: string;
  language: string;
  startLine: number | null;
}) {
  const html = useMemo(() => highlight(text, path, language), [text, path, language]);
  const count = text.split("\n").length;

  return (
    <div className="flex gap-3 overflow-x-auto font-mono text-[12px] leading-[1.6]">
      {startLine !== null && (
        <div className="sticky left-0 z-10 select-none bg-neutral-50 pr-1 text-right tabular-nums text-neutral-400 dark:bg-neutral-900 dark:text-neutral-600">
          {Array.from({ length: count }, (_, index) => (
            <div key={index}>{startLine + index}</div>
          ))}
        </div>
      )}
      <pre className="min-w-0 flex-1 text-neutral-800 dark:text-neutral-200">
        <code dangerouslySetInnerHTML={{ __html: html }} />
      </pre>
    </div>
  );
}

function Tag({ children }: { children: string }) {
  return (
    <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10.5px] text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
      {children}
    </span>
  );
}

function Rank({ label, value }: { label: string; value: number | null }) {
  return (
    <span
      title={label === "w" ? `Word search rank: ${value ?? "no match"}` : `Vector rank: ${value ?? "no match"}`}
      className={`rounded px-1 py-0.5 font-mono text-[10.5px] ${
        value === null
          ? "text-neutral-300 dark:text-neutral-700"
          : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400"
      }`}
    >
      {label}
      {value ?? "-"}
    </span>
  );
}
