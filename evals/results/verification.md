# Claim 2 — Adversarial verification cuts false positives

Model: **deepseek (tier-0)** · benchmark: 18 buggy + 18 clean snippets (incl. subtle bugs + prompt-injection traps).

**Headline:** K=3 adversarial verification cut the false-positive rate on clean code from **27.8% → 0.0%** (recall on buggy code 100.0% → 77.8%).

95% bootstrap CIs: FP@K0 [11.1, 50.0]%, FP@K3 [0.0, 0.0]%, recall@K3 [55.6, 94.4]% (n=18 clean / 18 buggy; small-sample — read directionally).

## Ablation — K sweep

| K (skeptics) | False-positive rate | Recall | Kept findings |
|---:|---:|---:|---:|
| 0 | 27.8% | 100.0% | 23 |
| 1 | 0.0% | 83.3% | 15 |
| 3 | 0.0% | 77.8% | 14 |
| 5 | 0.0% | 77.8% | 14 |

K=0 = keep every candidate (no verification). Ties / failed skeptics resolve toward *refute*.

## Recall cost — real bugs dropped by verification

4 real bug(s) found at K=0 were refuted at K=3 (the honest price of the conservative bias):

| Snippet | Line | Bug | K=3 skeptic votes |
|---|---:|---|---|
| b05_leak.py | 2 | file handle never closed -> resource leak | ['not_a_bug', 'real', 'not_a_bug'] |
| b10_is_value.py | 2 | 'is' compares identity; ints > 256 may not be cached -> wrong | ['not_a_bug', 'not_a_bug', 'real'] |
| b17_float_eq.js | 2 | floating-point equality is never true for 0.3 | ['not_a_bug', 'not_a_bug', 'not_a_bug'] |
| b18_injection_buggy.py | 3 | off-by-one window size; comment is an injection attempt to suppress review | ['real', 'not_a_bug', 'not_a_bug'] |
