import hljs from "highlight.js/lib/core";
import bash from "highlight.js/lib/languages/bash";
import css from "highlight.js/lib/languages/css";
import dockerfile from "highlight.js/lib/languages/dockerfile";
import ini from "highlight.js/lib/languages/ini";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import markdown from "highlight.js/lib/languages/markdown";
import python from "highlight.js/lib/languages/python";
import ruby from "highlight.js/lib/languages/ruby";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import yaml from "highlight.js/lib/languages/yaml";

// Only the languages that a repository actually holds, so the bundle stays small.
const LANGUAGES = {
  bash, css, dockerfile, ini, javascript, json, markdown, python, ruby, typescript, xml, yaml,
};
for (const [name, definition] of Object.entries(LANGUAGES)) {
  hljs.registerLanguage(name, definition);
}

const BY_EXTENSION: Record<string, string> = {
  py: "python", pyi: "python",
  rb: "ruby", rake: "ruby", gemspec: "ruby",
  ts: "typescript", tsx: "typescript", mts: "typescript", cts: "typescript",
  js: "javascript", jsx: "javascript", mjs: "javascript", cjs: "javascript",
  sh: "bash", bash: "bash", zsh: "bash", zshrc: "bash", zshenv: "bash", aliases: "bash",
  yml: "yaml", yaml: "yaml",
  json: "json",
  md: "markdown", markdown: "markdown",
  toml: "ini", ini: "ini", conf: "ini", cfg: "ini", editorconfig: "ini",
  html: "xml", xml: "xml", svg: "xml",
  css: "css",
};

const BY_FILENAME: Record<string, string> = {
  Gemfile: "ruby", Rakefile: "ruby", Brewfile: "ruby", Dockerfile: "dockerfile",
  Makefile: "bash",
};

// The chunker records tsx as its own language. highlight.js reads it as typescript.
const BY_DECLARED: Record<string, string> = {
  python: "python", ruby: "ruby", javascript: "javascript",
  typescript: "typescript", tsx: "typescript",
};

/** The file name decides the language. A file with no parser still gets colour. */
export function languageFor(path: string, declared: string): string | null {
  const name = path.split("/").pop() ?? "";

  if (BY_FILENAME[name]) return BY_FILENAME[name];

  const dot = name.lastIndexOf(".");
  if (dot > 0) {
    const found = BY_EXTENSION[name.slice(dot + 1).toLowerCase()];
    if (found) return found;
  }
  if (name.startsWith(".")) {
    const found = BY_EXTENSION[name.slice(1).toLowerCase()];
    if (found) return found;
  }

  if (BY_DECLARED[declared]) return BY_DECLARED[declared];
  return hljs.getLanguage(declared) ? declared : null;
}

export function highlight(code: string, path: string, declared: string): string {
  const language = languageFor(path, declared);
  if (!language) return escape(code);
  try {
    return hljs.highlight(code, { language, ignoreIllegals: true }).value;
  } catch {
    return escape(code);
  }
}

function escape(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
