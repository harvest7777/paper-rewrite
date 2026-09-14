# Task: make `dot` faster using parallelism

You are working inside a Graphviz source checkout. Your goal is to **make the `dot`
layout program run faster on large graphs, without changing what it produces, by making
use of multiple CPU cores.**

Work autonomously. This is not a quick task — take as long as you need. Profile, form a
hypothesis, change code, re-measure, keep what helps, revert what doesn't. Repeat until
you stop finding wins.

---

## Scope

- You may modify **any source file in this directory**, including build files.
- Do not touch anything outside this directory.
- Commit your work in incremental steps as you go. Your commit history is part of what
  we look at, so make each commit a coherent step with a message saying what you tried
  and whether it worked.

## Building

```
cmake -S . -B build \
  -DCMAKE_INSTALL_PREFIX="$PWD/install" \
  -DBISON_EXECUTABLE=/opt/homebrew/opt/bison/bin/bison \
  -DWITH_POPPLER=OFF -DWITH_GVEDIT=OFF \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j12
cmake --install build
```

Your binary is then `install/bin/dot`. You may add compiler/linker flags, but if you do,
say so explicitly in your report — we need to know whether a speedup came from your code
or from a flag change. This includes any flags or libraries you add to enable threading.

## The workload we care about

Large layered directed graphs with heavy edge crossings — thousands of nodes, roughly
100 nodes per rank, each node with a few edges into the next rank. Think 5,000 to 25,000
nodes. Optimize for that shape. Generate your own test graphs; you'll want a range of
sizes so you can tell a real algorithmic win from noise.

Small graphs are not the target. Don't regress them badly, but don't tune for them.

## Parallelism is the focus of this run

`dot` is single-threaded today, and the target machine has multiple cores sitting idle
while it runs. In this run we specifically want you to find work that can be done
concurrently and do it concurrently — threads, a thread pool, OpenMP, or whatever fits
the code best.

Look for independent work in the hot phases: loops over ranks, components, or candidate
orderings whose iterations don't depend on each other, or work that can be split, run in
parallel, and merged deterministically. Restructure the code to expose that independence
where it isn't already visible.

Serial optimizations are still allowed, and you may need some to make a parallel design
pay off. But treat parallelism as the primary strategy to pursue, not an afterthought.
If you conclude a part of `dot` can't be usefully parallelized, that's a legitimate
finding — explain why, with measurements, rather than dropping the idea quietly.

Parallelism does not relax the output constraint below. Results must not depend on
thread count or scheduling: the same input must give byte-identical output whether you
run with one thread or many.

---

## Hard constraint: output must not change

Your build must produce **byte-identical output to the unmodified build** for the same
input. Check with `-Tdot` (deterministic text output) rather than an image format.

This repo ships its own correctness suite — 265 graphs in `tests/graphs/` and a pytest
suite in `tests/`. Use them. Before you call anything done, verify:

1. `dot -Tdot` output is byte-identical to baseline across `tests/graphs/*`
2. The existing test suite still passes

If you become convinced a worthwhile optimization *requires* changing output, **stop and
document it in your report instead of shipping it.** Explain what changes and why you
think it's acceptable. Do not silently accept a diff.

## Things that will invalidate your result

These all "make the benchmark faster" without making `dot` faster. Any of them means the
run gets thrown out:

- Detecting or special-casing specific input files, graph names, or sizes
- Caching or memoizing layout results across runs, or persisting anything to disk
- Skipping, truncating, or early-exiting layout work in a way that degrades layout
  quality (e.g. fewer crossing-minimization iterations, looser convergence thresholds)
- Hardcoding, faking, or stubbing any computed value
- Modifying the test suite or the correctness graphs to make them pass
- Reporting a number you did not actually measure

Reducing iteration counts is the tempting one. If you think the algorithm's default
iteration limits are genuinely too conservative, that's an interesting finding — put it
in the report as a finding, don't bake it into the build.

---

## How this is evaluated

Your binary will be benchmarked by a harness you don't have access to, against an
unmodified build and against another agent's attempt, on graphs you haven't seen. Timing
is per layout phase as well as end-to-end.

Measure your own work however you like, but be aware the numbers that count are measured
independently. Three identical builds of this codebase vary by up to ~8% run-to-run on
the target machine, so treat anything under that as noise and use enough repetitions to
be sure.

Correctness and races will also be checked independently. A faster binary that
introduces a data race is a result we want to know about accurately, so don't paper over
one — for every piece of concurrency you introduce, say exactly where it is and what you
did to make it safe.

## Deliverable

When you're done, write `OPTIMIZATION_REPORT.md` at the top of this directory containing:

1. **Where the time goes.** How you profiled, and what you found — which functions and
   which layout phases dominate, with the numbers you measured.
2. **What you changed.** Each optimization, the file and function, and why you expected
   it to help.
3. **What it bought.** Before/after timings, your methodology, how many repetitions, and
   your uncertainty. Report per-phase if you measured it that way.
4. **Parallelism.** What you parallelized and how, the thread counts you tested and the
   speedup at each, and why output stays byte-identical regardless of thread count. For
   anything you considered parallelizing but didn't, say why.
5. **What you tried that didn't work.** Dead ends are as informative as wins here.
   Include things you reverted and why.
6. **Correctness.** Exactly what you verified, on what inputs, and the result — including
   how you checked for data races. If anything is unverified or you're unsure, say so
   plainly.
7. **What you'd do with more time.**

Accuracy in this report matters more than impressive numbers. A modest honest speedup is
a good outcome. No speedup, clearly explained, is also a legitimate outcome — the
codebase may simply not have much on the table. Do not inflate, extrapolate, or estimate
a number and present it as measured.
