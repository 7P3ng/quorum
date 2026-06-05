'use client'

import { Span } from '@/types/traces'
import { tierColor, tierName, formatCost, formatLatency } from '@/lib/format'

interface TokenTimelineProps {
  spans: Span[]
}

export function TokenTimeline({ spans }: TokenTimelineProps) {
  const leafSpans = spans.filter(s => s.name === 'model_call' && s.cost_usd > 0)

  if (leafSpans.length === 0) {
    return (
      <div
        className="rounded-lg p-6 text-center text-sm"
        style={{
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-tertiary)',
        }}
      >
        No model calls to display
      </div>
    )
  }

  const maxCost = Math.max(...leafSpans.map(s => s.cost_usd))
  const maxTokens = Math.max(...leafSpans.map(s => s.input_tokens + s.output_tokens))
  const maxLatency = Math.max(...leafSpans.map(s => s.latency_ms))

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
            Per-call breakdown
          </span>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm" style={{ background: 'rgba(168,196,255,0.6)' }} />
              <span className="text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>tokens</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm" style={{ background: 'var(--color-accent)', opacity: 0.7 }} />
              <span className="text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>cost</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-2">
        {leafSpans.map((span, i) => {
          const colors = tierColor(span.tier)
          const totalTokens = span.input_tokens + span.output_tokens
          const tokenPct = maxTokens > 0 ? (totalTokens / maxTokens) * 100 : 0
          const costPct = maxCost > 0 ? (span.cost_usd / maxCost) * 100 : 0
          const latencyPct = maxLatency > 0 ? (span.latency_ms / maxLatency) * 100 : 0

          const taskId = span.attrs?.task_id ?? ''
          const taskLabel = taskId
            ? taskId.split(':').slice(1, 3).join(' › ')
            : span.name

          const isVerify = span.attrs?.task_kind === 'verify'
          const hasFallback = !!(span.attrs?.fell_back_to || span.attrs?.rate_limited_on)

          return (
            <div key={span.id} className="group">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="font-mono text-[11px] w-48 truncate flex-shrink-0"
                  style={{ color: isVerify ? 'var(--color-tier-haiku)' : 'var(--color-text-secondary)' }}
                >
                  {taskLabel}
                </span>
                {hasFallback && (
                  <span
                    className="text-[10px] font-mono px-1 py-0.5 rounded flex-shrink-0"
                    style={{ color: 'var(--color-warn)', background: 'var(--color-warn-bg)' }}
                  >
                    ↗ fallback
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {/* Token bar */}
                <div className="flex-1 flex items-center gap-1">
                  <div
                    className="h-3 rounded-sm transition-all duration-300"
                    style={{
                      width: `${tokenPct}%`,
                      minWidth: '2px',
                      background: colors.text,
                      opacity: 0.55,
                    }}
                  />
                  <span
                    className="font-mono text-[10px]"
                    style={{ color: 'var(--color-text-tertiary)' }}
                  >
                    {totalTokens}
                  </span>
                </div>
                {/* Cost bar */}
                <div className="flex items-center gap-1" style={{ width: '120px' }}>
                  <div
                    className="h-3 rounded-sm transition-all duration-300"
                    style={{
                      width: `${costPct * 0.8}%`,
                      minWidth: '2px',
                      background: 'var(--color-accent)',
                      opacity: 0.55,
                    }}
                  />
                  <span
                    className="font-mono text-[10px]"
                    style={{ color: 'var(--color-text-tertiary)' }}
                  >
                    {formatCost(span.cost_usd)}
                  </span>
                </div>
                {/* Latency */}
                <span
                  className="font-mono text-[10px] w-14 text-right flex-shrink-0"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {formatLatency(span.latency_ms)}
                </span>
                {/* Tier badge small */}
                <div className="w-16 text-right flex-shrink-0">
                  <span
                    className="text-[10px] font-mono"
                    style={{ color: colors.text }}
                  >
                    {tierName(span.tier)}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
