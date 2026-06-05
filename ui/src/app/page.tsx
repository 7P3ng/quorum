'use client'

import { useState } from 'react'
import { TracesData } from '@/types/traces'
import { RunCard } from '@/components/RunCard'
import { RunDetailView } from '@/components/RunDetail'
import { ClaimView } from '@/components/ClaimView'
import { formatTimestamp } from '@/lib/format'

// Static import of traces
import tracesData from '../../public/traces.json'

const data = tracesData as unknown as TracesData

type TopView = 'traces' | 'claim'

export default function HomePage() {
  const [topView, setTopView] = useState<TopView>('traces')
  const [selectedRunId, setSelectedRunId] = useState<string | null>(
    data.runs.length > 0 ? data.runs[0].run_id : null
  )

  const selectedRun = selectedRunId ? data.runs.find(r => r.run_id === selectedRunId) ?? null : null
  const selectedDetail = selectedRunId ? data.runs_detail[selectedRunId] ?? null : null

  return (
    <div
      className="min-h-screen"
      style={{ background: 'var(--color-bg)' }}
    >
      {/* Top nav */}
      <header
        className="sticky top-0 z-10"
        style={{
          background: 'rgba(10, 10, 11, 0.85)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        <div className="max-w-screen-xl mx-auto px-6 h-12 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo mark */}
            <div
              className="w-6 h-6 rounded"
              style={{
                background: 'var(--color-accent-dim)',
                border: '1px solid rgba(0,201,177,0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <circle cx="6" cy="6" r="2.5" fill="var(--color-accent)" />
                <circle cx="6" cy="6" r="5" stroke="var(--color-accent)" strokeWidth="1" strokeOpacity="0.4" fill="none" />
              </svg>
            </div>
            <span
              className="font-semibold text-sm tracking-tight"
              style={{ color: 'var(--color-text-primary)' }}
            >
              Quorum
            </span>

            {/* Segmented view switcher */}
            <div
              className="flex items-center gap-0.5 p-0.5 rounded-md"
              style={{
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border)',
              }}
            >
              {(['traces', 'claim'] as const).map((view) => (
                <button
                  key={view}
                  onClick={() => setTopView(view)}
                  className="px-2.5 py-1 rounded text-[11px] font-medium transition-all duration-150"
                  style={{
                    background: topView === view ? 'var(--color-surface-3)' : 'transparent',
                    color: topView === view ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                    border: topView === view ? '1px solid var(--color-border-strong)' : '1px solid transparent',
                  }}
                >
                  {view}
                </button>
              ))}
            </div>
          </div>

          <div
            className="font-mono text-[11px]"
            style={{ color: 'var(--color-text-tertiary)' }}
          >
            {formatTimestamp(data.generated_at)}
          </div>
        </div>
      </header>

      {/* Main layout */}
      {topView === 'traces' ? (
        <div className="max-w-screen-xl mx-auto px-6 py-6 flex gap-6" style={{ minHeight: 'calc(100vh - 48px)' }}>
          {/* Sidebar: run list */}
          <aside
            className="flex-shrink-0"
            style={{ width: '320px' }}
          >
            <div className="sticky top-20">
              <div className="flex items-center justify-between mb-3">
                <h2
                  className="text-xs font-semibold uppercase tracking-widest"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  Runs
                </h2>
                <span
                  className="font-mono text-xs"
                  style={{ color: 'var(--color-text-tertiary)' }}
                >
                  {data.runs.length}
                </span>
              </div>

              {data.runs.length === 0 ? (
                <div
                  className="rounded-lg p-6 text-center text-sm"
                  style={{
                    background: 'var(--color-surface-1)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-tertiary)',
                  }}
                >
                  No runs recorded
                </div>
              ) : (
                <div className="space-y-2">
                  {data.runs.map(run => (
                    <RunCard
                      key={run.run_id}
                      run={run}
                      isSelected={run.run_id === selectedRunId}
                      onClick={() => setSelectedRunId(run.run_id)}
                    />
                  ))}
                </div>
              )}
            </div>
          </aside>

          {/* Main: run detail */}
          <main className="flex-1 min-w-0">
            {selectedRun && selectedDetail ? (
              <RunDetailView run={selectedRun} detail={selectedDetail} />
            ) : (
              <div
                className="rounded-xl h-64 flex items-center justify-center"
                style={{
                  background: 'var(--color-surface-1)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div className="text-center">
                  <div
                    className="text-sm font-medium mb-1"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    Select a run
                  </div>
                  <div
                    className="text-xs"
                    style={{ color: 'var(--color-text-tertiary)' }}
                  >
                    Choose a run from the sidebar to inspect its spans
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      ) : (
        <div className="max-w-screen-xl mx-auto px-6 py-6" style={{ minHeight: 'calc(100vh - 48px)' }}>
          <ClaimView />
        </div>
      )}
    </div>
  )
}
