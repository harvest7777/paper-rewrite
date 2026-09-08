# Result Dump — 5,000-node crossing-heavy graph

Source: `results/crossing-heavy-5000-nodes.gv-phase*.json`, produced by `./run.sh`
on 2026-08-26.

**Machine:** MacBook Pro, Apple M4 Pro, 12 cores (8P/4E), 24 GB, macOS 26.5.2
**Tool:** hyperfine 1.20.0, `-w 10 -r 10`, all three binaries measured in one
invocation per phase so they run seconds apart under the same thermal conditions.
**Graph:** `graphs/crossing-heavy-5000-nodes.gv` — 5,000 nodes, 50 ranks,
100 nodes/rank, fanout 3, fixed seed.
**Build:** identical CMake Release flags for all three; sources pinned to
graphviz `23b06521`, agents committed on top.

---

## Cumulative phase timings

`-Gphase=N` runs a prefix of the pipeline and returns early, so these are
cumulative, not per-stage. `full` is no flag at all.

| Phase | baseline | claude | codex |
|---|---|---|---|
| 1 (rank) | 198.8 ms ± 18.4 | 184.5 ms ± 14.9 | 173.9 ms ± 8.8 |
| 2 (+ mincross) | 748.7 ms ± 27.6 | 476.9 ms ± 23.2 | 572.9 ms ± 20.1 |
| 3 (+ position) | 1001.2 ms ± 27.0 | 640.2 ms ± 23.7 | 840.2 ms ± 28.2 |
| full (+ splines) | 1115.7 ms ± 16.2 | 758.9 ms ± 19.9 | 960.9 ms ± 27.1 |

± is standard deviation over 10 runs.

## Speedup vs baseline

| Phase | claude | codex |
|---|---|---|
| 1 | 1.08× | 1.14× |
| 2 | 1.57× | 1.31× |
| 3 | 1.56× | 1.19× |
| **full** | **1.47×** | **1.16×** |

## Per-stage cost, by differencing adjacent phases

| Stage | baseline | claude | codex |
|---|---|---|---|
| rank | 198.8 ms | 184.5 ms (1.08×) | 173.9 ms (1.14×) |
| **mincross** | **549.9 ms** | **292.4 ms (1.88×)** | **399.1 ms (1.38×)** |
| position | 252.5 ms | 163.3 ms (1.55×) | 267.3 ms (0.94×) |
| splines | 114.6 ms | 118.6 ms (0.97×) | 120.7 ms (0.95×) |

Differencing compounds the error of both terms, so treat stage figures as
weaker evidence than the cumulative table above.

### Notes on individual stages

- **rank** — the apparent 1.08×/1.14× is not a real difference. σ is 8–18 ms on a
  ~190 ms measurement and the three binaries span ~25 ms total. The test graph pins
  ranks with `rank=same`, so ranking does very little work here and neither agent
  meaningfully changed that path. Report as no-difference.
- **mincross** — the real result. Both agents targeted it; claude went roughly
  twice as far as codex.
- **position** — claude only. Its `lib/common/ns.c` rewrite helps here because
  graphviz runs network simplex twice, once for ranking and again for x-coordinate
  assignment. With ranks pinned, only the positioning solve is hot.
- **splines** — untouched by both, within noise.

---

## Baseline phase composition

Parse-only floor measured separately with `gc`: 11.9 ms ± 0.4 (1.1% of total).

| Stage | ms | share |
|---|---|---|
| parse | 11.9 | 1.1% |
| rank | 186.9 | 16.8% |
| mincross | 549.9 | 49.3% |
| position | 252.5 | 22.6% |
| splines | 114.5 | 10.3% |

## Amdahl ceilings

Maximum achievable end-to-end speedup if a stage were driven to zero cost:

| Optimize | Ceiling |
|---|---|
| mincross only | **1.97×** |
| mincross + position | 3.56× |
| everything but parse | 94× (not meaningful) |

Under *perfect* linear scaling on 8 performance cores:

| Parallelize | Ceiling |
|---|---|
| mincross only | 1.76× |
| mincross + position | 2.70× |
| everything but parse | 7.44× |

Claude's serial 1.88× on mincross already exceeds what perfect 4-way parallelism
of that stage would deliver. Its current build plus perfect 8-way parallelism on
the remaining mincross would reach 2.22×.

These shares are specific to this graph at 5k nodes. Mincross scales worse than
the other phases, so its share — and the ceiling — should rise at 10k and 25k.
Not yet measured.

---

## Correctness

`dot -Tdot` output on this graph is byte-identical across all three binaries
(SHA1 `3560c5d0c650dd10f088c42bde10000cc80dfd1f`).

Not yet verified: byte-identity across the 265 graphs in `tests/graphs/`, the
graphviz pytest suite, and ThreadSanitizer. Both agents claim the first two in
their reports; neither claim has been independently checked.

## What each agent changed

| | commits | files | lines |
|---|---|---|---|
| claude | 8 + report | `lib/common/ns.c`, `lib/dotgen/mincross.c` | +978 / −169 |
| codex | 3 + report | `lib/dotgen/mincross.c` | +122 / −17 |

Neither used OpenMP. Both went serial-algorithmic.

- **codex** — fused the symmetric `in_cross`/`out_cross` pairs into a single pass,
  and replaced the linear prefix scan in `rcross` with a Fenwick tree.
- **claude** — the same fused-crossing-count idea, plus a network simplex rewrite:
  DFS frame kept in locals with a reusable stack, and the scattered `ND_par`/
  `ND_low`/`ND_lim` accesses replaced by a dense 32-byte-per-node state array with
  cached neighbour pointers.

Both diffs were scanned for iteration-count changes, early exits, input
special-casing, and test modification. None found.

---

## Methodological caveat

Baseline drifted ~13% across sessions on this machine (phase 2 measured at
854.5 ms, 738.8 ms, and 748.7 ms in three separate runs). Only comparisons made
*within a single hyperfine invocation* are valid. Do not compare numbers across
runs, including against earlier dumps.

An earlier null test — three binaries built from identical sources — showed up to
7.9% spread. Treat that as the noise floor for this setup.
