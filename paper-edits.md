# Paper edits

Covers four of Prof. Xu's comments: null-test replication, command ordering,
topologies, and the rank-pinning artifact he predicted. Phase instrumentation
was added along the way. The correctness sweep and the Codex ablation are still
open — see `feedback-plan.md`.

Sections 4 and 5 supersede sections 1-3: everything before them was measured on
rank-pinned graphs.

---

# 1. Noise floor now comes from the baseline itself

Prof. Xu asked for the null test to be replicated so its uncertainty could be
quantified. We did that, then removed the null test entirely.

**Reason:** separately-installed identical binaries are benchmarked in their own
`hyperfine` invocation, with a different command set and thermal profile from
the runs they are supposed to bound. They describe a different experiment.

Because command order rotates, the baseline is already measured three times, once
in each position, *inside the invocations that produce the results*. Its own
spread is a floor measured under the real conditions, on the real graphs,
against the real competitors -- and it costs nothing.

**Apparent speedup between the baseline and itself:**

| Measurement | Worst case | Median |
|---|---|---|
| End-to-end | 1.019x | 1.006x |
| Initialization | 1.119x | 1.032x |
| Ranking | 1.020x | 1.007x |
| Crossing minimization | 1.015x | 1.006x |
| Coordinate assignment | 1.019x | 1.009x |
| Spline routing | 1.010x | 1.005x |

Initialization is much noisier than the rest (parse and setup, sensitive to page
cache), which is why the floor is reported per phase rather than as one number.

## Edits

**Done.** `2_method.tex` drops the null-test subsection; the floor is now two
paragraphs in the Measurement subsection. `3_results.tex` reports the table
above. Figure 1 is gone -- a floor of nine tightly clustered points did not earn
a figure. Intro, conclusion and reproducibility statement updated.

**Every claim got easier to defend.** The floor fell from 1.079x to 1.019x, so
Codex's 1.16x on default went from roughly twice the floor to roughly eight
times it. No conclusion changed direction.

---

# 2. Command order balanced — and it did not matter

*"Randomize command order in hyperfine... should pull the floor down and settle
whether Codex's 1.15× is alive or dead."*

`run.sh` now rotates the command order so each binary occupies each position
exactly once (a Latin square generated from the binary list, not hardcoded).
Three permutations, 10 warmup + 10 timed runs each, pooled to 30 runs per binary.

**End-to-end, pooled across all three permutations:**

| Binary | Mean | Speedup |
|---|---|---|
| baseline | 1155.2 ± 35.8 ms | 1.00× |
| Claude | 810.6 ± 20.7 ms | **1.43×** |
| Codex | 967.3 ± 30.4 ms | **1.19×** |

**Per permutation:**

| Permutation | Claude | Codex |
|---|---|---|
| 1 | 1.416× | 1.159× |
| 2 | 1.436× | 1.205× |
| 3 | 1.424× | 1.219× |

## Edits

**Report this as a checked negative result, not a silent fix.** Claude's spread
across permutations is 1.42–1.44×, and the balanced 1.43× matches the unbalanced
1.47× within noise. Order bias was real in the null data but was not distorting
the headline. Say so — a reviewer who asks "did you check?" should find the
answer, and a negative control that came back negative is worth the two
sentences.

**Codex survives.** 1.19× pooled, against a 1.052× identical-binary maximum.
The question Prof. Xu raised is answered: alive.

**Update `2_method.tex` §3.3** to describe the rotation, and note that hyperfine
runs all repetitions of one command before moving to the next, which is why
balancing across invocations is the available remedy.

---

# 3. Phases measured directly instead of by differencing

Not something Prof. Xu asked for, but it removes the weakest arithmetic in the
paper and made items 1–2 cheaper to run.

Each build now carries an identical patch (`lib/dotgen/dotinit.c`, cherry-picked
so all three diffs hash the same) that times each phase inside the process under
`GV_PHASE_TIMING` and writes to stderr. Layout output on stdout is unchanged —
still SHA-1 `3560c5d0…` for all three — so the correctness check is unaffected.

**Phase timings, 30 runs per binary:**

| Phase | Baseline | Claude | Codex |
|---|---|---|---|
| init | 153.3 ± 11.4 | 154.6 ± 10.7 | 161.2 ± 20.8 |
| rank | 1.0 ± 0.1 | 0.9 ± 0.0 | 0.9 ± 0.0 |
| mincross | 569.9 ± 12.9 | **301.9 ± 4.8** | 375.7 ± 8.9 |
| position | 258.8 ± 19.5 | **182.0 ± 9.7** | 257.2 ± 13.8 |
| splines | 67.5 ± 1.8 | 67.7 ± 2.0 | 68.4 ± 1.2 |

| Phase | Claude | Codex |
|---|---|---|
| mincross | 1.89× | 1.52× |
| position | **1.42×** | **1.01×** |

## Edits

**Rebuild Table 3 (per-stage) from direct measurements.** Standard deviations
fell from ±20–42 ms under differencing to ±5–13 ms. The paragraph calling
per-stage figures "weaker evidence than the cumulative table" can go, and the
`-Gphase` differencing description in §3.3 should be replaced.

**Split the "Ranking" row into `init` and `rank`.** Ranking is **1.0 ms**,
confirmed over 90 runs — not the 198.8 ms / 17.8% the paper currently reports.
That row is ~99.5% parse and graph initialization. This changes Table 1,
Figure 2, and any sentence describing ranking's share.

**Add an "other" row.** Phases sum to 1050 ms against 1155 ms end-to-end; ~105 ms
(9%) is parse and output writing outside `dotLayout`. The phases do not tile the
runtime and the paper should not imply they do. `-Gphase` differencing hid this
inside phase 1.

**Codex does nothing to coordinate assignment** — 1.01×, now unambiguous with the
smaller error bars. This is the mechanism behind its flat scaling at 10k, and it
strengthens the breadth-vs-depth argument in §5.2.

**Note the baseline is now the instrumented build.** All three binaries carry the
same timing patch, so the comparison stays fair; `2_method.tex` should say so.

---

# 4. Ranks are no longer pinned — this changes everything

The generator wrote `{ rank=same; ... }` for every layer, which pins each node's
layer and leaves network simplex nothing to compute. That is why ranking
measured 1.0 ms. Real DOT files almost never do this; it was an artifact we
introduced.

`graphs/gen-graphs.py` no longer emits `rank=same`. Node declarations are kept,
so the graphs are structurally identical — same 5,000 nodes, same 14,700
crossings, verified with `gc`.

**Ranking, same graph, pinned vs not:**

| | baseline | claude | codex |
|---|---|---|---|
| pinned (old) | 0.95 ms | 1.57 ms | 1.36 ms |
| unpinned | 267.1 ms | 129.5 ms | 271.5 ms |
| speedup | — | **2.06×** | 0.98× |

The pinning was hiding Claude's largest single-phase win — larger than its 1.89×
on crossing minimization.

**Every number currently in `main.tex` was measured on the pinned graph and is
superseded.**

---

# 5. Three topologies, not one

Added `sparse-deep` and `dense-shallow` alongside the existing shape, all at
5,000 nodes, all unpinned. Node count is held fixed so topology is the only
variable.

| topology | nodes/rank | fanout | layers | edges |
|---|---|---|---|---|
| sparse-deep | 10 | 2 | 500 | 9,980 |
| default | 100 | 3 | 50 | 14,700 |
| dense-shallow | 200 | 4 | 25 | 19,200 |

## End-to-end (30 runs each, pooled over 3 permutations)

| graph | baseline | claude | codex |
|---|---|---|---|
| sparse-deep | 600.2 ± 15.7 ms | 450.4 ± 30.2 — **1.33×** | 605.6 ± 40.2 — **0.99×** |
| default | 1412.9 ± 26.2 ms | 943.1 ± 33.4 — **1.50×** | 1215.3 ± 20.6 — **1.16×** |
| dense-shallow | 3118.3 ± 38.8 ms | 1693.8 ± 26.1 — **1.84×** | 2417.5 ± 89.7 — **1.29×** |

Per-permutation spread is tight (Claude 1.31–1.35 / 1.46–1.53 / 1.82–1.86), so
these are not ordering artifacts.

## Baseline phase composition — shape matters more than size

| | init | rank | mincross | position | splines |
|---|---|---|---|---|---|
| sparse-deep | 27.7% | 14.3% | 11.5% | **42.1%** | 4.3% |
| default | 11.2% | 20.4% | 43.9% | 19.2% | 5.2% |
| dense-shallow | 5.2% | 18.0% | **64.0%** | 9.4% | 3.4% |

Crossing minimization ranges from 11.5% to 64% of runtime across topologies at
identical node count. Compare the size axis, where it moved only 49%→38% between
5k and 10k. **Shape dominates size**, and the paper currently argues the weaker
of the two.

## Per-phase speedup

| phase | sparse-deep: claude | codex | default: claude | codex | dense-shallow: claude | codex |
|---|---|---|---|---|---|---|
| init | 0.99× | 0.94× | 1.00× | 1.01× | 1.02× | 0.99× |
| rank | **2.46×** | 0.98× | **2.04×** | 1.00× | **2.05×** | 0.98× |
| mincross | 1.47× | 1.31× | 1.87× | 1.52× | **2.34×** | 1.61× |
| position | **1.62×** | 0.97× | **1.37×** | 1.00× | **1.25×** | 0.98× |
| splines | 1.00× | 1.00× | 0.99× | 0.99× | 1.00× | 0.99× |

## Edits

**Codex measures 0.99× on sparse-deep — no speedup at all.** Its single
optimization targets a phase worth only 11.5% of runtime there. The paper's
"Codex achieves 1.16×" is a property of the topology we happened to pick. State
its result as a range across topologies (0.99×–1.29×), not a number.

**Claude wins four phases; Codex wins one.** Claude: rank ~2× on all three,
mincross 1.47–2.34×, position 1.25–1.62×. Codex: mincross only, and 0.97–1.01×
on everything else. The breadth-vs-depth argument in §5.2 no longer rests on a
single 10k data point — it is visible on every topology, and should be
promoted from inference to result.

**Ranking is now a headline result, not a non-result.** Claude is 2.0–2.5× on it
consistently. The current text reports ranking as "no difference," which was an
artifact of pinning.

**Replace the size-scaling argument with a shape argument, or run both.** The
10k data currently in the paper predates unpinning, instrumentation, and order
balancing, and cannot be mixed with anything above. Either re-run 10k under the
current protocol or drop the size axis and lead with topology.

**Mention the non-monotonic cost finding.** While choosing dense-shallow
parameters, layout time varied non-monotonically with edge count: at rank width
500, fanout 8 took 19 s while fanout 4 exceeded 45 s — *removing* edges made
layout slower. Cause is the convergence loop in `mincross.c` (`Convergence =
.995`, `MinQuit = 8`, `MaxIter = 24`): sparser wide ranks leave more
near-equivalent orderings, so the heuristic keeps clearing the improvement
threshold and runs all 24 iterations instead of quitting at 8. Rank width, not
node or edge count, is the dominant cost driver. Worth a short paragraph — it is
a real observation about `dot` and it justifies our parameter choices.

---

# Still outstanding

- **Re-measure 10k** under the new protocol. Everything above is 5k only, and the
  10k figures in the paper predate unpinning, instrumentation and order
  balancing. They cannot be mixed with anything here.
- **Sections 1-3 numbers are from pinned graphs** and are kept only for the
  null-test floor and the ordering negative result, which do not depend on graph
  content. The phase tables in section 3 are superseded by section 5.
- Correctness sweep over the 260 graphs plus the project test suite.
- Codex ablation with the phase profile supplied.
- Additional sizes and topologies.
- Unrelated correction: the paper says **265** graphs in `tests/graphs/`; there
  are **260** `.gv` files (265 entries, 5 non-graph). Wrong in three places.
