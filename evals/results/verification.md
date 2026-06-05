# Claim 2 — Adversarial verification cuts false positives

Model: **deepseek (tier-0)** · benchmark: 12 buggy + 12 clean snippets.

**Headline:** K=3 adversarial verification cut the false-positive rate on clean code from **50.0% → 0.0%** (recall on buggy code 100.0% → 66.7%).

## Ablation — K sweep

| K (skeptics) | False-positive rate | Recall | Kept findings |
|---:|---:|---:|---:|
| 0 | 50.0% | 100.0% | 18 |
| 1 | 0.0% | 66.7% | 8 |
| 3 | 0.0% | 66.7% | 8 |
| 5 | 0.0% | 66.7% | 8 |

K=0 = keep every candidate (no verification). Ties / failed skeptics resolve toward *refute*.
