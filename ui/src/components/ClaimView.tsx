'use client'

import verificationData from '../../public/verification.json'

interface VerificationData {
  claim: string
  model: string
  n_buggy: number
  n_clean: number
  headline: {
    fp_at_k0_pct: number
    fp_at_k3_pct: number
    recall_at_k0_pct: number
    recall_at_k3_pct: number
    fp_at_k0_ci95_pct: [number, number]
    fp_at_k3_ci95_pct: [number, number]
    recall_at_k3_ci95_pct: [number, number]
  }
  ablation_k_sweep: Array<{
    k: number
    fp_rate: number
    recall: number
    kept_findings: number
  }>
  recall_regressions: Array<{
    snippet: string
    line: number
    bug: string
    skeptic_votes_k3: string[]
  }>
}

const data = verificationData as unknown as VerificationData

function fmt(n: number, digits = 1) {
  return n.toFixed(digits) + '%'
}

function fmtRaw(n: number) {
  return (n * 100).toFixed(1) + '%'
}

function ci(pair: [number, number]) {
  return `[${pair[0].toFixed(1)}, ${pair[1].toFixed(1)}]%`
}

function Bar({ value, max = 1, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div
      className="h-1.5 rounded-full overflow-hidden"
      style={{ background: 'var(--color-surface-3)', width: '100%' }}
    >
      <div
        className="h-full rounded-full"
        style={{
          width: `${pct}%`,
          background: color,
          transition: 'width 0.4s ease',
        }}
      />
    </div>
  )
}

export function ClaimView() {
  const { headline, ablation_k_sweep, recall_regressions, model, n_buggy, n_clean } = data

  return (
    <div className="max-w-3xl mx-auto space-y-8 py-2">
      {/* Caption */}
      <div
        className="text-xs font-mono px-3 py-2 rounded-md"
        style={{
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          color: 'var(--color-text-tertiary)',
        }}
      >
        model: {model} · benchmark: {n_buggy} buggy + {n_clean} clean snippets · small sample — read directionally
      </div>

      {/* Hero stats */}
      <div
        className="rounded-xl p-6"
        style={{
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="text-xs font-semibold uppercase tracking-widest mb-6" style={{ color: 'var(--color-text-tertiary)' }}>
          Headline Result · K=0 → K=3
        </div>

        <div className="grid grid-cols-2 gap-8">
          {/* False Positive Rate */}
          <div>
            <div className="text-xs mb-3" style={{ color: 'var(--color-text-secondary)' }}>
              False-Positive Rate
            </div>
            <div className="flex items-baseline gap-3 flex-wrap">
              <span
                className="font-mono text-4xl font-semibold tabular-nums"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {fmt(headline.fp_at_k0_pct)}
              </span>
              <span style={{ color: 'var(--color-text-tertiary)' }}>→</span>
              <span
                className="font-mono text-4xl font-semibold tabular-nums"
                style={{ color: 'var(--color-accent)' }}
              >
                {fmt(headline.fp_at_k3_pct)}
              </span>
            </div>
            <div className="flex gap-4 mt-2">
              <span className="font-mono text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>
                {ci(headline.fp_at_k0_ci95_pct)}
              </span>
              <span style={{ color: 'var(--color-text-tertiary)', fontSize: 11 }}>→</span>
              <span className="font-mono text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>
                {ci(headline.fp_at_k3_ci95_pct)}
              </span>
            </div>
            <div className="mt-1 font-mono text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
              95% CI
            </div>
          </div>

          {/* Recall */}
          <div>
            <div className="text-xs mb-3" style={{ color: 'var(--color-text-secondary)' }}>
              Recall
            </div>
            <div className="flex items-baseline gap-3 flex-wrap">
              <span
                className="font-mono text-4xl font-semibold tabular-nums"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {fmt(headline.recall_at_k0_pct)}
              </span>
              <span style={{ color: 'var(--color-text-tertiary)' }}>→</span>
              <span
                className="font-mono text-4xl font-semibold tabular-nums"
                style={{ color: 'var(--color-accent)' }}
              >
                {fmt(headline.recall_at_k3_pct)}
              </span>
            </div>
            <div className="flex gap-4 mt-2">
              <span className="font-mono text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>
                —
              </span>
              <span style={{ color: 'var(--color-text-tertiary)', fontSize: 11 }}>→</span>
              <span className="font-mono text-[11px]" style={{ color: 'var(--color-text-tertiary)' }}>
                {ci(headline.recall_at_k3_ci95_pct)}
              </span>
            </div>
            <div className="mt-1 font-mono text-[10px]" style={{ color: 'var(--color-text-tertiary)' }}>
              95% CI
            </div>
          </div>
        </div>
      </div>

      {/* K-sweep ablation */}
      <div
        className="rounded-xl p-6"
        style={{
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="text-xs font-semibold uppercase tracking-widest mb-5" style={{ color: 'var(--color-text-tertiary)' }}>
          K-Sweep Ablation
        </div>

        {/* Column headers */}
        <div className="grid gap-3" style={{ gridTemplateColumns: '40px 1fr 1fr 60px' }}>
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>K</div>
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-error)' }}>FP Rate</div>
          <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--color-ok)' }}>Recall</div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-right" style={{ color: 'var(--color-text-tertiary)' }}>Kept</div>
        </div>

        <div className="mt-3 space-y-4">
          {ablation_k_sweep.map((row) => (
            <div key={row.k} className="grid gap-3 items-center" style={{ gridTemplateColumns: '40px 1fr 1fr 60px' }}>
              <span
                className="font-mono text-sm font-semibold tabular-nums"
                style={{ color: 'var(--color-text-primary)' }}
              >
                {row.k}
              </span>

              {/* FP Rate bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                    {fmtRaw(row.fp_rate)}
                  </span>
                </div>
                <Bar value={row.fp_rate} max={1} color="var(--color-error)" />
              </div>

              {/* Recall bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs tabular-nums" style={{ color: 'var(--color-text-secondary)' }}>
                    {fmtRaw(row.recall)}
                  </span>
                </div>
                <Bar value={row.recall} max={1} color="var(--color-ok)" />
              </div>

              <span
                className="font-mono text-xs tabular-nums text-right"
                style={{ color: 'var(--color-text-tertiary)' }}
              >
                {row.kept_findings}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recall regressions */}
      <div
        className="rounded-xl p-6"
        style={{
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="flex items-center justify-between mb-5">
          <div className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--color-text-tertiary)' }}>
            Recall Cost at K=3
          </div>
          <span
            className="font-mono text-xs px-2 py-0.5 rounded"
            style={{
              background: recall_regressions.length > 0 ? 'var(--color-warn-bg)' : 'var(--color-ok-bg)',
              color: recall_regressions.length > 0 ? 'var(--color-warn)' : 'var(--color-ok)',
              border: `1px solid ${recall_regressions.length > 0 ? 'rgba(245,158,11,0.2)' : 'rgba(74,222,128,0.2)'}`,
            }}
          >
            {recall_regressions.length} regression{recall_regressions.length !== 1 ? 's' : ''}
          </span>
        </div>

        {recall_regressions.length === 0 ? (
          <div
            className="rounded-lg px-4 py-8 text-center"
            style={{
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
            }}
          >
            <div className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              None on this run
            </div>
            <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
              K=3 quorum retained all real bugs
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {recall_regressions.map((reg, i) => {
              const real = reg.skeptic_votes_k3.filter(v => v === 'real').length
              const notBug = reg.skeptic_votes_k3.filter(v => v === 'not_a_bug').length
              return (
                <div
                  key={i}
                  className="rounded-lg p-4"
                  style={{
                    background: 'var(--color-surface-2)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className="font-mono text-xs px-1.5 py-0.5 rounded"
                        style={{
                          background: 'var(--color-surface-3)',
                          color: 'var(--color-text-secondary)',
                          border: '1px solid var(--color-border)',
                        }}
                      >
                        {reg.snippet}
                      </span>
                      <span
                        className="font-mono text-[11px]"
                        style={{ color: 'var(--color-text-tertiary)' }}
                      >
                        line {reg.line}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <span
                        className="font-mono text-[11px] px-1.5 py-0.5 rounded"
                        style={{
                          background: 'var(--color-ok-bg)',
                          color: 'var(--color-ok)',
                          border: '1px solid rgba(74,222,128,0.2)',
                        }}
                      >
                        {real} real
                      </span>
                      <span
                        className="font-mono text-[11px] px-1.5 py-0.5 rounded"
                        style={{
                          background: 'var(--color-error-bg)',
                          color: 'var(--color-error)',
                          border: '1px solid rgba(248,113,113,0.2)',
                        }}
                      >
                        {notBug} not_a_bug
                      </span>
                    </div>
                  </div>
                  <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    {reg.bug}
                  </div>
                  <div className="mt-2 text-[10px] font-mono" style={{ color: 'var(--color-text-tertiary)' }}>
                    skeptic votes: {reg.skeptic_votes_k3.join(' · ')}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
