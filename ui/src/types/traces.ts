export interface SpanAttrs {
  task_id?: string
  task_kind?: 'find_bugs' | 'verify' | string
  routed_tier?: string
  fell_back_to?: string
  rate_limited_on?: string
  errored_on?: string
  n_candidates?: number
  n_kept?: number
  k?: number
}

export interface Span {
  id: string
  run_id: string
  parent_id: string | null
  name: string
  model: string | null
  tier: 0 | 1 | 2 | 3 | null
  input_tokens: number
  output_tokens: number
  cost_usd: number
  latency_ms: number
  outcome: 'ok' | 'degraded' | 'failed'
  retries: number
  error: string | null
  started_at: number
  ended_at: number
  attrs: SpanAttrs
}

export interface SpanNode extends Span {
  children: SpanNode[]
}

export interface Run {
  run_id: string
  label: string | null
  created_at: number
  span_count: number
  total_cost_usd: number
  total_tokens: number
  had_failure: 0 | 1
}

export interface RunDetail {
  spans: Span[]
  tree: SpanNode[]
}

export interface TracesData {
  generated_at: number
  runs: Run[]
  runs_detail: Record<string, RunDetail>
}
