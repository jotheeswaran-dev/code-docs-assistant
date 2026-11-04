"use client";

import { Fragment, type ReactNode } from "react";

import { highlight } from "@/lib/highlight";

/**
 * The answer uses a known subset of markdown. We render that subset ourselves so a
 * citation can become a button inside the text, and so a half-written block that is
 * still streaming renders without a fault.
 */

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "code"; language: string; code: string };

const FENCE = /^```(\w*)\s*$/;
const BULLET = /^\s*[-*+]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const HEADING = /^(#{1,6})\s+(.*)$/;
const INLINE = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\[c\d+\])/g;

export function parse(markdown: string): Block[] {
  const blocks: Block[] = [];
  const lines = markdown.split("\n");
  let paragraph: string[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flush = () => {
    if (paragraph.length) {
      blocks.push({ kind: "paragraph", text: paragraph.join(" ").trim() });
      paragraph = [];
    }
    if (list) {
      blocks.push({ kind: "list", ...list });
      list = null;
    }
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const fence = FENCE.exec(line);

    if (fence) {
      flush();
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !FENCE.test(lines[i])) {
        code.push(lines[i]);
        i += 1;
      }
      blocks.push({ kind: "code", language: fence[1] || "text", code: code.join("\n") });
      continue;
    }

    if (!line.trim()) {
      flush();
      continue;
    }

    const heading = HEADING.exec(line);
    if (heading) {
      flush();
      blocks.push({ kind: "heading", level: heading[1].length, text: heading[2] });
      continue;
    }

    const item = BULLET.exec(line) ?? NUMBERED.exec(line);
    if (item) {
      if (paragraph.length) flush();
      const ordered = !BULLET.test(line);
      if (!list || list.ordered !== ordered) {
        if (list) blocks.push({ kind: "list", ...list });
        list = { ordered, items: [] };
      }
      list.items.push(item[1]);
      continue;
    }

    if (list) flush();
    paragraph.push(line);
  }

  flush();
  return blocks;
}

export function AnswerBody({
  text,
  onCite,
  activeCitation,
}: {
  text: string;
  onCite: (id: string) => void;
  activeCitation: string | null;
}) {
  return (
    <div className="space-y-3 text-[15px] leading-relaxed">
      {parse(text).map((block, index) => (
        <Fragment key={index}>{renderBlock(block, onCite, activeCitation)}</Fragment>
      ))}
    </div>
  );
}

function renderBlock(
  block: Block,
  onCite: (id: string) => void,
  active: string | null,
): ReactNode {
  switch (block.kind) {
    case "heading":
      return (
        <h3 className="pt-1 text-xs font-semibold uppercase tracking-wider text-neutral-500">
          {inline(block.text, onCite, active)}
        </h3>
      );
    case "code":
      return (
        <pre className="overflow-x-auto rounded-md border border-neutral-200 bg-neutral-50 p-3 font-mono text-[12.5px] leading-5 dark:border-neutral-800 dark:bg-neutral-900">
          <code
            dangerouslySetInnerHTML={{ __html: highlight(block.code, "", block.language) }}
          />
        </pre>
      );
    case "list":
      return (
        <ul className="space-y-1.5 pl-1">
          {block.items.map((item, index) => (
            <li key={index} className="flex gap-2.5">
              <span
                aria-hidden
                className="mt-[0.55rem] h-1 w-1 shrink-0 rounded-full bg-neutral-400"
              />
              <span>{inline(item, onCite, active)}</span>
            </li>
          ))}
        </ul>
      );
    default:
      return <p>{inline(block.text, onCite, active)}</p>;
  }
}

function inline(text: string, onCite: (id: string) => void, active: string | null): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;

  for (const match of text.matchAll(INLINE)) {
    const at = match.index ?? 0;
    if (at > last) out.push(text.slice(last, at));
    const token = match[0];

    if (token.startsWith("`")) {
      out.push(
        <code
          key={`${at}-c`}
          className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-[12.5px] text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**")) {
      out.push(
        <strong key={`${at}-b`} className="font-semibold">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      const id = token.slice(1, -1);
      out.push(
        <button
          key={`${at}-${id}`}
          type="button"
          onClick={() => onCite(id)}
          title={`Show source ${id}`}
          className={`mx-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded px-1 align-[1px] font-mono text-[11px] font-medium transition ${
            active === id
              ? "bg-indigo-600 text-white"
              : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-500/15 dark:text-indigo-300 dark:hover:bg-indigo-500/25"
          }`}
        >
          {id.slice(1)}
        </button>,
      );
    }
    last = at + token.length;
  }

  if (last < text.length) out.push(text.slice(last));
  return out;
}
