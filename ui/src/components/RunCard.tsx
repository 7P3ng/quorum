'use client'

import { Run } from '@/types/traces'
import { shortId, formatCost, formatTokens, formatTimestamp } from '@/lib/format'

interface RunCardProps {
  run: Run
  isSelected: boolean
  onClick: () => void
}

export function RunCard({ run, isSelected, onClick }: RunCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left group"
      aria-selected={isSelected}
    >
      <div
        className="rounded-lg p-4 transition-all duration-150"
        style={{
          background: isSelected ? 'var(--color-surface-3)' : 'var(--color-surface-1)',
          border: isSelected
            ? '1px solid rgba(0, 201, 177, 0.30)'
            : '1px solid var(--color-border)',
          boxShadow: isSelected ? '0 0 0 1px rgba(0, 201, 177, 0.08) inset' : 'none',
        }}
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{
                background: run.had_failure ? 'var(--color-error)' : 'var(--color-ok)',
                boxShadow: run.had_failure
                  ? '0 0 6px var(--color-error)'
                  : '0 0 6px var(--color-ok)',
              }}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className="text-sm font-semibold truncate"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  {run.label ?? 'Unnamed run'}
                </span>
                {run.had_failure === 1 && (
                  <span
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                    style={{
                      color: 'var(--color-error)',
                      background: 'var(--color-error-bg)',
                      border: '1px solid rgba(248, 113, 113, 0.20)',
                    }}
                  >
                    FAILURE
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span
                  className="font-mono text-[11px]"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {shortId(run.run_id)}
                </span>
                <span style={{ color: 'var(--color-text-tertiary)' }}>·</span>
                <span
                  className="text-[11px]"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {formatTimestamp(run.created_at)}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 flex-shrink-0">
            <div className="text-right">
              <div
                className="font-mono text-sm font-semibold"
                style={{ color: 'var(--color-accent)' }}
              >
                {formatCost(run.total_cost_usd)}
              </div>
              <div
                className="font-mono text-[11px]"
                style={{ color: 'var(--color-text-tertiary)' }}
              >
                {formatTokens(run.total_tokens)} tok
              </div>
            </div>
            <div className="text-right">
              <div
                className="font-mono text-sm"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {run.span_count}
              </div>
              <div
                className="text-[11px]"
                style={{ color: 'var(--color-text-tertiary)' }}
              >
                spans
              </div>
            </div>
          </div>
        </div>
      </div>
    </button>
  )
}
