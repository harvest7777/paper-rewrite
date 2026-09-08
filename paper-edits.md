# Paper edits — null test replication

Addresses Prof. Xu's comment: *"The current 8.4% is a single draw of 'max spread
among three means.' Its own uncertainty is unquantified."*

## New data

Five independent replicates of the null test at 5k (three byte-identical
binaries, `null-a/b/c`, installed from one build tree). Raw files:
`results/nulltest-5000-rep{1..5}-phase{1,2,3,full}.json`.

For each replicate and phase we take all three pairwise comparisons between the
identical binaries and orient each as slower/faster — the same quantity a
speedup claim reports. That is 15 comparisons per phase.

**Largest apparent speedup ever measured between two identical binaries:**

| Phase | Max ratio |
|---|---|
| 1 (ranking) | 1.118× |
| 2 (+ crossing min.) | 1.067× |
| 3 (+ coordinates) | 1.049× |
| full | 1.052× |

Against what the paper claims:

| | Claude | Codex | Identical-binary max |
|---|---|---|---|
| phase 2 | 1.57× | 1.31× | 1.067× |
| phase 3 | 1.56× | 1.19× | 1.049× |
| end-to-end | 1.47× | 1.16× | 1.052× |

## What changes in the paper

**1. Replace the single 8.4% floor with the per-phase table.**
The old figure was one draw of one statistic. It was also *over-conservative*:
8.4% is 1.084×, larger than any end-to-end ratio we now observe (max 1.052×).
Guarding an end-to-end claim with the noisiest phase's number understated our
own result.

Affects: `3_results.tex` §4.1, `2_method.tex` §3.4, the abstract, and
`7_conclusion.tex` — all currently say "8.4%".

**2. Rewrite the Codex sentence in §4.3.**
Currently: *"Codex's 16% improvement is roughly twice the floor."*
Now: 1.16× against a worst-observed 1.052×, i.e. roughly three times the floor.
Codex's result is stronger than the draft states, not weaker.

**3. Report the floor as a ratio, not a percentage.**
Same unit as the claim it guards, so no mental conversion: *"across 15
comparisons between identical binaries we never measured more than 1.05×
end-to-end; Codex measures 1.16×."*

**4. Keep the ranking non-result, with better support.**
Phase 1's floor reaches 1.118× and the three binaries differ by about 1.14×
there. Reporting ranking as no difference was correct; now it is justified with
data rather than asserted.

**5. Regenerate `fig1_null_test`.**
It currently plots one replicate's means. It should show the distribution across
all five.

**6. Add to §3.4 (the null test) — evidence for the ordering confound.**
Within every replicate, `a`–`b` pairs agree tightly (1.0015–1.0160) while every
pair involving `c` is larger (1.013–1.052). `c` is the extreme value in all five
replicates. Since hyperfine runs commands in listed order, `a` and `b` are
measured close together and `c` runs last, so the disagreement is structured by
run position rather than random across binaries.

This is direct evidence from our own data for the order bias flagged in the
feedback, and it predicts that balancing command order (next item) should shrink
the floor further.

## Still outstanding

- Balance command order across permutations and re-measure everything
  (feedback item 2). Numbers above are still single-order.
- Correction unrelated to this work: the paper says **265** graphs in
  `tests/graphs/`; there are **260** `.gv` files (265 total entries, 5 non-graph).
  Wrong in three places.
