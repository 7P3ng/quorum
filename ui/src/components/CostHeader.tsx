'use client'

import { Span } from '@/types/traces'
import { Run } from '@/types/traces'
import { TierBadge } from './TierBadge'
import { formatCost, formatTokens, formatTimestamp } from '@/lib/format'
import { tierName, tierColor } from '@/lib/format'

interface CostHeaderProps {
  run: Run
  spans: Span[]
}

const TIERS = [0, 1, 2, 3] as const

export function CostHeader({ run, spans }: CostHeaderProps) {
  // Build per-tier aggregates
  const tierStats: Record<number, { cost: number; tokens: number; calls: number }> = {}
  for (const tier of TIERS) {
    tierStats[tier] = { cost: 0, tokens: 0, calls: 0 }
  }

  for (const span of spans) {
    if (span.tier !== null) {
      tierStats[span.tier].cost += span.cost_usd
      tierStats[span.tier].tokens += span.input_tokens + span.output_tokens
      tierStats[span.tier].calls++
    }
  }

  const activeTiers = TIERS.filter(t => tierStats[t].calls > 0)

  return (
    <div
      className="rounded-xl p-5"
      style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* Top: total cost + tokens */}
      <div className="flex items-start justify-between gap-6">
        <div>
          <div className="flex items-baseline gap-2">
            <span
              className="font-mono text-3xl font-bold tracking-tight"
              style={{ color: 'var(--color-accent)' }}
            >
              {formatCost(run.total_cost_usd)}
            </span>
            <span
              className="text-sm"
              style={{ color: 'var(--color-text-tertiary)' }}
            >
              total
            </span>
          </div>
          <div
            className="font-mono text-sm mt-0.5"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            {formatTokens(run.total_tokens)} tokens · {run.span_count} spans
          </div>
        </div>

        <div className="text-right">
          <div
            className="font-mono text-xs"
            style={{ color: 'var(--color-text-tertiary)' }}
          >
            {formatTimestamp(run.created_at)}
          </div>
          <div
            className="font-mono text-xs mt-0.5"
            style={{ color: 'var(--color-text-tertiary)' }}
          >
            {run.run_id.slice(0, 16)}…
          </div>
          {run.had_failure === 1 && (
            <span
              className="inline-block mt-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded"
              style={{
                color: 'var(--color-error)',
                background: 'var(--color-error-bg)',
                border: '1px solid rgba(248,113,113,0.20)',
              }}
            >
              HAD FAILURE
            </span>
          )}
        </div>
      </div>

      {/* Divider */}
      <div
        className="my-4"
        style={{ height: '1px', background: 'var(--color-border)' }}
      />

      {/* Tier breakdown */}
      {activeTiers.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {activeTiers.map(tier => {
            const stats = tierStats[tier]
            const colors = tierColor(tier)
            return (
              <div
                key={tier}
                className="rounded-md px-3 py-2"
                style={{
                  background: colors.bg,
                  border: `1px solid ${colors.border}`,
                }}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ background: colors.text }}
                  />
                  <span
                    className="text-xs font-medium"
                    style={{ color: colors.text }}
                  >
                    {tierName(tier)}
                  </span>
                </div>
                <div
                  className="font-mono text-sm font-semibold"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  {formatCost(stats.cost)}
                </div>
                <div
                  className="font-mono text-[11px] mt-0.5"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {formatTokens(stats.tokens)} tok · {stats.calls} calls
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div
          className="text-sm"
          style={{ color: 'var(--color-text-tertiary)' }}
        >
          No model calls recorded
        </div>
      )}
    </div>
  )
}
