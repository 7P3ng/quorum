'use client'

import { useState } from 'react'
import { SpanNode as SpanNodeType } from '@/types/traces'
import { TierBadge } from './TierBadge'
import { formatCost, formatLatency, formatTokens } from '@/lib/format'

interface SpanNodeProps {
  node: SpanNodeType
  depth: number
  isLast: boolean
  parentLines: boolean[]
}

function getNodeRole(node: SpanNodeType): 'root' | 'finder' | 'skeptic' | 'leaf' {
  if (node.parent_id === null) return 'root'
  if (node.attrs?.task_kind === 'find_bugs') return 'finder'
  if (node.attrs?.task_kind === 'verify') return 'skeptic'
  return 'leaf'
}

function getRoleStyle(role: 'root' | 'finder' | 'skeptic' | 'leaf') {
  switch (role) {
    case 'root':
      return { accent: 'var(--color-accent)', bg: 'var(--color-accent-dim)' }
    case 'finder':
      return { accent: '#A8C4FF', bg: 'rgba(168, 196, 255, 0.06)' }
    case 'skeptic':
      return { accent: '#4ECDC4', bg: 'rgba(78, 205, 196, 0.06)' }
    default:
      return { accent: 'var(--color-text-tertiary)', bg: 'transparent' }
  }
}

function getRoleLabel(role: 'root' | 'finder' | 'skeptic' | 'leaf') {
  switch (role) {
    case 'root': return 'orchestrator'
    case 'finder': return 'finder'
    case 'skeptic': return 'skeptic'
    default: return null
  }
}

export function SpanNodeComponent({ node, depth, isLast, parentLines }: SpanNodeProps) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.children.length > 0
  const role = getNodeRole(node)
  const roleStyle = getRoleStyle(role)
  const roleLabel = getRoleLabel(role)

  const hasFallback = !!(node.attrs?.fell_back_to || node.attrs?.rate_limited_on)
  const isFailed = node.outcome === 'failed'
  const isDegraded = node.outcome === 'degraded'

  const taskId = node.attrs?.task_id
  const taskLabel = taskId ? taskId.split(':').slice(1, 3).join(' › ') : null

  return (
    <div className="relative">
      <div className="flex items-start gap-0">
        {/* Tree lines */}
        {depth > 0 && (
          <div className="flex-shrink-0 flex" style={{ width: `${depth * 20}px` }}>
            {parentLines.map((showLine, i) => (
              <div
                key={i}
                className="w-5 flex-shrink-0 relative"
                style={{ minWidth: '20px' }}
              >
                {showLine && i === parentLines.length - 1 ? (
                  <>
                    <div
                      className="absolute left-2"
                      style={{
                        top: 0,
                        bottom: isLast ? '50%' : 0,
                        width: '1px',
                        background: 'rgba(255,255,255,0.08)',
                      }}
                    />
                    <div
                      className="absolute"
                      style={{
                        top: '14px',
                        left: '8px',
                        width: '10px',
                        height: '1px',
                        background: 'rgba(255,255,255,0.08)',
                      }}
                    />
                  </>
                ) : showLine ? (
                  <div
                    className="absolute left-2"
                    style={{
                      top: 0,
                      bottom: 0,
                      width: '1px',
                      background: 'rgba(255,255,255,0.08)',
                    }}
                  />
                ) : null}
              </div>
            ))}
          </div>
        )}

        {/* Node content */}
        <div className="flex-1 min-w-0 mb-1">
          <div
            className="rounded-md px-3 py-2.5 transition-colors duration-100"
            style={{
              background: isFailed
                ? 'rgba(248, 113, 113, 0.06)'
                : role === 'root'
                ? 'var(--color-surface-2)'
                : 'var(--color-surface-1)',
              border: isFailed
                ? '1px solid rgba(248, 113, 113, 0.18)'
                : hasFallback
                ? '1px solid rgba(245, 158, 11, 0.18)'
                : `1px solid var(--color-border)`,
            }}
          >
            <div className="flex items-center gap-2 flex-wrap">
              {/* Toggle */}
              {hasChildren && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex-shrink-0 w-4 h-4 flex items-center justify-center rounded transition-colors duration-100"
                  style={{
                    color: 'var(--color-text-tertiary)',
                    background: 'rgba(255,255,255,0.04)',
                  }}
                  aria-label={expanded ? 'Collapse' : 'Expand'}
                >
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor">
                    {expanded ? (
                      <path d="M1 3L4 6L7 3" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                    ) : (
                      <path d="M3 1L6 4L3 7" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                    )}
                  </svg>
                </button>
              )}

              {/* Span name */}
              <span
                className="font-mono text-xs font-semibold"
                style={{ color: roleStyle.accent }}
              >
                {node.name}
              </span>

              {/* Role label */}
              {roleLabel && (
                <span
                  className="text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    color: roleStyle.accent,
                    background: roleStyle.bg,
                    opacity: 0.8,
                  }}
                >
                  {roleLabel}
                </span>
              )}

              {/* Task label */}
              {taskLabel && (
                <span
                  className="text-[11px] font-mono"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {taskLabel}
                </span>
              )}

              {/* Spacer */}
              <div className="flex-1" />

              {/* Outcome markers */}
              {isFailed && (
                <span
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ color: 'var(--color-error)', background: 'var(--color-error-bg)', border: '1px solid rgba(248,113,113,0.20)' }}
                >
                  FAILED
                </span>
              )}
              {isDegraded && (
                <span
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ color: 'var(--color-warn)', background: 'var(--color-warn-bg)', border: '1px solid rgba(245,158,11,0.20)' }}
                >
                  DEGRADED
                </span>
              )}
              {hasFallback && (
                <span
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ color: 'var(--color-warn)', background: 'var(--color-warn-bg)', border: '1px solid rgba(245,158,11,0.20)' }}
                >
                  ↗ {node.attrs.fell_back_to ?? node.attrs.rate_limited_on}
                </span>
              )}
              {node.retries > 0 && (
                <span
                  className="text-[10px] font-mono px-1.5 py-0.5 rounded flex-shrink-0"
                  style={{ color: 'var(--color-warn)', background: 'var(--color-warn-bg)' }}
                >
                  {node.retries}× retry
                </span>
              )}

              {/* Tier badge */}
              {node.tier !== null && (
                <TierBadge tier={node.tier} size="xs" />
              )}
            </div>

            {/* Metrics row */}
            <div className="flex items-center gap-4 mt-1.5 flex-wrap">
              {node.model && (
                <span
                  className="font-mono text-[11px]"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {node.model}
                </span>
              )}
              {(node.input_tokens > 0 || node.output_tokens > 0) && (
                <span
                  className="font-mono text-[11px]"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {node.input_tokens}↓ {node.output_tokens}↑ tok
                </span>
              )}
              {node.cost_usd > 0 && (
                <span
                  className="font-mono text-[11px]"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {formatCost(node.cost_usd)}
                </span>
              )}
              <span
                className="font-mono text-[11px]"
                style={{ color: 'var(--color-text-tertiary)' }}
              >
                {formatLatency(node.latency_ms)}
              </span>
              {node.attrs?.n_candidates !== undefined && (
                <span
                  className="text-[11px]"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {node.attrs.n_candidates} cand → {node.attrs.n_kept} kept
                </span>
              )}
            </div>

            {/* Error */}
            {node.error && (
              <div
                className="mt-1.5 text-[11px] font-mono px-2 py-1 rounded"
                style={{ color: 'var(--color-error)', background: 'var(--color-error-bg)' }}
              >
                {node.error}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div>
          {node.children.map((child, i) => (
            <SpanNodeComponent
              key={child.id}
              node={child}
              depth={depth + 1}
              isLast={i === node.children.length - 1}
              parentLines={[...parentLines, i < node.children.length - 1 || !isLast]}
            />
          ))}
        </div>
      )}
    </div>
  )
}
