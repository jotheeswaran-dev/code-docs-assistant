export type Source = {
  id: string;
  path: string;
  symbol: string | null;
  kind: string;
  language: string;
  start_line: number;
  end_line: number;
  label: string;
  text: string;
  enclosing: string | null;
  score: number;
  lexical_rank: number | null;
  vector_rank: number | null;
};

export type Usage = {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
};

export type Citations = {
  claims: number;
  cited: string[];
  unknown: string[];
  uncited: string[];
  clean: boolean;
};

export type Trace = {
  question: string;
  model: string;
  sources: Source[];
  retrieval_ms: number;
  answer_ms: number;
  usage: Usage;
  cost_usd: number;
  citations: Citations;
  stop_reason: string;
};

export type Health = {
  status: string;
  version: string;
  answer_model: string;
  anthropic_key_set: boolean;
  indexed_chunks: number | null;
  indexed_source: string | null;
};

export type Turn = {
  question: string;
  answer: string;
  sources: Source[];
  trace: Trace | null;
  error: string | null;
  streaming: boolean;
};
