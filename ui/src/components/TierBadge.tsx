'use client'

import { tierName, tierColor } from '@/lib/format'

interface TierBadgeProps {
  tier: 0 | 1 | 2 | 3 | null
  size?: 'sm' | 'xs'
}

export function TierBadge({ tier, size = 'sm' }: TierBadgeProps) {
  const colors = tierColor(tier)
  const name = tierName(tier)
  const padClass = size === 'xs' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs'

  return (
    <span
      className={`inline-flex items-center rounded font-mono font-medium tracking-wide ${padClass}`}
      style={{
        color: colors.text,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
      }}
    >
      {name}
    </span>
  )
}
