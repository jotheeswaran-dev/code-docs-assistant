"use client";

import type { Trace } from "@/lib/types";

export function TracePanel({ trace }: { trace: Trace | null }) {
  if (!trace) {
    return (
      <p className="px-4 py-6 text-sm text-neutral-500">
        Every answer records what it retrieved, what it cost, and whether each claim
        carries proof. That record appears here.
      </p>
    );
  }

  const { usage, citations } = trace;
  const cacheTotal = usage.cache_read_tokens + usage.cache_write_tokens;
  const cacheShare = cacheTotal ? Math.round((usage.cache_read_tokens / cacheTotal) * 100) : 0;

  return (
    <div className="space-y-5 px-4 py-4">
      <Section title="Time">
        <Stat label="Retrieval" value={`${trace.retrieval_ms} ms`} />
        <Stat label="Answer" value={`${(trace.answer_ms / 1000).toFixed(1)} s`} />
      </Section>

      <Section title="Tokens">
        <Stat label="Input" value={usage.input_tokens.toLocaleString()} />
        <Stat label="Output" value={usage.output_tokens.toLocaleString()} />
        <Stat
          label="Cache read"
          value={usage.cache_read_tokens.toLocaleString()}
          tone={usage.cache_read_tokens > 0 ? "good" : undefined}
        />
        <Stat label="Cache write" value={usage.cache_write_tokens.toLocaleString()} />
      </Section>

      <Section title="Cost">
        <Stat label="This answer" value={`$${trace.cost_usd.toFixed(4)}`} />
        <Stat
          label="From cache"
          value={cacheTotal ? `${cacheShare}%` : "cold"}
          tone={cacheShare > 0 ? "good" : undefined}
        />
      </Section>

      <div>
        <h4 className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-neutral-400">
          Citations
        </h4>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
          <Stat label="Claims" value={String(citations.claims)} />
          <Stat label="Sources used" value={String(citations.cited.length)} />
        </div>

        {citations.unknown.length > 0 && (
          <Note tone="bad">
            The answer named {citations.unknown.join(", ")}, which is not a source that we
            sent. Treat that claim as unproven.
          </Note>
        )}

        {citations.uncited.length > 0 && (
          <Note tone="warn">
            {citations.uncited.length} line
            {citations.uncited.length === 1 ? "" : "s"} state a fact with no citation:
            <ul className="mt-1.5 space-y-1">
              {citations.uncited.map((line, index) => (
                <li key={index} className="truncate font-mono text-[11px] opacity-80">
                  {line}
                </li>
              ))}
            </ul>
          </Note>
        )}

        {citations.clean && (
          <Note tone="good">Every claim in this answer points at a source.</Note>
        )}
      </div>

      <p className="border-t border-neutral-200 pt-3 font-mono text-[11px] text-neutral-400 dark:border-neutral-800">
        {trace.model} · stop: {trace.stop_reason}
      </p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-[10.5px] font-semibold uppercase tracking-wider text-neutral-400">
        {title}
      </h4>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">{children}</div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "good" }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-[12px] text-neutral-500">{label}</span>
      <span
        className={`font-mono text-[12.5px] tabular-nums ${
          tone === "good"
            ? "text-emerald-600 dark:text-emerald-400"
            : "text-neutral-800 dark:text-neutral-200"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function Note({ tone, children }: { tone: "good" | "warn" | "bad"; children: React.ReactNode }) {
  const styles = {
    good: "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300",
    warn: "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300",
    bad: "border-red-200 bg-red-50 text-red-800 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300",
  }[tone];

  return <div className={`mt-2.5 rounded-md border px-3 py-2 text-[12px] ${styles}`}>{children}</div>;
}
