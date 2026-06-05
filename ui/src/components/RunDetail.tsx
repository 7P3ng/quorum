'use client'

import { useState } from 'react'
import { Run, RunDetail as RunDetailType } from '@/types/traces'
import { CostHeader } from './CostHeader'
import { SpanNodeComponent } from './SpanNode'
import { TokenTimeline } from './TokenTimeline'

interface RunDetailProps {
  run: Run
  detail: RunDetailType
}

type Tab = 'tree' | 'timeline'

export function RunDetailView({ run, detail }: RunDetailProps) {
  const [activeTab, setActiveTab] = useState<Tab>('tree')

  return (
    <div className="space-y-4">
      {/* Cost header */}
      <CostHeader run={run} spans={detail.spans} />

      {/* Tab nav */}
      <div
        className="flex items-center gap-1 p-1 rounded-lg"
        style={{
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          width: 'fit-content',
        }}
      >
        {([['tree', 'Agent Tree'], ['timeline', 'Timeline']] as const).map(([tab, label]) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150"
            style={{
              background: activeTab === tab ? 'var(--color-surface-3)' : 'transparent',
              color: activeTab === tab ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
              border: activeTab === tab ? '1px solid var(--color-border-strong)' : '1px solid transparent',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'tree' && (
        <div
          className="rounded-lg p-4"
          style={{
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
          }}
        >
          {detail.tree.length === 0 ? (
            <div
              className="text-sm text-center py-8"
              style={{ color: 'var(--color-text-tertiary)' }}
            >
              No spans in this run
            </div>
          ) : (
            <div className="space-y-1">
              {detail.tree.map((node, i) => (
                <SpanNodeComponent
                  key={node.id}
                  node={node}
                  depth={0}
                  isLast={i === detail.tree.length - 1}
                  parentLines={[]}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'timeline' && (
        <TokenTimeline spans={detail.spans} />
      )}
    </div>
  )
}
