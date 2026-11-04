"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  version: string;
  answer_model: string;
  anthropic_key_set: boolean;
};

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-4 py-16">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Code Documentation Assistant</h1>
        <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
          Ask questions about a code repository. Every answer cites the code.
        </p>
      </header>

      <section className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">
          Service status
        </h2>
        {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">API unreachable: {error}</p>}
        {!error && !health && <p className="mt-3 text-sm text-neutral-500">Checking…</p>}
        {health && (
          <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 text-sm">
            <Row label="API" value={health.status} />
            <Row label="Version" value={health.version} />
            <Row label="Answer model" value={health.answer_model} />
            <Row
              label="Anthropic key"
              value={health.anthropic_key_set ? "configured" : "not set"}
              warn={!health.anthropic_key_set}
            />
          </dl>
        )}
      </section>

      <p className="text-xs text-neutral-500">
        Step 1 of 6. The ingest and the answer steps come next.
      </p>
    </main>
  );
}

function Row({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <>
      <dt className="text-neutral-500">{label}</dt>
      <dd className={warn ? "text-amber-600 dark:text-amber-400" : "font-mono text-xs leading-5"}>
        {value}
      </dd>
    </>
  );
}
