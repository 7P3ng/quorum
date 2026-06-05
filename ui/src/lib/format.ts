export function shortId(id: string): string {
  return id.slice(0, 8)
}

export function formatCost(usd: number): string {
  return '$' + usd.toFixed(4)
}

export function formatTokens(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toString()
}

export function formatLatency(ms: number): string {
  if (ms >= 1000) return (ms / 1000).toFixed(2) + 's'
  return ms.toFixed(0) + 'ms'
}

export function formatTimestamp(epoch: number): string {
  return new Date(epoch * 1000).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export function tierName(tier: 0 | 1 | 2 | 3 | null): string {
  if (tier === null) return 'Orchestrator'
  return ['DeepSeek', 'Haiku', 'Sonnet', 'Opus'][tier]
}

export function tierColor(tier: 0 | 1 | 2 | 3 | null): {
  text: string
  bg: string
  border: string
} {
  if (tier === null) return { text: '#8A9099', bg: 'rgba(138, 144, 153, 0.10)', border: 'rgba(138, 144, 153, 0.20)' }
  const tiers = [
    { text: '#6B8CFF', bg: 'rgba(107, 140, 255, 0.12)', border: 'rgba(107, 140, 255, 0.25)' },
    { text: '#4ECDC4', bg: 'rgba(78, 205, 196, 0.12)', border: 'rgba(78, 205, 196, 0.25)' },
    { text: '#A8C4FF', bg: 'rgba(168, 196, 255, 0.10)', border: 'rgba(168, 196, 255, 0.22)' },
    { text: '#D4A8FF', bg: 'rgba(212, 168, 255, 0.12)', border: 'rgba(212, 168, 255, 0.25)' },
  ]
  return tiers[tier]
}
