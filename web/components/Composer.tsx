"use client";

import { useState } from "react";

export function Composer({
  onAsk,
  onStop,
  busy,
  disabled,
}: {
  onAsk: (question: string) => void;
  onStop: () => void;
  busy: boolean;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const question = value.trim();
    if (!question || busy || disabled) return;
    onAsk(question);
    setValue("");
  };

  return (
    <div className="border-t border-neutral-200 bg-white/80 p-3 backdrop-blur dark:border-neutral-800 dark:bg-neutral-950/80">
      <div className="flex items-end gap-2 rounded-lg border border-neutral-300 bg-white px-3 py-2 focus-within:border-neutral-400 dark:border-neutral-700 dark:bg-neutral-900 dark:focus-within:border-neutral-600">
        <textarea
          rows={1}
          value={value}
          disabled={disabled}
          placeholder={disabled ? "Index a repository first" : "Ask about this repository…"}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          className="max-h-40 flex-1 resize-none bg-transparent py-1 text-[15px] outline-none placeholder:text-neutral-400 disabled:cursor-not-allowed"
        />
        {busy ? (
          <button
            type="button"
            onClick={onStop}
            className="shrink-0 rounded-md border border-neutral-300 px-3 py-1.5 text-[13px] font-medium text-neutral-600 transition hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            disabled={!value.trim() || disabled}
            className="shrink-0 rounded-md bg-neutral-900 px-3 py-1.5 text-[13px] font-medium text-white transition enabled:hover:bg-neutral-700 disabled:opacity-35 dark:bg-white dark:text-neutral-900 dark:enabled:hover:bg-neutral-200"
          >
            Ask
          </button>
        )}
      </div>
      <p className="mt-1.5 px-1 text-[11px] text-neutral-400">
        Every claim carries a citation. Open the trace to see what it cost.
      </p>
    </div>
  );
}
