# New Paper — Plan

## Claim

Two coding agents were each given an identical, pinned checkout of GraphViz and the
same open-ended prompt that named no target function, file, or phase. Both
independently located the dominant cost (crossing minimization), both produced
output-preserving speedups under independent measurement — **1.47×** and **1.16×**
end-to-end — and **neither used parallelism.**

That is the whole paper. Everything below either supports it or bounds it.

## What we can support, and with what

| Claim | Evidence |
|---|---|
| Agents found the bottleneck unaided | Prompt text (names no target) + both diffs land in `mincross.c` |
| Speedups are real, not noise | Null test: 3 binaries from identical source spread ≤ 7.9% |
| Speedups measured independently | Harness the agents never had access to; held-out graph |
| Output unchanged | `dot -Tdot` byte-identical, SHA1 `3560c5d0…` |
| Neither used OpenMP | Both diffs; zero `#pragma omp` |
| Serial beat the parallel ceiling | Amdahl: perfect 8-core on mincross caps at 1.76× < claude's 1.88× on that stage |
| No reward hacking | Diffs checked for iteration cuts, early exits, input special-casing, test edits |

## What we cannot support — do not claim

- Anything about cache hit rates, memory bandwidth, or false sharing. Not measured.
- Race freedom. TSan has not been run yet (see Open Items).
- Correctness beyond one graph. The 265-graph suite and pytest are unverified.
- That one agent is generally better. n = 1 run per agent.
- That token counts or wall times are comparable between agents. Different accounting.
- Any statistical power claim. We have an empirical noise floor instead, which is better.

## Structure (~8 pages)

**1. Introduction** *(~1p)*
The question: can an agent, given no hint, find and fix a real bottleneck in a
mature C codebase? Why GraphViz `dot` is a good testbed — real, mature, has a
deterministic text output format that makes correctness checkable. State the
result up front.

**2. Related Work** *(~0.5p)*
Short. `dot` layout and the Sugiyama pipeline; agent/LLM-driven code optimization.
Keep the bibliography small and verified — every entry read before citing.

**3. Method** *(~2p)*
The part the prior work got wrong, so spend the space here.
- Three sandboxes, one pinned SHA, identical CMake Release flags
- The prompt, quoted in full or in an appendix — it names no target, and it
  explicitly forbids the shortcuts that fake a win
- Held-out evaluation graph; agents generate their own test inputs
- hyperfine, 10 warmup + 10 timed, all binaries in one invocation per phase
- `-Gphase=N` for phase attribution, and the note that phases are cumulative
- **The null test**, presented before any result

**4. Results** *(~2.5p)*
- Null test / noise floor first
- Cumulative phase table, mean ± SD
- Per-stage costs by differencing, flagged as weaker evidence
- What each agent changed (one paragraph each, plus commit/line counts)
- Correctness: byte-identity
- Amdahl ceilings from the measured phase composition

**5. Discussion** *(~1p)*
- Both agents converged on the same region unaided
- Neither chose parallelism, and the ceiling arithmetic suggests that was correct
  on this workload
- Effort and token cost differed by more than an order of magnitude for a 1.27×
  difference in result — worth noting, not worth over-reading

**6. Limitations** *(~0.5p)*
One graph size, one topology, one run per agent, TSan pending, test suite
unverified, cross-agent cost figures not comparable. State them plainly; do not
bury them.

**7. Reproducibility** *(~0.25p)*
Three repo links, the pinned SHA, the exact build and benchmark commands.

**8. Conclusion** *(~0.25p)*

## Reuse from `original paper/`

- **Template only** — `agents4science_2025.sty`, the `main.tex` preamble.
- **Nothing else.** Not the intro, not the related work, not the figures. The
  design section describes a pipeline that was never run; the appendix asserts
  measurements that were never taken.

## How to handle the prior paper

It shares an author and a codebase, so it has to be addressed. Recommended
treatment: cite it once as prior work on the same target, state the measured
phase composition and the resulting ceiling, and let the arithmetic stand without
commentary. No accusation, no adjectives. Where a claim of ours contradicts one
of theirs, show our measurement and move on.

**This is Ryan + Prof. Xu's call, not a drafting decision.** Settle it before
Section 2 is written.

## Open items before drafting

Blocking:
- [ ] **Venue and page limit.** Assumed Agents4Science, ~8 pages. Changes structure if wrong.
- [ ] **Decide the prior-paper framing** (above).

Cheap and worth doing — each closes a stated limitation:
- [ ] **Re-run both agents a second time.** n = 1 per agent is the weakest point in
      the paper; a reviewer will ask. Cheap relative to its cost in credibility.
- [ ] **Measure at 10k and 25k nodes.** Graphs already generate from a seeded script.
      Mincross's share should grow with size, so the ceiling moves.
- [ ] **Run TSan in the Linux container** on all three binaries. Verified working;
      only the graphviz build in-container is untested.
- [ ] **Verify byte-identity across all 265 graphs in `tests/graphs/`** plus pytest.
      Currently claimed by both agents, independently checked by nobody.

Optional:
- [ ] Add 95% CIs from the raw hyperfine JSON (closes reviewer issue #9a on the old paper).

## Reviewer issues from the prior submission

Of the 18, ten dissolve because the new paper does not make the claim (M1 cache
specs, NUMA, the OpenMP listing, scheduling, bit-exact PNG hashes, false sharing,
the ensemble description, AI confidence levels, the AI-pipeline-to-diff link,
Linux `perf` on macOS). Four are closed by data we now have (#14 end-to-end
baseline, #15 public artifact, #7 test-suite mismatch, #12 versioning). #9 needs
a labeling decision — report SD explicitly, add CIs, drop the power claim.
Cross-reference and citation hygiene (#6, #10, #13) is avoided by construction in
a new document with a small, verified bibliography.
