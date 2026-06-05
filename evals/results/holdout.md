# Held-out target — real-world-style code with unseeded bugs

Target: `ratelimit.py` · model: **deepseek (tier-0)** · candidates 4 → kept 3 after K=3 adversarial verification.

Not part of the labeled benchmark — a small token-bucket limiter + LRU cache with three genuine, subtle bugs. Ground truth (author-verified):

- RateLimiter.allow: tokens never capped at capacity (burst overflow)
- LRUCache.get: hit does not update recency
- LRUCache.put: evicts most-recent instead of least-recent

## Kept after verification

| Line | Severity | Title | Skeptic votes |
|---:|---|---|---|
| 20 | medium | Token bucket capacity not enforced | 3-0 |
| 37 | high | LRU cache get does not update access order | 3-0 |
| 44 | high | Eviction pops the newest key instead of the oldest | 3-0 |

**Result: 3/3 genuine bugs found, 1 false candidate(s) refuted by verification (0 surviving false positives)** — on code the system was not built around.
